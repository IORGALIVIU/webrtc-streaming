#!/usr/bin/env python3
"""
Integrated WebRTC Sender + MQTT Client pentru Raspberry Pi.
- Trimite video prin WebRTC cu timestamp
- Publică date senzori prin MQTT (unghi, viteza)
- Primește comenzi prin MQTT (mod, unghi_manual, viteza_manual)
"""

import asyncio
import argparse
import logging
import sys
import time
import cv2
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame
import paho.mqtt.client as mqtt
import threading

# Import signaling
sys.path.insert(0, str(Path(__file__).parent.parent))
from common.signaling import SignalingClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# MQTT Configuration and Handlers
# ============================================================================

class MQTTHandler:
    """Handles MQTT communication for sensor data and commands."""
    
    def __init__(self, broker_address: str, broker_port: int = 1883, robot_controller=None):
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.client_id = "raspberry_pi_webrtc"
        
        # Robot hardware controller (optional)
        self.robot_controller = robot_controller
        
        # Topics
        self.topic_publish = "robot/senzori"
        self.topic_subscribe_mod = "robot/control/mod"
        self.topic_subscribe_unghi = "robot/control/unghi_manual"
        self.topic_subscribe_viteza = "robot/control/viteza_manual"
        
        # Data storage
        self.sensor_data = {
            "unghi": 0.0,
            "viteza": 0.0,
            "timestamp": None
        }
        
        self.received_commands = {
            "mod_de_functionare": 0,  # 0 = automat, 1 = manual
            "unghi_manual": 0,
            "viteza_manual": 0
        }
        
        self.client = None
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"MQTT: Connected to broker {self.broker_address}")
            self.connected = True
            # Subscribe to command topics
            client.subscribe(self.topic_subscribe_mod)
            client.subscribe(self.topic_subscribe_unghi)
            client.subscribe(self.topic_subscribe_viteza)
            logger.info("MQTT: Subscribed to command topics")
        else:
            logger.error(f"MQTT: Connection failed, code: {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Called when MQTT disconnects."""
        self.connected = False
        if rc != 0:
            logger.warning(f"MQTT: Unexpected disconnect! Code: {rc}")
            print(f"[MQTT DEBUG] Connection lost! Trying to reconnect...")
        else:
            logger.info("MQTT: Disconnected")
    
    def on_message(self, client, userdata, message):
        topic = message.topic
        payload = message.payload.decode()
        
        try:
            data = json.loads(payload)
            
            if topic == self.topic_subscribe_mod:
                self.received_commands["mod_de_functionare"] = data.get("mod_de_functionare", 0)
                mode = "MANUAL" if self.received_commands["mod_de_functionare"] == 1 else "AUTOMAT"
                logger.info(f"[MQTT] Mode received: {mode}")
                print(f"[MQTT DEBUG] Mode changed to: {mode}")
                
                # If switching to AUTO mode, stop robot
                if self.robot_controller and self.received_commands["mod_de_functionare"] == 0:
                    self.robot_controller.update(angle=0, speed=0)
                    logger.info("[ROBOT] Switched to AUTO - motors stopped")
            
            elif topic == self.topic_subscribe_unghi:
                self.received_commands["unghi_manual"] = data.get("unghi_manual", 0)
                logger.info(f"[MQTT] Manual angle: {self.received_commands['unghi_manual']}°")
                print(f"[MQTT DEBUG] Angle command: {self.received_commands['unghi_manual']}°")
                
                # Apply angle to robot if in MANUAL mode
                if self.robot_controller and self.received_commands["mod_de_functionare"] == 1:
                    angle = self.received_commands["unghi_manual"]
                    speed = self.received_commands["viteza_manual"]
                    print("MQTT MESSAGE RECEIVED:", message.topic, message.payload)
                    self.robot_controller.update(angle=angle, speed=speed)
                    logger.debug(f"[ROBOT] Updated: angle={angle}°, speed={speed}")
            
            elif topic == self.topic_subscribe_viteza:
                self.received_commands["viteza_manual"] = data.get("viteza_manual", 0)
                logger.info(f"[MQTT] Manual speed: {self.received_commands['viteza_manual']} RPM")
                print(f"[MQTT DEBUG] Speed command: {self.received_commands['viteza_manual']} RPM")
                
                # Apply speed to robot if in MANUAL mode
                if self.robot_controller and self.received_commands["mod_de_functionare"] == 1:
                    angle = self.received_commands["unghi_manual"]
                    speed = self.received_commands["viteza_manual"]
                    print("MQTT MESSAGE RECEIVED:", message.topic, message.payload)
                    self.robot_controller.update(angle=angle, speed=speed)
                    logger.debug(f"[ROBOT] Updated: angle={angle}°, speed={speed}")
                
        except json.JSONDecodeError:
            logger.error(f"[MQTT] JSON decode error: {payload}")
        except Exception as e:
            logger.error(f"[MQTT] Error processing command: {e}")
    
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
    
    def publish_sensor_data(self, unghi: float, viteza: float, timestamp_ms: int):
        """Publish sensor data with timestamp."""
        if not self.connected:
            return False
        
        self.sensor_data = {
            "unghi": round(unghi, 2),
            "viteza": round(viteza, 2),
            "timestamp": timestamp_ms,
            "timestamp_iso": datetime.fromtimestamp(timestamp_ms / 1000).isoformat()
        }
        
        try:
            result = self.client.publish(self.topic_publish, json.dumps(self.sensor_data))
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"MQTT: Publish error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT: Disconnected")


# ============================================================================
# WebRTC Video Track with MQTT Integration
# ============================================================================

class VideoFileTrackWithMQTT(VideoStreamTrack):
    """
    Video track that reads from file and integrates MQTT sensor data.
    Displays timestamp and sensor data on each frame.
    """
    
    def __init__(self, video_path: str, fps: int = 30, mqtt_handler: MQTTHandler = None):
        super().__init__()
        self.video_path = video_path
        self.target_fps = fps
        self.mqtt_handler = mqtt_handler
        self.cap = None
        self.frame_count = 0
        self.start_time = time.time()
        
        # Simulated sensor data (if no real sensors)
        self.simulated_angle = 0.0
        self.simulated_speed = 50.0
        
        self._open_video()
        
    def _open_video(self):
        """Open video file."""
        self.cap = cv2.VideoCapture(self.video_path)
        
        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video: {self.video_path}")
        
        self.original_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        logger.info(f"Video loaded: {self.width}x{self.height}, "
                   f"{self.original_fps:.2f} FPS, {self.total_frames} frames")
    
    def _simulate_sensor_data(self):
        """Simulate sensor data for testing."""
        # Simulate angle oscillation
        self.simulated_angle = 45 * np.sin(time.time() * 0.5)
        # Simulate speed variation
        self.simulated_speed = 50 + 30 * np.sin(time.time() * 0.3)
        return self.simulated_angle, self.simulated_speed
    
    async def recv(self):
        """Receive next frame with sensor data overlay."""
        pts, time_base = await self.next_timestamp()
        
        # Read frame
        ret, frame = self.cap.read()
        
        if not ret:
            logger.info("Video ended, restarting...")
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            
            if not ret:
                logger.error("Cannot read frame")
                frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Get current timestamp
        current_time = time.time()
        timestamp_ms = int(current_time * 1000)
        elapsed = current_time - self.start_time
        
        # Get sensor data (simulated or real)
        if self.mqtt_handler and self.mqtt_handler.connected:
            # Use received commands or simulate
            unghi, viteza = self._simulate_sensor_data()
            
            # Publish to MQTT
            self.mqtt_handler.publish_sensor_data(unghi, viteza, timestamp_ms)
            
            # Get commands
            commands = self.mqtt_handler.received_commands
        else:
            unghi, viteza = self._simulate_sensor_data()
            commands = {"mod_de_functionare": 0, "unghi_manual": 0, "viteza_manual": 0}
        
        # Add overlays to frame with larger, more readable text
        # Timestamp
        cv2.putText(
            frame, 
            f"Timestamp: {timestamp_ms}", 
            (15, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 
            1.0, 
            (0, 255, 0), 
            3
        )
        
        # Frame info
        cv2.putText(
            frame, 
            f"Frame: {self.frame_count} | Time: {elapsed:.2f}s", 
            (15, 80),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.8, 
            (0, 255, 0), 
            2
        )
        
        # Sensor data
        cv2.putText(
            frame, 
            f"Unghi: {unghi:.1f}deg | Viteza: {viteza:.1f} RPM", 
            (15, 120),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.9, 
            (255, 255, 0), 
            3
        )
        
        # Commands received
        mode_text = "MANUAL" if commands["mod_de_functionare"] == 1 else "AUTO"
        cv2.putText(
            frame, 
            f"Mode: {mode_text} | Cmd: {commands['unghi_manual']:.0f}deg, {commands['viteza_manual']:.0f}RPM", 
            (15, 160),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.8, 
            (255, 0, 255), 
            2
        )
        
        # MQTT status
        mqtt_status = "MQTT: Connected" if (self.mqtt_handler and self.mqtt_handler.connected) else "MQTT: Disconnected"
        cv2.putText(
            frame, 
            mqtt_status, 
            (15, self.height - 25),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.8, 
            (0, 255, 255), 
            2
        )
        
        self.frame_count += 1
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create VideoFrame
        video_frame = VideoFrame.from_ndarray(frame_rgb, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        
        return video_frame
    
    def __del__(self):
        if self.cap is not None:
            self.cap.release()


# ============================================================================
# Main WebRTC + MQTT Sender
# ============================================================================

async def run_sender(video_source: str, server_url: str, fps: int, 
                    mqtt_broker: str = None, mqtt_port: int = 1883, use_camera: bool = False,
                    camera_width: int = 1920, camera_height: int = 1080):
    """
    Run integrated WebRTC sender with MQTT support.
    
    Args:
        video_source: Path to video file OR 'camera' for Pi Camera
        use_camera: If True, use Pi Camera instead of video file
        camera_width: Camera resolution width
        camera_height: Camera resolution height
    """
    logger.info(f"Starting integrated sender")
    
    if use_camera:
        logger.info(f"Camera: {camera_width}x{camera_height}, FPS: {fps}")
    else:
        logger.info(f"Video: {video_source}, FPS: {fps}")
    
    logger.info(f"WebRTC Signaling: {server_url}")
    if mqtt_broker:
        logger.info(f"MQTT Broker: {mqtt_broker}:{mqtt_port}")
    
    # Check video source
    if not use_camera:
        if not Path(video_source).exists():
            logger.error(f"Video file not found: {video_source}")
            return
    else:
        logger.info("Using Pi Camera Module")
    
    # Initialize Robot Controller (optional)
    robot_controller = None
    try:
        from robot_controller import RobotCarController
        robot_controller = RobotCarController()
        logger.info("✅ Robot hardware controller initialized")
    except ImportError:
        logger.warning("⚠️  robot_controller.py not found - running without hardware control")
    except Exception as e:
        logger.warning(f"⚠️  Failed to initialize robot hardware: {e}")
        logger.warning("Continuing without hardware control (commands will be logged only)")
    
    # Setup MQTT
    mqtt_handler = None
    if mqtt_broker:
        mqtt_handler = MQTTHandler(mqtt_broker, mqtt_port, robot_controller=robot_controller)
        if not mqtt_handler.connect():
            logger.warning("MQTT connection failed, continuing without MQTT")
            mqtt_handler = None
    
    # Create peer connection
    pc = RTCPeerConnection()
    
    # Add video track (camera or file)
    try:
        if use_camera:
            # Import camera track
            from camera_track import PiCameraTrackWithMQTT
            video_track = PiCameraTrackWithMQTT(
                width=camera_width,
                height=camera_height,
                fps=fps,
                mqtt_handler=mqtt_handler
            )
            logger.info("Pi Camera track created")
        else:
            video_track = VideoFileTrackWithMQTT(video_source, fps=fps, mqtt_handler=mqtt_handler)
            logger.info("Video file track created")
        
        pc.addTrack(video_track)
        logger.info("Video track added")
    except Exception as e:
        logger.error(f"Error creating video track: {e}")
        if mqtt_handler:
            mqtt_handler.disconnect()
        return
    
    # Event handlers
    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info(f"WebRTC connection state: {pc.connectionState}")
        if pc.connectionState == "failed":
            await pc.close()
    
    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        logger.info(f"ICE connection state: {pc.iceConnectionState}")
    
    # Connect to signaling server
    async with SignalingClient(server_url) as signaling:
        logger.info("Checking signaling server...")
        if not await signaling.check_health():
            logger.error("Signaling server not responding")
            if mqtt_handler:
                mqtt_handler.disconnect()
            return
        
        logger.info("Creating WebRTC offer...")
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        
        logger.info("Sending offer...")
        if not await signaling.send_offer(
            pc.localDescription.sdp, 
            pc.localDescription.type
        ):
            logger.error("Failed to send offer")
            if mqtt_handler:
                mqtt_handler.disconnect()
            return
        
        logger.info("Waiting for answer...")
        answer_data = await signaling.get_answer(timeout=60)
        
        if not answer_data:
            logger.error("Did not receive answer")
            if mqtt_handler:
                mqtt_handler.disconnect()
            return
        
        answer = RTCSessionDescription(
            sdp=answer_data["sdp"],
            type=answer_data["type"]
        )
        await pc.setRemoteDescription(answer)
        
        logger.info("=" * 60)
        logger.info("WebRTC connection established!")
        logger.info(f"Streaming video at {fps} FPS")
        if mqtt_handler and mqtt_handler.connected:
            logger.info("MQTT connected - sensor data synchronized")
        logger.info("=" * 60)
        
        # Keep running
        try:
            while pc.connectionState != "closed":
                await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Stopping sender...")
        
        finally:
            logger.info("Closing connections...")
            await pc.close()
            if mqtt_handler:
                mqtt_handler.disconnect()
            if robot_controller:
                robot_controller.cleanup()
                logger.info("Robot hardware cleaned up")


def main():
    parser = argparse.ArgumentParser(
        description="Integrated WebRTC + MQTT Sender (Raspberry Pi)"
    )
    parser.add_argument(
        "--video",
        default="video.mp4",
        help="Path to video file (ignored if --camera is used)"
    )
    parser.add_argument(
        "--camera",
        action="store_true",
        help="Use Pi Camera Module instead of video file"
    )
    parser.add_argument(
        "--camera-width",
        type=int,
        default=1920,
        help="Camera resolution width (default: 1920)"
    )
    parser.add_argument(
        "--camera-height",
        type=int,
        default=1080,
        help="Camera resolution height (default: 1080)"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Target FPS for streaming"
    )
    parser.add_argument(
        "--server-ip",
        required=True,
        help="Signaling server IP (Windows laptop IP)"
    )
    parser.add_argument(
        "--server-port",
        type=int,
        default=8080,
        help="Signaling server port"
    )
    parser.add_argument(
        "--mqtt-broker",
        help="MQTT broker IP (usually same as server-ip)"
    )
    parser.add_argument(
        "--mqtt-port",
        type=int,
        default=1883,
        help="MQTT broker port"
    )
    
    args = parser.parse_args()
    
    # Run sender
    server_url = f"http://{args.server_ip}:{args.server_port}"
    mqtt_broker = args.mqtt_broker if args.mqtt_broker else args.server_ip
    
    try:
        asyncio.run(run_sender(
            video_source=args.video,
            server_url=server_url,
            fps=args.fps,
            mqtt_broker=mqtt_broker,
            mqtt_port=args.mqtt_port,
            use_camera=args.camera,
            camera_width=args.camera_width,
            camera_height=args.camera_height
        ))
    except KeyboardInterrupt:
        logger.info("Sender stopped by user")


if __name__ == "__main__":
    main()
