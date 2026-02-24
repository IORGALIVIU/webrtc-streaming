#!/usr/bin/env python3
"""
Sender application pentru Raspberry Pi.
Trimite video frames prin WebRTC cu timestamp.
"""

import asyncio
import argparse
import logging
import sys
import time
import cv2
import numpy as np
from pathlib import Path
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaBlackhole
from av import VideoFrame

# Import signaling
sys.path.insert(0, str(Path(__file__).parent.parent))
from common.signaling import SignalingServerSimple, SignalingClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoFileTrack(VideoStreamTrack):
    """
    Track video care citește din fișier și adaugă timestamp.
    """
    
    def __init__(self, video_path: str, fps: int = 30):
        super().__init__()
        self.video_path = video_path
        self.target_fps = fps
        self.cap = None
        self.frame_count = 0
        self.start_time = time.time()
        
        # Deschide video
        self._open_video()
        
    def _open_video(self):
        """Deschide fișierul video."""
        self.cap = cv2.VideoCapture(self.video_path)
        
        if not self.cap.isOpened():
            raise ValueError(f"Nu pot deschide video: {self.video_path}")
        
        # Informații despre video
        self.original_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        logger.info(f"Video loaded: {self.width}x{self.height}, "
                   f"{self.original_fps:.2f} FPS, {self.total_frames} frames")
    
    async def recv(self):
        """
        Primește următorul frame.
        Adaugă timestamp și îl trimite.
        """
        pts, time_base = await self.next_timestamp()
        
        # Citește frame
        ret, frame = self.cap.read()
        
        if not ret:
            # Restart video (loop)
            logger.info("Video ended, restarting...")
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            
            if not ret:
                logger.error("Cannot read frame even after restart")
                # Return black frame
                frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Timestamp curent
        current_time = time.time()
        timestamp_ms = int(current_time * 1000)
        elapsed = current_time - self.start_time
        
        # Adaugă informații pe frame
        cv2.putText(
            frame, 
            f"Timestamp: {timestamp_ms}", 
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, 
            (0, 255, 0), 
            2
        )
        
        cv2.putText(
            frame, 
            f"Frame: {self.frame_count} | Time: {elapsed:.2f}s", 
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            (0, 255, 0), 
            2
        )
        
        cv2.putText(
            frame, 
            f"Resolution: {self.width}x{self.height} | FPS: {self.target_fps}", 
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            (0, 255, 0), 
            2
        )
        
        self.frame_count += 1
        
        # Convert BGR (OpenCV) to RGB (VideoFrame)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create VideoFrame
        video_frame = VideoFrame.from_ndarray(frame_rgb, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        
        return video_frame
    
    def __del__(self):
        """Cleanup."""
        if self.cap is not None:
            self.cap.release()


async def run_sender(video_path: str, server_url: str, fps: int):
    """
    Rulează sender-ul WebRTC.
    """
    logger.info(f"Starting sender with video: {video_path}")
    
    # Verifică dacă fișierul există
    if not Path(video_path).exists():
        logger.error(f"Video file not found: {video_path}")
        return
    
    # Creează peer connection
    pc = RTCPeerConnection()
    
    # Adaugă video track
    try:
        video_track = VideoFileTrack(video_path, fps=fps)
        pc.addTrack(video_track)
        logger.info("Video track added")
    except Exception as e:
        logger.error(f"Error creating video track: {e}")
        return
    
    # Event handlers
    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info(f"Connection state: {pc.connectionState}")
        if pc.connectionState == "failed":
            await pc.close()
    
    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        logger.info(f"ICE connection state: {pc.iceConnectionState}")
    
    # Conectare la signaling server
    async with SignalingClient(server_url) as signaling:
        # Verifică server
        logger.info("Checking signaling server...")
        if not await signaling.check_health():
            logger.error("Signaling server is not responding")
            return
        
        logger.info("Signaling server is healthy")
        
        # Creează offer
        logger.info("Creating offer...")
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        
        # Trimite offer
        logger.info("Sending offer to signaling server...")
        if not await signaling.send_offer(
            pc.localDescription.sdp, 
            pc.localDescription.type
        ):
            logger.error("Failed to send offer")
            return
        
        logger.info("Offer sent successfully")
        logger.info("Waiting for answer from receiver...")
        
        # Așteaptă answer
        answer_data = await signaling.get_answer(timeout=60)
        
        if not answer_data:
            logger.error("Did not receive answer")
            return
        
        # Setează remote description
        logger.info("Setting remote description...")
        answer = RTCSessionDescription(
            sdp=answer_data["sdp"],
            type=answer_data["type"]
        )
        await pc.setRemoteDescription(answer)
        
        logger.info("WebRTC connection established!")
        logger.info(f"Streaming video at {fps} FPS...")
        
        # Keep running
        try:
            while pc.connectionState != "closed":
                await asyncio.sleep(1)
                
                # Log statistics every 10 seconds
                if int(time.time()) % 10 == 0:
                    stats = await pc.getStats()
                    logger.info(f"Frames sent: {video_track.frame_count}")
        
        except KeyboardInterrupt:
            logger.info("Stopping sender...")
        
        finally:
            logger.info("Closing connection...")
            await pc.close()


async def run_signaling_server(host: str, port: int):
    """
    Rulează signaling server.
    """
    logger.info(f"Starting signaling server on {host}:{port}")
    server = SignalingServerSimple(host=host, port=port)
    await server.start()


def main():
    parser = argparse.ArgumentParser(
        description="WebRTC Video Sender (Raspberry Pi)"
    )
    parser.add_argument(
        "--mode",
        choices=["sender", "server"],
        default="sender",
        help="Run mode: sender or signaling server"
    )
    parser.add_argument(
        "--video",
        default="video.mp4",
        help="Path to video file (for sender mode)"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Target FPS for streaming"
    )
    parser.add_argument(
        "--server-ip",
        default="127.0.0.1",
        help="Signaling server IP"
    )
    parser.add_argument(
        "--server-port",
        type=int,
        default=8080,
        help="Signaling server port"
    )
    
    args = parser.parse_args()
    
    if args.mode == "server":
        # Run signaling server
        try:
            asyncio.run(run_signaling_server(args.server_ip, args.server_port))
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
    
    else:
        # Run sender
        server_url = f"http://{args.server_ip}:{args.server_port}"
        try:
            asyncio.run(run_sender(args.video, server_url, args.fps))
        except KeyboardInterrupt:
            logger.info("Sender stopped by user")


if __name__ == "__main__":
    main()
