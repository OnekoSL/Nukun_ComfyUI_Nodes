# Wan 2.2 TI2V-5B workflow analysis

This document records the modernization of `pysssss-workflows/wan2.2_video.json` for an RTX 4060 Ti with 16 GB VRAM. The original file remains unchanged; the replacement is [wan2.2_video_toolkit.json](../../pysssss-workflows/wan2.2_video_toolkit.json).

## Findings in the original workflow

- `21` frames at `16` FPS produce only 1.3125 seconds of playback, while the prompt asks for five seconds. Wan frame counts must satisfy `4n+1`; five requested seconds now produce `81` frames.
- `ImageScale` forces every source image to `704x1056` with crop disabled. This changes arbitrary aspect ratios and contradicts the workflow note recommending `1280x704`.
- The connected `LoadImage` means the graph is always I2V until the cable is removed manually. The replacement keeps the cable and uses an explicit `text_to_video` or `image_to_video` mode.
- Sampling values were embedded in one `KSampler`, so controlled comparisons were awkward and the run metadata did not state which experimental preset was used.
- `SaveAnimatedWEBP` was the primary export and `SaveImage` wrote every decoded frame separately. Core `CreateVideo` and `SaveVideo` now provide the primary H.264 MP4 output.
- There was no validation for dimensions, duration, missing I2V images, incorrect VAE latent channels, or reproducibility metadata.

## Target architecture

The replacement deliberately keeps the locally installed `wan2.2_ti2v_5B_fp16` model. The installed Wan 14B Lightning LoRAs are not used because their matching high- and low-noise 14B diffusion models are absent and would be substantially heavier on 16 GB VRAM.

`NukunWan22VideoSettings` owns mode, resolution, orientation, requested duration, FPS, and Wan frame rounding. Presets are:

| Quality | Landscape | Portrait | Square |
| --- | --- | --- | --- |
| Draft | 640x352 | 352x640 | 512x512 |
| Balanced | 960x544 | 544x960 | 704x704 |
| Quality | 1280x704 | 704x1280 | 896x896 |

Custom dimensions are snapped to multiples of 32. `NukunWan22TI2VLatent` ignores a connected image in T2V mode, requires one in I2V mode, and prepares it with proportional center crop or padding. It reproduces the Core Wan 2.2 48-channel latent and noise-mask behavior.

The mandatory Ollama stage uses the `wan2_2_video` profile. It separates subject/action, environment, and camera/style guidance while adding video-specific negatives for flicker, temporal jitter, identity drift, frozen or abrupt motion, inconsistent limbs, camera shake, text, and compression artifacts. An unreachable Ollama endpoint stops the graph with a clear error.

`NukunWan22RunManifest` receives the actual connected seeds and sampling parameters. It emits stable JSON plus a filename-safe prefix used by `SaveVideo`; the normal ComfyUI workflow metadata remains embedded as well.

## Sampling matrix

These are controlled A/B starting points, not universal quality guarantees. Keep prompt, model, dimensions, duration, prompt seed, and sampling seed fixed when comparing them.

| Profile | Steps | CFG | Sampler | Scheduler | Shift |
| --- | ---: | ---: | --- | --- | ---: |
| Draft | 12 | 5 | `euler` | `linear_quadratic` | 5 |
| Balanced (workflow default) | 25 | 5 | `dpmpp_2m` | `bong_tangent` | 8 |
| Quality | 35 | 5 | `dpmpp_2m` | `beta57` | 8 |

The workflow uses rgthree seed and KSampler configuration nodes so the sampler and manifest share the same values. SageAttention remains an optional launch-level benchmark rather than a quality assumption. WanMove, WanDancer, Camera, VACE, Fun Control, and similar Core nodes require specialized compatible models and therefore belong in separate future workflows.

## Verification

- Unit tests cover presets, portrait/square/custom dimensions, `4n+1` rounding, T2V image bypass, I2V validation, crop/pad sizing, 48-channel latent shapes, noise masks, manifest output, Wan prompt ordering, video negatives, and hard Ollama connection errors.
- Fast smoke target: Draft, `640x352`, `17` frames.
- Acceptance target: Balanced, `960x544`, five requested seconds, `81` frames, H.264 MP4 output.
- Full model generation remains a manual GPU acceptance test because it is long-running and writes a large external output file.
