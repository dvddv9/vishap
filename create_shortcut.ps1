# create_shortcut.ps1
$ProjectDir = "C:\Users\HP\vishap-7.0.1"
$ShortcutPath = "$env:USERPROFILE\Desktop\Vishap.lnk"

$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($ShortcutPath)
$sc.TargetPath = "powershell.exe"
$sc.Arguments = "-ExecutionPolicy Bypass -NoExit -File `"$ProjectDir\start_all.ps1`""
$sc.WorkingDirectory = $ProjectDir
$sc.IconLocation = "$ProjectDir\icon.ico,0"
$sc.Description = "Launch Vishap (API + UI + Harness)"
$sc.Save()

Write-Host "[+] Desktop shortcut created: $ShortcutPath" -ForegroundColor Green
Write-Host "[+] Double-click it to start Vishap." -ForegroundColor Green