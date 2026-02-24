#!/usr/bin/env python3
"""
Signaling Server pentru WebRTC.
Rulează pe Windows pentru a minimiza consumul de resurse pe Raspberry Pi.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Import signaling
sys.path.insert(0, str(Path(__file__).parent.parent))
from common.signaling import SignalingServerSimple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_server(host: str, port: int):
    """
    Rulează signaling server.
    """
    logger.info("="*60)
    logger.info("WebRTC Signaling Server")
    logger.info("="*60)
    logger.info(f"Starting server on {host}:{port}")
    logger.info("")
    logger.info("This server facilitates WebRTC connection setup.")
    logger.info("It does NOT handle video data - only signaling.")
    logger.info("")
    logger.info("Keep this running while using the sender and receiver.")
    logger.info("="*60)
    logger.info("")
    
    server = SignalingServerSimple(host=host, port=port)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="WebRTC Signaling Server (runs on Windows)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0 - all interfaces)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)"
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_server(args.host, args.port))
    except KeyboardInterrupt:
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
