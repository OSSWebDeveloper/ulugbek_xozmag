param([Parameter(Mandatory=$true)][string]$DataFile, [string]$PreviewFile = '')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$data = ConvertFrom-Json -InputObject ([IO.File]::ReadAllText($DataFile))
$w = [double]$data.width_mm
$h = [double]$data.height_mm
if ($w -lt 20 -or $w -gt 80 -or $h -lt 15 -or $h -gt 80) { throw 'Invalid label size' }
$nameFont = New-Object Drawing.Font('Arial', 3.0, [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Millimeter)
$priceFont = New-Object Drawing.Font('Arial', 4.5, [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Millimeter)
$codeFont = New-Object Drawing.Font('Arial', 3.5, [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Millimeter)
$small = New-Object Drawing.Font('Arial', 2.0, [Drawing.FontStyle]::Regular, [Drawing.GraphicsUnit]::Millimeter)
$center = New-Object Drawing.StringFormat
$center.Alignment = [Drawing.StringAlignment]::Center
$center.LineAlignment = [Drawing.StringAlignment]::Center
$center.Trimming = [Drawing.StringTrimming]::EllipsisCharacter
function Text($g, $text, $font, $y, $height) {
  $r = New-Object Drawing.RectangleF(2, $y, 52, $height)
  $g.DrawString([string]$text, $font, [Drawing.Brushes]::Black, $r, $center)
}
function Draw-Label($g) {
  $g.PageUnit = [Drawing.GraphicsUnit]::Millimeter
  $g.ScaleTransform([single]($w/56), [single]($h/40))
  $g.Clear([Drawing.Color]::White)
  Text $g $data.nom $nameFont 1.5 10
  Text $g $data.narx $priceFont 12.5 6
  Text $g ('1 ' + $data.birlik + ' uchun') $small 18.5 3
  $module = [Math]::Min(0.5, 50.0 / [int]$data.modules)
  $left = (56 - [int]$data.modules * $module) / 2
  foreach ($bar in $data.bars) {
    $rect = New-Object Drawing.RectangleF(($left + [int]$bar[0]*$module), 23, ([int]$bar[1]*$module), 9)
    $g.FillRectangle([Drawing.Brushes]::Black, $rect)
  }
  Text $g ('KOD ' + $data.kod) $codeFont 33 5
}
try {
  if ($PreviewFile) {
    $image = New-Object Drawing.Bitmap([int][Math]::Ceiling($w/25.4*203), [int][Math]::Ceiling($h/25.4*203))
    $image.SetResolution(203,203)
    $g = [Drawing.Graphics]::FromImage($image)
    try { Draw-Label $g; $image.Save($PreviewFile, [Drawing.Imaging.ImageFormat]::Png) }
    finally { $g.Dispose(); $image.Dispose() }
  } else {
    $doc = New-Object Drawing.Printing.PrintDocument
    $doc.PrinterSettings.PrinterName = [string]$data.printer
    if (-not $doc.PrinterSettings.IsValid) { throw 'Printer topilmadi' }
    $doc.DocumentName = 'BizaroPOS yorliq ' + $data.kod
    $doc.PrintController = New-Object Drawing.Printing.StandardPrintController
    $doc.DefaultPageSettings.PaperSize = New-Object Drawing.Printing.PaperSize('BizaroPOS yorliq', [int][Math]::Round($w/25.4*100), [int][Math]::Round($h/25.4*100))
    $doc.DefaultPageSettings.Landscape = $false
    $doc.DefaultPageSettings.Margins = New-Object Drawing.Printing.Margins(0,0,0,0)
    $script:page = 0
    $doc.add_PrintPage({ param($sender,$e)
      Draw-Label $e.Graphics
      $script:page++
      $e.HasMorePages = $script:page -lt [int]$data.copies
    })
    try { $doc.Print() } finally { $doc.Dispose() }
  }
} catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }
finally { $nameFont.Dispose(); $priceFont.Dispose(); $codeFont.Dispose(); $small.Dispose(); $center.Dispose() }
