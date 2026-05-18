import os
import time
import gspread
import unicodedata
from dotenv import load_dotenv
from collections import defaultdict
from google.oauth2.service_account import Credentials

from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, CallbackQueryHandler, PreCheckoutQueryHandler,
    filters, ContextTypes
)

load_dotenv()

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
SHEET_ID       = os.environ.get('SHEET_ID')

# ================================================================
# CONFIGURACIÓN DE PAGOS
# Stars de Telegram: provider_token = "" para XTR (Stars)
# Para Redsys/Stripe: pon el token de BotFather aquí y cambia currency
# ================================================================
PAYMENT_PROVIDER_TOKEN = ""   # "" = Telegram Stars
STARS_ENTREGA          = 50   # Stars base de gastos de envío
STARS_POR_PRODUCTO     = 10   # Stars por cada producto de la lista

# ================================================================
# ESTADOS DE CONVERSACIÓN
# ================================================================
(BUSCAR_PRODUCTO, RECOMENDAR_CATEGORIA, LISTA_COMPRA,
 PEDIDO_NOMBRE, PEDIDO_TELEFONO, PEDIDO_DIRECCION,
 PEDIDO_CP, PEDIDO_CIUDAD, PEDIDO_CONFIRMAR) = range(9)

# ================================================================
# ALMACENAMIENTO EN MEMORIA
# ================================================================
listas_compra    = defaultdict(list)
pedidos_en_curso = {}

# ================================================================
# EMOJIS
# ================================================================
EMOJI_CATEGORIA = {
    'lácteos': '🥛', 'leche': '🥛', 'yogur': '🥛',
    'fruta': '🍎', 'frutas': '🍎', 'verdura': '🥦', 'verduras': '🥦',
    'carne': '🥩', 'carnes': '🥩', 'pollo': '🍗', 'pescado': '🐟',
    'pan': '🍞', 'panadería': '🍞', 'bollería': '🥐',
    'bebidas': '🥤', 'agua': '💧', 'refrescos': '🥤',
    'higiene': '🧴', 'limpieza': '🧹',
    'snacks': '🍪', 'galletas': '🍪', 'dulces': '🍫',
    'aceite': '🫙', 'conservas': '🥫',
    'congelados': '🧊', 'huevos': '🥚',
}
SUPERMERCADO_EMOJI = {
    'mercadona': '🟡', 'lidl': '🔵', 'alcampo': '🔴',
    'froiz': '🟢', 'gadis': '🟠',
}

# ================================================================
# GOOGLE SHEETS con caché de 10 minutos
# ================================================================
_cache_datos     = None
_cache_timestamp = 0

def conectar_sheets():
    scope   = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds   = Credentials.from_service_account_file('credenciales.json', scopes=scope)
    cliente = gspread.authorize(creds)
    return cliente.open_by_key(SHEET_ID).sheet1

def obtener_datos_sheets():
    global _cache_datos, _cache_timestamp
    ahora = time.time()
    if _cache_datos is None or (ahora - _cache_timestamp) > 600:
        _cache_datos     = conectar_sheets().get_all_records()
        _cache_timestamp = ahora
    return _cache_datos

def normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize('NFKD', texto.lower())
    return ''.join(c for c in texto if not unicodedata.combining(c)).strip()

def buscar_producto(texto: str):
    try:
        tn = normalizar_texto(texto)
        return [
            f for f in obtener_datos_sheets()
            if tn in normalizar_texto(str(f.get('Producto', '')))
            or tn in normalizar_texto(str(f.get('Categoría', '')))
        ]
    except Exception as e:
        print(f"Error buscando: {e}")
        return []

# ================================================================
# HELPERS VISUALES
# ================================================================
def emoji_para_categoria(cat: str) -> str:
    c = normalizar_texto(cat)
    for k, e in EMOJI_CATEGORIA.items():
        if k in c: return e
    return '🛒'

def emoji_supermercado(nom: str) -> str:
    n = normalizar_texto(nom)
    for k, e in SUPERMERCADO_EMOJI.items():
        if k in n: return e
    return '🏪'

def barra_precio(precio: float, maximo: float = 10.0) -> str:
    p = min(precio / maximo, 1.0)
    n = int(p * 8)
    return '█' * n + '░' * (8 - n)

def formatear_resultado(r: dict) -> str:
    super_name = str(r.get('Supermercado', '?'))
    prod_name  = str(r.get('Producto', '?'))
    precio_raw = r.get('Precio Total (€)', '')
    precio_kg  = r.get('Precio/kg o litro', '')
    categoria  = str(r.get('Categoría', ''))

    pl = str(precio_raw).replace(',', '.').replace('€', '').strip()
    try:
        pn = float(pl) if pl else None
    except (ValueError, TypeError):
        pn = None

    if pn and pn > 0:
        precio_str = f"{pn:.2f}€  <code>{barra_precio(pn)}</code>"
    elif pl and pl not in ('', '?', '-'):
        precio_str = f"{pl}€"
    else:
        precio_str = "<i>precio no disponible</i>"

    lineas = [
        f"{emoji_para_categoria(categoria)} <b>{prod_name}</b>",
        f"  {emoji_supermercado(super_name)} {super_name}",
        f"  💰 {precio_str}",
    ]
    if precio_kg:
        lineas.append(f"  📏 <i>{precio_kg}</i>")
    return '\n'.join(lineas)

# ================================================================
# TECLADOS
# ================================================================
def teclado_principal():
    return ReplyKeyboardMarkup([
        ["🔎 Buscar producto", "📊 Recomendaciones"],
        ["🛍️ Mi lista",        "🛒 Hacer pedido"],
        ["❓ Ayuda"],
    ], resize_keyboard=True)

def teclado_lista():
    return ReplyKeyboardMarkup([
        ["➕ Añadir productos", "📋 Ver lista"],
        ["🗑️ Limpiar lista",   "❌ Volver al menú"],
    ], resize_keyboard=True)

def teclado_cancelar():
    return ReplyKeyboardMarkup([["❌ Cancelar"]], resize_keyboard=True)

def inline_añadir_productos(resultados: list) -> InlineKeyboardMarkup:
    botones = []
    for r in resultados[:6]:
        prod   = str(r.get('Producto', '?'))
        super_ = str(r.get('Supermercado', ''))
        botones.append([InlineKeyboardButton(
            f"➕ {prod[:22]} ({super_[:8]})",
            callback_data=f"add|{prod[:40]}"
        )])
    botones.append([InlineKeyboardButton("🛍️ Ver mi lista completa", callback_data="ver_lista")])
    return InlineKeyboardMarkup(botones)

def inline_confirmar_pedido() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Pagar con Stars", callback_data="pedido_pagar_stars")],
        [
            InlineKeyboardButton("✏️ Corregir datos", callback_data="pedido_corregir"),
            InlineKeyboardButton("❌ Cancelar",        callback_data="pedido_cancelar"),
        ],
    ])

def inline_corregir_campos() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Cambiar nombre",    callback_data="editar|nombre")],
        [InlineKeyboardButton("📱 Cambiar teléfono",  callback_data="editar|telefono")],
        [InlineKeyboardButton("🏠 Cambiar dirección", callback_data="editar|direccion")],
        [InlineKeyboardButton("📮 Cambiar CP",        callback_data="editar|cp")],
        [InlineKeyboardButton("🏙️ Cambiar ciudad",   callback_data="editar|ciudad")],
        [InlineKeyboardButton("🛍️ Modificar lista",  callback_data="editar|lista")],
        [InlineKeyboardButton("↩️ Volver al resumen", callback_data="editar|volver")],
    ])

# ================================================================
# CÁLCULO DE STARS
# ================================================================
def calcular_stars(productos: list) -> int:
    return STARS_ENTREGA + STARS_POR_PRODUCTO * len(productos)

def stars_a_euros(stars: int) -> float:
    return round(stars * 0.012, 2)

# ================================================================
# /start y ayuda
# ================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.effective_user.first_name or "amigo/a"
    await update.message.reply_html(
        f"👋 ¡Hola, <b>{nombre}</b>! Bienvenido/a a <b>AhorraAI</b> 🛒\n\n"
        "Tu asistente de compra inteligente para Vigo y Galicia.\n\n"
        "🔎 <b>Busca</b> productos y compara precios entre supermercados\n"
        "📊 <b>Descubre</b> las mejores ofertas por categoría\n"
        "🛍️ <b>Gestiona</b> tu lista de la compra\n"
        "🚚 <b>Pide</b> a domicilio y paga con ⭐ Telegram Stars\n\n"
        "¿Qué quieres hacer?",
        reply_markup=teclado_principal()
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "❓ <b>¿Cómo usar AhorraAI?</b>\n\n"
        "🔎 <b>Buscar producto</b> → compara precios entre supermercados\n"
        "📊 <b>Recomendaciones</b> → mejores ofertas por categoría\n"
        "🛍️ <b>Mi lista</b> → gestiona tu lista de la compra\n"
        "🛒 <b>Hacer pedido</b> → entrega a domicilio, pago con ⭐ Stars\n\n"
        "⭐ <b>¿Qué son las Telegram Stars?</b>\n"
        "La moneda digital de Telegram. Se compran dentro de la app\n"
        "con tarjeta, Apple Pay o Google Pay. Sin salir del chat.\n\n"
        "💡 <i>Desde resultados puedes añadir productos a tu lista con un toque.</i>",
        reply_markup=teclado_principal()
    )

# ================================================================
# BUSCAR PRODUCTO
# ================================================================
async def iniciar_busqueda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "🔎 <b>Buscar producto</b>\n\n"
        "Escribe el nombre (puedes poner varios separados por comas):\n"
        "<i>Ejemplo: leche, pan, yogur</i>",
        reply_markup=teclado_cancelar()
    )
    return BUSCAR_PRODUCTO

async def procesar_busqueda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if texto == "❌ Cancelar":
        await update.message.reply_text("✅ Cancelado.", reply_markup=teclado_principal())
        return ConversationHandler.END
    items = [i.strip() for i in texto.replace('\n', ',').split(',') if i.strip()]
    if len(items) > 1:
        await update.message.reply_html(f"🔍 Analizando <b>{len(items)} productos</b>...")
        for item in items:
            await buscar_y_mostrar(update, item)
    else:
        await buscar_y_mostrar(update, texto)
    await update.message.reply_text("¿Qué más necesitas?", reply_markup=teclado_principal())
    return ConversationHandler.END

# ================================================================
# RECOMENDACIONES
# ================================================================
async def iniciar_recomendacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "📊 <b>Recomendaciones por categoría</b>\n\nElige una o escribe la que quieras:",
        reply_markup=ReplyKeyboardMarkup([
            ["🥛 Lácteos", "🍎 Frutas",   "🥦 Verduras"],
            ["🥩 Carnes",  "🐟 Pescado",  "🍞 Panadería"],
            ["🥤 Bebidas", "🧴 Higiene",  "❌ Cancelar"],
        ], resize_keyboard=True)
    )
    return RECOMENDAR_CATEGORIA

async def procesar_recomendacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if texto == "❌ Cancelar":
        await update.message.reply_text("✅ Cancelado.", reply_markup=teclado_principal())
        return ConversationHandler.END
    categoria = texto.split(' ', 1)[-1] if texto[0] in '🥛🍎🥦🥩🐟🍞🥤🧴' else texto
    await update.message.reply_html(f"🔎 Buscando lo mejor en <b>{categoria}</b>...")
    resultados = buscar_producto(categoria)
    if resultados:
        await mostrar_resultados(update, resultados[:8], categoria)
    else:
        await update.message.reply_html(f"😕 No encontré resultados para <b>{categoria}</b>.")
    await update.message.reply_text("¿Qué más necesitas?", reply_markup=teclado_principal())
    return ConversationHandler.END

# ================================================================
# LISTA DE LA COMPRA
# ================================================================
async def menu_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    n = len(listas_compra[user_id])
    await update.message.reply_html(
        f"🛍️ <b>Mi lista de la compra</b>\n"
        f"Tienes <b>{n} producto{'s' if n != 1 else ''}</b> en tu lista.",
        reply_markup=teclado_lista()
    )
    return LISTA_COMPRA

async def procesar_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto   = update.message.text.strip()
    user_id = update.effective_user.id
    if texto == "📋 Ver lista":
        await _mostrar_lista(update, user_id)
    elif texto == "🗑️ Limpiar lista":
        listas_compra[user_id].clear()
        await update.message.reply_html("🗑️ Lista limpiada.")
    elif texto == "➕ Añadir productos":
        await update.message.reply_html("Escribe los productos <i>(separa con comas)</i>:")
    elif texto == "❌ Volver al menú":
        await update.message.reply_text("✅ Volviendo al menú.", reply_markup=teclado_principal())
        return ConversationHandler.END
    else:
        await _añadir_a_lista(update, user_id, texto)
    return LISTA_COMPRA

async def _añadir_a_lista(update: Update, user_id: int, texto: str):
    items    = [i.strip() for i in texto.replace('\n', ',').split(',') if i.strip()]
    añadidos = []
    for item in items:
        res    = buscar_producto(item)
        nombre = res[0].get('Producto', item.capitalize()) if res else item.capitalize()
        listas_compra[user_id].append(nombre)
        añadidos.append(nombre)
    await update.message.reply_html(
        "Añadido a tu lista:\n" + '\n'.join(f"  ✅ {x}" for x in añadidos) +
        f"\n\nTotal: <b>{len(listas_compra[user_id])} productos</b>"
    )

async def _mostrar_lista(update: Update, user_id: int):
    items = listas_compra[user_id]
    if not items:
        await update.message.reply_html(
            "Tu lista está vacía 🛒\n\n"
            "Añade productos con <b>➕ Añadir productos</b> o desde búsqueda."
        )
        return
    stars = calcular_stars(items)
    euros = stars_a_euros(stars)
    texto = (
        "🛍️ <b>Tu lista de la compra:</b>\n\n" +
        '\n'.join(f"{i}. {item}" for i, item in enumerate(items, 1)) +
        f"\n\n<i>Coste estimado del pedido: <b>⭐ {stars} Stars</b> (≈ {euros}€ incluye envío)</i>"
    )
    await update.message.reply_html(texto, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🚚 Hacer pedido con esta lista", callback_data="iniciar_pedido")],
        [InlineKeyboardButton("🗑️ Limpiar lista", callback_data="limpiar_lista")],
    ]))

# ================================================================
# CALLBACK QUERY HANDLER
# ================================================================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data    = query.data

    if data.startswith("add|"):
        producto = data[4:]
        listas_compra[user_id].append(producto)
        n = len(listas_compra[user_id])
        await query.answer(f"'{producto[:20]}' añadido ({n} en lista)", show_alert=False)
        try:
            txt = query.message.text or query.message.caption or ""
            await query.edit_message_text(
                txt + f"\n\n\u2705 <b>'{producto[:30]}'</b> añadido a tu lista.",
                parse_mode='HTML', reply_markup=query.message.reply_markup
            )
        except Exception:
            pass
        return

    elif data == "ver_lista":
        items = listas_compra[user_id]
        if not items:
            await query.message.reply_html("Tu lista está vacía \U0001f6d2")
        else:
            await query.message.reply_html(
                "\U0001f6cd\ufe0f <b>Tu lista actual:</b>\n\n" +
                '\n'.join(f"{i}. {item}" for i, item in enumerate(items, 1))
            )
        return

    elif data == "limpiar_lista":
        listas_compra[user_id].clear()
        await query.answer("\U0001f5d1\ufe0f Lista limpiada", show_alert=True)
        await query.edit_message_text("\U0001f5d1\ufe0f Lista limpiada.", parse_mode='HTML')
        return

    elif data == "iniciar_pedido":
        items = listas_compra[user_id]
        if not items:
            await query.message.reply_html("\u26a0\ufe0f Tu lista está vacía.")
            return ConversationHandler.END
        pedidos_en_curso[user_id] = {'productos': list(items)}
        lineas = '\n'.join(f"  \u2022 {p}" for p in items)
        await query.message.reply_html(
            f"\U0001f69a <b>Nuevo pedido a domicilio</b>\n\nProductos:\n{lineas}\n\n"
            f"<b>Paso 1/5 — ¿Cuál es tu nombre completo?</b>",
            reply_markup=teclado_cancelar()
        )
        return PEDIDO_NOMBRE

    elif data == "pedido_pagar_stars":
        await _enviar_invoice_stars(query, user_id)
        return PEDIDO_CONFIRMAR

    elif data == "pedido_corregir":
        datos = pedidos_en_curso.get(user_id, {})
        nombre    = datos.get('nombre', '\u2014')
        telefono  = datos.get('telefono', '\u2014')
        direccion = datos.get('direccion', '\u2014')
        cp        = datos.get('cp', '\u2014')
        ciudad    = datos.get('ciudad', '\u2014')
        n_prods   = len(datos.get('productos', []))
        await query.message.reply_html(
            f"\u270f\ufe0f <b>¿Qué quieres corregir?</b>\n\n"
            f"\U0001f464 Nombre: {nombre}\n"
            f"\U0001f4f1 Teléfono: {telefono}\n"
            f"\U0001f3e0 Dirección: {direccion}\n"
            f"\U0001f4ee CP: {cp}\n"
            f"\U0001f3d9\ufe0f Ciudad: {ciudad}\n"
            f"\U0001f6d2 Productos: {n_prods} en lista\n\n"
            "Pulsa el campo que quieras cambiar:",
            reply_markup=inline_corregir_campos()
        )
        return PEDIDO_CONFIRMAR

    elif data == "pedido_cancelar":
        pedidos_en_curso.pop(user_id, None)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        await query.message.reply_html(
            "\u274c <b>Pedido cancelado.</b>\n¿Qué quieres hacer ahora?",
            reply_markup=teclado_principal()
        )
        return ConversationHandler.END

    elif data.startswith("editar|"):
        campo = data.split("|")[1]
        datos = pedidos_en_curso.get(user_id, {})

        if campo == "volver":
            if not datos:
                await query.message.reply_html("\u26a0\ufe0f No hay pedido activo.")
                return ConversationHandler.END
            stars = calcular_stars(datos["productos"])
            euros = stars_a_euros(stars)
            prods = '\n'.join(f"  \u2022 {p}" for p in datos["productos"])
            resumen = (
                "\U0001f4cb <b>Resumen de tu pedido</b>\n"
                "\u2500" * 21 + "\n"
                f"\U0001f464 <b>Nombre:</b> {datos.get('nombre')}\n"
                f"\U0001f4f1 <b>Teléfono:</b> {datos.get('telefono')}\n"
                f"\U0001f3e0 <b>Dirección:</b> {datos.get('direccion')}\n"
                f"\U0001f4ee <b>CP:</b> {datos.get('cp')}\n"
                f"\U0001f3d9\ufe0f <b>Ciudad:</b> {datos.get('ciudad')}\n"
                "\u2500" * 21 + "\n"
                f"\U0001f6d2 <b>Productos:</b>\n{prods}\n"
                "\u2500" * 21 + "\n"
                f"\U0001f4b0 <b>Total: \u2b50 {stars} Stars</b> (≈ {euros}€ con envío)\n\n"
                "Pulsa <b>\u2b50 Pagar con Stars</b> para completar el pedido."
            )
            await query.message.reply_html(resumen, reply_markup=inline_confirmar_pedido())
            return PEDIDO_CONFIRMAR

        elif campo == "lista":
            items = listas_compra[user_id]
            if not items:
                await query.message.reply_html("Tu lista está vacía. Añade productos primero.")
            else:
                lineas = '\n'.join(f"{i}. {item}" for i, item in enumerate(items, 1))
                await query.message.reply_html(
                    f"\U0001f6cd\ufe0f <b>Tu lista actual:</b>\n\n{lineas}\n\n"
                    "Busca más productos y añádelos con el botón \u2795"
                )
            return PEDIDO_CONFIRMAR

        else:
            prompts = {
                "nombre":    ("\U0001f464", "¿Cuál es el nuevo nombre completo?"),
                "telefono":  ("\U0001f4f1", "¿Cuál es el nuevo número de teléfono?"),
                "direccion": ("\U0001f3e0", "¿Cuál es la nueva dirección?\n<i>Ej: Calle Gran Vía 12, 3ºB</i>"),
                "cp":        ("\U0001f4ee", "¿Cuál es el nuevo código postal? (5 dígitos)"),
                "ciudad":    ("\U0001f3d9\ufe0f", "¿Cuál es la ciudad/municipio?"),
            }
            if campo in prompts:
                emoji, texto = prompts[campo]
                context.user_data["editando_campo"] = campo
                await query.message.reply_html(
                    f"{emoji} <b>Editando: {campo}</b>\n\n{texto}",
                    reply_markup=ReplyKeyboardMarkup([["❌ Cancelar"]], resize_keyboard=True)
                )
            return PEDIDO_CONFIRMAR


# ================================================================
# FLUJO DE PEDIDO — recogida de datos de entrega
# ================================================================
async def iniciar_pedido_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    items   = listas_compra[user_id]
    if not items:
        await update.message.reply_html(
            "⚠️ Tu lista está vacía.\nAñade productos primero con <b>🔎 Buscar producto</b>."
        )
        return ConversationHandler.END
    pedidos_en_curso[user_id] = {'productos': list(items)}
    lineas = '\n'.join(f"  • {p}" for p in items)
    await update.message.reply_html(
        f"🚚 <b>Nuevo pedido a domicilio</b>\n\nProductos:\n{lineas}\n\n"
        f"<b>Paso 1/5 — ¿Cuál es tu nombre completo?</b>",
        reply_markup=teclado_cancelar()
    )
    return PEDIDO_NOMBRE

async def pedido_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if texto == "❌ Cancelar":
        pedidos_en_curso.pop(update.effective_user.id, None)
        await update.message.reply_text("❌ Cancelado.", reply_markup=teclado_principal())
        return ConversationHandler.END
    pedidos_en_curso[update.effective_user.id]['nombre'] = texto
    await update.message.reply_html(
        f"✅ Nombre: <b>{texto}</b>\n\n📱 <b>Paso 2/5 — ¿Tu número de teléfono?</b>"
    )
    return PEDIDO_TELEFONO

async def pedido_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if texto == "❌ Cancelar":
        pedidos_en_curso.pop(update.effective_user.id, None)
        await update.message.reply_text("❌ Cancelado.", reply_markup=teclado_principal())
        return ConversationHandler.END
    if len(''.join(c for c in texto if c.isdigit())) < 9:
        await update.message.reply_html("⚠️ Teléfono no válido. Introduce al menos 9 dígitos:")
        return PEDIDO_TELEFONO
    pedidos_en_curso[update.effective_user.id]['telefono'] = texto
    await update.message.reply_html(
        f"✅ Teléfono: <b>{texto}</b>\n\n"
        "🏠 <b>Paso 3/5 — ¿Cuál es tu dirección?</b>\n"
        "<i>Ejemplo: Calle Gran Vía 12, 3ºB</i>"
    )
    return PEDIDO_DIRECCION

async def pedido_direccion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if texto == "❌ Cancelar":
        pedidos_en_curso.pop(update.effective_user.id, None)
        await update.message.reply_text("❌ Cancelado.", reply_markup=teclado_principal())
        return ConversationHandler.END
    pedidos_en_curso[update.effective_user.id]['direccion'] = texto
    await update.message.reply_html(
        f"✅ Dirección: <b>{texto}</b>\n\n📮 <b>Paso 4/5 — ¿Código postal?</b>"
    )
    return PEDIDO_CP

async def pedido_cp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if texto == "❌ Cancelar":
        pedidos_en_curso.pop(update.effective_user.id, None)
        await update.message.reply_text("❌ Cancelado.", reply_markup=teclado_principal())
        return ConversationHandler.END
    if not texto.isdigit() or len(texto) != 5:
        await update.message.reply_html("⚠️ CP no válido. Debe tener exactamente <b>5 dígitos</b>:")
        return PEDIDO_CP
    pedidos_en_curso[update.effective_user.id]['cp'] = texto
    await update.message.reply_html(
        f"✅ CP: <b>{texto}</b>\n\n🏙️ <b>Paso 5/5 — ¿Ciudad/municipio?</b>"
    )
    return PEDIDO_CIUDAD

async def pedido_ciudad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if texto == "❌ Cancelar":
        pedidos_en_curso.pop(update.effective_user.id, None)
        await update.message.reply_text("❌ Cancelado.", reply_markup=teclado_principal())
        return ConversationHandler.END
    user_id = update.effective_user.id
    pedidos_en_curso[user_id]['ciudad'] = texto
    datos = pedidos_en_curso[user_id]
    stars = calcular_stars(datos['productos'])
    euros = stars_a_euros(stars)
    prods = '\n'.join(f"  • {p}" for p in datos['productos'])
    resumen = (
        "📋 <b>Resumen de tu pedido</b>\n"
        "─────────────────────\n"
        f"👤 <b>Nombre:</b> {datos.get('nombre')}\n"
        f"📱 <b>Teléfono:</b> {datos.get('telefono')}\n"
        f"🏠 <b>Dirección:</b> {datos.get('direccion')}\n"
        f"📮 <b>CP:</b> {datos.get('cp')}\n"
        f"🏙️ <b>Ciudad:</b> {datos.get('ciudad')}\n"
        "─────────────────────\n"
        f"🛒 <b>Productos:</b>\n{prods}\n"
        "─────────────────────\n"
        f"💰 <b>Total: ⭐ {stars} Stars</b> (≈ {euros}€ con envío)\n\n"
        "Pulsa <b>⭐ Pagar con Stars</b> para completar el pedido."
    )
    await update.message.reply_html(resumen, reply_markup=inline_confirmar_pedido())
    return PEDIDO_CONFIRMAR

async def pedido_confirmar_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html("👆 Usa los botones de arriba para pagar o cancelar.")
    return PEDIDO_CONFIRMAR


async def pedido_editar_campo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Captura el texto cuando el usuario está editando un campo concreto del pedido.
    Se activa cuando context.user_data["editando_campo"] está definido.
    """
    texto   = update.message.text.strip()
    user_id = update.effective_user.id
    campo   = context.user_data.get("editando_campo")

    if texto == "❌ Cancelar" or not campo:
        context.user_data.pop("editando_campo", None)
        await update.message.reply_html(
            "↩️ Edición cancelada.",
            reply_markup=teclado_cancelar()
        )
        return PEDIDO_CONFIRMAR

    # Validación específica por campo
    if campo == "cp":
        if not texto.isdigit() or len(texto) != 5:
            await update.message.reply_html("⚠️ CP no válido. Debe tener exactamente <b>5 dígitos</b>:")
            return PEDIDO_CONFIRMAR
    elif campo == "telefono":
        if len(''.join(c for c in texto if c.isdigit())) < 9:
            await update.message.reply_html("⚠️ Teléfono no válido. Introduce al menos 9 dígitos:")
            return PEDIDO_CONFIRMAR

    # Guardar el nuevo valor
    pedidos_en_curso[user_id][campo] = texto
    context.user_data.pop("editando_campo", None)

    datos = pedidos_en_curso[user_id]
    await update.message.reply_html(
        f"✅ <b>{campo.capitalize()}</b> actualizado a: <b>{texto}</b>\n\n"
        "¿Qué más quieres corregir?",
        reply_markup=inline_corregir_campos()
    )
    return PEDIDO_CONFIRMAR


# ================================================================
# TELEGRAM STARS — invoice y confirmación
# ================================================================
async def _enviar_invoice_stars(query, user_id: int):
    datos = pedidos_en_curso.get(user_id)
    if not datos:
        await query.message.reply_html("⚠️ No hay pedido activo. Empieza de nuevo.")
        return
    productos = datos['productos']

    # Stars (XTR): LabeledPrice NO acepta emojis en el label
    # title max 32 chars, description max 255 chars, payload max 128 chars
    prices = [
        LabeledPrice("Gastos de envio",           STARS_ENTREGA),
        LabeledPrice(f"{len(productos)} producto(s)", STARS_POR_PRODUCTO * len(productos)),
    ]
    desc_prods = ', '.join(p[:20] for p in productos[:3])
    if len(productos) > 3:
        desc_prods += f" y {len(productos) - 3} mas"
    ciudad = datos.get('ciudad', 'tu ciudad')[:20]
    descripcion = f"Entrega en {ciudad}. Productos: {desc_prods}."[:255]

    await query.message.reply_invoice(
        title="Pedido AhorraAI Vigo",
        description=descripcion,
        payload=f"p_{user_id}_{int(time.time())}",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="XTR",
        prices=prices,
    )

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Telegram llama aquí antes de cobrar. Tienes < 10 segundos para responder.
    Aquí puedes validar stock, horario de reparto, zona de entrega, etc.
    """
    query   = update.pre_checkout_query
    user_id = query.from_user.id
    if user_id not in pedidos_en_curso:
        await query.answer(ok=False, error_message="El pedido ha expirado. Por favor, empieza de nuevo.")
        return
    await query.answer(ok=True)

async def pago_exitoso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Telegram llama aquí cuando el pago se completa correctamente.
    Aquí confirmas, guardas en BD, notificas al repartidor, etc.
    """
    user_id       = update.effective_user.id
    payment       = update.message.successful_payment
    datos         = pedidos_en_curso.pop(user_id, {})
    stars_pagados = payment.total_amount
    charge_id     = payment.telegram_payment_charge_id

    listas_compra[user_id].clear()
    prods = '\n'.join(f"  ✅ {p}" for p in datos.get('productos', []))

    await update.message.reply_html(
        f"🎉 <b>¡Pago recibido y pedido confirmado!</b>\n\n"
        f"⭐ <b>{stars_pagados} Stars</b> cobradas correctamente.\n"
        f"🔖 Referencia: <code>{charge_id}</code>\n\n"
        f"📦 <b>Pedido de {datos.get('nombre', '')}:</b>\n{prods}\n\n"
        f"🚚 Entrega en: {datos.get('direccion', '')}, "
        f"{datos.get('cp', '')} {datos.get('ciudad', '')}\n"
        f"📱 Te avisamos al {datos.get('telefono', '')} cuando salga.\n\n"
        f"⏱️ <i>Tiempo estimado: 2-4 horas</i>\n\n"
        f"¡Gracias por usar AhorraAI! 🛒",
        reply_markup=teclado_principal()
    )
    # LOG para debugging / integración futura con BD
    print(f"[PEDIDO PAGADO] user={user_id} stars={stars_pagados} charge={charge_id} datos={datos}")

# ================================================================
# MOSTRAR RESULTADOS
# ================================================================
async def buscar_y_mostrar(update: Update, query: str):
    resultados = buscar_producto(query)
    if not resultados:
        await update.message.reply_html(
            f"😕 No encontré resultados para <b>{query}</b>.\nPrueba con otro nombre."
        )
        return
    await mostrar_resultados(update, resultados, query)

async def mostrar_resultados(update: Update, resultados: list, query: str):
    mostrar = resultados[:6]
    sep     = '─' * 22
    msg = (
        f"🛒 <b>Resultados: {query}</b>\n{sep}\n" +
        f"\n{sep}\n".join(formatear_resultado(r) for r in mostrar) +
        f"\n{sep}\n<i>Mostrando {len(mostrar)} de {len(resultados)} resultados</i>"
    )
    if len(msg) > 3800:
        msg = msg[:3800] + "\n<i>... (truncado)</i>"
    await update.message.reply_html(msg, reply_markup=inline_añadir_productos(mostrar))

# ================================================================
# CANCELAR GLOBAL
# ================================================================
async def _cancelar_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pedidos_en_curso.pop(update.effective_user.id, None)
    await update.message.reply_text("✅ Operación cancelada.", reply_markup=teclado_principal())
    return ConversationHandler.END

# ================================================================
# MAIN
# ================================================================
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_principal = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex(r'^🔎 Buscar producto$'), iniciar_busqueda),
            MessageHandler(filters.Regex(r'^📊 Recomendaciones$'), iniciar_recomendacion),
            MessageHandler(filters.Regex(r'^🛍️ Mi lista$'),        menu_lista),
            MessageHandler(filters.Regex(r'^🛒 Hacer pedido$'),    iniciar_pedido_comando),
            MessageHandler(filters.Regex(r'^❓ Ayuda$'),            ayuda),
            CallbackQueryHandler(callback_handler),
        ],
        states={
            BUSCAR_PRODUCTO:      [MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_busqueda)],
            RECOMENDAR_CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_recomendacion)],
            LISTA_COMPRA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_lista),
                CallbackQueryHandler(callback_handler),
            ],
            PEDIDO_NOMBRE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, pedido_nombre)],
            PEDIDO_TELEFONO:  [MessageHandler(filters.TEXT & ~filters.COMMAND, pedido_telefono)],
            PEDIDO_DIRECCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedido_direccion)],
            PEDIDO_CP:        [MessageHandler(filters.TEXT & ~filters.COMMAND, pedido_cp)],
            PEDIDO_CIUDAD:    [MessageHandler(filters.TEXT & ~filters.COMMAND, pedido_ciudad)],
            PEDIDO_CONFIRMAR: [
                # Si el usuario está editando un campo, capturamos su texto con pedido_editar_campo
                # Si no, pedido_confirmar_estado le recuerda que use los botones
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    lambda u, c: pedido_editar_campo(u, c)
                    if c.user_data.get("editando_campo")
                    else pedido_confirmar_estado(u, c)
                ),
                CallbackQueryHandler(callback_handler),
            ],
        },
        fallbacks=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex(r'^❌ Cancelar$'), _cancelar_global),
        ],
        allow_reentry=True,
    )

    # Handlers de pago — FUERA del ConversationHandler (globales)
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, pago_exitoso))

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('ayuda', ayuda))
    app.add_handler(conv_principal)

    print("🤖 AhorraAI Bot iniciado — v3.0 con Telegram Stars ⭐")
    app.run_polling()


if __name__ == '__main__':
    main()