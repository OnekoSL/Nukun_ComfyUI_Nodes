# Nukun ComfyUI Example Workflows

These workflows are curated examples for the current Nukun node set. They are copied into `ComfyUI/user/default/workflows` for direct local use and kept here so the node repository can document them.

## Workflows

- `nukun_example_01_basic_loader_universal_sampler.json` - basic text-to-image graph using `NukunCheckpointCyclerLoader` and `NukunUniversalNoiseSampler`.
- `nukun_example_02_regional_split_densediffusion.json` - three horizontal regions with `NukunRegionalPromptEncoder` and `NukunDenseDiffusionSplitApply`.
- `nukun_example_03_regional_rect_densediffusion.json` - three rectangular DenseDiffusion regions with soft mask edges.
- `nukun_example_04_hiresfix_tiled.json` - first-pass generation followed by `NukunHiResFixTiled` with a local upscale model.
- `nukun_example_05_unet_block_noise_lab.json` - baseline versus conservative `NukunUNetBlockNoisePatch` branch using `NukunCheckpointPairCyclerLoader`.

## Optional Companion Nodes

The DenseDiffusion examples require `comfyui_densediffusion`. The tiled HiResFix example requires `ComfyUI_UltimateSDUpscale` and an installed upscale model. The local defaults use `A_pony`, `B_pony_7`, `OmniSR_X2_DIV2K.safetensors`, and `2x-AnimeSharpV4_RCAN.safetensors` where appropriate.

The examples avoid removed or stale node types such as `NukunSeedOrchestrator`.
