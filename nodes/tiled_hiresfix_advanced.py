import importlib
import sys
from pathlib import Path

import comfy.sample
import comfy.samplers
from comfy_extras.nodes_differential_diffusion import DifferentialDiffusion
from comfy_extras.nodes_edit_model import ReferenceLatent
from comfy_extras.nodes_upscale_model import ImageUpscaleWithModel
from nodes import VAEDecodeTiled, VAEEncodeTiled

from .noise_sampler_core import MAX_SEED, UNIVERSAL_NOISE_PROFILES, make_noise_generator


TILING_STRATEGIES = ["random", "random strict", "padded", "simple"]


def _combo_default(options, preferred):
    return preferred if preferred in options else options[0]


class NukunTiledHiResFixAdvanced:
    @classmethod
    def INPUT_TYPES(cls):
        samplers = comfy.samplers.KSampler.SAMPLERS
        schedulers = comfy.samplers.KSampler.SCHEDULERS
        return {
            "required": {
                "image": ("IMAGE",),
                "upscale_model": ("UPSCALE_MODEL",),
                "model": ("MODEL",),
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "vae": ("VAE",),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": MAX_SEED,
                        "control_after_generate": True,
                        "tooltip": "Seed used by the tiled HiRes refine pass.",
                    },
                ),
                "steps": ("INT", {"default": 20, "min": 1, "max": 10000, "step": 1}),
                "cfg": ("FLOAT", {"default": 3.5, "min": 0.0, "max": 100.0, "step": 0.1}),
                "sampler_name": (samplers, {"default": _combo_default(samplers, "res_2s")}),
                "scheduler": (schedulers, {"default": _combo_default(schedulers, "beta57")}),
                "denoise": ("FLOAT", {"default": 0.4, "min": 0.0, "max": 1.0, "step": 0.01}),
                "tile_width": ("INT", {"default": 1024, "min": 256, "max": 8192, "step": 64}),
                "tile_height": ("INT", {"default": 1024, "min": 256, "max": 8192, "step": 64}),
                "tiling_strategy": (TILING_STRATEGIES, {"default": "simple"}),
                "vae_tile_size": ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 32}),
                "vae_overlap": ("INT", {"default": 64, "min": 0, "max": 4096, "step": 32}),
                "noise_device": (
                    ["auto", "cpu", "cuda"],
                    {
                        "default": "auto",
                        "tooltip": "Device used to create Nukun noise before handing it to the tiled sampler.",
                    },
                ),
                "noise_profile": (
                    UNIVERSAL_NOISE_PROFILES,
                    {"default": "gaussian", "tooltip": "Universal Nukun noise profile for tiled refinement."},
                ),
                "noise_strength": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 5.0, "step": 0.01},
                ),
                "detail_bias": (
                    "FLOAT",
                    {
                        "default": 0.35,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                        "tooltip": "Only affects composite noise profiles.",
                    },
                ),
                "use_reference_latent": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Attach the encoded upscaled image to positive conditioning as reference_latents.",
                    },
                ),
                "use_differential_diffusion": (
                    "BOOLEAN",
                    {"default": True, "tooltip": "Patch the refine model with Differential Diffusion."},
                ),
                "differential_strength": (
                    "FLOAT",
                    {"default": 0.7, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
                "preview": (
                    ["disable", "enable"],
                    {
                        "default": "disable",
                        "tooltip": "Enable tiled latent previews during sampling. Disable is much faster.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "LATENT", "INT", "STRING")
    RETURN_NAMES = ("final_image", "upscaled_image", "refined_latent", "seed", "settings_report")
    FUNCTION = "hiresfix"
    CATEGORY = "Nukun/Sampling"
    DESCRIPTION = "Core image upscale plus tiled VAE encode/decode and BNK tiled KSampler refinement."

    def hiresfix(
        self,
        image,
        upscale_model,
        model,
        positive,
        negative,
        vae,
        seed,
        steps,
        cfg,
        sampler_name,
        scheduler,
        denoise,
        tile_width,
        tile_height,
        tiling_strategy,
        vae_tile_size,
        vae_overlap,
        noise_device,
        noise_profile,
        noise_strength,
        detail_bias,
        use_reference_latent,
        use_differential_diffusion,
        differential_strength,
        preview="disable",
    ):
        upscaled_image = _first_output(ImageUpscaleWithModel.execute(upscale_model, image))
        encoded_latent = _first_output(VAEEncodeTiled().encode(vae, upscaled_image, vae_tile_size, vae_overlap))

        work_model = model
        if use_differential_diffusion:
            work_model = _first_output(DifferentialDiffusion.execute(work_model, differential_strength))

        work_positive = positive
        if use_reference_latent:
            work_positive = _first_output(ReferenceLatent.execute(work_positive, encoded_latent))

        if float(denoise) <= 0.0:
            refined_latent = encoded_latent
            sampled = False
            total_steps = 0
            start_at_step = 0
            end_at_step = 0
        else:
            total_steps = max(int(steps), int(int(steps) / float(denoise)))
            start_at_step = max(0, total_steps - int(steps))
            end_at_step = total_steps
            refined_latent = _sample_tiled_with_nukun_noise(
                work_model,
                seed,
                tile_width,
                tile_height,
                tiling_strategy,
                total_steps,
                cfg,
                sampler_name,
                scheduler,
                work_positive,
                negative,
                encoded_latent,
                start_at_step,
                end_at_step,
                noise_device,
                noise_profile,
                noise_strength,
                detail_bias,
                preview == "enable",
            )
            sampled = True

        final_image = _first_output(VAEDecodeTiled().decode(vae, refined_latent, vae_tile_size, vae_overlap))
        report = _settings_report(
            upscaled_image,
            refined_latent,
            seed,
            sampled,
            total_steps,
            start_at_step,
            end_at_step,
            steps,
            cfg,
            sampler_name,
            scheduler,
            denoise,
            tile_width,
            tile_height,
            tiling_strategy,
            vae_tile_size,
            vae_overlap,
            noise_device,
            noise_profile,
            noise_strength,
            detail_bias,
            use_reference_latent,
            use_differential_diffusion,
            differential_strength,
            preview,
        )
        return (final_image, upscaled_image, refined_latent, seed, report)


def _sample_tiled_with_nukun_noise(
    model,
    seed,
    tile_width,
    tile_height,
    tiling_strategy,
    total_steps,
    cfg,
    sampler_name,
    scheduler,
    positive,
    negative,
    latent_image,
    start_at_step,
    end_at_step,
    noise_device,
    noise_profile,
    noise_strength,
    detail_bias,
    preview,
):
    tiled_nodes = _load_tiledksampler_nodes()
    original_prepare_noise = comfy.sample.prepare_noise

    def prepare_nukun_noise(latent_samples, noise_seed, noise_inds=None):
        work_latent = {"samples": latent_samples}
        if noise_inds is not None:
            work_latent["batch_index"] = noise_inds
        noise = make_noise_generator(
            noise_seed,
            noise_device,
            noise_profile,
            noise_strength,
            detail_bias,
        ).generate_noise(work_latent)
        return _noise_to_cpu(noise)

    try:
        comfy.sample.prepare_noise = prepare_nukun_noise
        return _first_output(
            tiled_nodes.sample_common(
                model,
                "enable",
                seed,
                tile_width,
                tile_height,
                tiling_strategy,
                total_steps,
                cfg,
                sampler_name,
                scheduler,
                positive,
                negative,
                latent_image,
                start_at_step,
                end_at_step,
                "disable",
                denoise=1.0,
                preview=preview,
            )
        )
    finally:
        comfy.sample.prepare_noise = original_prepare_noise


def _load_tiledksampler_nodes():
    try:
        return importlib.import_module("ComfyUI_TiledKSampler.nodes")
    except Exception as first_error:
        custom_nodes_dir = Path(__file__).resolve().parents[2]
        tiled_dir = custom_nodes_dir / "ComfyUI_TiledKSampler"
        if not tiled_dir.exists():
            raise ImportError(
                "NukunTiledHiResFixAdvanced requires the optional ComfyUI_TiledKSampler custom node package."
            ) from first_error

        original_sys_path = sys.path.copy()
        try:
            sys.path.insert(0, str(custom_nodes_dir))
            sys.path.insert(0, str(tiled_dir))
            return importlib.import_module("ComfyUI_TiledKSampler.nodes")
        except Exception as second_error:
            raise ImportError(
                "NukunTiledHiResFixAdvanced could not import ComfyUI_TiledKSampler.nodes."
            ) from second_error
        finally:
            sys.path = original_sys_path


def _noise_to_cpu(noise):
    if getattr(noise, "is_nested", False):
        import comfy.nested_tensor

        return comfy.nested_tensor.NestedTensor([tensor.cpu() for tensor in noise.unbind()])
    return noise.cpu()


def _first_output(value):
    if hasattr(value, "args"):
        return value.args[0]
    return value[0]


def _settings_report(
    upscaled_image,
    refined_latent,
    seed,
    sampled,
    total_steps,
    start_at_step,
    end_at_step,
    steps,
    cfg,
    sampler_name,
    scheduler,
    denoise,
    tile_width,
    tile_height,
    tiling_strategy,
    vae_tile_size,
    vae_overlap,
    noise_device,
    noise_profile,
    noise_strength,
    detail_bias,
    use_reference_latent,
    use_differential_diffusion,
    differential_strength,
    preview,
):
    image_shape = tuple(upscaled_image.shape)
    latent_shape = tuple(refined_latent["samples"].shape)
    lines = [
        "Tiled HiRes Fix Advanced (Nukun)",
        f"seed: {seed}",
        f"sampled: {sampled}",
        f"upscaled_image_shape: {image_shape}",
        f"refined_latent_shape: {latent_shape}",
        f"steps: {steps}",
        f"total_steps: {total_steps}",
        f"start_at_step: {start_at_step}",
        f"end_at_step: {end_at_step}",
        f"cfg: {cfg}",
        f"sampler_name: {sampler_name}",
        f"scheduler: {scheduler}",
        f"denoise: {denoise}",
        f"tile_width: {tile_width}",
        f"tile_height: {tile_height}",
        f"tiling_strategy: {tiling_strategy}",
        f"vae_tile_size: {vae_tile_size}",
        f"vae_overlap: {vae_overlap}",
        f"noise_device: {noise_device}",
        f"noise_profile: {noise_profile}",
        f"noise_strength: {noise_strength}",
        f"detail_bias: {detail_bias}",
        f"use_reference_latent: {use_reference_latent}",
        f"use_differential_diffusion: {use_differential_diffusion}",
        f"differential_strength: {differential_strength}",
        f"preview: {preview}",
    ]
    return "\n".join(lines)


NODE_CLASS_MAPPINGS = {
    "NukunTiledHiResFixAdvanced": NukunTiledHiResFixAdvanced,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NukunTiledHiResFixAdvanced": "Tiled HiRes Fix Advanced (Nukun)",
}
