"""เอนจินเสียง: ส่งเสียงออกหลายอุปกรณ์พร้อมกัน ปรับความเร็ว/ระดับเสียง/เบสแบบเรียลไทม์"""
import numpy as np
import sounddevice as sd
from scipy.signal import lfilter

from .config import SAMPLE_RATE as SR

BASS_A = float(np.exp(-2 * np.pi * 150 / SR))   # low-pass ที่ ~150Hz ใช้ทำ bass boost


# ---------------------------------------------------------------- อุปกรณ์
def output_devices():
    """รายชื่ออุปกรณ์เสียงออก [(ชื่อ, index)] (บน Windows เลือกเฉพาะ WASAPI เพื่อไม่ให้ชื่อซ้ำ)"""
    devs = sd.query_devices()
    apis = sd.query_hostapis()
    items = [(i, d, apis[d["hostapi"]]["name"]) for i, d in enumerate(devs)
             if d["max_output_channels"] > 0]
    wasapi = [x for x in items if "WASAPI" in x[2]]
    if wasapi:
        items = wasapi
    return [(d["name"], i) for i, d, _ in items]


def default_output_name():
    try:
        return sd.query_devices(sd.default.device[1])["name"]
    except Exception:
        return None


def _wasapi_extra(dev):
    try:
        api = sd.query_hostapis(sd.query_devices(dev)["hostapi"])["name"]
        if "WASAPI" in api:
            return sd.WasapiSettings(auto_convert=True)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------- Voice
class Voice:
    """หนึ่ง output stream (เช่น ไมค์เสมือน หรือ หูฟัง) มีตำแหน่งเล่นของตัวเอง"""

    def __init__(self, player, device, primary=False):
        self.p = player
        self.pos = 0.0
        self.primary = primary          # ตัวหลัก = ตัวที่เป็นผู้บอกว่าเพลงจบ/นับเวลา
        self.zi = np.zeros((1, 2))      # สถานะฟิลเตอร์เบส
        self.ch = min(2, sd.query_devices(device)["max_output_channels"])
        self.stream = sd.OutputStream(
            samplerate=SR, device=device, channels=self.ch, dtype="float32",
            callback=self.cb, extra_settings=_wasapi_extra(device))
        self.stream.start()

    def close(self):
        try:
            self.stream.stop()
            self.stream.close()
        except Exception:
            pass

    def render_file(self, frames):
        p, data = self.p, self.p.data
        n = len(data)
        idx = self.pos + np.arange(frames) * p.speed
        step = frames * p.speed
        if p.loop:                                   # วนเพลงเดียว: ต่อกันไม่มีช่องว่าง
            idx %= (n - 1)
            ok = np.ones(frames, bool)
            self.pos = (self.pos + step) % (n - 1)
        else:
            ok = idx < n - 1
            self.pos += step
        i0 = np.minimum(idx.astype(np.int64), n - 2)
        f = (idx - i0).astype(np.float32)[:, None]
        out = (data[i0].astype(np.float32) * (1 - f)
               + data[i0 + 1].astype(np.float32) * f) / 32768.0
        out[~ok] = 0
        if not p.loop and self.pos >= n - 1:
            if self.primary:
                p._on_end()
            else:
                self.pos = float(n - 1)              # ตัวฟังเอง: รอตัวหลักจบ
        return out

    def cb(self, outdata, frames, t, status):
        p = self.p
        try:
            if not (p.playing and p.data is not None and len(p.data) > 2):
                outdata[:] = 0
                return
            out = self.render_file(frames) * p.volume
            if p.bass > 0:                           # Bass boost
                low, self.zi = lfilter([1 - BASS_A], [1, -BASS_A], out, axis=0, zi=self.zi)
                out = out + low * p.bass * 4
            if p.loud:                               # Earrape
                out = out * 8
            out = np.clip(out, -1, 1)
            if self.ch == 1:
                out = out.mean(axis=1, keepdims=True)
            outdata[:] = out
        except Exception as e:                       # กัน stream ล้มกลางคัน
            print("audio callback error:", e)
            outdata[:] = 0


# ---------------------------------------------------------------- Player
class Player:
    def __init__(self):
        self.data = None            # int16 (N, 2) ที่ SR
        self.playing = False
        self.loop = False           # วนเพลงเดียว (ทำในเอนจินเพื่อให้ต่อกันเนียน)
        self.volume = 1.0
        self.speed = 1.0
        self.bass = 0.0             # 0..1
        self.loud = False
        self.ended = False          # ตั้งเป็น True เมื่อเพลงจบเอง (GUI อ่านแล้วเคลียร์)
        self.voices = []

    # --- อุปกรณ์
    def open(self, out_dev, mon_dev):
        keep = self.voices[0].pos if self.voices else 0.0
        for v in self.voices:
            v.close()
        self.voices = []
        new = [Voice(self, out_dev, primary=True)]
        if mon_dev is not None and mon_dev != out_dev:
            try:
                new.append(Voice(self, mon_dev))
            except Exception:
                for v in new:
                    v.close()
                raise
        for v in new:
            v.pos = keep
        self.voices = new

    # --- การเล่น
    def set_data(self, data):
        self.ended = False
        self.playing = False
        self.data = data
        for v in self.voices:
            v.pos = 0.0

    def clear(self):
        self.playing = False
        self.data = None
        for v in self.voices:
            v.pos = 0.0

    def seek(self, frac):
        if self.data is not None and len(self.data) > 2:
            pos = min(1.0, max(0.0, frac)) * (len(self.data) - 2)
            for v in self.voices:
                v.pos = pos

    def position(self):
        """เวลาที่เล่นถึง (วินาทีของไฟล์ต้นฉบับ)"""
        return self.voices[0].pos / SR if self.voices else 0.0

    def duration(self):
        return len(self.data) / SR if self.data is not None else 0.0

    def progress(self):
        if self.data is None or len(self.data) < 3 or not self.voices:
            return 0.0
        return min(1.0, self.voices[0].pos / (len(self.data) - 2))

    def finish(self):
        self.playing = False
        for v in self.voices:
            v.pos = 0.0

    def stop(self):
        self.finish()

    def _on_end(self):
        self.ended = True
        self.finish()
