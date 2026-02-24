@echo off
REM Network Diagnostic Script for WebRTC + MQTT
REM Run as Administrator for best results

echo ============================================
echo   WebRTC + MQTT Network Diagnostics
echo ============================================
echo.

echo [1/8] Checking Windows IP Address...
ipconfig | findstr "IPv4"
echo.

echo [2/8] Checking Firewall Status...
powershell -Command "Get-NetFirewallProfile | Select Name, Enabled"
echo.

echo [3/8] Checking if Signaling Server port (9000) is listening...
netstat -an | findstr "9000" || echo WARNING: Port 9000 not listening!
echo.

echo [4/8] Checking if MQTT Broker port (1883) is listening...
netstat -an | findstr "1883" || echo WARNING: Port 1883 not listening!
echo.

echo [5/8] Checking Python location...
where python
echo.

echo [6/8] Checking active network connections...
netstat -an | findstr "ESTABLISHED" | findstr ":9000 :1883"
echo.

echo [7/8] Testing if Python can bind to ports...
echo Testing port 9000...
python -c "import socket; s=socket.socket(); s.bind(('0.0.0.0', 9001)); s.close(); print('OK: Can bind to ports')" 2>&1
echo.

echo [8/8] Checking for multiple network interfaces...
ipconfig | findstr /C:"Ethernet adapter" /C:"Wireless LAN adapter"
echo.

echo ============================================
echo   Diagnostic Complete!
echo ============================================
echo.
echo Common Issues:
echo   - If port 9000 NOT listening: Start signaling_server.py
echo   - If port 1883 NOT listening: Start Mosquitto broker
echo   - If firewall ENABLED: May need to add rules or disable temporarily
echo   - If multiple adapters: May cause ICE confusion
echo.
echo Recommended Actions:
echo   1. Make sure signaling_server.py is running
echo   2. Make sure mosquitto.exe is running
echo   3. Add firewall rules (see TROUBLESHOOTING.md)
echo   4. Or temporarily disable firewall for testing
echo.
pause
