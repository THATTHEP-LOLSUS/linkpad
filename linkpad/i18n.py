"""ระบบสองภาษา (ไทย / English) — ตารางข้อความทั้งหมดของ UI อยู่ที่นี่

Two-language string table. To add a language: add its code to LANGS / LANG_NAMES
and give every entry in STRINGS a value for it (tests/test_i18n.py checks this).
"""
from string import Formatter

LANGS = ("th", "en")
LANG_NAMES = {"th": "ไทย", "en": "English"}
DEFAULT_LANG = "th"

_lang = DEFAULT_LANG

STRINGS = {
    # ---------------------------------------------------------- หน้าต่าง / หัวโปรแกรม
    "window_title": {
        "th": "{app} v{ver} — เล่นเสียงจากลิงก์เข้าไมค์เสมือน",
        "en": "{app} v{ver} — play audio from links into a virtual mic",
    },
    "help_btn": {"th": "? วิธีตั้งค่า", "en": "? Setup guide"},
    "tagline": {
        "th": "ซาวด์บอร์ดจากลิงก์ — ส่งเสียงจากลิงก์หรือไฟล์เข้าไมค์เสมือน "
              "เพื่อเล่นให้เพื่อนได้ยินในเกมและ Discord",
        "en": "A soundboard that plays links — sends audio from a link or file into a "
              "virtual mic so friends hear it in games and Discord",
    },
    "supports": {
        "th": "รองรับ:  YouTube  •  TikTok  •  ไฟล์ในเครื่อง (mp3 wav ogg m4a flac)  "
              "•  เว็บอื่นที่ yt-dlp รองรับอาจใช้ได้",
        "en": "Supports:  YouTube  •  TikTok  •  local files (mp3 wav ogg m4a flac)  "
              "•  other sites supported by yt-dlp may work",
    },

    # ---------------------------------------------------------- อุปกรณ์เสียง
    "dev_out": {"th": "ส่งเสียงเข้า (Virtual Mic)", "en": "Send to (Virtual Mic)"},
    "dev_mon": {"th": "ฟังเองที่ (หูฟัง/ลำโพง)", "en": "Monitor (headphones/speakers)"},
    "off": {"th": "ปิด", "en": "Off"},

    # ---------------------------------------------------------- เพิ่มลิงก์ / ไฟล์
    "url_placeholder": {
        "th": "วางลิงก์ YouTube / TikTok ที่นี่ แล้วกด Enter…",
        "en": "Paste a YouTube / TikTok link here and press Enter…",
    },
    "btn_add_play": {"th": "เพิ่ม + เล่น", "en": "Add + play"},
    "btn_add_file": {"th": "เพิ่มไฟล์", "en": "Add file"},
    "ft_media": {"th": "ไฟล์เสียง/วิดีโอ", "en": "Audio / video files"},
    "ft_all": {"th": "ทุกไฟล์", "en": "All files"},

    # ---------------------------------------------------------- แผงควบคุม
    "no_track": {"th": "ยังไม่ได้เลือกเพลง", "en": "No track selected"},
    "time_fmt": {"th": "เล่นถึง {pos} / {dur}", "en": "{pos} / {dur}"},
    "btn_play": {"th": "▶ เล่น", "en": "▶ Play"},
    "btn_pause": {"th": "❚❚ พัก", "en": "❚❚ Pause"},
    "btn_stop": {"th": "■ หยุด", "en": "■ Stop"},
    "play_mode": {"th": "โหมดการเล่น", "en": "Play mode"},
    "mode_once": {"th": "เล่นครั้งเดียว", "en": "Play once"},
    "mode_repeat_one": {"th": "วนเพลงนี้", "en": "Repeat track"},
    "mode_all": {"th": "เล่นต่อทั้งคลัง", "en": "Play library"},
    "mode_repeat_all": {"th": "วนทั้งคลัง", "en": "Repeat library"},
    "vol": {"th": "ระดับเสียง {v}%", "en": "Volume {v}%"},
    "spd": {"th": "ความเร็ว {v}x", "en": "Speed {v}x"},
    "bass": {"th": "เบส {v}%", "en": "Bass {v}%"},
    "loud": {"th": "โหมดลั่นสุด (Earrape)", "en": "Earrape mode"},
    "reset_fx": {"th": "รีเซ็ตเสียง", "en": "Reset audio"},
    "hotkeys": {
        "th": "ปุ่มลัด: F7 ก่อนหน้า • F8 เล่น/พัก • F9 หยุด • F10 ถัดไป",
        "en": "Hotkeys: F7 previous • F8 play/pause • F9 stop • F10 next",
    },

    # ---------------------------------------------------------- คลังเสียง
    "library_label": {
        "th": "คลังเสียง   (คลิกชื่อ = เล่น • ✎ หรือคลิกขวา = เปลี่ยนชื่อ • ✕ = ลบ)",
        "en": "Library   (click a title = play • ✎ or right-click = rename • ✕ = delete)",
    },
    "empty_library": {
        "th": "ยังไม่มีเสียงในคลัง — วางลิงก์ด้านบนแล้วกด “เพิ่ม + เล่น”",
        "en": "The library is empty — paste a link above and press “Add + play”",
    },
    "rename_title": {"th": "เปลี่ยนชื่อเพลง", "en": "Rename track"},
    "rename_new": {"th": "ชื่อใหม่", "en": "New name"},
    "save": {"th": "บันทึก", "en": "Save"},
    "cancel": {"th": "ยกเลิก", "en": "Cancel"},

    # ---------------------------------------------------------- แถบสถานะ
    "ready": {
        "th": "พร้อมใช้งาน — วางลิงก์แล้วกด “เพิ่ม + เล่น”",
        "en": "Ready — paste a link and press “Add + play”",
    },
    "no_cable": {
        "th": "ไม่พบ VB-CABLE — ติดตั้งก่อนเพื่อส่งเสียงเข้า Discord/เกม (กดปุ่ม ? วิธีตั้งค่า)",
        "en": "VB-CABLE not found — install it to send sound into Discord/games (press ? Setup guide)",
    },
    "dev_none": {"th": "ไม่พบอุปกรณ์เสียงออก", "en": "No audio output device found"},
    "dev_ok": {"th": "ตั้งค่าอุปกรณ์แล้ว", "en": "Devices applied"},
    "dev_fail": {"th": "เปิดอุปกรณ์ไม่ได้: {err}", "en": "Could not open device: {err}"},
    "renamed": {"th": "เปลี่ยนชื่อแล้ว", "en": "Renamed"},
    "rename_empty": {"th": "ชื่อว่างเปล่า — ไม่ได้เปลี่ยน", "en": "Name is empty — not changed"},
    "bad_link": {
        "th": "ลิงก์ไม่ถูกต้อง — วางลิงก์ YouTube หรือ TikTok เต็มๆ",
        "en": "Invalid link — paste the full YouTube or TikTok link",
    },
    "downloading": {"th": "กำลังดาวน์โหลดเสียง…", "en": "Downloading audio…"},
    "dl_fail": {"th": "โหลดไม่ได้: {msg}", "en": "Download failed: {msg}"},
    "loading": {"th": "กำลังโหลด: {title}", "en": "Loading: {title}"},
    "redownload": {
        "th": "ไฟล์หายจากแคช กำลังดาวน์โหลดใหม่…",
        "en": "File missing from cache, downloading again…",
    },
    "play_fail": {"th": "เล่นไม่ได้: {msg}", "en": "Cannot play: {msg}"},
    "file_gone": {"th": "ไม่พบไฟล์เสียงนี้แล้ว", "en": "This audio file no longer exists"},
    "now_playing": {"th": "กำลังเล่น — ความยาว {dur}", "en": "Playing — length {dur}"},
    "stopped": {"th": "หยุดแล้ว", "en": "Stopped"},
    "finished": {"th": "เล่นจบแล้ว", "en": "Finished"},

    # ---------------------------------------------------------- ข้อความ error (media.py)
    "err_unsupported": {"th": "ลิงก์นี้ไม่รองรับ", "en": "This link is not supported"},
    "err_private": {
        "th": "วิดีโอเป็นส่วนตัว/ต้องล็อกอิน โหลดไม่ได้",
        "en": "The video is private or requires login — cannot download",
    },
    "err_extract": {
        "th": "ดึงเสียงไม่ได้ ลองอัปเดต yt-dlp: python -m pip install -U yt-dlp",
        "en": "Could not extract audio. Try updating yt-dlp: python -m pip install -U yt-dlp",
    },
    "err_network": {"th": "เชื่อมต่ออินเทอร์เน็ตไม่ได้", "en": "Cannot connect to the internet"},
    "err_decode": {"th": "ถอดรหัสไม่สำเร็จ", "en": "decoding failed"},
    "err_no_audio": {"th": "ไม่พบเสียงในไฟล์นี้", "en": "No audio found in this file"},
    "link_audio_title": {"th": "เสียงจากลิงก์", "en": "Audio from link"},

    # ---------------------------------------------------------- หน้าต่างวิธีตั้งค่า
    "help_title": {"th": "LinkPad — วิธีตั้งค่า", "en": "LinkPad — Setup guide"},
    "help_text": {
        "th": """LinkPad คืออะไร
ซาวด์บอร์ดที่เล่นเสียงจากลิงก์ ส่งเสียงจากลิงก์หรือไฟล์เข้า "ไมค์เสมือน" เพื่อให้เพื่อนในเกมและ Discord ได้ยิน

รองรับ
• ลิงก์ YouTube
• ลิงก์ TikTok (ทั้งลิงก์เต็มและลิงก์สั้น vm.tiktok.com)
• ไฟล์ในเครื่อง: mp3 wav ogg m4a flac aac opus webm mp4 mkv
• เว็บอื่นที่ yt-dlp รองรับ เช่น SoundCloud อาจใช้ได้ (ไม่รับประกัน)

ตั้งค่าครั้งแรก
1. ติดตั้ง VB-CABLE (ฟรี) จาก vb-audio.com/Cable แล้วรีสตาร์ทเครื่อง
2. ในโปรแกรมนี้
   • ส่งเสียงเข้า = CABLE Input
   • ฟังเองที่ = หูฟังหรือลำโพงของคุณ (เลือก "ปิด" ถ้าไม่อยากได้ยินเอง)
3. ใน Discord หรือเกม ตั้ง Input Device (ไมค์) = CABLE Output
4. ใน Discord ปิด Noise Suppression, Echo Cancellation, Automatic Gain Control
   และตั้ง Input Sensitivity ให้ไว หรือใช้ Push to Talk
   (ถ้าอยากพูดพร้อมเล่นเสียง ให้ใช้ VoiceMeeter รวมไมค์จริงกับ CABLE)

วิธีใช้
• วางลิงก์ แล้วกด Enter หรือ "เพิ่ม + เล่น" เสียงจะถูกเก็บในคลัง เล่นซ้ำได้โดยไม่ต้องโหลดใหม่
• คลิกชื่อเพลงในคลังเพื่อเล่น  ✎ หรือคลิกขวาที่ชื่อ = เปลี่ยนชื่อ  ✕ = ลบ
• โหมดการเล่น: เล่นครั้งเดียว / วนเพลงนี้ / เล่นต่อทั้งคลัง / วนทั้งคลัง
• เลื่อนแถบเวลาเพื่อข้ามไปตำแหน่งที่ต้องการ
• ความเร็วเปลี่ยนแบบเทป (เร็วขึ้น = เสียงสูงขึ้น)
• เปลี่ยนภาษาโปรแกรมได้ที่ปุ่ม ไทย / English มุมขวาบน

ปุ่มลัด (ใช้ได้แม้อยู่ในเกม)
F7 ก่อนหน้า • F8 เล่น/พัก • F9 หยุด • F10 ถัดไป
""",
        "en": """What is LinkPad?
A soundboard that plays audio from links. It sends sound from a link or a file into a "virtual microphone" so your friends in games and Discord can hear it.

Supported
• YouTube links
• TikTok links (full links and vm.tiktok.com short links)
• Local files: mp3 wav ogg m4a flac aac opus webm mp4 mkv
• Other sites supported by yt-dlp, e.g. SoundCloud, may work (not guaranteed)

First-time setup
1. Install VB-CABLE (free) from vb-audio.com/Cable and restart your PC
2. In this app
   • Send to = CABLE Input
   • Monitor = your headphones or speakers (choose "Off" if you don't want to hear it yourself)
3. In Discord or your game, set the Input Device (microphone) = CABLE Output
4. In Discord turn off Noise Suppression, Echo Cancellation and Automatic Gain Control,
   and set Input Sensitivity low, or use Push to Talk
   (to talk and play sounds at the same time, use VoiceMeeter to mix your real mic with CABLE)

How to use
• Paste a link and press Enter or "Add + play". The audio is saved to the library and can be replayed without downloading again
• Click a title in the library to play  ✎ or right-click a title = rename  ✕ = delete
• Play modes: play once / repeat track / play library / repeat library
• Drag the time bar to jump to any position
• Speed works like a tape (faster = higher pitch)
• Switch the app language with the Thai / English button at the top right

Hotkeys (work even while you are in a game)
F7 previous • F8 play/pause • F9 stop • F10 next
""",
    },
}


def set_lang(code):
    """ตั้งภาษาปัจจุบัน (รหัสที่ไม่รู้จักจะถูกเมินและคงภาษาเดิม)"""
    global _lang
    if code in LANGS:
        _lang = code
    return _lang


def get_lang():
    return _lang


def tr(key, **kw):
    """คืนข้อความของ key ตามภาษาปัจจุบัน (เติมค่าด้วย str.format ถ้าส่ง kw มา)"""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(_lang) or entry[DEFAULT_LANG]
    return text.format(**kw) if kw else text


def placeholders(text):
    """ชื่อช่อง {x} ที่อยู่ในข้อความ (ใช้ในเทสต์เทียบสองภาษา)"""
    return {name for _, name, _, _ in Formatter().parse(text) if name}
