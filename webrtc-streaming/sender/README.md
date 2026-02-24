# Sender - Raspberry Pi Components

Acest director conține componentele care rulează pe Raspberry Pi 5.

## Fișiere

### `sender.py`
Aplicația principală care citește video din fișier, adaugă timestamp și trimite frames prin WebRTC.

**Rulare:**
```bash
python3 sender.py --video video.mp4 --server-ip 192.168.1.50
```

**Optimizat pentru consum minim de resurse!**
- Nu rulează HTTP server (acesta este pe Windows)
- Se concentrează doar pe video processing
- Consumă ~30-45% CPU și ~250-350 MB RAM la 720p @ 30 FPS

### `generate_test_video.py`
Script helper pentru generarea unui video de test dacă nu ai unul disponibil.

**Rulare:**
```bash
python3 generate_test_video.py --output video.mp4 --duration 30 --fps 30
```

**Parametri:**
- `--output`: Nume fișier de ieșire
- `--duration`: Durata în secunde (default: 30)
- `--fps`: Frame rate (default: 30)
- `--width`: Lățime video (default: 1280)
- `--height`: Înălțime video (default: 720)

### `requirements.txt`
Toate dependențele necesare pentru Raspberry Pi.

**Instalare:**
```bash
pip3 install -r requirements.txt
```

## Utilizare

### Pregătire Video

**Opțiune 1: Folosește video propriu**
```bash
# Copiază video în acest director
cp /path/to/your/video.mp4 video.mp4
```

**Opțiune 2: Generează video de test**
```bash
python3 generate_test_video.py --output video.mp4 --duration 60
```

**Opțiune 3: Descarcă video de test**
```bash
wget https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4 -O video.mp4
```

### Pornire Sender

**Metoda simplă (cu script helper):**
```bash
cd ..  # Înapoi la root
./start_pi.sh 192.168.1.50 video.mp4 30
```

**Metoda manuală:**
```bash
python3 sender.py \
    --video video.mp4 \
    --fps 30 \
    --server-ip 192.168.1.50
```

## Parametri

### `--video PATH`
Calea către fișierul video.
- **Default:** `video.mp4`
- **Formate suportate:** MP4, AVI, MOV, MKV (orice format suportat de OpenCV)

### `--fps FPS`
Frame rate țintă pentru streaming.
- **Default:** 30
- **Recomandări:**
  - 30 FPS: Calitate bună, consum normal
  - 24 FPS: Cinematic, consum redus
  - 20 FPS: Consum foarte redus
  - 15 FPS: Pentru Pi supraîncărcat

### `--server-ip IP` (REQUIRED)
IP-ul laptop-ului Windows unde rulează signaling server.
- Găsește-l cu `ipconfig` pe Windows
- Exemplu: `192.168.1.50`

### `--server-port PORT`
Portul signaling server.
- **Default:** 8080
- Schimbă doar dacă ai modificat portul pe server

## Optimizare Performanță

### CPU Prea Mare?

**1. Reduce FPS:**
```bash
python3 sender.py --video video.mp4 --fps 20 --server-ip 192.168.1.50
```

**2. Reduce rezoluția video:**
```bash
# Pre-procesează video-ul
ffmpeg -i input.mp4 -vf scale=960:540 output.mp4
python3 sender.py --video output.mp4 --server-ip 192.168.1.50
```

**3. Verifică procese în background:**
```bash
htop  # Oprește procese nefolosite
```

### Temperatură Prea Mare?

```bash
# Monitorizează temperatura
watch -n 1 vcgencmd measure_temp

# Adaugă cooling:
# - Heatsink pe procesor
# - Ventilator 5V
# - Carcasă cu ventilație
```

### Memorie Insuficientă?

```bash
# Verifică memoria
free -h

# Închide aplicații nefolosite
# Consideră swap increase (ultimă soluție)
```

## Monitorizare

### Verificare Status în Timp Real

```bash
# CPU și RAM
htop

# Temperatura
watch -n 1 vcgencmd measure_temp

# Network bandwidth
iftop

# Toate împreună
htop & watch -n 1 vcgencmd measure_temp
```

### Valori Normale (720p @ 30 FPS)

| Metric | Valoare Normală | Prea Mare |
|--------|----------------|-----------|
| CPU | 30-45% | > 60% |
| RAM | 250-350 MB | > 500 MB |
| Temp | 50-65°C | > 75°C |
| Upload | 2-4 Mbps | N/A |

## Troubleshooting

### "Video file not found"
```bash
# Verifică că fișierul există
ls -lh video.mp4

# Sau folosește cale absolută
python3 sender.py --video /home/pi/videos/test.mp4 --server-ip 192.168.1.50
```

### "Signaling server is not responding"
```bash
# Verifică conectivitatea
ping 192.168.1.50

# Testează manual
curl http://192.168.1.50:8080/health
# Ar trebui: {"status": "ok"}
```

### "Error creating video track"
```bash
# Verifică că OpenCV poate citi video-ul
python3 -c "import cv2; cap = cv2.VideoCapture('video.mp4'); print(cap.isOpened())"
# Ar trebui: True

# Dacă False, video-ul e corupt sau format nesuportat
```

### Frame drops sau lag
1. **Reduce FPS:** `--fps 20`
2. **Verifică rețeaua:** `ping 192.168.1.50`
3. **Închide procese:** verifică cu `htop`
4. **Folosește Ethernet:** mai stabil decât WiFi

## Dependențe

- **aiortc**: WebRTC implementation
- **aiohttp**: HTTP client
- **opencv-python**: Video processing
- **av**: Video codecs (PyAV)
- **numpy**: Array operations

## Tips

1. **Testează cu video scurt** (30 sec) înainte de unul lung
2. **Monitorizează temperatura** constant
3. **Folosește Ethernet** pentru stabilitate
4. **Începe cu FPS mai mic** (20) și crește gradual
5. **Generează test video** dacă nu ai unul disponibil

## Vezi și

- [../QUICKSTART.md](../QUICKSTART.md) - Ghid rapid
- [../OPTIMIZATION.md](../OPTIMIZATION.md) - Optimizare performanță
- [../CHECKLIST.md](../CHECKLIST.md) - Checklist complet
- [../COMPONENT_LOCATIONS.md](../COMPONENT_LOCATIONS.md) - Unde rulează fiecare componentă
