import json
import urllib3
import base64
from datetime import datetime

# --- CONFIGURACIÓN ---
# Las credenciales se cargan desde variables de entorno de AWS Lambda
# Nunca escribas credenciales directamente en el código
import os

ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN')
PHONE_ID = os.environ.get('WHATSAPP_PHONE_ID')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
APPS_SCRIPT_URL = os.environ.get('APPS_SCRIPT_URL')
# ---------------------

def lambda_handler(event, context):
    # 1. Validación Webhook
    query_params = event.get('queryStringParameters', {})
    if query_params and query_params.get('hub.mode') == 'subscribe':
        return {'statusCode': 200, 'body': query_params.get('hub.challenge')}

    http = urllib3.PoolManager()
    body = json.loads(event.get('body', '{}'))

    try:
        value = body['entry'][0]['changes'][0]['value']
        if 'messages' in value:
            message = value['messages'][0]
            user_phone = message['from']

            # CASO A: EL USUARIO MANDA TEXTO (BUSCAR)
            if 'text' in message:
                user_text = message['text']['body'].lower()
                gs_res = http.request('GET', f"{APPS_SCRIPT_URL}?action=search&producto={user_text}", retries=urllib3.util.retry.Retry(redirect=5))
                datos = json.loads(gs_res.data.decode('utf-8'))

                if datos:
                    res_txt = f"🔎 Precios en Vigo para '{user_text}':\n"
                    for i in datos:
                        res_txt += f"\n📍 {i['supermercado']}: {i['producto']} -> {i['precio']}€"
                else:
                    res_txt = f"No tengo precios para '{user_text}' todavía. 🛒"

                enviar_whatsapp(user_phone, res_txt, PHONE_ID, ACCESS_TOKEN)

            # CASO B: EL USUARIO MANDA FOTO (EXTRAER CON GEMINI)
            elif 'image' in message:
                enviar_whatsapp(user_phone, "📸 Procesando captura con Gemini...", PHONE_ID, ACCESS_TOKEN)
                image_id = message['image']['id']

                # 1. Obtener URL de la imagen en Meta
                meta_img_res = http.request('GET', f"https://graph.facebook.com/v21.0/{image_id}", headers={"Authorization": f"Bearer {ACCESS_TOKEN}"})
                img_url = json.loads(meta_img_res.data.decode('utf-8'))['url']

                # 2. Descargar la imagen
                img_data = http.request('GET', img_url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}).data
                img_b64 = base64.b64encode(img_data).decode('utf-8')

                # 3. Llamar a Gemini
                fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
                instruccion = f"La fecha es {fecha_hoy}. Analiza la captura de pantalla del supermercado. Devuelve SOLO: Fecha|Supermercado|Categoría|Producto|Precio Total|Precio Unidad. Usa | como separador."

                gemini_payload = {
                    "contents": [{"parts": [{"text": instruccion}, {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}]}]
                }

                gem_res = http.request('POST', gemini_url, body=json.dumps(gemini_payload), headers={'Content-Type': 'application/json'})
                gem_text = json.loads(gem_res.data.decode('utf-8'))['candidates'][0]['content']['parts'][0]['text'].strip()

                # 4. Guardar en Google Sheets
                lista_datos = gem_text.split('|')
                if len(lista_datos) >= 5:
                    http.request('POST', APPS_SCRIPT_URL, body=json.dumps(lista_datos))
                    enviar_whatsapp(user_phone, f"✅ Guardado: {lista_datos[3]} ({lista_datos[4]}€)", PHONE_ID, ACCESS_TOKEN)
                else:
                    enviar_whatsapp(user_phone, f"⚠️ Error en formato: {gem_text}", PHONE_ID, ACCESS_TOKEN)

    except Exception as e:
        print(f"Error general: {e}")

    return {'statusCode': 200, 'body': 'OK'}


def enviar_whatsapp(to, text, phone_id, token):
    url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    urllib3.PoolManager().request('POST', url, body=json.dumps(payload), headers=headers)