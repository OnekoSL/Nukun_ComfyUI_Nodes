from .noise_sampler_core import (
    ILLUSTRIOUS_MODES as VARIATION_MODES,
    MAX_SEED,
    NukunCompositeNoise,
    NukunEmptyNoise,
    sample_custom_advanced,
)


class NukunIllustriousCompositeNoise(NukunCompositeNoise):
    def __init__(self, seed, noise_device, variation_mode="balanced", variation_strength=1.0, detail_bias=0.35):
        super().__init__(
            seed,
            noise_device,
            "illustrious",
            variation_mode,
            variation_strength,
            detail_bias,
        )
        self.variation_mode = variation_mode
        self.variation_strength = variation_strength


class NukunIllustriousNoiseSampler:
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
                        "tooltip": "Generate composite IllustriousXL noise. Disable this to sample with zero noise.",
                    },
                ),
                "noise_seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": MAX_SEED,
                        "control_after_generate": True,
                        "tooltip": "Base seed used for all composite noise components.",
                    },
                ),
                "noise_device": (
                    ["auto", "cpu", "cuda"],
                    {
                        "default": "auto",
                        "tooltip": "auto uses CPU for ComfyUI-core-like reproducibility. cuda falls back to CPU when unavailable.",
                    },
                ),
                "variation_mode": (
                    VARIATION_MODES,
                    {
                        "default": "balanced",
                        "tooltip": "Composite noise recipe tuned for IllustriousXL variation.",
                    },
                ),
                "variation_strength": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 3.0,
                        "step": 0.01,
                        "tooltip": "Final multiplier after composite noise normalization.",
                    },
                ),
                "detail_bias": (
                    "FLOAT",
                    {
                        "default": 0.35,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                        "tooltip": "Lower values emphasize larger forms; higher values emphasize texture and micro detail.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("LATENT", "LATENT", "INT")
    RETURN_NAMES = ("output", "denoised_output", "seed")
    FUNCTION = "sample"
    CATEGORY = "Nukun/Sampling"
    DESCRIPTION = "SamplerCustomAdvanced-style node with IllustriousXL-oriented composite initial noise."

    def sample(
        self,
        guider,
        sampler,
        sigmas,
        latent_image,
        add_noise,
        noise_seed,
        noise_device,
        variation_mode="balanced",
        variation_strength=1.0,
        detail_bias=0.35,
    ):
        if add_noise:
            noise = NukunIllustriousCompositeNoise(
                noise_seed,
                noise_device,
                variation_mode,
                variation_strength,
                detail_bias,
            )
        else:
            noise = NukunEmptyNoise()

        return sample_custom_advanced(guider, sampler, sigmas, latent_image, noise, noise_seed)


NODE_CLASS_MAPPINGS = {
    "NukunIllustriousNoiseSampler": NukunIllustriousNoiseSampler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NukunIllustriousNoiseSampler": "Illustrious Noise Sampler (Nukun)",
}
