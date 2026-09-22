# Xozmag kuzatuvchisi
#
# Sayt va ngrok tunnelini kuzatib turadi. Biror biri o'chib qolsa qayta
# ishga tushiradi va hammasini `kuzatuv.log` ga yozib boradi.
#
# Ishga tushirish (KUZATUVCHI.bat shuni chaqiradi):
#   powershell -ExecutionPolicy Bypass -File D:\ulugbek_xozmag\kuzatuvchi.ps1
#
# To'xtatish: shu oynani yopish kifoya.

$ErrorActionPreference = 'SilentlyContinue'

# Kuzatuvchi ishlab turganda kompyuter o'zi uxlab qolmasin - aks holda
# sayt ham, tunnel ham o'chadi. Sozlamalarga tegilmaydi: bu faqat shu
# jarayon uchun, oyna yopilishi bilan bekor bo'ladi.
Add-Type -Name Quvvat -Namespace Win32 -MemberDefinition @'
[DllImport("kernel32.dll", SetLastError = true)]
public static extern uint SetThreadExecutionState(uint esFlags);
'@
# ES_CONTINUOUS (0x80000000) | ES_SYSTEM_REQUIRED (0x00000001)
[void][Win32.Quvvat]::SetThreadExecutionState([uint32]'0x80000001')

$loyiha = 'D:\ulugbek_xozmag'
$port   = 8000
$domen  = 'roughy-outgoing-iguana.ngrok-free.app'
$ngrok  = 'D:\asosiy\ngrok.exe'
$log    = Join-Path $loyiha 'kuzatuv.log'

$oraliq      = 30    # soniya - har qancha vaqtda tekshiriladi
$tashqiOraliq = 5    # daqiqa - tunnel tashqaridan qancha vaqtda bir tekshiriladi
$yurakOraliq  = 30   # daqiqa - "hammasi joyida" yozuvi

function Yoz([string]$matn) {
    $qator = '{0}  {1}' -f (Get-Date -Format 'dd.MM HH:mm:ss'), $matn
    Write-Host $qator
    Add-Content -Path $log -Value $qator -Encoding UTF8
}

function PortOchiqmi([int]$p) {
    $mijoz = New-Object Net.Sockets.TcpClient
    try {
        $natija = $mijoz.BeginConnect('127.0.0.1', $p, $null, $null)
        if (-not $natija.AsyncWaitHandle.WaitOne(2000)) { return $false }
        $mijoz.EndConnect($natija)
        return $true
    } catch {
        return $false
    } finally {
        $mijoz.Close()
    }
}

function TunnelTirikmi {
    # ngrok o'zining mahalliy API si: tunnel ro'yxatda bo'lsa - tirik
    try {
        $javob = Invoke-RestMethod -Uri 'http://127.0.0.1:4040/api/tunnels' -TimeoutSec 5
        foreach ($t in $javob.tunnels) {
            if ($t.public_url -like "*$domen*") { return $true }
        }
        return $false
    } catch {
        return $false
    }
}

function TashqaridanTekshir {
    # Haqiqiy tekshiruv: internet orqali sayt javob beradimi
    try {
        $javob = Invoke-WebRequest -Uri "https://$domen/" -UseBasicParsing -TimeoutSec 20 `
                                   -Headers @{'ngrok-skip-browser-warning' = '1'}
        return ($javob.StatusCode -ge 200 -and $javob.StatusCode -lt 400)
    } catch {
        $holat = $_.Exception.Response.StatusCode.value__
        # 302 (kirish sahifasiga yo'naltirish) ham yaxshi javob
        if ($holat -ge 200 -and $holat -lt 400) { return $true }
        Yoz ("Tashqi tekshiruv javobi: " + $(if ($holat) { $holat } else { $_.Exception.Message }))
        return $false
    }
}

function ServerniQoy {
    Yoz 'Sayt javob bermayapti - qayta ishga tushiryapman'
    Start-Process -FilePath 'cmd.exe' `
        -ArgumentList '/k', "title Xozmag - Django && py manage.py runserver 0.0.0.0:$port" `
        -WorkingDirectory $loyiha
}

function NgrokniQoy {
    Yoz 'ngrok tunneli yo''q - qayta ishga tushiryapman'
    Get-Process ngrok | Stop-Process -Force
    Start-Sleep -Seconds 3
    Start-Process -FilePath 'cmd.exe' `
        -ArgumentList '/k', "title Xozmag - ngrok && `"$ngrok`" http $port --url https://$domen" `
        -WorkingDirectory (Split-Path $ngrok)
}

# ---------------------------------------------------------------- kuzatuv
Yoz "===== Kuzatuv boshlandi (har $oraliq soniyada) ====="

$keyingiTashqi = (Get-Date).AddMinutes($tashqiOraliq)
$keyingiYurak  = (Get-Date).AddMinutes($yurakOraliq)
$ketmaKetXato  = 0

while ($true) {
    $sayt   = PortOchiqmi $port
    $tunnel = TunnelTirikmi

    if (-not $sayt) {
        ServerniQoy
        Start-Sleep -Seconds 10
        $sayt = PortOchiqmi $port
        Yoz $(if ($sayt) { 'Sayt qayta ko''tarildi' } else { 'Sayt hali ham javob bermayapti' })
    }

    if (-not $tunnel) {
        NgrokniQoy
        Start-Sleep -Seconds 10
        $tunnel = TunnelTirikmi
        Yoz $(if ($tunnel) { 'ngrok qayta ulandi' } else { 'ngrok hali ham ulanmadi' })
    }

    # Tunnel mahalliy API da bor, lekin tashqaridan ishlayaptimi?
    if ($tunnel -and (Get-Date) -gt $keyingiTashqi) {
        $keyingiTashqi = (Get-Date).AddMinutes($tashqiOraliq)
        if (-not (TashqaridanTekshir)) {
            Yoz 'Tashqaridan ochilmadi - ngrokni qayta ulayapman'
            NgrokniQoy
            Start-Sleep -Seconds 10
        }
    }

    if ($sayt -and $tunnel) {
        $ketmaKetXato = 0
        if ((Get-Date) -gt $keyingiYurak) {
            $keyingiYurak = (Get-Date).AddMinutes($yurakOraliq)
            Yoz 'Hammasi joyida: sayt ham, tunnel ham ishlayapti'
        }
    } else {
        $ketmaKetXato++
        # Ketma-ket xato ko'paysa tez-tez urinaverish foydasiz (masalan bepul
        # plan limiti tugagan bo'lsa) - sekinlashtiramiz
        if ($ketmaKetXato -ge 3) {
            Yoz "$ketmaKetXato marta ketma-ket muvaffaqiyatsiz - 5 daqiqa kutib turaman"
            Start-Sleep -Seconds 300
        }
    }

    Start-Sleep -Seconds $oraliq
}
