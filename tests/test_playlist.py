import unittest

from linkpad.playlist import ALL, ONCE, REPEAT_ALL, REPEAT_ONE, next_on_end, step


class NextOnEnd(unittest.TestCase):
    def test_once_stops(self):
        self.assertIsNone(next_on_end(ONCE, 0, 3))

    def test_repeat_one_stays(self):
        self.assertEqual(next_on_end(REPEAT_ONE, 1, 3), 1)

    def test_all_advances_then_stops_at_end(self):
        self.assertEqual(next_on_end(ALL, 0, 3), 1)
        self.assertEqual(next_on_end(ALL, 1, 3), 2)
        self.assertIsNone(next_on_end(ALL, 2, 3))

    def test_repeat_all_wraps(self):
        self.assertEqual(next_on_end(REPEAT_ALL, 2, 3), 0)
        self.assertEqual(next_on_end(REPEAT_ALL, 0, 1), 0)

    def test_empty_or_unknown_current(self):
        self.assertIsNone(next_on_end(REPEAT_ALL, 0, 0))
        self.assertIsNone(next_on_end(ALL, None, 3))


class Step(unittest.TestCase):
    def test_wraps_both_directions(self):
        self.assertEqual(step(2, 3, +1), 0)
        self.assertEqual(step(0, 3, -1), 2)
        self.assertEqual(step(1, 3, +1), 2)

    def test_no_current(self):
        self.assertEqual(step(None, 3, +1), 0)
        self.assertEqual(step(None, 3, -1), 2)

    def test_empty(self):
        self.assertIsNone(step(None, 0, +1))


if __name__ == "__main__":
    unittest.main()
