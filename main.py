import os

from dotenv import load_dotenv

load_dotenv(".env.local")

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot import db
from bot.health import iniciar_health_server
from bot.logging_config import configurar_logging
from bot.handlers.start import start
from bot.handlers.vincular import vincular
from bot.handlers.registro import registrar_servicio
from bot.handlers.consulta import hoy, rs
from bot.handlers.editar import editar, eliminar

configurar_logging()
import logging
logger = logging.getLogger(__name__)


async def on_startup(app: Application):
    await iniciar_health_server(port=int(os.environ.get("PORT", 8080)))
    logger.info("health_server_iniciado")
    try:
        await db.init_pool()
        logger.info("db_pool_iniciado")
    except Exception:
        logger.exception("db_pool_error")
        raise


async def on_shutdown(app: Application):
    await db.close_pool()


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = (
        Application.builder()
        .token(token)
        .post_init(on_startup)
        .post_shutdown(on_shutdown)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("vincular", vincular))
    app.add_handler(CommandHandler("hoy", hoy))
    app.add_handler(CommandHandler("rs", rs))
    app.add_handler(CommandHandler("editar", editar))
    app.add_handler(CommandHandler("eliminar", eliminar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_servicio))

    app.run_polling()


if __name__ == "__main__":
    main()