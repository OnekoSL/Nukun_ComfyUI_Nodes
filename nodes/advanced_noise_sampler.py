from .noise_sampler_core import (
    MAX_SEED,
    NOISE_TYPES,
    PREVIEW_METHODS,
    NukunEmptyNoise,
    NukunRandomNoise,
    generate_nukun_noise_for_tensor,
    sample_custom_advanced,
    _prepare_noise,
    _resolve_noise_device,
)


class NukunAdvancedNoiseSampler:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "guider": ("GUIDER",),
                "sampler": ("SAMPLER",),
                "sigmas": ("SIGMAS",),
                "latent_image": ("LATENT",),
                "add_noise": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Generate random noise. Disable this to sample with zero noise.",
                    },
                ),
                "noise_seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": MAX_SEED,
                        "control_after_generate": True,
                        "tooltip": "Seed used for the initial noise.",
                    },
                ),
                "noise_device": (
                    ["auto", "cpu", "cuda"],
                    {
                        "default": "auto",
                        "tooltip": "auto uses CPU for ComfyUI-core-like reproducibility. cuda falls back to CPU when unavailable.",
                    },
                ),
                "noise_type": (
                    NOISE_TYPES,
                    {
                        "default": "gaussian",
                        "tooltip": "Initial noise distribution. gaussian with auto device and strength 1.0 matches ComfyUI core noise.",
                    },
                ),
                "noise_strength": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 5.0,
                        "step": 0.01,
                        "tooltip": "Multiplier applied to generated noise. 1.0 keeps the selected noise type unchanged.",
                    },
                ),
                "preview_method": (
                    PREVIEW_METHODS,
                    {
                        "default": "default",
                        "tooltip": "Per-node latent preview override. default follows ComfyUI; latent2rgb is lightweight; none disables previews.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("LATENT", "LATENT", "INT")
    RETURN_NAMES = ("output", "denoised_output", "seed")
    FUNCTION = "sample"
    CATEGORY = "Nukun/Sampling"
    DESCRIPTION = "SamplerCustomAdvanced-style node with integrated CPU/CUDA noise control and a seed output."

    def sample(
        self,
        guider,
        sampler,
        sigmas,
        latent_image,
        add_noise,
        noise_seed,
        noise_device,
        noise_type="gaussian",
        noise_strength=1.0,
        preview_method="default",
    ):
        if add_noise:
            noise = NukunRandomNoise(noise_seed, noise_device, noise_type, noise_strength)
        else:
            noise = NukunEmptyNoise()

        return sample_custom_advanced(
            guider,
            sampler,
            sigmas,
            latent_image,
            noise,
            noise_seed,
            preview_method=preview_method,
        )


NODE_CLASS_MAPPINGS = {
    "NukunAdvancedNoiseSampler": NukunAdvancedNoiseSampler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NukunAdvancedNoiseSampler": "Advanced Noise Sampler (Nukun)",
}
