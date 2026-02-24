# Configuration file for WebRTC Streaming
# Copy this to config.local.py and customize

# Signaling Server Configuration
SIGNALING_HOST = "0.0.0.0"  # Listen on all interfaces
SIGNALING_PORT = 8080

# Video Configuration
DEFAULT_FPS = 30
DEFAULT_RESOLUTION = (1280, 720)  # Width x Height
VIDEO_CODEC = "VP8"  # VP8 or H264

# Network Configuration
# IMPORTANT: Set this to your Windows laptop's IP address!
# Find it with: ipconfig (Windows) or ifconfig (Linux/Mac)
WINDOWS_LAPTOP_IP = "192.168.1.50"  # CHANGE THIS to your Windows IP!
RASPBERRY_PI_IP = "192.168.1.100"   # Optional: Pi IP for reference

# GUI Configuration (Windows)
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
VIDEO_DISPLAY_HEIGHT = 500

# Logging Configuration
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# Performance Configuration
FRAME_QUEUE_SIZE = 10  # Number of frames to buffer
STATS_UPDATE_INTERVAL = 500  # milliseconds
VIDEO_UPDATE_INTERVAL = 33  # milliseconds (~30 FPS)

# Advanced: ICE Servers (for NAT traversal)
ICE_SERVERS = [
    # Add STUN/TURN servers if needed
    # {"urls": ["stun:stun.l.google.com:19302"]},
]

# Video File Settings
DEFAULT_VIDEO_PATH = "video.mp4"
VIDEO_LOOP = True  # Restart video when it ends

# Timeout Settings
OFFER_WAIT_TIMEOUT = 60  # seconds
ANSWER_WAIT_TIMEOUT = 60  # seconds
CONNECTION_TIMEOUT = 30  # seconds
