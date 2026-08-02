import json
import os
import asyncpg
from telegram import Update
from telegram.ext import ContextTypes

from bot.rate_limiter import limiter

pool: asyncpg.Pool | None = None


async def init_pool():
    global pool
    pool = await asyncpg.create_pool(dsn=os.environ["DATABASE_URL"], statement_cache_size=0)
    return pool


async def close_pool():
    global pool
    if pool:
        await pool.close()
        pool = None


# 3.2 — Resolución de identidad. Todo handler restringido por tenant llama esto primero.
async def resolver_tenant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    row = await pool.fetchrow(
        "SELECT id, tenant_id, role, name FROM tenant_users WHERE telegram_user_id = $1 AND active = true",
        user_id,
    )
    if row is None:
        await update.message.reply_text(
            "🚫 *Cuenta no activada.*\nContacta al administrador de tu taller para que te vincule.",
            parse_mode="Markdown",
        )
        await pool.execute(
            "INSERT INTO pending_users (telegram_user_id, username, name) VALUES ($1,$2,$3)",
            user_id, update.effective_user.username, update.effective_user.full_name,
        )
        return None

    if not limiter.permitido(row["tenant_id"]):
        await update.message.reply_text("⏳ Muchas solicitudes seguidas. Espera un momento.")
        return None

    return row


async def registrar_log(tenant_id: int, actor_id: int, action: str, entity: str, entity_id: int | None, metadata: dict | None = None):
    await pool.execute(
        """
        INSERT INTO activity_logs (tenant_id, actor_type, actor_id, action, entity, entity_id, metadata)
        VALUES ($1, 'bot', $2, $3, $4, $5, $6)
        """,
        tenant_id, actor_id, action, entity, entity_id,
        json.dumps(metadata) if metadata else None,
    )