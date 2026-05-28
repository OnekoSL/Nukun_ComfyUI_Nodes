from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESOURCES_DIR = ROOT / "resources"
DEFAULT_SOURCE = ROOT.parent.parent / "user" / "little_doom.txt"


OUTPUT_FILES = {
    "clean": "little_doom_clean.csv",
    "characters_sources": "little_doom_characters_sources.csv",
    "hair_eyes": "little_doom_hair_eyes.csv",
    "clothing_accessories": "little_doom_clothing_accessories.csv",
    "body_features": "little_doom_body_features.csv",
    "poses_actions": "little_doom_poses_actions.csv",
    "settings_props": "little_doom_settings_props.csv",
    "symbols_style": "little_doom_symbols_style.csv",
    "mature": "little_doom_mature.csv",
    "dark_gore": "little_doom_dark_gore.csv",
}

BLANK_LINE_RE = re.compile(r"\n\s*\n+")


CHARACTER_SOURCE_TOKENS = {
    "anime",
    "cosplay",
    "creeper",
    "disney",
    "genshin",
    "league",
    "minecraft",
    "nintendo",
    "pokemon",
    "sanrio",
    "sonic",
    "vocaloid",
}

HAIR_EYES_TOKENS = {
    "bangs",
    "beard",
    "blush",
    "braid",
    "braided",
    "braids",
    "cheek",
    "cheeks",
    "crying",
    "ear",
    "ears",
    "eye",
    "eyebrow",
    "eyebrows",
    "eyelashes",
    "eyes",
    "eyewear",
    "face",
    "facial",
    "fangs",
    "glasses",
    "hair",
    "hairband",
    "hairclip",
    "hairpods",
    "hairtie",
    "lipstick",
    "lips",
    "makeup",
    "mouth",
    "nose",
    "ponytail",
    "pupil",
    "pupils",
    "sclera",
    "smile",
    "tears",
    "teeth",
    "tongue",
    "twintails",
    "whiskers",
}

HAIR_EYES_PHRASES = {
    "animal ear",
    "black eye",
    "hair between eyes",
    "open mouth",
    "single eye",
}

CLOTHING_ACCESSORY_TOKENS = {
    "accessory",
    "apron",
    "armor",
    "bag",
    "bandaid",
    "bandage",
    "belt",
    "bikini",
    "bodysuit",
    "boots",
    "bra",
    "cape",
    "choker",
    "clothes",
    "clothing",
    "collar",
    "corset",
    "costume",
    "dress",
    "earrings",
    "eyewear",
    "glasses",
    "gloves",
    "goggles",
    "hat",
    "headband",
    "headphones",
    "heels",
    "helmet",
    "hood",
    "jacket",
    "jewelry",
    "kimono",
    "leotard",
    "lingerie",
    "mask",
    "necklace",
    "outfit",
    "panties",
    "pants",
    "piercing",
    "ribbon",
    "scarf",
    "shirt",
    "shoes",
    "shorts",
    "skirt",
    "sleeve",
    "sleeves",
    "socks",
    "suit",
    "swimsuit",
    "thighhighs",
    "uniform",
    "underwear",
    "veil",
}

CLOTHING_ACCESSORY_PHRASES = {
    "bunny suit",
    "maid outfit",
    "school uniform",
    "swim suit",
}

BODY_FEATURE_TOKENS = {
    "abs",
    "anatomy",
    "anus",
    "arm",
    "arms",
    "ass",
    "back",
    "belly",
    "body",
    "breast",
    "breasts",
    "butt",
    "claws",
    "clitoris",
    "ear",
    "ears",
    "fangs",
    "feet",
    "fingers",
    "foot",
    "genitals",
    "hand",
    "hands",
    "head",
    "heart",
    "hips",
    "horn",
    "horns",
    "leg",
    "legs",
    "mouth",
    "muscle",
    "muscular",
    "nail",
    "nails",
    "navel",
    "neck",
    "nipple",
    "nipples",
    "penis",
    "piercing",
    "pubic",
    "pussy",
    "skin",
    "tail",
    "teeth",
    "thigh",
    "thighs",
    "toe",
    "toes",
    "tongue",
    "torso",
    "vagina",
    "veins",
    "waist",
    "wings",
}

BODY_FEATURE_PHRASES = {
    "animal ears",
    "body hair",
    "large breasts",
    "small breasts",
}

POSE_ACTION_TOKENS = {
    "arched",
    "bent",
    "bound",
    "carrying",
    "clenched",
    "covering",
    "crying",
    "cutting",
    "facing",
    "falling",
    "fingering",
    "grabbing",
    "hanging",
    "holding",
    "kneeling",
    "leaning",
    "licking",
    "looking",
    "lying",
    "open",
    "peeing",
    "pulling",
    "pushing",
    "restrained",
    "running",
    "sitting",
    "smile",
    "spitroast",
    "spreading",
    "standing",
    "strangling",
    "sucking",
    "suspended",
    "tied",
    "touching",
    "walking",
}

POSE_ACTION_PHRASES = {
    "all fours",
    "arms behind",
    "arms up",
    "ass up",
    "bent over",
    "from behind",
    "on back",
    "open mouth",
    "spread legs",
}

SETTING_PROP_TOKENS = {
    "arcade",
    "background",
    "bag",
    "bath",
    "beach",
    "bed",
    "bowl",
    "box",
    "cafe",
    "camera",
    "car",
    "chain",
    "chair",
    "city",
    "cloud",
    "cloudy",
    "coffee",
    "couch",
    "desk",
    "dildo",
    "door",
    "fence",
    "food",
    "forest",
    "gun",
    "hammer",
    "indoor",
    "indoors",
    "joystick",
    "kalashnikov",
    "kitchen",
    "knife",
    "machine",
    "mirror",
    "moon",
    "outdoor",
    "outdoors",
    "pillow",
    "pool",
    "rifle",
    "rope",
    "room",
    "sky",
    "snow",
    "sofa",
    "spaghetti",
    "spotlight",
    "street",
    "sword",
    "table",
    "tool",
    "toy",
    "tree",
    "wall",
    "water",
    "watercraft",
    "weapon",
    "window",
    "wrench",
}

SETTING_PROP_PHRASES = {
    "gas mask",
    "sex toy",
}

SYMBOL_STYLE_TOKENS = {
    "border",
    "censor",
    "censored",
    "comic",
    "effect",
    "emoji",
    "icon",
    "mosaic",
    "perspective",
    "pov",
    "print",
    "sepia",
    "shape",
    "silhouette",
    "style",
    "symbol",
    "transparent",
    "tribal",
    "uncensored",
}

SYMBOL_STYLE_PHRASES = {
    "sound effect",
    "speech bubble",
}

MATURE_TOKENS = {
    "anal",
    "bdsm",
    "bondage",
    "bukkake",
    "clitoris",
    "cum",
    "dildo",
    "ejaculation",
    "erection",
    "fellatio",
    "fingering",
    "fisting",
    "genitals",
    "handjob",
    "hentai",
    "irrumatio",
    "lactation",
    "lingerie",
    "masturbation",
    "naked",
    "nipple",
    "nipples",
    "nude",
    "orgasm",
    "panties",
    "penis",
    "pussy",
    "sex",
    "sexual",
    "spitroast",
    "threesome",
    "underwear",
    "vaginal",
    "yuri",
}

MATURE_PHRASES = {
    "after sex",
    "sex toy",
}

DARK_GORE_TOKENS = {
    "amputated",
    "amputee",
    "asphyxiation",
    "beheading",
    "bisection",
    "blood",
    "bloody",
    "brain",
    "bruise",
    "corpse",
    "cutting",
    "dead",
    "death",
    "decapitation",
    "disembodied",
    "eviscerated",
    "gore",
    "guro",
    "headless",
    "impaled",
    "injury",
    "intestines",
    "mutilated",
    "rape",
    "scars",
    "severed",
    "skinned",
    "stab",
    "strangling",
    "viscera",
    "wound",
}

DARK_GORE_PHRASES = {
    "missing limb",
}


def normalize_for_matching(term: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", term.casefold()).strip()


def token_set(term: str) -> set[str]:
    normalized = normalize_for_matching(term)
    return set(normalized.split()) if normalized else set()


def has_token(term: str, keywords: set[str]) -> bool:
    return bool(token_set(term) & keywords)


def has_phrase(term: str, phrases: set[str]) -> bool:
    normalized = normalize_for_matching(term)
    return any(phrase in normalized for phrase in phrases)


def has_any(term: str, keywords: set[str], phrases: set[str] | None = None) -> bool:
    return has_token(term, keywords) or has_phrase(term, phrases or set())


def parse_terms(source: Path) -> list[str]:
    text = source.read_text(encoding="utf-8-sig")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = BLANK_LINE_RE.sub(",", text)

    terms = []
    for part in text.split(","):
        lines = [line.strip() for line in part.strip().split("\n")]
        terms.append(" ".join(line for line in lines if line))
    return [term for term in terms if term]


def dedupe_case_insensitive(terms: list[str]) -> list[str]:
    deduped: dict[str, str] = {}
    for term in terms:
        deduped.setdefault(term.casefold(), term)
    return sorted(deduped.values(), key=str.casefold)


def categorize(terms: list[str]) -> dict[str, list[str]]:
    categories: dict[str, list[str]] = {
        "clean": terms,
        "characters_sources": [],
        "hair_eyes": [],
        "clothing_accessories": [],
        "body_features": [],
        "poses_actions": [],
        "settings_props": [],
        "symbols_style": [],
        "mature": [],
        "dark_gore": [],
    }

    for term in terms:
        if "(" in term or r"\(" in term or has_token(term, CHARACTER_SOURCE_TOKENS):
            categories["characters_sources"].append(term)
        if has_any(term, HAIR_EYES_TOKENS, HAIR_EYES_PHRASES):
            categories["hair_eyes"].append(term)
        if has_any(term, CLOTHING_ACCESSORY_TOKENS, CLOTHING_ACCESSORY_PHRASES):
            categories["clothing_accessories"].append(term)
        if has_any(term, BODY_FEATURE_TOKENS, BODY_FEATURE_PHRASES):
            categories["body_features"].append(term)
        if has_any(term, POSE_ACTION_TOKENS, POSE_ACTION_PHRASES):
            categories["poses_actions"].append(term)
        if has_any(term, SETTING_PROP_TOKENS, SETTING_PROP_PHRASES):
            categories["settings_props"].append(term)
        if has_any(term, SYMBOL_STYLE_TOKENS, SYMBOL_STYLE_PHRASES):
            categories["symbols_style"].append(term)
        if has_any(term, MATURE_TOKENS, MATURE_PHRASES):
            categories["mature"].append(term)
        if has_any(term, DARK_GORE_TOKENS, DARK_GORE_PHRASES):
            categories["dark_gore"].append(term)

    return categories


def format_csv(terms: list[str]) -> str:
    return ", ".join(terms) + "\n"


def build_outputs(source: Path) -> tuple[list[str], dict[str, str]]:
    raw_terms = parse_terms(source)
    clean_terms = dedupe_case_insensitive(raw_terms)
    categories = categorize(clean_terms)

    clean_set = set(clean_terms)
    for name, terms in categories.items():
        if any(not term for term in terms):
            raise RuntimeError(f"{name} contains an empty term")
        if not set(terms).issubset(clean_set):
            raise RuntimeError(f"{name} contains terms outside little_doom_clean.csv")

    outputs = {
        OUTPUT_FILES[name]: format_csv(terms)
        for name, terms in categories.items()
    }
    return raw_terms, outputs


def write_outputs(resources_dir: Path, outputs: dict[str, str]) -> None:
    resources_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in outputs.items():
        (resources_dir / filename).write_text(content, encoding="utf-8")


def check_outputs(resources_dir: Path, outputs: dict[str, str]) -> list[str]:
    problems: list[str] = []
    for filename, expected in outputs.items():
        path = resources_dir / filename
        if not path.exists():
            problems.append(f"missing {path}")
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            problems.append(f"out of date {path}")
    return problems


def print_counts(raw_terms: list[str], outputs: dict[str, str]) -> None:
    clean_terms = [term.strip() for term in outputs[OUTPUT_FILES["clean"]].split(",") if term.strip()]
    print(f"source terms: {len(raw_terms)}")
    print(f"unique clean terms: {len(clean_terms)}")
    print(f"duplicates removed: {len(raw_terms) - len(clean_terms)}")
    for name, filename in OUTPUT_FILES.items():
        terms = [term.strip() for term in outputs[filename].split(",") if term.strip()]
        print(f"{filename}: {len(terms)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Little Doom LoRA keyword CSV resources.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Comma-separated source tag file.")
    parser.add_argument("--resources-dir", type=Path, default=RESOURCES_DIR, help="Output resources directory.")
    parser.add_argument("--dry-run", action="store_true", help="Show generated counts without writing files.")
    parser.add_argument("--check", action="store_true", help="Fail when generated files differ from disk.")
    args = parser.parse_args(argv)

    if not args.source.exists():
        raise RuntimeError(f"source file not found: {args.source}")

    raw_terms, outputs = build_outputs(args.source)
    print_counts(raw_terms, outputs)

    if args.check:
        problems = check_outputs(args.resources_dir, outputs)
        if problems:
            for problem in problems:
                print(problem, file=sys.stderr)
            return 1
        print("check passed")
        return 0

    if args.dry_run:
        print("dry run: no files written")
        return 0

    write_outputs(args.resources_dir, outputs)
    print(f"wrote {len(outputs)} files to {args.resources_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
