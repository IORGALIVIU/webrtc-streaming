#!/usr/bin/env python3
"""
Integrated Receiver GUI cu MQTT pentru Windows.
- Primește video WebRTC cu timestamp
- Primește date senzori prin MQTT sincronizate cu frame-urile
- Trimite comenzi prin MQTT (mod, unghi, viteza)
- Rulează MQTT broker local
"""

import asyncio
import argparse
import logging
import sys
import time
import queue
import threading
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
import cv2
import numpy as np

from aiortc import RTCPeerConnection, RTCSessionDescription
from av import VideoFrame
import paho.mqtt.client as mqtt

# Import signaling
sys.path.insert(0, str(Path(__file__).parent.parent))
from common.signaling import SignalingClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# MQTT Handler for Receiver
# ============================================================================

class MQTTReceiverHandler:
    """Handles MQTT for receiving sensor data and sending commands."""
    
    def __init__(self, broker_address: str = "localhost", broker_port: int = 1883):
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.client_id = "windows_receiver_gui"
        
        # Topics
        self.topic_subscribe_senzori = "robot/senzori"
        self.topic_publish_mod = "robot/control/mod"
        self.topic_publish_unghi = "robot/control/unghi_manual"
        self.topic_publish_viteza = "robot/control/viteza_manual"
        
        # Data storage with timestamp synchronization
        self.sensor_data_buffer = {}  # {timestamp: {unghi, viteza}}
        self.latest_sensor_data = {
            "unghi": 0.0,
            "viteza": 0.0,
            "timestamp": 0
        }
        
        self.client = None
        self.connected = False
        self.message_callback = None
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"MQTT: Connected to broker {self.broker_address}")
            self.connected = True
            client.subscribe(self.topic_subscribe_senzori)
            logger.info("MQTT: Subscribed to sensor topics")
        else:
            logger.error(f"MQTT: Connection failed, code: {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Called when MQTT disconnects."""
        self.connected = False
        if rc != 0:
            logger.warning(f"MQTT: Unexpected disconnect! Code: {rc}")
        else:
            logger.info("MQTT: Disconnected")
    
    def on_message(self, client, userdata, message):
        topic = message.topic
        payload = message.payload.decode()
        
        try:
            if topic == self.topic_subscribe_senzori:
                data = json.loads(payload)
                timestamp = data.get("timestamp", 0)
                
                self.latest_sensor_data = {
                    "unghi": data.get("unghi", 0.0),
                    "viteza": data.get("viteza", 0.0),
                    "timestamp": timestamp
                }
                
                # Store in buffer for synchronization
                self.sensor_data_buffer[timestamp] = self.latest_sensor_data.copy()
                
                # Keep buffer size manageable
                if len(self.sensor_data_buffer) > 100:
                    oldest = min(self.sensor_data_buffer.keys())
                    del self.sensor_data_buffer[oldest]
                
                # Debug log - IMPORTANT!
                print(f"[MQTT DEBUG] Received: unghi={self.latest_sensor_data['unghi']}, viteza={self.latest_sensor_data['viteza']}, ts={timestamp}")
                
                # Callback to GUI
                if self.message_callback:
                    self.message_callback(self.latest_sensor_data)
                    
        except json.JSONDecodeError:
            logger.error(f"MQTT: JSON decode error: {payload}")
        except Exception as e:
            logger.error(f"MQTT: Error processing message: {e}")
    
    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client = mqtt.Client(
                client_id=self.client_id,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1
            )
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            
            logger.info(f"MQTT: Connecting to {self.broker_address}:{self.broker_port}")
            self.client.connect(self.broker_address, self.broker_port, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            for _ in range(timeout * 2):
                if self.connected:
                    return True
                time.sleep(0.5)
            
            logger.warning("MQTT: Connection timeout")
            return False
            
        except Exception as e:
            logger.error(f"MQTT: Connection error: {e}")
            return False
    
    def get_sensor_data_at_timestamp(self, timestamp: int, tolerance_ms: int = 100):
        """Get sensor data closest to given timestamp."""
        if not self.sensor_data_buffer:
            return self.latest_sensor_data
        
        # Find closest timestamp
        closest_ts = min(self.sensor_data_buffer.keys(), 
                        key=lambda x: abs(x - timestamp))
        
        if abs(closest_ts - timestamp) <= tolerance_ms:
            return self.sensor_data_buffer[closest_ts]
        
        return self.latest_sensor_data
    
    def send_command_mode(self, mode: int):
        """Send mode command (0=auto, 1=manual)."""
        if not self.connected:
            return False
        
        message = {"mod_de_functionare": mode}
        try:
            result = self.client.publish(self.topic_publish_mod, json.dumps(message))
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"MQTT: Send mode error: {e}")
            return False
    
    def send_command_angle(self, angle: float):
        """Send manual angle command."""
        if not self.connected:
            return False
        
        message = {"unghi_manual": angle}
        try:
            result = self.client.publish(self.topic_publish_unghi, json.dumps(message))
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"MQTT: Send angle error: {e}")
            return False
    
    def send_command_speed(self, speed: float):
        """Send manual speed command."""
        if not self.connected:
            return False
        
        message = {"viteza_manual": speed}
        try:
            result = self.client.publish(self.topic_publish_viteza, json.dumps(message))
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"MQTT: Send speed error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT: Disconnected")


# ============================================================================
# Integrated Video Receiver GUI with MQTT
# ============================================================================

class VideoReceiverGUI_MQTT:
    """
    GUI application for receiving video and synchronized MQTT sensor data.
    Also sends commands to Raspberry Pi.
    """
    
    def __init__(self, root: tk.Tk, server_url: str, mqtt_broker: str):
        self.root = root
        self.server_url = server_url
        self.mqtt_broker = mqtt_broker
        self.root.title("WebRTC + MQTT Receiver")
        self.root.geometry("1200x800")
        
        # State
        self.pc: Optional[RTCPeerConnection] = None
        self.is_connected = False
        self.frame_queue = queue.Queue(maxsize=10)
        self.current_frame_timestamp = 0
        
        # Stats
        self.stats = {
            "frames_received": 0,
            "last_timestamp": 0,
            "fps": 0,
            "resolution": "N/A",
            "connection_state": "Disconnected",
            "mqtt_state": "Disconnected"
        }
        
        # MQTT Handler
        self.mqtt_handler = MQTTReceiverHandler(mqtt_broker)
        self.mqtt_handler.message_callback = self._on_mqtt_message
        
        # Gamepad Controller for keyboard input
        from gamepad_controller import GamepadController
        self.gamepad = GamepadController(
            angle_max=60, angle_min=-60,
            speed_max=100, speed_min=-100,  # Allow reverse!
            accel_rate=50.0,      # 50 units/second
            decel_rate=80.0,      # 80 units/second (faster return)
            quick_tap_boost=10.0  # +10 for quick taps
        )
        
        # Control values
        self.control_mode = tk.IntVar(value=0)  # 0=auto, 1=manual
        self.control_angle = tk.DoubleVar(value=0.0)
        self.control_speed = tk.DoubleVar(value=0.0)
        
        # Sensor display values
        self.sensor_angle = tk.StringVar(value="0.0")
        self.sensor_speed = tk.StringVar(value="0.0")
        self.sensor_timestamp = tk.StringVar(value="N/A")
        
        # Asyncio loop pentru async operations
        self.loop = None
        self.loop_thread = None
        
        # Setup GUI
        self._setup_ui()
        
        # Start asyncio loop
        self._start_async_loop()
        
        # Update loops
        self._update_video_display()
        self._update_stats_display()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_ui(self):
        """Setup GUI layout."""
        
        # ===== Top Control Panel =====
        control_frame = ttk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        # Connection buttons
        self.connect_btn = ttk.Button(
            control_frame,
            text="Connect WebRTC",
            command=self._on_connect_webrtc_clicked
        )
        self.connect_btn.grid(row=0, column=0, padx=5)
        
        self.disconnect_btn = ttk.Button(
            control_frame,
            text="Disconnect",
            command=self._on_disconnect_clicked,
            state=tk.DISABLED
        )
        self.disconnect_btn.grid(row=0, column=1, padx=5)
        
        # MQTT connect
        self.mqtt_connect_btn = ttk.Button(
            control_frame,
            text="Connect MQTT",
            command=self._on_connect_mqtt_clicked
        )
        self.mqtt_connect_btn.grid(row=0, column=2, padx=5)
        
        # Status labels
        self.webrtc_status = ttk.Label(
            control_frame,
            text="WebRTC: Disconnected",
            foreground="red"
        )
        self.webrtc_status.grid(row=0, column=3, padx=20)
        
        self.mqtt_status = ttk.Label(
            control_frame,
            text="MQTT: Disconnected",
            foreground="red"
        )
        self.mqtt_status.grid(row=0, column=4, padx=20)
        
        # ===== Main Content =====
        content_frame = ttk.Frame(self.root)
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left: Video
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Video display
        video_frame = ttk.LabelFrame(left_frame, text="Video Stream")
        video_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        
        self.video_label = ttk.Label(video_frame, text="No video stream")
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Right: Control Panel + Stats + Sensor Data
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        
        # Control panel
        control_panel = ttk.LabelFrame(right_frame, text="Control Commands")
        control_panel.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        # Mode control
        ttk.Label(control_panel, text="Mode:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Radiobutton(control_panel, text="Auto", variable=self.control_mode, value=0, 
                       command=self._on_mode_changed).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(control_panel, text="Manual", variable=self.control_mode, value=1,
                       command=self._on_mode_changed).grid(row=0, column=2, sticky=tk.W, padx=5)
        
        # Keyboard control instructions (Manual mode only)
        self.keyboard_label = ttk.Label(control_panel, text="Use Arrow Keys to Control", 
                                       foreground="blue", font=("Arial", 9, "bold"))
        self.keyboard_label.grid(row=1, column=0, columnspan=3, pady=(10,5))
        self.keyboard_label.grid_remove()  # Hidden by default
        
        # Arrow keys help
        self.arrows_help = ttk.Label(control_panel, 
                                     text="↑↓ Speed  |  ←→ Angle", 
                                     foreground="gray", font=("Arial", 8))
        self.arrows_help.grid(row=2, column=0, columnspan=3, pady=(0,10))
        self.arrows_help.grid_remove()  # Hidden by default
        
        # Angle display (read-only, no slider)
        ttk.Label(control_panel, text="Manual Angle:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        self.angle_value_label = ttk.Label(control_panel, textvariable=self.control_angle, 
                                          font=("Arial", 14, "bold"), foreground="blue")
        self.angle_value_label.grid(row=3, column=1, sticky=tk.W, padx=5)
        ttk.Label(control_panel, text="°").grid(row=3, column=2, sticky=tk.W)
        
        # Speed display (read-only, no slider)
        ttk.Label(control_panel, text="Manual Speed:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        self.speed_value_label = ttk.Label(control_panel, textvariable=self.control_speed,
                                          font=("Arial", 14, "bold"), foreground="blue")
        self.speed_value_label.grid(row=4, column=1, sticky=tk.W, padx=5)
        ttk.Label(control_panel, text="RPM").grid(row=4, column=2, sticky=tk.W)
        
        # Send button (removed - auto-send with keyboard)
        # Last command sent display
        ttk.Label(control_panel, text="Last Sent:").grid(row=5, column=0, sticky=tk.W, padx=10, pady=5)
        self.last_command_label = ttk.Label(control_panel, text="None", foreground="green", wraplength=200)
        self.last_command_label.grid(row=5, column=1, columnspan=2, sticky=tk.W, padx=5)
        
        # Stats panel
        stats_frame = ttk.LabelFrame(right_frame, text="Statistics")
        stats_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        self.stats_labels = {}
        stats_items = [
            ("WebRTC State", "connection_state"),
            ("MQTT State", "mqtt_state"),
            ("Frames Received", "frames_received"),
            ("Current FPS", "fps"),
            ("Resolution", "resolution"),
        ]
        
        for i, (label_text, key) in enumerate(stats_items):
            label = ttk.Label(stats_frame, text=f"{label_text}:")
            label.grid(row=i, column=0, sticky=tk.W, padx=10, pady=5)
            
            value_label = ttk.Label(stats_frame, text="N/A", foreground="blue")
            value_label.grid(row=i, column=1, sticky=tk.W, padx=10, pady=5)
            
            self.stats_labels[key] = value_label
        
        # Sensor data display - MOVED HERE under statistics
        sensor_frame = ttk.LabelFrame(right_frame, text="Sensor Data (Synced)")
        sensor_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        sensor_grid = ttk.Frame(sensor_frame)
        sensor_grid.pack(padx=10, pady=10)
        
        ttk.Label(sensor_grid, text="Unghi:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Label(sensor_grid, textvariable=self.sensor_angle, foreground="blue", font=("Arial", 11, "bold")).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Label(sensor_grid, text="°").grid(row=0, column=2, sticky=tk.W)
        
        ttk.Label(sensor_grid, text="Viteza:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Label(sensor_grid, textvariable=self.sensor_speed, foreground="blue", font=("Arial", 11, "bold")).grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Label(sensor_grid, text="RPM").grid(row=1, column=2, sticky=tk.W)
        
        ttk.Label(sensor_grid, text="Timestamp:").grid(row=2, column=0, sticky=tk.W, padx=5)
        ttk.Label(sensor_grid, textvariable=self.sensor_timestamp, foreground="gray", font=("Arial", 8)).grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=5)
        
        # Log area - bigger now with more space available
        log_frame = ttk.LabelFrame(self.root, text="Logs")
        log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Setup keyboard bindings
        self._setup_keyboard()
        
        # Start gamepad update loop
        self._start_gamepad_update()
    
    def _setup_keyboard(self):
        """Setup keyboard event handlers."""
        # Bind arrow keys
        self.root.bind('<KeyPress-Left>', lambda e: self._on_key_press('left'))
        self.root.bind('<KeyPress-Right>', lambda e: self._on_key_press('right'))
        self.root.bind('<KeyPress-Up>', lambda e: self._on_key_press('up'))
        self.root.bind('<KeyPress-Down>', lambda e: self._on_key_press('down'))
        
        self.root.bind('<KeyRelease-Left>', lambda e: self._on_key_release('left'))
        self.root.bind('<KeyRelease-Right>', lambda e: self._on_key_release('right'))
        self.root.bind('<KeyRelease-Up>', lambda e: self._on_key_release('up'))
        self.root.bind('<KeyRelease-Down>', lambda e: self._on_key_release('down'))
    
    def _on_key_press(self, key):
        """Handle key press - only in manual mode."""
        if self.control_mode.get() == 1:  # Manual mode
            self.gamepad.key_press(key)
    
    def _on_key_release(self, key):
        """Handle key release."""
        if self.control_mode.get() == 1:  # Manual mode
            self.gamepad.key_release(key)
    
    def _start_gamepad_update(self):
        """Start gamepad controller and update loop."""
        self.gamepad.start()
        self._update_from_gamepad()
    
    def _update_from_gamepad(self):
        """Update control values from gamepad at 60 FPS."""
        if self.control_mode.get() == 1:  # Manual mode
            # Get current values from gamepad
            angle, speed = self.gamepad.get_values()
            
            # Update GUI
            self.control_angle.set(round(angle, 1))
            self.control_speed.set(round(speed, 1))
            
            # Auto-send to MQTT (smooth updates)
            self._send_all_commands()
        
        # Schedule next update (~60 FPS)
        self.root.after(16, self._update_from_gamepad)
    
    def _log(self, message: str):
        """Add message to log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        # Only auto-scroll if user is at the bottom
        if self.log_text.yview()[1] >= 0.95:
            self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        logger.info(message)
    
    def _on_mqtt_message(self, sensor_data):
        """Callback when MQTT message received - update display immediately."""
        # Debug log
        print(f"DEBUG: MQTT message received: {sensor_data}")
        
        # Check data freshness (detect delay)
        current_time_ms = int(time.time() * 1000)
        data_timestamp = sensor_data.get('timestamp', current_time_ms)
        data_age_ms = current_time_ms - data_timestamp
        
        # Log warning if data is stale
        if data_age_ms > 500:
            self._log(f"⚠️  WARNING: MQTT data is {data_age_ms}ms old (delay detected!)")
        elif data_age_ms > 200:
            self._log(f"⚠️  MQTT data age: {data_age_ms}ms (slight delay)")
        else:
            self._log(f"MQTT data: unghi={sensor_data.get('unghi', 'N/A')}, viteza={sensor_data.get('viteza', 'N/A')}")
        
        # Update sensor display in GUI thread
        def update_gui():
            self.sensor_angle.set(f"{sensor_data['unghi']:.1f}")
            self.sensor_speed.set(f"{sensor_data['viteza']:.1f}")
            
            # Show timestamp with age indicator
            age_indicator = ""
            if data_age_ms > 500:
                age_indicator = " ⚠️"  # Stale data
            elif data_age_ms > 200:
                age_indicator = " ⏱"   # Slight delay
            
            self.sensor_timestamp.set(f"{data_timestamp}{age_indicator}")
        
        # Schedule GUI update in main thread
        self.root.after(0, update_gui)
    
    def _on_mode_changed(self):
        """Mode radio button changed."""
        mode = self.control_mode.get()
        
        if mode == 1:  # Manual mode
            # Show keyboard instructions
            self.keyboard_label.grid()
            self.arrows_help.grid()
            self._log("Manual mode - Use arrow keys to control")
        else:  # Auto mode
            # Hide keyboard instructions
            self.keyboard_label.grid_remove()
            self.arrows_help.grid_remove()
            # Reset gamepad to zero
            self.gamepad.reset()
            self.control_angle.set(0.0)
            self.control_speed.set(0.0)
            self._log("Auto mode activated")
        
        # Send mode change
        self._send_all_commands()
    
    # Removed _on_angle_changed and _on_speed_changed (no more sliders!)
    
    def _send_all_commands(self):
        """Send all control commands."""
        if not self.mqtt_handler.connected:
            self._log("MQTT not connected!")
            self.last_command_label.config(text="ERROR: MQTT not connected", foreground="red")
            return
        
        mode = self.control_mode.get()
        angle = self.control_angle.get()
        speed = self.control_speed.get()
        
        self.mqtt_handler.send_command_mode(mode)
        self.mqtt_handler.send_command_angle(angle)
        self.mqtt_handler.send_command_speed(speed)
        
        mode_text = "Manual" if mode == 1 else "Auto"
        command_str = f"{mode_text}, {angle:.0f}°, {speed:.0f} RPM"
        self._log(f"Commands sent: {command_str}")
        self.last_command_label.config(text=command_str, foreground="green")
    
    def _start_async_loop(self):
        """Start asyncio loop in separate thread."""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        
        while self.loop is None:
            time.sleep(0.01)
    
    def _run_async(self, coro):
        """Run coroutine in asyncio loop."""
        return asyncio.run_coroutine_threadsafe(coro, self.loop)
    
    def _on_connect_mqtt_clicked(self):
        """Connect to MQTT broker."""
        self.mqtt_connect_btn.config(state=tk.DISABLED)
        self._log("Connecting to MQTT broker...")
        
        def connect_thread():
            if self.mqtt_handler.connect():
                self.stats["mqtt_state"] = "Connected"
                self._log("MQTT connected successfully")
                self.root.after(0, lambda: self.mqtt_status.config(
                    text="MQTT: Connected", foreground="green"))
            else:
                self._log("MQTT connection failed")
                self.root.after(0, lambda: self.mqtt_connect_btn.config(state=tk.NORMAL))
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def _on_connect_webrtc_clicked(self):
        """Connect to WebRTC."""
        self.connect_btn.config(state=tk.DISABLED)
        self._log("Initiating WebRTC connection...")
        self._run_async(self._connect())
    
    def _on_disconnect_clicked(self):
        """Disconnect both WebRTC and MQTT."""
        self._log("Disconnecting...")
        self._run_async(self._disconnect())
    
    async def _connect(self):
        """Connect to sender via WebRTC."""
        try:
            self._log(f"Connecting to signaling server: {self.server_url}")
            
            self.pc = RTCPeerConnection()
            
            @self.pc.on("track")
            def on_track(track):
                self._log(f"Track received: {track.kind}")
                
                if track.kind == "video":
                    self._run_async(self._process_video_track(track))
            
            @self.pc.on("connectionstatechange")
            async def on_connectionstatechange():
                state = self.pc.connectionState
                self.stats["connection_state"] = state
                self._log(f"WebRTC state: {state}")
                
                if state == "connected":
                    self.is_connected = True
                    self.root.after(0, self._update_connection_ui, True)
                elif state in ["failed", "closed"]:
                    self.is_connected = False
                    self.root.after(0, self._update_connection_ui, False)
            
            async with SignalingClient(self.server_url) as signaling:
                if not await signaling.check_health():
                    self._log("ERROR: Signaling server not responding")
                    self.root.after(0, self._update_connection_ui, False)
                    return
                
                self._log("Waiting for offer...")
                offer_data = await signaling.get_offer(timeout=60)
                
                if not offer_data:
                    self._log("ERROR: Did not receive offer")
                    self.root.after(0, self._update_connection_ui, False)
                    return
                
                self._log("Creating answer...")
                offer = RTCSessionDescription(
                    sdp=offer_data["sdp"],
                    type=offer_data["type"]
                )
                await self.pc.setRemoteDescription(offer)
                
                answer = await self.pc.createAnswer()
                await self.pc.setLocalDescription(answer)
                
                self._log("Sending answer...")
                if not await signaling.send_answer(
                    self.pc.localDescription.sdp,
                    self.pc.localDescription.type
                ):
                    self._log("ERROR: Failed to send answer")
                    self.root.after(0, self._update_connection_ui, False)
                    return
                
                self._log("WebRTC connected successfully!")
        
        except Exception as e:
            self._log(f"ERROR: {e}")
            logger.exception("Connection error")
            self.root.after(0, self._update_connection_ui, False)
    
    async def _disconnect(self):
        """Disconnect all."""
        if self.pc:
            await self.pc.close()
            self.pc = None
        
        if self.mqtt_handler:
            self.mqtt_handler.disconnect()
        
        self.is_connected = False
        self._log("Disconnected")
        self.root.after(0, self._update_connection_ui, False)
        self.root.after(0, lambda: self.mqtt_status.config(
            text="MQTT: Disconnected", foreground="red"))
    
    async def _process_video_track(self, track):
        """Process video track."""
        self._log("Video track processing started")
        frame_times = []
        
        try:
            while True:
                frame = await track.recv()
                
                img = frame.to_ndarray(format="bgr24")
                
                # Update stats
                self.stats["frames_received"] += 1
                self.stats["resolution"] = f"{img.shape[1]}x{img.shape[0]}"
                
                # Calculate FPS
                current_time = time.time()
                frame_times.append(current_time)
                frame_times = [t for t in frame_times if current_time - t < 1.0]
                self.stats["fps"] = len(frame_times)
                
                # Store with timestamp (try to extract from frame or use current)
                self.current_frame_timestamp = int(current_time * 1000)
                
                # Put frame in queue
                try:
                    self.frame_queue.put_nowait(img)
                except queue.Full:
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(img)
                    except:
                        pass
        
        except Exception as e:
            self._log(f"ERROR in video processing: {e}")
            logger.exception("Video processing error")
    
    def _update_video_display(self):
        """Update video display with latest sensor data."""
        try:
            frame = self.frame_queue.get_nowait()
            
            # Use latest sensor data from MQTT (already updated by callback)
            # No need for complex timestamp synchronization - MQTT callback 
            # updates sensor_angle/speed/timestamp in real-time
            
            # Resize and display
            display_height = 500
            aspect_ratio = frame.shape[1] / frame.shape[0]
            display_width = int(display_height * aspect_ratio)
            
            frame_resized = cv2.resize(frame, (display_width, display_height))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(image=img_pil)
            
            self.video_label.config(image=img_tk)
            self.video_label.image = img_tk
        
        except queue.Empty:
            pass
        except Exception as e:
            logger.error(f"Error updating video: {e}")
        
        self.root.after(33, self._update_video_display)
    
    def _update_stats_display(self):
        """Update statistics display."""
        for key, label in self.stats_labels.items():
            value = self.stats.get(key, "N/A")
            label.config(text=str(value))
        
        self.root.after(500, self._update_stats_display)
    
    def _update_connection_ui(self, connected: bool):
        """Update UI based on connection state."""
        if connected:
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.webrtc_status.config(
                text="WebRTC: Connected",
                foreground="green"
            )
        else:
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.webrtc_status.config(
                text="WebRTC: Disconnected",
                foreground="red"
            )
    
    def _on_closing(self):
        """Handle window close."""
        if self.is_connected or self.mqtt_handler.connected:
            if messagebox.askokcancel("Quit", "Close connections and quit?"):
                self._run_async(self._disconnect())
                if self.loop:
                    self.loop.call_soon_threadsafe(self.loop.stop)
                self.root.destroy()
        else:
            if self.loop:
                self.loop.call_soon_threadsafe(self.loop.stop)
            self.root.destroy()


def main():
    parser = argparse.ArgumentParser(
        description="WebRTC + MQTT Receiver GUI (Windows)"
    )
    parser.add_argument(
        "--server-ip",
        default="192.168.0.199",
        help="Signaling server IP"
    )
    parser.add_argument(
        "--server-port",
        type=int,
        default=8080,
        help="Signaling server port"
    )
    parser.add_argument(
        "--mqtt-broker",
        default="localhost",
        help="MQTT broker address"
    )
    
    args = parser.parse_args()
    server_url = f"http://{args.server_ip}:{args.server_port}"
    
    root = tk.Tk()
    app = VideoReceiverGUI_MQTT(root, server_url, args.mqtt_broker)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")


if __name__ == "__main__":
    main()
