import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


COMFY_ROOT = Path(__file__).resolve().parents[3]
if str(COMFY_ROOT) not in sys.path:
    sys.path.insert(0, str(COMFY_ROOT))

from custom_nodes.Nukun_ComfyUI_Nodes.nodes import four_prompt_model_cycler_loader as cycler
from custom_nodes.Nukun_ComfyUI_Nodes.nodes import diffusion_clip_vae_cycler_loader as combined_loader


MODELS = [
    "root10.safetensors",
    "root2.safetensors",
    "ANIMA\\model10.safetensors",
    "ANIMA\\model2.safetensors",
    "ANIMA\\nested\\ignored.safetensors",
]


class FourPromptModelCyclerTests(unittest.TestCase):
    def test_four_prompts_then_next_model(self):
        models = cycler._models_in_folder("ANIMA", MODELS)
        prompts = ("one", "two", "three", "four")
        sequence = [cycler._cycle_selection(i, prompts, models)[:2] for i in range(5)]
        self.assertEqual(
            sequence,
            [
                ("one", "ANIMA\\model2.safetensors"),
                ("two", "ANIMA\\model2.safetensors"),
                ("three", "ANIMA\\model2.safetensors"),
                ("four", "ANIMA\\model2.safetensors"),
                ("one", "ANIMA\\model10.safetensors"),
            ],
        )

    def test_complete_cycle_wraps(self):
        models = cycler._models_in_folder("ANIMA", MODELS)
        prompts = ("one", "two", "three", "four")
        self.assertEqual(
            cycler._cycle_selection(8, prompts, models),
            ("one", "ANIMA\\model2.safetensors", 0, 0),
        )

    def test_empty_prompt_is_a_cycle_position(self):
        selected = cycler._cycle_selection(1, ("one", "", "three", "four"), ["model"])
        self.assertEqual(selected, ("", "model", 1, 0))

    def test_seed_stays_fixed_for_four_prompts_then_advances(self):
        self.assertEqual(
            [cycler._seed_for_cycle(100, index) for index in range(8)],
            [100, 100, 100, 100, 101, 101, 101, 101],
        )

    def test_seed_continues_when_models_wrap(self):
        self.assertEqual(cycler._seed_for_cycle(100, 8), 102)

    def test_seed_wraps_at_uint64_limit(self):
        self.assertEqual(cycler._seed_for_cycle(cycler.MAX_INDEX, 4), 0)

    def test_fixed_seed_never_changes(self):
        self.assertEqual(
            [cycler._seed_for_cycle(100, index, "fixed") for index in (0, 3, 4, 999)],
            [100, 100, 100, 100],
        )

    def test_random_mode_uses_frontend_supplied_seed(self):
        self.assertEqual(
            [cycler._seed_for_cycle(987654321, index, "random") for index in (0, 3, 4, 999)],
            [987654321, 987654321, 987654321, 987654321],
        )

    def test_folders_are_exact_and_models_use_natural_sort(self):
        self.assertEqual(
            cycler._models_in_folder("ANIMA", MODELS),
            ["ANIMA\\model2.safetensors", "ANIMA\\model10.safetensors"],
        )
        self.assertEqual(
            cycler._models_in_folder(cycler.ROOT_FOLDER, MODELS),
            ["root2.safetensors", "root10.safetensors"],
        )
        self.assertEqual(
            cycler._models_in_folder("ANIMA/nested", MODELS),
            ["ANIMA\\nested\\ignored.safetensors"],
        )

    def test_empty_or_stale_folder_is_rejected(self):
        with patch.object(cycler, "_unet_names", return_value=MODELS):
            result = cycler.NukunFourPromptModelCyclerLoader.VALIDATE_INPUTS(
                0,
                "missing",
                "one",
                "two",
                "three",
                "four",
                "clip.safetensors",
                "vae.safetensors",
            )
        self.assertEqual(result, "Invalid or empty diffusion-model folder: missing")

    def test_invalid_seed_mode_is_rejected(self):
        with (
            patch.object(cycler, "_unet_names", return_value=MODELS),
            patch.object(cycler.folder_paths, "get_full_path", return_value="clip-path"),
            patch.object(cycler, "_vae_names", return_value=["vae.safetensors"]),
        ):
            result = cycler.NukunFourPromptModelCyclerLoader.VALIDATE_INPUTS(
                0,
                "ANIMA",
                "one",
                "two",
                "three",
                "four",
                "clip.safetensors",
                "vae.safetensors",
                seed_mode="unsupported",
            )
        self.assertEqual(result, "Invalid seed mode: unsupported")

    def test_loader_returns_selected_text_model_and_metadata(self):
        class FakeUNETLoader:
            def load_unet(self, name, dtype):
                return (("model", name, dtype),)

        class FakeCLIPLoader:
            def load_clip(self, name, clip_type, device):
                return (("clip", name, clip_type, device),)

        class FakeVAELoader:
            def load_vae(self, name):
                return (("vae", name),)

        with (
            patch.object(cycler, "_unet_names", return_value=MODELS),
            patch.object(cycler, "UNETLoader", FakeUNETLoader),
            patch.object(cycler, "CLIPLoader", FakeCLIPLoader),
            patch.object(cycler, "VAELoader", FakeVAELoader),
            patch.object(cycler, "_clip_type_for_model", side_effect=lambda model, clip_type: clip_type),
        ):
            result = cycler.NukunFourPromptModelCyclerLoader().load_models(
                4,
                "ANIMA",
                "one",
                "two",
                "three",
                "four",
                "clip.safetensors",
                "vae.safetensors",
            )

        self.assertEqual(result[0], "one")
        self.assertEqual(result[1], ("model", "ANIMA\\model10.safetensors", "default"))
        self.assertEqual(result[4:8], ("model10", "model10", "ANIMA\\model10.safetensors", "ANIMA"))
        self.assertEqual(result[8:], (0, 1, 2, 1))

    def test_node_registration_and_category(self):
        node = cycler.NODE_CLASS_MAPPINGS["NukunFourPromptModelCyclerLoader"]
        self.assertEqual(node.CATEGORY, "Nukun/Loaders")
        self.assertEqual(node.RETURN_NAMES[0], "text")
        inputs = node.INPUT_TYPES()["required"]
        self.assertNotIn("base_seed", inputs)
        self.assertEqual(inputs["seed_mode"][0], cycler.SEED_MODES)
        self.assertEqual(inputs["seed"][1]["control_after_generate"], "fixed")

    def test_current_multimodal_clip_types_are_available(self):
        self.assertIn("boogu", cycler.CLIP_TYPES)
        self.assertIn("krea2", cycler.CLIP_TYPES)

    def test_legacy_stable_diffusion_type_is_corrected_for_krea2(self):
        class FakeKrea2:
            pass

        model = SimpleNamespace(model=FakeKrea2())
        with patch.object(combined_loader.comfy.model_base, "Krea2", FakeKrea2):
            self.assertEqual(cycler._clip_type_for_model(model, "stable_diffusion"), "krea2")
            self.assertEqual(cycler._clip_type_for_model(model, "flux2"), "flux2")


if __name__ == "__main__":
    unittest.main()
