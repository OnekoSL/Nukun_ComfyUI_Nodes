import time

import comfy.utils
import numpy as np
from PIL import Image


class SaveImageWebsocket:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "Nukun/Image"

    def save_images(self, images):
        pbar = comfy.utils.ProgressBar(images.shape[0])
        step = 0
        for image in images:
            image_np = 255.0 * image.cpu().numpy()
            image_file = Image.fromarray(np.clip(image_np, 0, 255).astype(np.uint8))
            pbar.update_absolute(step, images.shape[0], ("PNG", image_file, None))
            step += 1

        return {}

    @classmethod
    def IS_CHANGED(cls, images):
        return time.time()


NODE_CLASS_MAPPINGS = {
    "SaveImageWebsocket": SaveImageWebsocket,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageWebsocket": "Save Image (Websocket)",
}
