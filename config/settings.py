"""
Configuration du bot de trading avec IA
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Charger les variables d'environnement
load_dotenv()

class Config:
    """Configuration principale du bot"""
    
    # Telegram
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    CHANNEL_LINK = os.getenv('TELEGRAM_CHANNEL_LINK')
    
    # Pocket Option
    PO_EMAIL = os.getenv('POCKET_OPTION_EMAIL')
    PO_PASSWORD = os.getenv('POCKET_OPTION_PASSWORD')
    PO_API_KEY = os.getenv('POCKET_OPTION_API_KEY')
    PO_BASE_URL = os.getenv('POCKET_OPTION_BASE_URL')
    
    # IA APIs
    GEMINI_API_KEY = os.getenv('GOOGLE_GEMINI_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Trading
    TIMEFRAME = os.getenv('DEFAULT_TIMEFRAME', '1m')
    EXPIRATION = int(os.getenv('DEFAULT_EXPIRATION', 1))
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', 100))
    MIN_CONFIDENCE = float(os.getenv('MIN_CONFIDENCE', 85))
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/trading.db')
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / 'data'
    LOGS_DIR = BASE_DIR / 'logs'
    
    @classmethod
    def validate(cls):
        """Valide la configuration"""
        required = [
            'TELEGRAM_TOKEN', 'PO_EMAIL', 'PO_PASSWORD',
            'GEMINI_API_KEY', 'OPENAI_API_KEY'
        ]
        missing = [r for r in required if not getattr(cls, r)]
        if missing:
            raise ValueError(f"Variables manquantes: {missing}")
        return True

class TradingConfig:
    """Configuration des stratégies de trading"""
    
    # Stratégie principale
    STRATEGY_NAME = "Pocket Option AI Strategy"
    STRATEGY_VERSION = "2.0.0"
    
    # Indicateurs
    HEIKIN_ASHI = True
    BOLLINGER_PERIOD = 20
    BOLLINGER_DEVIATION = 2
    SMA_FAST = 2
    SMA_SLOW = 5
    RSI_PERIOD = 8
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    
    # IA Parameters
    AI_CONFIDENCE_THRESHOLD = 0.85
    USE_GEMINI = True
    USE_GPT = True
    HYBRID_MODE = True
    
    # Risk Management
    MAX_RISK_PER_TRADE = 0.02  # 2% du capital
    MAX_DAILY_TRADES = 10
    STOP_LOSS = 0.85  # Perte max 15%
    TAKE_PROFIT = 1.5  # Gain cible 50%
    
    # Pocket Option spécifique
    ALLOWED_ASSETS = [
        'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD',
        'BTCUSD', 'ETHUSD', 'LTCUSD', 'XRPUSD'
    ]
    EXPIRATION_TIMES = [1, 5, 15, 30, 60]  # minutes
    
    @classmethod
    def get_asset_id(cls, symbol):
        """Récupère l'ID de l'actif pour Pocket Option"""
        assets = {
            'EURUSD': 1, 'GBPUSD': 2, 'USDJPY': 3,
            'BTCUSD': 4, 'ETHUSD': 5, 'LTCUSD': 6,
            'XRPUSD': 7, 'AUDUSD': 8
        }
        return assets.get(symbol.upper())
