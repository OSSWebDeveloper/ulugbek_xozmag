@echo off
chcp 65001 > nul
title Ulug'bek Xozmag - o'chirish
setlocal EnableDelayedExpansion

rem ---------------------------------------------------------------
rem  Ulug'bek Xozmag dasturini kompyuterdan butunlay o'chiradi.
rem  Administrator huquqi kerak emas.
rem
rem  Ishlatish: shu faylni ikki marta bosing.
rem ---------------------------------------------------------------

set "DASTUR=%LOCALAPPDATA%\Programs\UlugbekXozmag"
set "MALUMOT=%LOCALAPPDATA%\UlugbekXozmag"
set "YORLIQ=Ulug'bek Xozmag.lnk"
set "MENYU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"

rem --- Agar shu fayl dastur papkasining ichida tursa, o'shani o'chiramiz
if exist "%~dp0Xozmag.exe" set "DASTUR=%~dp0"

echo.
echo ==========================================================
echo   Ulug'bek Xozmag - o'chirish
echo ==========================================================
echo.
echo   Dastur papkasi : %DASTUR%
echo   Ma'lumotlar    : %MALUMOT%
echo.

set "JAVOB="
set /p "JAVOB=Dastur o'chirilsinmi? (ha/yo'q): "
if /i not "%JAVOB%"=="ha" (
    echo Bekor qilindi.
    pause
    exit /b 0
)

echo.
echo [1/5] Dastur to'xtatilmoqda...
taskkill /F /IM Xozmag.exe > nul 2>&1
timeout /t 1 /nobreak > nul

echo [2/5] Yorliqlar olib tashlanmoqda...
if exist "%USERPROFILE%\Desktop\%YORLIQ%" del /f /q "%USERPROFILE%\Desktop\%YORLIQ%" > nul 2>&1
if exist "%MENYU%\%YORLIQ%" del /f /q "%MENYU%\%YORLIQ%" > nul 2>&1

echo [3/5] Ro'yxatdan o'chirilmoqda...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\UlugbekXozmag" /f > nul 2>&1

echo [4/5] Ma'lumotlar bazasi...
set "BAZA="
set /p "BAZA=Baza (qarzdorlar, sotuvlar) ham o'chirilsinmi? (ha/yo'q): "
if /i "%BAZA%"=="ha" (
    if exist "%MALUMOT%" rmdir /s /q "%MALUMOT%" > nul 2>&1
    echo     baza o'chirildi.
) else (
    echo     baza saqlab qolindi: %MALUMOT%
)

echo [5/5] Dastur fayllari o'chirilmoqda...
rem Shu bat faylning o'zi ham o'sha papkada bo'lishi mumkin - keyinroq o'chadi
if exist "%DASTUR%" (
    start "" /min cmd /c "ping 127.0.0.1 -n 3 > nul & rmdir /s /q ""%DASTUR%"""
)

echo.
echo Tayyor. Dastur o'chirildi.
echo.
timeout /t 4 /nobreak > nul
exit /b 0
