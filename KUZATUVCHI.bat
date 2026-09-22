@echo off
chcp 65001 >nul
title Xozmag - kuzatuvchi

rem Sayt (port 8000) va ngrok tunnelini kuzatib turadi.
rem Biror biri o'chib qolsa - qayta ishga tushiradi.
rem Hamma voqea: D:\ulugbek_xozmag\kuzatuv.log
rem To'xtatish: shu oynani yopish kifoya.

powershell -NoProfile -ExecutionPolicy Bypass -File "D:\ulugbek_xozmag\kuzatuvchi.ps1"
pause
