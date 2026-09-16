from pathlib import Path
import subprocess
import unittest


class ReaderNavigationTests(unittest.TestCase):
    def test_real_reader_url_state(self):
        script = Path(__file__).with_name('reader-navigation.cjs')
        result = subprocess.run(['node', str(script)], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
