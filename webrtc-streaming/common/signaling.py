"""
Signaling server și client pentru stabilirea conexiunilor WebRTC.
Folosit pentru schimbul de SDP offers/answers și ICE candidates.
"""

import asyncio
import json
import logging
from aiohttp import web, ClientSession
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class SignalingServer:
    """HTTP server simplu pentru signaling WebRTC."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.app.router.add_post('/offer', self.handle_offer)
        self.app.router.add_post('/answer', self.handle_answer)
        self.app.router.add_post('/ice', self.handle_ice)
        self.app.router.add_get('/health', self.handle_health)
        
        self.offer_data: Optional[dict] = None
        self.answer_data: Optional[dict] = None
        self.ice_candidates: list = []
        
    async def handle_health(self, request):
        """Health check endpoint."""
        return web.json_response({"status": "ok"})
    
    async def handle_offer(self, request):
        """Primește SDP offer de la sender."""
        try:
            data = await request.json()
            self.offer_data = data
            logger.info("Offer received and stored")
            return web.json_response({"status": "ok"})
        except Exception as e:
            logger.error(f"Error handling offer: {e}")
            return web.json_response({"status": "error", "message": str(e)}, status=400)
    
    async def handle_answer(self, request):
        """Primește SDP answer de la receiver."""
        try:
            data = await request.json()
            self.answer_data = data
            logger.info("Answer received and stored")
            return web.json_response({"status": "ok"})
        except Exception as e:
            logger.error(f"Error handling answer: {e}")
            return web.json_response({"status": "error", "message": str(e)}, status=400)
    
    async def handle_ice(self, request):
        """Primește ICE candidates."""
        try:
            data = await request.json()
            self.ice_candidates.append(data)
            logger.info(f"ICE candidate received: {data.get('role', 'unknown')}")
            return web.json_response({"status": "ok"})
        except Exception as e:
            logger.error(f"Error handling ICE: {e}")
            return web.json_response({"status": "error", "message": str(e)}, status=400)
    
    async def start(self):
        """Pornește server-ul."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"Signaling server running on http://{self.host}:{self.port}")
        
        # Keep running
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            pass


class SignalingClient:
    """Client pentru comunicare cu signaling server."""
    
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip('/')
        self.session: Optional[ClientSession] = None
        
    async def __aenter__(self):
        self.session = ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_offer(self, sdp: str, sdp_type: str) -> bool:
        """Trimite SDP offer la server."""
        try:
            data = {"sdp": sdp, "type": sdp_type}
            async with self.session.post(f"{self.server_url}/offer", json=data) as resp:
                result = await resp.json()
                logger.info(f"Offer sent: {result.get('status')}")
                return result.get('status') == 'ok'
        except Exception as e:
            logger.error(f"Error sending offer: {e}")
            return False
    
    async def send_answer(self, sdp: str, sdp_type: str) -> bool:
        """Trimite SDP answer la server."""
        try:
            data = {"sdp": sdp, "type": sdp_type}
            async with self.session.post(f"{self.server_url}/answer", json=data) as resp:
                result = await resp.json()
                logger.info(f"Answer sent: {result.get('status')}")
                return result.get('status') == 'ok'
        except Exception as e:
            logger.error(f"Error sending answer: {e}")
            return False
    
    async def send_ice_candidate(self, candidate: dict, role: str) -> bool:
        """Trimite ICE candidate la server."""
        try:
            data = {"candidate": candidate, "role": role}
            async with self.session.post(f"{self.server_url}/ice", json=data) as resp:
                result = await resp.json()
                return result.get('status') == 'ok'
        except Exception as e:
            logger.error(f"Error sending ICE candidate: {e}")
            return False
    
    async def get_offer(self, timeout: int = 30) -> Optional[dict]:
        """Așteaptă și primește offer de la server."""
        for _ in range(timeout * 2):  # Check every 0.5s
            try:
                async with self.session.get(f"{self.server_url}/offer") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data and 'sdp' in data:
                            logger.info("Offer received from server")
                            return data
            except Exception as e:
                logger.debug(f"Waiting for offer... {e}")
            
            await asyncio.sleep(0.5)
        
        logger.error("Timeout waiting for offer")
        return None
    
    async def get_answer(self, timeout: int = 30) -> Optional[dict]:
        """Așteaptă și primește answer de la server."""
        for _ in range(timeout * 2):  # Check every 0.5s
            try:
                async with self.session.get(f"{self.server_url}/answer") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data and 'sdp' in data:
                            logger.info("Answer received from server")
                            return data
            except Exception as e:
                logger.debug(f"Waiting for answer... {e}")
            
            await asyncio.sleep(0.5)
        
        logger.error("Timeout waiting for answer")
        return None
    
    async def check_health(self) -> bool:
        """Verifică dacă server-ul este accesibil."""
        try:
            async with self.session.get(f"{self.server_url}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('status') == 'ok'
        except Exception as e:
            logger.error(f"Health check failed: {e}")
        return False


# Versiune simplificată pentru polling (pentru compatibilitate cu alte implementări)
class SignalingServerSimple:
    """Versiune mai simplă cu polling pentru offer/answer."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.app.router.add_post('/offer', self.post_offer)
        self.app.router.add_get('/offer', self.get_offer)
        self.app.router.add_post('/answer', self.post_answer)
        self.app.router.add_get('/answer', self.get_answer)
        self.app.router.add_get('/health', self.handle_health)
        
        self.offer_data: Optional[dict] = None
        self.answer_data: Optional[dict] = None
        
    async def handle_health(self, request):
        return web.json_response({"status": "ok"})
    
    async def post_offer(self, request):
        try:
            self.offer_data = await request.json()
            logger.info("Offer stored")
            return web.json_response({"status": "ok"})
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=400)
    
    async def get_offer(self, request):
        if self.offer_data:
            return web.json_response(self.offer_data)
        return web.json_response({}, status=404)
    
    async def post_answer(self, request):
        try:
            self.answer_data = await request.json()
            logger.info("Answer stored")
            return web.json_response({"status": "ok"})
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=400)
    
    async def get_answer(self, request):
        if self.answer_data:
            return web.json_response(self.answer_data)
        return web.json_response({}, status=404)
    
    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"Signaling server (simple) running on http://{self.host}:{self.port}")
        
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            pass
