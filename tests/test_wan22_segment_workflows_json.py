import json
import unittest
from pathlib import Path


COMFY_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = PACKAGE_ROOT / "examples" / "wan22"


class WorkflowJson:
    def __init__(self, filename):
        self.path = WORKFLOW_DIR / filename
        self.workflow = json.loads(self.path.read_text(encoding="utf-8"))
        self.nodes = {int(node["id"]): node for node in self.workflow["nodes"]}
        self.links = {int(link[0]): link for link in self.workflow["links"]}

    def nodes_of_type(self, node_type):
        return [node for node in self.nodes.values() if node["type"] == node_type]

    def link(self, source_id, source_slot, target_id, target_slot):
        return next(
            (
                link
                for link in self.links.values()
                if (int(link[1]), int(link[2]), int(link[3]), int(link[4]))
                == (source_id, source_slot, target_id, target_slot)
            ),
            None,
        )

    def assert_links_valid(self, test_case):
        for node_id, node in self.nodes.items():
            for slot, input_data in enumerate(node.get("inputs", [])):
                link_id = input_data.get("link")
                if link_id is None:
                    continue
                test_case.assertIn(link_id, self.links, f"{self.path.name} input link {link_id}")
                test_case.assertEqual((int(self.links[link_id][3]), int(self.links[link_id][4])), (node_id, slot))
            for slot, output_data in enumerate(node.get("outputs", [])):
                for link_id in output_data.get("links") or []:
                    test_case.assertIn(link_id, self.links, f"{self.path.name} output link {link_id}")
                    test_case.assertEqual((int(self.links[link_id][1]), int(self.links[link_id][2])), (node_id, slot))


class Wan22SegmentWorkflowJsonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.start = WorkflowJson("anima_to_wan2.2_segment_start.json")
        cls.extend = WorkflowJson("wan2.2_segment_extend.json")
        cls.assemble = WorkflowJson("wan2.2_segment_assemble.json")

    def test_all_segment_workflow_links_are_bidirectional(self):
        self.start.assert_links_valid(self)
        self.extend.assert_links_valid(self)
        self.assemble.assert_links_valid(self)

    def test_new_stable_path_does_not_use_easy_loop_nodes(self):
        for workflow in (self.start, self.extend, self.assemble):
            self.assertFalse(
                [node for node in workflow.nodes.values() if node["type"] in {"easy forLoopStart", "easy forLoopEnd"}],
                workflow.path.name,
            )

    def test_start_workflow_stores_decode_frames_as_segment_zero(self):
        decode = self.start.nodes_of_type("VAEDecodeTiled")[0]
        store = self.start.nodes_of_type("NukunWan22SegmentStore")[0]
        settings = self.start.nodes_of_type("NukunWan22VideoSettings")[0]
        self.assertEqual(store["widgets_values"][1], 0)
        self.assertEqual(store["widgets_values"][3:5], [False, True])
        self.assertEqual(settings["widgets_values"][:5], ["image_to_video", "balanced", "portrait", 5, 16])
        self.assertIsNotNone(self.start.link(decode["id"], 0, store["id"], 0))

    def test_start_workflow_has_no_direct_video_save(self):
        self.assertFalse(self.start.nodes_of_type("CreateVideo"))
        self.assertFalse(self.start.nodes_of_type("SaveVideo"))
        self.assertFalse(self.start.nodes_of_type("SaveAnimatedWEBP"))

    def test_extend_workflow_loads_last_frame_caption_renders_and_trims(self):
        loader = self.extend.nodes_of_type("NukunWan22SegmentLoader")[0]
        vision = self.extend.nodes_of_type("NukunOllamaVisionCaptioner")[0]
        latent = self.extend.nodes_of_type("NukunWan22TI2VLatent")[0]
        decode = self.extend.nodes_of_type("VAEDecodeTiled")[0]
        store = self.extend.nodes_of_type("NukunWan22SegmentStore")[0]
        self.assertEqual(loader["widgets_values"], ["wan_run_001", -1])
        self.assertEqual(store["widgets_values"][3:5], [True, True])
        self.assertIsNotNone(self.extend.link(loader["id"], 0, vision["id"], 0))
        self.assertIsNotNone(self.extend.link(loader["id"], 0, latent["id"], 2))
        self.assertIsNotNone(self.extend.link(decode["id"], 0, store["id"], 0))
        self.assertIsNotNone(self.extend.link(loader["id"], 2, store["id"], 2))

    def test_extend_workflow_keeps_prompt_bridge_and_seed_connections_visible(self):
        loader = self.extend.nodes_of_type("NukunWan22SegmentLoader")[0]
        refiner = self.extend.nodes_of_type("NukunOllamaPromptRefiner")[0]
        sampler = self.extend.nodes_of_type("KSampler")[0]
        seed_nodes = self.extend.nodes_of_type("Seed (rgthree)")
        self.assertEqual(len(seed_nodes), 3)
        self.assertEqual({node["widgets_values"][0] for node in seed_nodes}, {33004, 44005, 55006})
        self.assertIsNotNone(self.extend.link(loader["id"], 6, self.extend.nodes_of_type("NukunWan22SegmentStore")[0]["id"], 13))
        self.assertIn("wan2_2_video", refiner["widgets_values"])
        self.assertEqual(sampler["widgets_values"][:7], [55006, "fixed", 25, 5, "dpmpp_2m", "bong_tangent", 1])

    def test_assemble_workflow_uses_frame_sequence_assembler_only(self):
        assembler = self.assemble.nodes_of_type("NukunWan22FrameSequenceAssembler")[0]
        self.assertEqual(assembler["widgets_values"], ["wan_run_001", 16, "final", "libx264", 8, True])
        self.assertFalse(self.assemble.nodes_of_type("CreateVideo"))
        self.assertFalse(self.assemble.nodes_of_type("SaveVideo"))


if __name__ == "__main__":
    unittest.main()
