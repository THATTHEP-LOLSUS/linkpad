"""รันด้วย: python -m linkpad"""


def main():
    from .gui import App   # import ตรงนี้ เพื่อให้ import แพ็กเกจเฉยๆ ไม่ดึง GUI/เสียงเข้ามา
    App().mainloop()


if __name__ == "__main__":
    main()
