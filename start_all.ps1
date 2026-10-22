$ErrorActionPreference = "SilentlyContinue"

Write-Host "--- Cleaning ports ---" -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort 8080, 3000, 3080 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
Start-Sleep -Seconds 1

Write-Host "--- Starting DSH (Harness) ---" -ForegroundColor Cyan
$dshCmd = "C:\Users\HP\AppData\Local\Programs\DeepSeek Harness\resources\runtime\cli\bin\dsh.cmd"
$dshLog = "C:\Users\HP\vishap-7.0.1\dsh_output.log"
if (Test-Path $dshLog) { Remove-Item $dshLog }

# Start DSH and write output to log file
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "& '$dshCmd' web *>&1 | Tee-Object -FilePath '$dshLog'"

Write-Host "Waiting for DSH to start..." -ForegroundColor Yellow
$token = $null
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $dshLog) {
        $content = Get-Content $dshLog -Raw
        if ($content -match "token=([a-zA-Z0-9_\-]+)") {
            $token = $matches[1]
            break
        }
    }
}

if (-not $token) {
    Write-Host "!!! ERROR: DSH did not provide a token. Check DSH window. !!!" -ForegroundColor Red
    exit
}
Write-Host "[+] DSH token received successfully!" -ForegroundColor Green

Write-Host "--- Starting Vishap API ---" -ForegroundColor Cyan
$apiCmd = "cd C:\Users\HP\vishap-7.0.1; `$env:VISHAP_DEV='true'; `$env:STRIPE_SECRET_KEY='sk_test_dummy'; `$env:CLERK_SECRET_KEY='sk_test_dummy'; `$env:HARNESS_URL='http://127.0.0.1:3080'; `$env:HARNESS_TOKEN='$token'; .\venv\Scripts\Activate.ps1; python -m src.main"
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", $apiCmd

Write-Host "--- Starting Vishap UI ---" -ForegroundColor Cyan
$uiCmd = "`$env:Path += ';C:\Program Files\nodejs'; cd C:\Users\HP\vishap-7.0.1\ui-next; npm run dev"
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", $uiCmd

Write-Host "--- Waiting for UI ---" -ForegroundColor Yellow
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    try {
        if ((Invoke-WebRequest "http://localhost:3000" -UseBasicParsing -TimeoutSec 1).StatusCode -eq 200) { break }
    } catch {}
}

Write-Host "--- OPENING BROWSER ---" -ForegroundColor Green
Start-Process "http://localhost:3000"
Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:3080"

Write-Host "`nEVERYTHING IS READY! Do not close API, UI, and DSH windows." -ForegroundColor Green
Write-Host "You can close this window (Press Enter)."
Read-Host