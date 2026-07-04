# Nukun ComfyUI Example Workflows

These workflows are curated examples for the current Nukun node set. They are copied into `ComfyUI/user/default/workflows` for direct local use and kept here so the node repository can document them. The main examples are core-first and avoid optional custom-node dependencies.

## Workflows

- `nukun_example_01_basic_loader_universal_sampler.json` - basic text-to-image graph using `NukunCheckpointCyclerLoader` and `NukunUniversalNoiseSampler`.
- `nukun_example_02_regional_split_native_conditioning.json` - three horizontal regions with `NukunRegionalPromptEncoder` and core masked conditioning metadata.
- `nukun_example_03_regional_rect_native_conditioning.json` - three rectangular native conditioning regions with soft mask edges.
- `nukun_example_04_hiresfix_tiled.json` - optional companion example with first-pass generation followed by `NukunHiResFixTiled`.
- `nukun_example_05_unet_block_noise_lab.json` - baseline versus conservative `NukunUNetBlockNoisePatch` branch using `NukunCheckpointPairCyclerLoader`.
- `nukun_example_06_controlled_noise_stages_unet_patch.json` - three ranged `Universal Noise Sampler Advanced` passes with mild UNet block noise modulation. This is a creative reinjection workflow, not an equivalence test: later passes intentionally add fresh low-strength noise for staged texture changes. It is the best starting point for trying expanded profiles such as `pyramid_mix`, `green_test`, `rainbow_mild`, and `wavelet` at controlled strengths.
- `nukun_example_07_simple_universal_ksampler.json` - simple text-to-image graph using `Universal KSampler (Nukun)` so users do not need to wire `CFGGuider`, `KSamplerSelect`, or `BasicScheduler` by hand.

## Optional Companion Nodes

The tiled HiResFix example requires `ComfyUI_UltimateSDUpscale` and an installed upscale model. DenseDiffusion wrapper nodes are still included in the package for older or advanced workflows, but the regional examples here use the dependency-free native regional conditioning nodes. The local defaults use `A_pony`, `B_pony_7`, `OmniSR_X2_DIV2K.safetensors`, and `2x-AnimeSharpV4_RCAN.safetensors` where appropriate.

The examples avoid removed or stale node types such as `NukunSeedOrchestrator`.
