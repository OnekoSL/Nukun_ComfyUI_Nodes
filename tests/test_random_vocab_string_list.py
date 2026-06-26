import importlib.util
import random
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


COMFY_ROOT = Path(__file__).resolve().parents[3]
if str(COMFY_ROOT) not in sys.path:
    sys.path.insert(0, str(COMFY_ROOT))

MODULE_PATH = COMFY_ROOT / "custom_nodes" / "Nukun_ComfyUI_Nodes" / "nodes" / "random_vocab_string_list.py"
spec = importlib.util.spec_from_file_location("random_vocab_string_list", MODULE_PATH)
vocab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vocab)


class MultiVocabShuffleBagTests(unittest.TestCase):
    def test_word_index_amount_one_covers_bag_before_repeating(self):
        words = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]
        picks = [vocab._shuffle_bag_sample(words, 1, word_index, 1)[0] for word_index in range(len(words))]

        self.assertEqual(len(picks), len(words))
        self.assertEqual(set(picks), set(words))

    def test_amount_greater_than_one_uses_non_overlapping_blocks(self):
        words = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]
        picks = []
        for word_index in range(3):
            picks.extend(vocab._shuffle_bag_sample(words, 2, word_index, 1))

        self.assertEqual(len(picks), len(words))
        self.assertEqual(set(picks), set(words))

    def test_cycle_wrap_uses_next_shuffled_bag(self):
        words = ["alpha", "beta", "gamma", "delta", "epsilon"]
        first_cycle = list(words)
        second_cycle = list(words)
        random.Random(vocab._slot_seed(0, 1)).shuffle(first_cycle)
        random.Random(vocab._slot_seed(1, 1)).shuffle(second_cycle)

        self.assertEqual(vocab._shuffle_bag_sample(words, 3, 0, 1), first_cycle[:3])
        self.assertEqual(
            vocab._shuffle_bag_sample(words, 3, 1, 1),
            first_cycle[3:] + second_cycle[:1],
        )
        self.assertNotEqual(first_cycle, second_cycle)

    def test_generate_slot_uses_word_index_as_block_cursor(self):
        with patch.object(vocab, "_load_words", return_value=["alpha", "beta", "gamma", "delta"]):
            first = vocab._generate_slot("resources/test.txt", 2, 0, 1)
            second = vocab._generate_slot("resources/test.txt", 2, 1, 1)

        words = first.split() + second.split()
        self.assertEqual(len(words), 4)
        self.assertEqual(set(words), {"alpha", "beta", "gamma", "delta"})

    def test_amount_zero_disables_slot(self):
        with patch.object(vocab, "_load_words", return_value=["alpha", "beta"]):
            self.assertEqual(vocab._generate_slot("resources/test.txt", 0, 0, 1), "")

    def test_duplicate_vocab_entries_do_not_increase_selection_weight(self):
        words = ["alpha", "beta", "alpha", "gamma", "beta", "delta"]
        deduped = vocab._dedupe_preserve_order(words)
        picks = []
        for seed in range(2):
            picks.extend(vocab._shuffle_bag_sample(words, 2, seed, 1))

        self.assertEqual(deduped, ["alpha", "beta", "gamma", "delta"])
        self.assertEqual(len(picks), len(set(picks)))
        self.assertEqual(set(picks), set(deduped))

    def test_slots_use_different_shuffle_orders(self):
        words = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]
        self.assertNotEqual(
            vocab._shuffle_bag_sample(words, 3, 0, 1),
            vocab._shuffle_bag_sample(words, 3, 0, 2),
        )

    def test_multi_node_inputs_use_word_indices_not_word_selectors(self):
        inputs = vocab.NukunVocabMultiStringList.INPUT_TYPES()["required"]

        self.assertNotIn("seed", inputs)
        for slot in range(1, vocab.MULTI_SLOT_COUNT + 1):
            self.assertIn(f"word_index_{slot}", inputs)
            self.assertEqual(inputs[f"word_index_{slot}"][1]["control_after_generate"], True)
            for word_index in range(1, 4):
                self.assertNotIn(f"word_{slot}_{word_index}", inputs)


if __name__ == "__main__":
    unittest.main()
