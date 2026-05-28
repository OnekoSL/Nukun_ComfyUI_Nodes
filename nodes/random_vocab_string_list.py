import hashlib
import os
import random

import folder_paths


def _vocab_path():
    return os.path.join(folder_paths.get_user_directory(), "vocab.json")


def _bundled_vocab_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources", "vocab.json"))


def _resolve_vocab_path():
    user_path = _vocab_path()
    if os.path.exists(user_path):
        return user_path

    bundled_path = _bundled_vocab_path()
    if os.path.exists(bundled_path):
        return bundled_path

    raise RuntimeError(
        "Random Vocab String List: vocab file not found. Expected "
        f"{user_path} or bundled fallback {bundled_path}"
    )


def _load_words():
    path = _resolve_vocab_path()
    with open(path, "r", encoding="utf-8") as vocab_file:
        text = vocab_file.read()

    words = [part.strip() for part in text.split(",") if part.strip()]
    if not words:
        raise RuntimeError(f"Random Vocab String List: vocab file is empty: {path}")

    return words


class NukunRandomVocabStringList:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "amount": (
                    "INT",
                    {
                        "default": 10,
                        "min": 1,
                        "max": 10000,
                        "tooltip": "Number of random words to output. Clamped to the number of available vocab words.",
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xffffffffffffffff,
                        "control_after_generate": True,
                        "tooltip": "Seed for deterministic random word selection. The frontend can change it after queueing.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("STRING",)
    FUNCTION = "generate"
    CATEGORY = "Nukun/Text"
    DESCRIPTION = "Outputs a deterministic random space-separated word list from ComfyUI/user/vocab.json."

    def generate(self, amount, seed):
        words = _load_words()
        pick_count = min(int(amount), len(words))
        selected = random.Random(int(seed)).sample(words, pick_count)
        return (" ".join(selected),)

    @classmethod
    def IS_CHANGED(cls, amount, seed):
        try:
            path = _resolve_vocab_path()
        except RuntimeError:
            path = ""

        digest = hashlib.sha256()
        digest.update(str(int(amount)).encode("utf-8"))
        digest.update(str(int(seed)).encode("utf-8"))

        if os.path.exists(path):
            with open(path, "rb") as vocab_file:
                digest.update(vocab_file.read())
        else:
            digest.update(b"missing")

        return digest.hexdigest()


NODE_CLASS_MAPPINGS = {
    "NukunRandomVocabStringList": NukunRandomVocabStringList,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NukunRandomVocabStringList": "Random Vocab String List (Nukun)",
}
