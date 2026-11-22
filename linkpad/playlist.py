"""ตรรกะลำดับการเล่น (ไม่ผูกกับ GUI เพื่อให้เทสต์ง่าย)"""

ONCE = "once"              # เล่นครั้งเดียวแล้วหยุด
REPEAT_ONE = "repeat_one"  # วนเพลงเดิมไปเรื่อยๆ
ALL = "all"                # เล่นต่อเนื่องทั้งคลัง จบแล้วหยุด
REPEAT_ALL = "repeat_all"  # เล่นต่อเนื่องทั้งคลังและวนกลับมาต้นเมื่อจบ


def next_on_end(mode, cur, n):
    """เพลงจบเองแล้วควรเล่นเพลงลำดับไหนต่อ (None = หยุด)"""
    if n <= 0 or cur is None:
        return None
    if mode == REPEAT_ONE:
        return cur
    if mode == ALL:
        return cur + 1 if cur + 1 < n else None
    if mode == REPEAT_ALL:
        return (cur + 1) % n
    return None


def step(cur, n, delta):
    """กดปุ่มก่อนหน้า/ถัดไปเอง (วนรอบเสมอ)"""
    if n <= 0:
        return None
    if cur is None:
        return 0 if delta > 0 else n - 1
    return (cur + delta) % n
