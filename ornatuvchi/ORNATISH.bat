@echo off
chcp 65001 > nul
title Ulug'bek Xozmag - o'rnatish
setlocal EnableDelayedExpansion

rem ---------------------------------------------------------------
rem  Ulug'bek Xozmag dasturini kompyuterga o'rnatadi.
rem
rem  Shu fayl yonida "Xozmag" papkasi turishi kerak (dasturning o'zi).
rem  Administrator huquqi kerak emas - hamma narsa foydalanuvchi
rem  papkasiga tushadi.
rem ---------------------------------------------------------------

set "MANBA=%~dp0Xozmag"
set "DASTUR=%LOCALAPPDATA%\Programs\UlugbekXozmag"
set "MALUMOT=%LOCALAPPDATA%\UlugbekXozmag"
set "YORLIQ=Ulug'bek Xozmag.lnk"
set "MENYU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"

echo.
echo ==========================================================
echo   Ulug'bek Xozmag - o'rnatish
echo ==========================================================
echo.

if not exist "%MANBA%\Xozmag.exe" (
    echo XATO: "%MANBA%\Xozmag.exe" topilmadi.
    echo.
    echo Shu .bat fayl "Xozmag" papkasi bilan bitta joyda turishi kerak.
    echo Arxivni to'liq ochib, keyin qaytadan bosing.
    echo.
    pause
    exit /b 1
)

echo   Qayerga : %DASTUR%
echo   Baza    : %MALUMOT%
echo.

set "JAVOB="
set /p "JAVOB=O'rnatilsinmi? (ha/yo'q): "
if /i not "%JAVOB%"=="ha" (
    echo Bekor qilindi.
    pause
    exit /b 0
)

echo.
echo [1/5] Ishlab turgan nusxa to'xtatilmoqda...
taskkill /F /IM Xozmag.exe > nul 2>&1
timeout /t 1 /nobreak > nul

echo [2/5] Fayllar ko'chirilmoqda (biroz vaqt oladi)...
if not exist "%DASTUR%" mkdir "%DASTUR%" > nul 2>&1
robocopy "%MANBA%" "%DASTUR%" /MIR /NFL /NDL /NJH /NJS /NP > nul
if errorlevel 8 (
    echo XATO: fayllarni ko'chirib bo'lmadi.
    pause
    exit /b 1
)
if exist "%~dp0OCHIRISH.bat" copy /y "%~dp0OCHIRISH.bat" "%DASTUR%\OCHIRISH.bat" > nul

echo [3/5] Boshlash menyusiga yorliq...
powershell -NoProfile -NonInteractive -Command "$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut('%MENYU%\%YORLIQ%');$s.TargetPath='%DASTUR%\Xozmag.exe';$s.WorkingDirectory='%DASTUR%';$s.IconLocation='%DASTUR%\xozmag.ico';$s.Description='Ulugbek Xozmag - dokon dasturi';$s.Save()" > nul 2>&1

echo [4/5] Ish stoliga yorliq...
set "ISHSTOLI="
set /p "ISHSTOLI=Ish stoliga ham yorliq qo'yilsinmi? (ha/yo'q): "
if /i "%ISHSTOLI%"=="ha" (
    powershell -NoProfile -NonInteractive -Command "$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut('%USERPROFILE%\Desktop\%YORLIQ%');$s.TargetPath='%DASTUR%\Xozmag.exe';$s.WorkingDirectory='%DASTUR%';$s.IconLocation='%DASTUR%\xozmag.ico';$s.Description='Ulugbek Xozmag - dokon dasturi';$s.Save()" > nul 2>&1
    echo     qo'yildi.
)

echo [5/5] Dasturlar ro'yxatiga yozilmoqda...
set "KALIT=HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\UlugbekXozmag"
set "VERSIYA=0.0.0"
if exist "%DASTUR%\_internal\versiya.txt" set /p VERSIYA=<"%DASTUR%\_internal\versiya.txt"
reg add "%KALIT%" /v DisplayName /t REG_SZ /d "Ulug'bek Xozmag" /f > nul
reg add "%KALIT%" /v DisplayVersion /t REG_SZ /d "%VERSIYA%" /f > nul
reg add "%KALIT%" /v Publisher /t REG_SZ /d "Ulug'bek Xozmag" /f > nul
reg add "%KALIT%" /v InstallLocation /t REG_SZ /d "%DASTUR%" /f > nul
reg add "%KALIT%" /v DisplayIcon /t REG_SZ /d "%DASTUR%\Xozmag.exe" /f > nul
reg add "%KALIT%" /v UninstallString /t REG_SZ /d "\"%DASTUR%\OCHIRISH.bat\"" /f > nul
reg add "%KALIT%" /v NoModify /t REG_DWORD /d 1 /f > nul
reg add "%KALIT%" /v NoRepair /t REG_DWORD /d 1 /f > nul

echo.
echo ==========================================================
echo   Tayyor. Dastur o'rnatildi.
echo ==========================================================
echo.
echo   Ochish     : ish stoli yorlig'i yoki Boshlash menyusi
echo   O'chirish  : %DASTUR%\OCHIRISH.bat
echo.

set "OCHAMI="
set /p "OCHAMI=Dastur hozir ochilsinmi? (ha/yo'q): "
if /i "%OCHAMI%"=="ha" start "" "%DASTUR%\Xozmag.exe"

exit /b 0
