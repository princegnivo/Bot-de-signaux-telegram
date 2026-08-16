"""
Point d'entrée principal du bot
"""

import asyncio
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config.settings import Config, TradingConfig
from src.bot.handlers import BotHandlers
from src.trading.pocket_option_api import PocketOptionAPI
from src.trading.strategy import AIStrategy
from src.ai.gemini_analyzer import GeminiAnalyzer
from src.ai.gpt_analyzer import GPTAnalyzer
from src.database.database import Database
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class TradingBot:
    """Bot principal de trading avec IA"""
    
    def __init__(self):
        self.config = Config()
        self.trading_config = TradingConfig()
        
        # Initialiser les composants
        self.db = Database(self.config.DATABASE_URL)
        self.pocket_option = PocketOptionAPI(
            email=self.config.PO_EMAIL,
            password=self.config.PO_PASSWORD,
            api_key=self.config.PO_API_KEY,
            base_url=self.config.PO_BASE_URL
        )
        
        # Initialiser les analyseurs IA
        self.gemini = GeminiAnalyzer(self.config.GEMINI_API_KEY)
        self.gpt = GPTAnalyzer(self.config.OPENAI_API_KEY)
        
        # Initialiser la stratégie
        self.strategy = AIStrategy(
            pocket_option=self.pocket_option,
            gemini=self.gemini,
            db=self.db,
            config={
                'min_confidence': self.trading_config.AI_CONFIDENCE_THRESHOLD * 100,
                'max_daily_trades': self.trading_config.MAX_DAILY_TRADES,
                'timeframe': self.trading_config.TIMEFRAME,
                'expiration': self.trading_config.EXPIRATION
            }
        )
        
        # Initialiser le bot Telegram
        self.bot_handlers = BotHandlers(
            strategy=self.strategy,
            pocket_option=self.pocket_option,
            gemini=self.gemini,
            config=self.config
        )
        
    async def run(self):
        """Démarre le bot"""
        try:
            # Vérifier la configuration
            self.config.validate()
            
            # Se connecter à Pocket Option
            await self.pocket_option.__aenter__()
            
            # Démarrer le bot Telegram
            application = Application.builder().token(self.config.TELEGRAM_TOKEN).build()
            
            # Ajouter les handlers
            application.add_handler(CommandHandler("start", self.bot_handlers.start))
            application.add_handler(CommandHandler("signal", self.bot_handlers.get_signal))
            application.add_handler(CommandHandler("stats", self.bot_handlers.get_stats))
            application.add_handler(CommandHandler("balance", self.bot_handlers.get_balance))
            application.add_handler(CommandHandler("positions", self.bot_handlers.get_positions))
            application.add_handler(CommandHandler("close", self.bot_handlers.close_position))
            application.add_handler(CallbackQueryHandler(self.bot_handlers.button_callback))
            
            logger.info("🚀 Bot de trading IA démarré avec succès!")
            logger.info(f"📊 Stratégie: {self.trading_config.STRATEGY_NAME}")
            logger.info(f"🤖 IA: Gemini + GPT Hybrid Mode")
            
            # Démarrer le polling
            await application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du bot: {e}")
            raise
        finally:
            if self.pocket_option:
                await self.pocket_option.__aexit__(None, None, None)

async def main():
    """Fonction principale"""
    bot = TradingBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot arrêté par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
