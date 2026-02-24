# 🚀 Quick Start - WebRTC + MQTT Integration

## ⚡ Start Rapid în 5 Pași

### Pregătire

**Windows:**
- Python 3.10+ instalat
- Dependențe: `pip install -r receiver/requirements.txt`
- **MQTT Broker instalat** (vezi mai jos)

**Raspberry Pi:**
- Python 3.10+ instalat  
- Dependențe: `pip3 install -r sender/requirements.txt`
- Video: `video.mp4` în folder `sender/`

---

## 🔧 Pas 0: Instalează MQTT Broker (Windows)

### Opțiunea A: Mosquitto (Recomandat)

```powershell
# Download: https://mosquitto.org/download/
# Instalează, apoi pornește:
mosquitto -v
```

### Opțiunea B: Broker Python (Alternative)

```powershell
pip install hbmqtt
hbmqtt
```

### Opțiunea C: Broker Cloud (Pentru testare)

Folosește `test.mosquitto.org` (public, fără configurare locală)

---

## 🎬 Pașii de Pornire

### Pas 1: Windows - MQTT Broker
```powershell
mosquitto -v
```
✅ Broker rulează pe `localhost:1883`

### Pas 2: Windows - Signaling Server
```powershell
cd receiver
python signaling_server.py
```
✅ Server rulează pe `http://0.0.0.0:8080`

### Pas 3: Raspberry Pi - Sender cu MQTT
```bash
cd sender
python3 sender_mqtt.py \
    --video video.mp4 \
    --fps 30 \
    --server-ip 192.168.1.50 \
    --mqtt-broker 192.168.1.50
```
⚠️ Înlocuiește `192.168.1.50` cu IP-ul Windows!

### Pas 4: Windows - Receiver GUI cu MQTT
```powershell
cd receiver
python receiver_gui_mqtt.py
```

### Pas 5: În GUI
1. Click **"Connect MQTT"**
2. Click **"Connect WebRTC"**
3. Ajustează controalele și click **"Send Commands"**

---

## 🎛️ Controale Disponibile

### În GUI (Windows):

**Mode:**
- `Auto`: Robotul funcționează autonom
- `Manual`: Controlezi tu unghiul și viteza

**Sliders:**
- `Angle`: -180° la +180°
- `Speed`: 0 la 100 RPM

**Buton:**
- `Send Commands`: Trimite toate setările

---

## 📺 Ce Vei Vedea

### Video (Windows):
- Stream video live de la Pi
- Overlay cu:
  - Timestamp (ms)
  - Unghi curent
  - Viteză curentă
  - Mod (Auto/Manual)
  - Status MQTT

### Sensor Panel (Windows):
- **Unghi**: Sincronizat cu frame-ul curent
- **Viteza**: Sincronizată cu frame-ul curent
- **Timestamp**: ID-ul frame-ului

### Control Panel (Windows):
- Sliders pentru comandă
- Status MQTT și WebRTC
- Statistici FPS, frames received

---

## 🔍 Verificare Funcționare

### Test 1: MQTT Funcționează?

**Pe Windows:**
```powershell
# Instalează client MQTT
pip install paho-mqtt

# Subscribe la topic senzori
mosquitto_sub -h localhost -t "robot/senzori"
```

Ar trebui să vezi mesaje JSON cu unghi și viteza.

### Test 2: Comenzi Ajung la Pi?

**Pe Raspberry Pi:**
```bash
# Subscribe la comenzi
mosquitto_sub -h 192.168.1.50 -t "robot/control/#"
```

Schimbă sliders în GUI, click "Send Commands", și vezi mesajele.

### Test 3: Sincronizare Timestamp

Observă timestamp-ul în video și timestamp-ul din Sensor Panel - ar trebui să fie identice sau foarte apropiate (±200ms).

---

## ⚠️ Troubleshooting Rapid

### "MQTT Connection Failed"

**Windows:**
```powershell
# Verifică că broker rulează
netstat -an | findstr 1883
```

**Raspberry Pi:**
```bash
# Testează conectivitatea
ping 192.168.1.50
telnet 192.168.1.50 1883
```

### "Senzori nu se actualizează"

1. Verifică că sender_mqtt.py rulează (nu sender.py!)
2. Verifică că MQTT broker e pornit
3. Verifică logs în GUI

### "Comenzi nu ajung la Pi"

1. Click "Connect MQTT" în GUI
2. Verifică că broker e pe IP corect
3. Verifică firewall Windows permite 1883

---

## 📋 Checklist Complet

```
☐ MQTT Broker instalat pe Windows
☐ Mosquitto pornit (mosquitto -v)
☐ Signaling server pornit (terminal 1)
☐ sender_mqtt.py pornit pe Pi (NU sender.py!)
☐ receiver_gui_mqtt.py pornit (terminal 2)
☐ Click "Connect MQTT" în GUI
☐ Click "Connect WebRTC" în GUI
☐ Video stream vizibil
☐ Date senzori se actualizează
☐ Comenzi se trimit (testează cu sliders)
```

---

## 🎉 Success!

Dacă vezi:
- ✅ Video streaming
- ✅ Date senzori actualizate
- ✅ Timestamp-uri sincronizate
- ✅ Comenzi se trimit

**Felicitări! Integrarea MQTT + WebRTC funcționează!** 🚀

---

## 📚 Vezi și

- [MQTT_INTEGRATION.md](MQTT_INTEGRATION.md) - Detalii complete integrare
- [README.md](README.md) - Documentație generală
- [COMPONENT_LOCATIONS.md](COMPONENT_LOCATIONS.md) - Arhitectură

---

**Timp estimat setup:** 10-15 minute
