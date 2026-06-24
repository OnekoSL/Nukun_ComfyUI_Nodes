import folder_paths

from .checkpoint_cycler_loader import _folder_name, _load_checkpoint, _model_name
from .diffusion_clip_vae_cycler_loader import _filename_model_name
from .four_prompt_model_cycler_loader import (
    MAX_INDEX,
    ROOT_FOLDER,
    SEED_MODES,
    _cycle_selection,
    _natural_key,
    _seed_for_cycle,
)


def _checkpoint_names():
    return folder_paths.get_filename_list("checkpoints")


def _folder_value(folder_name):
    return "" if folder_name == ROOT_FOLDER else folder_name.replace("\\", "/")


def _folder_choices(checkpoint_names=None):
    names = _checkpoint_names() if checkpoint_names is None else checkpoint_names
    folders = {_folder_name(name).replace("\\", "/") for name in names}
    return [ROOT_FOLDER if folder == "" else folder for folder in sorted(folders, key=_natural_key)]


def _checkpoints_in_exact_folder(folder_name, checkpoint_names=None):
    names = _checkpoint_names() if checkpoint_names is None else checkpoint_names
    selected_folder = _folder_value(folder_name)
    matching = [
        name
        for name in names
        if _folder_name(name).replace("\\", "/") == selected_folder
    ]
    return sorted(matching, key=_natural_key)


def _preferred_folder(folder_choices):
    return "A_pony" if "A_pony" in folder_choices else folder_choices[0]


class NukunFourPromptCheckpointCyclerLoader:
    @classmethod
    def INPUT_TYPES(cls):
        checkpoint_names = _checkpoint_names()
        folder_choices = _folder_choices(checkpoint_names) or [ROOT_FOLDER]
        prompt_options = {
            "default": "",
            "multiline": True,
            "dynamicPrompts": True,
        }
        return {
            "required": {
                "cycle_index": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": MAX_INDEX,
                        "control_after_generate": "increment",
                        "tooltip": "Advances through four prompts per checkpoint. Keep control after generate on increment.",
                    },
                ),
                "checkpoint_folder": (
                    folder_choices,
                    {
                        "default": _preferred_folder(folder_choices),
                        "tooltip": "Exact checkpoint folder to cycle; nested folders are separate choices.",
                    },
                ),
                "text_1": ("STRING", dict(prompt_options)),
                "text_2": ("STRING", dict(prompt_options)),
                "text_3": ("STRING", dict(prompt_options)),
                "text_4": ("STRING", dict(prompt_options)),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": MAX_INDEX,
                        "control_after_generate": "fixed",
                        "tooltip": "Starting or fixed seed. Random mode updates this widget only when a new four-prompt checkpoint group is queued.",
                    },
                ),
                "seed_mode": (
                    SEED_MODES,
                    {
                        "default": "increment",
                        "tooltip": "Increment once per checkpoint, stay fixed, or choose a new random seed once per checkpoint.",
                    },
                ),
            }
        }

    RETURN_TYPES = (
        "STRING",
        "MODEL",
        "CLIP",
        "VAE",
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "INT",
        "INT",
        "INT",
        "INT",
    )
    RETURN_NAMES = (
        "text",
        "MODEL",
        "CLIP",
        "VAE",
        "modelname",
        "filename_modelname",
        "ckpt_name",
        "folder",
        "prompt_index",
        "model_index",
        "model_count",
        "seed",
    )
    FUNCTION = "load_checkpoint"
    CATEGORY = "Nukun/Loaders"
    DESCRIPTION = "Cycles four prompt texts per checkpoint with an incrementing, fixed, or random checkpoint-synchronous seed."

    def load_checkpoint(
        self,
        cycle_index,
        checkpoint_folder,
        text_1,
        text_2,
        text_3,
        text_4,
        seed=0,
        seed_mode="increment",
    ):
        checkpoints = _checkpoints_in_exact_folder(checkpoint_folder)
        text, ckpt_name, prompt_index, model_index = _cycle_selection(
            cycle_index,
            (text_1, text_2, text_3, text_4),
            checkpoints,
        )
        model, clip, vae = _load_checkpoint(ckpt_name)
        return (
            text,
            model,
            clip,
            vae,
            _model_name(ckpt_name),
            _filename_model_name(ckpt_name),
            ckpt_name,
            _folder_name(ckpt_name),
            prompt_index,
            model_index,
            len(checkpoints),
            _seed_for_cycle(seed, cycle_index, seed_mode),
        )

    @classmethod
    def VALIDATE_INPUTS(
        cls,
        cycle_index,
        checkpoint_folder,
        text_1,
        text_2,
        text_3,
        text_4,
        seed=0,
        seed_mode="increment",
    ):
        if not _checkpoints_in_exact_folder(checkpoint_folder):
            return "Invalid or empty checkpoint folder: {}".format(checkpoint_folder)
        if seed_mode not in SEED_MODES:
            return "Invalid seed mode: {}".format(seed_mode)
        return True


NODE_CLASS_MAPPINGS = {
    "NukunFourPromptCheckpointCyclerLoader": NukunFourPromptCheckpointCyclerLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NukunFourPromptCheckpointCyclerLoader": "4-Prompt Checkpoint Cycler Loader (Nukun)",
}
