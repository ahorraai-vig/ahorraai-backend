from __future__ import annotations

START_TEXT = (
    "Bienvenido a <b>AhorraAI</b>.\n\n"
    "Este MVP conecta ciudadanos y negocios locales de Vigo desde un mismo sistema.\n"
    "Elige como quieres entrar."
)

CITIZEN_WELCOME_TEXT = (
    "Perfecto. Ya estas en modo ciudadano.\n"
    "Ahora puedes buscar en el catalogo, guardar una lista y pedir ofertas activas."
)

BUSINESS_WELCOME_TEXT = (
    "Perfecto. Ya estas en modo negocio.\n"
    "Vamos a publicar una oferta sencilla para que aparezca en el marketplace."
)

BUSINESS_NAME_PROMPT = "Escribe el nombre de tu negocio."
BUSINESS_TITLE_PROMPT = "Ahora escribe un titulo corto para la oferta."
BUSINESS_DESCRIPTION_PROMPT = "Describe la oferta en una o dos frases."
BUSINESS_PRICE_PROMPT = (
    "Indica el precio en euros. Si no quieres mostrar precio, escribe <b>sin precio</b>."
)

INVALID_PRICE_TEXT = "No pude entender ese precio. Ejemplo valido: <b>9.90</b> o <b>sin precio</b>."

BUSINESS_PUBLISH_SUCCESS_TEXT = (
    "Oferta publicada correctamente.\n\n"
    "Negocio: <b>{business_name}</b>\n"
    "Oferta: <b>{offer_title}</b>\n\n"
    "Ya puede verla un ciudadano desde el bot o desde la API."
)

EMPTY_OFFERS_TEXT = (
    "Todavia no hay ofertas publicadas. En cuanto un negocio cree una, la vera aqui."
)

CATALOG_SEARCH_PROMPT = (
    "Escribe lo que buscas. Ejemplos: <b>desayuno</b>, <b>menu</b>, <b>cafe</b>."
)

CATALOG_EMPTY_TEXT = (
    "No encontre resultados con esa busqueda. Prueba con otra palabra o publica mas ofertas."
)

CART_EMPTY_TEXT = "Tu lista esta vacia. Busca una oferta y anadela primero."

ORDER_NAME_PROMPT = "Escribe el nombre de contacto para el pedido."
ORDER_PHONE_PROMPT = "Escribe un telefono de contacto."
ORDER_ADDRESS_PROMPT = "Escribe la direccion de entrega."
ORDER_POSTAL_CODE_PROMPT = "Escribe el codigo postal."
ORDER_CITY_PROMPT = "Escribe la ciudad de entrega."

ORDER_CREATED_TEXT = (
    "Pedido registrado correctamente.\n\n"
    "Referencia: <b>{order_id}</b>\n"
    "Negocio: <b>{business_name}</b>\n"
    "Total: <b>{total_amount}</b>\n\n"
    "La base ya tiene el pedido y sus lineas guardadas."
)
