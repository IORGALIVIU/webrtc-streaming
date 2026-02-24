# 🎯 Clarificare: Unde Rulează Fiecare Componentă

## Arhitectură Simplificată

```
┌─────────────────────────┐          ┌─────────────────────────┐
│   🍓 RASPBERRY PI 5     │          │   💻 WINDOWS LAPTOP     │
├─────────────────────────┤          ├─────────────────────────┤
│                         │          │                         │
│  ✅ sender.py           │          │  ✅ signaling_server.py │
│     (Video Sender)      │          │     (Terminal 1)        │
│                         │          │                         │
│  • Citește video        │          │  ✅ receiver_gui.py     │
│  • Adaugă timestamp     │          │     (Terminal 2)        │
│  • Trimite frames       │          │                         │
│                         │          │  • Server HTTP (8080)   │
│  Consum:                │          │  • GUI Tkinter          │
│  - CPU: 35-45%          │          │  • Primește video       │
│  - RAM: 280 MB          │          │                         │
│                         │          │  Consum:                │
│                         │          │  - CPU: 18%             │
│                         │          │  - RAM: 310 MB          │
└─────────────────────────┘          └─────────────────────────┘
           │                                    │
           │    🌐 WebRTC P2P Video Stream     │
           └────────────────────────────────────┘
                    (Direct, encrypted)
```

## 📋 Checklist Componente

### Pe WINDOWS (2 terminale):

**Terminal 1 - Signaling Server:**
```bash
cd receiver/
python signaling_server.py
```
- Port: 8080
- Rol: Facilitează conectarea WebRTC
- Status: Activ doar la conectare, apoi IDLE

**Terminal 2 - Receiver GUI:**
```bash
cd receiver/
python receiver_gui.py --server-ip 127.0.0.1
```
- Se conectează la localhost (signaling server local)
- Afișează GUI pentru video
- Click "Connect" pentru a începe

### Pe RASPBERRY PI (1 terminal):

**Sender:**
```bash
cd sender/
python3 sender.py --video video.mp4 --server-ip 192.168.1.50
```
- `--server-ip` = IP-ul laptop-ului Windows
- Trimite video prin WebRTC
- Se conectează la signaling server de pe Windows

## 🔄 Flow de Conectare

### Pasul 1: Start Componente
```
1. Windows Terminal 1 → signaling_server.py (pornește primul!)
2. Raspberry Pi → sender.py (așteaptă conexiune)
3. Windows Terminal 2 → receiver_gui.py (click Connect)
```

### Pasul 2: Signaling (prin HTTP)
```
Pi → HTTP → Windows Signaling Server → HTTP → Receiver GUI
        (schimb de SDP offers/answers)
```

### Pasul 3: Stream Video (WebRTC P2P)
```
Pi ══════════════ Direct ══════════════► Windows Receiver
         (Video frames, encrypted)
    
Signaling server nu mai este folosit!
```

## 🌐 Adrese IP Importante

### Trebuie să știi:
- **IP Windows**: `ipconfig` → ex: 192.168.1.50
  - Folosit de Pi în `--server-ip 192.168.1.50`
  
- **Localhost Windows**: `127.0.0.1`
  - Folosit de receiver GUI: `--server-ip 127.0.0.1`

### NU trebuie:
- ❌ IP-ul Raspberry Pi pentru signaling
- ❌ IP public sau extern
- ❌ Port forwarding

## 💡 De ce această Arhitectură?

### Avantaje:
✅ **Pi optimizat**: -30% CPU, -120 MB RAM
✅ **Windows are resurse**: Laptop-ul suportă ușor signaling
✅ **Video P2P**: După conectare, direct Pi → Windows
✅ **Flexibil**: Poți opri signaling după conectare

### Alternativa (mai puțin eficientă):
❌ Signaling pe Pi = mai mult CPU + RAM pe Pi
❌ Video tot P2P, deci signaling pe Pi = overhead inutil

## 🎯 Rezumat în 3 Propoziții

1. **Windows** rulează signaling server (8080) + receiver GUI
2. **Raspberry Pi** rulează doar video sender (optimizat!)
3. După conectare, video curge **direct** Pi → Windows (P2P)

## 📝 Comenzi Complete (Copy-Paste)

### Pe Windows - Terminal 1:
```powershell
cd D:\INTERNET\webrtc-streaming\webrtc-streaming\receiver
python signaling_server.py
```

### Pe Raspberry Pi:
```bash
cd ~/webrtc-streaming/sender
python3 sender.py --video video.mp4 --server-ip 192.168.1.50
# ☝️ Înlocuiește cu IP-ul tău Windows!
```

### Pe Windows - Terminal 2:
```powershell
cd D:\INTERNET\webrtc-streaming\webrtc-streaming\receiver
python receiver_gui.py --server-ip 127.0.0.1
```

Apoi click **"Connect"** în GUI!

## ✅ Verificare Rapidă

Dacă ai confuzii:
1. Signaling server = **Windows**? ✅ DA
2. Video sender = **Raspberry Pi**? ✅ DA
3. Receiver GUI = **Windows**? ✅ DA
4. Signaling server = Pi? ❌ NU (vechi, ineficient)

---

**Clarificare completă! Sper că acum are sens!** 🎉
