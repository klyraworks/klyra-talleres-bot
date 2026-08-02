import datetime

from telegram import Update
from telegram.ext import ContextTypes

from bot import db

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}


# 3.6 — Función base compartida por /hoy y /rs
async def resumen(fecha_inicio: datetime.date, fecha_fin: datetime.date, tenant_id: int):
    return await db.pool.fetchrow(
        """
        SELECT COUNT(*) AS cantidad,
               COALESCE(SUM(total_amount), 0) AS total,
               COALESCE(SUM(pending_amount), 0) AS pendiente
        FROM services
        WHERE tenant_id = $1
          AND deleted_at IS NULL
          AND performed_at::date BETWEEN $2 AND $3
        """,
        tenant_id, fecha_inicio, fecha_fin,
    )


def _rango_desde_args(args):
    hoy = datetime.date.today()
    if not args:
        return hoy, hoy

    arg = args[0].lower()

    if arg == "semana":
        lunes = hoy - datetime.timedelta(days=hoy.weekday())
        return lunes, hoy

    if arg in MESES:
        mes = MESES[arg]
        anio = hoy.year
        inicio = datetime.date(anio, mes, 1)
        if mes == 12:
            fin = datetime.date(anio, 12, 31)
        else:
            fin = datetime.date(anio, mes + 1, 1) - datetime.timedelta(days=1)
        return inicio, fin

    try:
        fecha = datetime.datetime.strptime(arg, "%d/%m/%Y").date()
        return fecha, fecha
    except ValueError:
        return None, None


def _barra(pct: float, length: int = 10) -> str:
    llenos = round(max(0, min(pct, 100)) / 100 * length)
    return "🟩" * llenos + "⬜" * (length - llenos)


async def _responder_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenant_user = await db.resolver_tenant(update, context)
    if tenant_user is None:
        return
    tenant_user_id, tenant_id, role, name = tenant_user

    if role not in ("admin", "manager"):
        await update.message.reply_text("No tienes permiso para usar este comando.")
        return

    fecha_inicio, fecha_fin = _rango_desde_args(context.args)
    if fecha_inicio is None:
        await update.message.reply_text(
            "Formato no reconocido. Usa: /rs, /rs dd/mm/aaaa, /rs semana o /rs <mes>"
        )
        return

    fila = await resumen(fecha_inicio, fecha_fin, tenant_id)

    rango_txt = fecha_inicio.strftime("%d/%m/%Y")
    if fecha_fin != fecha_inicio:
        rango_txt += f" → {fecha_fin.strftime('%d/%m/%Y')}"

    total = float(fila["total"])
    pendiente = float(fila["pendiente"])
    cobrado = total - pendiente
    pct_cobrado = (cobrado / total * 100) if total else 100

    await update.message.reply_text(
        f"📊 *Resumen* — {rango_txt}\n"
        f"🧾 Servicios: *{fila['cantidad']}*\n"
        f"💰 Total: `${total:,.2f}`\n"
        f"⏳ Pendiente: `${pendiente:,.2f}`\n"
        f"{_barra(pct_cobrado)} {pct_cobrado:.0f}% cobrado",
        parse_mode="Markdown",
    )


async def hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.args = []
    await _responder_resumen(update, context)


async def rs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _responder_resumen(update, context)