"""ทดสอบตารางข้อความสองภาษา (ไม่ต้องมี GUI)"""
import re
import unittest
from pathlib import Path

from linkpad import i18n
from linkpad.i18n import LANGS, STRINGS, placeholders, set_lang, tr

SRC = Path(__file__).resolve().parent.parent / "linkpad"


class Strings(unittest.TestCase):
    def test_every_key_has_every_language(self):
        for key, entry in STRINGS.items():
            for lang in LANGS:
                self.assertTrue(entry.get(lang, "").strip(), f"{key!r} is missing {lang!r}")

    def test_placeholders_match_between_languages(self):
        for key, entry in STRINGS.items():
            fields = {lang: placeholders(entry[lang]) for lang in LANGS}
            self.assertEqual(len({frozenset(f) for f in fields.values()}), 1,
                             f"{key!r} placeholders differ: {fields}")

    def test_keys_used_in_source_exist(self):
        used = set()
        for py in SRC.glob("*.py"):
            if py.name == "i18n.py":
                continue
            used |= set(re.findall(r'\b(?:tr|say)\(\s*"([a-z_0-9]+)"', py.read_text(encoding="utf-8")))
        # คีย์ของโหมดการเล่นอยู่ในตาราง MODES ของ gui.py (import gui ตรงๆ ไม่ได้ เพราะต้องมี customtkinter)
        used |= set(re.findall(r'\("(mode_[a-z_]+)"', (SRC / "gui.py").read_text(encoding="utf-8")))
        self.assertFalse(used - set(STRINGS), f"unknown keys: {used - set(STRINGS)}")


class Switching(unittest.TestCase):
    def tearDown(self):
        set_lang(i18n.DEFAULT_LANG)

    def test_switch_and_format(self):
        set_lang("en")
        self.assertEqual(tr("vol", v=50), "Volume 50%")
        set_lang("th")
        self.assertEqual(tr("vol", v=50), "ระดับเสียง 50%")

    def test_unknown_language_is_ignored(self):
        set_lang("en")
        set_lang("xx")
        self.assertEqual(i18n.get_lang(), "en")

    def test_unknown_key_returns_key(self):
        self.assertEqual(tr("no_such_key"), "no_such_key")


if __name__ == "__main__":
    unittest.main()
