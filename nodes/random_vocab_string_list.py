import hashlib
import os
import random

import folder_paths

RESOURCE_EXTENSIONS = (".csv", ".txt", ".json")
USER_VOCAB_LABEL = "user/vocab.json"


def _vocab_path():
    return os.path.join(folder_paths.get_user_directory(), "vocab.json")


def _resources_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources"))


def _list_resource_vocab_files():
    resources_dir = _resources_dir()
    if not os.path.isdir(resources_dir):
        return []

    files = []
    for file_name in os.listdir(resources_dir):
        if file_name.lower().endswith(RESOURCE_EXTENSIONS):
            files.append(f"resources/{file_name}")
    return sorted(files)


def _available_vocab_files():
    files = []
    user_path = _vocab_path()
    if os.path.exists(user_path):
        files.append(USER_VOCAB_LABEL)
    files.extend(_list_resource_vocab_files())
    if not files:
        files.append(USER_VOCAB_LABEL)
    return files


def _resolve_vocab_path(vocab_file):
    if vocab_file == USER_VOCAB_LABEL:
        user_path = _vocab_path()
        if os.path.exists(user_path):
            return user_path

        resource_files = _list_resource_vocab_files()
        if resource_files:
            return _resolve_vocab_path(resource_files[0])

        raise RuntimeError(f"Random Vocab String List: vocab file not found: {user_path}")

    if vocab_file.startswith("resources/"):
        file_name = os.path.basename(vocab_file)
        path = os.path.abspath(os.path.join(_resources_dir(), file_name))
        resources_dir = _resources_dir()
        if os.path.commonpath([resources_dir, path]) != resources_dir:
            raise RuntimeError(f"Random Vocab String List: invalid vocab file: {vocab_file}")
        if os.path.exists(path):
            return path

    raise RuntimeError(f"Random Vocab String List: vocab file not found: {vocab_file}")


def _load_words(vocab_file):
    path = _resolve_vocab_path(vocab_file)
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
            "optional": {
                "chain": (
                    "STRING",
                    {
                        "default": "",
                        "defaultInput": True,
                        "forceInput": True,
                        "multiline": False,
                        "tooltip": "Optional incoming string. When connected, generated words are appended after it.",
                    },
                ),
            },
            "required": {
                "vocab_file": (
                    _available_vocab_files(),
                    {
                        "default": USER_VOCAB_LABEL if USER_VOCAB_LABEL in _available_vocab_files() else _available_vocab_files()[0],
                        "tooltip": "Comma-separated word list to sample from. Add .csv, .txt, or .json files to this node pack's resources folder.",
                    },
                ),
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
    DESCRIPTION = "Outputs a deterministic random space-separated word list from a selectable vocabulary file, optionally appended to an incoming string."

    def generate(self, vocab_file, amount, seed, chain=""):
        words = _load_words(vocab_file)
        pick_count = min(int(amount), len(words))
        selected = random.Random(int(seed)).sample(words, pick_count)
        generated = " ".join(selected)
        chain = chain.strip()
        if chain:
            return (f"{chain} {generated}",)
        return (generated,)

    @classmethod
    def IS_CHANGED(cls, vocab_file, amount, seed):
        try:
            path = _resolve_vocab_path(vocab_file)
        except RuntimeError:
            path = ""

        digest = hashlib.sha256()
        digest.update(str(vocab_file).encode("utf-8"))
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
