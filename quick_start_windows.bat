@echo off
REM Quick Start - Windows (assumes everything is already configured)

cd /d "%~dp0"

REM Activate venv
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    call ..\venv\Scripts\activate.bat
)

REM Start all in separate windows
cd receiver
start "MQTT Broker" cmd /k "mosquitto -c mosquitto.conf -v"
timeout /t 2 >nul
start "Signaling Server" cmd /k "python signaling_server.py"
timeout /t 2 >nul

echo Starting Receiver GUI...
python receiver_gui_mqtt.py
