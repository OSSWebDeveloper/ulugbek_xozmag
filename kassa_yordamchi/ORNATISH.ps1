$ErrorActionPreference = 'Stop'
$source = $PSScriptRoot
$target = Join-Path $env:LOCALAPPDATA 'BizaroPOS-Kassa'
New-Item -ItemType Directory -Path $target -Force | Out-Null
Copy-Item -Path (Join-Path $source '*') -Destination $target -Force
$runtime = Join-Path $target 'runtime'
Expand-Archive -LiteralPath (Join-Path $target 'python.zip') -DestinationPath $runtime -Force
$python = Join-Path $runtime 'pythonw.exe'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'BizaroPOS Kassa.lnk'))
$shortcut.TargetPath = $python
$shortcut.Arguments = '"' + (Join-Path $target 'agent.py') + '"'
$shortcut.WorkingDirectory = $target
$shortcut.IconLocation = (Join-Path $target 'bizaropos.ico') + ',0'
$shortcut.Description = 'BizaroPOS - USB kassa qurilmalari'
$shortcut.Save()
Start-Process -FilePath $python -ArgumentList $shortcut.Arguments -WorkingDirectory $target -WindowStyle Hidden
Write-Output 'Tayyor. Desktopdagi BizaroPOS Kassa yarligi bilan oching.'
