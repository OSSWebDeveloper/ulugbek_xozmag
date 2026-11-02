param([Parameter(Mandatory=$true)][string]$Address,[int]$InterfaceIndex=0)
$ErrorActionPreference='Stop'
$ip=[Net.IPAddress]::Parse($Address)
if ($ip.AddressFamily -ne [Net.Sockets.AddressFamily]::InterNetwork) {throw 'IPv4 kerak'}
if(-not $InterfaceIndex){
 $adapters=@(Get-NetAdapter -Physical | Where-Object Status -eq 'Up')
 $wifi=@($adapters | Where-Object {$_.NdisPhysicalMedium -eq 9})
 if($wifi.Count -eq 1){$InterfaceIndex=$wifi[0].ifIndex}
 elseif($adapters.Count -eq 1){$InterfaceIndex=$adapters[0].ifIndex}
 else {throw 'Bitta faol Wi-Fi/tarmoq kartasini tanlang'}
}
$before=Get-NetIPInterface -InterfaceIndex $InterfaceIndex -AddressFamily IPv4
foreach($store in @('active','persistent')) {
 & netsh interface ipv4 set interface interface=$InterfaceIndex dhcpstaticipcoexistence=enabled store=$store | Out-Null
 if($LASTEXITCODE){throw 'DHCP coexistence sozlanmadi. Administrator sifatida oching'}
}
if(-not(Get-NetIPAddress -InterfaceIndex $InterfaceIndex -IPAddress $Address -ErrorAction SilentlyContinue)) {
 & netsh interface ipv4 add address name=$InterfaceIndex address=$Address mask=255.255.255.0 skipassource=true store=persistent | Out-Null
 if($LASTEXITCODE){throw 'IP qoshilmadi. Administrator sifatida oching'}
}
if($before.Dhcp -eq 'Enabled') {
 Set-NetIPInterface -InterfaceIndex $InterfaceIndex -AddressFamily IPv4 -Dhcp Enabled
}
$limit=(Get-Date).AddSeconds(8)
do {$state=Get-NetIPAddress -InterfaceIndex $InterfaceIndex -IPAddress $Address; if($state.AddressState -eq 'Duplicate'){throw 'Bu IP boshqa qurilmada band'}; if($state.AddressState -eq 'Preferred'){break}; Start-Sleep -Milliseconds 300}while((Get-Date) -lt $limit)
if($state.AddressState -ne 'Preferred'){throw 'IP hali tayyor emas'}
Write-Output 'OK'
