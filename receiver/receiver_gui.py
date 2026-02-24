#!/usr/bin/env python3
"""
Receiver GUI application pentru Windows.
Afișează video stream-ul în aplicație desktop.
"""

import asyncio
import argparse
import logging
import sys
import time
import queue
import threading
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np

from aiortc import RTCPeerConnection, RTCSessionDescription
from av import VideoFrame

# Import signaling
sys.path.insert(0, str(Path(__file__).parent.parent))
from common.signaling import SignalingClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoReceiverGUI:
    """
    Aplicație GUI pentru primirea și afișarea video stream-ului.
    """
    
    def __init__(self, root: tk.Tk, server_url: str):
        self.root = root
        self.server_url = server_url
        self.root.title("WebRTC Video Receiver")
        self.root.geometry("1000x700")
        
        # State
        self.pc: Optional[RTCPeerConnection] = None
        self.is_connected = False
        self.frame_queue = queue.Queue(maxsize=10)
        self.stats = {
            "frames_received": 0,
            "last_timestamp": 0,
            "fps": 0,
            "resolution": "N/A",
            "connection_state": "Disconnected"
        }
        
        # Asyncio loop pentru async operations
        self.loop = None
        self.loop_thread = None
        
        # Setup GUI
        self._setup_ui()
        
        # Start asyncio loop in separate thread
        self._start_async_loop()
        
        # Update GUI
        self._update_video_display()
        self._update_stats_display()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_ui(self):
        """Configurează interfața grafică."""
        
        # Top control panel
        control_frame = ttk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        # Connect button
        self.connect_btn = ttk.Button(
            control_frame,
            text="Connect",
            command=self._on_connect_clicked
        )
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        # Disconnect button
        self.disconnect_btn = ttk.Button(
            control_frame,
            text="Disconnect",
            command=self._on_disconnect_clicked,
            state=tk.DISABLED
        )
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(
            control_frame,
            text="Status: Disconnected",
            foreground="red"
        )
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Main content frame
        content_frame = ttk.Frame(self.root)
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Video display (left side)
        video_frame = ttk.LabelFrame(content_frame, text="Video Stream")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.video_label = ttk.Label(video_frame, text="No video stream")
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Stats panel (right side)
        stats_frame = ttk.LabelFrame(content_frame, text="Statistics", width=250)
        stats_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        stats_frame.pack_propagate(False)
        
        # Stats labels
        self.stats_labels = {}
        stats_items = [
            ("Connection State", "connection_state"),
            ("Frames Received", "frames_received"),
            ("Current FPS", "fps"),
            ("Resolution", "resolution"),
            ("Last Timestamp", "last_timestamp"),
        ]
        
        for i, (label_text, key) in enumerate(stats_items):
            label = ttk.Label(stats_frame, text=f"{label_text}:")
            label.grid(row=i, column=0, sticky=tk.W, padx=10, pady=5)
            
            value_label = ttk.Label(stats_frame, text="N/A", foreground="blue")
            value_label.grid(row=i, column=1, sticky=tk.W, padx=10, pady=5)
            
            self.stats_labels[key] = value_label
        
        # Log text area
        log_frame = ttk.LabelFrame(self.root, text="Logs")
        log_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        self.log_text = tk.Text(log_frame, height=8, state=tk.DISABLED)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
    
    def _log(self, message: str):
        """Adaugă mesaj în log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        logger.info(message)
    
    def _start_async_loop(self):
        """Pornește asyncio loop în thread separat."""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        
        # Așteaptă până când loop-ul este gata
        while self.loop is None:
            time.sleep(0.01)
    
    def _run_async(self, coro):
        """Rulează corutină în loop-ul asyncio."""
        return asyncio.run_coroutine_threadsafe(coro, self.loop)
    
    def _on_connect_clicked(self):
        """Handler pentru butonul Connect."""
        self.connect_btn.config(state=tk.DISABLED)
        self._log("Initiating connection...")
        self._run_async(self._connect())
    
    def _on_disconnect_clicked(self):
        """Handler pentru butonul Disconnect."""
        self._log("Disconnecting...")
        self._run_async(self._disconnect())
    
    async def _connect(self):
        """Conectează la sender prin WebRTC."""
        try:
            self._log(f"Connecting to signaling server: {self.server_url}")
            
            # Creează peer connection
            self.pc = RTCPeerConnection()
            
            # Event handlers
            @self.pc.on("track")
            def on_track(track):
                self._log(f"Track received: {track.kind}")
                
                if track.kind == "video":
                    self._run_async(self._process_video_track(track))
            
            @self.pc.on("connectionstatechange")
            async def on_connectionstatechange():
                state = self.pc.connectionState
                self.stats["connection_state"] = state
                self._log(f"Connection state: {state}")
                
                if state == "connected":
                    self.is_connected = True
                    self.root.after(0, self._update_connection_ui, True)
                elif state in ["failed", "closed"]:
                    self.is_connected = False
                    self.root.after(0, self._update_connection_ui, False)
            
            # Conectare la signaling server
            async with SignalingClient(self.server_url) as signaling:
                # Verifică server
                if not await signaling.check_health():
                    self._log("ERROR: Signaling server is not responding")
                    self.root.after(0, self._update_connection_ui, False)
                    return
                
                self._log("Waiting for offer from sender...")
                
                # Așteaptă offer
                offer_data = await signaling.get_offer(timeout=60)
                
                if not offer_data:
                    self._log("ERROR: Did not receive offer")
                    self.root.after(0, self._update_connection_ui, False)
                    return
                
                self._log("Offer received, creating answer...")
                
                # Setează remote description
                offer = RTCSessionDescription(
                    sdp=offer_data["sdp"],
                    type=offer_data["type"]
                )
                await self.pc.setRemoteDescription(offer)
                
                # Creează answer
                answer = await self.pc.createAnswer()
                await self.pc.setLocalDescription(answer)
                
                # Trimite answer
                self._log("Sending answer to sender...")
                if not await signaling.send_answer(
                    self.pc.localDescription.sdp,
                    self.pc.localDescription.type
                ):
                    self._log("ERROR: Failed to send answer")
                    self.root.after(0, self._update_connection_ui, False)
                    return
                
                self._log("Answer sent successfully!")
                self._log("Waiting for video stream...")
        
        except Exception as e:
            self._log(f"ERROR: {e}")
            logger.exception("Connection error")
            self.root.after(0, self._update_connection_ui, False)
    
    async def _disconnect(self):
        """Deconectează."""
        if self.pc:
            await self.pc.close()
            self.pc = None
        
        self.is_connected = False
        self._log("Disconnected")
        self.root.after(0, self._update_connection_ui, False)
    
    async def _process_video_track(self, track):
        """Procesează video track-ul primit."""
        self._log("Video track processing started")
        frame_times = []
        
        try:
            while True:
                frame = await track.recv()
                
                # Convert to numpy array
                img = frame.to_ndarray(format="bgr24")
                
                # Update stats
                self.stats["frames_received"] += 1
                self.stats["resolution"] = f"{img.shape[1]}x{img.shape[0]}"
                
                # Calculate FPS
                current_time = time.time()
                frame_times.append(current_time)
                frame_times = [t for t in frame_times if current_time - t < 1.0]
                self.stats["fps"] = len(frame_times)
                
                # Put frame in queue (non-blocking)
                try:
                    self.frame_queue.put_nowait(img)
                except queue.Full:
                    # Remove oldest frame if queue is full
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(img)
                    except:
                        pass
        
        except Exception as e:
            self._log(f"ERROR in video processing: {e}")
            logger.exception("Video processing error")
    
    def _update_video_display(self):
        """Actualizează afișajul video."""
        try:
            # Get frame from queue
            frame = self.frame_queue.get_nowait()
            
            # Resize for display (maintain aspect ratio)
            display_height = 500
            aspect_ratio = frame.shape[1] / frame.shape[0]
            display_width = int(display_height * aspect_ratio)
            
            frame_resized = cv2.resize(frame, (display_width, display_height))
            
            # Convert to PIL Image
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(image=img_pil)
            
            # Update label
            self.video_label.config(image=img_tk)
            self.video_label.image = img_tk  # Keep reference
        
        except queue.Empty:
            pass
        except Exception as e:
            logger.error(f"Error updating video: {e}")
        
        # Schedule next update
        self.root.after(33, self._update_video_display)  # ~30 FPS
    
    def _update_stats_display(self):
        """Actualizează afișajul statisticilor."""
        for key, label in self.stats_labels.items():
            value = self.stats.get(key, "N/A")
            label.config(text=str(value))
        
        # Schedule next update
        self.root.after(500, self._update_stats_display)  # Every 0.5s
    
    def _update_connection_ui(self, connected: bool):
        """Actualizează UI-ul în funcție de starea conexiunii."""
        if connected:
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.status_label.config(
                text="Status: Connected",
                foreground="green"
            )
        else:
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.status_label.config(
                text="Status: Disconnected",
                foreground="red"
            )
    
    def _on_closing(self):
        """Handler pentru închiderea ferestrei."""
        if self.is_connected:
            if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
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
        description="WebRTC Video Receiver GUI (Windows)"
    )
    parser.add_argument(
        "--server-ip",
        required=True,
        help="Signaling server IP (Raspberry Pi IP)"
    )
    parser.add_argument(
        "--server-port",
        type=int,
        default=8080,
        help="Signaling server port"
    )
    
    args = parser.parse_args()
    server_url = f"http://{args.server_ip}:{args.server_port}"
    
    # Create GUI
    root = tk.Tk()
    app = VideoReceiverGUI(root, server_url)
    
    # Run
    try:
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")


if __name__ == "__main__":
    main()
