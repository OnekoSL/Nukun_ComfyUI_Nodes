# Vocab String List Guide

This guide explains how to use **Random Vocab String List (Nukun)** and **Multi Vocab String List (Nukun)** in ComfyUI.

Both nodes read selectable vocabulary files and output prompt text. They are useful when you want controlled random prompt variation without editing the prompt by hand for every queue run.

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

## Recommended Workflows

For simple variation:

```text
Random Vocab String List -> text encoder or prompt refiner
```

For richer prompt seeds:

```text
Multi Vocab String List -> Ollama Prompt Refiner (Nukun) -> text encoders
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
- `resources/anima2b_artists_clean.csv`
- `resources/adjectives.csv`
- `resources/objects.csv`
- `resources/place_environments.csv`
- `resources/animals_mythical_creatures.csv`
- `resources/little_doom_*.csv`

The resource list updates when ComfyUI reloads the custom node package.
