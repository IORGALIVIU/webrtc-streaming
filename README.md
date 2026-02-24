# 🚀 WebRTC + MQTT Streaming System

Complete system for live camera streaming from Raspberry Pi to Windows with MQTT sensor data and game-like keyboard control.

---

## 📋 Quick Start

### Windows:
```powershell
# Double-click:
start_all_windows.bat
```

### Raspberry Pi (with Camera):
```bash
./start_all_pi.sh
# When asked for video, type: camera
```

---

## 📷 Camera Module 3 NoIR

### Enable Camera:
```bash
sudo raspi-config
# Interface Options → Camera → Enable → Reboot
```

### Test Camera:
```bash
cd sender
python3 camera_track.py
# Should save test image to /tmp/camera_test.jpg
```

### Start with Camera:
```bash
python3 sender_mqtt.py --camera --server-ip 192.168.0.228 --mqtt-broker 192.168.0.228
```

**Resolutions:**
- `--camera-width 1920 --camera-height 1080` (Full HD, default)
- `--camera-width 1280 --camera-height 720` (HD, less bandwidth)
- `--camera-width 640 --camera-height 480` (VGA, low latency)

---

## 🎮 Keyboard Control (Manual Mode)

### Controls:
- **↑** - Increase speed
- **↓** - Decrease speed  
- **←** - Turn left (decrease angle)
- **→** - Turn right (increase angle)

### How It Works:
- **Hold** key = smooth acceleration
- **Release** = auto-decelerate to zero
- **Quick tap** = instant +10° boost
- **Opposite direction** = instant reverse

### Switch to Manual Mode:
1. Click "Manual" radio button in GUI
2. Use arrow keys to control
3. Values update automatically (no "Send" button needed!)

---

## 🛠️ Manual Start

### Windows (3 terminals):

**Terminal 1 - MQTT:**
```powershell
cd receiver
mosquitto -c mosquitto.conf -v
```

**Terminal 2 - Signaling:**
```powershell
cd receiver
venv\Scripts\activate
python signaling_server.py
```

**Terminal 3 - GUI:**
```powershell
cd receiver
venv\Scripts\activate
python receiver_gui_mqtt.py
```

### Raspberry Pi:

**With Camera:**
```bash
cd sender
source venv/bin/activate
python3 sender_mqtt.py --camera --server-ip YOUR_WINDOWS_IP --mqtt-broker YOUR_WINDOWS_IP
```

**With Video File:**
```bash
python3 sender_mqtt.py --video video.mp4 --fps 30 --server-ip YOUR_WINDOWS_IP --mqtt-broker YOUR_WINDOWS_IP
```

---

## 🔧 Troubleshooting

### Camera not working:
```bash
vcgencmd get_camera  # Should show: supported=1 detected=1
libcamera-hello --list-cameras
```

### Keyboard not responding:
```powershell
pip install pynput
```

### MQTT connection failed:
- Check Mosquitto is running with `mosquitto.conf`
- Verify both devices use same MQTT broker IP

### ICE connection failed:
- Restart receiver GUI between tests
- Check firewall (disable temporarily to test)

---

## 💡 Tips

- Use Full HD (1920x1080) for best quality on good WiFi
- Switch to HD (1280x720) if experiencing lag
- Manual mode resets to 0 when switching back to Auto
- Hold keys for smooth control, tap for quick adjustments

---

**Made with ❤️ for smooth streaming and responsive control!**
