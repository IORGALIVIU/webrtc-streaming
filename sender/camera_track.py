#!/usr/bin/env python3
"""
Video track using Raspberry Pi Camera Module 3 NoIR
Replaces file-based video with live camera feed
"""

import time
import numpy as np
import cv2
from aiortc import VideoStreamTrack
from av import VideoFrame
from picamera2 import Picamera2
from libcamera import controls
import logging

logger = logging.getLogger(__name__)


class PiCameraTrackWithMQTT(VideoStreamTrack):
    """
    Video track that captures from Raspberry Pi Camera Module 3 NoIR
    and integrates MQTT sensor data overlay.
    """
    
    def __init__(self, width: int = 1920, height: int = 1080, fps: int = 30, mqtt_handler=None):
        super().__init__()
        self.width = width
        self.height = height
        self.target_fps = fps
        self.mqtt_handler = mqtt_handler
        self.frame_count = 0
        self.start_time = time.time()
        
        # Initialize Pi Camera
        self.picam2 = Picamera2()
        
        # Configure camera
        config = self.picam2.create_video_configuration(
            main={"size": (width, height), "format": "RGB888"},
            controls={
                "FrameRate": fps,
                "ExposureTime": 33000,  # 33ms exposure (increased from 10ms)
                "AnalogueGain": 4.0,    # ISO 400 equivalent (increased from 1.0)
                "AeEnable": True,       # Enable auto-exposure
                "AwbEnable": True,      # Enable auto white balance
            }
        )
        
        self.picam2.configure(config)
        
        # Set autofocus mode (if supported by Camera Module 3)
        try:
            self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        except:
            logger.warning("Camera autofocus not available")
        
        self.picam2.start()
        logger.info(f"Pi Camera started: {width}x{height} @ {fps} FPS")
        
        # Wait for camera to warm up
        time.sleep(2)
    
    def _get_sensor_data(self):
        """Get sensor data from MQTT commands."""
        if self.mqtt_handler and self.mqtt_handler.connected:
            commands = self.mqtt_handler.received_commands
            unghi = commands.get('unghi_manual', 0)
            viteza = commands.get('viteza_manual', 0)
            mode = commands.get('mod_de_functionare', 0)
            return unghi, viteza, mode
        return 0, 0, 0
    
    async def recv(self):
        """Capture frame from camera with sensor data overlay."""
        pts, time_base = await self.next_timestamp()
        
        # Capture frame from Pi Camera
        frame = self.picam2.capture_array()
        
        # Convert RGB to BGR for OpenCV
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Get current timestamp
        current_time = time.time()
        timestamp_ms = int(current_time * 1000)
        elapsed = current_time - self.start_time
        self.frame_count += 1
        
        # Get sensor data
        unghi, viteza, mode = self._get_sensor_data()
        
        # Publish sensor data to MQTT
        if self.mqtt_handler and self.mqtt_handler.connected:
            self.mqtt_handler.publish_sensor_data(unghi, viteza, timestamp_ms)
        
        # ===== OVERLAY TEXT ON FRAME =====
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Timestamp (top-left, cyan)
        timestamp_text = f"Timestamp: {timestamp_ms}"
        cv2.putText(frame, timestamp_text, (15, 40), font, 1.0, (0, 255, 255), 3)
        
        # Frame info (below timestamp, cyan)
        frame_info = f"Frame: {self.frame_count} | Time: {elapsed:.2f}s"
        cv2.putText(frame, frame_info, (15, 80), font, 0.8, (0, 255, 255), 2)
        
        # Sensor data (below frame info, cyan)
        sensor_text = f"Unghi: {unghi:.2f}deg | Viteza: {viteza:.1f} RPM"
        cv2.putText(frame, sensor_text, (15, 120), font, 0.8, (0, 255, 255), 2)
        
        # Mode and commands (below sensor, magenta)
        mode_text = "AUTO" if mode == 0 else "MANUAL"
        commands_text = f"Mode: {mode_text} | Cmd: {unghi:.0f}deg, {viteza:.0f}RPM"
        cv2.putText(frame, commands_text, (15, 160), font, 0.8, (255, 0, 255), 2)
        
        # MQTT status (bottom-left, yellow)
        mqtt_status = "Connected" if (self.mqtt_handler and self.mqtt_handler.connected) else "Disconnected"
        cv2.putText(frame, f"MQTT: {mqtt_status}", (15, self.height - 20), font, 0.8, (0, 255, 255), 2)
        
        # Create av.VideoFrame
        new_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        new_frame.pts = pts
        new_frame.time_base = time_base
        
        return new_frame
    
    def stop(self):
        """Stop camera."""
        if self.picam2:
            self.picam2.stop()
            logger.info("Pi Camera stopped")


def test_camera():
    """Test Pi Camera capture."""
    print("Testing Pi Camera Module 3...")
    
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (1920, 1080)})
    picam2.configure(config)
    picam2.start()
    
    print("Camera started. Capturing test frame...")
    time.sleep(2)
    
    frame = picam2.capture_array()
    print(f"Captured frame: {frame.shape}")
    
    # Save test image
    cv2.imwrite("/tmp/camera_test.jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    print("Test image saved to /tmp/camera_test.jpg")
    
    picam2.stop()
    print("Camera test complete!")


if __name__ == "__main__":
    test_camera()
