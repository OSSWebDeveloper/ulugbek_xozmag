"""Ulug'bek Xozmag — o'rnatuvchi va o'chirgich.

Bitta dastur ikki ishni bajaradi:
  * oddiy ochilsa      — dasturni kompyuterga o'rnatadi;
  * `--ochirish` bilan — o'rnatilgan dasturni o'chiradi.

O'rnatgichning o'zi o'rnatish papkasiga `Ochirish.exe` nomi bilan ko'chiriladi,
shuning uchun «Dasturlar va imkoniyatlar» ro'yxatidan ham o'chirsa bo'ladi.

Administrator huquqi kerak emas: hamma narsa foydalanuvchining o'z papkasiga
tushadi (%LOCALAPPDATA% ichidagi Programs papkasi).
"""
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback
import zipfile
from pathlib import Path

NOM = "Ulug'bek Xozmag"
PAPKA_NOM = "UlugbekXozmag"
KALIT = "UlugbekXozmag"          # registrdagi o'chirish yozuvi
DASTUR_EXE = "Xozmag.exe"
OCHIRGICH_EXE = "Ochirish.exe"
YORLIQ = "Ulug'bek Xozmag.lnk"
TUB = chr(92)                     # teskari chiziq ("\\")

FON = "#0f172a"
FON_2 = "#1e293b"
MATN = "#e2e8f0"
XIRA = "#94a3b8"
KOK = "#2563eb"
KOK_2 = "#1d4ed8"


# --------------------------------------------------------------- yordamchilar
def ildiz() -> Path:
    """O'rnatgich ichidagi fayllar turgan papka."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def ozim() -> Path:
    """Shu dasturning o'zi (exe yoki .py)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return Path(__file__).resolve()


def standart_joy() -> Path:
    # O'chirgich o'rnatilgan papkaning ichidan ishga tushsa — o'sha papka.
    yonida = ozim().parent
    if (yonida / DASTUR_EXE).exists():
        return yonida
    asos = os.environ.get("LOCALAPPDATA")
    if asos:
        return Path(asos) / "Programs" / PAPKA_NOM
    return Path.home() / PAPKA_NOM


def malumot_joy() -> Path:
    asos = os.environ.get("LOCALAPPDATA")
    return (Path(asos) if asos else Path.home()) / PAPKA_NOM


def ish_stoli() -> Path:
    return Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop"


def bosh_menyu() -> Path:
    asos = os.environ.get("APPDATA")
    qism = ["Microsoft", "Windows", "Start Menu", "Programs"]
    yol = Path(asos) if asos else Path.home()
    for q in qism:
        yol = yol / q
    return yol


def powershell(buyruq: str) -> None:
    """Kichik PowerShell buyrug'ini jimgina bajaradi."""
    bayroq = 0x08000000 if os.name == "nt" else 0      # CREATE_NO_WINDOW
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", buyruq],
        creationflags=bayroq, capture_output=True, timeout=60,
    )


def yorliq_yasa(qayerga: Path, nishon: Path, ikon: Path) -> None:
    qayerga.parent.mkdir(parents=True, exist_ok=True)
    buyruq = (
        "$w = New-Object -ComObject WScript.Shell; "
        f"$s = $w.CreateShortcut('{qayerga}'); "
        f"$s.TargetPath = '{nishon}'; "
        f"$s.WorkingDirectory = '{nishon.parent}'; "
        f"$s.IconLocation = '{ikon}'; "
        f"$s.Description = 'Ulugbek Xozmag - dokon dasturi'; "
        "$s.Save()"
    )
    powershell(buyruq)


def registrga_yoz(joy: Path, versiya: str) -> None:
    if os.name != "nt":
        return
    import winreg

    yol = TUB.join(["Software", "Microsoft", "Windows", "CurrentVersion",
                    "Uninstall", KALIT])
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, yol) as k:
        winreg.SetValueEx(k, "DisplayName", 0, winreg.REG_SZ, NOM)
        winreg.SetValueEx(k, "DisplayVersion", 0, winreg.REG_SZ, versiya)
        winreg.SetValueEx(k, "Publisher", 0, winreg.REG_SZ, "Ulug'bek Xozmag")
        winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ, str(joy))
        winreg.SetValueEx(k, "DisplayIcon", 0, winreg.REG_SZ,
                          str(joy / DASTUR_EXE))
        winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ,
                          f'"{joy / OCHIRGICH_EXE}" --ochirish')
        winreg.SetValueEx(k, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(k, "NoRepair", 0, winreg.REG_DWORD, 1)


def registrdan_ochir() -> None:
    if os.name != "nt":
        return
    import winreg

    yol = TUB.join(["Software", "Microsoft", "Windows", "CurrentVersion",
                    "Uninstall", KALIT])
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, yol)
    except OSError:
        pass


def dasturni_toxtat() -> None:
    """Ishlab turgan Xozmag.exe ni yopadi."""
    if os.name != "nt":
        return
    subprocess.run(["taskkill", "/F", "/IM", DASTUR_EXE], capture_output=True,
                   creationflags=0x08000000)
    time.sleep(0.8)


def versiya_oqi() -> str:
    fayl = ildiz() / "versiya.txt"
    if fayl.exists():
        return fayl.read_text(encoding="utf-8").strip()
    return "0.0.0"


# ------------------------------------------------------------------ o'rnatish
def ornat(joy: Path, ish_stoli_yorliq: bool, xabar) -> None:
    arxiv = ildiz() / "dastur.zip"
    if not arxiv.exists():
        raise FileNotFoundError("dastur.zip topilmadi — o'rnatgich buzuq.")

    xabar("Eski nusxa tekshirilmoqda...")
    dasturni_toxtat()
    if joy.exists():
        for element in joy.iterdir():
            try:
                if element.is_dir():
                    shutil.rmtree(element, ignore_errors=True)
                else:
                    element.unlink(missing_ok=True)
            except OSError:
                pass
    joy.mkdir(parents=True, exist_ok=True)

    xabar("Fayllar ko'chirilmoqda...")
    with zipfile.ZipFile(arxiv) as z:
        z.extractall(joy)

    xabar("O'chirgich qo'yilmoqda...")
    try:
        shutil.copy2(ozim(), joy / OCHIRGICH_EXE)
    except OSError:
        pass

    nishon = joy / DASTUR_EXE
    ikon = joy / "xozmag.ico"
    if not ikon.exists():
        ikon = nishon

    xabar("Yorliqlar yasalmoqda...")
    if ish_stoli_yorliq:
        yorliq_yasa(ish_stoli() / YORLIQ, nishon, ikon)
    yorliq_yasa(bosh_menyu() / YORLIQ, nishon, ikon)

    xabar("Ro'yxatga yozilmoqda...")
    registrga_yoz(joy, versiya_oqi())
    xabar("Tayyor.")


# ------------------------------------------------------------------- o'chirish
def ochir(joy: Path, malumot_ham: bool, xabar) -> None:
    xabar("Dastur to'xtatilmoqda...")
    dasturni_toxtat()

    xabar("Yorliqlar olib tashlanmoqda...")
    for y in (ish_stoli() / YORLIQ, bosh_menyu() / YORLIQ):
        try:
            y.unlink(missing_ok=True)
        except OSError:
            pass

    xabar("Ro'yxatdan o'chirilmoqda...")
    registrdan_ochir()

    if malumot_ham:
        xabar("Ma'lumotlar o'chirilmoqda...")
        shutil.rmtree(malumot_joy(), ignore_errors=True)

    xabar("Fayllar o'chirilmoqda...")
    men = ozim()
    ichkarimi = joy in men.parents
    for element in (joy.iterdir() if joy.exists() else []):
        if element == men:
            continue
        try:
            if element.is_dir():
                shutil.rmtree(element, ignore_errors=True)
            else:
                element.unlink(missing_ok=True)
        except OSError:
            pass

    if ichkarimi:
        # O'chirgich o'zi shu papkada turibdi — o'zini keyinroq o'chiradi.
        subprocess.Popen(
            ["cmd", "/c", "ping 127.0.0.1 -n 3 > nul & rmdir /s /q " + f'"{joy}"'],
            creationflags=0x08000000,
        )
    else:
        shutil.rmtree(joy, ignore_errors=True)
    xabar("Tayyor.")


# ------------------------------------------------------------------------ oyna
class Oyna:
    def __init__(self, ochirish_rejimi: bool):
        import tkinter as tk
        from tkinter import font as tkfont

        self.tk = tk
        self.ochirish_rejimi = ochirish_rejimi
        self.t = tk.Tk()
        self.t.title(("O'chirish — " if ochirish_rejimi else "O'rnatish — ") + NOM)
        self.t.configure(bg=FON)
        self.t.resizable(False, False)
        eni, boyi = 470, 330
        x = (self.t.winfo_screenwidth() - eni) // 2
        y = (self.t.winfo_screenheight() - boyi) // 3
        self.t.geometry(f"{eni}x{boyi}+{x}+{y}")
        ikon = ildiz() / "xozmag.ico"
        if ikon.exists():
            try:
                self.t.iconbitmap(str(ikon))
            except Exception:
                pass

        self.qalin = tkfont.Font(family="Segoe UI", size=15, weight="bold")
        self.oddiy = tkfont.Font(family="Segoe UI", size=10)
        self.mayda = tkfont.Font(family="Segoe UI", size=9)

        tk.Label(self.t, text=NOM, bg=FON, fg="#ffffff",
                 font=self.qalin).pack(pady=(26, 2))
        tk.Label(self.t, text=("Dasturni kompyuterdan o'chirish"
                               if ochirish_rejimi else
                               f"Versiya {versiya_oqi()} — kompyuterga o'rnatish"),
                 bg=FON, fg=XIRA, font=self.mayda).pack()

        quti = tk.Frame(self.t, bg=FON)
        quti.pack(fill="x", padx=34, pady=(22, 0))

        self.joy = tk.StringVar(value=str(standart_joy()))
        tk.Label(quti, text="Papka:", bg=FON, fg=XIRA,
                 font=self.mayda).pack(anchor="w")
        maydon = tk.Entry(quti, textvariable=self.joy, font=self.mayda,
                          bg=FON_2, fg=MATN, relief="flat", insertbackground=MATN)
        maydon.pack(fill="x", ipady=6, pady=(4, 14))
        if ochirish_rejimi:
            maydon.configure(state="readonly", readonlybackground=FON_2)

        self.belgi = tk.BooleanVar(value=not ochirish_rejimi)
        tk.Checkbutton(
            quti,
            text=("Ma'lumotlar bazasini ham o'chirish (qaytarib bo'lmaydi)"
                  if ochirish_rejimi else "Ish stoliga yorliq qo'yilsin"),
            variable=self.belgi, bg=FON, fg=MATN, selectcolor=FON_2,
            activebackground=FON, activeforeground=MATN, font=self.mayda,
            anchor="w", cursor="hand2",
        ).pack(fill="x")
        if ochirish_rejimi:
            self.belgi.set(False)

        self.holat = tk.Label(self.t, text="", bg=FON, fg=XIRA, font=self.mayda)
        self.holat.pack(pady=(18, 0))

        self.tugma = tk.Button(
            self.t, text=("O'chirish" if ochirish_rejimi else "O'rnatish"),
            font=self.oddiy, width=30, relief="flat", cursor="hand2",
            bg=("#b91c1c" if ochirish_rejimi else KOK), fg="#ffffff",
            activebackground=("#991b1b" if ochirish_rejimi else KOK_2),
            activeforeground="#ffffff", command=self.boshla,
        )
        self.tugma.pack(pady=(14, 0), ipady=4)

    def xabar(self, matn: str) -> None:
        self.holat.configure(text=matn)
        self.t.update_idletasks()

    def boshla(self) -> None:
        self.tugma.configure(state="disabled")
        threading.Thread(target=self.ishla, daemon=True).start()

    def ishla(self) -> None:
        from tkinter import messagebox

        joy = Path(self.joy.get().strip() or standart_joy())
        try:
            if self.ochirish_rejimi:
                ochir(joy, self.belgi.get(), self.xabar)
                messagebox.showinfo(NOM, "Dastur o'chirildi.")
                self.t.destroy()
                return
            ornat(joy, self.belgi.get(), self.xabar)
            if messagebox.askyesno(NOM, "O'rnatildi. Dastur hozir ochilsinmi?"):
                os.startfile(joy / DASTUR_EXE)  # noqa: S606
            self.t.destroy()
        except Exception:
            messagebox.showerror(NOM, "Xatolik:" + os.linesep * 2
                                 + traceback.format_exc(limit=4))
            self.tugma.configure(state="normal")
            self.xabar("")

    def yur(self) -> None:
        self.t.mainloop()


def main() -> int:
    ochirish = "--ochirish" in sys.argv or "/ochirish" in sys.argv
    Oyna(ochirish).yur()
    return 0


if __name__ == "__main__":
    sys.exit(main())
