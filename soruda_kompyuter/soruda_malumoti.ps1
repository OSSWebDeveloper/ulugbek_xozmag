<#
Soruda tinting system ma'lumotlarini yig'ish. Faqat O'QIYDI - Soruda'ning
hech bir fayli o'zgartirilmaydi va o'chirilmaydi.

Rang mashinasi yonidagi kompyuterda (fleshkadan) ishga tushiriladi. Natija -
shu fayl yonida soruda_<KOMPYUTER>_<sana>.zip:

  jurnal.txt            - dastur qayerda, qaysi fayllar topildi, printerlar
  fayllar_royxati.csv   - Soruda papkasidagi hamma fayllar (nomi, hajmi, sanasi)
  yaqinda_ozgargan.csv  - oxirgi soatlarda o'zgargan fayllar
  fayllar\...           - ma'lumot fayllarining nusxasi (palitra, rang kodlari,
                          formulalar, yozuvlar); dastur fayllari (exe, dll,
                          rasmlar) olinmaydi

Soruda dasturi kompyuterga to'g'ridan-to'g'ri o'rnatilgan: rang kodlari,
palitra va har bir tayyorlangan bo'yoq yozuvi shu kompyuterdagi fayllarda.
Ularni ko'rgach Xozmag katalogi Soruda'ning o'z kodlari bilan to'ldiriladi va
tayyorlangan bo'yoq cheki Wi-Fi orqali bazaga o'zi yuboriladigan qilinadi.

Maslahat: avval Soruda'da bitta bo'yoq tayyorlang (yoki sinov qiling), keyin
ishga tushiring - o'sha yozuv tushgan fayl "yaqinda o'zgargan" ro'yxatida chiqadi.
#>
param(
    [int]$Soat = 3,                  # necha soat ichida o'zgargan fayllar qidiriladi
    [int]$EngKattaMb = 300,          # bundan katta fayl nusxalanmaydi
    [string[]]$QoshimchaPapka = @()  # qo'lda ko'rsatilgan Soruda papkasi (topilmasa)
)

$ErrorActionPreference = 'SilentlyContinue'
$bu = Split-Path -Parent $MyInvocation.MyCommand.Path
$vaqt = Get-Date -Format 'yyyyMMdd_HHmm'
$nom = "soruda_$($env:COMPUTERNAME)_$vaqt"
$ish = Join-Path $env:TEMP $nom
New-Item -ItemType Directory -Force -Path $ish | Out-Null
$jurnal = Join-Path $ish 'jurnal.txt'

function Yoz([string]$matn, [string]$rang = 'Gray') {
    Write-Host $matn -ForegroundColor $rang
    Add-Content -Path $jurnal -Value $matn -Encoding UTF8
}

# Soruda | tinting | Xitoycha nomi (U+7D22 U+745E U+8FBE) | "rang aralashtirish" (U+8C03 U+8272)
$xitoy1 = -join [char[]](0x7D22, 0x745E, 0x8FBE)
$xitoy2 = -join [char[]](0x8C03, 0x8272)
$naqsh = "soruda|tinting|$xitoy1|$xitoy2"

$papkalar = New-Object System.Collections.Generic.List[string]
$exelar = New-Object System.Collections.Generic.List[string]

function PapkaQosh([string]$yol) {
    if (-not $yol -or -not (Test-Path -LiteralPath $yol -PathType Container)) { return }
    $yol = (Resolve-Path -LiteralPath $yol).Path.TrimEnd('\')
    # Shu skript turgan papka (nomida "soruda" bor) va uning nusxalari Soruda emas
    if ($yol -eq $bu.TrimEnd('\') -or $yol.StartsWith($bu.TrimEnd('\') + '\')) { return }
    if (Test-Path -LiteralPath (Join-Path $yol 'soruda_malumoti.ps1')) { return }
    # exe odatda bin/Release ichida, ma'lumot esa bir qavat yuqorida turadi
    if ((Split-Path -Leaf $yol) -match '^(bin|debug|release|x86|x64|program)$') {
        $yol = Split-Path -Parent $yol
    }
    if (-not $papkalar.Contains($yol)) { $papkalar.Add($yol) }
}

Yoz "Soruda ma'lumotlari yig'ilmoqda - $(Get-Date -Format 'dd.MM.yyyy HH:mm'), kompyuter $env:COMPUTERNAME" 'Cyan'

# ---------- 1. Ishlab turgan dastur ----------
Yoz ''
Yoz '== 1. Ishlab turgan dastur' 'Cyan'
# Brauzer oynasi sarlavhasida ham "Soruda" bo'lishi mumkin (Xozmag stansiyasi,
# ishlab chiqaruvchi sayti) - brauzerlar Soruda emas
$brauzerlar = '^(chrome|msedge|msedgewebview2|firefox|opera|browser|iexplore|brave|vivaldi|yandex|claude|electron)$'
Get-Process | Where-Object {
    $_.ProcessName -notmatch $brauzerlar -and
    ($_.MainWindowTitle -match $naqsh -or $_.ProcessName -match $naqsh -or ($_.Path -and $_.Path -match $naqsh))
} | ForEach-Object {
    Yoz ("  {0} | oyna: {1} | {2}" -f $_.ProcessName, $_.MainWindowTitle, $_.Path)
    if ($_.Path) { $exelar.Add($_.Path); PapkaQosh (Split-Path -Parent $_.Path) }
}

# ---------- 2. Yorliqlar (ish stoli, Boshlash menyusi) ----------
Yoz ''
Yoz '== 2. Yorliqlar' 'Cyan'
$ws = New-Object -ComObject WScript.Shell
$joylar = @([Environment]::GetFolderPath('Desktop'), (Join-Path $env:PUBLIC 'Desktop'),
            (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu'),
            (Join-Path $env:ProgramData 'Microsoft\Windows\Start Menu'))
foreach ($joy in $joylar) {
    Get-ChildItem -LiteralPath $joy -Filter *.lnk -Recurse -Force | ForEach-Object {
        $maqsad = $ws.CreateShortcut($_.FullName).TargetPath
        if ($_.Name -match $naqsh -or $maqsad -match $naqsh) {
            Yoz ("  {0} -> {1}" -f $_.FullName, $maqsad)
            if ($maqsad) { $exelar.Add($maqsad); PapkaQosh (Split-Path -Parent $maqsad) }
        }
    }
}

# ---------- 3. Papka nomlari bo'yicha ----------
Yoz ''
Yoz '== 3. Papkalar' 'Cyan'
$disklar = Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | ForEach-Object { $_.DeviceID + '\' }
$ildizlar = @($env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:ProgramData, $env:PUBLIC) + $disklar
foreach ($ildiz in ($ildizlar | Where-Object { $_ } | Sort-Object -Unique)) {
    Get-ChildItem -LiteralPath $ildiz -Directory -Force | ForEach-Object {
        if ($_.Name -match $naqsh) { PapkaQosh $_.FullName }
        # bir qavat chuqurroq: C:\Program Files (x86)\Kompaniya\Soruda
        Get-ChildItem -LiteralPath $_.FullName -Directory -Force | Where-Object { $_.Name -match $naqsh } |
            ForEach-Object { PapkaQosh $_.FullName }
    }
}
foreach ($p in $QoshimchaPapka) { PapkaQosh $p }
# Ichma-ich papkalar bir marta olinsin: C:\Soruda bo'lsa C:\Soruda\Data alohida emas
$papkalar = @($papkalar | Sort-Object Length | Where-Object {
    $yol = $_; -not ($papkalar | Where-Object { $_ -ne $yol -and $yol.StartsWith($_ + '\') })
})
if ($papkalar.Count -eq 0) {
    Yoz '  Soruda papkasi topilmadi. Soruda ochiq holda qayta ishga tushiring yoki' 'Yellow'
    Yoz '  papkani qo''lda bering: soruda_malumoti.ps1 -QoshimchaPapka "C:\...\Soruda"' 'Yellow'
}
foreach ($p in $papkalar) { Yoz "  $p" 'Green' }

# ---------- 4. Fayllar ro'yxati va ma'lumot fayllarining nusxasi ----------
Yoz ''
Yoz "== 4. Ma'lumot fayllari" 'Cyan'
# Dastur fayllari va rasmlar olinmaydi - qolgan hammasi (noma'lum kengaytmali
# formula fayllari ham) nusxalanadi
$olinmaydi = '\.(exe|dll|ocx|sys|msi|msp|cab|pdb|png|jpe?g|bmp|gif|ico|tiff?|wav|mp3|mp4|avi|wmv|ttf|otf|fon|chm|cur|ani|pak)$'
$royxat = @()
$nusxa = 0; $hajm = 0
for ($i = 0; $i -lt $papkalar.Count; $i++) {
    $papka = $papkalar[$i]
    $manzil = Join-Path $ish ("fayllar\{0}_{1}" -f ($i + 1), (Split-Path -Leaf $papka))
    Get-ChildItem -LiteralPath $papka -File -Recurse -Force | ForEach-Object {
        $royxat += [pscustomobject]@{ Fayl = $_.FullName; Hajm = $_.Length; Ozgargan = $_.LastWriteTime }
        if ($_.Name -match $olinmaydi -or $_.Length -gt ($EngKattaMb * 1MB)) { return }
        $nisbiy = $_.FullName.Substring($papka.Length).TrimStart('\')
        $qayerga = Join-Path $manzil $nisbiy
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $qayerga) | Out-Null
        try {
            Copy-Item -LiteralPath $_.FullName -Destination $qayerga -ErrorAction Stop
            $nusxa++; $hajm += $_.Length
        } catch {
            Yoz "  nusxa olinmadi (dastur ochiq ushlab turibdi?): $($_.Exception.Message)" 'Yellow'
        }
    }
}
$royxat | Export-Csv -LiteralPath (Join-Path $ish 'fayllar_royxati.csv') -NoTypeInformation -Encoding UTF8
Yoz ("  {0} ta fayl ro'yxatda, {1} tasi nusxalandi ({2:N1} MB)" -f $royxat.Count, $nusxa, ($hajm / 1MB))

foreach ($exe in ($exelar | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Sort-Object -Unique)) {
    $v = (Get-Item -LiteralPath $exe).VersionInfo
    Yoz ("  {0} | {1} | versiya {2} | {3}" -f $exe, $v.ProductName, $v.FileVersion, $v.CompanyName)
}

# ---------- 5. Yaqinda o'zgargan fayllar - chek qayerga yozilishini topish uchun ----------
Yoz ''
Yoz "== 5. Oxirgi $Soat soatda o'zgargan fayllar" 'Cyan'
$chegara = (Get-Date).AddHours(-$Soat)
# Brauzer keshi, Windows'ning o'z fayllari va h.k. - ularga kirilmaydi ham
$shovqin = '\\(Temp|Tmp|Cache|Caches|INetCache|WebCache|Microsoft\\Windows|Microsoft\\Edge|Microsoft\\Office|Google\\Chrome|Mozilla|Packages|CrashDumps|D3DSCache|NVIDIA|Intel|XozmagStansiya|node_modules|\.git|pip|npm-cache|site-packages)\\'

function YangiFayllar([string]$ildiz) {
    # Get-ChildItem -Recurse shovqinli papkalarni ham oxirigacha aylanib chiqardi;
    # bu yerda ular umuman ochilmaydi, havolalarga (junction) ham kirilmaydi
    $navbat = New-Object System.Collections.Generic.Queue[string]
    $navbat.Enqueue($ildiz)
    while ($navbat.Count -gt 0) {
        $papka = $navbat.Dequeue()
        if (($papka + '\') -match $shovqin) { continue }
        try {
            foreach ($yol in [IO.Directory]::EnumerateFiles($papka)) {
                $f = New-Object IO.FileInfo $yol
                if ($f.LastWriteTime -ge $chegara) { $f }
            }
            foreach ($ichki in [IO.Directory]::EnumerateDirectories($papka)) {
                if (([IO.File]::GetAttributes($ichki) -band [IO.FileAttributes]::ReparsePoint) -eq 0) {
                    $navbat.Enqueue($ichki)
                }
            }
        } catch { }
    }
}

$qidiriladi = @($papkalar) + @($env:ProgramData, $env:PUBLIC)
Get-ChildItem -LiteralPath 'C:\Users' -Directory -Force | ForEach-Object {
    $qidiriladi += (Join-Path $_.FullName 'AppData'); $qidiriladi += (Join-Path $_.FullName 'Documents')
}
$yangilar = foreach ($joy in ($qidiriladi | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Sort-Object -Unique)) {
    YangiFayllar $joy
}
$yangilar = @($yangilar | Sort-Object FullName -Unique | Sort-Object LastWriteTime -Descending)
$yangilar | Select-Object LastWriteTime, Length, FullName |
    Export-Csv -LiteralPath (Join-Path $ish 'yaqinda_ozgargan.csv') -NoTypeInformation -Encoding UTF8
Yoz ("  {0} ta fayl" -f $yangilar.Count)
# Soruda papkasidan tashqarida yozilgan yangi fayllar faqat NOMI Soruda'ga
# tegishli bo'lsa nusxalanadi. Qolganlari faqat ro'yxatda: boshqa dasturlarning
# fayllari (Telegram sessiyasi, parollar va h.k.) zipga tushmasin.
foreach ($f in $yangilar) {
    if ($f.FullName -notmatch $naqsh -or $f.FullName -match $olinmaydi -or $f.Length -gt 50MB) { continue }
    if ($papkalar | Where-Object { $f.FullName.StartsWith($_ + '\') }) { continue }
    $qayerga = Join-Path $ish ('yaqinda\' + ($f.FullName -replace '^([A-Za-z]):', '$1'))
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $qayerga) | Out-Null
    Copy-Item -LiteralPath $f.FullName -Destination $qayerga
}
$yangilar | Select-Object -First 15 | ForEach-Object {
    Yoz ("  {0:dd.MM HH:mm}  {1,10}  {2}" -f $_.LastWriteTime, $_.Length, $_.FullName)
}

# ---------- 6. Ma'lumotlar bazasi xizmatlari ----------
# Soruda formulalari va yozuvlarini SQL Server'da saqlasa ular Soruda papkasida
# bo'lmaydi, fayli esa server ishlab turganda ochilmaydi - shuning uchun
# jadvallar shu yerning o'zida o'qilib CSV ga yoziladi (faqat SELECT).
Yoz ''
Yoz "== 6. Ma'lumotlar bazasi xizmatlari" 'Cyan'
Get-Service | Where-Object { $_.Name -match 'SQL|MySQL|Firebird|Postgre|Interbase' } | ForEach-Object {
    Yoz ("  {0} | {1} | {2}" -f $_.Name, $_.DisplayName, $_.Status)
}

function JadvalniYoz($ulanish, [string]$sorov, [string]$fayl, [int]$chegara = 200000) {
    # Har qanday IDataReader bilan ishlaydi. Qaytaradi: yozilgan qatorlar soni.
    $buyruq = $ulanish.CreateCommand()
    $buyruq.CommandText = $sorov
    $buyruq.CommandTimeout = 300
    $oquvchi = $buyruq.ExecuteReader()
    $yozuvchi = New-Object IO.StreamWriter($fayl, $false, (New-Object Text.UTF8Encoding $true))
    try {
        $ustunlar = for ($i = 0; $i -lt $oquvchi.FieldCount; $i++) {
            '"' + $oquvchi.GetName($i).Replace('"', '""') + '"'
        }
        $yozuvchi.WriteLine(($ustunlar -join ','))
        $soni = 0
        while ($soni -lt $chegara -and $oquvchi.Read()) {
            $qator = for ($i = 0; $i -lt $oquvchi.FieldCount; $i++) {
                $qiymat = $oquvchi.GetValue($i)
                if ($qiymat -is [byte[]]) {
                    $qiymat = if ($qiymat.Length -le 4096) { 'base64:' + [Convert]::ToBase64String($qiymat) }
                              else { "<$($qiymat.Length) bayt>" }
                } elseif ($qiymat -is [datetime]) {
                    $qiymat = $qiymat.ToString('yyyy-MM-dd HH:mm:ss')
                }
                '"' + ([string]$qiymat).Replace('"', '""') + '"'
            }
            $yozuvchi.WriteLine(($qator -join ','))
            $soni++
        }
        return $soni
    } finally {
        $yozuvchi.Close()
        $oquvchi.Close()
    }
}

$serverlar = @()
Get-Service | Where-Object { $_.Name -match '^MSSQL' -and $_.Status -eq 'Running' } | ForEach-Object {
    if ($_.Name -eq 'MSSQLSERVER') { $serverlar += '.' }
    elseif ($_.Name -match '^MSSQL\$(.+)$') { $serverlar += ".\$($Matches[1])" }
}
if (Get-Command sqllocaldb -ErrorAction SilentlyContinue) {
    sqllocaldb info | Where-Object { $_.Trim() } | ForEach-Object { $serverlar += "(localdb)\$($_.Trim())" }
}
foreach ($server in $serverlar) {
    try {
        $ulanish = New-Object System.Data.SqlClient.SqlConnection "Server=$server;Integrated Security=True;Connect Timeout=8"
        $ulanish.Open()
        $buyruq = $ulanish.CreateCommand()
        $buyruq.CommandText = 'SELECT name FROM sys.databases WHERE database_id > 4'
        $oquvchi = $buyruq.ExecuteReader()
        $bazalar = @(while ($oquvchi.Read()) { $oquvchi.GetString(0) })
        $oquvchi.Close()
        foreach ($baza in $bazalar) {
            $ulanish.ChangeDatabase($baza)
            $buyruq = $ulanish.CreateCommand()
            $buyruq.CommandText = "SELECT s.name, t.name FROM sys.tables t JOIN sys.schemas s ON s.schema_id = t.schema_id"
            $oquvchi = $buyruq.ExecuteReader()
            $jadvallar = @(while ($oquvchi.Read()) { ,@($oquvchi.GetString(0), $oquvchi.GetString(1)) })
            $oquvchi.Close()
            $serverNomi = ($server -replace '[\\\.\(\)]', '_').Trim('_')
            if (-not $serverNomi) { $serverNomi = 'MSSQLSERVER' }
            $papka = Join-Path $ish ("sql\{0}\{1}" -f $serverNomi, ($baza -replace '[^\w\-]', '_'))
            New-Item -ItemType Directory -Force -Path $papka | Out-Null
            foreach ($j in $jadvallar) {
                $fayl = Join-Path $papka ("{0}.{1}.csv" -f $j[0], ($j[1] -replace '[^\w\-]', '_'))
                try {
                    $soni = JadvalniYoz $ulanish ("SELECT * FROM [{0}].[{1}]" -f $j[0].Replace(']', ']]'), $j[1].Replace(']', ']]')) $fayl
                    Yoz ("  {0} / {1} / {2}.{3}: {4} qator" -f $server, $baza, $j[0], $j[1], $soni)
                } catch {
                    Yoz ("  {0} / {1} / {2}: o'qilmadi - {3}" -f $server, $baza, $j[1], $_.Exception.Message) 'Yellow'
                }
            }
        }
        $ulanish.Close()
    } catch {
        Yoz ("  {0}: ulanib bo'lmadi - {1}" -f $server, $_.Exception.Message) 'Yellow'
    }
}

# ---------- 7. Printerlar - chek qaysi printerdan chiqadi ----------
Yoz ''
Yoz '== 7. Printerlar' 'Cyan'
Get-CimInstance Win32_Printer | ForEach-Object {
    Yoz ("  {0} | drayver: {1} | port: {2}{3}" -f $_.Name, $_.DriverName, $_.PortName, $(if ($_.Default) { ' | asosiy' } else { '' }))
}

# ---------- 8. Kompyuter va tarmoq ----------
Yoz ''
Yoz '== 8. Kompyuter' 'Cyan'
$os = Get-CimInstance Win32_OperatingSystem
Yoz ("  {0} | {1} {2}" -f $env:COMPUTERNAME, $os.Caption, $os.OSArchitecture)
ipconfig /all | Out-File -LiteralPath (Join-Path $ish 'ipconfig.txt') -Encoding UTF8
Get-NetConnectionProfile | ForEach-Object { Yoz ("  tarmoq: {0} | {1} | {2}" -f $_.Name, $_.InterfaceAlias, $_.NetworkCategory) }

# ---------- Zip ----------
$zip = Join-Path $bu "$nom.zip"
try {
    Compress-Archive -Path (Join-Path $ish '*') -DestinationPath $zip -Force -ErrorAction Stop
} catch {
    # Fleshka yozishga yopiq bo'lsa - ish stoliga
    $zip = Join-Path ([Environment]::GetFolderPath('Desktop')) "$nom.zip"
    Compress-Archive -Path (Join-Path $ish '*') -DestinationPath $zip -Force
}
Remove-Item -LiteralPath $ish -Recurse -Force
Yoz ''
if (Test-Path -LiteralPath $zip) {
    Write-Host "TAYYOR: $zip" -ForegroundColor Green
    Write-Host 'Shu faylni dasturchiga bering (fleshkada yoki Telegram orqali).' -ForegroundColor Green
} else {
    Write-Host 'Zip yaratilmadi - yuqoridagi xabarlarni suratga olib yuboring.' -ForegroundColor Red
}
