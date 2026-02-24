@echo off
REM Start WebRTC + MQTT Integration on Windows
REM This script starts all necessary components

echo ========================================
echo   WebRTC + MQTT Integration - Windows
echo ========================================
echo.

set SCRIPT_DIR=%~dp0

REM Check if Mosquitto is installed
where mosquitto >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [1/3] Starting MQTT Broker (Mosquitto)...
    start "MQTT Broker" cmd /k "mosquitto -v"
    timeout /t 2 /nobreak > nul
) else (
    echo [WARNING] Mosquitto not found!
    echo Please install Mosquitto or start your MQTT broker manually.
    echo Download: https://mosquitto.org/download/
    echo.
    echo Press any key to continue without local broker...
    pause > nul
)

echo [2/3] Starting WebRTC Signaling Server...
start "Signaling Server" cmd /k "cd /d %SCRIPT_DIR%receiver && python signaling_server.py"
timeout /t 3 /nobreak > nul

echo [3/3] Starting Receiver GUI with MQTT...
start "Receiver GUI + MQTT" cmd /k "cd /d %SCRIPT_DIR%receiver && python receiver_gui_mqtt.py"

echo.
echo ========================================
echo All components started!
echo.
echo Components running:
echo - MQTT Broker: localhost:1883
echo - Signaling Server: http://localhost:8080  
echo - Receiver GUI: Will open shortly
echo.
echo Next steps:
echo 1. Start sender on Raspberry Pi:
echo    python3 sender_mqtt.py --video video.mp4 --server-ip YOUR_WINDOWS_IP --mqtt-broker YOUR_WINDOWS_IP
echo.
echo 2. In GUI: Click "Connect MQTT" then "Connect WebRTC"
echo.
echo 3. Use control panel to send commands!
echo.
echo Press any key to close this window...
echo ========================================
pause > nul
