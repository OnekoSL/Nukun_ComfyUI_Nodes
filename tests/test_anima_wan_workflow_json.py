import json
import unittest
from pathlib import Path


COMFY_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_PATH = COMFY_ROOT / "pysssss-workflows" / "anima_to_wan2.2_i2v.json"


class AnimaWanWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
        cls.nodes = {int(node["id"]): node for node in cls.workflow["nodes"]}
        cls.links = {int(link[0]): link for link in cls.workflow["links"]}

    def nodes_of_type(self, node_type):
        return [node for node in self.nodes.values() if node["type"] == node_type]

    def find_link(self, source_id, source_slot, target_id, target_slot):
        return next(
            (
                link
                for link in self.links.values()
                if (int(link[1]), int(link[2]), int(link[3]), int(link[4]))
                == (source_id, source_slot, target_id, target_slot)
            ),
            None,
        )

    def test_all_declared_links_match_both_endpoints(self):
        self.assertEqual(len(self.links), len(self.workflow["links"]))
        for node_id, node in self.nodes.items():
            for slot, input_data in enumerate(node.get("inputs", [])):
                link_id = input_data.get("link")
                if link_id is None:
                    continue
                self.assertIn(link_id, self.links)
                self.assertEqual(
                    (int(self.links[link_id][3]), int(self.links[link_id][4])),
                    (node_id, slot),
                )
            for slot, output_data in enumerate(node.get("outputs", [])):
                for link_id in output_data.get("links") or []:
                    self.assertIn(link_id, self.links)
                    self.assertEqual(
                        (int(self.links[link_id][1]), int(self.links[link_id][2])),
                        (node_id, slot),
                    )

    def test_anima_keyframe_feeds_vision_caption_and_wan_i2v(self):
        anima_decode = self.nodes_of_type("VAEDecode")[0]
        vision = self.nodes_of_type("NukunOllamaVisionCaptioner")[0]
        wan_latent = self.nodes_of_type("NukunWan22TI2VLatent")[0]
        self.assertIsNotNone(self.find_link(anima_decode["id"], 0, vision["id"], 0))
        self.assertIsNotNone(self.find_link(anima_decode["id"], 0, wan_latent["id"], 2))

    def test_vision_seed_and_manual_motion_feed_wan_refiner(self):
        vision = self.nodes_of_type("NukunOllamaVisionCaptioner")[0]
        refiners = self.nodes_of_type("NukunOllamaPromptRefiner")
        wan_refiner = next(node for node in refiners if "wan2_2_video" in node["widgets_values"])
        motion = next(node for node in self.nodes_of_type("BetterString") if node.get("title") == "motion_instruction")
        bridge = next(
            node
            for node in self.nodes_of_type("CR Text Concatenate")
            if node["id"] < 48
        )
        self.assertIsNotNone(self.find_link(vision["id"], 2, bridge["id"], 1))
        self.assertIsNotNone(self.find_link(motion["id"], 0, bridge["id"], 0))
        self.assertIsNotNone(self.find_link(bridge["id"], 0, wan_refiner["id"], 1))

    def test_default_video_settings_are_balanced_portrait_five_seconds(self):
        settings = self.nodes_of_type("NukunWan22VideoSettings")[0]
        self.assertEqual(
            settings["widgets_values"][:5],
            ["image_to_video", "balanced", "portrait", 5, 16],
        )

    def test_anima_and_wan_latents_have_expected_default_sizes(self):
        anima_latent = self.nodes_of_type("EmptySD3LatentImage")[0]
        self.assertEqual(anima_latent["widgets_values"], [704, 1248, 1])
        settings = self.nodes_of_type("NukunWan22VideoSettings")[0]
        self.assertEqual(settings["widgets_values"][5:7], [544, 960])

    def test_tiled_decode_receives_only_the_wan_ksampler_latent(self):
        for decode in self.nodes_of_type("VAEDecodeTiled"):
            link = self.links[decode["inputs"][0]["link"]]
            source = self.nodes[int(link[1])]
            self.assertEqual(link[5], "LATENT")
            self.assertEqual(source["type"], "KSampler")

    def test_five_independent_seed_nodes_are_visible(self):
        seeds = self.nodes_of_type("Seed (rgthree)")
        self.assertEqual(len(seeds), 5)
        self.assertEqual(len({node["widgets_values"][0] for node in seeds}), 5)

    def test_wan_seed_only_drives_wan_sampler_and_manifest(self):
        seed = next(node for node in self.nodes_of_type("Seed (rgthree)") if "Wan Sampling" in node.get("title", ""))
        targets = {
            self.nodes[int(self.links[link_id][3])]["type"]
            for link_id in seed["outputs"][0]["links"]
        }
        self.assertEqual(targets, {"KSampler", "NukunWan22RunManifest"})

    def test_loop_state_starts_with_endframe_batch_and_empty_log(self):
        plan = self.nodes_of_type("NukunWan22ContinuationPlan")[0]
        loop = self.nodes_of_type("easy forLoopStart")[0]
        first_decode = self.nodes_of_type("VAEDecodeTiled")[0]
        endframe = next(
            node
            for node in self.nodes_of_type("ImageFromBatch+")
            if node.get("title") == "Endframe des ersten Clips"
        )
        self.assertEqual(plan["widgets_values"], [1])
        self.assertIsNotNone(self.find_link(first_decode["id"], 0, endframe["id"], 0))
        self.assertIsNotNone(self.find_link(endframe["id"], 0, loop["id"], 1))
        self.assertIsNotNone(self.find_link(first_decode["id"], 0, loop["id"], 2))
        self.assertIsNotNone(self.find_link(plan["id"], 6, loop["id"], 3))

    def test_loop_endframe_is_cleaned_captioned_and_used_for_i2v(self):
        loop = self.nodes_of_type("easy forLoopStart")[0]
        cleaner = self.nodes_of_type("easy cleanGpuUsed")[0]
        current_vision = next(
            node
            for node in self.nodes_of_type("NukunOllamaVisionCaptioner")
            if "aktuelles Endframe" in node.get("title", "")
        )
        continuation_latent = next(
            node
            for node in self.nodes_of_type("NukunWan22TI2VLatent")
            if "Endframe" in node.get("title", "")
        )
        self.assertIsNotNone(self.find_link(loop["id"], 2, cleaner["id"], 0))
        self.assertIsNotNone(self.find_link(cleaner["id"], 0, current_vision["id"], 0))
        self.assertIsNotNone(self.find_link(cleaner["id"], 0, continuation_latent["id"], 2))

    def test_loop_seed_offsets_and_seam_nodes_are_explicit(self):
        math_nodes = {node.get("title", ""): node for node in self.nodes_of_type("easy mathInt")}
        self.assertEqual(math_nodes["Vision Seed · 33003 + i + 1"]["widgets_values"][1:], [33003, "add"])
        self.assertEqual(math_nodes["Wan Prompt Seed · 44004 + i + 1"]["widgets_values"][1:], [44004, "add"])
        self.assertEqual(math_nodes["Wan Sampling Seed · 55005 + i + 1"]["widgets_values"][1:], [55005, "add"])
        tail = next(
            node
            for node in self.nodes_of_type("ImageFromBatch+")
            if "Frames 1–80" in node.get("title", "")
        )
        self.assertEqual(tail["widgets_values"], [1, -1])

    def test_only_loop_result_reaches_final_video_outputs(self):
        loop_end = self.nodes_of_type("easy forLoopEnd")[0]
        create_video = self.nodes_of_type("CreateVideo")[0]
        webp = self.nodes_of_type("SaveAnimatedWEBP")[0]
        self.assertIsNotNone(self.find_link(loop_end["id"], 1, create_video["id"], 0))
        self.assertIsNotNone(self.find_link(loop_end["id"], 1, webp["id"], 0))
        self.assertEqual(webp["mode"], 4)

    def test_final_manifest_uses_loop_log_and_controls_save_prefix(self):
        loop_end = self.nodes_of_type("easy forLoopEnd")[0]
        manifest = self.nodes_of_type("NukunWan22ContinuationManifest")[0]
        save_video = self.nodes_of_type("SaveVideo")[0]
        self.assertIsNotNone(self.find_link(loop_end["id"], 2, manifest["id"], 2))
        self.assertIsNotNone(self.find_link(manifest["id"], 1, save_video["id"], 1))


if __name__ == "__main__":
    unittest.main()
