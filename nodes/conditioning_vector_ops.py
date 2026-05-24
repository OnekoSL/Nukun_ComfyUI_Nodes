from copy import deepcopy

import torch


def _safe_norm(tensor, dim=None, keepdim=False):
    return torch.norm(tensor, dim=dim, keepdim=keepdim)


def _normalize_or_keep(tensor, target_mag):
    norm = torch.norm(tensor)
    if norm == 0 or target_mag == 0:
        return tensor
    return tensor / norm * target_mag


def _average_keep_mag(to_tensor, from_tensor, to_strength):
    to_mag = torch.norm(to_tensor)
    from_mag = torch.norm(from_tensor)
    mixed = to_tensor * float(to_strength) + from_tensor * (1.0 - float(to_strength))
    mixed_norm = torch.norm(mixed)
    if mixed_norm == 0:
        return mixed
    return mixed / mixed_norm * (to_mag * float(to_strength) + from_mag * (1.0 - float(to_strength)))


def _slerp(to_tensor, from_tensor, to_strength):
    shape = from_tensor.shape
    low = from_tensor.reshape(shape[0], -1)
    high = to_tensor.reshape(shape[0], -1)

    low_norm = _safe_norm(low, dim=1, keepdim=True)
    high_norm = _safe_norm(high, dim=1, keepdim=True)
    linear = low * (1.0 - float(to_strength)) + high * float(to_strength)

    valid = (low_norm > 0) & (high_norm > 0)
    low_unit = torch.where(valid, low / low_norm.clamp_min(1e-12), torch.zeros_like(low))
    high_unit = torch.where(valid, high / high_norm.clamp_min(1e-12), torch.zeros_like(high))
    dot = (low_unit * high_unit).sum(1).clamp(-1.0, 1.0)
    omega = torch.acos(dot)
    sin_omega = torch.sin(omega)

    use_linear = (~valid.squeeze(1)) | (sin_omega.abs() < 1e-6)
    slerped = (
        (torch.sin((1.0 - float(to_strength)) * omega) / sin_omega.clamp_min(1e-12)).unsqueeze(1) * low
        + (torch.sin(float(to_strength) * omega) / sin_omega.clamp_min(1e-12)).unsqueeze(1) * high
    )
    return torch.where(use_linear.unsqueeze(1), linear, slerped).reshape(shape)


def _apply_sdxl_segments(to_tensor, from_tensor, to_strength, op):
    if to_tensor.shape[-1] == 2048 and from_tensor.shape[-1] == 2048:
        to_tensor[..., :768] = op(to_tensor[..., :768], from_tensor[..., :768], to_strength)
        to_tensor[..., 768:] = op(to_tensor[..., 768:], from_tensor[..., 768:], to_strength)
    else:
        to_tensor[...] = op(to_tensor, from_tensor, to_strength)
    return to_tensor


def _mix_conditioning(conditioning_to, conditioning_from, conditioning_to_strength, op):
    output = deepcopy(conditioning_to)
    source = deepcopy(conditioning_from)
    for index in range(min(len(output), len(source))):
        to_tensor = output[index][0]
        from_tensor = source[index][0]
        min_tokens = min(to_tensor.shape[1], from_tensor.shape[1])
        if min_tokens <= 0:
            continue
        to_view = to_tensor[:, :min_tokens, :]
        from_view = from_tensor[:, :min_tokens, :]
        output[index][0][:, :min_tokens, :] = _apply_sdxl_segments(
            to_view,
            from_view,
            conditioning_to_strength,
            op,
        )
    return output


class NukunConditioningSlerp:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "conditioning_to": ("CONDITIONING",),
                "conditioning_from": ("CONDITIONING",),
                "conditioning_to_strength": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
            }
        }

    FUNCTION = "mix"
    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("conditioning",)
    CATEGORY = "Nukun/Conditioning"
    DESCRIPTION = "Spherical interpolation between matching conditioning vectors."

    def mix(self, conditioning_to, conditioning_from, conditioning_to_strength):
        return (_mix_conditioning(conditioning_to, conditioning_from, conditioning_to_strength, _slerp),)


class NukunConditioningAverageKeepMagnitude:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "conditioning_to": ("CONDITIONING",),
                "conditioning_from": ("CONDITIONING",),
                "conditioning_to_strength": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
            }
        }

    FUNCTION = "mix"
    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("conditioning",)
    CATEGORY = "Nukun/Conditioning"
    DESCRIPTION = "Linear blend between matching conditioning vectors while preserving blended magnitude."

    def mix(self, conditioning_to, conditioning_from, conditioning_to_strength):
        return (
            _mix_conditioning(
                conditioning_to,
                conditioning_from,
                conditioning_to_strength,
                _average_keep_mag,
            ),
        )


class NukunConditioningNormalizeMagnitudeToEmpty:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "conditioning": ("CONDITIONING",),
                "empty_conditioning": ("CONDITIONING",),
                "enabled": ("BOOLEAN", {"default": True}),
            }
        }

    FUNCTION = "normalize"
    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("conditioning",)
    CATEGORY = "Nukun/Conditioning"
    DESCRIPTION = "Normalize conditioning token magnitudes to matching empty-conditioning token magnitudes."

    def normalize(self, conditioning, empty_conditioning, enabled):
        if not enabled:
            return (conditioning,)

        output = deepcopy(conditioning)
        empty_tensor = empty_conditioning[0][0]
        empty_tokens = empty_tensor.shape[1]
        if empty_tokens <= 0:
            return (output,)

        for cond_index in range(len(output)):
            tensor = output[cond_index][0]
            for batch_index in range(tensor.shape[0]):
                for token_index in range(tensor.shape[1]):
                    empty_token = empty_tensor[0, token_index % empty_tokens]
                    token = tensor[batch_index, token_index]
                    if token.shape[0] == 2048 and empty_token.shape[0] == 2048:
                        token[:768] = _normalize_or_keep(token[:768], torch.norm(empty_token[:768]))
                        token[768:] = _normalize_or_keep(token[768:], torch.norm(empty_token[768:]))
                    else:
                        tensor[batch_index, token_index] = _normalize_or_keep(token, torch.norm(empty_token))

        return (output,)


class NukunConditioningSDXLMergeClipGL:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "cond_clip_l": ("CONDITIONING",),
                "cond_clip_g": ("CONDITIONING",),
            }
        }

    FUNCTION = "merge"
    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("conditioning",)
    CATEGORY = "Nukun/Conditioning"
    DESCRIPTION = "Merge the first 768 CLIP-L channels into an SDXL CLIP-G conditioning."

    def merge(self, cond_clip_l, cond_clip_g):
        conditioning_l = deepcopy(cond_clip_l)
        conditioning_g = deepcopy(cond_clip_g)
        for index in range(min(len(conditioning_g), len(conditioning_l))):
            g_tensor = conditioning_g[index][0]
            l_tensor = conditioning_l[index][0]
            min_tokens = min(g_tensor.shape[1], l_tensor.shape[1])
            if min_tokens <= 0 or g_tensor.shape[-1] < 768 or l_tensor.shape[-1] < 768:
                continue
            g_tensor[:, :min_tokens, :768] = l_tensor[:, :min_tokens, :768]
        return (conditioning_g,)


NODE_CLASS_MAPPINGS = {
    "NukunConditioningSlerp": NukunConditioningSlerp,
    "NukunConditioningAverageKeepMagnitude": NukunConditioningAverageKeepMagnitude,
    "NukunConditioningNormalizeMagnitudeToEmpty": NukunConditioningNormalizeMagnitudeToEmpty,
    "NukunConditioningSDXLMergeClipGL": NukunConditioningSDXLMergeClipGL,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NukunConditioningSlerp": "Conditioning Slerp (Nukun)",
    "NukunConditioningAverageKeepMagnitude": "Conditioning Average Keep Magnitude (Nukun)",
    "NukunConditioningNormalizeMagnitudeToEmpty": "Conditioning Normalize Magnitude To Empty (Nukun)",
    "NukunConditioningSDXLMergeClipGL": "Conditioning SDXL Merge CLIP G/L (Nukun)",
}
