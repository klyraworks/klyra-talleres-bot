import os

from telegram import Update
from telegram.ext import ContextTypes

from bot import db

# load_dotenv(".env.local")

SUPERADMIN_TELEGRAM_ID = int(os.environ["SUPERADMIN_TELEGRAM_ID"])


# 3.4 — /vincular <telegram_id> <tenant_id> <role> <nombre completo> (solo superadmin)
async def vincular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != SUPERADMIN_TELEGRAM_ID:
        return

    if len(context.args) < 4:
        await update.message.reply_text(
            "ℹ️ Uso: `/vincular <telegram_id> <tenant_id> <role> <nombre completo>`",
            parse_mode="Markdown",
        )
        return

    telegram_id, tenant_id, role, *name = context.args
    if role not in ("admin", "manager", "mechanic"):
        await update.message.reply_text("⚠️ Rol inválido. Usa: `admin`, `manager` o `mechanic`.", parse_mode="Markdown")
        return

    try:
        creado = await db.pool.fetchrow(
            "INSERT INTO tenant_users (telegram_user_id, tenant_id, role, name) VALUES ($1,$2,$3,$4) RETURNING id",
            int(telegram_id), int(tenant_id), role, " ".join(name),
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error al vincular: `{e}`", parse_mode="Markdown")
        return

    await db.registrar_log(
        int(tenant_id), None, "create", "tenant_user", creado["id"],
        metadata={"after": {"name": " ".join(name), "role": role}, "vinculado_por": update.effective_user.id},
    )

    await update.message.reply_text(
        f"🔗 *Vinculado correctamente*\n👤 {' '.join(name)} — `{role}`",
        parse_mode="Markdown",
    )