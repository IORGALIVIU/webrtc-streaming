# 🔗 Integrare MQTT cu WebRTC

## 📋 Overview

Proiectul integrat combină:
- **WebRTC**: Video streaming cu timestamp
- **MQTT**: Date senzori sincronizate + comenzi bidireționale

### Arhitectură Integrată

```
🍓 RASPBERRY PI:
├─ sender_mqtt.py
│  ├─ WebRTC: Trimite video cu timestamp
│  ├─ MQTT Publish: unghi, viteza (sincronizat cu timestamp)
│  └─ MQTT Subscribe: mod, unghi_manual, viteza_manual

💻 WINDOWS:
├─ signaling_server.py (WebRTC signaling)
├─ MQTT Broker (Mosquitto - trebuie instalat separat)
└─ receiver_gui_mqtt.py
   ├─ WebRTC: Primește video
   ├─ MQTT Subscribe: unghi, viteza (sincronizat cu frame-uri)
   ├─ MQTT Publish: comenzi control
   └─ GUI: Afișare video + date + control panel
```

## 🚀 Instalare

### Windows - MQTT Broker (Mosquitto)

**Opțiunea 1: Instalare oficială**
```powershell
# Download de pe: https://mosquitto.org/download/
# Instalează Mosquitto pentru Windows
# Start broker:
net start mosquitto
# sau
mosquitto -v
```

**Opțiunea 2: Broker Python simplu**
```powershell
pip install paho-mqtt
# Folosește un broker extern sau cloud (ex: test.mosquitto.org)
```

### Raspberry Pi - Dependențe

```bash
pip3 install paho-mqtt
```

## 📡 Topic-uri MQTT

### De la Raspberry Pi → Windows (Senzori)
**Topic:** `robot/senzori`
```json
{
  "unghi": 45.5,
  "viteza": 75.3,
  "timestamp": 1704295200123,
  "timestamp_iso": "2024-01-03T12:00:00.123"
}
```

### De la Windows → Raspberry Pi (Comenzi)

**1. Mod de funcționare**
**Topic:** `robot/control/mod`
```json
{
  "mod_de_functionare": 1  // 0=auto, 1=manual
}
```

**2. Unghi manual**
**Topic:** `robot/control/unghi_manual`
```json
{
  "unghi_manual": 90.0  // grade
}
```

**3. Viteză manuală**
**Topic:** `robot/control/viteza_manual`
```json
{
  "viteza_manual": 50.0  // RPM
}
```

## 🎯 Utilizare

### Pas 1: Pornește MQTT Broker (Windows)

```powershell
# Dacă ai Mosquitto instalat:
mosquitto -v

# Broker-ul va rula pe localhost:1883
```

### Pas 2: Pornește Signaling Server (Windows - Terminal 1)

```powershell
cd receiver
python signaling_server.py
```

### Pas 3: Pornește Sender cu MQTT (Raspberry Pi)

```bash
cd sender
python3 sender_mqtt.py \
    --video video.mp4 \
    --fps 30 \
    --server-ip 192.168.1.50 \
    --mqtt-broker 192.168.1.50
```

**Parametri:**
- `--server-ip`: IP Windows (pentru WebRTC signaling)
- `--mqtt-broker`: IP Windows (pentru MQTT broker)
- Ambele sunt de obicei același IP!

### Pas 4: Pornește Receiver GUI cu MQTT (Windows - Terminal 2)

```powershell
cd receiver
python receiver_gui_mqtt.py --server-ip 127.0.0.1 --mqtt-broker localhost
```

### Pas 5: Conectează în GUI

1. Click **"Connect MQTT"** - Se conectează la broker
2. Click **"Connect WebRTC"** - Pornește video streaming
3. Folosește control panel-ul pentru a trimite comenzi

## 🔄 Sincronizare Timestamp

### Cum Funcționează

1. **Raspberry Pi**:
   - Frame video are timestamp `T` (ms)
   - Date senzori publicate cu același timestamp `T`

2. **Windows**:
   - Primește frame video cu timestamp `T`
   - Caută date senzori cu timestamp `≈T` (toleranță ±200ms)
   - Afișează sincronizat

### Buffer de Sincronizare

```python
# În receiver_gui_mqtt.py
sensor_data_buffer = {
    1704295200123: {"unghi": 45.5, "viteza": 75.3},
    1704295200223: {"unghi": 46.1, "viteza": 74.8},
    ...
}

# Găsește cea mai apropiată valoare de timestamp
closest_data = get_sensor_data_at_timestamp(frame_timestamp, tolerance=200)
```

## 🎮 Control Panel (GUI)

### Mode Control
- **Auto (0)**: Robotul funcționează autonom
- **Manual (1)**: Control manual prin comenzi

### Manual Controls
- **Angle Slider**: -180° la +180°
- **Speed Slider**: 0 la 100 RPM
- **Send Commands**: Trimite toate comenzile odată

### Afișare Date
- **Unghi**: Valoare curentă sincronizată cu frame-ul
- **Viteza**: Valoare curentă sincronizată cu frame-ul
- **Timestamp**: Timestamp-ul datelor afișate

## 📊 Flow Detaliat

```
┌─────────────────────────────────────────────────────────────┐
│ Raspberry Pi - Frame N (timestamp T)                        │
├─────────────────────────────────────────────────────────────┤
│ 1. Citește frame video                                      │
│ 2. Generează timestamp T = current_time_ms()                │
│ 3. Citește/simulează senzori: unghi=45°, viteza=75 RPM     │
│ 4. Publică MQTT: {unghi, viteza, timestamp: T}             │
│ 5. Adaugă overlay pe frame cu timestamp T                   │
│ 6. Trimite frame prin WebRTC                                │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ WebRTC (video)
                    │ MQTT (date)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ Windows - Primire și Sincronizare                           │
├─────────────────────────────────────────────────────────────┤
│ 1. Primește frame video (timestamp T în overlay)            │
│ 2. Primește date MQTT: {unghi, viteza, timestamp: T}       │
│ 3. Stochează în buffer: buffer[T] = {unghi, viteza}        │
│ 4. La afișare frame:                                        │
│    - Extrage T din frame                                    │
│    - Caută buffer[T] (toleranță ±200ms)                    │
│    - Afișează date sincronizate lângă video                │
│ 5. User schimbă control → publică comandă MQTT             │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ MQTT (comenzi)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ Raspberry Pi - Primire Comenzi                              │
├─────────────────────────────────────────────────────────────┤
│ 1. Primește comandă: mod=1 (manual)                        │
│ 2. Primește: unghi_manual=90, viteza_manual=60            │
│ 3. Aplică comenzile (în frame următ