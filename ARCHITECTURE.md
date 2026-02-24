# Arhitectura Proiectului WebRTC Streaming

## Overview

Acest document descrie arhitectura tehnică a sistemului de streaming video WebRTC între Raspberry Pi și Windows.

## Componente Principale

```
┌─────────────────────────────────────────────────────────────────┐
│                           WINDOWS PC                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────┐      ┌─────────────────────────┐  │
│  │  Signaling Server      │      │   Receiver GUI          │  │
│  │  (HTTP Server)         │      │   Application           │  │
│  │                        │      │                         │  │
│  │  - Stores SDP Offers   │      │  ┌──────────────────┐   │  │
│  │  - Stores SDP Answers  │      │  │ Video Display    │   │  │
│  │  - Port 8080          │      │  │ (Tkinter+OpenCV) │   │  │
│  │  - signaling_server.py │      │  │                  │   │  │
│  └────────────────────────┘      │  │ - Render frames  │   │  │
│                                   │  │ - Show stats     │   │  │
│                                   │  │ - UI controls    │   │  │
│                                   │  └──────────────────┘   │  │
│                                   │           │             │  │
│                                   │           ▼             │  │
│                                   │  ┌──────────────────┐   │  │
│                                   │  │ RTCPeerConnection│   │  │
│                                   │  │ (aiortc)         │   │  │
│                                   │  └──────────────────┘   │  │
│                                   └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ WebRTC Data Channel
                              │ (DTLS/SRTP encrypted)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         RASPBERRY PI 5                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    Video Sender                         │  │
│  │                    (sender.py)                          │  │
│  │                                                         │  │
│  │  ┌──────────────────┐                                   │  │
│  │  │ VideoFileTrack   │                                   │  │
│  │  │                  │                                   │  │
│  │  │ - Read Video     │                                   │  │
│  │  │ - Add Timestamp  │                                   │  │
│  │  │ - Encode Frame   │                                   │  │
│  │  └──────────────────┘                                   │  │
│  │           │                                             │  │
│  │           ▼                                             │  │
│  │  ┌──────────────────┐                                   │  │
│  │  │ RTCPeerConnection│                                   │  │
│  │  │ (aiortc)         │                                   │  │
│  │  │                  │                                   │  │
│  │  │ - Signaling      │───> Conectează la Windows:8080   │  │
│  │  │   Client         │                                   │  │
│  │  └──────────────────┘                                   │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Arhitectură Optimizată

**DE CE Signaling Server pe Windows?**

- ✅ **Minimizează consumul pe Pi**: -30% CPU, -120 MB RAM
- ✅ **Windows are resurse**: Laptop-ul suportă ușor server-ul
- ✅ **Pi se concentrează pe video**: 100% resurse pentru procesare video
- ✅ **Flexibil**: După conectare, signaling devine inactiv (poate fi oprit)

**După stabilirea conexiunii WebRTC:**
- Video curge **DIRECT** Pi → Windows (P2P)
- Signaling server nu mai este folosit (devine inactiv)
- Conexiunea este criptată (DTLS/SRTP)

## Flow de Date

### 1. Stabilirea Conexiunii (Signaling)

```
Sender (Pi)             Signaling Server (Win)     Receiver (Win)
  │                            │                       │
  │  1. Create Offer (SDP)     │                       │
  ├───────────────────────────>│                       │
  │                            │                       │
  │                            │  2. Poll for Offer    │
  │                            │<──────────────────────┤
  │                            │                       │
  │                            │  3. Return Offer      │
  │                            ├──────────────────────>│
  │                            │                       │
  │                            │  4. Create Answer     │
  │                            │<──────────────────────┤
  │                            │                       │
  │  5. Poll for Answer        │                       │
  │<───────────────────────────┤                       │
  │                            │                       │
  │  6. Return Answer          │                       │
  ├───────────────────────────>│                       │
  │                            │                       │
  │    7. WebRTC P2P Connection Established           │
  │<═══════════════════════════════════════════════════>│
```

### 2. Transmisia Video

```
Sender (Raspberry Pi)
    │
    ├─> Read video file (video.mp4)
    │
    ├─> For each frame:
    │   │
    │   ├─> Decode frame (OpenCV)
    │   │
    │   ├─> Add timestamp overlay
    │   │   - Current timestamp (ms)
    │   │   - Frame number
    │   │   - Elapsed time
    │   │
    │   ├─> Convert BGR → RGB
    │   │
    │   ├─> Create VideoFrame (av library)
    │   │
    │   └─> Send via WebRTC (aiortc)
    │       - Automatic encoding (VP8/H264)
    │       - DTLS encryption
    │       - RTP packetization
    │
    ▼
[WebRTC P2P Channel]
    │
    ▼
Receiver (Windows)
    │
    ├─> Receive VideoFrame
    │
    ├─> Decode frame
    │
    ├─> Convert to numpy array
    │
    ├─> Put in display queue
    │
    └─> GUI Thread:
        │
        ├─> Get frame from queue
        │
        ├─> Resize for display
        │
        ├─> Convert to PIL Image
        │
        ├─> Convert to ImageTk
        │
        └─> Update Tkinter Label
```

## Stack Tehnologic

### Raspberry Pi (Sender)

| Componentă | Tehnologie | Rol |
|------------|------------|-----|
| Runtime | Python 3.10+ | Execuție cod |
| WebRTC | aiortc | Peer connection, codec |
| Video Processing | OpenCV | Citire video, manipulare frames |
| Video Encoding | av (PyAV) | Wrapper FFmpeg pentru encoding |
| HTTP Client | aiohttp | Client signaling |
| Async | asyncio | Event loop pentru operații async |

### Windows (Receiver)

| Componentă | Tehnologie | Rol |
|------------|------------|-----|
| Runtime | Python 3.10+ | Execuție cod |
| WebRTC | aiortc | Peer connection, codec |
| GUI Framework | Tkinter | Interfață grafică |
| Image Processing | OpenCV, Pillow | Procesare și afișare imagini |
| Video Decoding | av (PyAV) | Wrapper FFmpeg pentru decoding |
| HTTP Server | aiohttp | Signaling server |
| HTTP Client | aiohttp | Client signaling |
| Async | asyncio + threading | Event loop + GUI thread |

## Protocoale și Standarde

### WebRTC Stack

```
Application Layer
    │
    ├─> Video Track (VideoStreamTrack)
    │
    ▼
WebRTC APIs (aiortc)
    │
    ├─> RTCPeerConnection
    ├─> RTCSessionDescription (SDP)
    ├─> ICE (Interactive Connectivity Establishment)
    │
    ▼
Transport Layer
    │
    ├─> DTLS (Datagram Transport Layer Security)
    ├─> SRTP (Secure Real-time Transport Protocol)
    │
    ▼
Network Layer
    │
    ├─> UDP (primary)
    ├─> TCP (fallback)
    │
    ▼
IP Layer
```

### Video Encoding

```
Raw Frame (BGR/RGB)
    │
    ▼
Video Encoder
    │
    ├─> VP8 (default in aiortc)
    │   - Open source
    │   - Good compression
    │   - Low latency
    │
    └─> Alternative: H.264
        - Better compression
        - Hardware acceleration
        - Licensing considerations
    │
    ▼
RTP Packets
    │
    ▼
Network
```

## Thread Model

### Sender (Raspberry Pi)

```
Main Thread
    │
    ├─> Parse arguments
    ├─> Setup logging
    └─> Start asyncio event loop
        │
        └─> WebRTC Sender
            │
            ├─> Signaling client
            │   └─> HTTP requests to Windows (non-blocking)
            │
            └─> Video track
                └─> Frame reading loop
                    - Read from video file
                    - Process frame
                    - Send to peer
```

### Receiver (Windows)

```
Main Thread (GUI)
    │
    ├─> Create Tkinter window
    ├─> Setup UI components
    └─> Tkinter mainloop
        │
        ├─> UI event handlers
        │   - Button clicks
        │   - Window events
        │
        └─> Periodic updates
            - Video display (33ms)
            - Stats display (500ms)

Asyncio Thread
    │
    └─> Event loop
        │
        ├─> Signaling server
        │   └─> HTTP request handlers
        │
        ├─> Signaling client
        │   └─> HTTP requests
        │
        └─> WebRTC receiver
            └─> Video track processing
                - Receive frames
                - Decode frames
                - Queue for display

Communication: queue.Queue (thread-safe)
```

## Securitate

### Encryption

- **Signaling**: HTTP (plain text)
  - Poate fi upgradată la HTTPS
  - Doar pentru SDP exchange (nu conține date sensibile)

- **Media**: DTLS + SRTP
  - Automatic în WebRTC
  - End-to-end encryption
  - Perfect forward secrecy

### Network Security

- **Firewall**: Portul 8080 trebuie deschis pe Windows
- **NAT Traversal**: ICE cu STUN/TURN (opțional pentru rețele complexe)

## Optimizări

### Bandwidth

- Encoding adaptiv (implicit în aiortc)
- FPS configurable
- Rezoluție configurabilă (prin resize în sender)

### Latency

- UDP pentru transport (default)
- Buffer minim în receiver (queue size = 10)
- Direct rendering (fără save to disk)

### CPU

- Hardware acceleration (dacă disponibil)
- Frame rate control
- Rezoluție optimă

## Extensibilitate

### Features Posibile

1. **Audio streaming**
   - Add audio track
   - Microphone input

2. **Bidirectional streaming**
   - Both devices send/receive
   - Video conferencing

3. **Recording**
   - Save received stream
   - Timestamps for sync

4. **Multiple receivers**
   - Broadcast to multiple clients
   - SFU (Selective Forwarding Unit)

5. **Quality controls**
   - Adaptive bitrate
   - Resolution switching
   - FPS throttling

6. **Advanced signaling**
   - WebSocket pentru real-time
   - MQTT pentru IoT
   - Dedicated signaling server

## Limitări Curente

1. **Single peer**: Un sender, un receiver
2. **HTTP signaling**: Polling-based, nu real-time
3. **No TURN**: NAT traversal limitat
4. **No authentication**: Oricine poate conecta
5. **No persistence**: State lost on restart

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Latency | < 500ms | End-to-end |
| Frame Rate | 30 FPS | Configurable |
| Resolution | 1280x720 | Default |
| CPU (Pi) | < 45% | At 30 FPS (optimized!) |
| CPU (Win) | < 20% | Signaling + GUI + decoding |
| Network | ~2-5 Mbps | Depends on resolution |

## Debugging

### Logs

Toate componentele folosesc Python `logging`:
- Level: INFO (production)
- Level: DEBUG (development)

### Tools

- **Wireshark**: Analiza trafic WebRTC
- **chrome://webrtc-internals**: Pentru debugging WebRTC (dacă folosești browser)
- **htop/Task Manager**: Monitorizare CPU/Memory

### Common Issues

Vezi `QUICKSTART.md` pentru troubleshooting detaliat.
