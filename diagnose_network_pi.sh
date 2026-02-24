#!/bin/bash
# Network Diagnostic Script for WebRTC + MQTT on Raspberry Pi
# Usage: ./diagnose_network_pi.sh [windows_ip]

echo "============================================"
echo "  WebRTC + MQTT Network Diagnostics (Pi)"
echo "============================================"
echo ""

WINDOWS_IP="${1:-192.168.0.228}"

echo "[1/8] Checking Raspberry Pi IP Address..."
hostname -I
echo ""

echo "[2/8] Checking network interfaces..."
ip addr show | grep "inet "
echo ""

echo "[3/8] Checking if multiple IPs are active..."
ACTIVE_IPS=$(ip addr show | grep "inet " | grep -v "127.0.0.1" | wc -l)
if [ $ACTIVE_IPS -gt 1 ]; then
    echo "⚠️  WARNING: Multiple IPs detected! This may cause ICE issues."
    echo "   Consider disabling unused interfaces."
else
    echo "✅ OK: Single active IP"
fi
echo ""

echo "[4/8] Testing ping to Windows ($WINDOWS_IP)..."
if ping -c 3 -W 2 $WINDOWS_IP > /dev/null 2>&1; then
    echo "✅ OK: Windows is reachable"
else
    echo "❌ ERROR: Cannot ping Windows at $WINDOWS_IP"
fi
echo ""

echo "[5/8] Testing Signaling Server connection (port 9000)..."
if timeout 3 bash -c "</dev/tcp/$WINDOWS_IP/9000" 2>/dev/null; then
    echo "✅ OK: Signaling server port 9000 is accessible"
else
    echo "❌ ERROR: Cannot connect to port 9000"
    echo "   Make sure signaling_server.py is running on Windows"
    echo "   Check Windows firewall!"
fi
echo ""

echo "[6/8] Testing MQTT Broker connection (port 1883)..."
if timeout 3 bash -c "</dev/tcp/$WINDOWS_IP/1883" 2>/dev/null; then
    echo "✅ OK: MQTT broker port 1883 is accessible"
else
    echo "❌ ERROR: Cannot connect to port 1883"
    echo "   Make sure Mosquitto is running on Windows"
    echo "   Check Windows firewall!"
fi
echo ""

echo "[7/8] Checking Python and required packages..."
if python3 -c "import aiortc, paho.mqtt.client" 2>/dev/null; then
    echo "✅ OK: Required Python packages installed"
else
    echo "❌ ERROR: Missing packages"
    echo "   Run: pip3 install -r requirements.txt"
fi
echo ""

echo "[8/8] Checking active connections..."
ss -tnp | grep "$WINDOWS_IP" || echo "No active connections to Windows"
echo ""

echo "============================================"
echo "  Diagnostic Complete!"
echo "============================================"
echo ""
echo "Summary:"
echo "  Windows IP: $WINDOWS_IP"
echo "  Pi IPs: $(hostname -I)"
echo ""
echo "If you see connection errors:"
echo "  1. Check Windows firewall (most common issue!)"
echo "  2. Make sure signaling server is running on Windows"
echo "  3. Make sure Mosquitto broker is running on Windows"
echo "  4. If multiple IPs on Pi, disable unused interface"
echo ""
echo "Quick firewall test on Windows:"
echo "  PowerShell (as Admin): Set-NetFirewallProfile -Enabled False"
echo "  Test connection, then re-enable: Set-NetFirewallProfile -Enabled True"
echo ""
