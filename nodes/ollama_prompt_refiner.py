import hashlib
import json
import re
import urllib.error
import urllib.request

try:
    from aiohttp import web
    from server import PromptServer
except ImportError:
    web = None
    PromptServer = None


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "autoren-darkidol-llama-3-1-8b:latest"
DEFAULT_OLLAMA_CONTEXT_LENGTH = 8192
OLLAMA_CONTEXT_LENGTH_CHOICES = ("2048", "4096", "8192", "16384", "32768", "65536", "131072")
DEFAULT_STYLE_CLUSTER = 430
SPLIT_BASE_WORD_RANGE = (10, 20)
SPLIT_DETAIL_WORD_RANGE = (36, 40)
Z_IMAGE_POSITIVE_WORD_RANGE = (360, 440)
Z_IMAGE_FOREGROUND_MIN_WORDS = 130
Z_IMAGE_BACKGROUND_MIN_WORDS = 130
Z_IMAGE_BASE_MIN_WORDS = 80
ANIMA_POSITIVE_WORD_RANGE = (180, 260)
ANIMA_FOREGROUND_WORD_RANGE = (110, 140)
ANIMA_BACKGROUND_WORD_RANGE = (70, 90)
TARGET_PROFILES = ("pony_v6", "illustrious", "pony_v7", "z_image", "anima", "wan2_2_video")
DEFAULT_TARGET_PROFILE = "pony_v7"

OUTPUT_KEYS = (
    "positive",
    "negative",
    "report",
    "base_prompt",
    "foreground_prompt",
    "background_prompt",
)

RESPONSE_KEYS = (
    "base_prompt",
    "foreground_prompt",
    "background_prompt",
    "negative",
    "report",
)

LEGACY_RESPONSE_KEYS = (
    "positive",
    "negative",
    "report",
)

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        key: {"type": "string", "minLength": 0 if key == "negative" else 1}
        for key in RESPONSE_KEYS
    },
    "required": list(RESPONSE_KEYS),
    "additionalProperties": False,
}

EQUINE_PATTERN = re.compile(r"\b(pony|ponies|horse|horses|equine|stallion|mare|foal)\b", re.IGNORECASE)
MODEL_LABEL_PATTERN = re.compile(r"\bpony[\s_-]+v?\d+\b", re.IGNORECASE)
MODEL_VERSION_LEAK_PATTERN = re.compile(r"\b(character|subject)[\s:_-]+v?\d+(?:_sdxl)?\b", re.IGNORECASE)

NEGATIVE_BASELINES = {
    "pony_v6": (
        "low quality",
        "worst quality",
        "bad anatomy",
        "bad hands",
        "malformed fingers",
        "extra fingers",
        "missing fingers",
        "deformed body",
        "duplicate character",
        "text",
        "watermark",
        "logo",
        "jpeg artifacts",
        "blurry",
    ),
    "illustrious": (
        "low quality",
        "worst quality",
        "bad anatomy",
        "bad hands",
        "malformed fingers",
        "extra fingers",
        "missing fingers",
        "poorly drawn face",
        "duplicate character",
        "text",
        "watermark",
        "logo",
        "jpeg artifacts",
        "blurry",
    ),
    "pony_v7": (
        "low resolution",
        "distorted hands",
        "extra fingers",
        "missing fingers",
        "broken limbs",
        "messy composition",
        "overexposed image",
        "blurry face",
        "duplicated character",
        "unreadable text",
        "watermark",
        "logo",
        "compression artifacts",
    ),
    "z_image": (),
    "anima": (
        "worst quality",
        "low quality",
        "score_1",
        "score_2",
        "score_3",
        "artist name",
        "bad anatomy",
        "bad hands",
        "malformed fingers",
        "extra fingers",
        "missing fingers",
        "text",
        "watermark",
        "logo",
        "blurry",
        "jpeg artifacts",
    ),
    "wan2_2_video": (
        "worst quality",
        "low quality",
        "blurry details",
        "text",
        "subtitles",
        "watermark",
        "flicker",
        "temporal jitter",
        "identity drift",
        "abrupt motion",
        "frozen motion",
        "inconsistent limbs",
        "deformed hands",
        "duplicate subject",
        "camera shake",
        "compression artifacts",
    ),
}

NEGATIVE_MARKERS = (
    "low quality",
    "worst quality",
    "bad anatomy",
    "bad hands",
    "malformed",
    "deformed",
    "artifact",
    "watermark",
    "blurry",
    "text",
)

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "background",
    "be",
    "behind",
    "by",
    "danbooru",
    "define",
    "description",
    "enabling",
    "factual",
    "film_grain",
    "foreground",
    "front",
    "for",
    "from",
    "her",
    "hers",
    "his",
    "image",
    "in",
    "into",
    "is",
    "it",
    "its",
    "medium",
    "model",
    "of",
    "on",
    "or",
    "remove_background",
    "render",
    "rendered",
    "shows",
    "stylistic",
    "that",
    "their",
    "them",
    "the",
    "this",
    "to",
    "tags",
    "test",
    "with",
}

LOW_VALUE_PROMPT_TERMS = {
    "ac_unit",
    "ability",
    "amazing",
    "answer",
    "answers",
    "architecture",
    "artificial",
    "baby_bottle",
    "balanced_composition",
    "beautiful",
    "best",
    "best_quality",
    "charger_cable",
    "change",
    "chain",
    "chains",
    "clay",
    "clear",
    "clean_lineart",
    "coffee",
    "compact",
    "concitable",
    "concise",
    "cool",
    "creative",
    "detailed_background",
    "detailed_character_design",
    "dynamic_pose",
    "dynamic",
    "enable",
    "enabled",
    "enabling",
    "enjoyable",
    "expressive_face",
    "feature",
    "fine",
    "high_detail",
    "masterpiece",
    "remove",
    "removed",
    "remove_background",
    "backgroundless",
    "define",
    "defined",
    "descriptive",
    "detailed",
    "detail",
    "details",
    "distant",
    "empty",
    "etc",
    "field",
    "fields",
    "filler",
    "fillers",
    "finest",
    "focus",
    "focused",
    "good",
    "great",
    "render",
    "rendered",
    "rendering",
    "importance",
    "interesting",
    "masterpieces",
    "material",
    "no",
    "place",
    "poynge",
    "pose",
    "readable",
    "reference",
    "show",
    "so",
    "source",
    "sources",
    "style",
    "overexposed",
    "quality",
    "race",
    "shape",
    "slay",
    "soft_shading",
    "suit",
    "tale",
    "test",
    "top_notch",
    "unit",
    "view",
    "views",
    "vivid",
    "vivid_colors",
    "wearing",
    "wears",
    "melt",
    "wood",
    "remaining",
}

GENERATED_TAG_NOISE = {
    "answer",
    "answers",
    "asking",
    "base",
    "base_tags",
    "base_prompt",
    "background_candidates",
    "background_prompt",
    "candidate",
    "candidates",
    "character",
    "current",
    "current_candidates",
    "discarded_noise",
    "empty",
    "establish",
    "established",
    "field",
    "fields",
    "fixed_base",
    "fixed_base_tags",
    "foreground_candidates",
    "foreground_prompt",
    "helper",
    "instruction",
    "instructions",
    "json",
    "label",
    "labels",
    "look",
    "looks",
    "main_subject",
    "must",
    "none",
    "other",
    "placeholder",
    "prompt",
    "prompts",
    "question",
    "questions",
    "required",
    "salad",
    "style_candidates",
    "subject",
    "truth",
    "unused",
    "use",
    "using",
    "valid",
    "value",
    "values",
    "word",
}

PONY_V6_BASE_TAGS = (
    "score_9",
    "score_8_up",
    "score_7_up",
)

PONY_V6_POLISH_TAGS = (
    "sharp_focus",
)

ILLUSTRIOUS_BASE_TAGS = (
    "masterpiece",
    "best_quality",
)

ILLUSTRIOUS_POLISH_TAGS = (
    "anime_illustration",
    "clean_linework",
    "detailed_subject",
)

PONY_V6_CONTEXT_EXPANSIONS = (
    (("phoenix",), ("wings", "feathers", "fiery_aura", "mythical_creature")),
    (("ogre",), ("large_creature", "muscular_body", "fantasy_monster", "tusks")),
    (("tapir",), ("tapir", "animal_focus", "long_snout")),
    (("applauding", "clapping"), ("clapping", "hands_together")),
    (("sharp",), ("sharp_focus", "crisp_edges")),
    (("artificial",), ("artificial_lighting", "synthetic_texture")),
    (("black_and_red", "black and red"), ("black_and_red_theme", "high_contrast_colors", "red_accents")),
    (("slay", "battle"), ("battle_scene", "action_pose", "dramatic_tension")),
    (("cave",), ("cave_interior", "rocky_walls", "dark_atmosphere")),
    (("melt", "melting"), ("molten_effects", "dripping_texture", "heat_haze")),
    (("beach",), ("ocean", "sand", "shoreline", "sunlight")),
    (("indoor", "interior", "room"), ("interior", "ambient_lighting")),
    (("close_shot", "close shot", "close_up", "close up"), ("close-up", "upper_body", "subject_focus")),
    (("capture_moment", "action_shot", "action shot"), ("action_shot", "motion", "candid_moment")),
    (("hidden", "deep"), ("atmospheric_depth", "mysterious_mood")),
    (("burnt", "scorched"), ("scorch_marks", "ash", "embers")),
    (("alien",), ("alien_artifact", "glowing_object", "sci-fi")),
    (("solarpunk",), ("solarpunk", "futuristic_architecture", "warm_light")),
    (("church", "temple", "shrine"), ("distant_architecture", "sacred_building")),
    (("landscape", "background"), ("wide_background", "environmental_depth")),
)


SYSTEM_INSTRUCTIONS = """You are a specialist prompt editor for anime and illustration image generation.
Turn chaotic random vocabulary into strong, coherent English prompts.

Rules:
- Return only valid JSON with exactly these string keys:
  base_prompt, foreground_prompt, background_prompt, negative, report
- Preserve the strongest visual ideas from the source words.
- Curate the input: remove contradictory, weak, duplicate, non-visual, or useless words.
- Never explain outside JSON.
- Keep all image prompts in English.
- Split the positive prompt into global model/style material, foreground subject detail, and background setting detail. For Z-Image, write natural descriptive prose instead of tags.
- For Anima, begin with one compact quality-tag line, then write long natural English prose made of short simple sentences.
- For Anima, order the prose from the main figure through appearance, action, and objects to environment, emotion, and atmosphere.
- Pony v6 and Pony v7 are model names, not subjects. Do not add a pony, horse, or equine character unless the input explicitly asks for one.
- Do not invent copyrighted character names unless they appear in the input or style anchor.
- If the input implies adult content, keep wording as neutral image-generation tags and do not add explicit acts.
- Negative prompts: conservative model-appropriate quality/anatomy/artifact negatives, text/watermark/logo, duplicates, distorted hands, messy composition. For Z-Image, leave negative empty.
- For Anima, use safety/content tags only when safe, sensitive, nsfw, explicit, or guro appear in the source text or style anchor; do not add a default safety tag.
- Report: one short sentence naming the retained core idea and what was discarded."""


def _normalize_generate_url(ollama_url):
    url = str(ollama_url).strip() or DEFAULT_OLLAMA_URL
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    url = url.rstrip("/")
    if url.endswith("/api/generate"):
        return url
    return f"{url}/api/generate"


def _normalize_tags_url(ollama_url):
    url = str(ollama_url).strip() or DEFAULT_OLLAMA_URL
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    return f"{url.rstrip('/')}/api/tags"


def _ollama_model_names(ollama_url=DEFAULT_OLLAMA_URL):
    models = []
    request = urllib.request.Request(_normalize_tags_url(ollama_url), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=1) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError):
        data = {}

    for model in data.get("models", []):
        name = str(model.get("name") or model.get("model") or "").strip()
        if name and name not in models:
            models.append(name)

    return models


def _available_ollama_models(ollama_url=DEFAULT_OLLAMA_URL):
    models = _ollama_model_names(ollama_url)
    return models or [DEFAULT_OLLAMA_MODEL]


def _register_routes():
    if web is None or PromptServer is None:
        return

    routes = PromptServer.instance.routes

    @routes.get("/nukun/ollama/models")
    async def get_ollama_models(request):
        ollama_url = request.query.get("url", DEFAULT_OLLAMA_URL)
        models = _ollama_model_names(ollama_url)
        return web.json_response(
            {
                "url": ollama_url,
                "models": models,
                "fallback": DEFAULT_OLLAMA_MODEL if not models else "",
            }
        )


_register_routes()


def _is_reka_flash_model(model):
    normalized = str(model).lower()
    return "reka-flash" in normalized or "reka_flash" in normalized


def _reka_output_contract():
    return """You are a JSON-only image prompt refiner.
Use the user's prompt-building instructions, but return only the final JSON object.
Do not reveal reasoning, analysis, markdown, code fences, notes, or commentary.
Do not output <reasoning>, </reasoning>, <think>, or </think> tags.
The JSON object must contain exactly these string keys:
base_prompt, foreground_prompt, background_prompt, negative, report"""


def _build_reka_prompt(prompt):
    return (
        "human: "
        + _reka_output_contract()
        + "\n\nTask instructions:\n"
        + str(prompt).strip()
        + "\n\nFinal answer: return exactly one valid JSON object and nothing else."
        + " <sep> assistant:"
    )


def _strip_reasoning_blocks(value):
    text = str(value).strip()
    text = re.sub(r"(?is)<\s*reasoning\s*>.*?<\s*/\s*reasoning\s*>", "", text)
    text = re.sub(r"(?is)<\s*think\s*>.*?<\s*/\s*think\s*>", "", text)
    text = re.sub(r"(?is)^.*?<\s*/\s*reasoning\s*>", "", text)
    text = re.sub(r"(?is)^.*?<\s*/\s*think\s*>", "", text)
    return text.strip()


def _request_ollama(ollama_url, model, prompt, seed, temperature, top_p, timeout_seconds, context_length=DEFAULT_OLLAMA_CONTEXT_LENGTH):
    model_name = str(model).strip() or DEFAULT_OLLAMA_MODEL
    is_reka = _is_reka_flash_model(model_name)
    options = {
        "seed": int(seed),
        "temperature": float(temperature),
        "top_p": float(top_p),
        "num_ctx": _normalize_context_length(context_length),
        "num_predict": 1400,
    }
    if is_reka:
        options["stop"] = ["<sep>", "<|endoftext|>"]

    payload = {
        "model": model_name,
        "prompt": _build_reka_prompt(prompt) if is_reka else prompt,
        "stream": False,
        "format": OUTPUT_SCHEMA,
        "options": options,
    }
    if not is_reka:
        payload["system"] = SYSTEM_INSTRUCTIONS

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        _normalize_generate_url(ollama_url),
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=max(1, int(timeout_seconds))) as response:
            response_data = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama Prompt Refiner: Ollama HTTP {error.code}: {body}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Ollama Prompt Refiner: could not reach Ollama at {ollama_url}: {error.reason}") from error
    except TimeoutError as error:
        raise RuntimeError(f"Ollama Prompt Refiner: Ollama request timed out after {timeout_seconds} seconds") from error

    try:
        envelope = json.loads(response_data)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Ollama Prompt Refiner: invalid Ollama response envelope: {error}") from error

    if not envelope.get("done", False):
        raise RuntimeError("Ollama Prompt Refiner: Ollama response did not finish cleanly")

    response_text = str(envelope.get("response", "")).strip()
    return _strip_reasoning_blocks(response_text)


def _extract_json_object(text):
    text = str(text).strip()
    if not text:
        raise ValueError("empty response")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("response does not contain a JSON object")

    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as error:
        raise ValueError(str(error)) from error


def _validate_result(data):
    if not isinstance(data, dict):
        raise ValueError("JSON root is not an object")

    if all(key in data for key in RESPONSE_KEYS):
        keys = RESPONSE_KEYS
    elif all(key in data for key in LEGACY_RESPONSE_KEYS):
        keys = LEGACY_RESPONSE_KEYS
    else:
        expected = " or ".join(("{base_prompt, foreground_prompt, background_prompt, negative, report}", "{positive, negative, report}"))
        available = ", ".join(sorted(str(key) for key in data.keys()))
        raise ValueError(f"missing result keys; expected {expected}; available: {available}")

    values = {key: str(data[key]).strip() for key in keys}
    empty = [key for key, value in values.items() if not value and key != "negative"]
    if empty:
        raise ValueError(f"empty keys: {', '.join(empty)}")

    return values


def _normalize_style_cluster(style_cluster):
    try:
        value = int(style_cluster)
    except (TypeError, ValueError):
        value = DEFAULT_STYLE_CLUSTER
    return max(0, min(2048, value))


def _normalize_context_length(context_length):
    try:
        value = int(context_length)
    except (TypeError, ValueError):
        value = DEFAULT_OLLAMA_CONTEXT_LENGTH
    return max(512, min(262144, value))


def _normalize_target_profile(target_profile):
    profile = str(target_profile).strip().lower()
    if profile in TARGET_PROFILES:
        return profile
    return DEFAULT_TARGET_PROFILE


def _is_model_meta_term(normalized):
    compact = re.sub(r"[^a-z0-9]+", "_", str(normalized).lower()).strip("_")
    if re.fullmatch(r"pony_v?\d+", compact):
        return True
    if re.fullmatch(r"(character|subject)_v?\d+(?:_sdxl)?", compact):
        return True
    if compact in {"character_sdxl", "subject_sdxl"}:
        return True
    return compact in {
        "pony_6",
        "pony_7",
        "pony_v6",
        "pony_v7",
        "character_6",
        "character_7",
        "character_v6",
        "character_v7",
        "character_6_sdxl",
        "character_7_sdxl",
        "subject_6",
        "subject_7",
        "subject_v6",
        "subject_v7",
    }


def _is_low_value_prompt_term(normalized):
    compact = re.sub(r"[^a-z0-9]+", "_", str(normalized).lower()).strip("_")
    return compact in LOW_VALUE_PROMPT_TERMS


def _source_allows_equine(word_salad, style_anchor):
    return bool(EQUINE_PATTERN.search(f"{word_salad} {style_anchor}"))


def _remove_model_name_leaks(value):
    value = MODEL_LABEL_PATTERN.sub("character", value)
    value = MODEL_VERSION_LEAK_PATTERN.sub(lambda match: match.group(1), value)
    replacements = {
        "pony": "character",
        "ponies": "characters",
        "horse": "character",
        "horses": "characters",
        "equine": "character",
        "stallion": "character",
        "mare": "character",
        "foal": "character",
    }

    def replace(match):
        text = match.group(0)
        replacement = replacements[text.lower()]
        if text[:1].isupper():
            return replacement.capitalize()
        return replacement

    return EQUINE_PATTERN.sub(replace, value)


def _has_negative_markers(value):
    lowered = value.lower()
    return any(marker in lowered for marker in NEGATIVE_MARKERS)


def _negative_prompt_is_unusable(value):
    lowered = str(value).lower()
    if _word_count(lowered) > 45:
        return True
    return any(
        marker in lowered
        for marker in (
            "base_prompt",
            "fixed_base",
            "foreground_prompt",
            "background_prompt",
            "and so on",
            "bad focus",
            "bad teeth",
            "bad handshakes",
            "bad handles",
            "best quality",
            "best_quality",
            "conservative model-appropriate",
            "describes the situation",
            "do not treat",
            "dull eyes",
            "field report",
            "heart attack",
            "non aesthetic",
            "non-artistic",
            "non desirable",
            "non-desirable",
            "non-aesthetic",
            "non-readable",
            "non-existent",
            "not the pony",
            "non-viable options",
            "negative words",
            "positive prompt",
            "source rating",
            "target profile",
            "unpleasant experience",
            "useless random objects",
            "weak descriptions",
        )
    )


def _with_negative_baseline(target_profile, value):
    baseline_terms = NEGATIVE_BASELINES.get(_normalize_target_profile(target_profile))
    if not baseline_terms:
        return value

    if _negative_prompt_is_unusable(value) or not _has_negative_markers(value):
        return ", ".join(baseline_terms)

    result = value
    lowered = result.lower()
    for term in baseline_terms:
        if term.lower() not in lowered:
            result = f"{result}, {term}"
            lowered = result.lower()
    return result


def _strip_commas_for_profile(target_profile, value):
    if _normalize_target_profile(target_profile) in ("pony_v7", "z_image", "anima", "wan2_2_video"):
        return value
    return re.sub(r"\s+", " ", str(value).replace(",", " ")).strip()


ANIMA_SAFETY_TAGS = ("safe", "sensitive", "nsfw", "explicit", "guro")
ANIMA_QUALITY_TAGS = ("masterpiece", "best quality", "score_9", "score_8_up", "score_7_up")
ANIMA_BASE_STYLE_TAGS = ("anime illustration", "digital art", "clean linework")


def _anima_safety_tags(*values):
    source = " ".join(str(value) for value in values)
    normalized = re.sub(r"[_-]+", " ", source.lower())
    found = []
    for tag in ANIMA_SAFETY_TAGS:
        if re.search(rf"\b{re.escape(tag)}\b", normalized):
            found.append(tag)
    return found


def _normalize_anima_tag(value):
    tag = str(value).strip().lower()
    tag = re.sub(
        r"(?i)^\s*(?:base_prompt|foreground_prompt|background_prompt|positive|negative|report|subject(?:\s+and\s+action)?|environment(?:\s+and\s+light)?)\s*[:=-]\s*",
        "",
        tag,
    )
    tag = tag.strip(" .:;()[]{}\"'")
    tag = re.sub(r"\s+", " ", tag)
    tag = re.sub(r"[^a-z0-9_ @.+:-]+", " ", tag)
    tag = re.sub(r"\s+", " ", tag).strip(" .:;")
    compact = tag.replace(" ", "_")
    if not compact or compact in GENERATED_TAG_NOISE or compact.startswith("style_cluster_"):
        return ""
    if _is_model_meta_term(compact) or re.fullmatch(r"rating_[a-z0-9_]+", compact):
        return ""
    if compact.startswith("source_"):
        compact = compact.removeprefix("source_")
        tag = compact
    if re.fullmatch(r"score_\d+(?:_up)?", compact):
        return compact
    tag = tag.replace("_", " ")
    tag = re.sub(r"\s+", " ", tag).strip()
    if not tag or tag in STOPWORDS:
        return ""
    if _is_low_value_prompt_term(tag.replace(" ", "_")) and tag.replace(" ", "_") not in {
        "masterpiece",
        "best_quality",
        "anime_illustration",
        "digital_art",
    }:
        return ""
    return tag


def _anima_tag_text(values, limit=32, fallback=""):
    if isinstance(values, str):
        raw_items = re.split(r"[,;|\n]+", values)
        if len(raw_items) == 1:
            raw_items = re.split(r"\s{2,}|\t+", values)
    else:
        raw_items = list(values or ())

    tags = []
    seen = set()
    for raw in raw_items:
        if isinstance(raw, (list, tuple, set)):
            nested = _anima_tag_text(raw, limit=limit, fallback="")
            candidates = nested.split(",") if nested else []
        else:
            candidates = [raw]
        for candidate in candidates:
            tag = _normalize_anima_tag(candidate)
            key = tag.replace(" ", "_")
            if not tag or key in seen:
                continue
            seen.add(key)
            tags.append(tag)
            if len(tags) >= limit:
                return ", ".join(tags)
    return ", ".join(tags) if tags else fallback


def _anima_tags(values, limit=32):
    text = _anima_tag_text(values, limit=limit, fallback="")
    return [tag.strip() for tag in text.split(",") if tag.strip()]


def _anima_anchor_style_tags(style_anchor, limit=10):
    tags = []
    for raw_tag in re.split(r"[,;|\n]+", str(style_anchor).strip()):
        cleaned = str(raw_tag)
        for safety_tag in ANIMA_SAFETY_TAGS:
            cleaned = re.sub(rf"\b{re.escape(safety_tag)}\b", " ", cleaned, flags=re.IGNORECASE)
        normalized = _normalize_anima_tag(cleaned)
        if not normalized or normalized in ANIMA_SAFETY_TAGS:
            continue
        if _term_is_background_like(normalized):
            continue
        tags.append(normalized)
    if not tags:
        for tag in _tokenize_prompt_tags(style_anchor, limit=limit * 3, filter_generated_noise=True):
            normalized = _normalize_anima_tag(tag)
            if normalized and normalized not in ANIMA_SAFETY_TAGS and not _term_is_background_like(normalized):
                tags.append(normalized)
    return _anima_tags(tags, limit=limit)


def _clean_report(report, target_profile, word_salad, style_anchor):
    report = re.sub(r"\s+", " ", str(report).replace(",", " ")).strip()
    lowered = report.lower()
    if lowered.startswith("built one ") or "parser detail:" in lowered:
        return report

    terms = _curated_terms(f"{style_anchor} {word_salad}", limit=8)
    core = " ".join(_prompt_token(term) for term in terms[:5]) if terms else "curated visual terms"
    profile_label = {
        "pony_v6": "Pony v6",
        "illustrious": "Illustrious",
        "pony_v7": "Pony v7",
        "z_image": "Z-Image",
        "anima": "Anima",
        "wan2_2_video": "Wan 2.2 video",
    }.get(_normalize_target_profile(target_profile), "selected profile")
    return f"Built one {profile_label} prompt from {core} and removed weak filler terms"


def _postprocess_result(values, target_profile, word_salad, style_anchor, style_cluster=DEFAULT_STYLE_CLUSTER):
    target_profile = _normalize_target_profile(target_profile)
    allow_equine = _source_allows_equine(word_salad, style_anchor)
    style_cluster = _normalize_style_cluster(style_cluster)
    if isinstance(values, dict):
        data = {key: str(value).strip() for key, value in values.items()}
    else:
        data = {key: value for key, value in zip(LEGACY_RESPONSE_KEYS, values)}

    positive = str(data.get("positive", "")).strip()
    base_prompt = str(data.get("base_prompt", "")).strip()
    foreground_prompt = str(data.get("foreground_prompt", "")).strip()
    background_prompt = str(data.get("background_prompt", "")).strip()
    if not positive:
        positive = _join_positive_parts(target_profile, base_prompt, foreground_prompt, background_prompt)
    negative = str(data["negative"]).strip()
    report = str(data["report"]).strip()

    if not allow_equine:
        positive = _remove_model_name_leaks(positive)
        base_prompt = _remove_model_name_leaks(base_prompt)
        foreground_prompt = _remove_model_name_leaks(foreground_prompt)
        background_prompt = _remove_model_name_leaks(background_prompt)
        negative = _remove_model_name_leaks(negative)
        report = _remove_model_name_leaks(report)

    negative = _with_negative_baseline(target_profile, negative)
    if target_profile == "z_image":
        provided = {
            "base_prompt": base_prompt,
            "foreground_prompt": foreground_prompt,
            "background_prompt": background_prompt,
        }
        base_prompt, foreground_prompt, background_prompt = _z_image_prompt_parts(
            positive,
            word_salad,
            style_anchor,
            provided if any(provided.values()) else None,
        )
        positive = _join_positive_parts(target_profile, base_prompt, foreground_prompt, background_prompt)
        negative = ""
    elif target_profile in ("pony_v6", "illustrious"):
        provided = {
            "base_prompt": base_prompt,
            "foreground_prompt": foreground_prompt,
            "background_prompt": background_prompt,
        }
        base_prompt, foreground_prompt, background_prompt = _light_tag_prompt_parts(
            target_profile,
            word_salad,
            style_anchor,
            provided if any(provided.values()) else None,
        )
        positive = _join_positive_parts(target_profile, base_prompt, foreground_prompt, background_prompt)
    elif target_profile == "anima":
        provided = {
            "base_prompt": base_prompt,
            "foreground_prompt": foreground_prompt,
            "background_prompt": background_prompt,
        }
        base_prompt, foreground_prompt, background_prompt = _anima_prompt_parts(
            positive,
            word_salad,
            style_anchor,
            provided if any(provided.values()) else None,
        )
        positive = _join_positive_parts(target_profile, base_prompt, foreground_prompt, background_prompt)
    elif target_profile == "wan2_2_video":
        if not base_prompt:
            base_prompt = "cinematic video, coherent lighting, stable camera, consistent visual style"
        if not foreground_prompt:
            foreground_prompt = positive or "A clearly visible subject performs one continuous, readable action."
        if not background_prompt:
            background_prompt = "The environment remains spatially consistent while natural secondary motion supports the action."
        positive = _join_positive_parts(target_profile, base_prompt, foreground_prompt, background_prompt)
    else:
        base_prompt, foreground_prompt, background_prompt = _structured_pony_v7_parts(
            positive,
            word_salad,
            style_anchor,
            style_cluster,
        )
        positive = _join_positive_parts(target_profile, base_prompt, foreground_prompt, background_prompt)

    base_prompt = _strip_commas_for_profile(target_profile, base_prompt)
    foreground_prompt = _strip_commas_for_profile(target_profile, foreground_prompt)
    background_prompt = _strip_commas_for_profile(target_profile, background_prompt)
    if target_profile not in ("pony_v7", "z_image", "wan2_2_video"):
        positive = _join_positive_parts(target_profile, base_prompt, foreground_prompt, background_prompt)
    positive = _strip_commas_for_profile(target_profile, positive)
    negative = _strip_commas_for_profile(target_profile, negative)
    report = _clean_report(report, target_profile, word_salad, style_anchor)

    return (positive, negative, report, base_prompt, foreground_prompt, background_prompt)


def _curated_terms(text, limit=28, filter_low_value=True):
    terms = []
    seen = set()
    for raw_term in re.split(r"[\s,;|]+", str(text).strip()):
        term = raw_term.strip(" .:()[]{}\"'")
        if not term:
            continue
        normalized = term.lower()
        if (
            normalized in STOPWORDS
            or normalized in seen
            or _is_model_meta_term(normalized)
            or (filter_low_value and _is_low_value_prompt_term(normalized))
            or normalized.isdigit()
            or not re.search(r"[a-zA-Z0-9]", normalized)
            or normalized.startswith(("score_", "rating_", "style_cluster_"))
            or re.fullmatch(r"tag\d+", normalized)
        ):
            continue
        seen.add(normalized)
        terms.append(term.replace("_", " "))
        if len(terms) >= limit:
            break
    return terms


def _prompt_token(value):
    token = re.sub(r"[^a-zA-Z0-9_<>,.:+-]+", "_", str(value).strip().lower())
    token = re.sub(r"_+", "_", token).strip("_")
    token = re.sub(r"^source_", "", token)
    return token


def _dedupe_terms(terms):
    result = []
    seen = set()
    for term in terms:
        clean = str(term).strip()
        if not clean:
            continue
        normalized = re.sub(r"\s+", "_", clean.lower())
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(clean)
    return result


def _contextual_pony_v6_tags(terms):
    joined = " ".join(terms).lower()
    result = []
    for triggers, expansions in PONY_V6_CONTEXT_EXPANSIONS:
        if any(trigger in joined for trigger in triggers):
            result.extend(expansions)
    return result


def _pony_v6_stopword_ratio(value):
    words = re.findall(r"\b[a-zA-Z]+\b", str(value).lower())
    if not words:
        return 0.0
    return sum(1 for word in words if word in STOPWORDS) / len(words)


def _needs_pony_v6_refine(prompt):
    prompt = str(prompt)
    lowered = prompt.lower()
    has_bad_terms = any(_is_model_meta_term(term) or _is_low_value_prompt_term(term) for term in re.split(r"[\s,;|]+", lowered))
    return "," not in prompt or _word_count(prompt) < 18 or _pony_v6_stopword_ratio(prompt) > 0.18 or has_bad_terms


def _source_content_tags(word_salad, value, style_anchor, limit=12):
    anchor_terms = {_prompt_token(term) for term in _curated_terms(style_anchor, limit=48)}
    source_terms = _curated_terms(word_salad, limit=28, filter_low_value=False)
    if not source_terms:
        source_terms = _curated_terms(value, limit=28, filter_low_value=False)
    content_tags = [_prompt_token(term) for term in source_terms]
    return [
        tag
        for tag in content_tags
        if tag
        and tag not in STOPWORDS
        and tag not in anchor_terms
        and not _is_model_meta_term(tag)
        and not _is_low_value_prompt_term(tag)
    ][:limit], source_terms


def _refined_pony_v6_prompt(value, word_salad, style_anchor):
    if not _needs_pony_v6_refine(value):
        return value

    anchor = str(style_anchor).strip()
    content_tags, source_terms = _source_content_tags(word_salad, value, anchor, limit=10)
    expansion_tags = [_prompt_token(term) for term in _contextual_pony_v6_tags(source_terms)]

    parts = list(PONY_V6_BASE_TAGS)
    if anchor:
        parts.append(anchor)
    parts.extend(content_tags[:12])
    parts.extend(expansion_tags)
    parts.extend(PONY_V6_POLISH_TAGS)
    return ", ".join(_dedupe_terms(parts)[:32])


def _needs_illustrious_refine(prompt):
    prompt = str(prompt)
    lowered = prompt.lower()
    has_bad_terms = any(_is_model_meta_term(term) or _is_low_value_prompt_term(term) for term in re.split(r"[\s,;|]+", lowered))
    return _word_count(prompt) < 10 or _pony_v6_stopword_ratio(prompt) > 0.14 or has_bad_terms


def _refined_illustrious_prompt(value, word_salad, style_anchor):
    if not _needs_illustrious_refine(value):
        return value

    anchor = str(style_anchor).strip()
    content_tags, source_terms = _source_content_tags(word_salad, value, anchor, limit=12)
    expansion_tags = [_prompt_token(term) for term in _contextual_pony_v6_tags(source_terms)]

    parts = list(ILLUSTRIOUS_BASE_TAGS)
    if anchor:
        parts.append(anchor)
    parts.extend(content_tags)
    parts.extend(expansion_tags[:10])
    parts.extend(ILLUSTRIOUS_POLISH_TAGS)
    return ", ".join(_dedupe_terms(parts)[:30])


def _tags_from_terms(terms, limit=18):
    tags = []
    for term in terms:
        tag = _prompt_token(term)
        if tag and tag not in STOPWORDS and not _is_model_meta_term(tag) and not _is_low_value_prompt_term(tag):
            tags.append(tag)
    return _dedupe_terms(tags)[:limit]


def _term_is_background_like(term):
    normalized = str(term).lower()
    return any(_term_matches_keyword(normalized, keyword) for keyword in TAG_PROFILE_BACKGROUND_KEYWORDS)


def _term_is_pony_v6_style_like(term):
    normalized = str(term).lower()
    return any(_term_matches_keyword(normalized, keyword) for keyword in PONY_V6_STYLE_KEYWORDS)


def _tag_is_pony_v6_background_noise(tag):
    key = _split_tag_key(tag)
    compact = key.replace(" ", "_")
    if compact in PONY_V6_FOREGROUND_BLOCKLIST_FOR_BACKGROUND:
        return True
    return any(part in PONY_V6_FOREGROUND_BLOCKLIST_FOR_BACKGROUND for part in compact.split("_"))


def _pony_v6_background_tags_from_terms(terms, limit=24):
    tags = []
    for term in terms:
        if not _term_is_background_like(term):
            continue
        for tag in _tags_from_terms((term,), limit=4):
            if not _tag_is_pony_v6_background_noise(tag):
                tags.append(tag)
    return _dedupe_terms(tags)[:limit]


def _pony_v6_foreground_tags_from_terms(terms, limit=36):
    tags = []
    for term in terms:
        if _term_is_background_like(term) or _term_is_pony_v6_style_like(term):
            continue
        tags.extend(_tags_from_terms((term,), limit=4))
    return _dedupe_terms(tags)[:limit]


def _candidate_tag_text(tags, fallback="none"):
    cleaned = [_normalize_split_tag(tag) for tag in tags]
    cleaned = [tag for tag in _dedupe_split_tags(cleaned) if tag]
    return " ".join(cleaned) if cleaned else fallback


def _candidate_terms_text(terms, fallback="none"):
    tags = _tags_from_terms(terms, limit=32)
    return _candidate_tag_text(tags, fallback)


def _candidate_discarded_noise(word_salad, style_anchor, limit=18):
    discarded = []
    seen = set()
    for raw_term in re.split(r"[\s,;|]+", str(word_salad).strip()):
        clean = raw_term.strip(" .:()[]{}\"'")
        if not clean:
            continue
        tag = _prompt_token(clean)
        key = _split_tag_key(tag)
        compact = key.replace(" ", "_")
        if not compact or compact in seen:
            continue
        if compact.startswith(("score_", "rating_", "source_")) or _is_model_meta_term(compact):
            continue
        if (
            clean.lower() in STOPWORDS
            or _is_low_value_prompt_term(compact)
            or _is_generated_tag_noise(compact)
        ):
            discarded.append(compact)
            seen.add(compact)
        if len(discarded) >= limit:
            break
    return discarded


def _generic_foreground_tags_from_terms(terms, limit=36):
    tags = []
    for term in terms:
        if _term_is_background_like(term) or _term_is_pony_v6_style_like(term):
            continue
        tags.extend(_tags_from_terms((term,), limit=4))
    return _dedupe_terms(tags)[:limit]


def _style_tags_from_terms(terms, limit=18):
    tags = []
    for term in terms:
        if _term_is_pony_v6_style_like(term):
            tags.extend(_tags_from_terms((term,), limit=4))
    return _dedupe_terms(tags)[:limit]


def _candidate_data(target_profile, word_salad, style_anchor):
    target_profile = _normalize_target_profile(target_profile)
    if target_profile not in ("pony_v6", "illustrious", "anima"):
        return {}

    source_terms = _curated_terms(word_salad, limit=48, filter_low_value=False)
    anchor_tags = _tokenize_prompt_tags(style_anchor, limit=24, filter_generated_noise=True)

    if target_profile == "pony_v6":
        fixed_base_tags = list(PONY_V6_BASE_TAGS)
        fixed_base_tags.extend(anchor_tags)
        fixed_base_tags.extend(("anime_illustration", "sharp_focus", "clean_linework", "best_quality"))
        foreground_tags = _pony_v6_foreground_tags_from_terms(source_terms, limit=36)
    else:
        if target_profile == "anima":
            fixed_base_tags = ("masterpiece", "best_quality", "score_9", "score_8_up", "score_7_up", *_anima_safety_tags(word_salad, style_anchor))
            fixed_base_tags = list(fixed_base_tags)
            fixed_base_tags.extend(anchor_tags)
            fixed_base_tags.extend(("anime_illustration", "digital_art", "clean_linework"))
        else:
            fixed_base_tags = list(ILLUSTRIOUS_BASE_TAGS)
            fixed_base_tags.extend(anchor_tags)
            fixed_base_tags.extend(("amazing_quality", "very_aesthetic", "polished_illustration", "soft_shading", "sharp_linework"))
        foreground_tags = _generic_foreground_tags_from_terms(source_terms, limit=36)

    background_tags = _pony_v6_background_tags_from_terms(source_terms, limit=30)
    background_tags.extend(_tag_profile_background_preset_tags(source_terms))
    style_tags = _style_tags_from_terms(source_terms, limit=18)
    discarded_noise = _candidate_discarded_noise(word_salad, style_anchor, limit=18)

    return {
        "fixed_base_tags": _dedupe_split_tags(fixed_base_tags),
        "foreground_candidates": _dedupe_split_tags(foreground_tags),
        "background_candidates": _dedupe_split_tags(background_tags),
        "style_candidates": _dedupe_split_tags(style_tags),
        "discarded_noise": _dedupe_split_tags(discarded_noise),
    }


def _build_candidate_context(target_profile, word_salad, style_anchor):
    data = _candidate_data(target_profile, word_salad, style_anchor)
    if not data:
        return ""

    return f"""Pre-sorted candidate ingredients:
fixed_base_tags: {_candidate_tag_text(data["fixed_base_tags"])}
foreground_candidates: {_candidate_tag_text(data["foreground_candidates"])}
background_candidates: {_candidate_tag_text(data["background_candidates"])}
style_candidates: {_candidate_tag_text(data["style_candidates"])}
discarded_noise: {_candidate_tag_text(data["discarded_noise"])}

Use the candidate lists as the main source of truth.
You may add a few fitting visual details when they clarify the image.
Do not move foreground candidates into background_prompt.
Do not move background candidates into foreground_prompt.
For Pony v6 and Illustrious, write background_prompt as concrete visible background tags.
For Anima, turn the candidate ingredients into short natural sentences rather than copying them as a tag list.
If background_candidates name a setting, expand that setting with matching visible objects from that same kind of place.
Do not borrow objects from unrelated example settings.
Do not copy candidate-list names, empty markers, or instruction words into any output value.
The raw word salad below is only a reference for context."""


FOREGROUND_TAG_FILLERS = (
    "clear_subject",
    "readable_pose",
    "focused_expression",
    "visible_silhouette",
    "defined_anatomy",
    "material_texture",
    "outfit_detail",
    "surface_highlights",
    "gesture_focus",
    "foreground_presence",
    "sharp_focal_point",
    "character_detail",
    "body_orientation",
    "layered_shapes",
    "clean_edges",
    "intentional_action",
    "visible_props",
    "balanced_subject",
    "pose_readability",
    "fine_details",
    "subject_focus",
    "expressive_design",
    "controlled_motion",
    "clear_contact_points",
)

BACKGROUND_TAG_FILLERS = (
    "detailed_background",
    "environmental_depth",
    "middle_ground",
    "distant_background",
    "atmospheric_haze",
    "visible_setting",
    "spatial_layering",
    "background_props",
    "ambient_lighting",
    "environmental_color",
    "distant_objects",
    "setting_detail",
    "ground_surface",
    "far_horizon",
    "surrounding_space",
    "depth_cues",
    "scene_context",
    "background_texture",
    "local_atmosphere",
    "scale_variation",
    "soft_distance",
    "clear_location",
    "supporting_scenery",
    "placed_environment",
    "coastline_detail",
    "pathway_detail",
    "noir_atmosphere",
    "safety_equipment",
    "travel_marker",
    "surface_detail",
    "scene_anchor",
    "local_landmark",
    "weathered_material",
    "directional_light",
    "environmental_shadow",
    "layered_depth",
    "setting_context",
    "background_anchor",
    "distant_structure",
    "ambient_detail",
)

TAG_PROFILE_MINIMAL_BACKGROUND_TAGS = (
    "quiet_room",
    "plain_wall",
    "wooden_floor",
    "soft_window_light",
    "small_table",
    "curtains",
    "quiet_shelves",
    "distant_doorway",
    "ceiling_light",
    "side_chair",
    "carpet",
    "wall_pictures",
    "potted_plant",
    "floor_boards",
    "muted_wallpaper",
    "shadowed_corner",
    "wooden_door",
    "window_frame",
)

TAG_PROFILE_BACKGROUND_WORD_RANGE = (30, 40)

FOREGROUND_EXPANSIONS = (
    (("latex",), ("glossy_latex", "reflective_material", "tight_surface", "specular_highlights")),
    (("lion",), ("lion_focus", "mane_detail", "fur_texture", "animal_features", "claws")),
    (("blurring", "blur"), ("motion_blur", "soft_edges", "speed_effect", "movement_trail")),
    (("blended",), ("blended_colors", "merged_shapes", "soft_transition", "layered_forms")),
    (("blobby",), ("rounded_shapes", "soft_volume", "organic_form", "bulging_surface")),
    (("break_apart", "break apart"), ("fragmented_motion", "separating_pieces", "impact_detail", "scattered_fragments")),
    (("notice", "listen_to", "listen to"), ("alert_expression", "attentive_pose", "turned_head", "listening_focus")),
    (("group_shot", "group shot"), ("multiple_subjects", "group_composition", "shared_focus", "subject_spacing")),
    (("jigsaw",), ("puzzle_piece", "interlocking_shapes", "cut_edges", "fragment_pattern")),
)

BACKGROUND_EXPANSIONS = (
    (("coast",), ("coastal_setting", "shoreline_detail", "distant_water", "windy_atmosphere")),
    (("mountain",), ("mountain_background", "rocky_slope", "distant_peak", "highland_landscape", "open_sky")),
    (("iraq",), ("arid_landscape", "sun_bleached_stone", "dusty_air", "distant_architecture", "desert_light")),
    (("sepia",), ("sepia_atmosphere", "warm_tint", "aged_color", "muted_contrast")),
    (("luggage_tag", "luggage tag"), ("travel_tag", "suitcase_detail", "paper_label", "travel_prop")),
    (("lens_cap", "lens cap"), ("camera_accessory", "small_plastic_cap", "photography_prop", "nearby_gear")),
    (("jigsaw",), ("scattered_puzzle_pieces", "tabletop_detail", "interlocking_pattern", "background_puzzle")),
    (("group_shot", "group shot"), ("wide_scene_space", "shared_environment", "crowd_spacing", "scene_depth")),
)

TAG_PROFILE_BACKGROUND_PRESETS = (
    (
        ("forest", "woods", "woodland", "wilderness"),
        (
            "dark_forest",
            "tall_trees",
            "mushrooms",
            "glowing_crystals",
            "mossy_ground",
            "twisted_roots",
            "misty_path",
            "fallen_leaves",
            "tree_trunks",
            "fern_patches",
            "shadowed_bushes",
            "distant_clearing",
            "wet_stones",
            "forest_floor",
            "small_stream",
            "hollow_log",
            "moonlit_fog",
            "scattered_ferns",
        ),
    ),
    (
        ("room", "living_room", "living room", "indoor", "indoors", "house", "apartment"),
        (
            "living_room",
            "sofa",
            "window",
            "curtains",
            "table_lamp",
            "carpet",
            "bookshelves",
            "coffee_table",
            "wall_pictures",
            "wooden_floor",
            "potted_plant",
            "city_view",
            "doorway",
            "cushions",
            "soft_window_light",
            "side_chair",
            "houseplants",
            "distant_city_rooftops",
        ),
    ),
    (
        ("city", "street", "town", "downtown", "german"),
        (
            "german_city",
            "city_street",
            "apartment_buildings",
            "lit_windows",
            "street_lamps",
            "shop_signs",
            "pavement",
            "distant_traffic",
            "balconies",
            "brick_walls",
            "parked_cars",
            "crosswalk",
            "tram_lines",
            "evening_sky",
            "storefront_windows",
            "traffic_lights",
            "distant_rooftops",
            "wet_asphalt",
        ),
    ),
    (
        ("airport", "terminal", "station"),
        (
            "airport_terminal",
            "large_windows",
            "luggage_carts",
            "departure_boards",
            "glass_walls",
            "waiting_seats",
            "polished_floor",
            "security_gate",
            "terminal_signs",
            "distant_passengers",
            "overhead_lights",
            "boarding_area",
            "metal_railings",
            "runway_view",
            "glass_doors",
            "ceiling_panels",
            "information_kiosks",
            "baggage_belts",
        ),
    ),
)

TAG_PROFILE_KNOWN_SETTING_KEYS = {
    "airport",
    "airport terminal",
    "apartment",
    "bathroom",
    "beach",
    "bedroom",
    "city",
    "city street",
    "forest",
    "garden",
    "german city",
    "house",
    "indoor",
    "indoors",
    "interior",
    "kitchen",
    "living",
    "living room",
    "room",
    "station",
    "street",
    "terminal",
    "town",
    "wilderness",
    "woodland",
    "woods",
}


def _is_generated_tag_noise(tag):
    key = _split_tag_key(tag)
    if not key or len(key) <= 1:
        return True
    compact = key.replace(" ", "_")
    if compact.startswith("style_cluster_"):
        return True
    if compact in GENERATED_TAG_NOISE or key in GENERATED_TAG_NOISE:
        return True
    return _is_low_value_prompt_term(compact)


def _tokenize_prompt_tags(value, limit=64, filter_generated_noise=False):
    tags = []
    for raw_term in re.split(r"[\s,;|]+", str(value).strip()):
        raw_clean = raw_term.strip()
        tag = _prompt_token(raw_clean)
        if raw_clean.lower().startswith("source_") and tag and not tag.startswith("source_"):
            tag = f"source_{tag}"
        if (
            tag
            and tag not in STOPWORDS
            and not _is_model_meta_term(tag)
            and not re.fullmatch(r"tag\d+", tag)
            and not (filter_generated_noise and _is_generated_tag_noise(tag))
        ):
            tags.append(tag)
    return _dedupe_terms(tags)[:limit]


def _expand_tags_from_terms(terms, expansions):
    joined = " ".join(str(term).lower() for term in terms)
    tags = []
    for triggers, expanded_tags in expansions:
        if any(trigger in joined for trigger in triggers):
            tags.extend(expanded_tags)
    return tags


def _tag_profile_background_preset_tags(terms):
    return _expand_tags_from_terms(terms, TAG_PROFILE_BACKGROUND_PRESETS)


def _normalize_split_tag(tag):
    raw = str(tag).strip()
    normalized = _prompt_token(raw)
    if raw.lower().startswith("source_") and normalized and not normalized.startswith("source_"):
        normalized = f"source_{normalized}"
    return normalized


def _is_protected_split_tag(tag):
    tag = str(tag).strip().lower()
    return tag.startswith(("score_", "rating_", "source_", "style_cluster_"))


def _split_tag_display(tag):
    tag = str(tag).strip()
    if _is_protected_split_tag(tag):
        return tag
    return tag.replace("_", " ")


def _split_tag_key(tag):
    display = _split_tag_display(tag).lower()
    return re.sub(r"[^a-z0-9]+", " ", display).strip()


TAG_PROFILE_BACKGROUND_FILLER_KEYS = {
    _split_tag_key(tag)
    for tag in BACKGROUND_TAG_FILLERS
}

TAG_PROFILE_BACKGROUND_FILLER_WORDS = {
    word
    for key in TAG_PROFILE_BACKGROUND_FILLER_KEYS
    for word in key.split()
}


def _dedupe_split_tags(tags):
    result = []
    seen = set()
    for tag in tags:
        normalized = _normalize_split_tag(tag)
        if not normalized:
            continue
        key = _split_tag_key(normalized)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result


def _drop_redundant_split_words(tags):
    tags = list(tags)
    compound_words = set()
    for tag in tags:
        if _is_protected_split_tag(tag) or "_" not in str(tag):
            continue
        parts = [part for part in str(tag).lower().split("_") if part]
        if len(parts) >= 2:
            compound_words.update(parts)

    result = []
    for tag in tags:
        if _is_protected_split_tag(tag):
            result.append(tag)
            continue
        key = _split_tag_key(tag)
        if " " not in key and key in compound_words:
            continue
        result.append(tag)
    return result


def _split_tags_text(tags):
    return " ".join(_split_tag_display(tag) for tag in tags).replace(",", " ").strip()


def _split_base_concepts(base_tags):
    concepts = set()
    for tag in base_tags:
        normalized = _normalize_split_tag(tag)
        key = _split_tag_key(normalized)
        if key:
            concepts.add(key)
        if normalized.startswith("source_"):
            concepts.add(_split_tag_key(normalized.removeprefix("source_")))
        if normalized.startswith("rating_"):
            concepts.add(_split_tag_key(normalized.removeprefix("rating_")))
    return concepts


def _remove_base_concept_tags(tags, base_concepts):
    result = []
    for tag in tags:
        normalized = _normalize_split_tag(tag)
        if not normalized:
            continue
        if _split_tag_key(normalized) in base_concepts:
            continue
        result.append(tag)
    return result


def _fit_tag_words(tags, min_words, max_words, fillers):
    result = _drop_redundant_split_words(_dedupe_split_tags(tags))
    filler_index = 0
    while _word_count(_split_tags_text(result)) < min_words and filler_index < len(fillers):
        result.append(fillers[filler_index])
        result = _drop_redundant_split_words(_dedupe_split_tags(result))
        filler_index += 1

    while _word_count(_split_tags_text(result)) > max_words and len(result) > 1:
        result.pop()
    return _split_tags_text(result)


def _meaningful_tag_word_count(tags):
    meaningful = []
    for tag in tags:
        key = _split_tag_key(tag)
        compact = key.replace(" ", "_")
        if not compact or compact in GENERATED_TAG_NOISE or compact in LOW_VALUE_PROMPT_TERMS:
            continue
        meaningful.append(tag)
    return _word_count(_split_tags_text(meaningful))


def _clean_tag_profile_tags(value, limit=32, keep_quality=False, remove_background_noise=False):
    tags = []
    for tag in _tokenize_prompt_tags(value, limit=limit * 4, filter_generated_noise=False):
        tag = _normalize_split_tag(tag).strip("._:-+")
        key = _split_tag_key(tag)
        compact = key.replace(" ", "_")
        if (
            not compact
            or len(compact) <= 1
            or compact in GENERATED_TAG_NOISE
            or compact.startswith("style_cluster_")
            or re.fullmatch(r"v\d+", compact)
            or _is_model_meta_term(compact)
        ):
            continue
        if not keep_quality and _is_low_value_prompt_term(compact):
            continue
        if remove_background_noise:
            if _tag_is_pony_v6_background_noise(tag) or _term_is_pony_v6_style_like(tag):
                continue
            background_noise_parts = {
                "amazing",
                "anime",
                "bad",
                "illustration",
                "illustrations",
                "lines",
                "linework",
                "natural",
                "sharp",
                "text",
            }
            if compact in background_noise_parts or any(part in background_noise_parts for part in compact.split("_")):
                continue
        tags.append(tag)
    return _drop_redundant_split_words(_dedupe_split_tags(tags))[:limit]


def _generic_background_only(tags):
    tags = _dedupe_split_tags(tags)
    if not tags:
        return True
    return all(
        _split_tag_key(tag) in TAG_PROFILE_BACKGROUND_FILLER_KEYS
        or _split_tag_key(tag) in TAG_PROFILE_BACKGROUND_FILLER_WORDS
        for tag in tags
    )


def _drop_background_filler_tags(tags):
    real_tags = [
        tag
        for tag in _dedupe_split_tags(tags)
        if _split_tag_key(tag) not in TAG_PROFILE_BACKGROUND_FILLER_KEYS
        and _split_tag_key(tag) not in TAG_PROFILE_BACKGROUND_FILLER_WORDS
    ]
    return real_tags or tags


def _drop_unrelated_setting_tags(tags, candidate_data):
    candidate_keys = {
        _split_tag_key(tag)
        for tag in candidate_data.get("background_candidates", ())
    }
    if not candidate_keys:
        return tags
    return [
        tag
        for tag in tags
        if _split_tag_key(tag) not in TAG_PROFILE_KNOWN_SETTING_KEYS
        or _split_tag_key(tag) in candidate_keys
    ]


def _minimal_background_tags():
    return list(TAG_PROFILE_MINIMAL_BACKGROUND_TAGS)


def _append_background_tags_until_min(result, source_tags):
    result = _drop_redundant_split_words(_dedupe_split_tags(result))
    for tag in source_tags:
        current_words = _word_count(_split_tags_text(result))
        if current_words >= TAG_PROFILE_BACKGROUND_WORD_RANGE[0]:
            break
        candidate = _drop_redundant_split_words(_dedupe_split_tags([*result, tag]))
        if _word_count(_split_tags_text(candidate)) <= current_words:
            continue
        result = candidate
    return result


def _extend_concrete_background_tags(background_tags, candidate_data):
    result = _drop_background_filler_tags(background_tags)
    result = _drop_unrelated_setting_tags(result, candidate_data)
    if _generic_background_only(result):
        result = []

    candidate_tags = _drop_background_filler_tags(list(candidate_data.get("background_candidates", ())))
    result = _append_background_tags_until_min(result, candidate_tags)
    if _word_count(_split_tags_text(result)) < TAG_PROFILE_BACKGROUND_WORD_RANGE[0]:
        result = _append_background_tags_until_min(result, _minimal_background_tags())

    while _word_count(_split_tags_text(result)) > TAG_PROFILE_BACKGROUND_WORD_RANGE[1] and len(result) > 1:
        result.pop()
    return result


def _light_tag_prompt_parts(target_profile, word_salad, style_anchor, provided=None):
    target_profile = _normalize_target_profile(target_profile)
    provided = provided or {}
    candidate_data = _candidate_data(target_profile, word_salad, style_anchor)

    provided_base_tags = _clean_tag_profile_tags(provided.get("base_prompt", ""), limit=24, keep_quality=True)
    fixed_base_tags = list(candidate_data.get("fixed_base_tags", ()))
    fixed_base_keys = {_split_tag_key(tag) for tag in fixed_base_tags}
    style_candidate_keys = {_split_tag_key(tag) for tag in candidate_data.get("style_candidates", ())}
    base_tags = list(fixed_base_tags)
    for tag in provided_base_tags:
        key = _split_tag_key(tag)
        if (
            _is_protected_split_tag(tag)
            or key in fixed_base_keys
            or key in style_candidate_keys
            or _term_is_pony_v6_style_like(tag)
        ):
            base_tags.append(tag)
    base_tags = _drop_redundant_split_words(_dedupe_split_tags(base_tags))
    if not base_tags:
        base_tags = list(candidate_data.get("fixed_base_tags", ()))
    base_prompt = _split_tags_text(base_tags[:24])

    foreground_tags = _clean_tag_profile_tags(provided.get("foreground_prompt", ""), limit=40)
    foreground_tags = [
        tag
        for tag in foreground_tags
        if not _term_is_background_like(tag) and not _term_is_pony_v6_style_like(tag)
    ]
    if not foreground_tags or _meaningful_tag_word_count(foreground_tags) < 3:
        foreground_tags = list(candidate_data.get("foreground_candidates", ()))[:28]
    if not foreground_tags:
        foreground_tags = ["clear_subject", "readable_pose"]
    foreground_prompt = _split_tags_text(foreground_tags[:40])

    background_tags = _clean_tag_profile_tags(
        provided.get("background_prompt", ""),
        limit=48,
        remove_background_noise=True,
    )
    background_tags = _extend_concrete_background_tags(background_tags, candidate_data)
    background_prompt = _split_tags_text(background_tags)

    return base_prompt, foreground_prompt, background_prompt


ANIMA_PROSE_CONTROL_PATTERN = re.compile(
    r"\b(?:score_\d+(?:_up)?|rating_[a-z0-9_]+|style_cluster_\d+|source_[a-z0-9_]+)\b\s*,?\s*",
    re.IGNORECASE,
)


def _clean_anima_prose(value):
    text = re.sub(
        r"(?im)^\s*(?:base_prompt|foreground_prompt|background_prompt|positive|negative|report|"
        r"subject(?:\s+and\s+action)?|environment(?:\s+and\s+light)?|emotion(?:al\s+tone)?)\s*[:=\-]\s*",
        "",
        str(value),
    )
    text = ANIMA_PROSE_CONTROL_PATTERN.sub("", text)
    text = re.sub(r"\b(?:masterpiece|best[ _]quality)\b\s*,?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"_+", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+([,.;!?])", r"\1", text)
    text = re.sub(r",\s*,+", ", ", text)
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    sentences = []
    seen = set()
    for raw_sentence in raw_sentences:
        sentence = re.sub(r"\s+", " ", raw_sentence).strip(" ,.;:-")
        if not sentence:
            continue
        key = sentence.casefold()
        if key in seen:
            continue
        seen.add(key)
        sentence = sentence[:1].upper() + sentence[1:]
        if sentence[-1] not in ".!?":
            sentence += "."
        sentences.append(sentence)
    return " ".join(sentences)


def _anima_prose_is_usable(value):
    text = _clean_anima_prose(value)
    if _word_count(text) < 12:
        return False
    sentence_count = len([part for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()])
    return sentence_count >= 2 and text.count(",") <= max(10, _word_count(text) // 5)


def _anima_sentences(value):
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", _clean_anima_prose(value)) if part.strip()]


def _fit_anima_prose(value, fallback, min_words, max_words):
    sentences = _anima_sentences(value) if _anima_prose_is_usable(value) else []
    fallback_sentences = _anima_sentences(fallback)
    seen = {sentence.casefold() for sentence in sentences}
    for sentence in fallback_sentences:
        if _word_count(" ".join(sentences)) >= min_words:
            break
        if sentence.casefold() not in seen:
            sentences.append(sentence)
            seen.add(sentence.casefold())

    fitted = []
    for sentence in sentences:
        candidate = " ".join((*fitted, sentence))
        if fitted and _word_count(candidate) > max_words:
            break
        if not fitted and _word_count(sentence) > max_words:
            continue
        fitted.append(sentence)

    if _word_count(" ".join(fitted)) < min_words:
        for sentence in fallback_sentences:
            if sentence.casefold() in {item.casefold() for item in fitted}:
                continue
            candidate = " ".join((*fitted, sentence))
            if _word_count(candidate) > max_words:
                break
            fitted.append(sentence)
            if _word_count(" ".join(fitted)) >= min_words:
                break
    return " ".join(fitted)


ANIMA_EMOTION_PATTERN = re.compile(
    r"\b(?:emotion|emotional|expression|body language|mood|feel|feels|hope|hopeful|fear|fearful|"
    r"joy|joyful|sad|sadness|anger|angry|calm|tension|tense|intimate|mysterious|melancholy|warmth)\b",
    re.IGNORECASE,
)


def _ensure_anima_emotional_ending(value, original_value, fallback, min_words, max_words):
    sentences = _anima_sentences(value)
    original_sentences = _anima_sentences(original_value)
    emotional_original = next(
        (sentence for sentence in reversed(original_sentences[-2:]) if ANIMA_EMOTION_PATTERN.search(sentence)),
        "",
    )
    fallback_sentences = _anima_sentences(fallback)
    ending = [emotional_original] if emotional_original else fallback_sentences[-2:]
    ending_keys = {sentence.casefold() for sentence in ending}
    body = [sentence for sentence in sentences if sentence.casefold() not in ending_keys]

    while body and _word_count(" ".join((*body, *ending))) > max_words:
        body.pop()

    existing = {sentence.casefold() for sentence in (*body, *ending)}
    for sentence in fallback_sentences:
        if _word_count(" ".join((*body, *ending))) >= min_words:
            break
        if sentence.casefold() in existing:
            continue
        candidate = " ".join((*body, sentence, *ending))
        if _word_count(candidate) > max_words:
            continue
        body.append(sentence)
        existing.add(sentence.casefold())
    return " ".join((*body, *ending))


def _anima_subject_phrase(terms):
    cleaned = [_clean_z_image_text(term).lower() for term in terms if _clean_z_image_text(term)]
    return _sentence_from_terms(cleaned[:4], "a clearly defined anime figure")


def _anima_foreground_fallback(foreground_terms, source_terms):
    subject = _anima_subject_phrase(foreground_terms or source_terms)
    objects = _anima_subject_phrase((foreground_terms or source_terms)[4:8])
    return (
        f"The main figure is built around {subject}, with a clear and readable silhouette. "
        "The face has carefully shaped features, attentive eyes, and a focused direction of gaze. "
        "Hair, skin, fur, or other visible surfaces carry distinct color and fine texture. "
        "Clothing and accessories use believable layers, visible seams, firm edges, and material contrast. "
        "The pose shows balanced weight, clear limb placement, and an action that reads immediately. "
        f"Important nearby objects reflect {objects} and connect directly with the figure's hands or movement. "
        "Small highlights, folds, worn marks, loose strands, and contact shadows strengthen the focal details. "
        "The camera keeps the figure dominant while allowing every important object to remain understandable. "
        "The expression is easy to read through the eyes, mouth, shoulders, and direction of movement. "
        "Body language gives the scene a personal motive instead of a neutral display pose."
    )


def _anima_background_fallback(background_terms, source_terms):
    setting = _anima_subject_phrase(background_terms or source_terms)
    return (
        f"Around the figure, details such as {setting} create a setting with recognizable shapes and surfaces. "
        "Nearby props occupy the foreground and middle distance without hiding the main action. "
        "Architecture, terrain, furniture, plants, or machinery establish scale and a believable location. "
        "A visible light source creates clean highlights, readable shadows, and a controlled color palette. "
        "Distant forms become softer and smaller, giving the illustration clear depth and atmosphere. "
        "Air, mist, dust, reflections, or weather connect the figure naturally with the surrounding space. "
        "The final mood joins the figure's expression with the light, color, and stillness of the environment. "
        "The scene should feel emotionally specific, visually coherent, and quietly memorable."
    )


def _anima_prompt_parts(value, word_salad, style_anchor, provided=None):
    provided = provided or {}
    combined_source = " ".join(
        str(part)
        for part in (
            word_salad,
            value,
            provided.get("foreground_prompt", ""),
            provided.get("background_prompt", ""),
        )
        if str(part).strip()
    )
    foreground_terms, background_terms, style_terms, all_terms = _split_pony_v7_terms(
        combined_source,
        style_anchor,
        value,
    )
    source_terms = _curated_terms(combined_source, limit=48, filter_low_value=False)
    safety_tags = _anima_safety_tags(word_salad, style_anchor)

    base_tags = list(ANIMA_QUALITY_TAGS)
    base_tags.extend(safety_tags)
    base_tags.extend(_anima_anchor_style_tags(style_anchor, limit=5))
    base_tags.extend(_tags_from_terms(style_terms[:5], limit=5))
    base_tags.extend(ANIMA_BASE_STYLE_TAGS)
    provided_base = _anima_tag_text(provided.get("base_prompt", ""), limit=8)
    if provided_base:
        base_tags.extend(provided_base.split(", "))
    base_prompt = _anima_tag_text(
        base_tags,
        limit=14,
        fallback="masterpiece, best quality, score_9, score_8_up, score_7_up, anime illustration, clean linework",
    )

    foreground_fallback = _anima_foreground_fallback(foreground_terms, source_terms)
    foreground_prompt = _fit_anima_prose(
        provided.get("foreground_prompt", ""),
        foreground_fallback,
        *ANIMA_FOREGROUND_WORD_RANGE,
    )

    background_fallback = _anima_background_fallback(background_terms, all_terms or source_terms)
    provided_background = provided.get("background_prompt", "")
    background_prompt = _fit_anima_prose(
        provided_background,
        background_fallback,
        *ANIMA_BACKGROUND_WORD_RANGE,
    )
    background_prompt = _ensure_anima_emotional_ending(
        background_prompt,
        provided_background,
        background_fallback,
        *ANIMA_BACKGROUND_WORD_RANGE,
    )

    return base_prompt, foreground_prompt, background_prompt


def _balanced_tag_prompt_parts(target_profile, value, word_salad, style_anchor, provided=None):
    target_profile = _normalize_target_profile(target_profile)
    provided = provided or {}
    if target_profile in ("pony_v6", "illustrious"):
        combined_source = str(word_salad)
    else:
        combined_source = " ".join(
            str(part)
            for part in (
                word_salad,
                value,
                provided.get("foreground_prompt", ""),
                provided.get("background_prompt", ""),
            )
        )
    source_terms = _curated_terms(combined_source, limit=48, filter_low_value=False)
    foreground_terms, background_terms, style_terms, all_terms = _split_pony_v7_terms(combined_source, "", "")
    anchor_tags = _tokenize_prompt_tags(style_anchor, limit=24)
    if target_profile in ("pony_v6", "illustrious"):
        provided_base_tags = []
        provided_foreground_tags = []
        provided_background_tags = []
    else:
        provided_base_tags = _tokenize_prompt_tags(provided.get("base_prompt", ""), limit=24, filter_generated_noise=True)
        provided_foreground_tags = _tokenize_prompt_tags(
            provided.get("foreground_prompt", ""),
            limit=80,
            filter_generated_noise=True,
        )
        provided_background_tags = _tokenize_prompt_tags(
            provided.get("background_prompt", ""),
            limit=80,
            filter_generated_noise=True,
        )

    if target_profile == "pony_v6":
        base_tags = list(PONY_V6_BASE_TAGS)
        base_tags.extend(anchor_tags)
        base_tags.extend(provided_base_tags)
        base_tags.extend(("anime_illustration", "sharp_focus", "clean_linework", "best_quality"))
    else:
        base_tags = list(ILLUSTRIOUS_BASE_TAGS)
        base_tags.extend(anchor_tags)
        base_tags.extend(provided_base_tags)
        base_tags.extend(("amazing_quality", "very_aesthetic", "polished_illustration", "soft_shading", "sharp_linework"))

    base_prompt = _fit_tag_words(
        base_tags,
        SPLIT_BASE_WORD_RANGE[0],
        SPLIT_BASE_WORD_RANGE[1],
        ("anime_artwork", "detailed_style", "polished_rendering", "clean_focus"),
    )
    base_concepts = _split_base_concepts(_tokenize_prompt_tags(base_prompt, limit=40))

    source_tags = _tags_from_terms(source_terms, limit=48)
    if target_profile == "pony_v6":
        foreground_source_tags = _pony_v6_foreground_tags_from_terms(source_terms, limit=42)
        background_source_tags = _pony_v6_background_tags_from_terms(source_terms, limit=30)
    elif target_profile == "illustrious":
        foreground_source_tags = _generic_foreground_tags_from_terms(source_terms, limit=42)
        background_source_tags = _pony_v6_background_tags_from_terms(source_terms, limit=30)
    else:
        foreground_source_tags = source_tags
        background_source_tags = _tags_from_terms(background_terms, limit=36)
    foreground_tags = []
    foreground_tags.extend(provided_foreground_tags)
    foreground_tags.extend(
        _tags_from_terms(foreground_terms, limit=36)
        if target_profile not in ("pony_v6", "illustrious")
        else []
    )
    foreground_tags.extend(foreground_source_tags)
    foreground_tags.extend(_expand_tags_from_terms(source_terms, FOREGROUND_EXPANSIONS))
    foreground_tags.extend(_contextual_pony_v6_tags(source_terms))
    foreground_tags = _remove_base_concept_tags(foreground_tags, base_concepts)
    foreground_prompt = _fit_tag_words(
        foreground_tags,
        SPLIT_DETAIL_WORD_RANGE[0],
        SPLIT_DETAIL_WORD_RANGE[1],
        FOREGROUND_TAG_FILLERS,
    )

    extracted_background = "" if target_profile == "pony_v6" else _extract_pony_v7_background_phrase(value)
    background_tags = []
    background_tags.extend(provided_background_tags)
    background_tags.extend(background_source_tags)
    background_tags.extend(_tokenize_prompt_tags(extracted_background, limit=24, filter_generated_noise=True))
    background_tags.extend(_expand_tags_from_terms(source_terms, BACKGROUND_EXPANSIONS))
    if target_profile in ("pony_v6", "illustrious"):
        background_tags = [tag for tag in background_tags if not _tag_is_pony_v6_background_noise(tag)]
    background_tags = _remove_base_concept_tags(background_tags, base_concepts)
    background_prompt = _fit_tag_words(
        background_tags,
        SPLIT_DETAIL_WORD_RANGE[0],
        SPLIT_DETAIL_WORD_RANGE[1],
        BACKGROUND_TAG_FILLERS,
    )

    return base_prompt, foreground_prompt, background_prompt


def _has_generic_background_prompt(value):
    lowered = str(value).lower()
    return any(
        marker in lowered
        for marker in (
            "coherent environment with visible depth",
            "supporting background elements",
            "background supports the subject",
            "clear spatial layering and does not overpower",
        )
    )


def _illustrious_prompt_parts(value, word_salad, style_anchor, provided=None):
    provided = provided or {}
    anchor = str(style_anchor).strip()
    foreground_terms, background_terms, style_terms, all_terms = _split_pony_v7_terms(word_salad, style_anchor, value)

    base_parts = list(ILLUSTRIOUS_BASE_TAGS)
    provided_base = str(provided.get("base_prompt", "")).strip()
    if provided_base:
        base_parts.extend(part.strip() for part in provided_base.split(",") if part.strip())
    if anchor:
        base_parts.append(anchor)
    base_parts.extend(_tags_from_terms(style_terms[:6], limit=6))
    base_parts.extend(ILLUSTRIOUS_POLISH_TAGS)
    base_prompt = ", ".join(_dedupe_terms(base_parts)[:24])

    foreground_prompt = str(provided.get("foreground_prompt", "")).strip()
    if not foreground_prompt or _word_count(foreground_prompt) < 3:
        foreground_tags = _tags_from_terms(foreground_terms[:18], limit=18)
        if not foreground_tags:
            foreground_tags = _tags_from_terms(all_terms[:14], limit=14)
        foreground_prompt = ", ".join(foreground_tags or ["detailed_subject", "clear_pose", "focused_character"])

    background_prompt = str(provided.get("background_prompt", "")).strip()
    if not background_prompt or _word_count(background_prompt) < 3 or _has_generic_background_prompt(background_prompt):
        background_tags = _tags_from_terms(background_terms[:14], limit=14)
        if not background_tags:
            extracted = _extract_pony_v7_background_phrase(value)
            background_tags = _tags_from_terms(re.split(r"[\s,;|]+", extracted), limit=12)
        background_prompt = ", ".join(background_tags or ["detailed_background", "atmospheric_background", "interior_details"])

    return base_prompt, foreground_prompt, background_prompt


def _word_count(text):
    return len(re.findall(r"\b\w+\b", str(text)))


def _sentence_from_terms(terms, fallback):
    terms = [term for term in terms if term]
    if not terms:
        return fallback
    if len(terms) == 1:
        return terms[0]
    if len(terms) == 2:
        return f"{terms[0]} and {terms[1]}"
    return f"{', '.join(terms[:-1])}, and {terms[-1]}"


def _clean_unstructured_sentence(value):
    value = re.sub(r"[ \t]+", " ", str(value).strip())
    if not value:
        return ""

    value = _strip_pony_v7_control_terms(value)
    foreground_match = re.search(r"1\.\s*foreground:\s*(.+?)(?:\s*2\.\s*background:|\s*#\s*stylistic description:|$)", value, re.IGNORECASE)
    if foreground_match:
        first_line = foreground_match.group(1).strip()
    else:
        lines = [
            line.strip()
            for line in str(value).splitlines()
            if line.strip()
            and not line.strip().lower().startswith(("score_", "#", "2. background", "# factual", "# stylistic", "# danbooru"))
            and not _looks_like_tag_list(line.strip())
            and not _looks_like_pony_v7_base_meta(line.strip())
            and not _looks_like_pony_v7_background_paragraph(line.strip())
            and not _looks_like_pony_v7_style_paragraph(line.strip())
        ]
        first_line = lines[0] if lines else ""
    first_line = re.sub(r"^#+\s*[^:]+:\s*", "", first_line)
    first_line = re.sub(r"\s+", " ", first_line)
    first_line = _strip_leading_pony_v7_tag_preamble(first_line)
    first_line = _strip_pony_v7_field_label(first_line)
    first_sentence = re.split(r"(?<=[.!?])\s+", first_line)[0].strip()
    first_sentence = first_sentence.strip(" .")
    if not first_sentence:
        return ""
    first_sentence = first_sentence[:1].upper() + first_sentence[1:]
    return f"{first_sentence}."


def _strip_pony_v7_control_terms(value):
    value = re.sub(
        r"\b(?:score_\d+(?:_up)?|rating_[a-z0-9_]+|style_cluster_\d+)\b\s*,?\s*",
        "",
        str(value),
        flags=re.IGNORECASE,
    )
    value = re.sub(r"[ \t]+([,.])", r"\1", value)
    value = re.sub(r"(?:^|\n)\s*,+\s*", "\n", value)
    value = re.sub(r",\s*,+", ", ", value)
    return value.strip(" ,")


PONY_V7_FIELD_LABEL_PATTERN = re.compile(
    r"^\s*(?:"
    r"global\s+(?:model/)?source/style\s+tags?"
    r"|global\s+model\s+source\s+style\s+tags?"
    r"|base\s+prompt"
    r"|foreground\s+prompt"
    r"|foreground\s+description"
    r"|background\s+prompt"
    r"|background\s+description"
    r"|style\s+tags?"
    r"|danbooru\s+tags?"
    r")\s*[:\-–—,]*\s*",
    re.IGNORECASE,
)


def _strip_pony_v7_field_label(value):
    previous = str(value).strip()
    while True:
        current = PONY_V7_FIELD_LABEL_PATTERN.sub("", previous).strip()
        if current == previous:
            return current
        previous = current


def _looks_like_pony_v7_base_meta(value):
    lowered = str(value).strip().lower()
    return bool(PONY_V7_FIELD_LABEL_PATTERN.match(lowered)) or any(
        marker in lowered
        for marker in (
            "global model/source/style tags",
            "global model source style tags",
            "source/style tags",
            "model/source/style",
        )
    )


def _looks_like_pony_v7_background_paragraph(value):
    lowered = str(value).strip().lower()
    return lowered.startswith("behind the subject") or "background" in lowered


def _looks_like_pony_v7_style_paragraph(value):
    lowered = str(value).strip().lower()
    return any(
        marker in lowered
        for marker in (
            "digital anime illustration",
            "clean linework",
            "soft shading",
            "camera framing",
            "focused color palette",
            "medium shot",
            "balanced composition",
            "low angle perspective",
        )
    )


def _looks_like_pony_v7_prefix_tag(value):
    normalized = re.sub(r"[_-]+", " ", str(value).strip().lower())
    normalized = re.sub(r"\s+", " ", normalized).strip(" .")
    if not normalized:
        return True
    if normalized in {
        "masterpiece",
        "best quality",
        "high quality",
        "source anthro",
        "source furry",
        "source anime",
        "source cartoon",
        "anthro",
        "furry",
        "explicit",
        "solo",
    }:
        return True
    sentence_markers = {
        "a",
        "an",
        "the",
        "this",
        "that",
        "wearing",
        "holding",
        "standing",
        "sitting",
        "lying",
        "walking",
        "running",
        "with",
        "in",
        "on",
        "near",
        "behind",
    }
    words = normalized.split()
    return len(words) <= 3 and not any(word in sentence_markers for word in words)


def _strip_leading_pony_v7_tag_preamble(value):
    parts = [part.strip() for part in str(value).split(",")]
    while len(parts) > 1 and _looks_like_pony_v7_prefix_tag(parts[0]):
        parts.pop(0)
    return ", ".join(part for part in parts if part).strip()


PONY_V7_BACKGROUND_KEYWORDS = (
    "airport",
    "apartment",
    "background",
    "barren",
    "beach",
    "bookshelf",
    "bookshelves",
    "building",
    "bush",
    "bushes",
    "castle",
    "church",
    "city",
    "coast",
    "desert",
    "decor",
    "desk",
    "dock",
    "forest",
    "floor",
    "gambia",
    "garden",
    "harbor",
    "harbour",
    "interior",
    "lamp",
    "landscape",
    "microphone",
    "mountain",
    "ocean",
    "pier",
    "plushie",
    "plushies",
    "port",
    "poster",
    "posters",
    "room",
    "rug",
    "ruined",
    "sail",
    "sea",
    "ship",
    "shore",
    "shrine",
    "sky",
    "sofa",
    "street",
    "table",
    "temple",
    "tree",
    "trees",
    "valley",
    "wall",
    "water",
    "window",
    "windows",
    "woods",
    "mushroom",
    "mushrooms",
    "crystal",
    "crystals",
)

TAG_PROFILE_EXTRA_BACKGROUND_KEYWORDS = (
    "bathroom",
    "bedroom",
    "brick",
    "carpet",
    "chair",
    "deutsch",
    "deutsche",
    "door",
    "doorway",
    "evening",
    "german",
    "germany",
    "kitchen",
    "light",
    "lights",
    "living",
    "shelf",
    "shelves",
    "walls",
)

TAG_PROFILE_BACKGROUND_KEYWORDS = PONY_V7_BACKGROUND_KEYWORDS + TAG_PROFILE_EXTRA_BACKGROUND_KEYWORDS

PONY_V6_FOREGROUND_BLOCKLIST_FOR_BACKGROUND = {
    "anthro",
    "body",
    "character",
    "cool",
    "corset",
    "cybernetic",
    "drift",
    "dynamic",
    "enjoying",
    "explicit",
    "feature",
    "fine",
    "furry",
    "hand",
    "latex",
    "lend",
    "nsfw",
    "sexy",
    "subject",
    "velociraptor",
}

PONY_V6_STYLE_KEYWORDS = (
    "composition",
    "watercolor",
    "cinematic",
    "dynamic composition",
    "lighting",
    "perspective",
    "shot",
    "view",
)


def _clean_pony_v7_background_phrase(value):
    phrase = _strip_pony_v7_control_terms(value)
    phrase = re.sub(r"^\s*behind\s+(?:the\s+)?subject,?\s*(?:the\s+)?scene\s+includes\s+", "", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"^\s*(?:the\s+)?scene\s+includes\s+", "", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\b(?:in|on|at|against|inside|within|under|beneath|behind)\s+the\s+background\b", "", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bthe\s+background\b", "", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\s+", " ", phrase).strip(" ,.;")
    phrase = _strip_leading_pony_v7_tag_preamble(phrase)
    if not phrase or _word_count(phrase) < 2:
        return ""
    return phrase


def _extract_pony_v7_background_phrase(value):
    cleaned = _strip_pony_v7_control_terms(value)
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    for sentence in sentences:
        if re.search(r"\b(?:these setting details|background should contain|background supports|spatial layering)\b", sentence, re.IGNORECASE):
            continue
        if not re.search(r"\b(?:background|behind|harbou?r|dock|pier|port|ship|sail|sea|ocean|street|room|forest|city|sky)\b", sentence, re.IGNORECASE):
            continue
        patterns = (
            r"\b(?:in|inside|within|at|on|against|under|beneath)\s+((?:a|an|the)\s+[^.!?]{5,160})",
            r"\bbehind\s+(?:the\s+subject,?\s*)?((?:a|an|the)?\s*[^.!?]{5,160})",
            r"\bwith\s+([^.!?]{5,120}\bbackground\b[^.!?]{0,60})",
        )
        for pattern in patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                phrase = _clean_pony_v7_background_phrase(match.group(1))
                if phrase:
                    return phrase
        phrase = _clean_pony_v7_background_phrase(sentence)
        if phrase and _word_count(phrase) <= 24:
            return phrase
    return ""


def _pony_v7_background_description(value, background_terms):
    extracted = _extract_pony_v7_background_phrase(value)
    if extracted:
        return extracted
    return _sentence_from_terms(
        background_terms[:7],
        "a specific visible setting with identifiable structures, surfaces, light sources, and distant context",
    )


PONY_V7_FOREGROUND_META_TERMS = {
    "anthro",
    "furry",
    "explicit",
    "rating_explicit",
    "source_anthro",
    "source_furry",
    "source_anime",
    "source_cartoon",
    "masterpiece",
    "best_quality",
    "amazing_quality",
    "very_aesthetic",
}


def _pony_v7_foreground_terms(terms):
    result = []
    for term in terms:
        token = _prompt_token(term)
        if token in PONY_V7_FOREGROUND_META_TERMS:
            continue
        result.append(term)
    return result


def _term_matches_keyword(term, keyword):
    normalized = re.sub(r"[_-]+", " ", str(term).lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    keyword = str(keyword).lower().strip()
    if " " in keyword:
        return keyword in normalized
    return keyword in normalized.split()


def _split_pony_v7_terms(word_salad, style_anchor, existing_prompt):
    source_terms = _curated_terms(f"{style_anchor} {word_salad} {existing_prompt}", limit=36)
    style_keywords = (
        "angle",
        "bokeh",
        "cinematic",
        "close up",
        "composition",
        "depth",
        "illustration",
        "lighting",
        "medium shot",
        "perspective",
        "shading",
        "soft",
        "volumetric",
    )

    foreground = []
    background = []
    style = []
    for term in source_terms:
        normalized = term.lower()
        if any(_term_matches_keyword(normalized, keyword) for keyword in style_keywords):
            style.append(term)
        elif any(_term_matches_keyword(normalized, keyword) for keyword in PONY_V7_BACKGROUND_KEYWORDS):
            background.append(term)
        else:
            foreground.append(term)

    return foreground[:12], background[:8], style[:6], source_terms


Z_IMAGE_FORBIDDEN_TAG_PATTERN = re.compile(
    r"\b(?:"
    r"score_\d+(?:_up)?|rating_[a-z0-9_]+|style_cluster_\d+|source[_ ][a-z0-9_]+|"
    r"masterpiece|best|quality|best[_ ]quality|amazing|amazing[_ ]quality|very[_ ]aesthetic|aesthetic|"
    r"worst[_ ]quality|low[_ ]quality|danbooru|8k|tag\d+"
    r")\b,?\s*",
    re.IGNORECASE,
)


def _strip_z_image_labels(value):
    value = re.sub(
        r"(?im)^\s*(?:base_prompt|foreground_prompt|background_prompt|positive|negative|report|"
        r"main subject|environment|lighting|camera|style|color mood|additional details)\s*[:\-–—]\s*",
        "",
        str(value),
    )
    return value


def _clean_z_image_text(value):
    text = _strip_z_image_labels(value)
    text = Z_IMAGE_FORBIDDEN_TAG_PATTERN.sub("", text)
    text = re.sub(r"[_]+", " ", text)
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r",\s*,+", ", ", text)
    text = re.sub(r"\s+", " ", text).strip(" ,.;")
    if not text:
        return ""
    return text[:1].upper() + text[1:]


def _z_image_terms(word_salad, style_anchor, value, limit=18):
    source = f"{style_anchor} {word_salad}"
    terms = _curated_terms(source, limit=limit, filter_low_value=False)
    if len(terms) < 4:
        terms = _curated_terms(f"{source} {value}", limit=limit, filter_low_value=False)
    result = []
    seen = set()
    for term in terms:
        clean = _clean_z_image_text(term)
        key = clean.lower()
        if not clean or key in seen or Z_IMAGE_FORBIDDEN_TAG_PATTERN.fullmatch(key):
            continue
        seen.add(key)
        result.append(clean)
    return result


def _z_image_section_is_usable(value, min_words=18):
    text = _clean_z_image_text(value)
    if _word_count(text) < min_words:
        return False
    comma_count = text.count(",")
    sentence_count = len([part for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()])
    return sentence_count >= 1 and comma_count <= max(8, _word_count(text) // 8)


def _z_image_foreground_fallback(word_salad, style_anchor, value):
    terms = _z_image_terms(word_salad, style_anchor, value, limit=12)
    subject = _sentence_from_terms(terms[:8], "a clearly defined subject based on the provided idea")
    return (
        f"The image centers on {subject}. The subject appears as a real visual presence with a readable pose, "
        "clear body language, visible clothing or surface texture, and small details that make the concept feel "
        "intentional. The action is easy to understand at a glance, with natural proportions, believable materials, "
        "and a few distinctive features that guide the viewer's attention. The angle of the head or object, the "
        "placement of the hands or edges, the weight of the body, and the condition of fabric, metal, skin, fur, "
        "glass, dust, water, or other visible surfaces are clear in the foreground. Small cues such as tension in "
        "the posture, direction of the gaze, contact with nearby props, reflected highlights, worn edges, scratches, "
        "damp areas, loose strands, or other local details make the main figure or object feel present inside the scene."
    )


def _z_image_background_fallback(word_salad, style_anchor, value):
    _, background_terms, _, all_terms = _split_pony_v7_terms(word_salad, style_anchor, "")
    background = _sentence_from_terms(
        _z_image_terms(" ".join(background_terms), "", "", limit=8) or _z_image_terms(" ".join(all_terms), "", "", limit=6),
        "a concrete environment with visible depth and recognizable surroundings",
    )
    return (
        f"The scene takes place in {background}. The environment supports the subject with a clear foreground, "
        "middle ground, and distant background, using recognizable surfaces, objects, architecture, terrain, or decor. "
        "Light sources and atmosphere are visible inside the scene, so the image feels grounded rather than empty. "
        "The space includes floor or ground texture, wall or horizon shape, nearby props, distant silhouettes, "
        "openings, furniture, signage, vegetation, machinery, weather, smoke, mist, dust, or reflections where they "
        "fit the source idea. The background contains concrete objects at different distances, visible occlusion, "
        "scale changes, and a sense of air "
        "between the subject and the farthest shapes. Mention how the environment affects the mood through color, "
        "temperature, shadow direction, and the kind of light falling across the scene."
    )


def _z_image_base_fallback(word_salad, style_anchor, value):
    terms = _z_image_terms(word_salad, style_anchor, value, limit=10)
    mood = _sentence_from_terms(terms[:4], "the core idea")
    return (
        f"The visual treatment frames {mood} with cinematic composition, atmospheric lighting, realistic shadows, "
        "and a coherent color mood. The camera language suggests an eye-level view, three-quarter composition, "
        "85mm lens, shallow depth of field, or wide-angle framing when it fits the scene. The style reads as a "
        "coherent visual direction, such as photographic realism, painterly fantasy illustration, polished "
        "anime-inspired rendering, or editorial concept art. Contrast, color palette, texture handling, and the "
        "relationship between sharp focal areas and softer peripheral details are visible in the final image."
    )


def _extend_z_image_section(section, fallback, min_words):
    section = _clean_z_image_text(section)
    fallback = _clean_z_image_text(fallback)
    if not section:
        return fallback
    if _word_count(section) >= min_words:
        return section
    if fallback and fallback.lower() not in section.lower():
        section = f"{section}. {fallback}".strip(" .") + "."
    return _clean_z_image_text(section)


def _z_image_prompt_parts(value, word_salad, style_anchor, provided=None):
    provided = provided or {}
    combined = _join_positive_parts(
        "z_image",
        provided.get("base_prompt", ""),
        provided.get("foreground_prompt", ""),
        provided.get("background_prompt", ""),
    ) or str(value)

    foreground = _clean_z_image_text(provided.get("foreground_prompt", ""))
    foreground_fallback = _z_image_foreground_fallback(word_salad, style_anchor, "")
    if not _z_image_section_is_usable(foreground):
        foreground = foreground_fallback
    foreground = _extend_z_image_section(foreground, foreground_fallback, Z_IMAGE_FOREGROUND_MIN_WORDS)

    background = _clean_z_image_text(provided.get("background_prompt", ""))
    background_fallback = _z_image_background_fallback(word_salad, style_anchor, "")
    if not _z_image_section_is_usable(background):
        background = background_fallback
    background = _extend_z_image_section(background, background_fallback, Z_IMAGE_BACKGROUND_MIN_WORDS)

    base = _clean_z_image_text(provided.get("base_prompt", ""))
    base_fallback = _z_image_base_fallback(word_salad, style_anchor, "")
    if not _z_image_section_is_usable(base, min_words=15):
        base = base_fallback
    base = _extend_z_image_section(base, base_fallback, Z_IMAGE_BASE_MIN_WORDS)

    return base, foreground, background


def _danbooru_tags_from_terms(terms):
    tags = []
    seen = set()
    for term in terms:
        tag = re.sub(r"[^a-z0-9_ ]+", "", term.lower().replace("-", " ")).strip().replace(" ", "_")
        if not tag or tag in seen or tag in STOPWORDS:
            continue
        seen.add(tag)
        tags.append(tag)
        if len(tags) >= 15:
            break

    defaults = ("solo", "character", "detailed_background", "looking_at_viewer", "standing")
    for tag in defaults:
        if len(tags) >= 7:
            break
        if tag not in seen:
            tags.append(tag)
            seen.add(tag)
    return tags[:15]


def _needs_pony_v7_structure(prompt):
    prompt = str(prompt)
    lowered = prompt.lower()
    has_bad_numbered_tags = bool(re.search(r"\btag\s*\d+\s*:", lowered))
    has_repeated_control_tags = (
        len(re.findall(r"\brating_[a-z0-9_]+\b", lowered)) > 1
        or len(re.findall(r"\bstyle_cluster_\d+\b", lowered)) > 1
        or len(re.findall(r"\bscore_9\b", lowered)) > 1
    )
    has_visible_section_labels = any(
        marker in lowered
        for marker in (
            "# factual description",
            "# stylistic description",
            "# danbooru tags",
            "1. foreground:",
            "2. background:",
        )
    )
    has_generic_background = any(
        marker in lowered
        for marker in (
            "coherent environment with visible depth",
            "supporting background elements",
            "background supports the subject",
            "clear spatial layering and does not overpower",
        )
    )
    has_special_tags = "score_9" in lowered and "rating_" in lowered and "style_cluster_" in lowered
    return (
        _word_count(prompt) < 220
        or not has_special_tags
        or has_repeated_control_tags
        or has_bad_numbered_tags
        or has_visible_section_labels
        or has_generic_background
    )


def _join_positive_parts(target_profile, base_prompt, foreground_prompt, background_prompt):
    profile = _normalize_target_profile(target_profile)
    if profile == "z_image":
        parts = [foreground_prompt, background_prompt, base_prompt]
        return "\n\n".join(str(part).strip() for part in parts if str(part).strip())
    if profile == "anima":
        parts = [str(part).strip().strip(",") for part in (base_prompt, foreground_prompt, background_prompt) if str(part).strip()]
        return "\n\n".join(parts)
    if profile == "wan2_2_video":
        parts = [str(part).strip() for part in (foreground_prompt, background_prompt, base_prompt) if str(part).strip()]
        return "\n\n".join(parts)
    if profile == "pony_v7":
        base_sections = [part.strip() for part in re.split(r"\n\s*\n+", str(base_prompt).strip()) if part.strip()]
        header = ""
        base_remainder = []
        for index, section in enumerate(base_sections):
            if index == 0 and section.lower().startswith("score_"):
                header = section
            else:
                base_remainder.append(section)
        parts = [header, foreground_prompt, background_prompt, *base_remainder]
        return "\n\n".join(str(part).strip() for part in parts if str(part).strip())
    parts = [str(part).strip() for part in (base_prompt, foreground_prompt, background_prompt) if str(part).strip()]
    return " ".join(parts)


def _looks_like_tag_list(value):
    text = str(value).strip()
    if not text or "." in text:
        return False
    parts = [part.strip() for part in text.split(",") if part.strip()]
    return len(parts) >= 3


def _split_structured_pony_v7_prompt(value, word_salad, style_anchor, style_cluster=DEFAULT_STYLE_CLUSTER):
    style_cluster = _normalize_style_cluster(style_cluster)
    normalized = re.sub(r"style_cluster_\d+", f"style_cluster_{style_cluster}", str(value).strip())
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", normalized) if part.strip()]

    header = f"score_9, rating_explicit, style_cluster_{style_cluster}"
    base_parts = []
    foreground_parts = []
    background_parts = []

    for index, paragraph in enumerate(paragraphs):
        lowered = paragraph.lower()
        if index == 0 and lowered.startswith("score_"):
            base_parts.append(paragraph)
        elif _looks_like_pony_v7_background_paragraph(paragraph):
            background_parts.append(paragraph)
        elif _looks_like_pony_v7_base_meta(paragraph) or _looks_like_tag_list(paragraph) or _looks_like_pony_v7_style_paragraph(paragraph):
            base_parts.append(paragraph)
        elif not foreground_parts:
            foreground_parts.append(paragraph)
        else:
            base_parts.append(paragraph)

    if not any(part.lower().startswith("score_") for part in base_parts):
        base_parts.insert(0, header)

    foreground = " ".join(foreground_parts).strip()
    if not foreground:
        foreground = _clean_unstructured_sentence(value)
    if not foreground or _word_count(foreground) < 8:
        foreground_terms, _, _, _ = _split_pony_v7_terms(word_salad, style_anchor, value)
        foreground_terms = _pony_v7_foreground_terms(foreground_terms)
        foreground = (
            "The image shows "
            + _sentence_from_terms(
                foreground_terms[:10],
                "a clearly defined character with readable pose, silhouette, and visible design details",
            )
            + "."
        )

    background = " ".join(background_parts).strip()
    if not background or _word_count(background) < 8:
        _, background_terms, _, _ = _split_pony_v7_terms(word_salad, style_anchor, value)
        background = f"Behind the subject, the scene includes {_pony_v7_background_description(value, background_terms)}."

    _, _, style_terms, all_terms = _split_pony_v7_terms(word_salad, style_anchor, value)
    tags = ", ".join(_danbooru_tags_from_terms(all_terms))
    if tags and not any(_looks_like_tag_list(part) for part in base_parts):
        base_parts.append(tags)
    if len(base_parts) == 1 and _word_count(base_parts[0]) < 8:
        style_text = _sentence_from_terms(style_terms[:4], "digital anime illustration, clean linework, soft shading, atmospheric lighting")
        base_parts.append(style_text)

    return "\n\n".join(part for part in base_parts if part).strip(), foreground, background


def _structured_pony_v7_parts(value, word_salad, style_anchor, style_cluster=DEFAULT_STYLE_CLUSTER):
    if not _needs_pony_v7_structure(value):
        cluster = _normalize_style_cluster(style_cluster)
        normalized = re.sub(r"style_cluster_\d+", f"style_cluster_{cluster}", value)
        return _split_structured_pony_v7_prompt(normalized, word_salad, style_anchor, cluster)

    style_cluster = _normalize_style_cluster(style_cluster)
    foreground_terms, background_terms, style_terms, all_terms = _split_pony_v7_terms(word_salad, style_anchor, value)
    foreground_sentence = ""
    if _word_count(value) >= 12:
        foreground_sentence = _clean_unstructured_sentence(value)
    if not foreground_sentence or _word_count(foreground_sentence) < 8:
        foreground_terms = _pony_v7_foreground_terms(foreground_terms)
        foreground_sentence = (
            "The image shows "
            + _sentence_from_terms(
                foreground_terms[:10],
                "a clearly defined character with readable pose, silhouette, and visible design details",
            )
            + "."
        )
    background = _pony_v7_background_description(value, background_terms)
    style_fallback = "medium shot, balanced composition, and slight low angle perspective"
    style_anchor_text = _sentence_from_terms(style_terms[:4], style_fallback)
    if _word_count(style_anchor_text) < 3:
        style_anchor_text = style_fallback
    tags = ", ".join(_danbooru_tags_from_terms(all_terms))

    base_prompt = (
        f"score_9, rating_explicit, style_cluster_{style_cluster}\n\n"
        f"{style_anchor_text}. Digital anime illustration with clean linework, soft shading, controlled contrast, atmospheric lighting, and a focused color palette. The image uses depth of field and polished rendering to keep the main subject readable. Camera framing, line weight, shadow placement, highlight shape, and color separation should guide attention from the strongest focal point toward secondary details while keeping the scene finished and visually grounded.\n\n"
        f"{tags}"
    )
    foreground_prompt = (
        f"{foreground_sentence} The main subject is placed clearly in the foreground with readable form, controlled pose, and visible focal details. Material texture, expression, outfit details, and nearby props are described with enough specificity for a coherent image. The pose should make the action and body orientation understandable at a glance, with clear contact points, visible silhouette breaks, and readable spacing between limbs, clothing, accessories, and important objects. Surface details should reinforce the source concept through fabric shine, skin or fur texture, hard edges, soft edges, and small visual accents.\n\n"
    ).strip()
    background_prompt = (
        f"Behind the subject, the scene includes {background}. These setting details should be visibly placed behind and around the subject, giving the image clear spatial layering without overpowering the foreground. The background should contain identifiable middle-ground and far-background shapes, such as architecture, terrain, furniture, props, horizon elements, light sources, or atmospheric details from the source terms. It should feel like a real space with depth cues, occlusion, scale changes, and environmental color."
    )
    return base_prompt, foreground_prompt, background_prompt


def _structured_pony_v7_prompt(value, word_salad, style_anchor, style_cluster=DEFAULT_STYLE_CLUSTER):
    return _join_positive_parts(
        "pony_v7",
        *_structured_pony_v7_parts(value, word_salad, style_anchor, style_cluster),
    )


def _profile_positive_fallback(target_profile, word_salad, style_anchor, style_cluster):
    target_profile = _normalize_target_profile(target_profile)
    anchor = str(style_anchor).strip()
    salad_terms = _curated_terms(word_salad)
    core_terms = ", ".join(salad_terms) if salad_terms else "coherent anime subject, clean composition"
    anchor_prefix = f"{anchor}, " if anchor else ""

    if target_profile == "pony_v6":
        return f"score_9, score_8_up, score_7_up, {anchor_prefix}{core_terms}"
    if target_profile == "illustrious":
        return f"masterpiece, best_quality, {anchor_prefix}{core_terms}"
    if target_profile == "anima":
        base_prompt, foreground_prompt, background_prompt = _anima_prompt_parts(
            "",
            word_salad,
            style_anchor,
            None,
        )
        return _join_positive_parts("anima", base_prompt, foreground_prompt, background_prompt)
    if target_profile == "z_image":
        base_prompt, foreground_prompt, background_prompt = _z_image_prompt_parts(
            "",
            word_salad,
            style_anchor,
            None,
        )
        return _join_positive_parts("z_image", base_prompt, foreground_prompt, background_prompt)
    if target_profile == "wan2_2_video":
        subject = core_terms.rstrip(".,")
        foreground = (
            f"{anchor_prefix}{subject}. The subject performs one continuous, physically readable action "
            "with a clear beginning, progression, and settled ending. Motion remains fluid and identity stays consistent."
        )
        background = (
            "The visible environment remains spatially coherent. Clothing, hair, dust, foliage, or nearby props "
            "show restrained secondary motion that follows the main action."
        )
        base = "cinematic video, stable composition, coherent lighting, natural motion, consistent color and texture"
        return _join_positive_parts("wan2_2_video", base, foreground, background)

    phrase = ", ".join(salad_terms[:12]) if salad_terms else "a coherent anime subject with clean visual focus"
    return _structured_pony_v7_prompt(
        f"A polished anime illustration featuring {anchor_prefix}{phrase}, with coherent composition, detailed lighting, and a clear visual focus.",
        word_salad,
        style_anchor,
        style_cluster,
    )


def _local_fallback_result(target_profile, word_salad, style_anchor, style_cluster, error_message):
    target_profile = _normalize_target_profile(target_profile)
    values = {
        "positive": _profile_positive_fallback(target_profile, word_salad, style_anchor, style_cluster),
        "negative": ", ".join(NEGATIVE_BASELINES[target_profile]),
        "report": (
            "Ollama returned invalid JSON, so a local fallback prompt was built from curated input terms. "
            f"Parser detail: {error_message}"
        ),
    }
    return _postprocess_result(values, target_profile, word_salad, style_anchor, style_cluster)


def _target_profile_instructions(target_profile, style_cluster):
    target_profile = _normalize_target_profile(target_profile)
    style_cluster = _normalize_style_cluster(style_cluster)
    if target_profile == "pony_v6":
        return """Target profile: Pony v6.
- base_prompt must be 10 to 20 words and contain Pony v6 score tags plus broad model/style anchors.
- foreground_prompt must be about 36 to 40 words of concrete SDXL/Pony v6 subject, action, material, pose, expression, and focal-detail tags.
- background_prompt must be about 30 to 40 words of concrete visible background tags: places, rooms, furniture, windows, buildings, plants, terrain, distant objects, light sources, props, and decor.
- If the source only names a setting, add fitting visible details. Example: forest can become dark_forest tall_trees mushrooms glowing_crystals mossy_ground roots misty_path.
- Avoid abstract filler chains such as environmental_depth middle_ground visible_setting scene_context background_texture unless concrete visible objects are also present.
- Use space-separated tags without commas in base_prompt, foreground_prompt, and background_prompt.
- Write tag tokens only. Do not write sentences, articles, helper prose, labels, explanations, or grammar filler.
- Include only concrete subject, action, material, setting, prop, composition, and a few useful quality tags.
- Avoid filler words, prose sentences, random process words, generic style spam, and purely abstract background filler."""
    if target_profile == "illustrious":
        return """Target profile: Illustrious.
- base_prompt must be 10 to 20 words and contain compact IllustriousXL quality, style, artist/medium, and global aesthetic tags.
- foreground_prompt must be about 36 to 40 words of concrete subject, action, outfit/material, pose, expression, and focal-detail tags.
- background_prompt must be about 30 to 40 words of concrete visible background tags: places, rooms, furniture, windows, buildings, plants, terrain, distant objects, light sources, props, and decor.
- If the source only names a setting, add fitting visible details. Example: living_room can become sofa window curtains table_lamp carpet shelves city_view.
- Avoid abstract filler chains such as environmental_depth middle_ground visible_setting scene_context background_texture unless concrete visible objects are also present.
- Use space-separated tags without commas in base_prompt, foreground_prompt, and background_prompt.
- Do not copy the word salad literally.
- Avoid process words, useless random objects, generic style spam, and purely abstract background filler."""
    if target_profile == "anima":
        return """Target profile: Anima.
- Anima is an anime, illustration, and artistic image model. It is not a realism profile.
- Write a natural English image description of about 180 to 260 words in total.
- Use short, simple sentences, preferably 8 to 18 words each. Avoid long compound sentences.
- base_prompt must be one compact comma-separated tag line beginning exactly with: masterpiece, best quality, score_9, score_8_up, score_7_up.
- After those required tags, base_prompt may contain only a few useful safety, medium, lighting, style, and composition tags.
- Only include safe, sensitive, nsfw, explicit, or guro when one of those safety/content tags appears in the source text or style anchor. Do not add a default safety tag.
- Use spaces instead of underscores in the base tags, except score tags such as score_9, score_8_up, score_7_up, score_6, score_1.
- foreground_prompt must contain 5 to 7 short sentences and about 110 to 140 words.
- Begin foreground_prompt with the main figure. Continue with appearance, face, hair, clothing, materials, pose, action, expression, and important objects held or touched by the figure.
- background_prompt must contain 4 to 6 short sentences and about 70 to 90 words.
- Begin background_prompt with nearby objects and the visible setting. Continue with architecture or terrain, light sources, color, atmosphere, and depth.
- End background_prompt with the figure's emotional expression, body language, and the emotional effect of the whole scene.
- Write concrete visual prose, not a Danbooru tag list, keyword chain, instruction, or wish list.
- Do not use Pony v7 controls such as rating_explicit, style_cluster_*, source_* tags, or a rating/style_cluster header.
- negative should include Anima-appropriate quality/anatomy/artifact negatives and must not repeat the positive prompt."""
    if target_profile == "z_image":
        return """Target profile: Z-Image.
- Write natural, detailed image-description prose, not SDXL/Danbooru tag lists.
- Write enough complete sentences for a long Z-Image prompt, about 360 to 440 words total after the three positive fields are joined.
- base_prompt describes medium, visual style, camera/framing, lighting approach, color mood, rendering language, lens behavior, focus, contrast, and texture handling in about 80 to 100 words.
- foreground_prompt describes the main subject, action, posture, visible materials, expression, clothing or surface details, focal details, contact points, and physical readability in about 130 to 160 words.
- background_prompt describes the environment, scene context, light sources, atmosphere, architecture/terrain/props, depth cues, distant objects, and spatial layering in about 130 to 160 words.
- positive is built locally from foreground_prompt, background_prompt, then base_prompt and should read like one detailed 400 word Z-Image prompt.
- negative should be an empty string because Z-Image Turbo does not use negative prompts.
- Do not use control tags such as score_9, source_anthro, rating_explicit, style_cluster, masterpiece, best quality, 8k, or tag spam.
- Do not include visible section labels."""
    if target_profile == "wan2_2_video":
        return """Target profile: Wan 2.2 TI2V-5B video.
- Write concise natural English visual prose, not Danbooru tags or an image-quality keyword pile.
- foreground_prompt must identify the subject and describe one continuous temporal action with a clear start, progression, and ending. Include pose, direction, speed, expression, and physically plausible secondary motion when visible.
- background_prompt must describe the concrete environment, spatial layout, atmosphere, and environmental motion. Keep objects and scene geometry temporally consistent.
- base_prompt must describe camera framing and movement, lens or shot scale when useful, lighting, color, medium/style, and temporal behavior. State whether the camera is locked, tracking, panning, tilting, or orbiting; do not combine contradictory camera moves.
- Prefer a single achievable shot. Avoid cuts, montages, scene changes, teleports, and simultaneous unrelated actions.
- Use positive temporal language such as continuous motion, stable identity, coherent trajectory, natural inertia, and a settled end pose only when it fits the requested scene.
- negative must focus on video failures: flicker, temporal jitter, identity drift, abrupt motion, frozen motion, inconsistent limbs, duplicate subjects, deformation, camera shake, text, watermark, and compression artifacts.
- base_prompt + foreground_prompt + background_prompt should normally total 80 to 180 words.
- Do not include field labels in the values."""
    return f"""Target profile: Pony v7.
- base_prompt must start with: score_9, rating_explicit, style_cluster_{style_cluster}
- base_prompt must also contain global model/source/style tags, medium, lighting, camera, and rendering guidance.
- foreground_prompt must be a rich concrete foreground caption: subject, body/clothing/materials, pose, action, expression, props, and focal details.
- background_prompt must be a rich concrete background caption: place, room, architecture, terrain, decor, weather, light sources, distant objects, and depth cues.
- Do not include these labels: "# factual description", "1. Foreground:", "2. Background:", "# stylistic description", "# danbooru tags:".
- background_prompt must name concrete visible setting details from the source words. Do not use generic placeholders like "coherent environment" or "supporting background elements".
- Keep rating_explicit in the first line when explicit content is requested or implied.
- base_prompt + foreground_prompt + background_prompt should be about 220 to 300 words total."""


def _candidate_few_shot_example(target_profile, word_salad, style_anchor):
    target_profile = _normalize_target_profile(target_profile)
    data = _candidate_data(target_profile, word_salad, style_anchor)
    if not data:
        return ""

    fixed_base = data["fixed_base_tags"]
    foreground = data["foreground_candidates"]
    background = data["background_candidates"]
    style = data["style_candidates"]

    if target_profile == "pony_v6":
        base = _candidate_tag_text([*fixed_base[:12], *style[:3], "anime_illustration", "sharp_focus"])
        foreground_prompt = _candidate_tag_text([*foreground[:10], "readable_pose", "visible_silhouette", "material_texture"])
        background_prompt = _candidate_tag_text(background[:24] or _minimal_background_tags())
        return f"""Example field values for Pony v6 using the current candidates only:
base_prompt => {base}
foreground_prompt => {foreground_prompt}
background_prompt => {background_prompt}
negative => low quality worst quality bad anatomy bad hands malformed fingers extra fingers missing fingers text watermark logo blurry
report => Built a Pony v6 split prompt from sorted foreground background and style candidates."""
    if target_profile == "illustrious":
        base = _candidate_tag_text([*fixed_base[:12], *style[:3], "anime_illustration", "soft_shading"])
        foreground_prompt = _candidate_tag_text([*foreground[:10], "readable_pose", "clear_subject", "material_texture"])
        background_prompt = _candidate_tag_text(background[:24] or _minimal_background_tags())
        return f"""Example field values for Illustrious using the current candidates only:
base_prompt => {base}
foreground_prompt => {foreground_prompt}
background_prompt => {background_prompt}
negative => low quality worst quality bad anatomy bad hands malformed fingers poorly drawn face text watermark logo blurry
report => Built an Illustrious split prompt from sorted visual candidates."""
    if target_profile == "anima":
        base, foreground_prompt, background_prompt = _anima_prompt_parts(
            "",
            word_salad,
            style_anchor,
            {"base_prompt": _anima_tag_text([*fixed_base[:12], *style[:3], "anime_illustration", "digital_art"])},
        )
        return f"""Example field values for Anima using the current candidates only:
base_prompt => {base}
foreground_prompt => {foreground_prompt}
background_prompt => {background_prompt}
negative => worst quality, low quality, score_1, score_2, score_3, artist name, bad anatomy, bad hands, text, watermark, blurry
report => Built a natural Anima prompt from sorted visual candidates."""
    return ""


def _build_generation_prompt(target_profile, word_salad, style_anchor, style_cluster):
    target_profile = _normalize_target_profile(target_profile)
    anchor = str(style_anchor).strip()
    anchor_block = anchor if anchor else "(none)"
    candidate_context = _build_candidate_context(target_profile, word_salad, style_anchor)
    example = _candidate_few_shot_example(target_profile, word_salad, style_anchor)
    candidate_block = f"\n{candidate_context}\n" if candidate_context else ""
    example_block = f"\n{example}\n" if example else ""
    return f"""Rewrite this random word salad into one model-specific image prompt set.

{_target_profile_instructions(target_profile, style_cluster)}
{example_block}{candidate_block}

Random word salad:
{str(word_salad).strip()}

Style anchor / fixed requirements:
{anchor_block}

Important:
- Fill every JSON field with a useful non-empty string, except Z-Image negative which should be empty.
- Negative fields must describe things to avoid, not repeat the positive prompt. For Z-Image only, negative must be an empty string.
- Do not treat Pony v6 or Pony v7 as animal subjects.
- For Anima, keep the required quality tags on the first line, then use 180 to 260 words of short natural sentences in subject-to-emotion order.
- For Anima, do not use Pony v7/SDXL/Z-Image control language such as style_cluster_*, rating_explicit, or source_* tags.
- Start your response with {{ and end it with }}.
- Use exactly the requested JSON keys, with no markdown and no commentary.
- Required JSON keys: {", ".join(RESPONSE_KEYS)}.

Return valid JSON only."""


def _build_repair_prompt(raw_response):
    return f"""Repair the following invalid answer into valid JSON only.
It must contain exactly these string keys:
{", ".join(RESPONSE_KEYS)}
Every value except negative must be a non-empty string.
Negative fields must be real negative prompts unless the target instructions say the model uses no negative prompt.

Invalid answer:
{raw_response}"""


def _build_minimal_retry_prompt(target_profile, word_salad, style_anchor, style_cluster):
    terms = ", ".join(_curated_terms(f"{style_anchor} {word_salad}", limit=18))
    if not terms:
        terms = "anime subject, clean composition, detailed lighting"
    target_profile = _normalize_target_profile(target_profile)
    candidate_context = _build_candidate_context(target_profile, word_salad, style_anchor)
    example = _candidate_few_shot_example(target_profile, word_salad, style_anchor)
    candidate_block = f"\n{candidate_context}" if candidate_context else ""
    example_block = f"\n{example}" if example else ""
    return f"""Return one JSON object only. No markdown. No prose.
Use exactly these keys: {", ".join(RESPONSE_KEYS)}
{_target_profile_instructions(target_profile, style_cluster)}
{example_block}{candidate_block}
Source visual terms: {terms}
Rules: base_prompt contains global model/style or natural style guidance; foreground_prompt describes the main subject; background_prompt describes the visible setting; negative lists quality/anatomy/artifact problems to avoid unless the target profile says it is unused; report is one short sentence."""


class NukunOllamaPromptRefiner:
    @classmethod
    def INPUT_TYPES(cls):
        available_models = _available_ollama_models()
        default_model = DEFAULT_OLLAMA_MODEL if DEFAULT_OLLAMA_MODEL in available_models else available_models[0]
        return {
            "required": {
                "word_salad": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "dynamicPrompts": True,
                        "defaultInput": True,
                        "tooltip": "Random vocabulary text to curate into model-specific prompts.",
                    },
                ),
                "ollama_url": (
                    "STRING",
                    {
                        "default": DEFAULT_OLLAMA_URL,
                        "multiline": False,
                        "tooltip": "Base Ollama URL, usually http://127.0.0.1:11434.",
                    },
                ),
                "ollama_model": (
                    available_models,
                    {
                        "default": default_model,
                        "tooltip": "Local Ollama model used to rewrite the prompt. The dropdown refreshes from the selected Ollama URL in the browser.",
                    },
                ),
                "target_profile": (
                    TARGET_PROFILES,
                    {
                        "default": DEFAULT_TARGET_PROFILE,
                        "tooltip": "Prompt profile to generate. Ollama only writes this one split prompt set per run.",
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xffffffffffffffff,
                        "control_after_generate": True,
                        "tooltip": "Seed passed to Ollama for repeatable prompt rewriting.",
                    },
                ),
                "temperature": (
                    "FLOAT",
                    {
                        "default": 0.45,
                        "min": 0.0,
                        "max": 2.0,
                        "step": 0.01,
                        "tooltip": "Ollama generation temperature. Lower is more deterministic.",
                    },
                ),
                "top_p": (
                    "FLOAT",
                    {
                        "default": 0.9,
                        "min": 0.01,
                        "max": 1.0,
                        "step": 0.01,
                        "tooltip": "Ollama nucleus sampling value.",
                    },
                ),
                "style_cluster": (
                    "INT",
                    {
                        "default": DEFAULT_STYLE_CLUSTER,
                        "min": 0,
                        "max": 2048,
                        "tooltip": "Pony v7 style_cluster number used in the structured prompt header.",
                    },
                ),
                "timeout_seconds": (
                    "INT",
                    {
                        "default": 120,
                        "min": 1,
                        "max": 600,
                        "tooltip": "Maximum time to wait for each Ollama request.",
                    },
                ),
                "context_length": (
                    OLLAMA_CONTEXT_LENGTH_CHOICES,
                    {
                        "default": str(DEFAULT_OLLAMA_CONTEXT_LENGTH),
                        "tooltip": "Ollama num_ctx context window. Higher values need more VRAM/RAM and may be limited by the selected model.",
                    },
                ),
            },
            "optional": {
                "style_anchor": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "dynamicPrompts": True,
                        "defaultInput": True,
                        "tooltip": "Optional fixed motifs, character names, LoRA tags, or quality tags to preserve.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = OUTPUT_KEYS
    FUNCTION = "refine"
    CATEGORY = "Nukun/Text"
    DESCRIPTION = "Uses a local Ollama model to turn source text into a selected image- or Wan 2.2 video-specific split prompt set."

    def refine(
        self,
        word_salad,
        ollama_url,
        ollama_model,
        target_profile,
        seed,
        temperature,
        top_p,
        style_cluster,
        timeout_seconds,
        context_length=DEFAULT_OLLAMA_CONTEXT_LENGTH,
        style_anchor="",
    ):
        if not str(word_salad).strip() and not str(style_anchor).strip():
            raise RuntimeError("Ollama Prompt Refiner: word_salad or style_anchor must contain text")

        raw_response = _request_ollama(
            ollama_url,
            ollama_model,
            _build_generation_prompt(target_profile, word_salad, style_anchor, style_cluster),
            seed,
            temperature,
            top_p,
            timeout_seconds,
            context_length,
        )

        try:
            values = _validate_result(_extract_json_object(raw_response))
            return _postprocess_result(values, target_profile, word_salad, style_anchor, style_cluster)
        except ValueError as first_error:
            repair_response = _request_ollama(
                ollama_url,
                ollama_model,
                _build_repair_prompt(raw_response),
                int(seed) + 1,
                0.0,
                1.0,
                timeout_seconds,
                context_length,
            )
            try:
                values = _validate_result(_extract_json_object(repair_response))
                return _postprocess_result(values, target_profile, word_salad, style_anchor, style_cluster)
            except ValueError as second_error:
                minimal_response = _request_ollama(
                    ollama_url,
                    ollama_model,
                    _build_minimal_retry_prompt(target_profile, word_salad, style_anchor, style_cluster),
                    int(seed) + 2,
                    0.0,
                    1.0,
                    timeout_seconds,
                    context_length,
                )
                try:
                    values = _validate_result(_extract_json_object(minimal_response))
                    return _postprocess_result(values, target_profile, word_salad, style_anchor, style_cluster)
                except ValueError as third_error:
                    return _local_fallback_result(
                        target_profile,
                        word_salad,
                        style_anchor,
                        style_cluster,
                        f"initial={first_error}; repair={second_error}; minimal={third_error}",
                    )

    @classmethod
    def IS_CHANGED(
        cls,
        word_salad,
        ollama_url,
        ollama_model,
        target_profile,
        seed,
        temperature,
        top_p,
        style_cluster,
        timeout_seconds,
        context_length=DEFAULT_OLLAMA_CONTEXT_LENGTH,
        style_anchor="",
    ):
        digest = hashlib.sha256()
        for value in (
            word_salad,
            ollama_url,
            ollama_model,
            _normalize_target_profile(target_profile),
            int(seed),
            float(temperature),
            float(top_p),
            _normalize_style_cluster(style_cluster),
            int(timeout_seconds),
            _normalize_context_length(context_length),
            style_anchor,
        ):
            digest.update(str(value).encode("utf-8"))
            digest.update(b"\0")
        return digest.hexdigest()


NODE_CLASS_MAPPINGS = {
    "NukunOllamaPromptRefiner": NukunOllamaPromptRefiner,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NukunOllamaPromptRefiner": "Ollama Prompt Refiner (Nukun)",
}
