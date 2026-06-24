import json
import unittest
from pathlib import Path


COMFY_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_PATH = COMFY_ROOT / "pysssss-workflows" / "wan2.2_video_toolkit.json"


class Wan22WorkflowJsonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
        cls.nodes = {int(node["id"]): node for node in cls.workflow["nodes"]}
        cls.links = {int(link[0]): link for link in cls.workflow["links"]}

    def test_every_input_and_output_declaration_points_to_the_same_link_endpoint(self):
        for node_id, node in self.nodes.items():
            for slot, input_data in enumerate(node.get("inputs", [])):
                link_id = input_data.get("link")
                if link_id is None:
                    continue
                self.assertIn(link_id, self.links)
                link = self.links[link_id]
                self.assertEqual((int(link[3]), int(link[4])), (node_id, slot))

            for slot, output_data in enumerate(node.get("outputs", [])):
                for link_id in output_data.get("links") or []:
                    self.assertIn(link_id, self.links)
                    link = self.links[link_id]
                    self.assertEqual((int(link[1]), int(link[2])), (node_id, slot))

    def test_tiled_decode_receives_the_ksampler_latent(self):
        sampler = next(node for node in self.nodes.values() if node["type"] == "KSampler")
        decode = next(node for node in self.nodes.values() if node["type"] == "VAEDecodeTiled")
        link_id = decode["inputs"][0]["link"]
        link = self.links[link_id]
        self.assertEqual(link[5], "LATENT")
        self.assertEqual(int(link[1]), int(sampler["id"]))
        self.assertEqual(int(link[3]), int(decode["id"]))
        self.assertIn(link_id, sampler["outputs"][0]["links"])


if __name__ == "__main__":
    unittest.main()
