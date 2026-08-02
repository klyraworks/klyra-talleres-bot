from telegram import Update
from telegram.ext import ContextTypes

from bot import db
from bot.parser import parsear_servicio


async def registrar_servicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenant_user = await db.resolver_tenant(update, context)
    if tenant_user is None:
        return
    tenant_user_id, tenant_id, role, name = tenant_user

    datos = parsear_servicio(update.message.text)
    if datos is None:
        await update.message.reply_text(
            "Formato no reconocido. Usa: [placa] monto_total [monto_pendiente]p descripción"
        )
        return

    vehicle_id = None
    if datos["placa"]:
        vehicle = await db.pool.fetchrow(
            "SELECT id FROM vehicles WHERE tenant_id = $1 AND plate = $2 AND deleted_at IS NULL",
            tenant_id, datos["placa"],
        )
        if vehicle is None:
            vehicle = await db.pool.fetchrow(
                """
                INSERT INTO vehicles (tenant_id, plate, profile_complete, created_by_type, created_by_id)
                VALUES ($1, $2, false, 'bot', $3)
                RETURNING id
                """,
                tenant_id, datos["placa"], tenant_user_id,
            )
            await db.registrar_log(tenant_id, tenant_user_id, "create", "vehicle", vehicle["id"], {"after": {"plate": datos["placa"]}})
        vehicle_id = vehicle["id"]

    servicio = await db.pool.fetchrow(
        """
        INSERT INTO services (tenant_id, vehicle_id, mechanic_id, total_amount, pending_amount, description)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
        """,
        tenant_id, vehicle_id, tenant_user_id,
        datos["total_amount"], datos["pending_amount"], datos["descripcion"],
    )
    await db.registrar_log(
        tenant_id, tenant_user_id, "create", "service", servicio["id"],
        {"after": {
            "total_amount": datos["total_amount"],
            "pending_amount": datos["pending_amount"],
            "description": datos["descripcion"],
        }},
    )

    await update.message.reply_text(
        f"✅ *Servicio registrado*\n"
        f"🚗 Placa: `{datos['placa'] or '—'}`\n"
        f"💵 Total: `${datos['total_amount']:,.2f}`\n"
        f"⏳ Pendiente: `${datos['pending_amount']:,.2f}`\n"
        f"👨‍🔧 Mecánico: {name}",
        parse_mode="Markdown",
    )