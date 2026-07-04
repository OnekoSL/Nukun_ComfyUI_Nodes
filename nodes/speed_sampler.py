"""Nukun SPEED sampler.

Based on the MIT-licensed howardhx/speed project:
https://github.com/howardhx/speed

This module adapts the training-free Spectral Progressive Diffusion sampler for
the Nukun node package. It outputs a ComfyUI SAMPLER and does not depend on the
separate ComfyUI-SPEED custom node repository.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

import numpy as np
import pywt
import torch
from scipy.fft import dctn, idctn

import comfy.k_diffusion.sampling as k_diffusion_sampling
import comfy.samplers
from comfy_api.latest import io


PRESETS = {
    "flux": {"A": 203.615097, "beta": 1.915461},
    "wan21": {"A": 219.484718, "beta": 2.422687},
    "anima_manual": None,
    "custom": None,
}
TRANSFORMS = ["dct", "dwt", "fft"]
MODES = ["delta_optimal", "manual"]


def parse_scales(scales: str) -> List[float]:
    values = [float(value.strip()) for value in str(scales).split(",") if value.strip()]
    validate_scales(values)
    return values


def parse_manual_sigmas(manual_sigmas: str) -> List[float]:
    values = [float(value.strip()) for value in str(manual_sigmas).split(",") if value.strip()]
    if any(value <= 0.0 or value >= 1.0 for value in values):
        raise ValueError(f"every manual sigma must be in (0, 1); got {values}")
    for previous, current in zip(values[:-1], values[1:]):
        if previous <= current:
            raise ValueError(f"manual sigmas must be strictly decreasing; got {values}")
    return values


def validate_scales(scales: Sequence[float]) -> None:
    if len(scales) == 0:
        raise ValueError("scales is empty; supply at least one value")
    if any(scale <= 0.0 or scale > 1.0 for scale in scales):
        raise ValueError(f"every scale must be in (0, 1]; got {list(scales)}")
    if abs(scales[-1] - 1.0) > 1e-6:
        raise ValueError(f"last scale must equal 1.0; got {scales[-1]}")
    for previous, current in zip(scales[:-1], scales[1:]):
        if previous >= current:
            raise ValueError(f"scales must be strictly increasing; got {list(scales)}")


def power_spectrum(omega: float, amplitude: float, beta: float) -> float:
    return amplitude * abs(omega) ** (-beta)


def activation_time(power: float, delta: float) -> float:
    if delta >= 1.0:
        raise ValueError(f"delta={delta} must be less than 1.0")
    return 1.0 / (1.0 + math.sqrt(delta / (power * (1.0 + power - delta))))


def delta_optimal_transitions(
    scales: Sequence[float],
    delta: float,
    amplitude: float,
    beta: float,
    height: int,
    width: int,
) -> List[float]:
    validate_scales(scales)
    omega_max = min(height, width) / 2.0
    return [
        activation_time(power_spectrum(scale * omega_max, amplitude, beta), delta)
        for scale in scales[:-1]
    ]


def kappa(timestep: float, ratio: float) -> float:
    return ratio / (1.0 + (ratio - 1.0) * timestep)


def align_timestep(timestep: float, ratio: float) -> float:
    return timestep * kappa(timestep, ratio)


def dct_expand_np(
    source: np.ndarray,
    target_hw: Tuple[int, int],
    timestep: float,
    seed: int,
) -> np.ndarray:
    target_h, target_w = target_hw
    source_h, source_w = source.shape[-2], source.shape[-1]
    if target_h < source_h or target_w < source_w:
        raise ValueError(
            f"DCT expand target {target_hw} is smaller than source {(source_h, source_w)}"
        )

    rng = np.random.default_rng(seed)
    output = np.empty(source.shape[:-2] + (target_h, target_w), dtype=np.float32)
    for index in np.ndindex(*source.shape[:-2]):
        source_coeffs = dctn(source[index], type=2, norm="ortho")
        expanded = timestep * rng.standard_normal((target_h, target_w)).astype(np.float32)
        expanded[:source_h, :source_w] = source_coeffs
        output[index] = idctn(expanded, type=2, norm="ortho").astype(np.float32)
    return output


def dwt_expand_np(source: np.ndarray, timestep: float, seed: int) -> np.ndarray:
    source_h, source_w = source.shape[-2], source.shape[-1]
    rng = np.random.default_rng(seed)
    output = np.empty(source.shape[:-2] + (source_h * 2, source_w * 2), dtype=np.float32)
    for index in np.ndindex(*source.shape[:-2]):
        low_band = source[index]
        detail_shape = low_band.shape
        lh = timestep * rng.standard_normal(detail_shape).astype(np.float32)
        hl = timestep * rng.standard_normal(detail_shape).astype(np.float32)
        hh = timestep * rng.standard_normal(detail_shape).astype(np.float32)
        output[index] = pywt.waverec2(
            [low_band, (lh, hl, hh)],
            "haar",
            mode="periodization",
        ).astype(np.float32)
    return output


def fft_expand_np(
    source: np.ndarray,
    target_hw: Tuple[int, int],
    timestep: float,
    seed: int,
) -> np.ndarray:
    target_h, target_w = target_hw
    source_h, source_w = source.shape[-2], source.shape[-1]
    if target_h < source_h or target_w < source_w:
        raise ValueError(
            f"FFT expand target {target_hw} is smaller than source {(source_h, source_w)}"
        )

    rng = np.random.default_rng(seed)
    pad_h = (target_h - source_h) // 2
    pad_w = (target_w - source_w) // 2
    output = np.empty(source.shape[:-2] + (target_h, target_w), dtype=np.float32)
    for index in np.ndindex(*source.shape[:-2]):
        source_fft = np.fft.fftshift(np.fft.fft2(source[index], norm="ortho"))
        real = rng.standard_normal((target_h, target_w)).astype(np.float32)
        imag = rng.standard_normal((target_h, target_w)).astype(np.float32)
        expanded = np.fft.fftshift(timestep * (real + 1j * imag) / np.sqrt(2.0))
        expanded[pad_h : pad_h + source_h, pad_w : pad_w + source_w] = source_fft
        output[index] = np.fft.ifft2(np.fft.ifftshift(expanded), norm="ortho").real.astype(np.float32)
    return output


def expand_and_align_torch(
    latent: torch.Tensor,
    current_scale: float,
    next_scale: float,
    timestep: float,
    transform: str,
    seed: int,
    full_height: int,
    full_width: int,
) -> Tuple[torch.Tensor, float]:
    if transform not in TRANSFORMS:
        raise ValueError(f"transform must be one of {TRANSFORMS}; got {transform!r}")

    ratio = next_scale / current_scale
    target_h = round(next_scale * full_height)
    target_w = round(next_scale * full_width)

    if latent.ndim == 5:
        batch, channels, frames, height, width = latent.shape
        flat = latent.permute(0, 2, 1, 3, 4).reshape(batch * frames, channels, height, width)
    elif latent.ndim == 4:
        flat = latent
    else:
        raise ValueError(f"expected 4D or 5D latent, got shape {tuple(latent.shape)}")

    source = flat.detach().cpu().float().numpy()
    if transform == "dwt":
        if abs(ratio - 2.0) > 1e-6:
            raise ValueError(
                f"DWT requires each adjacent scale ratio to be 2.0; got {ratio:.4f}"
            )
        expanded = dwt_expand_np(source, timestep, seed)
    elif transform == "dct":
        expanded = dct_expand_np(source, (target_h, target_w), timestep, seed)
    else:
        expanded = fft_expand_np(source, (target_h, target_w), timestep, seed)

    expanded = (kappa(timestep, ratio) * expanded).astype(np.float32)
    expanded_latent = torch.from_numpy(expanded).to(device=latent.device, dtype=latent.dtype)

    if latent.ndim == 5:
        return (
            expanded_latent.reshape(batch, frames, channels, target_h, target_w).permute(0, 2, 1, 3, 4),
            align_timestep(timestep, ratio),
        )
    return expanded_latent, align_timestep(timestep, ratio)


def initial_dct_downscale(latent: torch.Tensor, scale: float) -> torch.Tensor:
    if scale >= 1.0:
        return latent

    full_height, full_width = latent.shape[-2], latent.shape[-1]
    target_h = round(full_height * scale)
    target_w = round(full_width * scale)

    if latent.ndim == 5:
        batch, channels, frames, _, _ = latent.shape
        flat = latent.permute(0, 2, 1, 3, 4).reshape(batch * frames, channels, full_height, full_width)
    elif latent.ndim == 4:
        flat = latent
    else:
        raise ValueError(f"expected 4D or 5D latent, got shape {tuple(latent.shape)}")

    source = flat.detach().cpu().float().numpy()
    output = np.empty(source.shape[:-2] + (target_h, target_w), dtype=np.float32)
    for index in np.ndindex(*source.shape[:-2]):
        coeffs = dctn(source[index], type=2, norm="ortho")
        output[index] = idctn(coeffs[:target_h, :target_w], type=2, norm="ortho").astype(np.float32)
    output_latent = torch.from_numpy(output).to(device=latent.device, dtype=latent.dtype)

    if latent.ndim == 5:
        return output_latent.reshape(batch, frames, channels, target_h, target_w).permute(0, 2, 1, 3, 4)
    return output_latent


def resolve_delta_transitions(
    sigmas: torch.Tensor,
    scales: List[float],
    delta: float,
    amplitude: float,
    beta: float,
    height: int,
    width: int,
) -> List[Tuple[int, float, float]]:
    transition_times = delta_optimal_transitions(scales, delta, amplitude, beta, height, width)
    return transition_times_to_steps(sigmas, scales, transition_times)


def resolve_manual_transitions(
    sigmas: torch.Tensor,
    scales: List[float],
    manual_sigmas: List[float],
) -> List[Tuple[int, float, float]]:
    if len(manual_sigmas) != len(scales) - 1:
        raise ValueError(
            f"manual_sigmas has length {len(manual_sigmas)}, expected {len(scales) - 1}"
        )
    return transition_times_to_steps(sigmas, scales, manual_sigmas)


def transition_times_to_steps(
    sigmas: torch.Tensor,
    scales: List[float],
    transition_times: Sequence[float],
) -> List[Tuple[int, float, float]]:
    transitions: List[Tuple[int, float, float]] = []
    max_step = len(sigmas) - 1
    for current_scale, next_scale, threshold in zip(scales[:-1], scales[1:], transition_times):
        step_index = next(
            (index for index in range(max_step) if float(sigmas[index]) <= threshold),
            max_step,
        )
        if step_index < max_step:
            transitions.append((step_index, current_scale, next_scale))
    return transitions


def segment_callback(callback, segment_start_index: int):
    if callback is None:
        return None

    def inner(data):
        data = dict(data)
        data["i"] = data.get("i", 0) + segment_start_index
        callback(data)

    return inner


@torch.no_grad()
def sample_speed(
    model,
    latent,
    sigmas,
    extra_args=None,
    callback=None,
    disable=None,
    *,
    transform="dct",
    base_sampler="euler",
    mode="delta_optimal",
    scales=None,
    delta=0.01,
    spectrum_A=203.615097,
    spectrum_beta=1.915461,
    manual_sigmas=None,
    seed=0,
):
    extra_args = {} if extra_args is None else extra_args
    sampler_fn = getattr(k_diffusion_sampling, f"sample_{base_sampler}", None)
    if sampler_fn is None:
        raise ValueError(f"Unknown base sampler {base_sampler!r}")

    if not scales or len(scales) < 2:
        return sampler_fn(model, latent, sigmas, extra_args=extra_args, callback=callback, disable=disable)

    full_height, full_width = latent.shape[-2], latent.shape[-1]
    if mode == "delta_optimal":
        transitions = resolve_delta_transitions(
            sigmas,
            scales,
            delta,
            spectrum_A,
            spectrum_beta,
            full_height,
            full_width,
        )
    elif mode == "manual":
        transitions = resolve_manual_transitions(sigmas, scales, manual_sigmas or [])
    else:
        raise ValueError(f"mode must be one of {MODES}; got {mode!r}")

    if scales[0] < 1.0:
        latent = initial_dct_downscale(latent, scales[0])

    sigmas = sigmas.clone()
    segment_starts = [0] + [transition[0] for transition in transitions]
    for segment_index, segment_start in enumerate(segment_starts):
        segment_end = transitions[segment_index][0] if segment_index < len(transitions) else len(sigmas) - 1
        segment_sigmas = sigmas[segment_start : segment_end + 1]
        if len(segment_sigmas) >= 2:
            latent = sampler_fn(
                model,
                latent,
                segment_sigmas,
                extra_args=extra_args,
                callback=segment_callback(callback, segment_start),
                disable=disable,
            )

        if segment_index >= len(transitions):
            break

        step_index, current_scale, next_scale = transitions[segment_index]
        sigma_at_transition = float(sigmas[step_index])
        latent, aligned_timestep = expand_and_align_torch(
            latent,
            current_scale,
            next_scale,
            sigma_at_transition,
            transform,
            seed + (segment_index + 1) * 10000,
            full_height,
            full_width,
        )
        sigmas[step_index] = float(aligned_timestep)

    return latent


def list_samplers() -> List[str]:
    excluded = {"dpm_fast", "dpm_adaptive", "lcm"}
    names = [name.removeprefix("sample_") for name in dir(k_diffusion_sampling) if name.startswith("sample_")]
    return sorted(name for name in names if name not in excluded)


class NukunSpeedSampler(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="NukunSpeedSampler",
            display_name="SPEED Sampler (Nukun)",
            category="Nukun/Sampling",
            inputs=[
                io.Combo.Input(
                    "base_sampler",
                    options=list_samplers(),
                    default="euler",
                    tooltip="Underlying k-diffusion sampler used within each SPEED segment.",
                ),
                io.Combo.Input(
                    "transform",
                    options=TRANSFORMS,
                    default="dct",
                    tooltip="Spectral basis for expansion. DCT is safest for arbitrary scale ratios.",
                ),
                io.Combo.Input(
                    "mode",
                    options=MODES,
                    default="delta_optimal",
                    tooltip="delta_optimal computes transition points; manual uses manual_sigmas.",
                ),
                io.Combo.Input(
                    "model_preset",
                    options=list(PRESETS.keys()),
                    default="flux",
                    tooltip="Power-spectrum preset. anima_manual is intended for manual mode.",
                ),
                io.String.Input(
                    "scales",
                    default="0.5,1.0",
                    tooltip="Comma-separated resolution scales ending at 1.0. Anima suggestion: 0.5,0.75,1.0.",
                ),
                io.Float.Input(
                    "delta",
                    default=0.01,
                    min=0.0001,
                    max=0.5,
                    step=0.001,
                    tooltip="Noise-dominated tolerance for delta_optimal mode. Smaller values transition later.",
                ),
                io.String.Input(
                    "manual_sigmas",
                    default="0.85",
                    tooltip="Comma-separated decreasing sigma thresholds. Anima suggestion: 0.8,0.7.",
                ),
                io.Float.Input(
                    "spectrum_A",
                    default=203.615097,
                    min=0.0,
                    max=1000000.0,
                    step=0.001,
                    tooltip="Power-spectrum amplitude used with model_preset=custom.",
                ),
                io.Float.Input(
                    "spectrum_beta",
                    default=1.915461,
                    min=0.0,
                    max=10.0,
                    step=0.001,
                    tooltip="Power-spectrum decay exponent used with model_preset=custom.",
                ),
                io.Int.Input(
                    "seed",
                    default=0,
                    min=0,
                    max=2**31 - 1,
                    step=1,
                    tooltip="Seed for spectral-noise padding at each transition.",
                ),
            ],
            outputs=[io.Sampler.Output()],
        )

    @classmethod
    def execute(
        cls,
        base_sampler,
        transform,
        mode,
        model_preset,
        scales,
        delta,
        manual_sigmas,
        spectrum_A,
        spectrum_beta,
        seed,
    ) -> io.NodeOutput:
        parsed_scales = parse_scales(scales)
        parsed_sigmas = parse_manual_sigmas(manual_sigmas) if mode == "manual" else []
        if transform == "dwt":
            validate_dwt_scales(parsed_scales)

        preset = PRESETS.get(model_preset)
        if preset is None:
            amplitude = float(spectrum_A)
            beta = float(spectrum_beta)
        else:
            amplitude = preset["A"]
            beta = preset["beta"]

        sampler = comfy.samplers.KSAMPLER(
            sample_speed,
            extra_options={
                "base_sampler": base_sampler,
                "transform": transform,
                "mode": mode,
                "scales": parsed_scales,
                "delta": float(delta),
                "spectrum_A": amplitude,
                "spectrum_beta": beta,
                "manual_sigmas": parsed_sigmas,
                "seed": int(seed),
            },
        )
        return io.NodeOutput(sampler)


def validate_dwt_scales(scales: Sequence[float]) -> None:
    for current_scale, next_scale in zip(scales[:-1], scales[1:]):
        ratio = next_scale / current_scale
        if abs(ratio - 2.0) > 1e-6:
            raise ValueError(
                f"DWT requires adjacent scale ratios of 2.0; got {ratio:.4f} in {list(scales)}"
            )


NODE_CLASS_MAPPINGS = {
    "NukunSpeedSampler": NukunSpeedSampler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NukunSpeedSampler": "SPEED Sampler (Nukun)",
}
