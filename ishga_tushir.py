"""Ulug'bek Xozmag — o'rnatilgan dastur uchun ishga tushirgich.

Dastur ochilganda:
  1. birinchi marta bo'lsa — ichidagi tayyor baza foydalanuvchi papkasiga
     ko'chiriladi (%LOCALAPPDATA% ichidagi UlugbekXozmag papkasiga);
  2. bo'sh port topiladi va Django serveri fonda ishga tushadi;
  3. brauzer ochiladi, ekranda esa kichkina boshqaruv oynasi qoladi.

Oyna yopilsa server ham to'xtaydi.
"""
import ctypes
import os
import shutil
import socket
import sys
import threading
import traceback
import webbrowser
from pathlib import Path

NOM = "Ulug'bek Xozmag"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def ildiz() -> Path:
    """Dastur fayllari turgan papka (yig'ilganda — vaqtinchalik papka)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def malumot_papka() -> Path:
    if getattr(sys, "frozen", False):
        p = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "UlugbekXozmag"
    else:
        p = ildiz()
    p.mkdir(parents=True, exist_ok=True)
    return p


def bazani_tayyorla() -> None:
    """Birinchi ishga tushirishda ichidagi tayyor bazani ko'chiradi."""
    baza = malumot_papka() / "db.sqlite3"
    if baza.exists():
        return
    urugh = ildiz() / "boshlangich_baza" / "db.sqlite3"
    if urugh.exists():
        shutil.copy2(urugh, baza)


def bosh_port(boshlanish: int = 8000, urinish: int = 30) -> int:
    for port in range(boshlanish, boshlanish + urinish):
        with socket.socket() as s:
            s.settimeout(0.3)
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return boshlanish


def yagona_nusxa() -> bool:
    """Dastur ikki marta ochilmasin (Windows mutex)."""
    if os.name != "nt":
        return True
    ctypes.windll.kernel32.CreateMutexW(None, False, "UlugbekXozmagYagona")
    return ctypes.windll.kernel32.GetLastError() != 183  # ERROR_ALREADY_EXISTS


def serverni_boshla(port: int) -> None:
    import django

    django.setup()
    from django.core.management import call_command

    call_command("migrate", interactive=False, verbosity=0)

    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.handlers.wsgi import WSGIHandler
    from django.core.servers.basehttp import WSGIServer, run

    # DEBUG o'chiq bo'lgani uchun css/js ni shu qobiq uzatadi.
    run("127.0.0.1", port, StaticFilesHandler(WSGIHandler()),
        ipv6=False, threading=True, server_cls=WSGIServer)


def xato_oyna(matn: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        t = tk.Tk()
        t.withdraw()
        messagebox.showerror(NOM, matn)
        t.destroy()
    except Exception:
        print(matn)


def oyna(manzil: str) -> None:
    import tkinter as tk
    from tkinter import font as tkfont

    t = tk.Tk()
    t.title(NOM)
    t.configure(bg="#111827")
    t.resizable(False, False)
    eni, boyi = 420, 230
    x = (t.winfo_screenwidth() - eni) // 2
    y = (t.winfo_screenheight() - boyi) // 3
    t.geometry(f"{eni}x{boyi}+{x}+{y}")
    ikon = ildiz() / "xozmag.ico"
    if ikon.exists():
        try:
            t.iconbitmap(str(ikon))
        except Exception:
            pass

    qalin = tkfont.Font(family="Segoe UI", size=14, weight="bold")
    oddiy = tkfont.Font(family="Segoe UI", size=10)

    tk.Label(t, text=NOM, bg="#111827", fg="#ffffff", font=qalin).pack(pady=(24, 4))
    tk.Label(t, text="Dastur ishlab turibdi", bg="#111827", fg="#9ca3af",
             font=oddiy).pack()
    tk.Label(t, text=manzil, bg="#111827", fg="#60a5fa", font=oddiy).pack(pady=(6, 16))

    tk.Button(t, text="Saytni ochish", font=oddiy, width=26, relief="flat",
              bg="#2563eb", fg="#ffffff", activebackground="#1d4ed8",
              activeforeground="#ffffff", cursor="hand2",
              command=lambda: webbrowser.open(manzil)).pack(pady=3)
    tk.Button(t, text="To'xtatish", font=oddiy, width=26, relief="flat",
              bg="#1f2937", fg="#e5e7eb", activebackground="#374151",
              activeforeground="#ffffff", cursor="hand2",
              command=t.destroy).pack(pady=3)

    tk.Label(t, text="Oyna yopilsa dastur to'xtaydi", bg="#111827",
             fg="#6b7280", font=tkfont.Font(family="Segoe UI", size=8)).pack(side="bottom", pady=8)
    t.mainloop()


def main() -> int:
    if not yagona_nusxa():
        xato_oyna("Dastur allaqachon ochiq. Ekranning pastidagi oynani qarang.")
        return 0
    try:
        bazani_tayyorla()
        port = bosh_port()
        manzil = f"http://127.0.0.1:{port}/"
        threading.Thread(target=serverni_boshla, args=(port,), daemon=True).start()
        webbrowser.open(manzil)
        oyna(manzil)
    except Exception:
        xato_oyna("Dastur ochilmadi:\n\n" + traceback.format_exc(limit=4))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
