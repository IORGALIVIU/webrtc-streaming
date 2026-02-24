#!/bin/bash
# Start WebRTC + MQTT Sender on Raspberry Pi
# Usage: ./start_pi_mqtt.sh [windows_ip] [video_file] [fps]

echo "========================================"
echo "  WebRTC + MQTT Sender - Raspberry Pi"
echo "========================================"
echo ""

# Default values
WINDOWS_IP="${1:-192.168.1.50}"
VIDEO_FILE="${2:-video.mp4}"
FPS="${3:-30}"

echo "Configuration:"
echo "  Windows IP:  $WINDOWS_IP"
echo "  MQTT Broker: $WINDOWS_IP (same as Windows)"
echo "  Video file:  $VIDEO_FILE"
echo "  FPS:         $FPS"
echo ""

# Check if video file exists
if [ ! -f "$VIDEO_FILE" ]; then
    echo "❌ ERROR: Video file not found: $VIDEO_FILE"
    echo ""
    echo "Please provide a video file:"
    echo "  1. Copy video to sender/ directory"
    echo "  2. Run: ./start_pi_mqtt.sh $WINDOWS_IP your_video.mp4"
    echo ""
    echo "Or generate a test video:"
    echo "  cd sender && python3 generate_test_video.py --output video.mp4"
    echo ""
    exit 1
fi

# Check if paho-mqtt is installed
if ! python3 -c "import paho.mqtt.client" 2>/dev/null; then
    echo "❌ ERROR: paho-mqtt not installed"
    echo ""
    echo "Please install:"
    echo "  pip3 install paho-mqtt"
    echo ""
    exit 1
fi

# Check other requirements
if ! python3 -c "import aiortc" 2>/dev/null; then
    echo "❌ ERROR: Requirements not installed"
    echo ""
    echo "Please install all requirements:"
    echo "  pip3 install -r sender/requirements.txt"
    echo ""
    exit 1
fi

echo "✅ All checks passed!"
echo ""
echo "========================================"
echo "Starting integrated sender..."
echo "========================================"
echo ""
echo "Make sure on Windows:"
echo "  1. MQTT Broker is running (mosquitto -v)"
echo "  2. Signaling server is running"
echo "  3. Receiver GUI is ready"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Change to sender directory
cd "$(dirname "$0")/sender" || exit 1

# Start sender with MQTT
python3 sender_mqtt.py \
    --video "$VIDEO_FILE" \
    --fps "$FPS" \
    --server-ip "$WINDOWS_IP" \
    --mqtt-broker "$WINDOWS_IP"

echo ""
echo "Sender stopped."
