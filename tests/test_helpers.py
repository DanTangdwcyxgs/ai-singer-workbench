import sys
import tempfile
import unittest
from pathlib import Path


WORKBENCH = Path(__file__).resolve().parents[1] / "workbench"
sys.path.insert(0, str(WORKBENCH))

from helpers import matching_index, model_pairs, safe_name, validate_model_name


class HelperTests(unittest.TestCase):
    def test_safe_name_replaces_unsupported_characters(self):
        self.assertEqual(safe_name("My Song 你好!"), "My_Song")

    def test_safe_name_uses_fallback(self):
        self.assertEqual(safe_name("中文", "song"), "song")

    def test_model_name_validation(self):
        self.assertEqual(validate_model_name("my_voice-v2"), "my_voice-v2")
        with self.assertRaises(ValueError):
            validate_model_name("我的声音")

    def test_model_pairs_requires_model_and_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            complete = root / "complete"
            complete.mkdir()
            (complete / "complete.pth").write_bytes(b"model")
            (complete / "complete.index").write_bytes(b"index")
            incomplete = root / "incomplete"
            incomplete.mkdir()
            (incomplete / "incomplete.pth").write_bytes(b"model")
            self.assertEqual(model_pairs(root), [("complete", str(complete / "complete.pth"))])
            self.assertEqual(matching_index(complete / "complete.pth"), complete / "complete.index")


if __name__ == "__main__":
    unittest.main()
