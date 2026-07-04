import sys
import unittest
from pathlib import Path

import torch


COMFY_ROOT = Path(__file__).resolve().parents[3]
CUSTOM_NODES_ROOT = COMFY_ROOT / "custom_nodes"
NUKUN_ROOT = CUSTOM_NODES_ROOT / "Nukun_ComfyUI_Nodes"

for path in (str(COMFY_ROOT), str(CUSTOM_NODES_ROOT), str(NUKUN_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from nodes.speed_sampler import (  # noqa: E402
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
    NukunSpeedSampler,
    parse_manual_sigmas,
    parse_scales,
    resolve_manual_transitions,
    validate_dwt_scales,
)


class SpeedSamplerParsingTests(unittest.TestCase):
    def test_parse_scales_accepts_strictly_increasing_scales_ending_at_one(self):
        self.assertEqual(parse_scales("0.25, 0.5, 1.0"), [0.25, 0.5, 1.0])

    def test_parse_scales_rejects_missing_full_resolution(self):
        with self.assertRaises(ValueError):
            parse_scales("0.25,0.5")

    def test_parse_scales_rejects_non_increasing_values(self):
        with self.assertRaises(ValueError):
            parse_scales("0.5,0.5,1.0")

    def test_parse_manual_sigmas_accepts_decreasing_thresholds(self):
        self.assertEqual(parse_manual_sigmas("0.8, 0.7"), [0.8, 0.7])

    def test_parse_manual_sigmas_rejects_increasing_thresholds(self):
        with self.assertRaises(ValueError):
            parse_manual_sigmas("0.7,0.8")

    def test_manual_transition_count_must_match_scale_transitions(self):
        sigmas = torch.tensor([1.0, 0.8, 0.6, 0.0])
        with self.assertRaises(ValueError):
            resolve_manual_transitions(sigmas, [0.25, 0.5, 1.0], [0.8])

    def test_dwt_requires_two_x_scale_jumps(self):
        validate_dwt_scales([0.25, 0.5, 1.0])
        with self.assertRaises(ValueError):
            validate_dwt_scales([0.5, 0.75, 1.0])


class SpeedSamplerRegistrationTests(unittest.TestCase):
    def test_speed_sampler_is_registered(self):
        self.assertIs(NODE_CLASS_MAPPINGS["NukunSpeedSampler"], NukunSpeedSampler)
        self.assertEqual(
            NODE_DISPLAY_NAME_MAPPINGS["NukunSpeedSampler"],
            "SPEED Sampler (Nukun)",
        )

    def test_speed_sampler_constructs_default_flux_sampler(self):
        NukunSpeedSampler.execute(
            "euler",
            "dct",
            "delta_optimal",
            "flux",
            "0.5,1.0",
            0.01,
            "0.85",
            203.615097,
            1.915461,
            0,
        )

    def test_speed_sampler_constructs_wan_sampler(self):
        NukunSpeedSampler.execute(
            "euler",
            "dct",
            "delta_optimal",
            "wan21",
            "0.5,1.0",
            0.01,
            "0.85",
            203.615097,
            1.915461,
            0,
        )

    def test_speed_sampler_constructs_manual_anima_sampler(self):
        NukunSpeedSampler.execute(
            "euler",
            "dct",
            "manual",
            "anima_manual",
            "0.5,0.75,1.0",
            0.01,
            "0.8,0.7",
            203.615097,
            1.915461,
            0,
        )


if __name__ == "__main__":
    unittest.main()
