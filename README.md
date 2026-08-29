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

The main node set and core examples work with a standard ComfyUI installation. These optional integration nodes need additional custom-node packages only when you use those specific workflows:

- `NukunDenseDiffusionSplitApply` and `NukunDenseDiffusionRectApply` need `comfyui_densediffusion`.
- `NukunHiResFixTiled` needs `ComfyUI_UltimateSDUpscale`.
- `NukunTiledHiResFixAdvanced` needs `ComfyUI_TiledKSampler`.

`NukunRegionalSplitRegions` has no runtime dependency on A8R8 by itself; it outputs `ATTENTION_COUPLE_REGION` data for workflows that connect it to A8R8 `Attention Couple`.

## Included nodes

- `NukunCheckpointCyclerLoader` - display name `Checkpoint Cycler Loader (Nukun)`, category `Nukun/Loaders`
- `NukunCheckpointVaeCyclerLoader` - display name `Checkpoint + VAE Cycler Loader (Nukun)`, category `Nukun/Loaders`
- `NukunCheckpointPairCyclerLoader` - display name `Checkpoint Pair Cycler Loader (Nukun)`, category `Nukun/Loaders`
- `NukunFourPromptModelCyclerLoader` - display name `4-Prompt Model Cycler Loader (Nukun)`, category `Nukun/Loaders`
- `NukunFourPromptCheckpointCyclerLoader` - display name `4-Prompt Checkpoint Cycler Loader (Nukun)`, category `Nukun/Loaders`
- `NukunIncrementingIntString` - display name `Incrementing Int to String (Nukun)`, category `Nukun/Text`
- `NukunRandomVocabStringList` - display name `Random Vocab String List (Nukun)`, category `Nukun/Text`
- `NukunVocabMultiStringList` - display name `Multi Vocab String List (Nukun)`, category `Nukun/Text`
- `NukunMiniMaxH3PromptBuilder` - display name `MiniMax H3 Prompt Builder (Nukun)`, category `Nukun/Text`
- `NukunOllamaPromptRefiner` - display name `Ollama Prompt Refiner (Nukun)`, category `Nukun/Text`
- `NukunOllamaVideoPromptRefiner` - display name `Ollama Video Prompt Refiner (Nukun)`, category `Nukun/Video`
- `NukunAceSongVariationDirector` - display name `ACE Song Variation Director (Nukun)`, category `Nukun/Audio/ACE`
- `NukunAceSongTimelineConditioning` - display name `ACE Song Timeline Conditioning (Nukun)`, category `Nukun/Audio/ACE`
- `NukunAudioTimelineMixer5` - display name `Audio Timeline Mixer 5 (Nukun)`, category `Nukun/Audio`
- `NukunWan22VideoSettings` - display name `Wan 2.2 Video Settings (Nukun)`, category `Nukun/Video/Wan 2.2`
- `NukunWan22TI2VLatent` - display name `Wan 2.2 TI2V Latent (Nukun)`, category `Nukun/Video/Wan 2.2`
- `NukunWan22RunManifest` - display name `Wan 2.2 Run Manifest (Nukun)`, category `Nukun/Video/Wan 2.2`
- `NukunWan22ContinuationPlan` - plans 1-10 iterative five-second extensions and their memory/duration totals
- `NukunWan22ContinuationRecord` - appends deterministic per-segment captions, prompts, and seeds to JSON
- `NukunWan22ContinuationManifest` - combines the base run and continuation log into the final manifest and filename
- `NukunWan22SegmentStore` - stores one Wan segment as numbered PNG frames, updates `last_frame.png`, and writes segment/run manifests
- `NukunWan22SegmentLoader` - loads a saved Wan run's current end frame and manifest state for the next manual continuation
- `NukunWan22FrameSequenceAssembler` - assembles a saved PNG frame sequence into a final MP4 via bundled `imageio_ffmpeg`
- `NukunOllamaVisionCaptioner` - display name `Ollama Vision Captioner (Nukun)`, category `Nukun/Image`
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
- `NukunNativeRegionalSplitConditioning` - display name `Native Regional Split Conditioning (Nukun)`, category `Nukun/Conditioning`
- `NukunNativeRegionalRectConditioning` - display name `Native Regional Rect Conditioning (Nukun)`, category `Nukun/Conditioning`
- `NukunDenseDiffusionSplitApply` - display name `DenseDiffusion Split Apply (Nukun)`, category `Nukun/Conditioning`
- `NukunDenseDiffusionRectApply` - display name `DenseDiffusion Rect Apply (Nukun)`, category `Nukun/Conditioning`
- `NukunRegionalSplitRegions` - display name `Regional Split Regions (Nukun)`, category `Nukun/Conditioning`
- `SaveImageWebsocket` - display name `Save Image (Websocket)`, category `Nukun/Image`
- `NukunAdvancedNoiseSampler` - display name `Advanced Noise Sampler (Nukun)`, category `Nukun/Sampling`
- `NukunIllustriousNoiseSampler` - display name `Illustrious Noise Sampler (Nukun)`, category `Nukun/Sampling`
- `NukunPonyV7NoiseSampler` - display name `Pony V7 Noise Sampler (Nukun)`, category `Nukun/Sampling`
- `NukunUniversalNoiseSampler` - display name `Universal Noise Sampler (Nukun)`, category `Nukun/Sampling`
- `NukunUniversalNoiseSamplerAdvanced` - display name `Universal Noise Sampler Advanced (Nukun)`, category `Nukun/Sampling`
- `NukunNoiseProfileCycler` - display name `Noise Profile Cycler (Nukun)`, category `Nukun/Sampling`
- `NukunSpeedSampler` - display name `SPEED Sampler (Nukun)`, category `Nukun/Sampling`
- `NukunUNetBlockNoisePatch` - display name `UNet Block Noise Patch (Nukun)`, category `Nukun/Model Patches`
- `NukunHiResFixTiled` - display name `HiResFix Tiled (Nukun)`, category `Nukun/Sampling`
- `NukunTiledHiResFixAdvanced` - display name `Tiled HiRes Fix Advanced (Nukun)`, category `Nukun/Sampling`

Wan 2.2 example workflows live in `examples/wan22/`, including the segmented Anima-to-Wan start, extension, and final assembly workflows.

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

## 4-Prompt Model Cycler Loader

This node cycles four multiline prompt fields for every diffusion model in one exact model folder.
Keep `cycle_index` on `increment`: indices 0-3 output text 1-4 with the first naturally sorted UNET, index 4 starts text 1 with the next UNET, and the complete model/prompt sequence wraps automatically.
Empty text fields remain intentional cycle positions. CLIP and VAE stay fixed while `MODEL`, model metadata, prompt/model indices, and the selected text are exposed as outputs.
`seed_mode` controls the shared seed for each four-prompt model group: `increment` advances once per model, `fixed` always keeps the entered `seed`, and `random` generates a fresh seed when the first group or a new model group is queued in the ComfyUI frontend.
Random seeds remain fixed inside their four-prompt group. API prompts queued without the frontend use the supplied `seed` unchanged in random mode.

## 4-Prompt Checkpoint Cycler Loader

This node provides the same four-prompt and model-synchronous seed cycle for normal checkpoints.
It cycles naturally sorted checkpoints from one exact folder and returns the checkpoint's `MODEL`, `CLIP`, and embedded `VAE` together with text, checkpoint metadata, indices, model count, and seed.
The `increment`, `fixed`, and `random` seed modes behave exactly like the diffusion-model version.

## Incrementing Int to String

This node replaces the common `Int` plus `Int to String (Mikey)` pattern.
It exposes one integer widget with ComfyUI's control-after-generate support and outputs a plain string without a commas toggle.
`min_value` and `max_value` define the output cycle, so incrementing values wrap around in a predictable range.

## Random Vocab String List

This node reads a selected comma-separated plain-text word list and outputs a deterministic shuffle-bag space-separated string.
It can use `ComfyUI/user/vocab.json` or bundled files such as `resources/english_words.csv`; add more `.csv`, `.txt`, or `.json` files to `resources/` to make them selectable.
Set `amount` for the number of words and use the `seed` widget's control-after-generate behavior as a block cursor: incrementing walks through non-overlapping shuffled blocks before reshuffling, while randomizing jumps to another block.
Words are deduplicated before sampling; if `amount` is larger than the available vocabulary, the output is clamped to the full list.
Bundled category vocabularies include places/environments, objects, animals and mythical creatures, verbs, nouns, adjectives, `*ing` words, camera/composition terms, quality tags, person names, countries, cities, and 250 visual art styles.
Use `resources/visual_art_styles.csv` with `amount = 1` when you want one clear style anchor spanning drawing, painting, printmaking, comics, animation, design, digital art, crafted media, photography, or historical art movements.
Bundled Little Doom LoRA keyword resources are also available as `little_doom_*.csv`, including clean, character/source, visual feature, clothing, action, setting, style, mature, and dark/gore subsets.
Connect the optional `chain` input to append generated words after an existing string and build prompt chains.

`Multi Vocab String List (Nukun)` combines four selectable vocab files in one node. Each slot has its own `amount` and incrementable `word_index` cursor, so ComfyUI's control-after-generate menu can keep, increment, decrement, or randomize each slot independently. The node returns a combined string plus one output per slot.

## MiniMax H3 Prompt Builder

`MiniMax H3 Prompt Builder (Nukun)` creates one structured video prompt from up to six sections in fixed order: `[Scene]`, `[Character]`, `[Action]`, `[Camera]`, `[Visual Style]`, and `[Audio]`. Empty sections are omitted. Each section combines an optional fixed multiline description with phrases selected from one existing vocab file. Keep `amount = 0` for text only, or increment the section's `word_index` to walk its deterministic shuffle bag.

`spoken_dialogue` is copied exactly into both Action and Audio. The Action block states that the character speaks the line; the Audio block adds `dialogue_language`, `dialogue_voice`, `dialogue_delivery`, and `No other dialogue.` The separate section outputs contain their finished bodies without headers, while `prompt` contains the complete blank-line-separated H3 structure.

Each section defaults to its matching bundled `resources/minimax_h3_*.csv` file. These six resources contain 80 complete phrases each. Actions describe continuous movement, camera entries contain one compatible shot plan, and Audio entries provide coherent ambience/music packages without spoken text. All section amounts still default to `0`, so sampling starts only when explicitly enabled.

See [VOCAB_STRING_LIST_GUIDE.md](VOCAB_STRING_LIST_GUIDE.md) for practical guides to all three vocabulary-based text nodes and a complete H3 example.

## Ollama Video Prompt Refiner

`Ollama Video Prompt Refiner (Nukun)` accepts six independent Scene, Character, Action, Camera, Visual Style, and Audio source strings in English, German, or mixed language. It uses the selected local Ollama model to harmonize them for either `minimax_h3` or `wan2_2_video`, then returns only the finished `prompt`, `negative`, and a processing `report`.

MiniMax H3 output is assembled locally with fixed `[Scene]`, `[Character]`, `[Action]`, `[Camera]`, `[Visual Style]`, and `[Audio]` headers. Ollama is instructed to target approximately 100 focused words per H3 section (normally 90–120 and never more than 140 in the writing instruction), while validation accepts sections from 60 words upward without enforcing a maximum. The structured compiler disables model thinking so Ollama can enforce the JSON schema and uses a larger completion budget to avoid truncated objects. Exact source dialogue is restored locally and model-invented quoted lines are removed. In `adaptive` mode, a creative, otherwise valid result that remains below 60 words is retained instead of being replaced by the translated source; `strict` still rejects it. Wan 2.2 output is joined as one continuous visual shot in character/action/scene/camera/style order; Audio is intentionally excluded and recorded in the report.

`creativity_mode = balanced` is the default and substantially rewrites the source into more useful production direction with compatible secondary motion, atmosphere, camera timing, lighting response, and sound texture. Use `faithful` for a restrained rewrite or `cinematic` for stronger grounded directing and sound-design choices. German source fields first pass through a separate translation request before creative compilation. Translation and compiler validation both reject remaining German production prose. Double-quoted dialogue remains untouched throughout both stages.

`pipeline_mode = single` makes one compiler request and one JSON-repair request only when needed; German input adds a preceding translation request and at most one translation repair. `review` adds a semantic continuity/grounding review and at most one correction. `fallback_mode = strict` stops on invalid output, `adaptive` can locally format the supplied sections after repeated validation failure, and `continue` also survives Ollama connection or timeout failures. Local fallbacks preserve source content without inventing replacement prose.

For a randomized H3 workflow, connect the six section outputs from `MiniMax H3 Prompt Builder (Nukun)` directly to the matching six Video Refiner inputs. The older `wan2_2_video` profile remains available in `Ollama Prompt Refiner (Nukun)` for saved-workflow compatibility, while new video workflows should use the dedicated Video Refiner.

## ACE-Step song tools

`ACE Song Variation Director (Nukun)` uses a local Ollama model to turn existing ACE-Step tags and sectioned lyrics into a coherent variation plan. Separate controls govern overall, energy, rhythm, instrument, vocal, harmonic, and transition variation. Exact `must_keep` phrases are validated, and passthrough mode preserves the original tags and lyrics if generation or repair fails.

`ACE Song Timeline Conditioning (Nukun)` converts lyrics or the director's `plan_json` into time-regional ACE-Step 1.5 conditioning. It allocates the available audio codes across song sections, supports explicit per-section duration overrides and transition windows, and returns both the combined conditioning and a reproducible timeline report.

`Audio Timeline Mixer 5 (Nukun)` places and mixes up to five ComfyUI audio inputs with independent offsets, gains, mutes, and fades. It can resample inputs, normalize mono/stereo channel layout, apply master gain, and reduce peaks or hard-clip to a selected ceiling.

## Ollama Prompt Refiner

This node sends a random vocabulary string to a local Ollama model and returns one curated split prompt set for the selected `target_profile`: `pony_v6`, `illustrious`, `pony_v7`, `z_image`, `anima`, `wan2_2_video`, or `krea2`.
It is designed to sit after `Random Vocab String List (Nukun)` or `Multi Vocab String List (Nukun)`: connect the random `STRING` output to `word_salad`, choose one `target_profile`, then connect the generated prompt outputs to your text encoders.
The default Ollama endpoint is `http://127.0.0.1:11434` and the default model is `autoren-darkidol-llama-3-1-8b:latest`.
The `ollama_model` widget is populated from the selected Ollama URL's `/api/tags` list and refreshes in the browser when `ollama_url` changes.
Set `style_cluster` to choose the Pony v7 `style_cluster_XXXX` header value; the default is `430`.
Use `style_anchor` for fixed character names, LoRA trigger words, quality tags, or motifs that should survive the rewrite even when the random input is noisy.
The optional multiline inputs `left`, `right`, `top`, and `bottom` provide independent regional ideas for `pony_v7`, `z_image`, `anima`, `wan2_2_video`, and `krea2`. They can be used without `word_salad` or `style_anchor` on these natural-prompt profiles. The positions are creative composition guidance rather than rigid geometry, so Ollama may improve transitions and overlap while preserving the broad orientation. For Anima, every placement is explicitly merged into one continuous full-frame image with one camera view; repeated character details describe the same main figure instead of producing panels, split screens, or additional portraits. After generation, a region counts as integrated only when one sentence contains both its direction and relevant content words. Only missing regions receive a short positional safety sentence at the beginning of `background_prompt`, in left/right/top/bottom order. `word_salad` remains global guidance that may influence every region; Pony v6 and Illustrious ignore the spatial inputs.
For Pony v6 and Illustrious, the node pre-sorts the random words into fixed/base, foreground, background, style, and discarded-noise candidate lists before asking Ollama to write the split prompts. Their `background_prompt` is a concrete 30-40 word tag list of visible background things such as rooms, furniture, windows, city details, trees, mushrooms, crystals, props, and terrain, not an abstract depth/filler chain.
The node keeps `positive`, `negative`, `report`, `base_prompt`, `foreground_prompt`, and `background_prompt` as its first six outputs, followed by `plan_json` and `review_json`. The JSON outputs are `{}` when their stage did not run. Pony v6 and Illustrious split outputs are normalized without commas to reduce prompt tokens; Pony v7 keeps commas for its structured caption and Danbooru tag block.
`pipeline_mode = single` is the backward-compatible default and uses the original one-stage generation and recovery flow. `plan_compile` first asks the selected Ollama model to classify the noisy input into a fixed JSON plan, then gives both that plan and the original source to the target-profile compiler. `plan_compile_review` adds a semantic reviewer. Local checks and reviewer findings can trigger exactly one correction request; there is no automatic rewrite loop. All roles use the same `ollama_model` and context settings, with deterministic seed offsets and role-specific temperatures.
The chained modes support every target profile. They preserve `style_anchor` and spatial inputs as fixed requirements while allowing the planner to place weak random vocabulary in `discarded_terms`. A normal `plan_compile` run makes two Ollama requests, and `plan_compile_review` makes three; either mode can make one additional correction request. Only one Ollama model remains loaded during these sequential stages, but the extra requests increase total generation time.
In `fallback_mode = continue`, a failed planner is replaced by a small source-grounded local plan instead of an empty plan. `plan_json` includes `planner_status.status = local_fallback` and the original `stage_error`, so the degraded path remains visible. Final validation requires the planned subject in `foreground_prompt`; if one bounded correction still fails that check, the node rebuilds a local prompt from connected source content rather than forwarding the ungrounded compiler response.
Anima and Krea2 use source-derived candidate lists without static semantic few-shot scenes. This prevents unrelated example characters, props, or locations from being copied into the generated prompt. Reviewer findings are normalized so non-empty finding lists always imply `needs_revision = true`, and missing elements force `all_required_preserved = false`.
Before generation, the node checks Ollama's `/api/show` capabilities for the selected model. Models advertised with the `thinking` capability receive `think = true`, a doubled output-token allowance, and no JSON grammar that could suppress their reasoning. The node removes separated or tagged reasoning before the existing JSON validation and repair path checks the final answer. Ordinary completion models keep schema-constrained structured output.
Reka Flash models use an explicit compatibility path even though current Ollama builds advertise their GGUFs only with the `completion` capability. They are sent with their native compact `human: ... <sep> assistant:` wrapper and `<sep>`/`<|endoftext|>` stop strings. Anima retains inline compiler reasoning. Krea2, Z-Image, Wan 2.2, and Pony v7 instead use schema-constrained 900-token compiler, repair, and correction responses; local Q4 tests found this both faster and more reliable for those output-oriented profiles. Planner and reviewer also use schema-constrained JSON without a reasoning trace. The node applies the original Reka Flash sampling recommendation `top_k = 1024` in both modes.
For `DavidAU/Reka-Flash-3-21B-Reasoning-*` GGUF models, use `temperature = 0.60`, `top_p = 0.95`, and keep `context_length` at least `8192`. Prefer `16384` or `32768` when memory permits and the GGUF metadata supports it. Values beyond the model's reported context window do not add useful capacity.
`prompt_mode` defaults to `strict`, which stays closely grounded in the connected source text. `creative` preserves the main subject, style anchor, spatial inputs, and explicit requirements while allowing compatible poses, props, setting details, lighting, color, texture, and atmosphere. It also raises low sampling values to at least `temperature = 0.80` and `top_p = 0.95`; higher user-selected values remain unchanged.
The `context_length` dropdown offers fixed `num_ctx` values from `2048` to `131072`; the memory-conscious default is `4096`.
`unload_after_run` defaults to enabled. The node keeps the selected model available across all initial, repair, planner, compiler, reviewer, and correction requests, then sends one `keep_alive = 0` unload request before returning control to downstream ComfyUI nodes. Disable it only when a prompt-only workflow benefits more from keeping the Ollama model warm than from releasing its RAM and VRAM.
The node asks Ollama for strict JSON and retries once with a repair prompt if the model returns malformed JSON.
This is a breaking output change from older versions that exposed separate `pony_v6_*`, `illustrious_*`, and `pony_v7_*` outputs; reconnect old workflows to `positive` and `negative`.

The `anima` profile starts with a compact quality-tag line, then writes a 180-260 word natural English description in short sentences. It moves from the main figure through appearance, action, materials, and important objects to the environment, lighting, body language, and emotional atmosphere. The split outputs remain available, while `positive` joins them in that order.

The `z_image` and `krea2` profiles ask Ollama for detailed, subject-focused natural English descriptions of about 300-360 words. Their target split is roughly 55-70 words for style/camera, 140-165 for the main subject, and 105-125 for the environment. These are writing targets rather than hard minimums, so valid concise model prose is preserved instead of being padded with generic filler. Their combined `positive` starts directly with the main subject and follows pose/action, appearance, clothing or surfaces, props and materials, composition, environment, lighting/color/mood, and finally medium/aesthetic. It uses at most two paragraphs and avoids meta openings such as `The image shows`. Visible text is quoted exactly and tied to its sign, screen, garment, page, label, or other surface. UI and graphic-design subjects use the same subject-first flow while retaining typography, relative size, decoration, color, and placement details.

The `krea2` profile keeps `style_anchor` unchanged at the beginning of the separate `base_prompt`, then describes camera, lighting, color, subject quantity and shape, materials, textures, visible text, and concrete spatial relationships. The combined positive order is `foreground_prompt`, followed by `background_prompt` and `base_prompt` in one closing paragraph, so the subject remains first and the style treatment comes last. Photography, anime, illustration, and LoRA triggers remain controlled by `style_anchor`. Its conservative negative output affects generation only when the Krea2 workflow uses unconditional guidance/CFG; Z-Image continues to emit an empty negative prompt.

In `single` mode, `fallback_mode` controls recovery for the natural `anima`, `krea2`, `z_image`, and `wan2_2_video` profiles. The default `adaptive` mode preserves concrete prose even when it is short or consists of one sentence, and rebuilds only empty, meta-like, or tag-pile sections from connected source terms. `strict` performs the initial, repair, and minimal Ollama attempts, then stops with a detailed error instead of generating local positive text. `continue` prioritizes uninterrupted workflows: it keeps partial JSON fields or raw prose and, after transport or response failures, passes through `style_anchor`, `word_salad`, and exact spatial inputs without adding stock descriptive paragraphs. Pony v6, Pony v7, and Illustrious ignore this setting only in `single` mode. In either chained mode, `strict` stops at the failed stage, `adaptive` restarts through the complete single path, and `continue` keeps the best available plan or compiled result. The `report` records the executed stages, correction status, final local findings, and any continued or fallback error.

The `wan2_2_video` profile creates natural Wan 2.2 video prompts with an explicit continuous action, stable environment, camera behavior, lighting/style guidance, and temporal-artifact negatives. Connection and timeout failures normally stop execution with a clear error; in `fallback_mode = continue`, the node instead passes through usable connected inputs without inventing replacement prose.

## Wan 2.2 TI2V-5B toolkit

`Wan 2.2 Video Settings (Nukun)` converts duration and FPS to a valid `4n+1` frame count and provides draft, balanced, quality, portrait, landscape, square, and snapped custom resolutions. `Wan 2.2 TI2V Latent (Nukun)` switches T2V/I2V without cable changes and prepares I2V images proportionally with center crop or padding. `Wan 2.2 Run Manifest (Nukun)` records model, dimensions, FPS, both seeds, sampling configuration, and prompts as JSON and a filename-safe prefix.

The continuation helpers support the Easy-Use loop in `anima_to_wan2.2_i2v.json`. Each iteration re-captionizes the current end frame, advances three deterministic seeds, removes the new segment's duplicate first frame, and appends the remaining frames. The final frame formula is `81 + extension_count * 80`; ten extensions produce 881 frames and require about 5.1 GiB of decoded-frame RAM at balanced portrait resolution.

See [WAN22_WORKFLOW_ANALYSIS.md](WAN22_WORKFLOW_ANALYSIS.md) and the example [wan2.2_video_toolkit.json](../../pysssss-workflows/wan2.2_video_toolkit.json) for the full 16 GB workflow and sampling comparison matrix.

The separate [Anima to Wan workflow](../../pysssss-workflows/anima_to_wan2.2_i2v.json) generates a 704x1248 Anima keyframe, captions the actual result with JoyCaption, converts that caption plus a manual motion instruction into a Wan prompt, and renders a balanced portrait I2V video. See [ANIMA_WAN_WORKFLOW.md](ANIMA_WAN_WORKFLOW.md) for controls and verified smoke-test details.

## Ollama Vision Captioner

This node captions a ComfyUI `IMAGE` with a local Ollama vision model and returns `caption`, `tags`, `text_seed`, `report`, and `hiresfix_text`.
The intended wiring is `IMAGE -> Ollama Vision Captioner (Nukun) -> Ollama Prompt Refiner (Nukun)`: connect `text_seed` to the refiner's `word_salad` or use it as a richer `style_anchor`.
Backend v1 uses only Ollama's `/api/generate` image support, so it does not add Transformers, llama-cpp-python, or other new Python requirements.
The default model is `user-v4/joycaption-beta`; JoyCaption Alpha Two can be selected or typed through Ollama as `hf.co/Jobaar/Llama-JoyCaption-Alpha-Two-GGUF:F16` or a local alias such as an `ollama pull`/Modelfile name.
The `ollama_model` dropdown shares the browser refresh helper used by the Prompt Refiner and keeps the current widget value even when that model is not present in the local `/api/tags` response yet.
The Vision Captioner also defaults to `context_length = 4096` and `unload_after_run = true`. It keeps the model loaded for a possible JSON repair request, then releases it before downstream image-generation nodes execute.

`caption_mode` controls the shape of the text:

- `natural_caption` writes two to four readable sentences plus a fuller visible tag list.
- `danbooru_tags` prefers 24-48 comma-separated booru-style tags.
- `pony_source` writes 35-65 comma-free factual image words for Pony v6 and Illustrious workflows.
- `refiner_seed` writes the richest comma-free 40-80 word seed text for the Prompt Refiner and strips final model-control tags such as `score_9`, `rating_*`, and `style_cluster_*`.

`hiresfix_text` is a direct detail-pass prompt for HiResFix or another upscale/refine text input.
It describes the same image and adds visible material/detail cues such as `fluffy fur`, `shaggy fur`, `fine hair strands`, `glossy latex highlights`, `leather grain`, `fabric weave`, `metal reflections`, `refined shading`, `clean linework`, and `background detail` when the caption contains matching visual material.

Batch behavior is intentionally simple in v1: only `image[0]` is captioned, and `report` mentions the batch size when additional images were present.
Images are converted from ComfyUI's float tensor format to RGB JPEG, downscaled to `resize_long_edge = 1024` by default while preserving aspect ratio, base64 encoded, and sent in the Ollama `images` field.
If Ollama returns malformed JSON, the node retries once with a text-only repair prompt; if that also fails, it builds a local fallback from the raw response so the workflow still receives usable text.
Use an Ollama model with vision support. Text-only models will usually return an Ollama error or captions that ignore the image.

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

This experimental node keeps the equal-length T5 prompt encoding behavior, then optionally replaces eligible token IDs with sculpted T5/Qwen embedding vectors before scheduled encoding.
It skips special, padded, and Qwen3-VL chat-template tokens, shares repeated token IDs across positive and negative prompts, and performs the exact `top_k` nearest-vector search in bounded chunks instead of cloning the complete embedding table to VRAM. The accelerator is used automatically; an accelerator OOM clears only temporary cache data and transparently retries the search on CPU. The report states the search device, fallback state, chunk size, query batches, and unique-token count.
The defaults are mildly active for the positive prompt and normalization-only for the negative prompt, so compare against `T5 Equal-Length Prompt Balancer (Nukun)` before increasing intensity.
Both equal-length nodes keep `target = 1024` as their default. On low-memory systems, set `target = 0` to equalize only to the longer real prompt instead of adding artificial 1024-token padding.

## CLIP Sculpt Text Encode

This SD1/SDXL CLIP node is the Nukun-native replacement for the old external `CLIP Vector Sculptor text encode`.
It tokenizes text, skips special and precomputed embedding tokens, sculpts eligible CLIP token vectors with the same exact chunked/CPU-fallback search, then encodes with ComfyUI's scheduled CLIP path. `mean of all tokens` is also calculated as a streaming chunk reduction and no longer materializes a full FP32 embedding copy.
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
All active regional and HiRes texts are tokenized before sculpting, so each unique token is searched once per CLIP stream and reused across every regional conditioning with bounded memory.
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
The included browser-side rectangle editor adds a draggable canvas to `Regional Rect Masks`, `Native Regional Rect Conditioning`, and `DenseDiffusion Rect Apply` so region bounds can be adjusted directly in the node UI.

## Native Regional Conditioning

`Native Regional Split Conditioning (Nukun)` and `Native Regional Rect Conditioning (Nukun)` are dependency-free regional wrappers built on ComfyUI core conditioning metadata.
They create split or rectangular masks, apply each mask to its regional conditioning with `mask_strength`, and return one combined conditioning output for the sampler positive path.
Use these for core-first regional workflows when you do not need DenseDiffusion model patching.

## DenseDiffusion Split Apply

This optional integration node wraps `Split Masks`, multiple `DenseDiffusion Add Cond` nodes, and `DenseDiffusion Apply` into one node.
Connect the patched `model` output to the sampler model path and the `conditioning` output to the positive conditioning path.
For `region_count = 2`, `conditioning_3`, `split_2`, and `strength_3` are ignored and `mask_3` is an empty mask.
It requires the `comfyui_densediffusion` custom node package.

## DenseDiffusion Rect Apply

This optional integration node wraps `Regional Rect Masks`, multiple `DenseDiffusion Add Cond` nodes, and `DenseDiffusion Apply` into one node.
Use it instead of `DenseDiffusion Split Apply` when the regional areas should be freely positioned rectangles instead of full-height or full-width splits.
For DenseDiffusion safety, uncovered pixels are internally assigned to all active region masks so empty attention areas do not produce black/NaN images.
It requires the `comfyui_densediffusion` custom node package.

## Advanced Noise Sampler

This node replaces `RandomNoise` plus `SamplerCustomAdvanced` with one sampler node.
It accepts `guider`, `sampler`, `sigmas`, and `latent_image`, then generates random or zero initial noise internally.
`noise_device = auto` keeps ComfyUI-core-like CPU noise behavior, while `cuda` uses CUDA when available and falls back to CPU otherwise.
`noise_type` supports `gaussian`, `uniform`, `laplacian`, `pink`, `brown`, `blue`, `violet`, `pyramid`, `perlin`, `studentt`, `white`, `grey`, `velvet`, `green_test`, `highres_pyramid`, `pyramid_discount5`, `pyramid_mix`, `rainbow_mild`, `rainbow_intense`, and `wavelet`.
Use `noise_strength` as a multiplier for the generated noise; `gaussian` + `auto` + `1.0` is the stable ComfyUI-compatible default.
Disabling `add_noise` still produces zero noise and ignores the selected noise type.
The `seed` output exposes the final `noise_seed` value for filenames, logging, or downstream helper nodes.
The expanded profiles are Sonar-inspired but implemented directly in Nukun; they do not require `ComfyUI-sonar`.
`green_test`, `rainbow_intense`, `velvet`, and `wavelet` are stronger experimental profiles and are usually easier to control in partial denoise or multi-stage Advanced Sampler passes.
All Nukun sampler nodes include `preview_method`: `default` follows ComfyUI's queue setting, `latent2rgb` gives a lightweight per-step latent preview, `taesd` uses TAESD/TAEHV preview assets when available, and `none` disables previews.
For low-memory testers, set `preview_method = latent2rgb` so they can cancel the queue early when the first previews are off target.

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
Basic profiles are `gaussian`, `uniform`, `laplacian`, `pink`, `brown`, `blue`, `violet`, `pyramid`, `perlin`, `studentt`, `white`, `grey`, `velvet`, `green_test`, `highres_pyramid`, `pyramid_discount5`, `pyramid_mix`, `rainbow_mild`, `rainbow_intense`, and `wavelet`.
Composite profiles include `illustrious_balanced`, `illustrious_texture`, `illustrious_composition`, `illustrious_wild`, plus `pony_v7_stage1_gaussian`, `pony_v7_stage2_violet`, `pony_v7_balanced`, `pony_v7_soft`, and `pony_v7_graphic`.
`noise_strength` scales every profile; `detail_bias` only affects composite profiles.
Use `gaussian` + `auto` + `1.0` for the stable ComfyUI-core-like baseline, or Pony v7 profiles around `0.55` and `0.50` for the two-pass Pony v7 workflow.
The Sonar-inspired expanded profiles are dependency-free Nukun implementations. Use the more expressive profiles, especially `green_test`, `rainbow_intense`, `velvet`, and `wavelet`, at lower strengths or in later ranged passes when you want localized texture or style shifts.

## Universal KSampler

`Universal KSampler (Nukun)` is the simple path for users who want a familiar KSampler-shaped node.
Connect loader and conditioning outputs directly: `MODEL`, positive `CONDITIONING`, negative `CONDITIONING`, and `LATENT` go into `Universal KSampler (Nukun)`, then send its `output` latent to VAE decode.
The node builds the CFG guider, sampler selection, and scheduler internally, while keeping the same Universal noise profiles and `preview_method` control.
Use the advanced path when you need explicit graph control: `CFGGuider` + `KSamplerSelect` + `BasicScheduler` feed `Universal Noise Sampler (Nukun)`.

## Universal Noise Sampler Advanced

This node keeps the same noise profiles and outputs as `Universal Noise Sampler (Nukun)`, then adds `start_at_step`, `end_at_step`, and `return_with_leftover_noise`.
Use it for partial denoise passes, multi-stage handoff workflows, or experiments that would otherwise need `KSampler (Advanced)` step ranges.
The node slices the incoming `SIGMAS` input directly: `start_at_step` is inclusive, `end_at_step = 10000` means continue to the end, and `return_with_leftover_noise = enable` preserves the nonzero final sigma when ending early.
Existing Universal workflows can swap to this advanced node when they need step ranges; the original Universal node remains stable for compatibility.
For a continuity handoff that should stay close to a single full pass, add noise only in the first pass. Use `0..N` with leftover noise enabled, then continue with `N..M` and `add_noise = false`, and finish with `M..10000`, `add_noise = false`, and leftover noise disabled.
Do not set the next pass to `previous end_at_step + 1`; that skips the shared handoff sigma and changes the trajectory.
Intentional later-pass noise reinjection is still useful for creative texture shifts, but it is not an equivalence test against a single sampler pass.
Multistep samplers such as `deis_2m` may still differ after splitting because their internal step history restarts at each ranged pass. If a different sampler matches without overlap, keep the clean `N..M` handoff. For history-sensitive multistep samplers, use a small warmup overlap such as `0..20`, `18..30`, `28..10000` to get closer to the single-pass image.

## SPEED Sampler

`SPEED Sampler (Nukun)` outputs a `SAMPLER` for `SamplerCustomAdvanced`.
It is based on the MIT-licensed `howardhx/speed` implementation of Spectral Progressive Diffusion for Efficient Image and Video Generation: https://github.com/howardhx/speed
SPEED starts denoising at a lower latent resolution and spectrally expands to full resolution during the trajectory, which can reduce runtime when the model tolerates the resolution jumps.
Use it when a workflow is sampler-bound and you can inspect results for artifacts; use a normal sampler when exact stability matters more than speed.

Recommended starting points:
- General/FLUX: `transform=dct`, `mode=delta_optimal`, `model_preset=flux`, `scales=0.5,1.0`, `delta=0.01`.
- WAN 2.1-style experiments: same settings with `model_preset=wan21`.
- Anima/manual experiments: `mode=manual`, `model_preset=anima_manual`, `scales=0.5,0.75,1.0`, `manual_sigmas=0.8,0.7`.

`dct` is the safest transform for arbitrary scale ratios.
`fft` also accepts arbitrary ratios.
`dwt` requires each adjacent scale jump to be exactly `2x`, such as `0.25,0.5,1.0`.
This node is self-contained in Nukun and does not require installing the separate `ComfyUI-SPEED` custom node package.

## Noise Profile Cycler

This helper outputs a `noise_profile` combo value for systematic Universal Noise Sampler tests.
Use `profile_index` with ComfyUI's control-after-generate increment mode, connect `noise_profile` to a Universal sampler, and optionally use `profile_name` in filenames or logs.
`profile_set` can limit the run to `all`, `basic`, `legacy_basic`, `expanded`, `composite`, `illustrious`, or `pony_v7`; `start_index` and `end_index` further restrict the tested slice and wrap the incrementing index inside that range.

## UNet Block Noise Patch

This experimental model patch injects separate noise into UNet `input`, `middle`, and `output` block groups.
Use it on the `MODEL` path before the guider or sampler, while `Advanced Noise Sampler` still controls the initial latent noise.
Each group has its own noise type, strength, and seed; the default strengths are zero so adding the patch starts neutral.
Block noise strength is relative to the current feature magnitude, so small values are meant as gentle perturbations rather than latent-noise scale values.
Input and output strengths are spread across their repeated UNet blocks, while middle strength applies to its single block group pass.
`start_percent` and `end_percent` constrain the effect during denoising, and noise varies reproducibly per block and sigma step.

## HiResFix Tiled

This optional integration node wraps model upscaling, optional `ReferenceLatent`, optional `DifferentialDiffusion`, and `Ultimate SD Upscale (No Upscale)` into one compact tiled HiResFix step.
It takes an `UPSCALE_MODEL` input, uses the model's native scale through ComfyUI's `ImageUpscaleWithModel`, then refines the upscaled image with tiled img2img.
The defaults mirror the local Pony v7 tiled workflow: `steps=20`, `cfg=3.5`, `denoise=0.4`, `tile_width=1024`, `tile_height=1024`, `mask_blur=64`, `tile_padding=192`, reference latent enabled, differential diffusion enabled at `0.7`, and tiled decode enabled.
It also supports Universal Noise Sampler profiles for tiled refinement through `noise_profile`, `noise_strength`, and `detail_bias`.
The older `noise_type` widget remains for compatibility; if `noise_profile` is left at `gaussian`, legacy `noise_type` values such as `blue` or `violet` are still honored.
Use `gaussian` + `auto` + `1.0` for ComfyUI-compatible tile noise, or try `pony_v7_stage2_violet`, `illustrious_texture`, `pyramid_mix`, `highres_pyramid`, `pink`, or `perlin` for more textured HiResFix redraws.
The outputs are the final refined image, the raw upscaled image, and the seed.
It requires the `ComfyUI_UltimateSDUpscale` custom node package.

## Tiled HiRes Fix Advanced

This node is a core-first tiled HiResFix wrapper without Ultimate SD Upscale.
It uses ComfyUI's `ImageUpscaleWithModel`, tiled VAE encode/decode, optional `ReferenceLatent`, optional `DifferentialDiffusion`, and `ComfyUI_TiledKSampler` sampling behavior.
The tiled refine pass supports the Nukun Universal noise profiles through `noise_profile`, `noise_strength`, and `detail_bias`.
The default `tiling_strategy` is `simple` and tile previews are disabled for speed; switch to `random` when hiding seams matters more than runtime.
Use `denoise = 0` to skip sampling and only return the upscaled tiled VAE round trip.
Outputs are `final_image`, `upscaled_image`, `refined_latent`, `seed`, and a `settings_report` string for comparisons.
FreeU, SpotDiffusion, and TiledDiffusion should stay as external model patches before this node when you want to test them.
It requires the optional `ComfyUI_TiledKSampler` custom node package.

## Maintenance rules

- Keep public node IDs stable so saved workflows continue to load.
- Add new personal nodes under `nodes/` and export them from `__init__.py`.
- Keep `torch`, `comfy`, `folder_paths`, `latent_preview`, and other ComfyUI internals out of `requirements.txt`.
- Do not store models, LoRAs, VAEs, outputs, or workflows in this folder.

## Test after changes

Restart ComfyUI and check `/object_info` for the expected node IDs. For Pony v7 workflows, verify that `T5Balancer` still appears before moving or disabling older copies.
