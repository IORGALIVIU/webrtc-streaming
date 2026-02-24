#!/usr/bin/env python3
"""
Script pentru generarea unui video de test.
Util dacă nu ai un video la dispoziție.
"""

import cv2
import numpy as np
import argparse
from pathlib import Path


def generate_test_video(
    output_path: str,
    duration: int = 30,
    fps: int = 30,
    width: int = 1280,
    height: int = 720
):
    """
    Generează un video de test cu forme animate și text.
    
    Args:
        output_path: Calea către fișierul de ieșire
        duration: Durata în secunde
        fps: Frame rate
        width: Lățimea video
        height: Înălțimea video
    """
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = duration * fps
    
    print(f"Generating test video: {width}x{height}, {fps} FPS, {duration}s")
    print(f"Total frames: {total_frames}")
    
    for frame_num in range(total_frames):
        # Create blank frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Background gradient
        for y in range(height):
            color = int(255 * (y / height))
            frame[y, :] = [color // 3, color // 2, color]
        
        # Moving circle
        circle_x = int(width * ((frame_num % fps) / fps))
        circle_y = height // 2
        cv2.circle(frame, (circle_x, circle_y), 50, (0, 255, 0), -1)
        
        # Moving rectangle
        rect_y = int(height * ((frame_num % (fps * 2)) / (fps * 2)))
        cv2.rectangle(
            frame,
            (width - 150, rect_y),
            (width - 50, rect_y + 100),
            (255, 0, 0),
            -1
        )
        
        # Rotating line
        angle = (frame_num * 5) % 360
        rad = np.radians(angle)
        center_x, center_y = width // 4, height // 4
        end_x = int(center_x + 100 * np.cos(rad))
        end_y = int(center_y + 100 * np.sin(rad))
        cv2.line(frame, (center_x, center_y), (end_x, end_y), (0, 255, 255), 3)
        
        # Frame number
        text = f"Frame: {frame_num + 1}/{total_frames}"
        cv2.putText(
            frame,
            text,
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )
        
        # Time
        time_sec = frame_num / fps
        time_text = f"Time: {time_sec:.2f}s"
        cv2.putText(
            frame,
            time_text,
            (50, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )
        
        # Info
        info_text = f"{width}x{height} @ {fps} FPS"
        cv2.putText(
            frame,
            info_text,
            (50, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )
        
        # Write frame
        out.write(frame)
        
        # Progress
        if (frame_num + 1) % fps == 0:
            progress = ((frame_num + 1) / total_frames) * 100
            print(f"Progress: {progress:.1f}%")
    
    out.release()
    print(f"\nVideo generated successfully: {output_path}")
    print(f"File size: {Path(output_path).stat().st_size / 1024 / 1024:.2f} MB")


def main():
    parser = argparse.ArgumentParser(
        description="Generate test video for WebRTC streaming"
    )
    parser.add_argument(
        "--output",
        default="test_video.mp4",
        help="Output video path"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Video duration in seconds"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Frame rate"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Video width"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Video height"
    )
    
    args = parser.parse_args()
    
    generate_test_video(
        args.output,
        args.duration,
        args.fps,
        args.width,
        args.height
    )


if __name__ == "__main__":
    main()
