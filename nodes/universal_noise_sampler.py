from .noise_sampler_core import (
    MAX_SEED,
    UNIVERSAL_NOISE_PROFILES,
    NukunEmptyNoise,
    make_noise_generator,
    sample_custom_advanced,
)


class NukunUniversalNoiseSampler:
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
                        "tooltip": "Generate noise from the selected Nukun profile. Disable this to sample with zero noise.",
                    },
                ),
                "noise_seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": MAX_SEED,
                        "control_after_generate": True,
                        "tooltip": "Seed used for the selected noise profile.",
                    },
                ),
                "noise_device": (
                    ["auto", "cpu", "cuda"],
                    {
                        "default": "auto",
                        "tooltip": "auto uses CPU for ComfyUI-core-like reproducibility. cuda falls back to CPU when unavailable.",
                    },
                ),
                "noise_profile": (
                    UNIVERSAL_NOISE_PROFILES,
                    {
                        "default": "gaussian",
                        "tooltip": "Basic noise type or composite Nukun profile.",
                    },
                ),
                "noise_strength": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 5.0,
                        "step": 0.01,
                        "tooltip": "Final noise multiplier. For gaussian + auto, 1.0 keeps ComfyUI-core-like behavior.",
                    },
                ),
                "detail_bias": (
                    "FLOAT",
                    {
                        "default": 0.35,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                        "tooltip": "Only affects composite profiles. Lower values emphasize larger forms; higher values emphasize details.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("LATENT", "LATENT", "INT")
    RETURN_NAMES = ("output", "denoised_output", "seed")
    FUNCTION = "sample"
    CATEGORY = "Nukun/Sampling"
    DESCRIPTION = "SamplerCustomAdvanced-style node with all Nukun basic and composite noise profiles."

    def sample(
        self,
        guider,
        sampler,
        sigmas,
        latent_image,
        add_noise,
        noise_seed,
        noise_device,
        noise_profile="gaussian",
        noise_strength=1.0,
        detail_bias=0.35,
    ):
        if add_noise:
            noise = make_noise_generator(noise_seed, noise_device, noise_profile, noise_strength, detail_bias)
        else:
            noise = NukunEmptyNoise()

        return sample_custom_advanced(guider, sampler, sigmas, latent_image, noise, noise_seed)


NODE_CLASS_MAPPINGS = {
    "NukunUniversalNoiseSampler": NukunUniversalNoiseSampler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NukunUniversalNoiseSampler": "Universal Noise Sampler (Nukun)",
}
