@echo off
title Ulug'bek Xozmag - server
rem ---------------------------------------------------------------
rem  Django serverini va ngrok tunnelini bitta bosishda ishga tushiradi.
rem  Ikkita yangi oyna ochiladi:
rem     "Xozmag - Django"  - saytning o'zi (port 8000)
rem     "Xozmag - ngrok"   - internetga chiqaradigan tunnel
rem  To'xtatish uchun shu ikkala oynani yopish kifoya.
rem ---------------------------------------------------------------

set "PORT=8000"
set "DOMEN=roughy-outgoing-iguana.ngrok-free.app"

rem --- Loyiha papkasi: shu fayl yonida manage.py bo'lsa o'sha, aks holda D: dagisi
set "LOYIHA=%~dp0"
if not exist "%LOYIHA%manage.py" set "LOYIHA=D:\ulugbek_xozmag\"
if not exist "%LOYIHA%manage.py" (
    echo XATO: manage.py topilmadi.
    echo Loyiha papkasi ko'chirilgan bo'lsa, shu faylni o'sha papkaga qo'ying.
    pause
    exit /b 1
)
cd /d "%LOYIHA%"

rem --- Python bormi
py --version >nul 2>&1
if errorlevel 1 (
    echo XATO: python topilmadi. Python o'rnatilganini tekshiring.
    pause
    exit /b 1
)

rem --- ngrok.exe ni qidiramiz
set "NGROK=D:\asosiy\ngrok.exe"
if not exist "%NGROK%" set "NGROK=%LOYIHA%ngrok.exe"
if not exist "%NGROK%" for %%i in (ngrok.exe) do set "NGROK=%%~$PATH:i"
if not exist "%NGROK%" (
    echo XATO: ngrok.exe topilmadi.
    echo Uni D:\asosiy\ngrok.exe ga qo'ying yoki loyiha papkasiga nusxalang.
    pause
    exit /b 1
)

rem --- Port band bo'lsa server allaqachon ishlayapti
netstat -ano | findstr /r /c:":%PORT% .*LISTENING" >nul
if not errorlevel 1 (
    echo Diqqat: %PORT% porti allaqachon band - server ishlayotgan bo'lishi mumkin.
    echo Eski oynalarni yopib, shu faylni qaytadan ishga tushiring.
    pause
    exit /b 1
)

echo Django ishga tushmoqda...
start "Xozmag - Django" cmd /k py manage.py runserver 0.0.0.0:%PORT%
timeout /t 4 /nobreak >nul

echo ngrok ishga tushmoqda...
start "Xozmag - ngrok" "%NGROK%" http %PORT% --url https://%DOMEN%
timeout /t 4 /nobreak >nul

echo Brauzer ochilmoqda...
start "" "https://%DOMEN%"

echo.
echo ====================================================
echo  Sayt tayyor:  https://%DOMEN%
echo  Shu kompyuterda: http://127.0.0.1:%PORT%
echo.
echo  Birinchi kirishda ngrok ogohlantirish sahifasi chiqsa,
echo  "Visit Site" tugmasini bosing.
echo.
echo  To'xtatish: "Xozmag - Django" va "Xozmag - ngrok"
echo  oynalarini yoping.
echo ====================================================
timeout /t 8
