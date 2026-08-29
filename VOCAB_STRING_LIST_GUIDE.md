# Vocab String List Guide

This guide explains how to use **Random Vocab String List (Nukun)**, **Multi Vocab String List (Nukun)**, and **MiniMax H3 Prompt Builder (Nukun)** in ComfyUI.

All three nodes can read selectable vocabulary files and output prompt text. They are useful when you want controlled random prompt variation without editing the prompt by hand for every queue run.

## Vocabulary Files

The nodes can read:

- `ComfyUI/user/vocab.json`, when present.
- Bundled files in `custom_nodes/Nukun_ComfyUI_Nodes/resources/`.
- Custom `.csv`, `.txt`, or `.json` files added to the `resources/` folder.

Vocabulary files are read as comma-separated entries:

```text
masterpiece,best quality,cinematic lighting,sharp focus
```

Avoid leading spaces after commas. Use `tag_a,tag_b,tag_c` instead of `tag_a, tag_b, tag_c`.

## Random Vocab String List

Use **Random Vocab String List (Nukun)** when you want one vocabulary file and one generated text output.

Inputs:

- `vocab_file`: the vocabulary file to use.
- `amount`: how many entries to output.
- `seed`: the shuffle-bag block cursor.
- `chain`: optional incoming text. When connected, generated words are appended after it.

The node uses deterministic shuffle-bag sampling. Incrementing `seed` walks through non-overlapping shuffled blocks before reshuffling, so repeated queued runs cover more of the vocabulary before entries repeat.

Example:

```text
vocab_file = resources/quality_tags.csv
amount = 4
seed = increment after generate
```

This is good for adding a small rotating set of quality, detail, lighting, or camera tags.

## Multi Vocab String List

Use **Multi Vocab String List (Nukun)** when you want to combine up to four independent vocabulary files.

Each slot has:

- `vocab_file_N`: the vocabulary file for that slot.
- `amount_N`: how many entries to output from that slot. Set `0` to disable the slot.
- `word_index_N`: the shuffle-bag block cursor for that slot.

Outputs:

- `combined`: all enabled slot outputs joined into one string, plus optional `chain` text.
- `slot_1`
- `slot_2`
- `slot_3`
- `slot_4`

Each slot has its own deterministic shuffle order, so the slots do not all walk through their vocabularies in the same pattern.

Example setup:

```text
Slot 1: resources/quality_tags.csv, amount 3
Slot 2: resources/camera_composition.csv, amount 2
Slot 3: resources/anima2b_artists_clean.csv, amount 1
Slot 4: resources/place_environments.csv, amount 2
```

This can produce a compact prompt seed such as:

```text
best quality sharp focus cinematic lighting close_up depth_of_field dairi moonlit forest
```

## MiniMax H3 Prompt Builder

Use **MiniMax H3 Prompt Builder (Nukun)** when a video workflow should receive one natural-language prompt split into these fixed sections:

1. `Scene`
2. `Character`
3. `Action`
4. `Camera`
5. `Visual Style`
6. `Audio`

Each section has four controls:

- `<section>_text`: fixed multiline prose, placed first.
- `<section>_vocab_file`: one existing user or bundled vocabulary file.
- `<section>_amount`: number of sampled phrases; keep this at `0` for text-only use.
- `<section>_word_index`: deterministic shuffle-bag cursor with control-after-generate support.

The matching bundled defaults are:

- `resources/minimax_h3_scenes.csv`
- `resources/minimax_h3_characters.csv`
- `resources/minimax_h3_actions.csv`
- `resources/minimax_h3_cameras.csv`
- `resources/minimax_h3_visual_styles.csv`
- `resources/minimax_h3_audio.csv`

Each file contains 80 complete phrases designed for its section. Keep Audio vocabulary separate from `spoken_dialogue`: the Audio resource supplies ambience, effects, and music while the dedicated dialogue controls preserve the exact spoken line.

Selected multiword phrases stay intact and are appended with commas. Empty sections are omitted from the complete `prompt` output. The six individual section outputs contain the finished text without their square-bracket headers.

For spoken dialogue, enter the line without surrounding quotes in `spoken_dialogue`. The node quotes that exact line in both Action and Audio. Use `dialogue_language`, `dialogue_voice`, and `dialogue_delivery` to describe how it should sound. When a line is present, the Audio block always finishes with `No other dialogue.`

Example text-only setup:

```text
scene_text = A young anime mage stands in a glowing forest at twilight. Soft luminous plants, drifting sparkles, and faint magical mist create a mysterious enchanted atmosphere.
character_text = She has long blue hair, a white and blue fantasy outfit, and a flowing cape. She holds a small glowing magical orb and looks calm, confident, and curious.
action_text = Sparkling particles drift through the air as her hair and cape move gently in the wind. She raises her hand, looks around, and turns toward the camera.
camera_text = Medium shot, subtle slow camera movement, cinematic framing, gentle forward drift.
visual_style_text = Beautiful anime style, clean line art, soft fantasy colors, detailed background, glowing effects, cinematic twilight lighting, smooth motion.
audio_text = Quiet magical forest ambience, soft breeze, rustling leaves, subtle magical sparkles, distant nighttime atmosphere, soft piano, airy pads, and light strings.
spoken_dialogue = Hallo, ist da jemand?
dialogue_language = German
dialogue_voice = clear young female voice
dialogue_delivery = natural speech, calm and slightly cautious tone
```

The complete output follows this structure:

```text
[Scene]
A young anime mage stands in a glowing forest at twilight. Soft luminous plants, drifting sparkles, and faint magical mist create a mysterious enchanted atmosphere.

[Character]
She has long blue hair, a white and blue fantasy outfit, and a flowing cape. She holds a small glowing magical orb and looks calm, confident, and curious.

[Action]
Sparkling particles drift through the air as her hair and cape move gently in the wind. She raises her hand, looks around, and turns toward the camera. The character says in German: "Hallo, ist da jemand?"

[Camera]
Medium shot, subtle slow camera movement, cinematic framing, gentle forward drift.

[Visual Style]
Beautiful anime style, clean line art, soft fantasy colors, detailed background, glowing effects, cinematic twilight lighting, smooth motion.

[Audio]
Quiet magical forest ambience, soft breeze, rustling leaves, subtle magical sparkles, distant nighttime atmosphere, soft piano, airy pads, and light strings. A clear young female voice says in German: "Hallo, ist da jemand?" Natural speech, calm and slightly cautious tone. No other dialogue.
```

## Refining the six sections with Ollama

`Ollama Video Prompt Refiner (Nukun)` can refine the six section outputs into a more coherent MiniMax H3 or Wan 2.2 video prompt. Its connectable inputs use the same semantic names as the manual builder outputs:

```text
MiniMax H3 Prompt Builder.scene        -> Ollama Video Prompt Refiner.scene
MiniMax H3 Prompt Builder.character    -> Ollama Video Prompt Refiner.character
MiniMax H3 Prompt Builder.action       -> Ollama Video Prompt Refiner.action
MiniMax H3 Prompt Builder.camera       -> Ollama Video Prompt Refiner.camera
MiniMax H3 Prompt Builder.visual_style -> Ollama Video Prompt Refiner.visual_style
MiniMax H3 Prompt Builder.audio        -> Ollama Video Prompt Refiner.audio
```

You can also type or connect six ordinary strings without using the manual builder. At least one section must contain text. German fields are translated in a dedicated Ollama stage before creative refinement while every double-quoted line remains exact. For H3 dialogue, keep the spoken line in double quotes in Action or Audio; the refiner validates that the same line survives in both final sections.

Choose `target_profile = minimax_h3` for the six-header video-and-audio format. Ollama is asked for approximately 100 focused words in every H3 section, using a 90–120-word writing corridor; validation tolerates outputs from 60 words upward and does not enforce a maximum. The compiler uses schema-constrained output without model thinking to prevent incomplete JSON. Exact source dialogue is restored locally and invented quoted lines are removed. In `adaptive` mode, structurally valid creative prose below the minimum is kept rather than replaced by the translated input. Choose `wan2_2_video` for one continuous visual-shot paragraph; Wan ignores the Audio section and mentions that choice in `report`. Keep `creativity_mode = balanced` for a noticeably richer rewrite or select `cinematic` for stronger grounded directing and sound design. `faithful` stays close to the supplied concepts but must still meet the H3 minimum section length in `strict` mode. Start with `pipeline_mode = single`. Use `review` when an extra Ollama pass for source fidelity, temporal continuity, camera consistency, and dialogue preservation is worth the additional runtime.

## Recommended Workflows

For simple variation:

```text
Random Vocab String List -> text encoder or prompt refiner
```

For richer prompt seeds:

```text
Multi Vocab String List -> Ollama Prompt Refiner (Nukun) -> text encoders
```

For a structured MiniMax H3 video prompt:

```text
MiniMax H3 Prompt Builder -> video prompt input
```

For Ollama refinement before generation:

```text
MiniMax H3 Prompt Builder -> Ollama Video Prompt Refiner -> video prompt input
```

For prompt chaining:

```text
fixed base prompt -> chain input
generated vocab output -> appended after the base prompt
```

## Practical Tips

- Use small `amount` values for quality tags, usually `2-5`.
- Use `amount = 1` for artist lists if you want a clear single style reference.
- Use separate slots for different concepts, such as quality, camera, artist, environment, action, or objects.
- Set ComfyUI control-after-generate to `increment` for steady exploration.
- Set it to `randomize` when you want a larger jump through the vocabulary.
- Keep vocabulary entries short and prompt-ready.
- Avoid duplicate entries in custom vocab files; the nodes deduplicate before sampling.

## Bundled Useful Resources

Common bundled choices include:

- `resources/quality_tags.csv`
- `resources/camera_composition.csv`
- `resources/visual_art_styles.csv`
- `resources/anima2b_artists_clean.csv`
- `resources/adjectives.csv`
- `resources/objects.csv`
- `resources/place_environments.csv`
- `resources/animals_mythical_creatures.csv`
- `resources/little_doom_*.csv`
- `resources/minimax_h3_*.csv`

`resources/visual_art_styles.csv` contains 250 short, model-neutral style phrases covering drawing and linework, painting, printmaking and paper, comics, animation and illustration, graphic design, digital and concept art, 3D and crafted media, photography and cinematography, and historical or decorative art. Use `amount = 1` for a clear single style anchor; larger values intentionally blend multiple visual treatments.

The resource list updates when ComfyUI reloads the custom node package.
