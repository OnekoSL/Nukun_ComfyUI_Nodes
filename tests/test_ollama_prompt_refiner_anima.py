import sys
import unittest
from pathlib import Path


COMFY_ROOT = Path(__file__).resolve().parents[3]
if str(COMFY_ROOT) not in sys.path:
    sys.path.insert(0, str(COMFY_ROOT))

from custom_nodes.Nukun_ComfyUI_Nodes.nodes import ollama_prompt_refiner as refiner


def anima_result(foreground, background, word_salad="archivist crystal workshop rain", style_anchor=""):
    return refiner._postprocess_result(
        {
            "base_prompt": "masterpiece, best quality, score_9, score_8_up, score_7_up",
            "foreground_prompt": foreground,
            "background_prompt": background,
            "negative": "bad anatomy",
            "report": "Kept the archivist and workshop concept.",
        },
        "anima",
        word_salad,
        style_anchor,
        430,
    )


class AnimaNaturalPromptTests(unittest.TestCase):
    def test_natural_prompt_starts_with_quality_tags_and_fits_target_length(self):
        result = anima_result(
            "A silver-haired archivist opens a sealed book beside a quiet brass machine. "
            "She watches a blue crystal with careful attention. "
            "Her dark coat has silver seams and worn leather straps. "
            "One hand protects the crystal while the other steadies the book. "
            "Small tools and glass bottles surround her working space. "
            "Her balanced posture shows patience and controlled tension.",
            "Three glass bottles stand beside a copper lamp. "
            "Tall windows reveal a rainy city beyond the workshop. "
            "Warm light creates soft shadows across the wooden room. "
            "Her cautious smile makes the quiet scene feel hopeful and mysterious.",
        )
        positive, _, _, base, foreground, background = result
        self.assertTrue(base.startswith("masterpiece, best quality, score_9, score_8_up, score_7_up"))
        self.assertTrue(positive.startswith(base + "\n\n"))
        self.assertGreaterEqual(refiner._word_count(positive), refiner.ANIMA_POSITIVE_WORD_RANGE[0])
        self.assertLessEqual(refiner._word_count(positive), refiner.ANIMA_POSITIVE_WORD_RANGE[1])
        self.assertIn("A silver-haired archivist opens a sealed book", foreground)
        self.assertIn("Three glass bottles stand beside a copper lamp", background)
        self.assertTrue(background.endswith("Her cautious smile makes the quiet scene feel hopeful and mysterious."))
        self.assertLess(positive.index("A silver-haired archivist"), positive.index("Three glass bottles"))

    def test_short_answer_is_extended_with_simple_prose(self):
        positive = anima_result(
            "A mage holds a crystal. She studies its light.",
            "A workshop surrounds her. The room feels calm.",
        )[0]
        self.assertGreaterEqual(refiner._word_count(positive), refiner.ANIMA_POSITIVE_WORD_RANGE[0])
        self.assertGreaterEqual(len(refiner._anima_sentences(positive)), 10)

    def test_long_answer_is_trimmed_at_sentence_boundaries(self):
        foreground = " ".join(
            f"The heroine examines artifact {index} while careful blue light reveals its engraved metal surface."
            for index in range(20)
        )
        background = " ".join(
            f"Workshop shelf {index} holds glass tools beneath a warm lamp and drifting silver dust."
            for index in range(14)
        ) + " Her steady expression gives the crowded room a calm and hopeful mood."
        positive, _, _, _, foreground_result, background_result = anima_result(foreground, background)
        self.assertLessEqual(refiner._word_count(positive), refiner.ANIMA_POSITIVE_WORD_RANGE[1])
        self.assertTrue(foreground_result.endswith("."))
        self.assertTrue(background_result.endswith("Her steady expression gives the crowded room a calm and hopeful mood."))

    def test_safety_tags_are_source_controlled(self):
        safe_base = anima_result("A mage studies a crystal. She turns a page.", "A lamp lights the room. The mood feels calm.")[3]
        nsfw_base = anima_result(
            "A mage studies a crystal. She turns a page.",
            "A lamp lights the room. The mood feels tense.",
            style_anchor="nsfw",
        )[3]
        self.assertNotIn("nsfw", safe_base)
        self.assertIn("nsfw", nsfw_base)

    def test_style_anchor_controls_anima_base_prefix(self):
        anchor = "masterpiece, best quality, anime illustration, cinematic lighting, clean linework, detailed materials"
        positive, _, _, base, _, _ = anima_result(
            "A red-haired woman stands beside a tiled wall.",
            "Cool room light falls across simple wall tiles. The mood feels tense.",
            word_salad="red hair tiled wall nsfw explicit",
            style_anchor=anchor,
        )
        self.assertTrue(base.startswith(anchor))
        self.assertIn("nsfw", base)
        self.assertIn("explicit", base)
        self.assertNotIn("score_9", base)
        self.assertEqual(base.count("masterpiece"), 1)
        self.assertEqual(base.count("best quality"), 1)
        self.assertEqual(base.count("clean linework"), 1)
        self.assertTrue(positive.startswith(base + "\n\n"))

    def test_anima_fallback_does_not_turn_meta_tags_into_subject(self):
        positive = anima_result(
            "",
            "",
            word_salad="year 1988 newest nsfw explicit young woman long red hair blue bandana tiled wall ropes",
            style_anchor="masterpiece, best quality, anime illustration, clean linework",
        )[0]
        self.assertIn("built around young, woman, long, and red", positive)
        self.assertNotIn("built around year", positive)
        self.assertNotIn("year, newest, nsfw", positive)
        self.assertNotIn("nsfw, and explicit, with a clear", positive)

    def test_other_profile_instructions_remain_profile_specific(self):
        self.assertIn("Write tag tokens only", refiner._target_profile_instructions("pony_v6", 430))
        self.assertIn("360 to 440 words", refiner._target_profile_instructions("z_image", 430))
        self.assertIn("style_cluster_430", refiner._target_profile_instructions("pony_v7", 430))


if __name__ == "__main__":
    unittest.main()
