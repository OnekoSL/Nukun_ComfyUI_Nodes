import hashlib
import os

import folder_paths
import numpy as np
import torch
from PIL import Image, ImageOps


class LoadImage:
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        exclude_folders = ["clipspace", "folder_to_exclude2"]
        file_list = []

        for root, dirs, files in os.walk(input_dir):
            dirs[:] = [d for d in dirs if d not in exclude_folders]

            for file in files:
                file_path = os.path.relpath(os.path.join(root, file), start=input_dir)
                file_path = file_path.replace("\\", "/")
                file_list.append(file_path)

        return {
            "required": {
                "image": (sorted(file_list), {"image_upload": True}),
            },
        }

    CATEGORY = "Nukun/Image"
    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image"

    def load_image(self, image):
        image_path = folder_paths.get_annotated_filepath(image)
        image_file = Image.open(image_path)
        image_file = ImageOps.exif_transpose(image_file)
        image_rgb = image_file.convert("RGB")
        image_np = np.array(image_rgb).astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(image_np)[None,]

        if "A" in image_file.getbands():
            mask_np = np.array(image_file.getchannel("A")).astype(np.float32) / 255.0
            mask = 1.0 - torch.from_numpy(mask_np)
        else:
            mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")

        return (image_tensor, mask.unsqueeze(0))

    @classmethod
    def IS_CHANGED(cls, image):
        image_path = folder_paths.get_annotated_filepath(image)
        digest = hashlib.sha256()
        with open(image_path, "rb") as image_file:
            digest.update(image_file.read())
        return digest.hexdigest()

    @classmethod
    def VALIDATE_INPUTS(cls, image):
        if not folder_paths.exists_annotated_filepath(image):
            return "Invalid image file: {}".format(image)
        return True


NODE_CLASS_MAPPINGS = {
    "LoadImagewithSubfolders": LoadImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImagewithSubfolders": "Load Image with Subfolders",
}
