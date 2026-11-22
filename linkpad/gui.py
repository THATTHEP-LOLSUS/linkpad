"""หน้าต่างหลักของ LinkPad (customtkinter)"""
import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

try:
    from PIL import Image          # ใช้แสดงโลโก้ (ถ้าไม่มีจะใช้ข้อความแทน)
except Exception:
    Image = None

from . import __version__
from .audio import Player, default_output_name, output_devices
from .config import (APP_NAME, AUDIO_EXTS, SAMPLE_RATE as SR, asset_path, cache_dir,
                     library_path, load_settings, save_settings)
from .i18n import DEFAULT_LANG, LANG_NAMES, LANGS, get_lang, set_lang, tr
from .library import Library, is_inside
from .media import decode, download, explain_error
from .playlist import ALL, ONCE, REPEAT_ALL, REPEAT_ONE, next_on_end, step

try:
    import keyboard          # ปุ่มลัดทั่วระบบ (ไม่จำเป็น)
except Exception:
    keyboard = None

# (คีย์ข้อความ, โหมด) เรียงตามที่แสดงบนแถบเลือกโหมด
MODES = (
    ("mode_once", ONCE),
    ("mode_repeat_one", REPEAT_ONE),
    ("mode_all", ALL),
    ("mode_repeat_all", REPEAT_ALL),
)
LANG_BY_NAME = {name: code for code, name in LANG_NAMES.items()}
LOGO_WIDTH = 130


def fmt(sec):
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def short(text, n=48):
    return text if len(text) <= n else text[: n - 1] + "…"


class RenameDialog(ctk.CTkToplevel):
    """หน้าต่างเล็กๆ สำหรับเปลี่ยนชื่อเพลง (มีชื่อเดิมให้แก้ได้เลย)"""

    def __init__(self, master, current):
        super().__init__(master)
        self.title(tr("rename_title"))
        self.geometry("440x150")
        self.resizable(False, False)
        self.result = None
        self.transient(master)
        ctk.CTkLabel(self, text=tr("rename_new"), anchor="w").pack(fill="x", padx=16, pady=(14, 2))
        self.entry = ctk.CTkEntry(self)
        self.entry.pack(fill="x", padx=16)
        self.entry.insert(0, current)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=14)
        ctk.CTkButton(row, text=tr("save"), width=100, command=self.ok).pack(side="right")
        ctk.CTkButton(row, text=tr("cancel"), width=100, fg_color="#444", hover_color="#555",
                      command=self.destroy).pack(side="right", padx=8)
        self.bind("<Return>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.destroy())
        self.after(150, self._focus)

    def _focus(self):
        try:
            self.grab_set()
            self.entry.focus()
            self.entry.select_range(0, "end")
        except Exception:
            pass

    def ok(self):
        self.result = self.entry.get()
        self.destroy()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        set_lang(load_settings().get("lang", DEFAULT_LANG))
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.set_title()
        self.geometry("640x900")
        self.minsize(580, 760)
        self.after(250, self.apply_icon)

        self.player = Player()
        self.lib = Library(library_path())
        self.q = queue.Queue()                 # งานจาก thread อื่นที่ต้องไปทำบน UI thread
        self.status = ctk.StringVar()
        self._status = ("ready", {})           # (คีย์, ค่า) ของข้อความล่าสุด เพื่อแสดงใหม่ตอนเปลี่ยนภาษา
        self.cur = None                        # ตำแหน่งเพลงที่กำลังเล่นในคลัง
        self.mode = ONCE
        self.load_token = 0
        self.help_win = None
        self.logo_img = None

        self.outs = output_devices()
        self.names = [n for n, _ in self.outs]
        self.build()
        self.say("ready")
        self.apply_devices()
        if not any("cable" in n.lower() for n in self.names):
            self.say("no_cable")
        self.refresh_lib()
        self.setup_hotkeys()
        self.after(100, self.tick)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------------------------------------------------ ชื่อหน้าต่าง / ไอคอน / สถานะ
    def set_title(self):
        self.title(tr("window_title", app=APP_NAME, ver=__version__))

    def apply_icon(self):
        try:
            if sys.platform.startswith("win"):
                self.iconbitmap(str(asset_path("icon.ico")))   # ต้องตั้งหลังเปิดหน้าต่าง ไม่งั้น customtkinter ทับ
            else:
                self._icon = tk.PhotoImage(file=str(asset_path("icon.png")))
                self.iconphoto(True, self._icon)
        except Exception:
            pass

    def say(self, key, **kw):
        """แสดงข้อความในแถบสถานะ (เก็บคีย์ไว้เพื่อแปลใหม่เมื่อเปลี่ยนภาษา)"""
        self._status = (key, kw)
        self.status.set(tr(key, **kw))

    # ------------------------------------------------------------ หน้าตา
    def load_logo(self):
        if Image is None:
            return None
        try:
            img = Image.open(asset_path("logo-on-dark.png"))
            size = (LOGO_WIDTH, round(LOGO_WIDTH * img.height / img.width))
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except Exception:
            return None

    def build(self):
        pad = dict(padx=14, pady=(8, 0))

        # --- หัวโปรแกรม: โลโก้ | ปุ่มภาษา/ช่วยเหลือ + คำอธิบาย
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=14, pady=(10, 0))
        self.logo_img = self.load_logo()
        if self.logo_img is not None:
            ctk.CTkLabel(head, image=self.logo_img, text="").pack(side="left", padx=(0, 14))
        else:
            ctk.CTkLabel(head, text="♪ LinkPad", font=ctk.CTkFont(size=28, weight="bold")
                         ).pack(side="left", padx=(0, 14))
        side = ctk.CTkFrame(head, fg_color="transparent")
        side.pack(side="left", fill="both", expand=True)
        bar = ctk.CTkFrame(side, fg_color="transparent")
        bar.pack(fill="x")
        ctk.CTkButton(bar, text=tr("help_btn"), width=100, fg_color="#333", hover_color="#444",
                      command=self.show_help).pack(side="right")
        self.seg_lang = ctk.CTkSegmentedButton(bar, values=[LANG_NAMES[c] for c in LANGS],
                                               command=self.on_language)
        self.seg_lang.set(LANG_NAMES[get_lang()])
        self.seg_lang.pack(side="right", padx=(0, 8))
        ctk.CTkLabel(side, anchor="w", justify="left", wraplength=400, text=tr("tagline")
                     ).pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(side, anchor="w", justify="left", wraplength=400, text_color="#7fb3ff",
                     text=tr("supports")).pack(fill="x", pady=(2, 0))

        # --- อุปกรณ์เสียง
        dev = ctk.CTkFrame(self)
        dev.pack(fill="x", **pad)
        dev.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(dev, text=tr("dev_out"), anchor="w").grid(
            row=0, column=0, sticky="w", padx=10, pady=(8, 0))
        ctk.CTkLabel(dev, text=tr("dev_mon"), anchor="w").grid(
            row=0, column=1, sticky="w", padx=10, pady=(8, 0))
        default_out = next((n for n in self.names if "cable input" in n.lower() or "voicemeeter" in n.lower()),
                           self.names[0] if self.names else "")
        self.cb_out = ctk.CTkComboBox(dev, values=self.names, command=lambda _: self.apply_devices())
        self.cb_out.set(default_out)
        self.cb_out.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 10))
        self.off_label = tr("off")
        dflt = default_output_name() or ""
        mon = next((n for n in self.names if dflt and (n == dflt or dflt in n or n in dflt)), self.off_label)
        self.cb_mon = ctk.CTkComboBox(dev, values=[self.off_label] + self.names,
                                      command=lambda _: self.apply_devices())
        self.cb_mon.set(mon)
        self.cb_mon.grid(row=1, column=1, sticky="ew", padx=10, pady=(2, 10))

        # --- เพิ่มลิงก์ / ไฟล์
        add = ctk.CTkFrame(self)
        add.pack(fill="x", **pad)
        self.ent_url = ctk.CTkEntry(add, placeholder_text=tr("url_placeholder"))
        self.ent_url.pack(side="left", fill="x", expand=True, padx=(10, 6), pady=10)
        self.ent_url.bind("<Return>", lambda e: self.add_url())
        ctk.CTkButton(add, text=tr("btn_add_play"), width=96, command=self.add_url).pack(side="left", padx=2)
        ctk.CTkButton(add, text=tr("btn_add_file"), width=84, fg_color="#444", hover_color="#555",
                      command=self.add_file).pack(side="left", padx=(2, 10))

        # --- แถบสถานะ (ล่างสุด) → แผงควบคุม → คลังเสียง (ยืดหดตามพื้นที่ที่เหลือ)
        ctk.CTkLabel(self, textvariable=self.status, anchor="w", justify="left", wraplength=600,
                     text_color="gray").pack(side="bottom", fill="x", padx=14, pady=8)

        ctl = ctk.CTkFrame(self)
        ctl.pack(side="bottom", fill="x", **pad)

        self.lbl_now = ctk.CTkLabel(ctl, text=tr("no_track"), anchor="w",
                                    font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_now.pack(fill="x", padx=12, pady=(10, 0))
        self.lbl_time = ctk.CTkLabel(ctl, text=tr("time_fmt", pos="0:00", dur="0:00"), anchor="w",
                                     font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_time.pack(fill="x", padx=12, pady=(2, 0))
        self.sl_pos = ctk.CTkSlider(ctl, from_=0, to=1, command=self.on_seek)
        self.sl_pos.set(0)
        self.sl_pos.pack(fill="x", padx=12, pady=8)

        row = ctk.CTkFrame(ctl, fg_color="transparent")
        row.pack(pady=(0, 6))
        ctk.CTkButton(row, text="◀◀", width=56, fg_color="#444", hover_color="#555",
                      command=self.prev_track).pack(side="left", padx=4)
        self.btn_play = ctk.CTkButton(row, text=tr("btn_play"), width=110, command=self.toggle)
        self.btn_play.pack(side="left", padx=4)
        ctk.CTkButton(row, text=tr("btn_stop"), width=90, fg_color="#b33", hover_color="#922",
                      command=self.stop).pack(side="left", padx=4)
        ctk.CTkButton(row, text="▶▶", width=56, fg_color="#444", hover_color="#555",
                      command=self.next_track).pack(side="left", padx=4)

        ctk.CTkLabel(ctl, text=tr("play_mode"), anchor="w", text_color="gray").pack(fill="x", padx=12)
        self.mode_by_label = {tr(k): m for k, m in MODES}
        self.seg_mode = ctk.CTkSegmentedButton(ctl, values=list(self.mode_by_label), command=self.on_mode,
                                               font=ctk.CTkFont(size=12))
        self.seg_mode.set(self.mode_label(self.mode))
        self.seg_mode.pack(fill="x", padx=12, pady=(2, 6))

        mix = ctk.CTkFrame(ctl, fg_color="transparent")
        mix.pack(fill="x", pady=(2, 0))
        mix.grid_columnconfigure(1, weight=1)
        self.lbl_vol, self.sl_vol = self.make_slider(mix, 0, tr("vol", v=100), 0, 500, 100, self.on_vol)
        self.lbl_spd, self.sl_spd = self.make_slider(mix, 1, tr("spd", v="1.00"), 0.5, 2.0, 1.0, self.on_spd)
        self.lbl_bass, self.sl_bass = self.make_slider(mix, 2, tr("bass", v=0), 0, 100, 0, self.on_bass)

        fx = ctk.CTkFrame(ctl, fg_color="transparent")
        fx.pack(fill="x", padx=12, pady=(2, 4))
        self.loud_v = ctk.BooleanVar()
        ctk.CTkCheckBox(fx, text=tr("loud"), variable=self.loud_v,
                        command=lambda: setattr(self.player, "loud", self.loud_v.get())).pack(side="left")
        ctk.CTkButton(fx, text=tr("reset_fx"), width=90, fg_color="#444", hover_color="#555",
                      command=self.reset_fx).pack(side="right")
        ctk.CTkLabel(ctl, text=tr("hotkeys"), text_color="gray",
                     font=ctk.CTkFont(size=11)).pack(pady=(0, 8))

        self.listf = ctk.CTkScrollableFrame(self, height=140, label_text=tr("library_label"))
        self.listf.pack(fill="both", expand=True, **pad)

    def make_slider(self, parent, row, text, lo, hi, init, cmd):
        lbl = ctk.CTkLabel(parent, text=text, anchor="w", width=130)
        lbl.grid(row=row, column=0, sticky="w", padx=(12, 4), pady=3)
        sl = ctk.CTkSlider(parent, from_=lo, to=hi, command=cmd)
        sl.set(init)
        sl.grid(row=row, column=1, sticky="ew", padx=(0, 12), pady=3)
        return lbl, sl

    def mode_label(self, mode):
        return next(label for label, m in self.mode_by_label.items() if m == mode)

    # ------------------------------------------------------------ เปลี่ยนภาษา
    def on_language(self, name):
        code = LANG_BY_NAME.get(name)
        if code and code != get_lang():
            # รอให้แอนิเมชันคลิกของปุ่มเดิมจบก่อน แล้วค่อยสร้างหน้าจอใหม่
            self.after(200, lambda: self.apply_language(code))

    def apply_language(self, code):
        set_lang(code)
        try:
            save_settings({**load_settings(), "lang": code})
        except OSError:
            pass
        keep = dict(out=self.cb_out.get(), mon=self.cb_mon.get(), mon_off=self.cb_mon.get() == self.off_label,
                    vol=self.sl_vol.get(), spd=self.sl_spd.get(), bass=self.sl_bass.get(),
                    loud=self.loud_v.get())
        for w in self.winfo_children():
            w.destroy()
        self.help_win = None
        self.build()
        self.cb_out.set(keep["out"])
        self.cb_mon.set(self.off_label if keep["mon_off"] else keep["mon"])
        self.sl_vol.set(keep["vol"])
        self.on_vol(keep["vol"])
        self.sl_spd.set(keep["spd"])
        self.on_spd(keep["spd"])
        self.sl_bass.set(keep["bass"])
        self.on_bass(keep["bass"])
        self.loud_v.set(keep["loud"])
        self.set_title()
        self.say(self._status[0], **self._status[1])
        self.refresh_lib()
        self.update_now()

    # ------------------------------------------------------------ อุปกรณ์/เสียง
    def dev_index(self, name):
        return next((i for n, i in self.outs if n == name), None)

    def apply_devices(self):
        out = self.dev_index(self.cb_out.get())
        mon = self.dev_index(self.cb_mon.get())
        if out is None:
            self.say("dev_none")
            return
        try:
            self.player.open(out, mon)
            self.say("dev_ok")
        except Exception as e:
            self.say("dev_fail", err=str(e)[:80])

    def on_vol(self, v):
        self.player.volume = v / 100
        self.lbl_vol.configure(text=tr("vol", v=int(v)))

    def on_spd(self, v):
        self.player.speed = round(v, 2)
        self.lbl_spd.configure(text=tr("spd", v=f"{v:.2f}"))

    def on_bass(self, v):
        self.player.bass = v / 100
        self.lbl_bass.configure(text=tr("bass", v=int(v)))

    def reset_fx(self):
        self.sl_vol.set(100)
        self.on_vol(100)
        self.sl_spd.set(1.0)
        self.on_spd(1.0)
        self.sl_bass.set(0)
        self.on_bass(0)
        self.loud_v.set(False)
        self.player.loud = False

    def on_seek(self, v):
        if self.player.data is not None:
            self.player.seek(v)

    def on_mode(self, label):
        self.mode = self.mode_by_label[label]
        self.player.loop = self.mode == REPEAT_ONE

    # ------------------------------------------------------------ คลังเสียง
    def refresh_lib(self):
        for w in self.listf.winfo_children():
            w.destroy()
        if not self.lib.items:
            ctk.CTkLabel(self.listf, text=tr("empty_library"), text_color="gray").pack(pady=16)
            return
        for i, it in enumerate(self.lib.items):
            is_cur = i == self.cur
            r = ctk.CTkFrame(self.listf, fg_color="transparent")
            r.pack(fill="x", pady=2)
            prefix = "▶ " if is_cur else f"{i + 1}. "
            btn = ctk.CTkButton(r, text=prefix + short(it["title"]), anchor="w",
                                fg_color="#1f538d" if is_cur else "#2b2b2b",
                                hover_color="#2a6bb5" if is_cur else "#3a3a3a",
                                command=lambda i=i: self.play_index(i))
            btn.pack(side="left", fill="x", expand=True)
            btn.bind("<Button-3>", lambda e, i=i: self.rename_item(i))
            ctk.CTkButton(r, text="✎", width=32, fg_color="#444", hover_color="#555",
                          command=lambda i=i: self.rename_item(i)).pack(side="left", padx=(4, 0))
            ctk.CTkButton(r, text="✕", width=32, fg_color="#444", hover_color="#a33",
                          command=lambda i=i: self.delete_item(i)).pack(side="left", padx=(4, 0))

    def update_now(self):
        if self.cur is None or self.cur >= len(self.lib.items):
            self.lbl_now.configure(text=tr("no_track"))
        else:
            self.lbl_now.configure(text="♪ " + short(self.lib.items[self.cur]["title"], 64))

    def rename_item(self, i):
        if not (0 <= i < len(self.lib.items)):
            return
        dlg = RenameDialog(self, self.lib.items[i]["title"])
        self.wait_window(dlg)
        if dlg.result is not None:
            if self.lib.rename(i, dlg.result):
                self.say("renamed")
                self.refresh_lib()
                self.update_now()
            else:
                self.say("rename_empty")

    def delete_item(self, i):
        item = self.lib.remove(i)
        if item is None:
            return
        # ลบไฟล์แคชด้วย (เฉพาะไฟล์ที่โปรแกรมโหลดมาเอง ไม่แตะไฟล์ในเครื่องของผู้ใช้)
        if is_inside(item["file"], cache_dir()):
            try:
                os.remove(item["file"])
            except OSError:
                pass
        if i == self.cur:
            self.load_token += 1
            self.player.clear()
            self.cur = None
        elif self.cur is not None and i < self.cur:
            self.cur -= 1
        self.refresh_lib()
        self.update_now()

    # ------------------------------------------------------------ เพิ่ม/โหลดเสียง
    def add_url(self):
        url = self.ent_url.get().strip()
        if not url:
            return
        if " " in url or "." not in url:
            self.say("bad_link")
            return
        if not url.lower().startswith(("http://", "https://")):
            url = "https://" + url
        self.ent_url.delete(0, "end")
        self.say("downloading")
        threading.Thread(target=self._download_worker, args=(url,), daemon=True).start()

    def add_file(self):
        exts = " ".join(f"*.{e}" for e in AUDIO_EXTS)
        paths = filedialog.askopenfilenames(filetypes=[(tr("ft_media"), exts), (tr("ft_all"), "*.*")])
        if not paths:
            return
        first = None
        for p in paths:
            idx = self.lib.add(Path(p).stem, p)
            first = idx if first is None else first
        self.refresh_lib()
        self.play_index(first)

    def _download_worker(self, url):
        try:
            title, path = download(url, str(cache_dir()))
        except Exception as e:
            msg = explain_error(e)      # แปลงเป็นข้อความก่อน (ตัวแปร e หายหลังจบ except)
            self.q.put(lambda: self.say("dl_fail", msg=msg))
            return
        self.q.put(lambda: self._added(title, path, url))

    def _added(self, title, path, url):
        idx = self.lib.add(title, path, url)
        self.refresh_lib()
        self.play_index(idx)

    def play_index(self, i):
        if not 0 <= i < len(self.lib.items):
            return
        it = self.lib.items[i]
        self.load_token += 1
        token = self.load_token
        self.say("loading", title=short(it["title"], 40))
        threading.Thread(target=self._load_worker, args=(it, token), daemon=True).start()

    def _load_worker(self, it, token):
        try:
            path = it["file"]
            if not os.path.exists(path):
                if not it.get("src"):
                    raise FileNotFoundError(tr("file_gone"))
                self.q.put(lambda: self.say("redownload"))
                _, path = download(it["src"], str(cache_dir()))
                it["file"] = path
                self.q.put(self.lib.save)
            data = decode(path)
        except Exception as e:
            msg = explain_error(e)
            self.q.put(lambda: self.say("play_fail", msg=msg))
            return
        self.q.put(lambda: self._start(it, token, data))

    def _start(self, it, token, data):
        if token != self.load_token:        # มีการสั่งเล่นเพลงอื่นแทรกมาแล้ว
            return
        idx = self.lib.index_of(it)
        if idx is None:                      # เพลงถูกลบระหว่างโหลด
            return
        p = self.player
        p.set_data(data)
        p.loop = self.mode == REPEAT_ONE
        p.playing = True
        self.cur = idx
        self.refresh_lib()
        self.update_now()
        self.say("now_playing", dur=fmt(len(data) / SR))

    # ------------------------------------------------------------ ควบคุม
    def toggle(self):
        p = self.player
        if p.data is None:
            if self.lib.items:
                self.play_index(self.cur if self.cur is not None else 0)
            return
        p.playing = not p.playing

    def stop(self):
        self.player.stop()
        self.say("stopped")

    def next_track(self):
        i = step(self.cur, len(self.lib.items), +1)
        if i is not None:
            self.play_index(i)

    def prev_track(self):
        i = step(self.cur, len(self.lib.items), -1)
        if i is not None:
            self.play_index(i)

    def on_track_end(self):
        nxt = next_on_end(self.mode, self.cur, len(self.lib.items))
        if nxt is None:
            self.say("finished")
        else:
            self.play_index(nxt)

    def setup_hotkeys(self):
        if not keyboard:
            return
        for key, fn in (("f7", self.prev_track), ("f8", self.toggle),
                        ("f9", self.stop), ("f10", self.next_track)):
            try:
                keyboard.add_hotkey(key, lambda fn=fn: self.q.put(fn))
            except Exception:
                pass

    def show_help(self):
        if self.help_win is not None and self.help_win.winfo_exists():
            self.help_win.lift()
            return
        w = ctk.CTkToplevel(self)
        w.title(tr("help_title"))
        w.geometry("580x600")
        box = ctk.CTkTextbox(w, wrap="word")
        box.pack(fill="both", expand=True, padx=12, pady=12)
        box.insert("1.0", tr("help_text"))
        box.configure(state="disabled")
        self.help_win = w
        w.after(200, w.lift)

    # ------------------------------------------------------------ วนอัปเดตหน้าจอ
    def tick(self):
        while True:
            try:
                fn = self.q.get_nowait()
            except queue.Empty:
                break
            try:
                fn()
            except Exception as e:
                print("ui error:", e)
        p = self.player
        self.btn_play.configure(text=tr("btn_pause") if p.playing else tr("btn_play"))
        if p.data is not None:
            self.lbl_time.configure(text=tr("time_fmt", pos=fmt(p.position()), dur=fmt(p.duration())))
            self.sl_pos.set(p.progress())
        else:
            self.lbl_time.configure(text=tr("time_fmt", pos="0:00", dur="0:00"))
            self.sl_pos.set(0)
        if p.ended:
            p.ended = False
            self.on_track_end()
        self.after(150, self.tick)

    def on_close(self):
        if keyboard:
            try:
                keyboard.unhook_all()
            except Exception:
                pass
        for v in self.player.voices:
            v.close()
        self.destroy()
