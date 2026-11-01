param(
 [Parameter(Mandatory=$true)][string]$DriverDir,
 [Parameter(Mandatory=$true)][string]$Address,
 [ValidateSet('probe','sync')][string]$Mode = 'probe',
 [string]$InputJson,
 [string]$OutputJson,
 [string]$BackupFile,
 [string]$ProgressJson
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
[Environment]::CurrentDirectory = $DriverDir
$env:PATH = "$DriverDir;$env:PATH"
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Collections.Generic;
public class RongtaNative {
 [DllImport("rtslabelscale.dll", CallingConvention=CallingConvention.StdCall, CharSet=CharSet.Ansi)]
 public static extern int rtscaleConnect(string address, int baud, out int connection);
 [DllImport("rtslabelscale.dll", CallingConvention=CallingConvention.StdCall)]
 public static extern int rtscaleDisConnect(int connection);
 [DllImport("rtslabelscale.dll", CallingConvention=CallingConvention.StdCall)]
 public static extern int rtscaleGetScaleType(int connection, byte[] text, int length);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)]
 public delegate void Callback(IntPtr json, int record, int total);
 [DllImport("rtslabelscale.dll", CallingConvention=CallingConvention.StdCall)]
 public static extern int rtscaleUploadPluData(int connection, Callback callback);
 [DllImport("rtslabelscale.dll", CallingConvention=CallingConvention.StdCall, CharSet=CharSet.Ansi)]
 public static extern int rtscaleDownLoadPLU(int connection, string json, int packet);
 public static List<string> Rows = new List<string>();
 private static void Receive(IntPtr json, int record, int total) {
   Rows.Add(Marshal.PtrToStringAnsi(json));
 }
 public static int Read(int connection) {
   Rows.Clear();
   Callback cb = Receive;
   int result = rtscaleUploadPluData(connection, cb);
   GC.KeepAlive(cb);
   return result;
 }
 public static string ReadJson() { return "[" + string.Join(",", Rows) + "]"; }
}
'@
function SaveJson($path, $text) {
 $temp = $path + '.tmp'
 [IO.File]::WriteAllText($temp, $text, (New-Object Text.UTF8Encoding($false)))
 $saved = $false
 for ($try = 0; $try -lt 7; $try++) {
   try {
     if ([IO.File]::Exists($path)) { [IO.File]::Replace($temp, $path, $null) }
     else { [IO.File]::Move($temp, $path) }
     $saved = $true
     break
   } catch { Start-Sleep -Milliseconds (50 * ($try+1)) }
 }
 if (-not $saved) { [IO.File]::WriteAllText($path, $text, (New-Object Text.UTF8Encoding($false))) }
}
$connection = 0
try {
 $ret = [RongtaNative]::rtscaleConnect($Address, 0, [ref]$connection)
 if ($ret -ne 0) { throw "Tarozi bilan aloqa yo'q ($ret)." }
 $buffer = New-Object byte[] 1024
 $ret = [RongtaNative]::rtscaleGetScaleType($connection, $buffer, $buffer.Length)
 if ($ret -ne 0) { throw "Tarozi protokoli javob bermadi ($ret)." }
 $protocol = [Text.Encoding]::Default.GetString($buffer).Trim([char]0) | ConvertFrom-Json
 if ($Mode -eq 'probe') {
   Write-Output (@{ok=$true; protocol=$protocol.Protocol; address=$Address} | ConvertTo-Json -Compress)
 } else {
   # Eski ro'yxatni o'qish muvaffaqiyatsiz bo'lsa hech narsa yozilmaydi.
   $ret = [RongtaNative]::Read($connection)
   if ($ret -lt 0) { throw 'Tarozi bazasini zaxiralab bo‘lmadi.' }
   SaveJson $BackupFile ([RongtaNative]::ReadJson())
   $rows = ConvertFrom-Json -InputObject ([IO.File]::ReadAllText($InputJson))
   $keep = @{}
   foreach ($row in $rows) { $keep[[int]$row.LFCode] = $true }
   $oldRows = ConvertFrom-Json -InputObject ([RongtaNative]::ReadJson())
   $remove = @()
   foreach ($row in $oldRows) {
     if (-not $keep.ContainsKey([int]$row.LFCode) -and $row.isDelete -ne 1) {
       $row.isDelete = 1
       $remove += $row
     }
   }
   # Faqat kg katalogi qoladi: qolgan yozuvlar alohida isDelete belgisi bilan yashiriladi.
   # PLU xotirasi, qo'shimcha xabarlar va tarozi sozlamalari ommaviy tozalanmaydi.
   $rows = @($remove) + @($rows)
   $total = $rows.Count
   for ($i = 0; $i -lt $total; $i += 4) {
     $end = [Math]::Min($i + 3, $total - 1)
     $batch = @($rows[$i..$end])
     while ($batch.Count -lt 4) { $batch += @{} }
     $json = ConvertTo-Json -InputObject $batch -Depth 8 -Compress
     # SDK'ning eski JSON parseri PowerShell qo'ygan HTML unicode escape'larini ochmaydi.
     $json = $json.Replace('\u0027', "'").Replace('\u003c', '<').Replace('\u003e', '>').Replace('\u0026', '&')
     $ret = [RongtaNative]::rtscaleDownLoadPLU($connection, $json, [int]($i / 4))
     if ($ret -ne 0) { throw "PLU paketi yuborilmadi: $i ($ret). Ayrim mahsulotlar yuborilgan bo'lishi mumkin." }
     if ($i % 40 -eq 0 -or $end -eq $total - 1) {
       SaveJson $ProgressJson (@{holat='yuborilmoqda'; yuborildi=($end+1); jami=$total} | ConvertTo-Json -Compress)
     }
   }
   SaveJson $ProgressJson (@{holat='tekshirilmoqda'; yuborildi=$total; jami=$total} | ConvertTo-Json -Compress)
   $ret = [RongtaNative]::Read($connection)
   if ($ret -lt 0) { throw "Yuborildi, ammo tarozidan qayta o'qib tekshirib bo'lmadi." }
   SaveJson $OutputJson ([RongtaNative]::ReadJson())
   Write-Output (@{ok=$true; sent=$total; read=$ret; protocol=$protocol.Protocol} | ConvertTo-Json -Compress)
 }
} catch {
 [Console]::Error.WriteLine($_.Exception.Message)
 exit 1
} finally {
 if ($connection -gt 0) { [void][RongtaNative]::rtscaleDisConnect($connection) }
}
