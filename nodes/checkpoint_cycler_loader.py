import os

import comfy.sd
import folder_paths
from nodes import VAELoader


def _model_name(ckpt_name):
    normalized = ckpt_name.replace("\\", "/")
    filename = normalized.rsplit("/", 1)[-1]
    return os.path.splitext(filename)[0]


def _folder_name(ckpt_name):
    normalized = ckpt_name.replace("\\", "/")
    if "/" not in normalized:
        return ""
    return normalized.rsplit("/", 1)[0]


def _checkpoint_folders():
    folders = []
    seen = set()
    for ckpt_name in folder_paths.get_filename_list("checkpoints"):
        folder = _folder_name(ckpt_name)
        if not folder or folder in seen:
            continue
        seen.add(folder)
        folders.append(folder)
    if not folders:
        folders.append("")
    return folders


def _folder_default(folders):
    return "A_pony" if "A_pony" in folders else folders[0]


def _checkpoints_in_folder(checkpoint_folder):
    normalized_folder = checkpoint_folder.replace("\\", "/").strip("/")
    prefix = "{}/".format(normalized_folder) if normalized_folder else ""
    return [
        ckpt_name
        for ckpt_name in folder_paths.get_filename_list("checkpoints")
        if ckpt_name.replace("\\", "/").startswith(prefix)
    ]


def _range_error(checkpoints, model_index_start, model_index_end):
    if not checkpoints:
        return "No checkpoints found in folder"
    last_index = len(checkpoints) - 1
    if model_index_start > last_index:
        return "model_index_start {} is outside the checkpoint range 0..{}".format(model_index_start, last_index)
    effective_end = min(model_index_end, last_index)
    if model_index_start > effective_end:
        return "model_index_start {} is greater than effective model_index_end {}".format(
            model_index_start,
            effective_end,
        )
    return None


def _checkpoint_range(checkpoints, model_index_start, model_index_end):
    error = _range_error(checkpoints, model_index_start, model_index_end)
    if error is not None:
        raise ValueError(error)
    effective_end = min(model_index_end, len(checkpoints) - 1)
    return checkpoints[model_index_start : effective_end + 1]


def _load_checkpoint(ckpt_name):
    ckpt_path = folder_paths.get_full_path_or_raise("checkpoints", ckpt_name)
    out = comfy.sd.load_checkpoint_guess_config(
        ckpt_path,
        output_vae=True,
        output_clip=True,
        embedding_directory=folder_paths.get_folder_paths("embeddings"),
    )
    return out[:3]


class NukunCheckpointCyclerLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ckpt_name": (
                    folder_paths.get_filename_list("checkpoints"),
                    {
                        "control_after_generate": True,
                        "tooltip": "Checkpoint to load. The frontend can increment, decrement, randomize, or wrap this combo after queueing.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("MODEL", "CLIP", "VAE", "modelname", "ckpt_name", "folder")
    FUNCTION = "load_checkpoint"
    CATEGORY = "Nukun/Loaders"
    DESCRIPTION = "Loads a checkpoint and exposes model name metadata, with combo control-after-generate support."

    def load_checkpoint(self, ckpt_name):
        model, clip, vae = _load_checkpoint(ckpt_name)
        return (model, clip, vae, _model_name(ckpt_name), ckpt_name, _folder_name(ckpt_name))

    @classmethod
    def VALIDATE_INPUTS(cls, ckpt_name):
        if folder_paths.get_full_path("checkpoints", ckpt_name) is None:
            return "Invalid checkpoint file: {}".format(ckpt_name)
        return True


def _vae_name_list():
    return ["checkpoint"] + [name for name in VAELoader.vae_list(VAELoader) if name != "checkpoint"]


class NukunCheckpointVaeCyclerLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ckpt_name": (
                    folder_paths.get_filename_list("checkpoints"),
                    {
                        "control_after_generate": True,
                        "tooltip": "Checkpoint to load. The frontend can increment, decrement, randomize, or wrap this combo after queueing.",
                    },
                ),
                "vae_name": (
                    _vae_name_list(),
                    {
                        "default": "checkpoint",
                        "tooltip": "Use 'checkpoint' to keep the checkpoint VAE, or select an external VAE to override it.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("MODEL", "CLIP", "VAE", "modelname", "ckpt_name", "folder")
    FUNCTION = "load_checkpoint"
    CATEGORY = "Nukun/Loaders"
    DESCRIPTION = "Loads a checkpoint with cycler support and optionally overrides its VAE with a selected external VAE."

    def load_checkpoint(self, ckpt_name, vae_name="checkpoint"):
        model, clip, vae = _load_checkpoint(ckpt_name)
        if vae_name != "checkpoint":
            vae = VAELoader().load_vae(vae_name)[0]
        return (model, clip, vae, _model_name(ckpt_name), ckpt_name, _folder_name(ckpt_name))

    @classmethod
    def VALIDATE_INPUTS(cls, ckpt_name, vae_name="checkpoint"):
        if folder_paths.get_full_path("checkpoints", ckpt_name) is None:
            return "Invalid checkpoint file: {}".format(ckpt_name)
        if vae_name != "checkpoint" and vae_name not in VAELoader.vae_list(VAELoader):
            return "Invalid VAE file: {}".format(vae_name)
        return True


class NukunCheckpointPairCyclerLoader:
    @classmethod
    def INPUT_TYPES(cls):
        folders = _checkpoint_folders()
        return {
            "required": {
                "pair_index": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xffffffffffffffff,
                        "control_after_generate": True,
                        "tooltip": "Single matrix index. The second checkpoint advances fastest; the first advances after one full folder pass.",
                    },
                ),
                "checkpoint_folder": (
                    folders,
                    {
                        "default": _folder_default(folders),
                        "tooltip": "Checkpoint subfolder used to build the ordered all-with-all matrix.",
                    },
                ),
                "vae_name": (
                    _vae_name_list(),
                    {
                        "default": "checkpoint",
                        "tooltip": "Use 'checkpoint' to keep the second checkpoint VAE, or select an external VAE to override it.",
                    },
                ),
                "model_index_start": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xffffffffffffffff,
                        "tooltip": "First global model index included in the checkpoint matrix.",
                    },
                ),
                "model_index_end": (
                    "INT",
                    {
                        "default": 0xffffffffffffffff,
                        "min": 0,
                        "max": 0xffffffffffffffff,
                        "tooltip": "Last global model index included in the checkpoint matrix. Values past the folder end use the last model.",
                    },
                ),
            },
        }

    RETURN_TYPES = (
        "MODEL",
        "CLIP",
        "MODEL",
        "CLIP",
        "VAE",
        "STRING",
        "STRING",
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
        "MODEL_1",
        "CLIP_1",
        "MODEL_2",
        "CLIP_2",
        "VAE",
        "modelname_1",
        "modelname_2",
        "combined_modelname",
        "ckpt_name_1",
        "ckpt_name_2",
        "folder",
        "pair_index",
        "model_index_1",
        "model_index_2",
        "total_pairs",
    )
    FUNCTION = "load_pair"
    CATEGORY = "Nukun/Loaders"
    DESCRIPTION = "Loads two checkpoints from one folder as an ordered all-with-all matrix using a single cycling index."

    def load_pair(
        self,
        pair_index,
        checkpoint_folder,
        vae_name="checkpoint",
        model_index_start=0,
        model_index_end=0xffffffffffffffff,
    ):
        checkpoints = _checkpoints_in_folder(checkpoint_folder)
        if not checkpoints:
            raise ValueError("No checkpoints found in folder: {}".format(checkpoint_folder))

        ranged_checkpoints = _checkpoint_range(checkpoints, model_index_start, model_index_end)
        model_count = len(ranged_checkpoints)
        total_pairs = model_count * model_count
        normalized_pair_index = pair_index % total_pairs
        local_index_1 = normalized_pair_index // model_count
        local_index_2 = normalized_pair_index % model_count
        model_index_1 = model_index_start + local_index_1
        model_index_2 = model_index_start + local_index_2
        ckpt_name_1 = ranged_checkpoints[local_index_1]
        ckpt_name_2 = ranged_checkpoints[local_index_2]

        model_1, clip_1, vae_1 = _load_checkpoint(ckpt_name_1)
        if ckpt_name_1 == ckpt_name_2:
            model_2, clip_2, vae_2 = model_1, clip_1, vae_1
        else:
            model_2, clip_2, vae_2 = _load_checkpoint(ckpt_name_2)

        vae = vae_2
        if vae_name != "checkpoint":
            vae = VAELoader().load_vae(vae_name)[0]

        modelname_1 = _model_name(ckpt_name_1)
        modelname_2 = _model_name(ckpt_name_2)
        combined_modelname = "{}__x__{}".format(modelname_1, modelname_2)

        return (
            model_1,
            clip_1,
            model_2,
            clip_2,
            vae,
            modelname_1,
            modelname_2,
            combined_modelname,
            ckpt_name_1,
            ckpt_name_2,
            checkpoint_folder,
            normalized_pair_index,
            model_index_1,
            model_index_2,
            total_pairs,
        )

    @classmethod
    def VALIDATE_INPUTS(
        cls,
        pair_index,
        checkpoint_folder,
        vae_name="checkpoint",
        model_index_start=0,
        model_index_end=0xffffffffffffffff,
    ):
        checkpoints = _checkpoints_in_folder(checkpoint_folder)
        if not checkpoints:
            return "No checkpoints found in folder: {}".format(checkpoint_folder)
        range_error = _range_error(checkpoints, model_index_start, model_index_end)
        if range_error is not None:
            return range_error
        if vae_name != "checkpoint" and vae_name not in VAELoader.vae_list(VAELoader):
            return "Invalid VAE file: {}".format(vae_name)
        return True


NODE_CLASS_MAPPINGS = {
    "NukunCheckpointCyclerLoader": NukunCheckpointCyclerLoader,
    "NukunCheckpointVaeCyclerLoader": NukunCheckpointVaeCyclerLoader,
    "NukunCheckpointPairCyclerLoader": NukunCheckpointPairCyclerLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NukunCheckpointCyclerLoader": "Checkpoint Cycler Loader (Nukun)",
    "NukunCheckpointVaeCyclerLoader": "Checkpoint + VAE Cycler Loader (Nukun)",
    "NukunCheckpointPairCyclerLoader": "Checkpoint Pair Cycler Loader (Nukun)",
}
