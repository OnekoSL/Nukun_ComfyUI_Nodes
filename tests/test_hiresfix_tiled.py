import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


COMFY_ROOT = Path(__file__).resolve().parents[3]
CUSTOM_NODES_ROOT = COMFY_ROOT / "custom_nodes"
NUKUN_ROOT = CUSTOM_NODES_ROOT / "Nukun_ComfyUI_Nodes"

sys.path.insert(0, str(COMFY_ROOT))
import nodes as comfy_nodes  # noqa: E402

package_name = "nukun_hiresfix_test_nodes"
package = types.ModuleType(package_name)
package.__path__ = [str(NUKUN_ROOT / "nodes")]
sys.modules[package_name] = package
hiresfix_tiled = importlib.import_module(f"{package_name}.hiresfix_tiled")


class HiResFixTiledDependencyTests(unittest.TestCase):
    def test_uses_registered_ultimate_sd_upscale_node(self):
        expected = object()
        with mock.patch.dict(
            hiresfix_tiled.nodes.NODE_CLASS_MAPPINGS,
            {"UltimateSDUpscaleNoUpscale": expected},
        ):
            self.assertIs(
                hiresfix_tiled._load_ultimate_sd_upscale_no_upscale(),
                expected,
            )

    def test_reports_when_ultimate_sd_upscale_node_is_not_loaded(self):
        with mock.patch.dict(comfy_nodes.NODE_CLASS_MAPPINGS, {}, clear=True):
            with self.assertRaisesRegex(
                ImportError,
                "Install or enable ComfyUI_UltimateSDUpscale",
            ):
                hiresfix_tiled._load_ultimate_sd_upscale_no_upscale()


if __name__ == "__main__":
    unittest.main()
