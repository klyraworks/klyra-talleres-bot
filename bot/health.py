# bot/health.py
from aiohttp import web


async def health(_request):
    return web.json_response({"status": "ok"})


async def iniciar_health_server(port: int = 8080):
    app = web.Application()
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


# En main(), correr junto al polling del bot:
# async def main():
#     await iniciar_health_server(port=int(os.environ.get("PORT", 8080)))
#     await application.run_polling()
#
# En Railway: Settings > Healthcheck Path = /health, y activar Restart on failure.