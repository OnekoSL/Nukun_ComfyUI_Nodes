import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "resources"
SOURCE = RESOURCES / "english_words.csv"


PLACE_ENVIRONMENTS = """
airport alley arena attic backyard balcony barn basement bathroom beach bedroom bridge building cafe canyon castle cave chapel church city classroom cliff club coast corridor cottage countryside desert diner downtown factory farm field forest garden greenhouse gym hallway harbor harbour highway hill hospital hotel house indoor indoors island jungle kitchen laboratory lake library lobby mall mansion market meadow monastery mountain museum office outdoors palace park parking pathway pier plaza pool porch prison rainforest restaurant river road rooftop room school sea shop shoreline stadium station store street studio subway temple theater theatre town trail valley village warehouse waterfall wilderness woods workshop
"""


OBJECTS = """
album armor armour bag ball basket battery bed belt bicycle bike blade blanket boat book boot bottle bowl box bracelet brush bucket button camera candle canvas car card carpet chair clock cloth coin comb computer cord cup curtain desk document door dress envelope fabric fan flag flower folder fork frame glass glove guitar hammer handle hat helmet jacket jar key keyboard knife lamp laptop letter lock map mask mirror necklace needle notebook paint painting pan paper pencil pen phone photograph pillow plate poster ring rope rug scissors screen shelf shirt shoe sign spoon stone suitcase table tablet ticket tool towel toy umbrella vase wallet watch wheel window wire wood
"""


PERSON_NAMES = """
aaron abigail adam adrian alan albert alex alexander alexis alice alicia amanda amber amy andrea andrew angela anna anne anthony arthur ashley austin ava barbara ben benjamin betty brandon brian brittany bruce carl carlos carol caroline catherine charles charlie chris christian christina christine christopher cindy claire daniel david deborah dennis diana donna dorothy dylan edward elizabeth emily emma eric ethan evelyn frank gabriel george grace hannah harry heather henry isabella jack jacob james jason jennifer jeremy jessica john jonathan jose joseph joshua julia justin karen katherine kelly kevin kimberly laura linda lisa logan lucas mark maria marie martha mary matthew megan melissa michael michelle nancy natalie nicholas noah olivia pamela patricia paul peter philip rachel rebecca richard robert ryan samantha samuel sandra sara sarah scott sean sophia stephen steven susan thomas timothy victoria william zachary
"""


COUNTRIES = """
afghanistan albania algeria america andorra angola argentina armenia australia austria azerbaijan bahamas bahrain bangladesh barbados belarus belgium belize benin bhutan bolivia bosnia botswana brazil brunei bulgaria cambodia cameroon canada chad chile china colombia congo croatia cuba cyprus denmark ecuador egypt estonia ethiopia finland france gabon gambia georgia germany ghana greece guatemala guinea haiti honduras hungary iceland india indonesia iran iraq ireland israel italy jamaica japan jordan kazakhstan kenya korea kuwait latvia lebanon liberia libya liechtenstein lithuania luxembourg madagascar malawi malaysia maldives mali malta mauritania mauritius mexico moldova monaco mongolia montenegro morocco mozambique myanmar namibia nepal netherlands nicaragua niger nigeria norway oman pakistan panama paraguay peru philippines poland portugal qatar romania russia rwanda senegal serbia singapore slovakia slovenia somalia spain sudan sweden switzerland syria taiwan tanzania thailand tunisia turkey uganda ukraine uruguay uzbekistan venezuela vietnam yemen zambia zimbabwe
"""


CITIES = """
amsterdam athens atlanta auckland bangkok barcelona beijing berlin birmingham boston brisbane brussels budapest cairo chicago copenhagen dallas delhi denver detroit dubai dublin edinburgh florence glasgow hamburg helsinki houston istanbul jakarta jerusalem johannesburg kyoto lagos lasvegas lisbon liverpool london losangeles madrid manchester melbourne miami milan montreal moscow mumbai munich naples nashville newyork orlando osaka oslo ottawa paris philadelphia phoenix prague rome seattle seoul shanghai singapore stockholm sydney tokyo toronto valencia vancouver venice vienna warsaw washington zurich
"""


SEED_CATEGORIES = {
    "place_environments.csv": PLACE_ENVIRONMENTS,
    "objects.csv": OBJECTS,
    "person_names.csv": PERSON_NAMES,
    "countries.csv": COUNTRIES,
    "cities.csv": CITIES,
}


def read_words(path):
    return [part.strip() for part in path.read_text(encoding="utf-8").split(",") if part.strip()]


def write_words(path, words):
    path.write_text(", ".join(words) + "\n", encoding="utf-8")


def seed_words(seed_text, wordset):
    candidates = {word.strip().lower() for word in seed_text.split() if word.strip()}
    return sorted(word for word in candidates if word in wordset)


def build_categories(source_words):
    wordset = set(source_words)
    categories = {
        file_name: seed_words(seed_text, wordset)
        for file_name, seed_text in SEED_CATEGORIES.items()
    }
    categories["ing_words.csv"] = sorted(word for word in wordset if word.endswith("ing"))
    return categories


def validate_categories(categories, source_words):
    wordset = set(source_words)
    errors = []
    for file_name, words in categories.items():
        if any(not word for word in words):
            errors.append(f"{file_name}: contains an empty entry")
        unknown = [word for word in words if word not in wordset]
        if unknown:
            errors.append(f"{file_name}: contains words outside english_words.csv: {unknown[:10]}")
        bad_markup = [word for word in words if '"' in word or "</w>" in word]
        if bad_markup:
            errors.append(f"{file_name}: contains invalid markup: {bad_markup[:10]}")
        if file_name == "ing_words.csv":
            not_ing = [word for word in words if not word.endswith("ing")]
            if not_ing:
                errors.append(f"{file_name}: contains non-ing words: {not_ing[:10]}")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Build curated vocabulary resource CSV files.")
    parser.add_argument("--check", action="store_true", help="Validate existing generated files without writing.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned counts without writing files.")
    args = parser.parse_args()

    source_words = read_words(SOURCE)
    categories = build_categories(source_words)
    errors = validate_categories(categories, source_words)
    if errors:
        raise SystemExit("\n".join(errors))

    if args.check:
        mismatches = []
        for file_name, words in categories.items():
            path = RESOURCES / file_name
            if not path.exists():
                mismatches.append(f"{file_name}: missing")
                continue
            current = read_words(path)
            if current != words:
                mismatches.append(f"{file_name}: does not match generated output")
        if mismatches:
            raise SystemExit("\n".join(mismatches))

    for file_name, words in categories.items():
        print(f"{file_name}: {len(words)}")
        if not args.check and not args.dry_run:
            write_words(RESOURCES / file_name, words)


if __name__ == "__main__":
    main()
