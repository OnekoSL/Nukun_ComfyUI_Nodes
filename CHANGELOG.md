# Changelog

## v0.5.0

- Added `Multi Vocab String List (Nukun)` for combining four selectable vocabulary files with deterministic random fills and optional direct word selectors.
- Added `resources/camera_composition.csv` for camera, framing, focus, perspective, and composition prompt terms.

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
