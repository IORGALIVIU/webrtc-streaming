@echo off
REM ============================================================
REM   WebRTC + MQTT Windows Launcher
REM   Pornește automat toate componentele necesare
REM ============================================================

echo.
echo ============================================
echo   WebRTC + MQTT Windows Launcher
echo ============================================
echo.

REM Schimbă la directorul script-ului
cd /d "%~dp0"

REM Verifică dacă venv există
if not exist "venv\Scripts\activate.bat" (
    if not exist "..\venv\Scripts\activate.bat" (
        echo [ERROR] Virtual environment not found!
        echo Please create venv first: python -m venv venv
        pause
        exit /b 1
    )
    REM venv e un nivel mai sus
    set VENV_PATH=..\venv
) else (
    set VENV_PATH=venv
)

echo [1/6] Activating virtual environment...
call %VENV_PATH%\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate venv!
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Verifică dacă mosquitto.conf există
if not exist "receiver\mosquitto.conf" (
    echo [2/6] Creating mosquitto.conf...
    (
        echo listener 1883 0.0.0.0
        echo allow_anonymous true
        echo log_type all
        echo log_dest stdout
    ) > receiver\mosquitto.conf
    echo [OK] mosquitto.conf created
) else (
    echo [2/6] mosquitto.conf found
)
echo.

REM Verifică dacă Mosquitto este instalat
where mosquitto >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Mosquitto not found!
    echo Please install Mosquitto: https://mosquitto.org/download/
    echo.
    echo Alternative: Run components manually without Mosquitto
    pause
    exit /b 1
)

echo [3/6] Starting Mosquitto broker...
cd receiver
start "MQTT Broker" cmd /k "mosquitto -c mosquitto.conf -v"
timeout /t 2 >nul
echo [OK] Mosquitto started
echo.

echo [4/6] Starting Signaling Server...
start "Signaling Server" cmd /k "python signaling_server.py"
timeout /t 2 >nul
echo [OK] Signaling server started
echo.

echo [5/6] Starting Receiver GUI...
timeout /t 1 >nul
echo [OK] Launching GUI...
echo.

echo [6/6] All components started!
echo.
echo ============================================
echo   READY! Now start sender on Raspberry Pi
echo ============================================
echo.
echo Windows IP: 
ipconfig | findstr "IPv4" | findstr "192.168"
echo.
echo On Raspberry Pi, run:
echo   python3 sender/sender_mqtt.py --video video.mp4 --server-ip YOUR_WINDOWS_IP --mqtt-broker YOUR_WINDOWS_IP
echo.
echo Press any key to start Receiver GUI...
pause >nul

REM Pornește GUI în fereastra curentă
python receiver_gui_mqtt.py

echo.
echo ============================================
echo   Receiver GUI closed
echo ============================================
echo.
echo Press any key to exit...
pause
