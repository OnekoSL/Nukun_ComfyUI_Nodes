import re

import folder_paths
from nodes import CLIPLoader, UNETLoader, VAELoader

from .diffusion_clip_vae_cycler_loader import (
    CLIP_DEVICES,
    CLIP_TYPES,
    PREFERRED_CLIP,
    PREFERRED_UNET,
    PREFERRED_VAE,
    WEIGHT_DTYPES,
    _filename_model_name,
    _folder_name,
    _model_name,
    _preferred_name,
)


ROOT_FOLDER = "(root)"
MAX_INDEX = 0xFFFFFFFFFFFFFFFF
SEED_MODES = ("increment", "fixed", "random")


def _natural_key(value):
    return tuple(
        int(part) if part.isdigit() else part.casefold()
        for part in re.split(r"(\d+)", value.replace("\\", "/"))
    )


def _unet_names():
    return folder_paths.get_filename_list("diffusion_models")


def _clip_names():
    return folder_paths.get_filename_list("text_encoders")


def _vae_names():
    return VAELoader.vae_list(VAELoader)


def _folder_value(folder_name):
    return "" if folder_name == ROOT_FOLDER else folder_name.replace("\\", "/")


def _folder_choices(unet_names=None):
    names = _unet_names() if unet_names is None else unet_names
    folders = {_folder_name(name).replace("\\", "/") for name in names}
    return [ROOT_FOLDER if folder == "" else folder for folder in sorted(folders, key=_natural_key)]


def _models_in_folder(folder_name, unet_names=None):
    names = _unet_names() if unet_names is None else unet_names
    selected_folder = _folder_value(folder_name)
    matching = [
        name
        for name in names
        if _folder_name(name).replace("\\", "/") == selected_folder
    ]
    return sorted(matching, key=_natural_key)


def _preferred_folder(folder_choices):
    preferred = _folder_name(PREFERRED_UNET).replace("\\", "/") or ROOT_FOLDER
    return preferred if preferred in folder_choices else folder_choices[0]


def _cycle_selection(cycle_index, prompts, models):
    if not models:
        raise ValueError("The selected model folder contains no models.")
    raw_index = int(cycle_index)
    prompt_index = raw_index % 4
    model_index = (raw_index // 4) % len(models)
    return prompts[prompt_index], models[model_index], prompt_index, model_index


def _seed_for_cycle(seed, cycle_index, seed_mode="increment"):
    seed = int(seed) & MAX_INDEX
    if seed_mode == "increment":
        return (seed + (int(cycle_index) // 4)) & MAX_INDEX
    return seed


class NukunFourPromptModelCyclerLoader:
    @classmethod
    def INPUT_TYPES(cls):
        unet_names = _unet_names()
        folder_choices = _folder_choices(unet_names) or [ROOT_FOLDER]
        clip_names = _clip_names()
        vae_names = _vae_names()
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
                        "tooltip": "Advances through four prompts per model. Keep control after generate on increment.",
                    },
                ),
                "unet_folder": (
                    folder_choices,
                    {
                        "default": _preferred_folder(folder_choices),
                        "tooltip": "Exact diffusion-model folder to cycle; nested folders are separate choices.",
                    },
                ),
                "text_1": ("STRING", dict(prompt_options)),
                "text_2": ("STRING", dict(prompt_options)),
                "text_3": ("STRING", dict(prompt_options)),
                "text_4": ("STRING", dict(prompt_options)),
                "clip_name": (
                    clip_names,
                    {
                        "default": _preferred_name(clip_names, PREFERRED_CLIP),
                        "tooltip": "Text encoder/CLIP shared by every model in the cycle.",
                    },
                ),
                "vae_name": (
                    vae_names,
                    {
                        "default": _preferred_name(vae_names, PREFERRED_VAE),
                        "tooltip": "VAE shared by every model in the cycle.",
                    },
                ),
                "weight_dtype": (
                    WEIGHT_DTYPES,
                    {"default": "default", "advanced": True},
                ),
                "clip_type": (CLIP_TYPES, {"default": "stable_diffusion"}),
                "clip_device": (
                    CLIP_DEVICES,
                    {"default": "default", "advanced": True},
                ),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": MAX_INDEX,
                        "control_after_generate": "fixed",
                        "tooltip": "Starting or fixed seed. Random mode updates this widget only when a new four-prompt model group is queued.",
                    },
                ),
                "seed_mode": (
                    SEED_MODES,
                    {
                        "default": "increment",
                        "tooltip": "Increment once per model, stay fixed, or choose a new random seed once per model.",
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
        "unet_name",
        "folder",
        "prompt_index",
        "model_index",
        "model_count",
        "seed",
    )
    FUNCTION = "load_models"
    CATEGORY = "Nukun/Loaders"
    DESCRIPTION = "Cycles four prompt texts per diffusion model with an incrementing, fixed, or random model-synchronous seed."

    def load_models(
        self,
        cycle_index,
        unet_folder,
        text_1,
        text_2,
        text_3,
        text_4,
        clip_name,
        vae_name,
        weight_dtype="default",
        clip_type="stable_diffusion",
        clip_device="default",
        seed=0,
        seed_mode="increment",
    ):
        models = _models_in_folder(unet_folder)
        text, unet_name, prompt_index, model_index = _cycle_selection(
            cycle_index,
            (text_1, text_2, text_3, text_4),
            models,
        )
        model = UNETLoader().load_unet(unet_name, weight_dtype)[0]
        clip = CLIPLoader().load_clip(clip_name, clip_type, clip_device)[0]
        vae = VAELoader().load_vae(vae_name)[0]
        return (
            text,
            model,
            clip,
            vae,
            _model_name(unet_name),
            _filename_model_name(unet_name),
            unet_name,
            _folder_name(unet_name),
            prompt_index,
            model_index,
            len(models),
            _seed_for_cycle(seed, cycle_index, seed_mode),
        )

    @classmethod
    def VALIDATE_INPUTS(
        cls,
        cycle_index,
        unet_folder,
        text_1,
        text_2,
        text_3,
        text_4,
        clip_name,
        vae_name,
        weight_dtype="default",
        clip_type="stable_diffusion",
        clip_device="default",
        seed=0,
        seed_mode="increment",
    ):
        models = _models_in_folder(unet_folder)
        if not models:
            return "Invalid or empty diffusion-model folder: {}".format(unet_folder)
        if folder_paths.get_full_path("text_encoders", clip_name) is None:
            return "Invalid CLIP/text encoder file: {}".format(clip_name)
        if vae_name not in _vae_names():
            return "Invalid VAE file: {}".format(vae_name)
        if weight_dtype not in WEIGHT_DTYPES:
            return "Invalid weight dtype: {}".format(weight_dtype)
        if clip_type not in CLIP_TYPES:
            return "Invalid CLIP type: {}".format(clip_type)
        if clip_device not in CLIP_DEVICES:
            return "Invalid CLIP device: {}".format(clip_device)
        if seed_mode not in SEED_MODES:
            return "Invalid seed mode: {}".format(seed_mode)
        return True


NODE_CLASS_MAPPINGS = {
    "NukunFourPromptModelCyclerLoader": NukunFourPromptModelCyclerLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NukunFourPromptModelCyclerLoader": "4-Prompt Model Cycler Loader (Nukun)",
}
