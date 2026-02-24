# Receiver - Windows Components

Acest director conține componentele care rulează pe Windows.

## Fișiere

### `signaling_server.py`
Server HTTP simplu pentru schimbul de SDP offers/answers între sender și receiver.

**Rulare:**
```bash
python signaling_server.py
```

**De ce pe Windows?**
- Minimizează consumul de resurse pe Raspberry Pi
- Windows are suficiente resurse pentru a gestiona server-ul
- După stabilirea conexiunii, server-ul devine inactiv

### `receiver_gui.py`
Aplicație desktop cu interfață grafică pentru primirea și afișarea video stream-ului.

**Rulare:**
```bash
python receiver_gui.py --server-ip 127.0.0.1
```

**Features:**
- Afișare video în timp real
- Statistici conexiune (FPS, rezoluție, frames primite)
- Control butoane (Connect/Disconnect)
- Log viewer integrat

### `requirements.txt`
Toate dependențele necesare pentru Windows.

**Instalare:**
```bash
pip install -r requirements.txt
```

**Pentru Python 3.14:** Vezi `requirements-py314.txt` sau [WINDOWS_PYTHON_314_FIX.md](../WINDOWS_PYTHON_314_FIX.md)

## Workflow Tipic

### Terminal 1: Signaling Server
```bash
python signaling_server.py
```
Lasă acest terminal deschis pe toată durata streaming-ului.

### Terminal 2: Receiver GUI
```bash
python receiver_gui.py --server-ip 127.0.0.1
```
După ce GUI se deschide, apasă "Connect".

## Configurare Firewall Windows

Dacă întâmpini probleme de conexiune, permite portul 8080:

### Windows Defender Firewall
1. Deschide "Windows Defender Firewall with Advanced Security"
2. Click "Inbound Rules" → "New Rule"
3. Selectează "Port" → Next
4. TCP, Specific port: 8080 → Next
5. Allow the connection → Next
6. Bifează toate profilurile → Next
7. Nume: "WebRTC Signaling Server" → Finish

### Sau prin Command Prompt (ca Administrator):
```cmd
netsh advfirewall firewall add rule name="WebRTC Signaling" dir=in action=allow protocol=TCP localport=8080
```

## Troubleshooting

### "Cannot import aiortc"
```bash
pip install --upgrade aiortc
```

### GUI nu se deschide
Verifică că Tkinter este instalat:
```bash
python -c "import tkinter"
```

Dacă eroare, reinstalează Python cu Tk/Tcl support.

### "Connection refused"
1. Verifică că signaling server rulează
2. Verifică firewall-ul
3. Testează cu: `curl http://localhost:8080/health`

### Video lag sau freeze
1. Verifică CPU usage (Task Manager)
2. Închide alte aplicații heavy
3. Cere sender-ului să reducă FPS

## Dependențe

- **aiortc**: WebRTC implementation
- **aiohttp**: HTTP client/server
- **opencv-python**: Video processing
- **av**: Video codecs
- **Pillow**: Image handling pentru GUI
- **tkinter**: GUI framework (built-in cu Python)

## Tips

1. **Păstrează signaling server pornit** pe toată durata streaming-ului
2. **Închide corect** aplicațiile cu Ctrl+C (nu forțat)
3. **Monitorizează statisticile** în GUI pentru debugging
4. **Citește log-urile** pentru informații detaliate despre conexiune

## Vezi și

- [../QUICKSTART.md](../QUICKSTART.md) - Ghid rapid
- [../OPTIMIZATION.md](../OPTIMIZATION.md) - De ce signaling pe Windows
- [../CHECKLIST.md](../CHECKLIST.md) - Checklist complet
- [../COMPONENT_LOCATIONS.md](../COMPONENT_LOCATIONS.md) - Unde rulează fiecare componentă
