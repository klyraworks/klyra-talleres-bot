from telegram import Update
from telegram.ext import ContextTypes

from bot import db


# 3.3 — Onboarding vía deep link: https://t.me/TuBot?start=supermoto
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    ya_activo = await db.pool.fetchrow(
        "SELECT 1 FROM tenant_users WHERE telegram_user_id = $1 AND active = true",
        user_id,
    )
    if ya_activo:
        await update.message.reply_text("✅ Ya tienes acceso activo. Envía un servicio para registrarlo.")
        return

    tenant_hint = context.args[0] if context.args else None
    row = await db.pool.fetchrow(
        """
        INSERT INTO pending_users (telegram_user_id, username, name, tenant_hint)
        VALUES ($1,$2,$3,$4)
        ON CONFLICT (telegram_user_id) WHERE resolved = false DO NOTHING
        RETURNING id
        """,
        user_id, update.effective_user.username, update.effective_user.full_name, tenant_hint,
    )
    if row is None:
        await update.message.reply_text(
            "⏳ Ya tienes una solicitud pendiente. Espera a que el administrador la revise."
        )
        return

    await update.message.reply_text(
        "📨 *Solicitud enviada.*\nEl administrador de tu taller activará tu cuenta pronto.",
        parse_mode="Markdown",
    )