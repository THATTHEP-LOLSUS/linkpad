"""ทดสอบการคำนวณเสียงโดยไม่ต้องมีการ์ดเสียง (จำลอง sounddevice)"""
import sys
import types
import unittest

try:
    import numpy as np
    import scipy  # noqa: F401
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False

if HAVE_DEPS:
    sys.modules.setdefault("sounddevice", types.ModuleType("sounddevice"))
    from linkpad.audio import Player, Voice


def make_voice(player, primary=True):
    v = Voice.__new__(Voice)          # ข้ามการเปิด stream จริง
    v.p, v.pos, v.primary, v.ch, v.zi = player, 0.0, primary, 2, np.zeros((1, 2))
    return v


def ramp(n):
    """ข้อมูลทดสอบ: ค่าเพิ่มทีละ 1 ทุกเฟรม ทั้งสองช่อง"""
    x = np.arange(n, dtype=np.int16)
    return np.stack([x, x], axis=1)


@unittest.skipUnless(HAVE_DEPS, "needs numpy and scipy")
class RenderTests(unittest.TestCase):
    def setUp(self):
        self.p = Player()
        self.v = make_voice(self.p)
        self.p.voices = [self.v]
        self.p.data = ramp(1000)
        self.p.playing = True

    def test_normal_speed_advances_one_sample_per_frame(self):
        out = self.v.render_file(10)
        np.testing.assert_allclose(out[:, 0] * 32768, np.arange(10), atol=1e-3)
        self.assertAlmostEqual(self.v.pos, 10.0)

    def test_double_speed_skips_samples(self):
        self.p.speed = 2.0
        out = self.v.render_file(10)
        np.testing.assert_allclose(out[:, 0] * 32768, np.arange(10) * 2, atol=1e-3)

    def test_end_signals_once_and_resets(self):
        self.v.pos = 995.0
        self.v.render_file(50)
        self.assertTrue(self.p.ended)
        self.assertFalse(self.p.playing)
        self.assertEqual(self.v.pos, 0.0)

    def test_end_pads_with_silence(self):
        self.v.pos = 995.0
        out = self.v.render_file(20)
        self.assertTrue(np.all(out[10:] == 0))

    def test_loop_is_seamless_and_never_ends(self):
        self.p.loop = True
        self.v.pos = 995.0
        out = self.v.render_file(20)
        self.assertFalse(self.p.ended)
        self.assertTrue(self.p.playing)
        self.assertTrue(np.all(np.isfinite(out)))
        self.assertTrue(0 <= self.v.pos < 999)
        self.assertTrue(np.any(out[10:] != 0))      # หลังวนกลับยังมีเสียงต่อ

    def test_secondary_voice_waits_for_primary(self):
        mon = make_voice(self.p, primary=False)
        mon.pos = 995.0
        mon.render_file(50)
        self.assertFalse(self.p.ended)
        self.assertEqual(mon.pos, 999.0)

    def test_callback_applies_volume_and_clips(self):
        self.p.volume = 100.0
        buf = np.zeros((16, 2), np.float32)
        self.v.pos = 500.0
        self.v.cb(buf, 16, None, None)
        self.assertTrue(np.all(np.abs(buf) <= 1.0))
        self.assertTrue(np.any(buf == 1.0))

    def test_callback_silent_when_paused(self):
        self.p.playing = False
        buf = np.ones((16, 2), np.float32)
        self.v.cb(buf, 16, None, None)
        self.assertTrue(np.all(buf == 0))

    def test_bass_adds_energy_and_keeps_filter_state(self):
        self.p.bass = 1.0
        self.v.pos = 100.0
        buf = np.zeros((64, 2), np.float32)
        self.v.cb(buf, 64, None, None)
        self.assertTrue(np.any(self.v.zi != 0))


@unittest.skipUnless(HAVE_DEPS, "needs numpy and scipy")
class PlayerTests(unittest.TestCase):
    def test_seek_position_duration(self):
        p = Player()
        v = make_voice(p)
        p.voices = [v]
        p.data = ramp(48000 * 10)
        p.seek(0.5)
        self.assertAlmostEqual(p.position(), 5.0, places=2)
        self.assertAlmostEqual(p.duration(), 10.0)
        self.assertAlmostEqual(p.progress(), 0.5, places=3)

    def test_stop_resets_position_without_signalling_end(self):
        p = Player()
        v = make_voice(p)
        p.voices = [v]
        p.data = ramp(1000)
        p.playing = True
        v.pos = 300.0
        p.stop()
        self.assertFalse(p.playing)
        self.assertFalse(p.ended)
        self.assertEqual(v.pos, 0.0)

    def test_set_data_clears_ended_flag(self):
        p = Player()
        p.ended = True
        p.set_data(ramp(100))
        self.assertFalse(p.ended)


if __name__ == "__main__":
    unittest.main()
