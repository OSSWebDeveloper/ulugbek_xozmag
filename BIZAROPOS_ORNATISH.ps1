param([string]$Python = '')
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
if (-not $Python) { $Python = (& py -c 'import sys; print(sys.executable)').Trim() }
$Python = [IO.Path]::GetFullPath($Python)
$pythonw = Join-Path (Split-Path $Python) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonw)) { throw 'pythonw.exe topilmadi' }
& $Python -m pip install -r (Join-Path $root 'requirements-server.txt') openpyxl
if ($LASTEXITCODE -ne 0) { throw 'Kutubxonalar ornatilmadi' }
& $Python (Join-Path $root 'manage.py') migrate --noinput
if ($LASTEXITCODE -ne 0) { throw 'Baza migratsiyasi bajarilmadi' }
& $Python (Join-Path $root 'manage.py') standart_akkauntlar
if ($LASTEXITCODE -ne 0) { throw 'Standart akkauntlar yaratilmadi' }
$gitPath = (Get-Command git.exe).Source
$startFile = Join-Path $root 'BizaroPOS.vbs'
$vbs = @"
Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = "$root"
shell.Environment("PROCESS")("BIZARO_GIT") = "$gitPath"
shell.Run """$pythonw"" ""$root\bizaropos_server.py""", 0, False
"@
[IO.File]::WriteAllText($startFile, $vbs, [Text.Encoding]::Unicode)
$shell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcut = $shell.CreateShortcut((Join-Path $desktop 'BizaroPOS.lnk'))
$shortcut.TargetPath = Join-Path $env:WINDIR 'System32\wscript.exe'
$shortcut.Arguments = '"' + $startFile + '"'
$shortcut.WorkingDirectory = $root
$shortcut.IconLocation = (Join-Path $root 'static\img\bizaropos.ico') + ',0'
$shortcut.Description = 'BizaroPOS — asosiy kassa va Wi-Fi serveri (5555)'
$shortcut.Save()
# Pythonw.exe worker ham shu portda tinglaydi. Shuning uchun qoidani
# python.exe bilan cheklamaymiz; faqat Private LAN + LocalSubnet + TCP 5555.
# Windows Firewall qoidasini o'rnatish Administrator huquqini talab qiladi.
$rule = 'BizaroPOS-LAN-5555'
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'O‘rnatishni administrator PowerShell orqali boshlang: LAN firewall qoidasini yaratish uchun ruxsat kerak.'
}
if (Get-NetFirewallRule -Name $rule -ErrorAction SilentlyContinue) {
    Remove-NetFirewallRule -Name $rule
}
New-NetFirewallRule -Name $rule -DisplayName 'BizaroPOS Wi-Fi server 5555' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5555 -RemoteAddress LocalSubnet -Profile Private | Out-Null
Write-Output ('Tayyor: ' + (Join-Path $desktop 'BizaroPOS.lnk'))
