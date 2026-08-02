# bot/rate_limiter.py
import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_requests: int = 15, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[int, list[float]] = defaultdict(list)

    def permitido(self, tenant_id: int) -> bool:
        ahora = time.monotonic()
        ventana = self._hits[tenant_id]
        while ventana and ahora - ventana[0] > self.window_seconds:
            ventana.pop(0)
        if len(ventana) >= self.max_requests:
            return False
        ventana.append(ahora)
        return True


limiter = RateLimiter(max_requests=15, window_seconds=60)

# Uso al inicio de cada handler, ya con tenant_id resuelto:
# if not limiter.permitido(tenant_id):
#     await update.message.reply_text("Muchas solicitudes seguidas. Espera un momento.")
#     return