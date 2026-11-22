"""ดาวน์โหลดเสียงจากลิงก์ (yt-dlp) และถอดรหัสเป็น PCM (ffmpeg)"""
import re
import subprocess

import imageio_ffmpeg
import numpy as np
from yt_dlp import YoutubeDL

from .config import SAMPLE_RATE
from .i18n import tr

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def decode(path):
    """ถอดรหัสไฟล์เสียง/วิดีโอเป็น int16 stereo ที่ SAMPLE_RATE รูปร่าง (N, 2)"""
    cmd = [FFMPEG, "-v", "error", "-i", str(path), "-vn", "-f", "s16le",
           "-ac", "2", "-ar", str(SAMPLE_RATE), "-"]
    proc = subprocess.run(cmd, capture_output=True,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if proc.returncode != 0:
        lines = [l for l in proc.stderr.decode("utf-8", "ignore").splitlines() if l.strip()]
        raise RuntimeError("ffmpeg: " + (lines[-1][:100] if lines else tr("err_decode")))
    data = np.frombuffer(proc.stdout, np.int16)
    data = data[: len(data) // 2 * 2].reshape(-1, 2)
    if len(data) < 2:
        raise RuntimeError(tr("err_no_audio"))
    return data


def download(url, out_dir):
    """โหลดเสียงจากลิงก์ คืน (ชื่อ, path ไฟล์)"""
    opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
        "socket_timeout": 20,
        "outtmpl": str(out_dir) + "/%(id)s.%(ext)s",
        "ffmpeg_location": FFMPEG,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        reqs = info.get("requested_downloads") or []
        path = reqs[0].get("filepath") if reqs else None
        path = path or ydl.prepare_filename(info)
        return (info.get("title") or info.get("id") or tr("link_audio_title")), path


def explain_error(e):
    """แปลง error ให้อ่านง่ายสำหรับแสดงในแถบสถานะ"""
    msg = re.sub(r"\x1b\[[0-9;]*m", "", str(e)).strip()
    low = msg.lower()
    if "unsupported url" in low:
        return tr("err_unsupported")
    if any(k in low for k in ("private", "log in", "login", "sign in", "members-only",
                              "confirm your age", "age-restricted")):
        return tr("err_private")
    if any(k in low for k in ("http error 403", "http error 429", "unable to extract",
                              "unable to download", "no video formats")):
        return tr("err_extract")
    if "urlopen error" in low or "getaddrinfo" in low or "timed out" in low:
        return tr("err_network")
    return msg[:100] or e.__class__.__name__
