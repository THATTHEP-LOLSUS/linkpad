import json
import tempfile
import unittest
from pathlib import Path

from linkpad.library import Library, clean_title, is_inside


class CleanTitle(unittest.TestCase):
    def test_strips_newlines_and_extra_spaces(self):
        self.assertEqual(clean_title("  hello \n  #tag   world "), "hello #tag world")

    def test_removes_emoji_outside_bmp(self):
        self.assertEqual(clean_title("funny \U0001F602 clip"), "funny clip")

    def test_fallback_and_limit(self):
        self.assertEqual(clean_title("   "), "(ไม่มีชื่อ)")
        self.assertEqual(clean_title("", fallback=""), "")
        self.assertEqual(len(clean_title("x" * 500)), 120)


class IsInside(unittest.TestCase):
    def test_inside_and_outside(self):
        base = tempfile.gettempdir()
        self.assertTrue(is_inside(str(Path(base) / "a" / "b.mp3"), base))
        self.assertFalse(is_inside(str(Path(base).parent / "x.mp3"), base))
        self.assertFalse(is_inside(base, base))


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "library.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_persists_and_reloads(self):
        lib = Library(self.path)
        i = lib.add("Song", "/x/song.webm", "https://example.com/v")
        self.assertEqual(i, 0)
        again = Library(self.path)
        self.assertEqual(again.items[0]["title"], "Song")
        self.assertEqual(again.items[0]["src"], "https://example.com/v")

    def test_no_duplicate_files(self):
        lib = Library(self.path)
        a = lib.add("A", "/x/a.mp3")
        b = lib.add("A again", "/x/a.mp3")
        self.assertEqual(a, b)
        self.assertEqual(len(lib), 1)

    def test_rename(self):
        lib = Library(self.path)
        lib.add("Old", "/x/a.mp3")
        self.assertTrue(lib.rename(0, "  New \n name "))
        self.assertEqual(lib.items[0]["title"], "New name")
        self.assertEqual(Library(self.path).items[0]["title"], "New name")

    def test_rename_rejects_empty_and_bad_index(self):
        lib = Library(self.path)
        lib.add("Keep", "/x/a.mp3")
        self.assertFalse(lib.rename(0, "   "))
        self.assertFalse(lib.rename(5, "x"))
        self.assertEqual(lib.items[0]["title"], "Keep")

    def test_remove(self):
        lib = Library(self.path)
        lib.add("A", "/x/a.mp3")
        lib.add("B", "/x/b.mp3")
        removed = lib.remove(0)
        self.assertEqual(removed["title"], "A")
        self.assertEqual([i["title"] for i in lib.items], ["B"])
        self.assertIsNone(lib.remove(9))

    def test_index_of_uses_identity(self):
        lib = Library(self.path)
        lib.add("A", "/x/a.mp3")
        lib.add("B", "/x/b.mp3")
        item = lib.items[1]
        lib.remove(0)
        self.assertEqual(lib.index_of(item), 0)
        lib.remove(0)
        self.assertIsNone(lib.index_of(item))

    def test_loads_old_format_and_ignores_garbage(self):
        self.path.write_text(json.dumps([{"title": "Old", "file": "/x/o.mp3"}, "junk", {"title": "no file"}]),
                             encoding="utf-8")
        lib = Library(self.path)
        self.assertEqual(len(lib), 1)
        self.assertIsNone(lib.items[0]["src"])

    def test_corrupt_json_gives_empty_library(self):
        self.path.write_text("{not json", encoding="utf-8")
        self.assertEqual(len(Library(self.path)), 0)


if __name__ == "__main__":
    unittest.main()
