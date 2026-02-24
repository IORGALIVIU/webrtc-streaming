# Ghid Rapid de Instalare și Utilizare

## 1. Pregătire Raspberry Pi 5

### Instalare Python și dependențe sistem
```bash
sudo apt update
sudo apt install -y python3-pip python3-opencv
```

### Instalare dependențe Python
```bash
cd sender/
pip3 install -r requirements.txt
```

### Pregătire video
Copiază un fișier video în folder-ul `sender/`:
```bash
# Exemplu: descarcă un video de test
wget https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4 -O video.mp4
```

Sau folosește orice fișier MP4/AVI pe care îl ai.

## 2. Pregătire Windows

### Instalare Python
1. Descarcă Python 3.10+ de pe [python.org](https://www.python.org/downloads/)
2. Asigură-te că bifezi "Add Python to PATH" la instalare

### Instalare dependențe
```bash
cd receiver/
pip install -r requirements.txt
```

## 3. Găsește IP-ul Laptop-ului Windows

Pe Windows, deschide Command Prompt și rulează:
```bash
ipconfig
```

Caută "IPv4 Address" pentru conexiunea ta (WiFi sau Ethernet).
Notează IP-ul (ex: `192.168.1.50`)

## 4. Rulare

### Pe Windows - Terminal 1: Pornește Signaling Server
```bash
cd receiver/
python signaling_server.py
```

Ar trebui să vezi:
```
INFO - Signaling server (simple) running on http://0.0.0.0:8080
```

**IMPORTANT:** Lasă acest terminal deschis!

### Pe Raspberry Pi: Pornește Sender
```bash
cd sender/
python3 sender.py --video video.mp4 --server-ip 192.168.1.50
```

**Înlocuiește `192.168.1.50` cu IP-ul laptop-ului tău Windows** (cel notat la pasul 3).

Ar trebui să vezi:
```
INFO - Video loaded: 1280x720, 30.00 FPS, 900 frames
INFO - Signaling server is healthy
INFO - Sending offer to signaling server...
```

### Pe Windows - Terminal 2: Pornește Receiver GUI
```bash
cd receiver/
python receiver_gui.py --server-ip 127.0.0.1
```

Se va deschide fereastra aplicației. Apasă butonul **"Connect"**.

## 5. Verificare

Dacă totul merge bine, vei vedea:

**Pe Windows (Terminal 1 - Signaling Server):**
```
INFO - Signaling server (simple) running on http://0.0.0.0:8080
INFO - Offer received and stored
INFO - Answer received and stored
```

**Pe Raspberry Pi (Sender):**
```
INFO - WebRTC connection established!
INFO - Streaming video at 30 FPS...
```

**Pe Windows (Terminal 2 - Receiver GUI):**
- Status: "Connected" (verde)
- Video stream afișat în fereastră
- Statistici actualizate în panoul din dreapta

## Rezumat Flow:

```
Windows Terminal 1        Raspberry Pi           Windows Terminal 2
(Signaling Server)        (Video Sender)         (Receiver GUI)
      │                        │                        │
      │◄───── Offer SDP ───────┤                        │
      │                        │                        │
      ├────── Offer ──────────────────────────────────► │
      │                        │                        │
      │◄────── Answer ─────────────────────────────────┤
      │                        │                        │
      ├────── Answer ──────────►                        │
      │                        │                        │
      │    [Server IDLE]       │◄═════ Video P2P ═════►│
      │                        │    (Direct stream)     │
```

**Important:** După conectare, video-ul curge DIRECT între Pi și Windows.
Signaling server-ul devine inactiv și poate fi oprit (opțional).

## Troubleshooting Rapid

### "Connection refused"
- Verifică că signaling server rulează pe Windows (Terminal 1)
- Verifică firewall-ul pe Windows:
  - Permite portul 8080 în Windows Defender Firewall
  - Sau dezactivează temporar firewall-ul pentru test

### "Signaling server is not responding"
- Verifică conectivitatea de la Pi la Windows:
  ```bash
  # Pe Raspberry Pi
  ping 192.168.1.50  # IP-ul Windows
  curl http://192.168.1.50:8080/health
  # Ar trebui: {"status": "ok"}
  ```
- Verifică că IP-ul Windows este corect (folosit la `--server-ip`)

### "Video file not found"
- Verifică că `video.mp4` există în folder-ul `sender/`
- Sau specifică calea completă:
  ```bash
  python3 sender.py --video /path/to/your/video.mp4
  ```

### Video încetinit sau frame drops
- Reduce FPS-ul:
  ```bash
  python3 sender.py --video video.mp4 --fps 15 --server-ip 192.168.1.50
  ```
  *Înlocuiește 192.168.1.50 cu IP-ul Windows*

### Eroare "No module named 'aiortc'"
- Reinstalează dependențele:
  ```bash
  pip3 install --upgrade -r requirements.txt
  ```

## Comenzi Utile

### Oprire grațioasă
- Sender/Receiver: `Ctrl+C`
- Sau închide fereastra GUI

### Verificare loguri
Toate aplicațiile afișează loguri detaliate în consolă.

### Schimbă portul
Dacă portul 8080 este ocupat:

```bash
# Windows - Signaling Server
python signaling_server.py --port 9090

# Raspberry Pi - Sender
python3 sender.py --video video.mp4 --server-port 9090 --server-ip 192.168.1.50

# Windows - Receiver
python receiver_gui.py --server-ip 127.0.0.1 --server-port 9090
```

*Înlocuiește 192.168.1.50 cu IP-ul Windows*

## Next Steps

După ce totul funcționează:
1. Încearcă cu diferite videoclipuri
2. Ajustează FPS-ul pentru performanță optimă
3. Monitorizează statisticile în GUI
4. Experimentează cu rezoluții diferite

Succes! 🚀
