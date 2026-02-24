#!/bin/bash
# Quick Start - Raspberry Pi (uses defaults)

cd "$(dirname "$0")"

# Activate venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    source ../venv/bin/activate
fi

# Default values (edit these if needed)
WINDOWS_IP="192.168.0.228"
VIDEO_FILE="video.mp4"
FPS="30"

echo "Starting sender with defaults..."
echo "  Windows IP: $WINDOWS_IP"
echo "  Video: $VIDEO_FILE"
echo "  FPS: $FPS"
echo ""

cd sender
python3 sender_mqtt.py \
    --video "$VIDEO_FILE" \
    --fps "$FPS" \
    --server-ip "$WINDOWS_IP" \
    --mqtt-broker "$WINDOWS_IP"
