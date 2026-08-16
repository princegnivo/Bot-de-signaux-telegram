"""
API Client pour Pocket Option avec authentification et trading automatique
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib
import hmac
import base64

logger = logging.getLogger(__name__)

class PocketOptionAPI:
    """Client pour l'API Pocket Option"""
    
    def __init__(self, email: str, password: str, api_key: str, base_url: str):
        self.email = email
        self.password = password
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.websocket = None
        self.is_connected = False
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def authenticate(self) -> bool:
        """
        Authentification à l'API Pocket Option
        """
        try:
            login_data = {
                'email': self.email,
                'password': self.password,
                'grant_type': 'password'
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v2/auth/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get('access_token')
                    self.refresh_token = data.get('refresh_token')
                    self.token_expiry = datetime.now() + timedelta(seconds=data.get('expires_in', 3600))
                    self.is_connected = True
                    logger.info("Authentification Pocket Option réussie")
                    return True
                else:
                    error = await response.text()
                    logger.error(f"Erreur d'authentification: {error}")
                    return False
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification: {e}")
            return False
    
    async def get_market_data(self, asset_id: int, timeframe: str = '1m', limit: int = 150) -> Dict:
        """
        Récupère les données de marché en direct
        """
        if not self.is_connected:
            await self.authenticate()
            
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            params = {
                'asset_id': asset_id,
                'timeframe': timeframe,
                'limit': limit
            }
            
            async with self.session.get(
                f"{self.base_url}/api/v2/market/data",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Erreur récupération données: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erreur get_market_data: {e}")
            return None
    
    async def get_candles(self, asset_id: int, timeframe: str = '1m', count: int = 150) -> List[Dict]:
        """
        Récupère les bougies OHLCV pour l'analyse
        """
        data = await self.get_market_data(asset_id, timeframe, count)
        if data and 'candles' in data:
            return data['candles']
        return []
    
    async def place_trade(self, asset_id: int, direction: str, amount: float, 
                          expiration: int, stop_loss: float = None, 
                          take_profit: float = None) -> Dict:
        """
        Place un ordre sur Pocket Option
        """
        if not self.is_connected:
            await self.authenticate()
            
        try:
            trade_data = {
                'asset_id': asset_id,
                'direction': direction,  # 'call' ou 'put'
                'amount': amount,
                'expiration': expiration,  # en minutes
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'strategy': 'AI_Strategy_v2'
            }
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v2/trading/order",
                headers=headers,
                json=trade_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Trade placé: {result}")
                    return result
                else:
                    error = await response.text()
                    logger.error(f"Erreur placement trade: {error}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erreur place_trade: {e}")
            return None
    
    async def get_balance(self) -> Dict:
        """
        Récupère le solde du compte
        """
        if not self.is_connected:
            await self.authenticate()
            
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            async with self.session.get(
                f"{self.base_url}/api/v2/account/balance",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Erreur récupération solde: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erreur get_balance: {e}")
            return None
    
    async def get_open_positions(self) -> List[Dict]:
        """
        Récupère les positions ouvertes
        """
        if not self.is_connected:
            await self.authenticate()
            
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            async with self.session.get(
                f"{self.base_url}/api/v2/trading/positions",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Erreur récupération positions: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Erreur get_open_positions: {e}")
            return []
    
    async def close_position(self, position_id: str) -> bool:
        """
        Ferme une position
        """
        if not self.is_connected:
            await self.authenticate()
            
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            async with self.session.delete(
                f"{self.base_url}/api/v2/trading/position/{position_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    logger.info(f"Position {position_id} fermée")
                    return True
                else:
                    logger.error(f"Erreur fermeture position: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Erreur close_position: {e}")
            return False
    
    async def stream_realtime_data(self, asset_ids: List[int], callback):
        """
        Streaming de données en temps réel via WebSocket
        """
        if not self.websocket:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            self.websocket = await self.session.ws_connect(
                f"{self.base_url}/ws/market",
                headers=headers
            )
            
            # S'abonner aux actifs
            subscribe_msg = {
                'action': 'subscribe',
                'assets': asset_ids
            }
            await self.websocket.send_json(subscribe_msg)
        
        try:
            async for msg in self.websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await callback(data)
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
        except Exception as e:
            logger.error(f"Erreur streaming: {e}")
        finally:
            if self.websocket:
                await self.websocket.close()
                self.websocket = None

    async def get_historical_data(self, asset_id: int, timeframe: str = '1m', 
                                 start: datetime = None, end: datetime = None) -> List[Dict]:
        """
        Récupère les données historiques pour l'entraînement IA
        """
        if not self.is_connected:
            await self.authenticate()
            
        try:
            params = {
                'asset_id': asset_id,
                'timeframe': timeframe,
                'start': start.isoformat() if start else None,
                'end': end.isoformat() if end else None,
                'limit': 1000
            }
            
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            async with self.session.get(
                f"{self.base_url}/api/v2/market/historical",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Erreur données historiques: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Erreur get_historical_data: {e}")
            return []
