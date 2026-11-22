"""ค่าคงที่และตำแหน่งเก็บข้อมูลของ LinkPad"""
import json
import os
from pathlib import Path

APP_NAME = "LinkPad"
SAMPLE_RATE = 48000
AUDIO_EXTS = ("mp3", "wav", "ogg", "m4a", "flac", "aac", "opus", "webm", "mp4", "mkv")
ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def data_dir() -> Path:
    """โฟลเดอร์เก็บคลังเสียงและแคช (ตั้งเองได้ด้วยตัวแปรแวดล้อม LINKPAD_HOME)"""
    override = os.environ.get("LINKPAD_HOME")
    if override:
        base = Path(override)
    else:
        root = os.environ.get("APPDATA") or str(Path.home() / ".config")
        base = Path(root) / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def cache_dir() -> Path:
    d = data_dir() / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def library_path() -> Path:
    return data_dir() / "library.json"


def asset_path(name) -> Path:
    """ไฟล์ในโฟลเดอร์ assets (โลโก้ ไอคอน)"""
    return ASSETS_DIR / name


def settings_path() -> Path:
    return data_dir() / "settings.json"


def load_settings() -> dict:
    """อ่านการตั้งค่าของผู้ใช้ (เช่น ภาษา) ถ้าไฟล์ไม่มีหรือเสียจะคืน dict ว่าง"""
    try:
        raw = json.loads(settings_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return raw if isinstance(raw, dict) else {}


def save_settings(values: dict) -> None:
    settings_path().write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding="utf-8")
