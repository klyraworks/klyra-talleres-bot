from telegram import Update
from telegram.ext import ContextTypes

from bot import db
from bot.parser import parsear_edicion


async def _obtener_servicio_autorizado(update, tenant_id, role, tenant_user_id, service_id):
    """Devuelve la fila del servicio si existe y el usuario tiene permiso, o None (ya respondió el error)."""
    servicio = await db.pool.fetchrow(
        "SELECT mechanic_id, total_amount, pending_amount, description FROM services WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        service_id, tenant_id,
    )
    if servicio is None:
        await update.message.reply_text("❌ Servicio no encontrado.")
        return None

    if role == "mechanic" and servicio["mechanic_id"] != tenant_user_id:
        await update.message.reply_text("🚫 No puedes modificar un servicio registrado por otro mecánico.")
        return None

    return servicio


# /editar <id> monto_total [monto_pendiente]p descripción
async def editar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenant_user = await db.resolver_tenant(update, context)
    if tenant_user is None:
        return
    tenant_user_id, tenant_id, role, name = tenant_user

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "ℹ️ Uso: `/editar <id> monto_total [monto_pendiente]p descripción`",
            parse_mode="Markdown",
        )
        return

    service_id = int(context.args[0])
    partes = update.message.text.split(maxsplit=2)
    texto_datos = partes[2] if len(partes) > 2 else ""

    datos = parsear_edicion(texto_datos)
    if datos is None:
        await update.message.reply_text(
            "⚠️ Formato no reconocido. Uso: `/editar <id> monto_total [monto_pendiente]p descripción`",
            parse_mode="Markdown",
        )
        return

    previo = await _obtener_servicio_autorizado(update, tenant_id, role, tenant_user_id, service_id)
    if previo is None:
        return

    await db.pool.execute(
        """
        UPDATE services
        SET total_amount = $1, pending_amount = $2, description = $3,
            updated_at = now(), updated_by_type = 'bot', updated_by_id = $4
        WHERE id = $5
        """,
        datos["total_amount"], datos["pending_amount"], datos["descripcion"],
        tenant_user_id, service_id,
    )
    await db.registrar_log(
        tenant_id, tenant_user_id, "update", "service", service_id,
        {
            "before": {
                "total_amount": float(previo["total_amount"]),
                "pending_amount": float(previo["pending_amount"]),
                "description": previo["description"],
            },
            "after": {
                "total_amount": datos["total_amount"],
                "pending_amount": datos["pending_amount"],
                "description": datos["descripcion"],
            },
        },
    )
    await update.message.reply_text(f"✏️ *Servicio #{service_id}* actualizado.", parse_mode="Markdown")


# /eliminar <id>
async def eliminar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenant_user = await db.resolver_tenant(update, context)
    if tenant_user is None:
        return
    tenant_user_id, tenant_id, role, name = tenant_user

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("ℹ️ Uso: `/eliminar <id>`", parse_mode="Markdown")
        return

    service_id = int(context.args[0])

    previo = await _obtener_servicio_autorizado(update, tenant_id, role, tenant_user_id, service_id)
    if previo is None:
        return

    await db.pool.execute(
        """
        UPDATE services
        SET deleted_at = now(), updated_at = now(), updated_by_type = 'bot', updated_by_id = $1
        WHERE id = $2
        """,
        tenant_user_id, service_id,
    )
    await db.registrar_log(
        tenant_id, tenant_user_id, "delete", "service", service_id,
        {"before": {
            "total_amount": float(previo["total_amount"]),
            "pending_amount": float(previo["pending_amount"]),
            "description": previo["description"],
        }},
    )
    await update.message.reply_text(f"🗑️ *Servicio #{service_id}* eliminado.", parse_mode="Markdown")