# Changelog

## v0.6.0

- Added a Wan 2.2 TI2V-5B toolkit with validated video settings, cable-free T2V/I2V latent switching, proportional image preparation, and reproducible run manifests.
- Added the `wan2_2_video` Ollama profile with temporal action, camera, environment, and video-artifact guidance.
- Added the 16 GB `wan2.2_video_toolkit.json` workflow, MP4 export, tiled VAE decode, sampling comparison notes, and Wan-specific unit coverage.
- Added the separate `anima_to_wan2.2_i2v.json` pipeline with an Anima keyframe, JoyCaption visual bridge, editable Wan motion instruction, five independent seeds, and verified 17-frame GPU smoke coverage.
- Added iterative Wan continuation planning, JSON records, and final manifests plus an Easy-Use loop that extends the Anima-to-Wan video by 1-10 segments without duplicate transition frames.
- Added a robust segmented Wan continuation path with `NukunWan22SegmentStore`, `NukunWan22SegmentLoader`, and `NukunWan22FrameSequenceAssembler`, plus start/extend/assemble workflows that persist PNG frames and assemble the final MP4 without relying on dynamic loop nodes.
- Added the segmented Wan workflows under `examples/wan22/` so the complete setup is versioned with the custom nodes.
- Added `4-Prompt Model Cycler Loader (Nukun)` for synchronized four-prompt-per-UNET folder cycles with `increment`, `fixed`, and frontend-randomized model-synchronous seed modes.
- Added `4-Prompt Checkpoint Cycler Loader (Nukun)` with the same prompt and seed cycles for normal checkpoints with embedded CLIP and VAE outputs.
- Fixed both 4-prompt cyclers so ComfyUI's automatic seed randomizer is locked to `fixed`; `seed_mode` is now the only seed controller.
- Added `Ollama Vision Captioner (Nukun)` with natural caption, Danbooru tag, Pony source, refiner seed, and HiResFix text outputs.
- Added Anima prompt-refiner support, Anima/Wan workflows, and expanded Anima prompt ordering.
- Added `Pixel Anchored Remaster (Nukun)`, `SPEED Sampler (Nukun)`, sampler preview controls, and `Universal KSampler (Nukun)`.
- Replaced `Multi Vocab String List (Nukun)` direct word selectors with per-slot cursor controls and added the practical vocab usage guide.
- Added Anima2B artist, quality tag, expression style, and hair style vocabulary resources, and normalized bundled CSV entries so entries do not start with spaces.
- Updated `Random Vocab String List (Nukun)` to use the same deduplicated shuffle-bag selection as the multi-vocab node, so incrementing the seed walks non-overlapping blocks before reshuffling.
- Reworked all T5/Qwen, CLIP, and regional sculpt nodes to use exact chunked nearest-token search with automatic CPU fallback, eliminating full FP32 embedding-table VRAM copies such as the 1.45 GiB Krea2/Qwen3-VL allocation spike.

## v0.5.0

- Added `Ollama Prompt Refiner (Nukun)` for local Ollama-based split prompt generation with selectable `pony_v6`, `illustrious`, `pony_v7`, and `z_image` target profiles.
- Added split prompt outputs for `positive`, `negative`, `report`, `base_prompt`, `foreground_prompt`, and `background_prompt`.
- Added Z-Image prompt refining support and bundled prompt-design reference notes.
- Added Qwen-aware conditioning support for the T5 equal-length and sculpt balancer nodes.
- Added `Multi Vocab String List (Nukun)` for combining four selectable vocabulary files with deterministic random fills and optional direct word selectors.
- Added `resources/camera_composition.csv` for camera, framing, focus, perspective, and composition prompt terms.
- Fixed `Ollama Prompt Refiner (Nukun)` model selection so installed Ollama models take priority and the dropdown refreshes from the selected Ollama URL.
- Improved `Ollama Prompt Refiner (Nukun)` for Reka Flash GGUF models with a compact JSON-only prompt wrapper, fixed context-length choices, and stricter reasoning cleanup.
- Improved Pony v6 and Illustrious prompt refining with pre-sorted visual candidates and concrete 30-40 word background tag lists.
- Changed `Ollama Prompt Refiner (Nukun)` to a single-target workflow; older workflows should reconnect to the new shared prompt outputs.

## v0.4.0

- Added deduplicated `little_doom_*.csv` Illustrious LoRA keyword resources and a reproducible generator utility.
- Fixed Little Doom CSV formatting so wrapped source lines do not become embedded line breaks inside resource entries.

## v0.3.0

- Added `Random Vocab String List (Nukun)` for deterministic random word-list prompt strings from `ComfyUI/user/vocab.json`.
- Added an optional `chain` input to `Random Vocab String List (Nukun)` for prompt chaining.
- Added a bundled fallback vocabulary at `resources/vocab.json`.
- Added `resources/english_words.csv` and selectable vocabulary files for `Random Vocab String List (Nukun)`.
- Added categorized vocabulary files for places/environments, objects, `*ing` words, person names, countries, and cities.
- Added categorized vocabulary files for animals and mythical creatures, verbs, nouns, and adjectives.
- Added a browser-side rectangle editor for rectangular regional nodes.
- Added `Tiled HiRes Fix Advanced (Nukun)` for step-ranged tiled HiResFix workflows.
- Added expanded Universal Noise Sampler profiles and `Noise Profile Cycler (Nukun)`.
- Fixed `Noise Profile Cycler (Nukun)` range wrapping.
