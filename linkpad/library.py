"""คลังเสียง: เก็บรายชื่อเพลง (ชื่อ, ไฟล์, ลิงก์ต้นทาง) เป็นไฟล์ JSON"""
import json
import os
from pathlib import Path


def clean_title(title, fallback="(ไม่มีชื่อ)", limit=120):
    """ล้างชื่อ: ตัดขึ้นบรรทัดใหม่/อักขระแปลก และอีโมจิ (Tk บางเครื่องแสดงไม่ได้)"""
    text = "".join(c if (c.isprintable() or c.isspace()) else " "
                   for c in str(title) if ord(c) <= 0xFFFF)
    text = " ".join(text.split())
    return text[:limit].rstrip() if text else fallback


def is_inside(path, folder):
    """path อยู่ในโฟลเดอร์ folder หรือไม่"""
    try:
        a, b = os.path.abspath(path), os.path.abspath(folder)
        return os.path.commonpath([a, b]) == b and a != b
    except ValueError:
        return False


class Library:
    def __init__(self, path):
        self.path = Path(path)
        self.items = []
        self.load()

    def __len__(self):
        return len(self.items)

    def load(self):
        self.items = []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if not isinstance(raw, list):
            return
        for it in raw:
            if isinstance(it, dict) and it.get("file"):
                self.items.append({
                    "title": clean_title(it.get("title") or Path(str(it["file"])).stem),
                    "file": str(it["file"]),
                    "src": it.get("src"),
                })

    def save(self):
        tmp = self.path.with_suffix(".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp, self.path)
            return True
        except OSError:
            return False

    def index_of(self, item):
        """หาตำแหน่งของ item ตัวเดิม (เทียบแบบ identity) หรือ None ถ้าถูกลบไปแล้ว"""
        for i, it in enumerate(self.items):
            if it is item:
                return i
        return None

    def add(self, title, file, src=None):
        """เพิ่มเพลง คืนตำแหน่ง (ถ้ามีไฟล์เดียวกันอยู่แล้วจะไม่เพิ่มซ้ำ)"""
        file = str(file)
        for i, it in enumerate(self.items):
            if os.path.normcase(it["file"]) == os.path.normcase(file):
                return i
        self.items.append({"title": clean_title(title or Path(file).stem), "file": file, "src": src})
        self.save()
        return len(self.items) - 1

    def rename(self, i, new_title):
        title = clean_title(new_title, fallback="")
        if not title or not (0 <= i < len(self.items)):
            return False
        self.items[i]["title"] = title
        self.save()
        return True

    def remove(self, i):
        """ลบเพลงออกจากคลัง คืน item ที่ถูกลบ (หรือ None)"""
        if not (0 <= i < len(self.items)):
            return None
        item = self.items.pop(i)
        self.save()
        return item
