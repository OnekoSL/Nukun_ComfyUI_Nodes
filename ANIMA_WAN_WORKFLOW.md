# Anima to Wan 2.2 I2V workflow

The separate workflow [anima_to_wan2.2_i2v.json](../../pysssss-workflows/anima_to_wan2.2_i2v.json) generates a portrait keyframe with Anima and animates that exact image with Wan 2.2 TI2V-5B. Existing Anima and Wan workflows are unchanged.

The recommended robust continuation path now avoids dynamic ComfyUI loop nodes:

- [examples/wan22/anima_to_wan2.2_segment_start.json](examples/wan22/anima_to_wan2.2_segment_start.json) renders segment 0 and stores numbered PNG frames.
- [examples/wan22/wan2.2_segment_extend.json](examples/wan22/wan2.2_segment_extend.json) loads the saved `last_frame.png`, renders one more Wan segment, drops its duplicate first frame, and appends frames to the same run folder.
- [examples/wan22/wan2.2_segment_assemble.json](examples/wan22/wan2.2_segment_assemble.json) checks the frame sequence and writes the final MP4.

## Pipeline

1. `master_concept` and `anima_style_anchor` are refined with the Ollama `anima` profile.
2. The currently selected Anima model (`ANIMA\animaXz_v070.safetensors`), Qwen 3 0.6B, and the Qwen Image VAE generate a 704x1248 keyframe with the user-selected CFG, sampler, and advanced noise node.
3. JoyCaption analyzes the decoded keyframe in `refiner_seed` mode.
4. The visual seed and editable `motion_instruction` feed the Ollama `wan2_2_video` profile.
5. Wan 2.2 TI2V-5B center-crops the keyframe proportionally to balanced portrait 544x960 and generates 81 frames at 16 FPS.
6. In the original experimental workflow, the first 81-frame clip initializes an Easy-Use continuation loop. Each extension cleans VRAM, captions the latest end frame, rebuilds the Wan prompt, renders another I2V segment, removes its duplicate first frame, and appends frames 1-80.
7. In the robust segmented workflow, each queue renders exactly one segment and persists frames on disk. Segment 0 stores frames 0-80; every continuation stores only frames 1-80. The final MP4 is assembled later from the saved PNG sequence.

Five visible rgthree seeds independently control the Anima prompt, Anima noise, vision caption, Wan prompt, and Wan sampling. Changing only the fifth seed keeps the cached Anima image and prompt bridge unchanged.

## Defaults and editing

- Edit `master_concept` for subject, setting, composition, and appearance.
- Edit `anima_style_anchor` for persistent image style and character requirements.
- Edit `motion_instruction` only for action, speed, camera behavior, secondary motion, and end pose.
- The workflow defaults to a five-second balanced portrait video. Change `Wan 2.2 Video Settings` to draft portrait for short tests.
- WebP export is present but bypassed. MP4 is the primary output.
- `extension_count` defaults to 1 and accepts 1-10. Final frames are `81 + extension_count * 80`; ten extensions are experimental because of runtime, identity drift, and roughly 5.1 GiB decoded-frame RAM.
- The visible `continuation_instruction` is applied in every loop iteration. It should describe continuous motion and camera behavior without cuts, scene changes, or a return to the starting pose.

## Robust segmented continuation

Use the segmented path when the Easy-Use loop becomes unreliable or when long runs should survive UI crashes:

1. Open `anima_to_wan2.2_segment_start.json`.
2. Set a stable `run_id` in `Segment 0 speichern`, then queue once. This creates `ComfyUI/output/wan_runs/<run_id>/frames`, `state/last_frame.png`, and JSON manifests.
3. Open `wan2.2_segment_extend.json`, set the same `run_id`, and queue once per extra segment. `segment_index = -1` means "use the next segment automatically".
4. Open `wan2.2_segment_assemble.json`, set the same `run_id`, and queue once to create `ComfyUI/output/wan_runs/<run_id>/videos/final.mp4`.

Frame totals are deterministic: 17-frame smoke runs become `17 + extension_count * 16`; normal 81-frame runs become `81 + extension_count * 80`. Re-running a continuation segment with `overwrite_segment` enabled replaces only that segment's tail frames and updates its manifest.

## Verified smoke test

The original complete backend path and the Easy-Use continuation loop were tested on the local RTX 4060 Ti 16 GB installation using draft portrait video settings:

- Anima keyframe: 704x1248
- Continuation smoke output: 352x640, 33 frames (17 + 16 seam-cleaned frames), 16 FPS
- Video: H.264 MP4, 2.0625 seconds container duration
- Result: successful dynamic Easy-Use loop execution, including VRAM cleanup, JoyCaption, prompt refinement, second Wan pass, seam removal, manifest, and final encode in approximately 154 seconds

The normal workflow default is now 544x960 with 81 base frames plus one 80-frame extension (161 final frames).

The segmented backend is covered by unit tests for 17 + 16 smoke-frame storage, tail overwrite, missing-frame detection, loader state, and MP4 assembly through the bundled `imageio_ffmpeg`.
