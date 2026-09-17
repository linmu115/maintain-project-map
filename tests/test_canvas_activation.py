"""Selection-gate unit checks using the shipped script and a small DOM double.

This checks event ownership and state transitions, not browser layout/gestures.
"""
from pathlib import Path
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "maintain-project-map" / "scripts"))
from archify_adapter import find_node


class CanvasActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = find_node()
        cls.script = ROOT / "maintain-project-map" / "assets" / "canvas-interaction.js"
        cls.runner = Path(__file__).with_name("canvas-activation.cjs")

    def check(self, scenario):
        result = subprocess.run(
            [self.node, str(self.runner), str(self.script), scenario],
            capture_output=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["passed"])

    def test_default_keeps_wheel_with_document(self):
        self.check("default")

    def test_first_click_selects_without_forwarding_click_or_reloading(self):
        self.check("select")

    def test_outside_pointer_and_focus_restore_document(self):
        self.check("outside")

    def test_only_one_of_multiple_diagrams_is_selected(self):
        self.check("multiple")

    def test_explicit_exit_and_parent_escape_are_keyboard_accessible(self):
        self.check("exit")

    def test_reset_releases_removed_frames_without_duplicate_listeners(self):
        self.check("reset")


if __name__ == "__main__":
    unittest.main()
