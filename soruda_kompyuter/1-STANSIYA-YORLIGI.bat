@echo off
title Rang stansiyasi - yorliq
rem ---------------------------------------------------------------
rem  Rang mashinasi kompyuterida ish stoliga "Rang stansiyasi"
rem  yorlig'ini yaratadi. Kompyuter do'kon Wi-Fi'iga ulangan bo'lsin.
rem ---------------------------------------------------------------
cd /d "%~dp0"
echo Xozmag server kompyuteridagi kichik oynada Wi-Fi manzili yozilgan,
echo masalan:  192.168.1.5:8000
echo.
set "MANZIL="
set /p "MANZIL=Server manzili: "
if "%MANZIL%"=="" goto :eof
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stansiya_yorligi.ps1" -Manzil "%MANZIL%"
echo.
pause
