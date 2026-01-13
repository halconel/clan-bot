"""Main entry point for the clan registration bot."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from config.settings import load_settings
from database.database import create_database

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log"),
    ],
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Main function to run the bot."""
    # Load settings
    logger.info("Loading settings...")
    settings = load_settings()

    # Initialize database
    logger.info("Initializing database...")
    db = create_database(
        settings.database.database_url,
        echo=settings.logging.log_level == "DEBUG",
    )

    # Run migrations if needed
    try:
        await db.create_tables()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        await db.close()
        sys.exit(1)

    # Initialize bot and dispatcher
    logger.info("Initializing bot...")
    bot = Bot(token=settings.telegram.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # Store database instance in bot data for access in handlers
    dp["db"] = db
    dp["settings"] = settings

    # Register routers/handlers
    from bot.handlers import admin, common, registration

    dp.include_router(common.router)
    dp.include_router(registration.router)
    dp.include_router(admin.router)

    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
    finally:
        logger.info("Shutting down...")
        await bot.session.close()
        await db.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
