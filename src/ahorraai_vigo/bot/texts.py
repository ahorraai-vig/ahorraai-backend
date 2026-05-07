from __future__ import annotations

START_TEXT = (
    "Bienvenido a <b>AhorraAI</b>.\n\n"
    "Este MVP conecta ciudadanos y negocios locales de Vigo desde un mismo sistema.\n"
    "Elige cómo quieres entrar."
)

CITIZEN_WELCOME_TEXT = (
    "Perfecto. Ya estás en modo ciudadano.\n"
    "Ahora puedes ver ofertas activas publicadas por negocios locales."
)

BUSINESS_WELCOME_TEXT = (
    "Perfecto. Ya estás en modo negocio.\n"
    "Vamos a publicar una oferta sencilla para que aparezca en el marketplace."
)

BUSINESS_NAME_PROMPT = "Escribe el nombre de tu negocio."
BUSINESS_TITLE_PROMPT = "Ahora escribe un título corto para la oferta."
BUSINESS_DESCRIPTION_PROMPT = "Describe la oferta en una o dos frases."
BUSINESS_PRICE_PROMPT = (
    "Indica el precio en euros. Si no quieres mostrar precio, escribe <b>sin precio</b>."
)

INVALID_PRICE_TEXT = "No pude entender ese precio. Ejemplo válido: <b>9.90</b> o <b>sin precio</b>."

BUSINESS_PUBLISH_SUCCESS_TEXT = (
    "Oferta publicada correctamente.\n\n"
    "Negocio: <b>{business_name}</b>\n"
    "Oferta: <b>{offer_title}</b>\n\n"
    "Ya puede verla un ciudadano desde el bot o desde la API."
)

EMPTY_OFFERS_TEXT = (
    "Todavía no hay ofertas publicadas. En cuanto un negocio cree una, la verás aquí."
)
