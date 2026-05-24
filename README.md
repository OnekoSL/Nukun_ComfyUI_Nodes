# Nukun ComfyUI Nodes

Personal ComfyUI nodes for loaders, prompt/conditioning helpers, regional masks, noise samplers, model patches, and tiled HiResFix workflows.

## Installation

Clone this repository into your ComfyUI `custom_nodes` directory:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/OnekoSL/Nukun_ComfyUI_Nodes.git
```

Restart ComfyUI after installation.

`requirements.txt` lists the small runtime packages imported directly by these nodes. PyTorch is intentionally not listed because ComfyUI manages the correct `torch` build for your hardware.

## Optional companion nodes

Most nodes work with a standard ComfyUI installation. These wrapper nodes need additional custom-node packages when you use them:

- `NukunDenseDiffusionSplitApply` and `NukunDenseDiffusionRectApply` need `comfyui_densediffusion`.
- `NukunHiResFixTiled` needs `ComfyUI_UltimateSDUpscale`.
- `NukunRegionalSplitRegions` outputs regions compatible with A8R8 `Attention Couple`.

## Included nodes

- `NukunCheckpointCyclerLoader` - display name `Checkpoint Cycler Loader (Nukun)`, category `Nukun/Loaders`
- `NukunCheckpointVaeCyclerLoader` - display name `Checkpoint + VAE Cycler Loader (Nukun)`, category `Nukun/Loaders`
- `NukunCheckpointPairCyclerLoader` - display name `Checkpoint Pair Cycler Loader (Nukun)`, category `Nukun/Loaders`
- `NukunIncrementingIntString` - display name `Incrementing Int to String (Nukun)`, category `Nukun/Text`
- `LoadImagewithSubfolders` - display name `Load Image with Subfolders`, category `Nukun/Image`
- `T5Balancer` - display name `T5 Token-based Prompt Balancer`, category `Nukun/Conditioning`
- `NukunT5EqualLengthBalancer` - display name `T5 Equal-Length Prompt Balancer (Nukun)`, category `Nukun/Conditioning`
- `NukunT5SculptEqualLengthBalancer` - display name `T5 Sculpt Equal-Length Prompt Balancer (Nukun)`, category `Nukun/Conditioning`
- `NukunCLIPSculptTextEncode` - display name `CLIP Sculpt Text Encode (Nukun)`, category `Nukun/Conditioning`
- `NukunConditioningSlerp` - display name `Conditioning Slerp (Nukun)`, category `Nukun/Conditioning`
- `NukunConditioningAverageKeepMagnitude` - display name `Conditioning Average Keep Magnitude (Nukun)`, category `Nukun/Conditioning`
- `NukunConditioningNormalizeMagnitudeToEmpty` - display name `Conditioning Normalize Magnitude To Empty (Nukun)`, category `Nukun/Conditioning`
- `NukunConditioningSDXLMergeClipGL` - display name `Conditioning SDXL Merge CLIP G/L (Nukun)`, category `Nukun/Conditioning`
- `NukunConditioningAnalyzer` - display name `Conditioning Analyzer (Nukun)`, category `Nukun/Conditioning`
- `NukunConditioningAdjust` - display name `Conditioning Adjust (Nukun)`, category `Nukun/Conditioning`
- `NukunRegionalPromptEncoder` - display name `Regional Prompt Encoder (Nukun)`, category `Nukun/Conditioning`
- `NukunRegionalSculptPromptEncoder` - display name `Regional Sculpt Prompt Encoder (Nukun)`, category `Nukun/Conditioning`
- `NukunSplitMasks` - display name `Split Masks (Nukun)`, category `Nukun/Mask`
- `NukunRegionalRectMasks` - display name `Regional Rect Masks (Nukun)`, category `Nukun/Mask`
- `NukunDenseDiffusionSplitApply` - display name `DenseDiffusion Split Apply (Nukun)`, category `Nukun/Conditioning`
- `NukunDenseDiffusionRectApply` - display name `DenseDiffusion Rect Apply (Nukun)`, category `Nukun/Conditioning`
- `NukunRegionalSplitRegions` - display name `Regional Split Regions (Nukun)`, category `Nukun/Conditioning`
- `SaveImageWebsocket` - display name `Save Image (Websocket)`, category `Nukun/Image`
- `NukunAdvancedNoiseSampler` - display name `Advanced Noise Sampler (Nukun)`, category `Nukun/Sampling`
- `NukunIllustriousNoiseSampler` - display name `Illustrious Noise Sampler (Nukun)`, category `Nukun/Sampling`
- `NukunPonyV7NoiseSampler` - display name `Pony V7 Noise Sampler (Nukun)`, category `Nukun/Sampling`
- `NukunUniversalNoiseSampler` - display name `Universal Noise Sampler (Nukun)`, category `Nukun/Sampling`
- `NukunUNetBlockNoisePatch` - display name `UNet Block Noise Patch (Nukun)`, category `Nukun/Model Patches`
- `NukunHiResFixTiled` - display name `HiResFix Tiled (Nukun)`, category `Nukun/Sampling`

## Checkpoint Cycler Loader

This node replaces the common `PrimitiveNode` plus `Checkpoint Loader w/Name (WLSH)` pattern.
It loads the selected checkpoint, exposes `MODEL`, `CLIP`, `VAE`, a clean `modelname`, the full `ckpt_name`, and the checkpoint `folder`.
The `ckpt_name` combo has ComfyUI's control-after-generate support enabled for increment, decrement, randomize, and wrap behavior in the frontend.

## Checkpoint + VAE Cycler Loader

This node combines `Checkpoint Cycler Loader (Nukun)` with ComfyUI's native `Load VAE` behavior.
Use `vae_name = checkpoint` to keep the VAE embedded in the selected checkpoint, or choose an external VAE to override only the VAE output while keeping the same `MODEL`, `CLIP`, and metadata outputs.

## Checkpoint Pair Cycler Loader

This node loads two checkpoints from one selected checkpoint subfolder as an ordered all-with-all matrix.
Use one incrementing `pair_index`: `MODEL_2` advances fastest, while `MODEL_1` advances after each full folder pass.
The matrix includes self-pairs and reversed pairs, so `A x A`, `A x B`, and `B x A` are all generated.
Use `model_index_start` and `model_index_end` to restrict the matrix to an inclusive global model index range, for example `20..49`.
For chunked runs, set `pair_index` to `increment-wrap` and wrap it over the reduced `total_pairs` value.
`combined_modelname` outputs a filename-friendly `modelname_1__x__modelname_2` string for save prefixes.
Use `vae_name = checkpoint` to keep the VAE from `MODEL_2`, or select an external VAE to override the shared VAE output.

## Incrementing Int to String

This node replaces the common `Int` plus `Int to String (Mikey)` pattern.
It exposes one integer widget with ComfyUI's control-after-generate support and outputs a plain string without a commas toggle.
`min_value` and `max_value` define the output cycle, so incrementing values wrap around in a predictable range.

## Regional Split Regions

This node creates simple horizontal or vertical 2/3-way split masks and returns A8R8 `AttentionCouple` compatible regions.
Connect `regions` directly to A8R8 `Attention Couple`, and optionally preview `mask_1`, `mask_2`, and `mask_3`.
For `region_count = 2`, `positive_3`, `split_2`, and `weight_3` are ignored and `mask_3` is an empty mask.

## T5 Equal-Length Prompt Balancer

This node is a safer Pony v7/AuraFlow-oriented prompt encoder than the legacy `T5Balancer`.
It detects the active T5 token stream, measures positive and negative prompts without padding, then encodes both prompts with a shared effective token length.
The effective length is `max(target, positive_raw_tokens, negative_raw_tokens)`, so long prompts are preserved instead of truncated.
It also outputs raw token counts, the effective target, and a short text report for prompt tuning.

## T5 Sculpt Equal-Length Prompt Balancer

This experimental node keeps the equal-length T5 prompt encoding behavior, then optionally replaces eligible token IDs with sculpted T5 embedding vectors before scheduled encoding.
It skips special/padded tokens, caches repeated token IDs per branch, and limits nearest-vector search with `top_k`.
The defaults are mildly active for the positive prompt and normalization-only for the negative prompt, so compare against `T5 Equal-Length Prompt Balancer (Nukun)` before increasing intensity.

## CLIP Sculpt Text Encode

This SD1/SDXL CLIP node is the Nukun-native replacement for the old external `CLIP Vector Sculptor text encode`.
It tokenizes text, skips special and precomputed embedding tokens, sculpts eligible CLIP token vectors with cached `top_k` nearest-vector search, then encodes with ComfyUI's scheduled CLIP path.
The old `Vector_Sculptor_ComfyUI` package is not patched, so older workflows can still load while new workflows can use `CLIP Sculpt Text Encode (Nukun)`.
The companion conditioning nodes provide Nukun versions of slerp, average-keep-magnitude, normalize-to-empty, and SDXL CLIP G/L merge.

## Conditioning Analyzer and Adjust

`Conditioning Analyzer (Nukun)` passes conditioning through unchanged and returns a text report with entry count, tensor shapes, dtype/device, metadata keys, pooled-output presence, token count, channel count, token-norm stats, and NaN/Inf checks.
Use it before and after experimental nodes such as Capitan Advanced Enhancer to see what changed numerically.

`Conditioning Adjust (Nukun)` is a deterministic, preset-based conditioner for gentle Pony v7/T5 and SDXL/Pony v6 experiments.
It does not use random MLPs, attention layers, or external Capitan code.
Presets are `neutral_report_only`, `literal_detail`, `soft_balance`, `contrast_pop`, and `negative_tamer`.
`model_profile` can be left on `auto`, or set explicitly to `t5`, `sdxl_clip`, or `sd15_clip`.
Auto mode uses conservative profile scaling for older CLIP conditionings, so SDXL/Pony v6 gets a milder detail push than T5.
Keep `preserve_magnitude` enabled for safer comparisons on the same seed.

Recommended starting points:

- Pony v7/T5 positive: `literal_detail` or `soft_balance`, `model_profile = auto`, `strength = 0.5..1.0`.
- Pony v7/T5 negative: `negative_tamer`, `model_profile = auto`, `strength = 0.5..1.0`.
- SDXL/Pony v6 positive: `soft_balance`, `model_profile = auto` or `sdxl_clip`, `strength = 0.4..0.8`.
- SD1.5 positive: `soft_balance`, `model_profile = auto` or `sd15_clip`, `strength = 0.3..0.7`.
- Diagnostics only: `neutral_report_only` or `Conditioning Analyzer (Nukun)`.

## Regional Prompt Encoder

This node combines one `base_prompt` with 2/3 region prompts and encodes them with CLIP.
It replaces repeated `BetterString` plus text-concatenate plus `CLIPTextEncode` chains in regional workflows.
Use `conditioning_1..3` for regional nodes, and `base_conditioning` when a separate full-scene conditioning is needed.
The regional conditionings are encoded from exactly `base_prompt + separator + region_n`, without hidden position or cast text.
The `hiresfix_conditioning` output is encoded from all active text boxes plus `hiresfix_prompt`, so the upscale/detail pass can use the full scene and an explicit polish prompt.

## Regional Sculpt Prompt Encoder

This experimental SDXL/CLIP node keeps the same text assembly as `Regional Prompt Encoder (Nukun)`, then applies local Vector-Sculptor-style token embedding edits to the regional and HiRes conditionings.
`base_conditioning` remains unsculpted as a stable global reference, and `conditioning_3` remains the unsculpted base fallback when `region_count = 2`.
Use it when a regional workflow currently needs separate `CLIP Vector Sculptor text encode` chains after prompt composition.
The defaults are mildly active: `forward`, intensity `0.5`, and `mean` token normalization.

## Split Masks

This node creates simple horizontal or vertical 2/3-way split masks from `width` and `height` inputs.
Use it when a workflow only needs masks, for example RES4LYF regional conditioning or native `ConditioningSetMask` workflows.
For `region_count = 2`, `split_2` is ignored and `mask_3` is an empty mask.
`overlap` expands neighboring regions around the split boundary when soft overlap is useful.

## Regional Rect Masks

This node creates 2/3 freely placed rectangular masks from percentage coordinates.
Each region has `x`, `y`, `w`, and `h` controls in the 0.0-1.0 image range.
Use `soft_edge` to blur rectangle edges, and preview `mask_1..3` to tune placement visually.

## DenseDiffusion Split Apply

This node wraps `Split Masks`, multiple `DenseDiffusion Add Cond` nodes, and `DenseDiffusion Apply` into one node.
Connect the patched `model` output to the sampler model path and the `conditioning` output to the positive conditioning path.
For `region_count = 2`, `conditioning_3`, `split_2`, and `strength_3` are ignored and `mask_3` is an empty mask.

## DenseDiffusion Rect Apply

This node wraps `Regional Rect Masks`, multiple `DenseDiffusion Add Cond` nodes, and `DenseDiffusion Apply` into one node.
Use it instead of `DenseDiffusion Split Apply` when the regional areas should be freely positioned rectangles instead of full-height or full-width splits.
For DenseDiffusion safety, uncovered pixels are internally assigned to all active region masks so empty attention areas do not produce black/NaN images.

## Advanced Noise Sampler

This node replaces `RandomNoise` plus `SamplerCustomAdvanced` with one sampler node.
It accepts `guider`, `sampler`, `sigmas`, and `latent_image`, then generates random or zero initial noise internally.
`noise_device = auto` keeps ComfyUI-core-like CPU noise behavior, while `cuda` uses CUDA when available and falls back to CPU otherwise.
`noise_type` supports `gaussian`, `uniform`, `laplacian`, `pink`, `brown`, `blue`, `violet`, `pyramid`, and `perlin`.
Use `noise_strength` as a multiplier for the generated noise; `gaussian` + `auto` + `1.0` is the stable ComfyUI-compatible default.
Disabling `add_noise` still produces zero noise and ignores the selected noise type.
The `seed` output exposes the final `noise_seed` value for filenames, logging, or downstream helper nodes.

## Illustrious Noise Sampler

This node is a compact sampler for IllustriousXL-style experiments where more initial-noise variation is useful than plain Gaussian noise.
It keeps the same `guider`, `sampler`, `sigmas`, `latent_image`, zero-noise, seed output, preview callback, `noise_mask`, and batch behavior as `Advanced Noise Sampler`.
Instead of a single `noise_type`, it builds normalized composite noise from Nukun noise components.
`variation_mode` offers `balanced`, `texture`, `composition`, and `wild`; `variation_strength` scales the final composite, and `detail_bias` shifts the recipe toward larger forms or more micro-detail.
For IllustriousXL, prefer this sampler before trying `UNet Block Noise Patch`, which is stronger and more model-sensitive.

## Pony V7 Noise Sampler

This node is a Pony v7-oriented drop-in sampler based on the same sampling behavior as `Advanced Noise Sampler`.
It uses normalized composite noise recipes like `Illustrious Noise Sampler`, but the defaults are tuned for lower noise energy.
Use `stage1_gaussian` around `0.55` for the first pass and `stage2_violet` around `0.50` for the refine pass.
Additional profiles are `balanced`, `soft`, and `graphic`; `detail_bias` shifts the recipe toward larger forms or more texture and line variation.
The node keeps zero-noise mode, CPU/CUDA noise selection, nested latent support, `batch_index`, preview callback, `noise_mask`, `denoised_output`, and the seed output.

## Universal Noise Sampler

This node is the preferred combined sampler for new Nukun workflows.
It keeps the same sampler behavior and outputs as the other Nukun sampler nodes, but exposes all basic and composite profiles through one `noise_profile` combo.
Basic profiles are `gaussian`, `uniform`, `laplacian`, `pink`, `brown`, `blue`, `violet`, `pyramid`, and `perlin`.
Composite profiles include `illustrious_balanced`, `illustrious_texture`, `illustrious_composition`, `illustrious_wild`, plus `pony_v7_stage1_gaussian`, `pony_v7_stage2_violet`, `pony_v7_balanced`, `pony_v7_soft`, and `pony_v7_graphic`.
`noise_strength` scales every profile; `detail_bias` only affects composite profiles.
Use `gaussian` + `auto` + `1.0` for the stable ComfyUI-core-like baseline, or Pony v7 profiles around `0.55` and `0.50` for the two-pass Pony v7 workflow.

## UNet Block Noise Patch

This experimental model patch injects separate noise into UNet `input`, `middle`, and `output` block groups.
Use it on the `MODEL` path before the guider or sampler, while `Advanced Noise Sampler` still controls the initial latent noise.
Each group has its own noise type, strength, and seed; the default strengths are zero so adding the patch starts neutral.
Block noise strength is relative to the current feature magnitude, so small values are meant as gentle perturbations rather than latent-noise scale values.
Input and output strengths are spread across their repeated UNet blocks, while middle strength applies to its single block group pass.
`start_percent` and `end_percent` constrain the effect during denoising, and noise varies reproducibly per block and sigma step.

## HiResFix Tiled

This node wraps model upscaling, optional `ReferenceLatent`, optional `DifferentialDiffusion`, and `Ultimate SD Upscale (No Upscale)` into one compact tiled HiResFix step.
It takes an `UPSCALE_MODEL` input, uses the model's native scale through ComfyUI's `ImageUpscaleWithModel`, then refines the upscaled image with tiled img2img.
The defaults mirror the local Pony v7 tiled workflow: `steps=20`, `cfg=3.5`, `denoise=0.4`, `tile_width=1024`, `tile_height=1024`, `mask_blur=64`, `tile_padding=192`, reference latent enabled, differential diffusion enabled at `0.7`, and tiled decode enabled.
It also supports Universal Noise Sampler profiles for tiled refinement through `noise_profile`, `noise_strength`, and `detail_bias`.
The older `noise_type` widget remains for compatibility; if `noise_profile` is left at `gaussian`, legacy `noise_type` values such as `blue` or `violet` are still honored.
Use `gaussian` + `auto` + `1.0` for ComfyUI-compatible tile noise, or try `pony_v7_stage2_violet`, `illustrious_texture`, `pyramid`, `pink`, or `perlin` for more textured HiResFix redraws.
The outputs are the final refined image, the raw upscaled image, and the seed.

## Maintenance rules

- Keep public node IDs stable so saved workflows continue to load.
- Add new personal nodes under `nodes/` and export them from `__init__.py`.
- Keep `torch`, `comfy`, `folder_paths`, `latent_preview`, and other ComfyUI internals out of `requirements.txt`.
- Do not store models, LoRAs, VAEs, outputs, or workflows in this folder.

## Test after changes

Restart ComfyUI and check `/object_info` for the expected node IDs. For Pony v7 workflows, verify that `T5Balancer` still appears before moving or disabling older copies.
