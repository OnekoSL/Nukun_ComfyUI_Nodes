from .noise_sampler_core import (
    MAX_SEED,
    PONY_V7_PROFILES,
    PREVIEW_METHODS,
    NukunCompositeNoise,
    NukunEmptyNoise,
    sample_custom_advanced,
)


class NukunPonyV7CompositeNoise(NukunCompositeNoise):
    def __init__(self, seed, noise_device, v7_profile="stage1_gaussian", noise_strength=0.55, detail_bias=0.35):
        super().__init__(
            seed,
            noise_device,
            "pony_v7",
            v7_profile,
            noise_strength,
            detail_bias,
        )
        self.v7_profile = v7_profile


class NukunPonyV7NoiseSampler:
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
                        "tooltip": "Generate Pony v7-oriented composite noise. Disable this to sample with zero noise.",
                    },
                ),
                "noise_seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": MAX_SEED,
                        "control_after_generate": True,
                        "tooltip": "Seed used for all Pony v7 noise components.",
                    },
                ),
                "noise_device": (
                    ["auto", "cpu", "cuda"],
                    {
                        "default": "auto",
                        "tooltip": "auto uses CPU for ComfyUI-core-like reproducibility. cuda falls back to CPU when unavailable.",
                    },
                ),
                "v7_profile": (
                    PONY_V7_PROFILES,
                    {
                        "default": "stage1_gaussian",
                        "tooltip": "Pony v7 noise recipe. stage1_gaussian is the stable first pass; stage2_violet is tuned for the refine pass.",
                    },
                ),
                "noise_strength": (
                    "FLOAT",
                    {
                        "default": 0.55,
                        "min": 0.0,
                        "max": 3.0,
                        "step": 0.01,
                        "tooltip": "Final multiplier after Pony v7 composite noise normalization.",
                    },
                ),
                "detail_bias": (
                    "FLOAT",
                    {
                        "default": 0.35,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                        "tooltip": "Lower values emphasize larger forms; higher values emphasize texture, color, and line variation.",
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
    DESCRIPTION = "SamplerCustomAdvanced-style node with Pony v7-oriented low-strength composite initial noise."

    def sample(
        self,
        guider,
        sampler,
        sigmas,
        latent_image,
        add_noise,
        noise_seed,
        noise_device,
        v7_profile="stage1_gaussian",
        noise_strength=0.55,
        detail_bias=0.35,
        preview_method="default",
    ):
        if add_noise:
            noise = NukunPonyV7CompositeNoise(
                noise_seed,
                noise_device,
                v7_profile,
                noise_strength,
                detail_bias,
            )
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
    "NukunPonyV7NoiseSampler": NukunPonyV7NoiseSampler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NukunPonyV7NoiseSampler": "Pony V7 Noise Sampler (Nukun)",
}
