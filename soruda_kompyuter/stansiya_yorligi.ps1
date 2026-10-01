<#
Rang mashinasi kompyuterida ish stoliga "Rang stansiyasi" yorlig'ini yaratadi.

Yorliq brauzerni (Edge, bo'lmasa Chrome) alohida oynada ochadi:
  --app=...            manzil satri va tablar yo'q - oddiy dasturdek
  --kiosk-printing     chek so'ramasdan printerga ketadi (chop etish oynasi chiqmaydi)
  --user-data-dir=...  alohida profil: kompyuterdagi boshqa brauzer oynalariga
                       aralashmaydi, kirish (login) shu yerda eslab qolinadi

Stansiya Xozmag serverida turadi, kompyuter unga do'kon Wi-Fi'i orqali ulanadi.
Chek shu tarmoq orqali to'g'ridan-to'g'ri serverdagi bazaga yoziladi.
#>
param([Parameter(Mandatory = $true)][string]$Manzil)

$Manzil = $Manzil.Trim() -replace '^https?://', '' -replace '/.*$', ''
if ($Manzil -notmatch ':\d+$') { $Manzil += ':8000' }
$sayt = "http://$Manzil/rang/"

Write-Host "Server tekshirilmoqda: $sayt"
try {
    Invoke-WebRequest -Uri "http://$Manzil/kirish/" -UseBasicParsing -TimeoutSec 6 | Out-Null
    Write-Host '  Server topildi.' -ForegroundColor Green
} catch {
    Write-Host '  Server javob bermadi. Tekshiring: kompyuter Wi-Fi ga ulanganmi, server' -ForegroundColor Yellow
    Write-Host '  kompyuterida Xozmag ochiqmi, u yerda Windows "ruxsat" so''raganda ruxsat berilganmi.' -ForegroundColor Yellow
    Write-Host '  Yorliq baribir yaratiladi - server yoqilgach ishlaydi.' -ForegroundColor Yellow
}

$brauzer = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
             "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
             "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
             "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
             "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe") |
    Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $brauzer) {
    Write-Host 'Edge ham, Chrome ham topilmadi - yorliq yaratilmadi.' -ForegroundColor Red
    exit 1
}

$profil = Join-Path $env:LOCALAPPDATA 'XozmagStansiya'
$ws = New-Object -ComObject WScript.Shell
$yorliq = $ws.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Rang stansiyasi.lnk'))
$yorliq.TargetPath = $brauzer
$yorliq.Arguments = "--app=$sayt --kiosk-printing --no-first-run --user-data-dir=`"$profil`""
$yorliq.WorkingDirectory = Split-Path -Parent $brauzer
$yorliq.IconLocation = "$brauzer,0"
$yorliq.Description = 'Xozmag - rang mashinasi stansiyasi'
$yorliq.Save()

Write-Host ''
Write-Host "Ish stolida 'Rang stansiyasi' yorlig'i yaratildi:" -ForegroundColor Green
Write-Host "  $sayt" -ForegroundColor Green
Write-Host 'Birinchi ochilganda login va parol so''raladi - keyin eslab qoladi.'
