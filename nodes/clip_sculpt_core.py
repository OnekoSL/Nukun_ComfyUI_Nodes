import numbers

import torch
import comfy.model_management as model_management


SCULPT_METHODS = ("forward", "backward", "maximum_absolute", "add_minimum_absolute")
NORMALIZATION_MODES = (
    "none",
    "mean",
    "set at 1",
    "default * attention",
    "mean * attention",
    "set at attention",
    "mean of all tokens",
)


def maximum_absolute_values(tensors, reversed=False):
    shape = tensors.shape
    tensors = tensors.reshape(shape[0], -1)
    tensors_abs = torch.abs(tensors)
    if reversed:
        idx = torch.argmin(tensors_abs, dim=0)
    else:
        idx = torch.argmax(tensors_abs, dim=0)
    return tensors[idx, torch.arange(tensors.shape[1], device=tensors.device)].reshape(shape[1:])


def get_clip_submodel(clip, stream_key):
    candidates = (f"clip_{stream_key}", stream_key)
    submodel = None
    matched_name = None
    for candidate in candidates:
        submodel = getattr(clip.cond_stage_model, candidate, None)
        if submodel is not None:
            matched_name = candidate
            break
    if submodel is None:
        raise RuntimeError(
            f"ERROR: CLIP stream '{stream_key}' is not supported by this node. "
            f"Expected one of: {', '.join('cond_stage_model.' + name for name in candidates)}."
        )
    if not hasattr(submodel, "transformer"):
        raise RuntimeError(f"ERROR: CLIP stream '{stream_key}' on cond_stage_model.{matched_name} has no transformer.")
    embedding = get_input_embedding(submodel, stream_key)
    if not hasattr(embedding, "weight"):
        raise RuntimeError(
            f"ERROR: CLIP stream '{stream_key}' has no token embedding table. "
            "This node is for SD1/SDXL CLIP-style encoders, not T5."
        )
    return submodel


def maybe_get_clip_submodel(clip, stream_key):
    try:
        return get_clip_submodel(clip, stream_key), None
    except RuntimeError as error:
        return None, str(error)


def get_input_embedding(submodel, stream_key):
    transformer = submodel.transformer
    if hasattr(transformer, "get_input_embeddings"):
        return transformer.get_input_embeddings()
    try:
        return transformer.text_model.embeddings.token_embedding
    except AttributeError:
        raise RuntimeError(
            f"ERROR: CLIP stream '{stream_key}' has no supported input embedding accessor."
        )


def special_token_ids(submodel):
    special_tokens = getattr(submodel, "special_tokens", None)
    if special_tokens:
        return {token_id for token_id in special_tokens.values() if token_id is not None}
    return {49406, 49407, 0}


def embedding_weights(submodel, stream_key):
    weight = get_input_embedding(submodel, stream_key).weight
    return torch.clone(weight).to(device=model_management.get_torch_device(), dtype=torch.float32)


def refine_token_weight(token_id, all_weights, method, intensity, top_k):
    initial_weight = all_weights[token_id]
    pre_mag = torch.norm(initial_weight)
    if pre_mag == 0:
        return initial_weight.detach().cpu(), 0

    token_norm = torch.nn.functional.normalize(initial_weight.unsqueeze(0), dim=1)
    all_norm = torch.nn.functional.normalize(all_weights, dim=1)
    scores = torch.matmul(all_norm, token_norm.T).squeeze(1)
    k = max(1, min(int(top_k) + 1, all_weights.shape[0]))
    sorted_scores, sorted_ids = torch.topk(scores, k=k, largest=True)

    candidate_ids = []
    candidate_scores = []
    for score, idx in zip(sorted_scores.tolist(), sorted_ids.tolist()):
        idx = int(idx)
        if idx == int(token_id):
            continue
        candidate_ids.append(idx)
        candidate_scores.append(float(score))
        if len(candidate_ids) >= int(top_k):
            break

    previous_cos_score = 0.0
    cos_score = 1.0
    selected_scores = []
    selected_weights = []
    initial_clone = torch.clone(initial_weight)

    for idx, score in zip(candidate_ids, candidate_scores):
        if len(selected_weights) > 0:
            previous_cos_score = cos_score
        selected_scores.append(score)
        selected_weights.append(all_weights[idx])
        vec_sum = torch.sum(torch.stack(selected_weights), dim=0)
        cos_score = torch.nn.functional.cosine_similarity(
            initial_clone.unsqueeze(0), vec_sum.unsqueeze(0), dim=1, eps=1e-6
        ).item()
        if not previous_cos_score < cos_score:
            selected_scores.pop()
            selected_weights.pop()
            break

    if len(selected_weights) <= 1:
        return initial_weight.detach().cpu(), 0

    normalized_weights = [
        initial_clone / torch.norm(initial_clone),
        *[t / torch.norm(t) for t in selected_weights if torch.norm(t) > 0],
    ]

    if method == "maximum_absolute":
        new_weight = maximum_absolute_values(torch.stack(normalized_weights))
        new_weight = new_weight * pre_mag / torch.norm(new_weight)
        return new_weight.detach().cpu(), len(selected_weights)

    if method == "add_minimum_absolute":
        minimum_weight = maximum_absolute_values(torch.stack(normalized_weights), reversed=True)
        new_weight = initial_clone + minimum_weight * float(intensity)
        new_weight = new_weight * pre_mag / torch.norm(new_weight)
        return new_weight.detach().cpu(), len(selected_weights)

    weighted_neighbors = torch.sum(
        torch.stack([t * (selected_scores[i] ** 2) for i, t in enumerate(selected_weights)]),
        dim=0,
    )
    final_score = torch.nn.functional.cosine_similarity(
        initial_weight.unsqueeze(0), weighted_neighbors.unsqueeze(0), dim=1, eps=1e-6
    ).item() * float(intensity)

    if method == "backward":
        new_weight = initial_weight + weighted_neighbors * final_score
    else:
        new_weight = initial_weight - weighted_neighbors * final_score

    new_norm = torch.norm(new_weight)
    if new_norm == 0:
        return initial_weight.detach().cpu(), 0
    new_weight = new_weight * pre_mag / new_norm
    return new_weight.detach().cpu(), len(selected_weights)


def eligible_entries(tokens, stream_key, special_ids):
    coords = []
    for batch_index, batch in enumerate(tokens[stream_key]):
        for token_index, token_weight in enumerate(batch):
            if len(token_weight) < 2:
                continue
            token_id = token_weight[0]
            if not isinstance(token_id, numbers.Integral):
                continue
            if int(token_id) in special_ids:
                continue
            coords.append((batch_index, token_index, int(token_id)))
    return coords


def apply_mean_normalization(tokens, stream_key, coords, normalization):
    if normalization not in ("mean", "mean * attention"):
        return

    mean_mag = 0.0
    mean_coords = []
    for batch_index, token_index, _ in coords:
        token_vector, attn_weight = tokens[stream_key][batch_index][token_index]
        if not torch.is_tensor(token_vector):
            continue
        mean_mag += torch.norm(token_vector).item()
        mean_coords.append((batch_index, token_index, float(attn_weight)))

    if len(mean_coords) == 0:
        return

    mean_mag /= len(mean_coords)
    for batch_index, token_index, attn_weight in mean_coords:
        token_vector, current_attn = tokens[stream_key][batch_index][token_index]
        norm = torch.norm(token_vector)
        if norm == 0:
            continue
        scale = mean_mag * (attn_weight if normalization == "mean * attention" else 1.0)
        tokens[stream_key][batch_index][token_index] = (token_vector / norm * scale, current_attn)


def sculpt_clip_tokens(clip, text, intensity, method, normalization, top_k):
    tokens = clip.tokenize(text)
    cache = {}
    total_eligible = 0
    total_sculpted = 0
    total_neighbors = 0
    stream_reports = []

    if float(intensity) <= 0 and normalization == "none":
        return tokens, {
            "eligible": 0,
            "sculpted": 0,
            "neighbors": 0,
            "cache_entries": 0,
            "streams": "disabled",
        }

    for stream_key in tokens:
        submodel, skip_reason = maybe_get_clip_submodel(clip, stream_key)
        if submodel is None:
            stream_reports.append(f"{stream_key}: skipped unsupported")
            continue
        special_ids = special_token_ids(submodel)
        coords = eligible_entries(tokens, stream_key, special_ids)
        total_eligible += len(coords)
        if len(coords) == 0:
            stream_reports.append(f"{stream_key}: 0 eligible")
            continue

        all_weights = embedding_weights(submodel, stream_key)
        if normalization == "mean of all tokens":
            all_mags = torch.stack([torch.norm(t) for t in all_weights])
            mean_mag_all_weights = torch.mean(all_mags, dim=0).item()
        else:
            mean_mag_all_weights = None

        actual_intensity = float(intensity) * 4.0 / 1.5 if stream_key.lower() == "g" else float(intensity)

        for batch_index, token_index, token_id in coords:
            token_weight = tokens[stream_key][batch_index][token_index]
            attn_weight = float(token_weight[1])

            if float(intensity) > 0:
                cache_key = (stream_key, token_id, method, actual_intensity, int(top_k))
                if cache_key not in cache:
                    cache[cache_key] = refine_token_weight(
                        token_id, all_weights, method, actual_intensity, int(top_k)
                    )
                new_vector, found = cache[cache_key]
                if found > 0:
                    total_sculpted += 1
                    total_neighbors += found
            else:
                new_vector = all_weights[token_id].detach().cpu()

            if normalization == "set at 1":
                norm = torch.norm(new_vector)
                if norm > 0:
                    new_vector = new_vector / norm
            elif normalization == "default * attention":
                new_vector = new_vector * attn_weight
            elif normalization == "set at attention":
                norm = torch.norm(new_vector)
                if norm > 0:
                    new_vector = new_vector / norm * attn_weight
            elif normalization == "mean of all tokens":
                norm = torch.norm(new_vector)
                if norm > 0:
                    new_vector = new_vector / norm * mean_mag_all_weights

            tokens[stream_key][batch_index][token_index] = (new_vector, attn_weight)

        apply_mean_normalization(tokens, stream_key, coords, normalization)
        stream_reports.append(f"{stream_key}: {len(coords)} eligible")
        del all_weights

    return tokens, {
        "eligible": total_eligible,
        "sculpted": total_sculpted,
        "neighbors": total_neighbors,
        "cache_entries": len(cache),
        "streams": ", ".join(stream_reports),
    }
