# bot/logging_config.py
import json
import logging
import sys


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "event": record.getMessage(),
            "tenant_id": getattr(record, "tenant_id", None),
            "logger": record.name,
        }
        return json.dumps(payload, ensure_ascii=False)


def configurar_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])


# Uso — nunca loguear nombres, teléfonos ni descripciones completas:
# logger = logging.getLogger("bot")
# logger.info("servicio_registrado", extra={"tenant_id": tenant_id})