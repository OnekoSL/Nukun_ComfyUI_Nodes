import numbers

import torch
import comfy.model_management as model_management

from .t5_equal_length_balancer import SUPPORTED_T5_KEYS


SCULPT_METHODS = ("forward", "backward", "maximum_absolute", "add_minimum_absolute")
NORMALIZATION_MODES = ("none", "mean", "mean * attention")


def maximum_absolute_values(tensors, reversed=False):
    shape = tensors.shape
    tensors = tensors.reshape(shape[0], -1)
    tensors_abs = torch.abs(tensors)
    if reversed:
        idx = torch.argmin(tensors_abs, dim=0)
    else:
        idx = torch.argmax(tensors_abs, dim=0)
    return tensors[idx, torch.arange(tensors.shape[1], device=tensors.device)].reshape(shape[1:])


class NukunT5SculptEqualLengthBalancer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tokenizer": ("CLIP", {"tooltip": "The loaded T5 tokenizer to use."}),
                "target": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 0,
                        "max": 4096,
                        "step": 1,
                        "tooltip": "Minimum shared token length for positive and negative prompts.",
                    },
                ),
                "positive": ("STRING", {"multiline": True, "dynamicPrompts": True}),
                "negative": ("STRING", {"multiline": True, "dynamicPrompts": True}),
                "positive_intensity": (
                    "FLOAT",
                    {"default": 0.35, "min": 0.0, "max": 5.0, "step": 0.01},
                ),
                "positive_method": (SCULPT_METHODS, {"default": "forward"}),
                "positive_normalization": (NORMALIZATION_MODES, {"default": "none"}),
                "negative_intensity": (
                    "FLOAT",
                    {"default": 0.0, "min": 0.0, "max": 5.0, "step": 0.01},
                ),
                "negative_method": (SCULPT_METHODS, {"default": "forward"}),
                "negative_normalization": (NORMALIZATION_MODES, {"default": "mean"}),
                "top_k": (
                    "INT",
                    {
                        "default": 64,
                        "min": 1,
                        "max": 512,
                        "step": 1,
                        "tooltip": "Number of nearest token vectors used for sculpting.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "INT", "INT", "INT", "INT", "INT", "STRING")
    RETURN_NAMES = (
        "positive",
        "negative",
        "positive_raw_tokens",
        "negative_raw_tokens",
        "effective_target",
        "positive_sculpted_tokens",
        "negative_sculpted_tokens",
        "report",
    )
    FUNCTION = "balance"
    CATEGORY = "Nukun/Conditioning"
    DESCRIPTION = (
        "Encodes positive and negative prompts with equal T5 token length, "
        "optionally sculpting eligible T5 token embeddings before scheduled encoding."
    )

    def _set_t5_options(self, clip, min_length=None, min_padding=None):
        for key in SUPPORTED_T5_KEYS:
            if min_length is not None:
                clip.set_tokenizer_option(f"{key}_min_length", min_length)
            if min_padding is not None:
                clip.set_tokenizer_option(f"{key}_min_padding", min_padding)

    def _detect_t5_key(self, *token_sets):
        available = set()
        for tokens in token_sets:
            if isinstance(tokens, dict):
                available.update(tokens.keys())

        for key in SUPPORTED_T5_KEYS:
            if key in available:
                return key
        return None

    def _available_token_keys(self, *token_sets):
        available = set()
        for tokens in token_sets:
            if isinstance(tokens, dict):
                available.update(tokens.keys())
        if not available:
            return "none"
        return ", ".join(sorted(available))

    def _token_count(self, tokens, key):
        try:
            batches = tokens[key]
            if len(batches) == 0:
                return 0
            return len(batches[0])
        except (KeyError, TypeError):
            raise RuntimeError(f"ERROR: Token stream '{key}' was not found in tokenizer output.")

    def _get_t5_submodel(self, clip, t5_key):
        submodel = getattr(clip.cond_stage_model, t5_key, None)
        if submodel is None:
            raise RuntimeError(f"ERROR: T5 submodel '{t5_key}' was not found on cond_stage_model.")
        if not hasattr(submodel, "transformer"):
            raise RuntimeError(f"ERROR: T5 submodel '{t5_key}' has no transformer.")
        if not hasattr(submodel.transformer, "get_input_embeddings"):
            raise RuntimeError(f"ERROR: T5 submodel '{t5_key}' has no input embeddings accessor.")
        return submodel

    def _special_token_ids(self, submodel):
        special_tokens = getattr(submodel, "special_tokens", {}) or {}
        return {
            token_id
            for token_id in (
                special_tokens.get("start"),
                special_tokens.get("end"),
                special_tokens.get("pad"),
            )
            if token_id is not None
        }

    def _embedding_weights(self, submodel):
        weight = submodel.transformer.get_input_embeddings().weight
        device = model_management.get_torch_device()
        return torch.clone(weight).to(device=device, dtype=torch.float32)

    def _refine_token_weight(self, token_id, all_weights, method, intensity, top_k):
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

        if method == "maximum_absolute":
            concurrent_weights = torch.stack(
                [initial_clone / torch.norm(initial_clone)]
                + [t / torch.norm(t) for t in selected_weights if torch.norm(t) > 0]
            )
            new_weight = maximum_absolute_values(concurrent_weights)
            new_weight = new_weight * pre_mag / torch.norm(new_weight)
            return new_weight.detach().cpu(), len(selected_weights)

        if method == "add_minimum_absolute":
            concurrent_weights = torch.stack(
                [initial_clone / torch.norm(initial_clone)]
                + [t / torch.norm(t) for t in selected_weights if torch.norm(t) > 0]
            )
            minimum_weight = maximum_absolute_values(concurrent_weights, reversed=True)
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

    def _eligible_entries(self, tokens, t5_key, special_ids):
        coords = []
        for batch_index, batch in enumerate(tokens[t5_key]):
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

    def _apply_sculpting(self, tokens, t5_key, submodel, intensity, method, normalization, top_k):
        if float(intensity) <= 0 and normalization == "none":
            return 0, 0

        if t5_key not in tokens:
            raise RuntimeError(f"ERROR: Token stream '{t5_key}' was not found for sculpting.")

        special_ids = self._special_token_ids(submodel)
        coords = self._eligible_entries(tokens, t5_key, special_ids)
        if len(coords) == 0:
            return 0, 0

        all_weights = self._embedding_weights(submodel)
        sculpt_cache = {}
        sculpted_count = 0
        neighbor_count = 0
        mean_mag = 0.0
        mean_coords = []

        for batch_index, token_index, token_id in coords:
            token_weight = tokens[t5_key][batch_index][token_index]
            attn_weight = float(token_weight[1])
            if float(intensity) > 0:
                cache_key = (token_id, method, float(intensity), int(top_k))
                if cache_key not in sculpt_cache:
                    sculpt_cache[cache_key] = self._refine_token_weight(
                        token_id, all_weights, method, float(intensity), int(top_k)
                    )
                new_vector, found = sculpt_cache[cache_key]
                if found > 0:
                    sculpted_count += 1
                    neighbor_count += found
            else:
                new_vector = all_weights[token_id].detach().cpu()

            if normalization in ("mean", "mean * attention"):
                mean_mag += torch.norm(new_vector).item()
                mean_coords.append((batch_index, token_index, attn_weight))

            tokens[t5_key][batch_index][token_index] = (new_vector, attn_weight)

        if normalization in ("mean", "mean * attention") and len(mean_coords) > 0:
            mean_mag /= len(mean_coords)
            for batch_index, token_index, attn_weight in mean_coords:
                token_vector, current_attn = tokens[t5_key][batch_index][token_index]
                norm = torch.norm(token_vector)
                if norm == 0:
                    continue
                scale = mean_mag * (attn_weight if normalization == "mean * attention" else 1.0)
                tokens[t5_key][batch_index][token_index] = (token_vector / norm * scale, current_attn)

        del all_weights
        return sculpted_count, neighbor_count

    def balance(
        self,
        tokenizer,
        target,
        positive,
        negative,
        positive_intensity,
        positive_method,
        positive_normalization,
        negative_intensity,
        negative_method,
        negative_normalization,
        top_k,
    ):
        if tokenizer is None:
            raise RuntimeError("ERROR: A valid tokenizer is required.")

        measure = tokenizer.clone()
        self._set_t5_options(measure, min_length=0, min_padding=0)
        raw_positive_tokens = measure.tokenize(positive)
        raw_negative_tokens = measure.tokenize(negative)

        t5_key = self._detect_t5_key(raw_positive_tokens, raw_negative_tokens)
        if t5_key is None:
            expected = ", ".join(SUPPORTED_T5_KEYS)
            available = self._available_token_keys(raw_positive_tokens, raw_negative_tokens)
            raise RuntimeError(
                "ERROR: No supported T5 token stream found. "
                f"Expected one of: {expected}. Available token streams: {available}."
            )

        positive_raw_count = self._token_count(raw_positive_tokens, t5_key)
        negative_raw_count = self._token_count(raw_negative_tokens, t5_key)
        requested_target = max(0, int(target))
        effective_target = max(requested_target, positive_raw_count, negative_raw_count)

        encoder = tokenizer.clone()
        self._set_t5_options(encoder, min_padding=0)
        encoder.set_tokenizer_option(f"{t5_key}_min_length", effective_target)
        submodel = self._get_t5_submodel(encoder, t5_key)

        positive_tokens = encoder.tokenize(positive)
        negative_tokens = encoder.tokenize(negative)

        positive_sculpted, positive_neighbors = self._apply_sculpting(
            positive_tokens,
            t5_key,
            submodel,
            positive_intensity,
            positive_method,
            positive_normalization,
            top_k,
        )
        negative_sculpted, negative_neighbors = self._apply_sculpting(
            negative_tokens,
            t5_key,
            submodel,
            negative_intensity,
            negative_method,
            negative_normalization,
            top_k,
        )

        cond_positive = encoder.encode_from_tokens_scheduled(positive_tokens)
        cond_negative = encoder.encode_from_tokens_scheduled(negative_tokens)

        report = (
            f"T5 key: {t5_key}; "
            f"positive raw: {positive_raw_count}; "
            f"negative raw: {negative_raw_count}; "
            f"requested target: {requested_target}; "
            f"effective target: {effective_target}; "
            f"positive sculpted: {positive_sculpted} tokens / {positive_neighbors} neighbors; "
            f"positive method: {positive_method}; positive intensity: {float(positive_intensity):.2f}; "
            f"positive normalization: {positive_normalization}; "
            f"negative sculpted: {negative_sculpted} tokens / {negative_neighbors} neighbors; "
            f"negative method: {negative_method}; negative intensity: {float(negative_intensity):.2f}; "
            f"negative normalization: {negative_normalization}; "
            f"top_k: {int(top_k)}"
        )

        return (
            cond_positive,
            cond_negative,
            positive_raw_count,
            negative_raw_count,
            effective_target,
            positive_sculpted,
            negative_sculpted,
            report,
        )


NODE_CLASS_MAPPINGS = {
    "NukunT5SculptEqualLengthBalancer": NukunT5SculptEqualLengthBalancer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NukunT5SculptEqualLengthBalancer": "T5 Sculpt Equal-Length Prompt Balancer (Nukun)",
}
