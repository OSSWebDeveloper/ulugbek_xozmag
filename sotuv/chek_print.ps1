param([Parameter(Mandatory=$true)][string]$DataFile, [string]$PreviewFile = '')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$data = ConvertFrom-Json -InputObject ([IO.File]::ReadAllText($DataFile))
$font = New-Object Drawing.Font('Consolas', 10)
$bold = New-Object Drawing.Font('Consolas', 11, [Drawing.FontStyle]::Bold)
$title = New-Object Drawing.Font('Consolas', 13, [Drawing.FontStyle]::Bold)
$totalFont = New-Object Drawing.Font('Consolas', 15, [Drawing.FontStyle]::Bold)
$small = New-Object Drawing.Font('Consolas', 9)
$pen = New-Object Drawing.Pen([Drawing.Color]::Black, 1.6)
$pen.DashPattern = [single[]]@(4,3)
$framePen = New-Object Drawing.Pen([Drawing.Color]::Black, 2)
$rightFormat = New-Object Drawing.StringFormat
$rightFormat.Alignment = [Drawing.StringAlignment]::Far
$center = New-Object Drawing.StringFormat
$center.Alignment = [Drawing.StringAlignment]::Center
$blocks = @($data.blocks)
if (-not $data.blocks) {
 $blocks = @([pscustomobject]@{kind='title';text='SAVDO CHEKI'})
 foreach ($line in $data.lines) { $blocks += [pscustomobject]@{kind='detail';text=[string]$line} }
}
function Draw-Receipt($g, $draw) {
 if ($draw) { $g.Clear([Drawing.Color]::White) }
 $g.TextRenderingHint = [Drawing.Text.TextRenderingHint]::SingleBitPerPixelGridFit
 $y = 14.0
 foreach ($block in $blocks) {
  if ($block.kind -eq 'rule') {
   $y += 8
   if ($draw) { $g.DrawLine($pen, 6, $y, 274, $y) }
   $y += 12
   continue
  }
  $f = $font
  if ($block.kind -eq 'title') { $f = $title }
  elseif ($block.kind -eq 'total') { $f = $totalFont }
  elseif ($block.kind -eq 'item') { $f = $bold }
  elseif ($block.kind -eq 'meta' -or $block.kind -eq 'footer') { $f = $small }
  $text = [string]$block.text
  if ($block.kind -eq 'title') { $text = '*** ' + $text + ' ***' }
  if ($block.kind -eq 'item') { $text = $text.ToUpperInvariant() }
  $r = [string]$block.right
  $left = 6
  $right = 274
  if ($block.kind -eq 'total') { $left = 14; $right = 266; $y += 9 }
  elseif ($block.kind -eq 'item') { $y += 4 }
  $leftWidth = $right - $left
  $rWidth = 0
  if ($r) {
   $rWidth = [Math]::Min(196, [Math]::Ceiling($g.MeasureString($r, $f).Width) + 3)
   $leftWidth = $right - $left - $rWidth - 8
  }
  $h = [Math]::Ceiling($g.MeasureString($text, $f, [int]$leftWidth).Height)
  if ($r) { $h = [Math]::Max($h,[Math]::Ceiling($g.MeasureString($r,$f,[int]$rWidth).Height)) }
  if ($draw) {
   if ($block.kind -eq 'total') { $g.DrawLine($framePen,6,($y-8),274,($y-8)); $g.DrawLine($framePen,6,($y-13),274,($y-13)) }
   $rect = New-Object Drawing.RectangleF($left, $y, $leftWidth, ($h+3))
   if ($block.kind -eq 'title' -or $block.kind -eq 'footer') {
    $g.DrawString($text,$f,[Drawing.Brushes]::Black,$rect,$center)
   } else { $g.DrawString($text,$f,[Drawing.Brushes]::Black,$rect) }
   if ($r) {
    $rect = New-Object Drawing.RectangleF(($right-$rWidth),$y,$rWidth,($h+3))
    $g.DrawString($r,$f,[Drawing.Brushes]::Black,$rect,$rightFormat)
   }
  }
  $y += $h + 7
  if ($block.kind -eq 'title') { $y += 8 }
  elseif ($block.kind -eq 'total') { $y += 13 }
 }
 if ($data.barcode) {
  $y += 9
  $module = [Math]::Min(2.0,264.0/[int]$data.width)
  $left = (280 - ([int]$data.width*$module))/2
  if ($draw) {
   foreach ($bar in $data.bars) {
    $rect = New-Object Drawing.RectangleF(($left+[int]$bar[0]*$module),$y,([int]$bar[1]*$module),52)
    $g.FillRectangle([Drawing.Brushes]::Black,$rect)
   }
   $rect = New-Object Drawing.RectangleF(0,($y+56),280,20)
   $g.DrawString([string]$data.barcode,$small,[Drawing.Brushes]::Black,$rect,$center)
   $rect = New-Object Drawing.RectangleF(0,($y+78),280,20)
   $g.DrawString('Qaytarish uchun chekni saqlang.',$small,[Drawing.Brushes]::Black,$rect,$center)
  }
  $y += 103
 }
 return [int][Math]::Ceiling($y+12)
}
try {
 $bitmap = New-Object Drawing.Bitmap(280,1)
 $measure = [Drawing.Graphics]::FromImage($bitmap)
 try { $height = Draw-Receipt $measure $false } finally { $measure.Dispose(); $bitmap.Dispose() }
 if ($PreviewFile) {
  $image = New-Object Drawing.Bitmap(280,$height)
  $g = [Drawing.Graphics]::FromImage($image)
  try { $null = Draw-Receipt $g $true; $image.Save($PreviewFile,[Drawing.Imaging.ImageFormat]::Png) }
  finally { $g.Dispose(); $image.Dispose() }
 } else {
  $doc = New-Object Drawing.Printing.PrintDocument
  $doc.PrinterSettings.PrinterName = [string]$data.printer
  if ([string]$data.printer -in @('RONGTA 80mm Series Printer','Xprinter') -and
      [Drawing.Printing.PrinterSettings]::InstalledPrinters -contains 'Xprinter XP-80') {
   $doc.PrinterSettings.PrinterName = 'Xprinter XP-80'
  }
  if (-not $doc.PrinterSettings.IsValid) { throw 'Printer topilmadi' }
  # Uzilgan printerga yuborilsa Windows chekni navbatda saqlab, printer
  # ulanganda chiqarib yuboradi. Shuning uchun avval ulanganini tekshiramiz.
  $target = $doc.PrinterSettings.PrinterName
  $state = Get-CimInstance Win32_Printer | Where-Object { $_.Name -eq $target } | Select-Object -First 1
  if ($state -and $state.WorkOffline) { throw 'Printer ulanmagan' }
  $doc.DocumentName = 'BizaroPOS ' + $(if($data.test){'printer test'}else{'chek '+$data.barcode})
  $doc.PrintController = New-Object Drawing.Printing.StandardPrintController
  $doc.DefaultPageSettings.PaperSize = New-Object Drawing.Printing.PaperSize('Receipt 80mm',315,($height+15))
  $doc.DefaultPageSettings.Margins = New-Object Drawing.Printing.Margins(0,0,0,0)
  $doc.add_PrintPage({param($sender,$e) $null = Draw-Receipt $e.Graphics $true; $e.HasMorePages=$false})
  try { $doc.Print() } finally { $doc.Dispose() }
 }
} catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }
finally { $font.Dispose();$bold.Dispose();$title.Dispose();$totalFont.Dispose();$small.Dispose();$pen.Dispose();$framePen.Dispose();$center.Dispose();$rightFormat.Dispose() }
