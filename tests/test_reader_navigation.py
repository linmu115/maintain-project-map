from pathlib import Path
import subprocess
import unittest


class ReaderNavigationTests(unittest.TestCase):
    def test_archival_scope_and_review_notices(self):
        script = Path(__file__).with_name('reader-archive.cjs')
        result = subprocess.run(['node', str(script)], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_history_occurrences_are_independent(self):
        script = Path(__file__).with_name('reader-history-navigation.cjs')
        result = subprocess.run(['node', str(script)], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_real_reader_url_state(self):
        script = Path(__file__).with_name('reader-navigation.cjs')
        result = subprocess.run(['node', str(script)], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
