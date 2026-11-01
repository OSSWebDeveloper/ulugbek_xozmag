param([Parameter(Mandatory=$true)][string]$DataFile, [string]$PreviewFile = '')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$data = ConvertFrom-Json -InputObject ([IO.File]::ReadAllText($DataFile))
$font = New-Object Drawing.Font('Arial', 9)
$bold = New-Object Drawing.Font('Arial', 12, [Drawing.FontStyle]::Bold)
$small = New-Object Drawing.Font('Arial', 8)
$bitmap = New-Object Drawing.Bitmap(280, 1)
$measure = [Drawing.Graphics]::FromImage($bitmap)
$height = 160
foreach ($line in $data.lines) { $height += [int]$measure.MeasureString([string]$line, $font, 270).Height + 4 }
$measure.Dispose(); $bitmap.Dispose()
function Draw-Receipt($g) {
 $g.Clear([Drawing.Color]::White)
 $g.DrawString([string]$data.nom, $bold, [Drawing.Brushes]::Black, 5, 5)
 $y = 32.0
 foreach ($line in $data.lines) {
   $h = $g.MeasureString([string]$line, $font, 270).Height + 4
   $rect = New-Object Drawing.RectangleF(5, $y, 270, $h)
   $g.DrawString([string]$line, $font, [Drawing.Brushes]::Black, $rect)
   $y += $h
 }
 $y += 10
 # Jim zonalar ham width ichida: Code 128 to'liq saqlanadi.
 $module = 2.0
 $left = (280 - ([int]$data.width * $module)) / 2
 foreach ($bar in $data.bars) {
   $rect = New-Object Drawing.RectangleF(($left + [int]$bar[0] * $module), $y, ([int]$bar[1] * $module), 52)
   $g.FillRectangle([Drawing.Brushes]::Black, $rect)
 }
 $y += 56
 $format = New-Object Drawing.StringFormat
 $format.Alignment = [Drawing.StringAlignment]::Center
 $rect = New-Object Drawing.RectangleF(0, $y, 280, 18)
 $g.DrawString([string]$data.barcode, $small, [Drawing.Brushes]::Black, $rect, $format)
 $g.DrawString('Qaytarish uchun chekni saqlang.', $small, [Drawing.Brushes]::Black, 22, ($y + 22))
 $format.Dispose()
}
try {
 if ($PreviewFile) {
   $image = New-Object Drawing.Bitmap(280, $height)
   $g = [Drawing.Graphics]::FromImage($image)
   Draw-Receipt $g
   $image.Save($PreviewFile, [Drawing.Imaging.ImageFormat]::Png)
   $g.Dispose(); $image.Dispose()
 } else {
   $doc = New-Object Drawing.Printing.PrintDocument
   $doc.PrinterSettings.PrinterName = [string]$data.printer
   # Old running server processes may still send the previous queue name.
   if ([string]$data.printer -in @('RONGTA 80mm Series Printer', 'Xprinter') -and
       [Drawing.Printing.PrinterSettings]::InstalledPrinters -contains 'Xprinter XP-80') {
     $doc.PrinterSettings.PrinterName = 'Xprinter XP-80'
   }
   if (-not $doc.PrinterSettings.IsValid) { throw 'Printer topilmadi' }
   $doc.DocumentName = 'Xozmag chek ' + $data.barcode
   $doc.PrintController = New-Object Drawing.Printing.StandardPrintController
   $doc.DefaultPageSettings.PaperSize = New-Object Drawing.Printing.PaperSize('Xozmag 80mm',315,($height+15))
   $doc.DefaultPageSettings.Margins = New-Object Drawing.Printing.Margins(0,0,0,0)
   $doc.add_PrintPage({ param($sender,$e) Draw-Receipt $e.Graphics; $e.HasMorePages=$false })
   try { $doc.Print() } finally { $doc.Dispose() }
 }
} catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }
finally { $font.Dispose(); $bold.Dispose(); $small.Dispose() }
