@echo off
chcp 65001 >nul
setlocal
set "XOZMAG_INSTALLER=%~f0"
rem BizaroPOS v3.9.20 - admin UAC automatically requested when double-clicked.
rem Only this process uses PowerShell ExecutionPolicy Bypass.
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$id=[Security.Principal.WindowsIdentity]::GetCurrent(); $principal=New-Object Security.Principal.WindowsPrincipal($id); if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){ try { $q=[char]34; $argsText='/d /c '+$q+$q+$env:XOZMAG_INSTALLER+$q+$q; $child=Start-Process -FilePath $env:ComSpec -ArgumentList $argsText -Verb RunAs -Wait -PassThru -ErrorAction Stop; exit $child.ExitCode } catch { Write-Host 'Administrator ruxsati berilmadi yoki ishga tushirishda xato.' -ForegroundColor Red; exit 1 } }; $src=[IO.File]::ReadAllText($env:XOZMAG_INSTALLER,[Text.Encoding]::UTF8); $mark=[char]58+'PS_SCRIPT_START'; $i=$src.LastIndexOf($mark); if($i -lt 0){throw 'Installer script missing'}; Invoke-Expression $src.Substring($i+$mark.Length)"
set "RESULT=%ERRORLEVEL%"
echo.
pause
exit /b %RESULT%
:PS_SCRIPT_START
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$repo = 'https://github.com/OSSWebDeveloper/ulugbek_xozmag.git'
$gitWeb = 'https://git-scm.com/downloads/win'
$serverPath = Join-Path $env:LOCALAPPDATA 'BizaroPOS-Server'
$installerVersion = '3.9.20'

function Status([string]$msg) { Write-Host ('  ' + $msg) -ForegroundColor Cyan }
function Stop-Setup([string]$msg) { throw $msg }
function Command-Path([string]$name) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}
function Refresh-Path {
    $env:PATH = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
}
function Is-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($id)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
function Require-Admin {
    if (-not (Is-Admin)) { Stop-Setup 'O`rnatish uchun ushbu faylni sichqonchaning o`ng tugmasi orqali "Run as administrator" bilan oching.' }
}
function Ensure-Winget {
    if (-not (Command-Path 'winget.exe')) {
        Stop-Setup 'winget topilmadi. Microsoft App Installer dasturini o`rnating yoki Windows Package Manager (winget) ni yangilang.'
    }
}
function Ensure-Git {
    Refresh-Path
    $git = Command-Path 'git.exe'
    if (-not $git) {
        $default = Join-Path $env:ProgramFiles 'Git\cmd\git.exe'
        if (Test-Path $default) { $git = $default }
    }
    if (-not $git) {
        Ensure-Winget
        Status 'Git avtomatik o`rnatilmoqda...'
        & winget.exe install --id Git.Git --exact --source winget --silent --accept-package-agreements --accept-source-agreements --disable-interactivity | Out-Host
        if ($LASTEXITCODE -ne 0) { Stop-Setup 'Git o`rnatilmadi.' }
        Refresh-Path
        $git = Command-Path 'git.exe'
        if (-not $git) {
            $default = Join-Path $env:ProgramFiles 'Git\cmd\git.exe'
            if (Test-Path $default) { $git = $default }
        }
    }
    if (-not $git) { Stop-Setup ('Git topilmadi: ' + $gitWeb) }
    return $git
}
function Ensure-Python {
    Refresh-Path
    $p = Command-Path 'py.exe'
    if ($p) {
        $null = & $p -3.13 -c 'import sys; print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0) { return @($p,'-3.13') }
    }
    $p = Command-Path 'python.exe'
    if ($p) {
        $v = & $p -c 'import sys; print(sys.version_info[:2] == (3,13))' 2>$null
        if ($v -eq 'True') { return @($p) }
    }
    Ensure-Winget
    Status 'Python 3.13 avtomatik o`rnatilmoqda...'
    & winget.exe install --id Python.Python.3.13 --exact --source winget --silent --accept-package-agreements --accept-source-agreements --disable-interactivity | Out-Host
    if ($LASTEXITCODE -ne 0) { Stop-Setup 'Python 3.13 o`rnatilmadi.' }
    Refresh-Path
    $p = Command-Path 'py.exe'
    if ($p) {
        $null = & $p -3.13 -c 'import sys; print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0) { return @($p,'-3.13') }
    }
    $python = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'
    if (Test-Path $python) { return @($python) }
    Stop-Setup 'Python o`rnatildi, lekin terminal uni topolmadi. Kompyuterni qayta ishga tushirib, faylni qayta oching.'
}
function Run-Python([string[]]$python, [string[]]$arguments) {
    if ($python.Count -gt 1) { & ($python[0]) $python[1] @arguments }
    else { & ($python[0]) @arguments }
    if ($LASTEXITCODE -ne 0) { Stop-Setup ('Python amali xato berdi: ' + ($arguments -join ' ')) }
}
function Server-Install {
    Require-Admin
    Status 'SERVER KASSA (GitHub main branch)' 
    $git = Ensure-Git
    $python = @(Ensure-Python)
    $freshInstall = -not (Test-Path $serverPath)
    if ($freshInstall) {
        Status ('GitHub dan loyiha olinmoqda: ' + $serverPath)
        & $git clone --branch main $repo $serverPath
        if ($LASTEXITCODE -ne 0) { Stop-Setup 'GitHub dan dastur yuklab bo`lmadi.' }
    } elseif (Test-Path (Join-Path $serverPath '.git')) {
        # O'rnatuvchi qayta ochilganda eski kodda qolib ketmasin.
        # Mahalliy kod, foydalanuvchi bazasi va qurilma fayllari saqlanadi.
        Status 'Mavjud server kodi GitHub main bilan tekshirilmoqda...'
        & $git -c ('safe.directory=' + $serverPath) -C $serverPath fetch origin main
        if ($LASTEXITCODE -ne 0) { Stop-Setup 'GitHub yangilanishini olib bo`lmadi.' }
        $current = (& $git -c ('safe.directory=' + $serverPath) -C $serverPath rev-parse HEAD).Trim()
        $latest = (& $git -c ('safe.directory=' + $serverPath) -C $serverPath rev-parse FETCH_HEAD).Trim()
        if ($LASTEXITCODE -ne 0) { Stop-Setup 'Git holatini aniqlab bo`lmadi.' }
        if ($current -ne $latest) {
            & $git -c ('safe.directory=' + $serverPath) -C $serverPath merge-base --is-ancestor $current $latest
            if ($LASTEXITCODE -ne 0) {
                Stop-Setup 'Mahalliy branch GitHub main dan farq qiladi. Avval zaxira olib, Git holatini qo`lda tekshiring.'
            }
            # Only tracked local code changes block updates; untracked runtime files stay intact.
            $changed = @(& $git -c ('safe.directory=' + $serverPath) -C $serverPath status --porcelain --untracked-files=no -- . ':(exclude)db.sqlite3')
            if ($LASTEXITCODE -ne 0) { Stop-Setup 'Mahalliy fayllarni tekshirib bo`lmadi.' }
            if ($changed.Count -gt 0 -and ($changed -join '').Trim()) {
                Stop-Setup 'Mahalliy kodda saqlanmagan o`zgarishlar bor. Hech narsa o`chirilmagan.'
            }
            $diff = @(& $git -c ('safe.directory=' + $serverPath) -C $serverPath diff --name-only $current $latest)
            if ($LASTEXITCODE -ne 0) { Stop-Setup 'Yangilanish fayllarini tekshirib bo`lmadi.' }
            if (@($diff | Where-Object { $_ -eq 'db.sqlite3' -or $_ -eq '.secret_key' -or $_ -like 'qurilmalar_data/*' -or $_ -like 'qurilma_drivers/*' }).Count -gt 0) {
                Stop-Setup 'GitHub yangilanishi bazaga yoki qurilma fayllariga tegmoqda. Xavfsizlik uchun to`xtatildi.'
            }
            # Ishlayotgan serverni foydalanuvchi tray menyusidan yopishi kerak.
            $listener = Get-NetTCPConnection -LocalPort 5555 -State Listen -ErrorAction SilentlyContinue
            if ($listener) { Stop-Setup 'Avval tray menyusidan BizaroPOS serverini yoping, so`ng o`rnatuvchini qayta oching.' }
            $db = Join-Path $serverPath 'db.sqlite3'
            if (Test-Path $db) {
                $backupFolder = Join-Path $serverPath 'qurilmalar_data\server\zaxira'
                New-Item -ItemType Directory -Path $backupFolder -Force | Out-Null
                $backup = Join-Path $backupFolder ('oldindan-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.sqlite3')
                $pyexe = if ($python.Count -gt 1) { (& ($python[0]) $python[1] -c 'import sys; print(sys.executable)').Trim() } else { $python[0] }
                # Avoid nested CMD -> PowerShell -> Python quotes: execute a temporary .py file.
                $backupScript = Join-Path $env:TEMP ('bizaropos-backup-' + [guid]::NewGuid().ToString('N') + '.py')
                $backupCode = @'
import sqlite3
import sys
source_path, dest_path = sys.argv[1:3]
with sqlite3.connect(source_path) as source:
    with sqlite3.connect(dest_path) as destination:
        source.backup(destination)
        result = destination.execute('PRAGMA integrity_check').fetchone()[0]
        if result != 'ok':
            raise RuntimeError('Backup integrity check failed: ' + result)
print('SQLite backup OK')
'@
                try {
                    [IO.File]::WriteAllText($backupScript, $backupCode, [Text.Encoding]::UTF8)
                    & $pyexe $backupScript $db $backup
                    if ($LASTEXITCODE -ne 0) { Stop-Setup 'Baza zaxirasini yaratib bo`lmadi. Yangilash to`xtatildi.' }
                } finally {
                    Remove-Item -LiteralPath $backupScript -Force -ErrorAction SilentlyContinue
                }
                Status ('Baza zaxiralandi: ' + $backup)
            }
            Status 'GitHub main dagi so`nggi kod o`rnatilmoqda...'
            & $git -c ('safe.directory=' + $serverPath) -C $serverPath merge --ff-only $latest
            if ($LASTEXITCODE -ne 0) { Stop-Setup 'GitHub main kodi birlashtirilmadi.' }
        } else {
            Status 'Dastur kodi allaqachon yangilangan.'
        }
    } else { Stop-Setup ('Papka mavjud, lekin Git loyihasi emas: ' + $serverPath) }
    # GitHub dagi sinov bazasini yangi do`kon bazasi sifatida ishlatmaymiz.
    if ($freshInstall -and (Test-Path (Join-Path $serverPath 'db.sqlite3'))) {
        $importedDb = Join-Path $serverPath 'db.sqlite3'
        $oldFolder = Join-Path $env:LOCALAPPDATA 'BizaroPOS-Imported-DB'
        New-Item -Path $oldFolder -ItemType Directory -Force | Out-Null
        $saved = Join-Path $oldFolder ('repo-db-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.sqlite3')
        Move-Item -LiteralPath $importedDb -Destination $saved
        Status ('GitHub bilan kelgan baza arxivlandi: ' + $saved)
    }
    Push-Location $serverPath
    try {
        Status 'Server uchun Django va boshqa kutubxonalar o`rnatilmoqda...'
        Run-Python $python @('-m','pip','install','-r','requirements-server.txt','openpyxl')
        Status 'Baza migratsiyalari bajarilmoqda...'
        Run-Python $python @('manage.py','migrate','--noinput')
        $accountCommand = Join-Path $serverPath 'qarz\management\commands\standart_akkauntlar.py'
        if (-not (Test-Path $accountCommand)) {
            Stop-Setup 'GitHub main kodi eskirgan: standart_akkauntlar.py yo`q. O`rnatuvchini qayta ishga tushiring.'
        }
        Status 'Boshlangich server va kassa akkauntlari tekshirilmoqda...'
        Run-Python $python @('manage.py','standart_akkauntlar')
        Status 'Serverga birinchi kirish: server / server (parolni darhol almashtiring).'
        Status 'Ikkinchi kassaga birinchi kirish: kassa / kassa (parolni darhol almashtiring).'
        Status 'Avval yaratilgan akkauntlarning parollari o`zgartirilmaydi.'
        # Server uchun kassa paketidagi Windows Python runtime tayyorlanadi.
        # GitHub dagi dastur kodida bu ZIP saqlanmaydi.
        $drivers = Join-Path $serverPath 'qurilma_drivers\kassa'
        $runtimeZip = Join-Path $drivers 'python.zip'
        $trayDeps = Join-Path $drivers 'tray_deps'
        New-Item -Path $drivers -ItemType Directory -Force | Out-Null
        if (-not (Test-Path $runtimeZip)) {
            if (-not [Environment]::Is64BitOperatingSystem) { Stop-Setup 'Ikkinchi kassa runtime faqat Windows 64-bit uchun.' }
            Status 'Ikkinchi kassa uchun Python runtime tayyorlanmoqda...'
            if ($python.Count -gt 1) { $pythonVersion = (& ($python[0]) $python[1] -c 'import sys; print(sys.version.split()[0])').Trim() }
            else { $pythonVersion = (& ($python[0]) -c 'import sys; print(sys.version.split()[0])').Trim() }
            if (-not $pythonVersion -or $pythonVersion -notmatch '^3\.13\.\d+$') { Stop-Setup ('Python versiyasini aniqlab bo`lmadi: ' + $pythonVersion) }
            $runtimeUrl = 'https://www.python.org/ftp/python/' + $pythonVersion + '/python-' + $pythonVersion + '-embed-amd64.zip'
            try { Invoke-WebRequest -UseBasicParsing -Uri $runtimeUrl -OutFile ($runtimeZip + '.tmp') -TimeoutSec 180; Move-Item -LiteralPath ($runtimeZip + '.tmp') -Destination $runtimeZip -Force }
            catch { Stop-Setup ('Rasmiy Python runtime yuklab bo`lmadi: ' + $runtimeUrl + '. Kassa yordamchisi uchun runtime kerak.') }
        }
        if (-not (Test-Path (Join-Path $trayDeps 'pystray'))) {
            Status 'Kassa tray kutubxonalari tayyorlanmoqda...'
            Run-Python $python @('-m','pip','install','--target',$trayDeps,'pystray==0.19.5','Pillow>=12,<14')
        }
        Status 'Windows yorlig`i va mahalliy tarmoq ruxsati sozlanmoqda...'
        $pyexe = if ($python.Count -gt 1) { (& ($python[0]) $python[1] -c 'import sys; print(sys.executable)').Trim() } else { $python[0] }
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $serverPath 'BIZAROPOS_ORNATISH.ps1') -Python $pyexe
        if ($LASTEXITCODE -ne 0) { Stop-Setup 'Server yorlig`ini yaratib bo`lmadi.' }
        Write-Host ''
        Write-Host '  SERVER KASSA ORNATILDI.' -ForegroundColor Green
        Write-Host '  Ish stolidagi BizaroPOS yorlig`ini oching.'
        Write-Host '  Manzil: http://127.0.0.55:5555/'
        Write-Host '  Eslatma: kassir uchun maxsus ZIP paketni server yaratadi.'
    } finally { Pop-Location }
}
function Login-And-Download([string]$base,[string]$username,[string]$password,[string]$zip) {
    $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
    $login = Invoke-WebRequest -Uri ($base + '/kirish/') -WebSession $session -UseBasicParsing -TimeoutSec 20
    $match = [regex]::Match($login.Content,'name=["'']csrfmiddlewaretoken["'']\s+value=["'']([^"'']+)')
    if (-not $match.Success) { Stop-Setup 'Server login sahifasidan CSRF kaliti topilmadi.' }
    $csrf = $match.Groups[1].Value
    $body = @{ username=$username; password=$password; csrfmiddlewaretoken=$csrf; next='/' }
    $null = Invoke-WebRequest -Uri ($base + '/kirish/') -Method POST -Body $body -WebSession $session -UseBasicParsing -TimeoutSec 25 -Headers @{Referer=($base+'/kirish/')}
    # For authenticated views, wrong passwords redirect back to /kirish/.
    $null = Invoke-WebRequest -Uri ($base + '/qurilmalar/kassa-agent/yukla/') -Method POST -Body @{csrfmiddlewaretoken=$csrf} -WebSession $session -UseBasicParsing -TimeoutSec 120 -Headers @{Referer=($base+'/qurilmalar/')} -OutFile $zip
    $stream = [IO.File]::OpenRead($zip)
    try {
        $h = New-Object byte[] 2
        if ($stream.Read($h,0,2) -ne 2 -or $h[0] -ne 80 -or $h[1] -ne 75) {
            Stop-Setup 'ZIP o`rniga HTML yoki xato javobi qaytdi. Loginni, serverni va runtime mavjudligini tekshiring.'
        }
    } finally { $stream.Dispose() }
}
function Cashier-Install {
    Require-Admin
    Status 'IKKINCHI KASSA - USB PRINTER YORDAMCHISI'
    Write-Host '  Server avval ishga tushirilgan bo`lishi kerak.'
    $base = Read-Host '  Server manzili (masalan http://WIN-HS2MGB9MV4U:5555)'
    $base = $base.Trim().TrimEnd('/')
    if ($base -notmatch '^https?://[A-Za-z0-9.\-]+(:\d{2,5})?$') {
        Stop-Setup 'Server manzilini to`liq yozing: http://SERVER-NOMI:5555'
    }
    Write-Host '  Faqat ishonchli mahalliy Wi-Fi/LAN tarmog`ida foydalaning.' -ForegroundColor Yellow
    Write-Host '  Birinchi martada server brauzeridan kassa / kassa bilan kiring va login/parolni yangilang.' -ForegroundColor Yellow
    Write-Host '  Endi shu yangilangan login/parolni kiriting. Dastlabki standart parol bilan printer paketini olish bloklanadi.' -ForegroundColor Yellow
    $user = Read-Host '  Ikkinchi kassa login nomi'
    if ([string]::IsNullOrWhiteSpace($user)) { Stop-Setup 'Kassa loginini kiriting.' }
    $secure = Read-Host '  Ikkinchi kassa paroli' -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $password = ''
    try { $password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
    $target = Join-Path $env:TEMP ('BizaroPOS-Install-' + [guid]::NewGuid().ToString('N'))
    New-Item -Path $target -ItemType Directory -Force | Out-Null
    try {
        $zip = Join-Path $target 'kassa.zip'
        Status 'Serverdan kassirga biriktirilgan paket yuklab olinmoqda...'
        Login-And-Download $base $user $password $zip
        $password = $null
        Expand-Archive -LiteralPath $zip -DestinationPath (Join-Path $target 'paket') -Force
        # Serverning sozlamalaridagi eski IP o`rniga foydalanuvchi kiritgan manzil ishlatiladi.
        $configFile = Join-Path $target 'paket\kassa.json'
        $config = Get-Content -LiteralPath $configFile -Raw | ConvertFrom-Json
        $config.url = $base
        $config | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $configFile -Encoding UTF8
        if (-not (Test-Path (Join-Path $target 'paket\ORNATISH.ps1'))) {
            Stop-Setup 'Paketda ORNATISH.ps1 topilmadi.'
        }
        Status 'USB kassa yordamchisi o`rnatilmoqda...'
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $target 'paket\ORNATISH.ps1')
        if ($LASTEXITCODE -ne 0) { Stop-Setup 'Kassa yordamchisi o`rnatilmadi.' }
        Write-Host ''
        Write-Host '  IKKINCHI KASSA TAYYOR!' -ForegroundColor Green
        Write-Host '  Ish stolida BizaroPOS Kassa yorlig`i yaratildi.'
        Start-Process $base
    } finally {
        $password = $null
        Remove-Item -LiteralPath $target -Force -Recurse -ErrorAction SilentlyContinue
    }
}
try {
    Clear-Host
    Write-Host '====================================================' -ForegroundColor Cyan
    Write-Host ('        BizaroPOS - AVTOMATIK ORNATGICH v' + $installerVersion) -ForegroundColor White
    Write-Host '====================================================' -ForegroundColor Cyan
    Write-Host '  1 - Asosiy SERVER kassa (Django + Git + Python)' -ForegroundColor Green
    Write-Host '  2 - IKKINCHI kassa (USB printer yordamchisi)' -ForegroundColor Green
    Write-Host '  0 - Chiqish'
    $mode = Read-Host '  Tanlang (1/2/0)'
    switch ($mode) {
        '1' { Server-Install }
        '2' { Cashier-Install }
        '0' { return }
        default { Stop-Setup 'Noto`g`ri tanlov. Qayta oching.' }
    }
} catch {
    Write-Host ''
    Write-Host ('  XATO: ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host '  Xatoni tekshirib, shu faylni qayta ishga tushiring.' -ForegroundColor Yellow
    exit 1
}
