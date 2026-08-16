"""
Templates de prompts pour les modèles IA (Gemini, GPT)
"""

class GeminiPromptTemplates:
    """Templates de prompts pour Gemini"""
    
    def market_analysis_prompt(self, market_data: Dict, indicators: Dict) -> str:
        """Prompt pour l'analyse de marché"""
        return f"""
        En tant qu'analyste financier expert en options binaires, analysez ces données de marché :
        
        ### DONNÉES DE MARCHÉ
        - Actif : {market_data.get('asset', 'EUR/USD')}
        - Prix actuel : {market_data.get('price', 'N/A')}
        - Volatilité : {market_data.get('volatility', 'N/A')}
        
        ### INDICATEURS TECHNIQUES
        - Heikin Ashi : {indicators.get('ha_trend', 'N/A')}
        - Bollinger Bands : 
          - Supérieure : {indicators.get('bb_upper', 'N/A')}
          - Médiane : {indicators.get('bb_middle', 'N/A')}
          - Inférieure : {indicators.get('bb_lower', 'N/A')}
        - SMA 2 : {indicators.get('sma_2', 'N/A')}
        - SMA 5 : {indicators.get('sma_5', 'N/A')}
        - RSI (8) : {indicators.get('rsi', 'N/A')}
        
        ### ANALYSE REQUISE
        1. Analysez la tendance générale
        2. Identifiez les niveaux clés de support/résistance
        3. Évaluez les conditions de surachat/survente
        4. Donnez un signal : CALL, PUT, ou NO_SIGNAL
        5. Indiquez un niveau de confiance (0-100%)
        6. Expliquez votre raisonnement
        
        RÉPONDEZ UNIQUEMENT EN FORMAT JSON :
        {{
            "signal": "CALL/PUT/NO_SIGNAL",
            "confidence": 85,
            "trend": "haussière/baissière/neutre",
            "key_levels": {{
                "support": "1.0850",
                "resistance": "1.0950"
            }},
            "reasons": ["raison1", "raison2", "raison3"],
            "recommendation": "Action recommandée",
            "risk_level": "LOW/MEDIUM/HIGH"
        }}
        """
    
    def signal_confirmation_prompt(self, signal: Dict, market_data: Dict) -> str:
        """Prompt pour confirmer un signal"""
        return f"""
        CONFIRMEZ CE SIGNAL DE TRADING :
        
        ### SIGNAL TECHNIQUE
        - Direction : {signal.get('direction', 'N/A')}
        - Confiance technique : {signal.get('confidence', 0)}%
        - Raison : {signal.get('reason', 'N/A')}
        
        ### DONNÉES MARCHÉ ACTUELLES
        - Prix : {market_data.get('price', 'N/A')}
        - Volume : {market_data.get('volume', 'N/A')}
        - Momentum : {market_data.get('momentum', 'N/A')}
        
        ### TÂCHE
        1. Vérifiez la validité du signal
        2. Confirmez ou infirmez avec une analyse approfondie
        3. Donnez un niveau de confiance global
        4. Recommandez une action
        
        RÉPONSE EN JSON :
        {{
            "confirmed": true/false,
            "confidence": 85,
            "analysis": "Analyse détaillée...",
            "recommendation": "Achat/Vente/Attente",
            "additional_signals": []
        }}
        """
    
    def risk_analysis_prompt(self, trade_setup: Dict) -> str:
        """Prompt pour l'analyse de risque"""
        return f"""
        ANALYSE DE RISQUE POUR CE TRADE :
        
        ### CONFIGURATION DU TRADE
        - Actif : {trade_setup.get('asset', 'N/A')}
        - Direction : {trade_setup.get('direction', 'N/A')}
        - Montant : {trade_setup.get('amount', 'N/A')}
        - Expiration : {trade_setup.get('expiration', 'N/A')} minutes
        - Capital disponible : {trade_setup.get('balance', 'N/A')}
        
        ### ANALYSE REQUISE
        1. Évaluez le risque de ce trade (0-100%)
        2. Calculez un stop-loss optimal
        3. Calculez un take-profit optimal
        4. Donnez une recommandation de position sizing
        5. Identifiez les risques spécifiques
        
        RÉPONSE EN JSON :
        {{
            "risk_level": "LOW/MEDIUM/HIGH",
            "risk_score": 25,
            "stop_loss": 0.9500,
            "take_profit": 1.1000,
            "position_sizing": "2% du capital",
            "risks": ["risque1", "risque2"],
            "mitigation": ["mitigation1", "mitigation2"],
            "recommendation": "Trade acceptable/À éviter"
        }}
        """

class GPTPromptTemplates:
    """Templates de prompts pour ChatGPT/GPT-4"""
    
    def trading_decision_prompt(self, context: Dict) -> str:
        return f"""
        You are an expert financial analyst specialized in binary options trading.
        
        Market Context:
        {json.dumps(context, indent=2)}
        
        Please provide a comprehensive trading analysis with:
        1. Technical analysis summary
        2. Market sentiment
        3. Clear trading signal (CALL/PUT/NO_SIGNAL)
        4. Confidence level (0-100%)
        5. Risk assessment
        
        Format your response as JSON.
        """
