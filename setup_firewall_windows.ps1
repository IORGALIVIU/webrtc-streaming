# Add Firewall Rules for WebRTC + MQTT
# Run as Administrator!

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  WebRTC + MQTT Firewall Configuration" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

Write-Host "✅ Running as Administrator" -ForegroundColor Green
Write-Host ""

# Get Python path
Write-Host "[1/4] Finding Python installation..." -ForegroundColor Yellow
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source

if ($pythonPath) {
    Write-Host "    Found: $pythonPath" -ForegroundColor Green
} else {
    Write-Host "    ⚠️  Python not found in PATH" -ForegroundColor Yellow
    Write-Host "    Will add port-based rules only" -ForegroundColor Yellow
}
Write-Host ""

# Add Python firewall rule if Python found
if ($pythonPath) {
    Write-Host "[2/4] Adding Python firewall rule..." -ForegroundColor Yellow
    
    # Remove existing rule if present
    Remove-NetFirewallRule -DisplayName "Python WebRTC+MQTT" -ErrorAction SilentlyContinue
    
    # Add new rule
    New-NetFirewallRule -DisplayName "Python WebRTC+MQTT" `
        -Direction Inbound `
        -Program $pythonPath `
        -Action Allow `
        -Profile Any `
        -Description "Allow Python for WebRTC and MQTT communication"
    
    Write-Host "    ✅ Python rule added" -ForegroundColor Green
} else {
    Write-Host "[2/4] Skipping Python rule (Python not found)" -ForegroundColor Yellow
}
Write-Host ""

# Add port-specific rules
Write-Host "[3/4] Adding port-specific firewall rules..." -ForegroundColor Yellow

# Signaling Server (TCP 9000)
Remove-NetFirewallRule -DisplayName "WebRTC Signaling Server" -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "WebRTC Signaling Server" `
    -Direction Inbound `
    -LocalPort 9000 `
    -Protocol TCP `
    -Action Allow `
    -Profile Any `
    -Description "WebRTC signaling server port"
Write-Host "    ✅ Port 9000 (TCP) - Signaling" -ForegroundColor Green

# Alternative signaling port
Remove-NetFirewallRule -DisplayName "WebRTC Signaling Alt" -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "WebRTC Signaling Alt" `
    -Direction Inbound `
    -LocalPort 8080 `
    -Protocol TCP `
    -Action Allow `
    -Profile Any `
    -Description "WebRTC signaling server alternate port"
Write-Host "    ✅ Port 8080 (TCP) - Signaling Alt" -ForegroundColor Green

# MQTT Broker
Remove-NetFirewallRule -DisplayName "MQTT Broker" -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "MQTT Broker" `
    -Direction Inbound `
    -LocalPort 1883 `
    -Protocol TCP `
    -Action Allow `
    -Profile Any `
    -Description "MQTT broker port"
Write-Host "    ✅ Port 1883 (TCP) - MQTT" -ForegroundColor Green

# WebRTC ICE/RTP (UDP range)
Remove-NetFirewallRule -DisplayName "WebRTC ICE/RTP" -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "WebRTC ICE/RTP" `
    -Direction Inbound `
    -LocalPort 49152-65535 `
    -Protocol UDP `
    -Action Allow `
    -Profile Any `
    -Description "WebRTC ICE candidates and RTP streams"
Write-Host "    ✅ Ports 49152-65535 (UDP) - WebRTC ICE" -ForegroundColor Green

Write-Host ""

# Verify rules
Write-Host "[4/4] Verifying firewall rules..." -ForegroundColor Yellow
$rules = Get-NetFirewallRule | Where-Object { 
    $_.DisplayName -like "*WebRTC*" -or 
    $_.DisplayName -like "*MQTT*" -or 
    $_.DisplayName -like "*Python WebRTC*"
}

Write-Host ""
Write-Host "Active rules:" -ForegroundColor Cyan
foreach ($rule in $rules) {
    $status = if ($rule.Enabled) { "✅" } else { "❌" }
    Write-Host "  $status $($rule.DisplayName)" -ForegroundColor $(if ($rule.Enabled) { "Green" } else { "Red" })
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Configuration Complete!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Firewall rules have been added successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Start Mosquitto: mosquitto -v" -ForegroundColor White
Write-Host "  2. Start Signaling: python receiver/signaling_server.py" -ForegroundColor White
Write-Host "  3. Start Receiver: python receiver/receiver_gui_mqtt.py" -ForegroundColor White
Write-Host "  4. Start Sender on Pi with your Windows IP" -ForegroundColor White
Write-Host ""
Write-Host "If problems persist:" -ForegroundColor Yellow
Write-Host "  - Run: .\diagnose_network_windows.bat" -ForegroundColor White
Write-Host "  - Check Windows Defender settings" -ForegroundColor White
Write-Host "  - Temporarily disable firewall to test" -ForegroundColor White
Write-Host ""

pause
