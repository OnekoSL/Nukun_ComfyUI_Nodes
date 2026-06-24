import sys
import unittest
from pathlib import Path
from unittest.mock import patch


COMFY_ROOT = Path(__file__).resolve().parents[3]
if str(COMFY_ROOT) not in sys.path:
    sys.path.insert(0, str(COMFY_ROOT))

from custom_nodes.Nukun_ComfyUI_Nodes.nodes import four_prompt_checkpoint_cycler_loader as cycler


CHECKPOINTS = [
    "root10.safetensors",
    "root2.safetensors",
    "A_pony\\pony10.safetensors",
    "A_pony\\pony2.safetensors",
    "A_pony\\nested\\ignored.safetensors",
]


class FourPromptCheckpointCyclerTests(unittest.TestCase):
    def test_four_prompts_then_next_checkpoint(self):
        checkpoints = cycler._checkpoints_in_exact_folder("A_pony", CHECKPOINTS)
        prompts = ("one", "two", "three", "four")
        sequence = [cycler._cycle_selection(i, prompts, checkpoints)[:2] for i in range(5)]
        self.assertEqual(
            sequence,
            [
                ("one", "A_pony\\pony2.safetensors"),
                ("two", "A_pony\\pony2.safetensors"),
                ("three", "A_pony\\pony2.safetensors"),
                ("four", "A_pony\\pony2.safetensors"),
                ("one", "A_pony\\pony10.safetensors"),
            ],
        )

    def test_checkpoint_folders_are_exact_and_naturally_sorted(self):
        self.assertEqual(
            cycler._checkpoints_in_exact_folder("A_pony", CHECKPOINTS),
            ["A_pony\\pony2.safetensors", "A_pony\\pony10.safetensors"],
        )
        self.assertEqual(
            cycler._checkpoints_in_exact_folder(cycler.ROOT_FOLDER, CHECKPOINTS),
            ["root2.safetensors", "root10.safetensors"],
        )
        self.assertEqual(
            cycler._checkpoints_in_exact_folder("A_pony/nested", CHECKPOINTS),
            ["A_pony\\nested\\ignored.safetensors"],
        )

    def test_loader_returns_checkpoint_outputs_and_synchronized_seed(self):
        with (
            patch.object(cycler, "_checkpoint_names", return_value=CHECKPOINTS),
            patch.object(cycler, "_load_checkpoint", return_value=("model", "clip", "vae")),
        ):
            result = cycler.NukunFourPromptCheckpointCyclerLoader().load_checkpoint(
                4,
                "A_pony",
                "one",
                "two",
                "three",
                "four",
                seed=100,
                seed_mode="increment",
            )

        self.assertEqual(result[:4], ("one", "model", "clip", "vae"))
        self.assertEqual(
            result[4:8],
            ("pony10", "pony10", "A_pony\\pony10.safetensors", "A_pony"),
        )
        self.assertEqual(result[8:], (0, 1, 2, 101))

    def test_empty_folder_and_invalid_seed_mode_are_rejected(self):
        with patch.object(cycler, "_checkpoint_names", return_value=CHECKPOINTS):
            empty = cycler.NukunFourPromptCheckpointCyclerLoader.VALIDATE_INPUTS(
                0, "missing", "one", "two", "three", "four"
            )
            invalid_mode = cycler.NukunFourPromptCheckpointCyclerLoader.VALIDATE_INPUTS(
                0, "A_pony", "one", "two", "three", "four", seed_mode="unsupported"
            )
        self.assertEqual(empty, "Invalid or empty checkpoint folder: missing")
        self.assertEqual(invalid_mode, "Invalid seed mode: unsupported")

    def test_node_registration_and_interface(self):
        node = cycler.NODE_CLASS_MAPPINGS["NukunFourPromptCheckpointCyclerLoader"]
        self.assertEqual(node.CATEGORY, "Nukun/Loaders")
        self.assertEqual(node.RETURN_NAMES[:4], ("text", "MODEL", "CLIP", "VAE"))
        self.assertEqual(node.RETURN_NAMES[-1], "seed")
        self.assertEqual(node.INPUT_TYPES()["required"]["seed"][1]["control_after_generate"], "fixed")


if __name__ == "__main__":
    unittest.main()
