import numbers

import torch
import comfy.model_management as model_management

from .regional_prompt_encoder import (
    _clean_text,
    _combine_hiresfix_text,
    _combine_text,
    _encode_text,
)


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


class NukunRegionalSculptPromptEncoder:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP",),
                "base_prompt": ("STRING", {"multiline": True, "dynamicPrompts": True}),
                "region_1": ("STRING", {"multiline": True, "dynamicPrompts": True}),
                "region_2": ("STRING", {"multiline": True, "dynamicPrompts": True}),
                "region_3": ("STRING", {"multiline": True, "dynamicPrompts": True}),
                "region_count": ("INT", {"default": 2, "min": 2, "max": 3, "step": 1}),
                "separator": ("STRING", {"default": ", "}),
                "hiresfix_prompt": ("STRING", {"multiline": True, "dynamicPrompts": True}),
                "sculptor_intensity": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.0, "max": 5.0, "step": 0.01},
                ),
                "sculptor_method": (SCULPT_METHODS, {"default": "forward"}),
                "token_normalization": (NORMALIZATION_MODES, {"default": "mean"}),
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

    RETURN_TYPES = (
        "CONDITIONING",
        "CONDITIONING",
        "CONDITIONING",
        "CONDITIONING",
        "CONDITIONING",
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "STRING",
    )
    RETURN_NAMES = (
        "base_conditioning",
        "conditioning_1",
        "conditioning_2",
        "conditioning_3",
        "hiresfix_conditioning",
        "base_text",
        "text_1",
        "text_2",
        "text_3",
        "hiresfix_text",
        "report",
    )
    FUNCTION = "encode"
    CATEGORY = "Nukun/Conditioning"
    DESCRIPTION = (
        "Combines base and regional prompts, then encodes SDXL/CLIP regional prompts "
        "with optional Vector-Sculptor-style token embedding edits."
    )

    def _get_clip_submodel(self, clip, stream_key):
        submodel = getattr(clip.cond_stage_model, f"clip_{stream_key}", None)
        if submodel is None:
            raise RuntimeError(
                f"ERROR: CLIP stream '{stream_key}' is not supported by this node. "
                f"Expected cond_stage_model.clip_{stream_key}."
            )
        if not hasattr(submodel, "transformer"):
            raise RuntimeError(f"ERROR: CLIP stream '{stream_key}' has no transformer.")
        try:
            submodel.transformer.text_model.embeddings.token_embedding.weight
        except AttributeError:
            raise RuntimeError(
                f"ERROR: CLIP stream '{stream_key}' has no token embedding table. "
                "This node is for SDXL/CLIP-style encoders, not T5."
            )
        return submodel

    def _special_token_ids(self, submodel):
        special_tokens = getattr(submodel, "special_tokens", None)
        if special_tokens:
            return {token_id for token_id in special_tokens.values() if token_id is not None}
        return {49406, 49407, 0}

    def _embedding_weights(self, submodel):
        weight = submodel.transformer.text_model.embeddings.token_embedding.weight
        return torch.clone(weight).to(device=model_management.get_torch_device(), dtype=torch.float32)

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

    def _eligible_entries(self, tokens, stream_key, special_ids):
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

    def _apply_normalization(self, tokens, stream_key, coords, normalization):
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

    def _sculpt_tokens(self, clip, text, intensity, method, normalization, top_k, cache):
        tokens = clip.tokenize(text)
        total_eligible = 0
        total_sculpted = 0
        total_neighbors = 0
        stream_reports = []

        if float(intensity) <= 0 and normalization == "none":
            for stream_key in tokens:
                self._get_clip_submodel(clip, stream_key)
            return tokens, total_eligible, total_sculpted, total_neighbors, "disabled"

        for stream_key in tokens:
            submodel = self._get_clip_submodel(clip, stream_key)
            special_ids = self._special_token_ids(submodel)
            coords = self._eligible_entries(tokens, stream_key, special_ids)
            total_eligible += len(coords)
            if len(coords) == 0:
                stream_reports.append(f"{stream_key}: 0 eligible")
                continue

            all_weights = self._embedding_weights(submodel)
            if normalization == "mean of all tokens":
                all_mags = torch.stack([torch.norm(t) for t in all_weights])
                mean_mag_all_weights = torch.mean(all_mags, dim=0).item()
            else:
                mean_mag_all_weights = None

            for batch_index, token_index, token_id in coords:
                token_weight = tokens[stream_key][batch_index][token_index]
                attn_weight = float(token_weight[1])

                if float(intensity) > 0:
                    cache_key = (stream_key, token_id, method, float(intensity), int(top_k))
                    if cache_key not in cache:
                        cache[cache_key] = self._refine_token_weight(
                            token_id, all_weights, method, float(intensity), int(top_k)
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

            self._apply_normalization(tokens, stream_key, coords, normalization)
            stream_reports.append(f"{stream_key}: {len(coords)} eligible")
            del all_weights

        return (
            tokens,
            total_eligible,
            total_sculpted,
            total_neighbors,
            ", ".join(stream_reports),
        )

    def _encode_sculpted_text(self, clip, text, intensity, method, normalization, top_k, cache):
        tokens, eligible, sculpted, neighbors, stream_report = self._sculpt_tokens(
            clip, text, intensity, method, normalization, top_k, cache
        )
        return clip.encode_from_tokens_scheduled(tokens), eligible, sculpted, neighbors, stream_report

    def encode(
        self,
        clip,
        base_prompt,
        region_1,
        region_2,
        region_3,
        region_count,
        separator,
        hiresfix_prompt,
        sculptor_intensity,
        sculptor_method,
        token_normalization,
        top_k,
    ):
        if clip is None:
            raise RuntimeError("ERROR: A valid CLIP input is required.")

        region_count = 3 if region_count >= 3 else 2
        base_text = _clean_text(base_prompt)
        combined_1 = _combine_text(base_text, region_1, separator)
        combined_2 = _combine_text(base_text, region_2, separator)
        combined_3 = _combine_text(base_text, region_3, separator) if region_count == 3 else ""
        hiresfix_text = _combine_hiresfix_text(
            base_text,
            [region_1, region_2, region_3 if region_count == 3 else ""],
            hiresfix_prompt,
            separator,
        )

        cache = {}
        base_conditioning = _encode_text(clip, base_text)
        conditioning_1, eligible_1, sculpted_1, neighbors_1, streams_1 = self._encode_sculpted_text(
            clip, combined_1, sculptor_intensity, sculptor_method, token_normalization, top_k, cache
        )
        conditioning_2, eligible_2, sculpted_2, neighbors_2, streams_2 = self._encode_sculpted_text(
            clip, combined_2, sculptor_intensity, sculptor_method, token_normalization, top_k, cache
        )

        if combined_3:
            conditioning_3, eligible_3, sculpted_3, neighbors_3, streams_3 = self._encode_sculpted_text(
                clip, combined_3, sculptor_intensity, sculptor_method, token_normalization, top_k, cache
            )
        else:
            conditioning_3 = _encode_text(clip, base_text)
            eligible_3 = sculpted_3 = neighbors_3 = 0
            streams_3 = "base fallback"

        hiresfix_conditioning, eligible_h, sculpted_h, neighbors_h, streams_h = self._encode_sculpted_text(
            clip, hiresfix_text, sculptor_intensity, sculptor_method, token_normalization, top_k, cache
        )

        total_eligible = eligible_1 + eligible_2 + eligible_3 + eligible_h
        total_sculpted = sculpted_1 + sculpted_2 + sculpted_3 + sculpted_h
        total_neighbors = neighbors_1 + neighbors_2 + neighbors_3 + neighbors_h
        report = (
            f"method: {sculptor_method}; intensity: {float(sculptor_intensity):.2f}; "
            f"normalization: {token_normalization}; top_k: {int(top_k)}; "
            f"eligible: {total_eligible}; sculpted: {total_sculpted}; "
            f"neighbors: {total_neighbors}; cache entries: {len(cache)}; "
            f"region_1 streams: {streams_1}; region_2 streams: {streams_2}; "
            f"region_3 streams: {streams_3}; hires streams: {streams_h}"
        )

        return (
            base_conditioning,
            conditioning_1,
            conditioning_2,
            conditioning_3,
            hiresfix_conditioning,
            base_text,
            combined_1,
            combined_2,
            combined_3,
            hiresfix_text,
            report,
        )


NODE_CLASS_MAPPINGS = {
    "NukunRegionalSculptPromptEncoder": NukunRegionalSculptPromptEncoder,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NukunRegionalSculptPromptEncoder": "Regional Sculpt Prompt Encoder (Nukun)",
}
