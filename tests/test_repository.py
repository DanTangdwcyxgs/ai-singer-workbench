import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryTests(unittest.TestCase):
    def test_readme_relative_markdown_links_exist(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        targets = re.findall(r"\[[^]]+\]\(([^)]+)\)", readme)
        missing = []
        for target in targets:
            if "://" in target or target.startswith("#"):
                continue
            if not (ROOT / target).is_file():
                missing.append(target)
        self.assertEqual(missing, [])

    def test_required_entrypoints_exist(self):
        required = [
            "workbench/app.py",
            "workbench/train_voice.py",
            "workbench/separate_vocals.py",
            "scripts/configure-windows.ps1",
            "scripts/verify-windows.ps1",
            "启动 AI歌手工作台.cmd",
        ]
        self.assertEqual([item for item in required if not (ROOT / item).is_file()], [])


if __name__ == "__main__":
    unittest.main()
