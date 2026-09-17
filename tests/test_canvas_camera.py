"""Execute the shipped camera closure against a small, deterministic DOM double.

These are camera/event unit checks, not browser layout or visual verification.
The JavaScript under test is extracted from the real downstream export; the
double supplies element dimensions and SVG geometry, never a replacement camera.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "maintain-project-map" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from archify_adapter import VENDOR, _style_export, find_node


def camera_script(page: str) -> str:
    start = page.index("    Archify.view = (function () {")
    end = page.index("    /* ============================================================\n       Semantic Radar", start)
    return page[start:end]


class CanvasCameraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = find_node()
        cls.runner = Path(__file__).with_name("canvas-camera.cjs")
        native = (VENDOR / "assets/template.html").read_text(encoding="utf-8")
        cls.payload = json.dumps({
            "native": camera_script(native),
            "adapted": camera_script(_style_export(native)),
        }, ensure_ascii=False)

    def run_scenario(self, name: str):
        result = subprocess.run(
            [self.node, str(self.runner), name], input=self.payload,
            capture_output=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["scenario"], name)
        self.assertTrue(receipt["passed"])

    def test_initial_state_uses_fitted_svg(self):
        self.run_scenario("fit")

    def test_fit_includes_outlying_edges_and_canvas_has_only_stage_clipping(self):
        self.run_scenario("bounds")

    def test_wheel_is_continuous_below_one_and_anchored_to_pointer(self):
        self.run_scenario("wheel")

    def test_control_panel_wheel_is_not_consumed(self):
        self.run_scenario("controls")

    def test_drag_works_at_and_below_one_without_stealing_node_clicks(self):
        self.run_scenario("drag")

    def test_zoom_limits_and_reset_share_native_state(self):
        self.run_scenario("limits")

    def test_canvas_resize_refits_overview_and_retains_manual_camera(self):
        self.run_scenario("resize")

    def test_mobile_canvas_uses_semantic_camera_instead_of_horizontal_scroll(self):
        self.run_scenario("mobile")

    def test_noncanvas_camera_retains_native_interaction_contract(self):
        self.run_scenario("native")


if __name__ == "__main__":
    unittest.main()
