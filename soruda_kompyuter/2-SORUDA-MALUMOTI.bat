@echo off
title Soruda ma'lumotlarini yig'ish
rem ---------------------------------------------------------------
rem  Soruda tinting system qayerda o'rnatilganini topadi va uning
rem  ma'lumotlarini (rang kodlari, palitra, formulalar, yozuvlar)
rem  shu papkaga zip qilib yig'adi. Hech narsa o'zgartirilmaydi.
rem
rem  Soruda dasturi OCHIQ tursin - shunda u qayerdan ishlayotgani
rem  aniq topiladi. Avval bitta bo'yoq tayyorlang (yoki sinov).
rem ---------------------------------------------------------------
cd /d "%~dp0"
echo Soruda ma'lumotlari yig'ilmoqda, 1-3 daqiqa kuting...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0soruda_malumoti.ps1"
echo.
pause
