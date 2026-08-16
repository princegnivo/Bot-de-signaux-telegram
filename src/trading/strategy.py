"""
Stratégie de trading avancée avec IA et gestion de risque
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from .indicators import TechnicalIndicators
from .pocket_option_api import PocketOptionAPI
from ..ai.gemini_analyzer import GeminiAnalyzer
from ..ai.hybrid_analyzer import HybridAnalyzer
from ..database.database import Database
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class AIStrategy:
    """Stratégie de trading avec IA intégrée"""
    
    def __init__(self, pocket_option: PocketOptionAPI, gemini: GeminiAnalyzer, 
                 db: Database = None, config: Dict = None):
        self.pocket_option = pocket_option
        self.gemini = gemini
        self.db = db
        self.config = config or {}
        self.indicators = TechnicalIndicators()
        self.hybrid_analyzer = HybridAnalyzer(gemini)
        
        # Paramètres stratégiques
        self.min_confidence = self.config.get('min_confidence', 85)
        self.max_risk = self.config.get('max_risk_per_trade', 0.02)
        self.timeframe = self.config.get('timeframe', '1m')
        self.expiration = self.config.get('expiration', 1)
        
        # Stats de trading
        self.trading_stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0,
            'total_loss': 0,
            'win_rate': 0
        }
    
    async def analyze_and_act(self, asset: str) -> Dict:
        """
        Analyse complète et exécution si conditions remplies
        """
        try:
            # 1. Récupération des données en direct
            asset_id = self._get_asset_id(asset)
            market_data = await self.pocket_option.get_market_data(asset_id, self.timeframe)
            
            if not market_data:
                return {'success': False, 'error': 'Impossible de récupérer les données'}
            
            # 2. Calcul des indicateurs techniques
            indicators = self.indicators.calculate_all(market_data)
            
            # 3. Signal technique initial
            tech_signal = self._generate_technical_signal(indicators)
            
            # 4. Analyse IA avec Gemini
            ai_analysis = await self.gemini.analyze_market(market_data, indicators)
            
            # 5. Analyse hybride
            hybrid_signal = await self.hybrid_analyzer.analyze(
                tech_signal=tech_signal,
                ai_analysis=ai_analysis,
                market_data=market_data
            )
            
            # 6. Vérification des conditions de trading
            if not self._should_trade(hybrid_signal):
                return {
                    'success': False,
                    'signal': hybrid_signal,
                    'reason': 'Conditions de trading non remplies'
                }
            
            # 7. Analyse du risque
            risk_analysis = await self.gemini.analyze_risk({
                'asset': asset,
                'direction': hybrid_signal['signal'],
                'amount': self._calculate_position_size(),
                'expiration': self.expiration,
                'balance': await self.pocket_option.get_balance()
            })
            
            # 8. Exécution du trade
            trade_result = await self._execute_trade(
                asset=asset,
                direction=hybrid_signal['signal'],
                confidence=hybrid_signal['confidence'],
                risk_analysis=risk_analysis
            )
            
            # 9. Sauvegarde des résultats
            await self._save_trade_result(trade_result, hybrid_signal)
            
            return trade_result
            
        except Exception as e:
            logger.error(f"Erreur dans analyze_and_act: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_technical_signal(self, indicators: Dict) -> Dict:
        """
        Génère un signal basé sur les indicateurs techniques
        """
        signal = {
            'direction': 'NO_SIGNAL',
            'confidence': 0,
            'reason': 'Aucun signal technique'
        }
        
        # Conditions CALL
        if (indicators['ha_trend'] == 1 and 
            indicators['bb_contact_lower'] and 
            indicators['sma_cross'] == 1 and 
            indicators['rsi'] > 30 and 
            indicators['rsi'] < 60):
            
            signal['direction'] = 'CALL'
            signal['confidence'] = self._calculate_tech_confidence(indicators, 'CALL')
            signal['reason'] = 'Signal technique CALL confirmé'
            
        # Conditions PUT
        elif (indicators['ha_trend'] == -1 and 
              indicators['bb_contact_upper'] and 
              indicators['sma_cross'] == -1 and 
              indicators['rsi'] < 70 and 
              indicators['rsi'] > 40):
            
            signal['direction'] = 'PUT'
            signal['confidence'] = self._calculate_tech_confidence(indicators, 'PUT')
            signal['reason'] = 'Signal technique PUT confirmé'
        
        return signal
    
    def _calculate_tech_confidence(self, indicators: Dict, direction: str) -> float:
        """
        Calcule la confiance du signal technique
        """
        confidence = 50  # Base
        
        if direction == 'CALL':
            # Facteurs de confiance pour CALL
            if indicators['bb_contact_lower']:
                confidence += 15
            if indicators['sma_cross'] == 1:
                confidence += 20
            if indicators['ha_trend'] == 1:
                confidence += 15
            if indicators['rsi'] > 30 and indicators['rsi'] < 50:
                confidence += 10
                
        else:  # PUT
            if indicators['bb_contact_upper']:
                confidence += 15
            if indicators['sma_cross'] == -1:
                confidence += 20
            if indicators['ha_trend'] == -1:
                confidence += 15
            if indicators['rsi'] > 50 and indicators['rsi'] < 70:
                confidence += 10
        
        return min(confidence, 100)
    
    def _should_trade(self, hybrid_signal: Dict) -> bool:
        """
        Vérifie si les conditions de trading sont remplies
        """
        # Vérifier la confiance
        if hybrid_signal.get('confidence', 0) < self.min_confidence:
            return False
        
        # Vérifier le signal
        if hybrid_signal.get('signal') not in ['CALL', 'PUT']:
            return False
        
        # Vérifier les limites de trading
        if self.trading_stats['total_trades'] >= self.config.get('max_daily_trades', 10):
            return False
        
        return True
    
    def _calculate_position_size(self) -> float:
        """
        Calcule la taille de la position basée sur le risk management
        """
        try:
            balance = self.pocket_option.get_balance()
            if not balance:
                return 10  # Montant par défaut
            
            available = balance.get('available', 1000)
            max_loss = available * self.max_risk
            
            # Taille de position adaptative
            return min(max_loss, 100)  # Max 100$ par trade
            
        except Exception as e:
            logger.error(f"Erreur calcul position size: {e}")
            return 10
    
    async def _execute_trade(self, asset: str, direction: str, 
                            confidence: float, risk_analysis: Dict) -> Dict:
        """
        Exécute le trade
        """
        try:
            asset_id = self._get_asset_id(asset)
            amount = self._calculate_position_size()
            
            # Calculer stop-loss et take-profit
            stop_loss = risk_analysis.get('stop_loss')
            take_profit = risk_analysis.get('take_profit')
            
            # Placer l'ordre
            trade_result = await self.pocket_option.place_trade(
                asset_id=asset_id,
                direction=direction.lower(),
                amount=amount,
                expiration=self.expiration,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            if trade_result:
                self.trading_stats['total_trades'] += 1
                
                return {
                    'success': True,
                    'trade_id': trade_result.get('id'),
                    'asset': asset,
                    'direction': direction,
                    'amount': amount,
                    'confidence': confidence,
                    'expiration': self.expiration,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Échec du placement de l\'ordre'
                }
                
        except Exception as e:
            logger.error(f"Erreur exécution trade: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_asset_id(self, asset: str) -> int:
        """
        Convertit le symbole en ID Pocket Option
        """
        asset_map = {
            'EURUSD': 1, 'GBPUSD': 2, 'USDJPY': 3,
            'AUDUSD': 4, 'USDCAD': 5, 'USDCHF': 6,
            'NZDUSD': 7, 'BTCUSD': 8, 'ETHUSD': 9,
            'LTCUSD': 10, 'XRPUSD': 11, 'SOLUSD': 12
        }
        return asset_map.get(asset.upper(), 1)
    
    async def _save_trade_result(self, trade_result: Dict, signal: Dict):
        """
        Sauvegarde le résultat du trade dans la base de données
        """
        if self.db and trade_result.get('success'):
            await self.db.save_trade({
                'trade_id': trade_result.get('trade_id'),
                'asset': trade_result.get('asset'),
                'direction': trade_result.get('direction'),
                'amount': trade_result.get('amount'),
                'confidence': trade_result.get('confidence'),
                'signal': signal,
                'timestamp': datetime.now().isoformat()
            })
    
    async def update_stats(self, trade_result: Dict):
        """
        Met à jour les statistiques de trading
        """
        if trade_result.get('success'):
            if trade_result.get('profit', 0) > 0:
                self.trading_stats['winning_trades'] += 1
                self.trading_stats['total_profit'] += trade_result['profit']
            else:
                self.trading_stats['losing_trades'] += 1
                self.trading_stats['total_loss'] += abs(trade_result.get('loss', 0))
            
            total = self.trading_stats['winning_trades'] + self.trading_stats['losing_trades']
            if total > 0:
                self.trading_stats['win_rate'] = (
                    self.trading_stats['winning_trades'] / total * 100
                )
