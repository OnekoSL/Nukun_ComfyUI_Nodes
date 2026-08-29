# Changelog

## Unreleased

## v0.8.0

- Enabled actual reasoning for Ollama models advertised with the `thinking` capability and for Reka Flash's inline `<reasoning>` format by removing the conflicting JSON grammar only on those paths, stripping reasoning before validation, and reserving a larger output-token budget. Reka Flash also receives its recommended `top_k = 1024`.
- Grounded Reka's unconstrained final answer with the complete JSON schema and recover harmless stringified planner/reviewer list fields locally instead of abandoning a long pipeline run.
- Capped requested Reka reasoning at 400 tokens so slow Q4 builds retain enough generation budget to reach their final JSON.
- Kept reasoning on Reka compiler/correction work but switched planner and reviewer classification stages to fast schema-constrained JSON so Q4 models cannot exhaust those stages in an unbounded reasoning trace.
- Switched Reka Flash generation for Krea2, Z-Image, Wan 2.2, and Pony v7 to schema-constrained 900-token output after local Q4 tests showed faster, more reliable profile-compliant prompts than compiler reasoning.
- Added a `prompt_mode` switch: `strict` preserves the source-grounded behavior, while `creative` allows coherent supporting details and broadens sampling without relaxing fixed style or spatial requirements.

- Added `ACE Song Variation Director (Nukun)` for Ollama-guided ACE-Step arrangement and lyric variations with independent musical controls, exact must-keep phrases, bounded JSON repair, and source-preserving fallback.
- Added `ACE Song Timeline Conditioning (Nukun)` for section-aware time-regional ACE-Step 1.5 conditioning with automatic or explicit durations, transition masks, timeline JSON, and allocation diagnostics.
- Added `Audio Timeline Mixer 5 (Nukun)` for offsetting and mixing up to five audio tracks with per-track gain and fades, resampling, channel normalization, master gain, and configurable peak protection.
- Fixed linked `control after generate` selectors in `Multi Vocab String List (Nukun)` and `MiniMax H3 Prompt Builder (Nukun)`. Multi Vocab now declares four distinct server-side control prefixes so the fix is independent of frontend extensions and browser caches; the H3 builder uses browser-side identities without changing its serialized text-field layout.
- Fixed pre-quoted multi-speaker dialogue in the MiniMax H3 builder so individual spoken lines are no longer wrapped in invalid nested quotes; the Video Refiner now also restores exact multi-speaker quotes locally when Ollama alters or drops them. H3 compilation targets approximately 100 focused words per section, accepts 60 or more without an upper limit, disables thinking for schema reliability, raises the completion budget, and keeps creative underlength JSON in `adaptive` mode instead of reverting to translated source text.
- Added `Ollama Video Prompt Refiner (Nukun)` for MiniMax H3 and Wan 2.2 with six connectable source sections, protected quoted dialogue, structured H3 assembly, Wan single-shot assembly, optional semantic review/correction, and source-preserving fallbacks.
- Added `faithful`, `balanced`, and `cinematic` creativity modes to the Video Refiner; balanced now requires a substantive production rewrite and untranslated German prose triggers JSON repair while quoted dialogue remains untouched.
- Split German video-source translation into a dedicated protected stage and added automatic repair for missing, short, or untranslated MiniMax H3 compiler output.
- Added `MiniMax H3 Prompt Builder (Nukun)` with six structured Scene/Character/Action/Camera/Visual Style/Audio sections, independent deterministic vocabulary cursors, fixed-text fields, and exact spoken-dialogue guidance for Action and Audio.
- Added six curated MiniMax H3 vocabulary resources with 80 prompt-ready Scene, Character, Action, Camera, Visual Style, and Audio phrases each and selected them as the builder's section defaults.
- Prevented Anima and Krea2 compiler prompts from leaking static example subjects, replaced a failed planner with a source-grounded local plan in `continue` mode, exposed the planner error in `plan_json`, normalized contradictory reviewer flags, and locally rebuilt results whose planned subject is still missing after correction.
- Made both Ollama nodes default to a 4096-token context and automatically unload their selected model after the complete node run, with an optional `unload_after_run` switch for prompt-only workflows that prefer a warm model.
- Added optional `plan_compile` and `plan_compile_review` Ollama Prompt Refiner pipelines with structured planning, local validation, semantic review, one bounded correction, appended plan/review JSON outputs, and stage-aware fallback behavior for every target profile.
- Added `resources/visual_art_styles.csv` with 250 original, model-neutral style phrases across ten visual-art categories, inspired in breadth by [ComfyUI-NO8D-controls](https://github.com/no8d/ComfyUI-NO8D-controls) without copying its long prompt descriptions or named styles.
- Strengthened Anima spatial prompting so left, right, top, and bottom inputs form one continuous camera view, merge repeated character details into one figure, and discourage split screens, panels, and duplicate views.
- Replaced the natural-profile stock prompt fallback with selectable `adaptive`, `strict`, and `continue` recovery modes; short concrete Ollama prose is preserved by default, while `continue` can pass through partial responses or connected inputs after response and transport errors.

## v0.7.0

- Added the `krea2` Ollama Prompt Refiner profile with subject-first natural-language prompts, exact preservation of visible quoted text, concrete spatial and material descriptions, and conservative negative prompts.
- Aligned Krea2 and Z-Image prompt composition around a shared subject-to-aesthetic order while preserving their model-specific negative-prompt behavior and Krea2 style anchors.
- Added Krea2 CLIP selection to the model cycler loaders and Krea2/Qwen stream detection plus chat-template exclusions to the T5 equal-length and sculpt balancers.
- Reworked all T5/Qwen, CLIP, and regional sculpt nodes to use exact chunked nearest-token search with automatic CPU fallback, eliminating full FP32 embedding-table VRAM copies such as the 1.45 GiB Krea2/Qwen3-VL allocation spike.

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
