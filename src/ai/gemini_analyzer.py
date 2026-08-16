"""
Analyseur avec Google Gemini AI pour la confirmation des signaux
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.generativeai as genai
from .prompt_templates import GeminiPromptTemplates

logger = logging.getLogger(__name__)

class GeminiAnalyzer:
    """Analyseur de marché utilisant Google Gemini AI"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        # Configuration du modèle
        self.model = genai.GenerativeModel(
            model_name='gemini-pro',
            generation_config={
                'temperature': 0.1,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 2048,
            }
        )
        
        self.prompts = GeminiPromptTemplates()
        self.analysis_cache = {}
        self.cache_duration = 60  # secondes
        
    async def analyze_market(self, market_data: Dict, technical_indicators: Dict) -> Dict:
        """
        Analyse complète du marché avec Gemini
        """
        try:
            # Préparer les données pour Gemini
            prompt = self.prompts.market_analysis_prompt(
                market_data=market_data,
                indicators=technical_indicators
            )
            
            # Obtenir l'analyse
            response = await self._get_analysis(prompt)
            
            # Parser la réponse
            analysis = self._parse_response(response)
            
            # Ajouter la confiance
            analysis['confidence'] = self._calculate_confidence(analysis)
            analysis['timestamp'] = datetime.now().isoformat()
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur analyse Gemini: {e}")
            return {
                'signal': 'NO_SIGNAL',
                'confidence': 0,
                'reason': f"Erreur Gemini: {str(e)}",
                'error': str(e)
            }
    
    async def _get_analysis(self, prompt: str) -> str:
        """
        Envoie la requête à Gemini
        """
        try:
            # Exécuter en boucle asynchrone
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self.model.generate_content,
                prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Erreur requête Gemini: {e}")
            raise
    
    def _parse_response(self, response: str) -> Dict:
        """
        Parse la réponse de Gemini en JSON structuré
        """
        try:
            # Essayer de parser le JSON directement
            data = json.loads(response)
            return data
        except json.JSONDecodeError:
            # Si ce n'est pas du JSON, extraire les informations
            lines = response.lower().split('\n')
            analysis = {
                'signal': 'NO_SIGNAL',
                'confidence': 50,
                'analysis': response
            }
            
            # Extraire le signal
            if 'call' in response.lower() or 'achat' in response.lower():
                analysis['signal'] = 'CALL'
            elif 'put' in response.lower() or 'vente' in response.lower():
                analysis['signal'] = 'PUT'
                
            # Extraire la confiance
            for line in lines:
                if 'confiance' in line or 'confidence' in line:
                    try:
                        # Chercher un pourcentage
                        parts = line.split(':') if ':' in line else line.split(' ')
                        for part in parts:
                            if '%' in part:
                                value = part.replace('%', '').strip()
                                if value.isdigit():
                                    analysis['confidence'] = int(value)
                                    break
                    except:
                        pass
            
            return analysis
    
    def _calculate_confidence(self, analysis: Dict) -> float:
        """
        Calcule le score de confiance basé sur l'analyse
        """
        base_confidence = analysis.get('confidence', 50)
        
        # Ajustements basés sur le signal
        if analysis['signal'] == 'CALL':
            factors = [
                'tendance haussière' in str(analysis).lower(),
                'support' in str(analysis).lower(),
                'volume' in str(analysis).lower()
            ]
        elif analysis['signal'] == 'PUT':
            factors = [
                'tendance baissière' in str(analysis).lower(),
                'résistance' in str(analysis).lower(),
                'volume' in str(analysis).lower()
            ]
        else:
            return 0
            
        # Augmenter la confiance pour chaque facteur
        bonus = sum(10 for f in factors if f)
        return min(base_confidence + bonus, 100)
    
    async def confirm_signal(self, technical_signal: Dict, market_data: Dict) -> Dict:
        """
        Confirme un signal technique avec l'IA Gemini
        """
        try:
            prompt = self.prompts.signal_confirmation_prompt(
                signal=technical_signal,
                market_data=market_data
            )
            
            response = await self._get_analysis(prompt)
            confirmation = self._parse_response(response)
            
            return {
                'confirmed': confirmation.get('confirmed', False),
                'confidence': confirmation.get('confidence', 0),
                'analysis': confirmation.get('analysis', ''),
                'recommendation': confirmation.get('recommendation', '')
            }
            
        except Exception as e:
            logger.error(f"Erreur confirmation signal: {e}")
            return {
                'confirmed': False,
                'confidence': 0,
                'analysis': f"Erreur: {str(e)}",
                'recommendation': 'Ne pas trader'
            }
    
    async def analyze_risk(self, trade_setup: Dict) -> Dict:
        """
        Analyse du risque avec Gemini
        """
        try:
            prompt = self.prompts.risk_analysis_prompt(trade_setup)
            response = await self._get_analysis(prompt)
            risk_analysis = self._parse_response(response)
            
            return {
                'risk_level': risk_analysis.get('risk_level', 'HIGH'),
                'risk_score': risk_analysis.get('risk_score', 100),
                'recommendation': risk_analysis.get('recommendation', ''),
                'stop_loss': risk_analysis.get('stop_loss', 0),
                'take_profit': risk_analysis.get('take_profit', 0)
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse risque: {e}")
            return {
                'risk_level': 'HIGH',
                'risk_score': 100,
                'recommendation': 'Erreur lors de l\'analyse',
                'stop_loss': 0,
                'take_profit': 0
            }
