#!/bin/bash
# ============================================================
#   WebRTC + MQTT Raspberry Pi Launcher
#   Pornește automat sender-ul cu parametrii corecți
# ============================================================

set -e  # Exit on error

echo ""
echo "============================================"
echo "  WebRTC + MQTT Raspberry Pi Launcher"
echo "============================================"
echo ""

# Schimbă la directorul script-ului
cd "$(dirname "$0")"

# Verifică dacă venv există
if [ ! -f "venv/bin/activate" ]; then
    if [ ! -f "../venv/bin/activate" ]; then
        echo "[ERROR] Virtual environment not found!"
        echo "Please create venv first: python3 -m venv venv"
        exit 1
    fi
    VENV_PATH="../venv"
else
    VENV_PATH="venv"
fi

echo "[1/5] Activating virtual environment..."
source "$VENV_PATH/bin/activate"
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to activate venv!"
    exit 1
fi
echo "[OK] Virtual environment activated"
echo ""

# Obține IP-ul Windows de la user
echo "[2/5] Configuration"
echo ""
read -p "Enter Windows IP address [192.168.0.228]: " WINDOWS_IP
WINDOWS_IP=${WINDOWS_IP:-192.168.0.228}
echo "Using Windows IP: $WINDOWS_IP"
echo ""

# Obține fișierul video
read -p "Enter video file path [video.mp4]: " VIDEO_FILE
VIDEO_FILE=${VIDEO_FILE:-video.mp4}

# Verifică dacă fișierul video există
if [ ! -f "$VIDEO_FILE" ]; then
    echo "[ERROR] Video file not found: $VIDEO_FILE"
    exit 1
fi
echo "Using video: $VIDEO_FILE"
echo ""

# Obține FPS
read -p "Enter FPS [30]: " FPS
FPS=${FPS:-30}
echo "Using FPS: $FPS"
echo ""

echo "[3/5] Checking dependencies..."
python3 -c "import aiortc, paho.mqtt.client, cv2, av" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[WARNING] Some dependencies missing!"
    echo "Installing..."
    pip3 install -r sender/requirements.txt --break-system-packages
fi
echo "[OK] Dependencies OK"
echo ""

echo "[4/5] Testing connection to Windows..."
ping -c 2 -W 2 "$WINDOWS_IP" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[WARNING] Cannot ping Windows at $WINDOWS_IP"
    echo "Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "[OK] Windows is reachable"
fi
echo ""

# Test MQTT connection
echo "Testing MQTT broker..."
timeout 3 bash -c "cat < /dev/null > /dev/tcp/$WINDOWS_IP/1883" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "[OK] MQTT broker is accessible"
else
    echo "[WARNING] Cannot connect to MQTT broker on $WINDOWS_IP:1883"
    echo "Make sure Mosquitto is running on Windows!"
    echo ""
fi

# Test Signaling server
echo "Testing Signaling server..."
timeout 3 bash -c "cat < /dev/null > /dev/tcp/$WINDOWS_IP/9000" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "[OK] Signaling server is accessible"
else
    echo "[WARNING] Cannot connect to Signaling server on $WINDOWS_IP:9000"
    echo "Make sure signaling_server.py is running on Windows!"
    echo ""
fi
echo ""

echo "[5/5] Starting sender..."
echo ""
echo "============================================"
echo "  Configuration Summary:"
echo "============================================"
echo "  Video:         $VIDEO_FILE"
echo "  FPS:           $FPS"
echo "  Windows IP:    $WINDOWS_IP"
echo "  Signaling:     http://$WINDOWS_IP:9000"
echo "  MQTT Broker:   $WINDOWS_IP:1883"
echo "============================================"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Pornește sender-ul
cd sender
python3 sender_mqtt.py \
    --video "$VIDEO_FILE" \
    --fps "$FPS" \
    --server-ip "$WINDOWS_IP" \
    --mqtt-broker "$WINDOWS_IP"

echo ""
echo "============================================"
echo "  Sender stopped"
echo "============================================"
