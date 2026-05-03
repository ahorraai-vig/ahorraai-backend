# AhorraAI — Backend

Bot de WhatsApp para comparación de precios en supermercados de Vigo.

## ¿Qué hace?

- El usuario manda un texto con un producto → el bot responde con precios de supermercados de Vigo
- El usuario manda una foto de una oferta → Gemini extrae los datos automáticamente → se guardan en Google Sheets

## Arquitectura

```
WhatsApp → AWS Lambda → Google Sheets
                ↓
             Gemini API (extracción de datos por visión)
```

## Stack

| Componente | Tecnología |
|---|---|
| Función serverless | AWS Lambda |
| Bot de mensajería | WhatsApp Business API |
| Extracción de datos | Google Gemini 1.5 Flash |
| Base de datos | Google Sheets + Apps Script |
| Lenguaje | Python 3.x |

## Variables de entorno necesarias

| Variable | Descripción |
|---|---|
| WHATSAPP_ACCESS_TOKEN | Token de acceso de Meta |
| WHATSAPP_PHONE_ID | ID del número de WhatsApp Business |
| GEMINI_API_KEY | Clave de la API de Google Gemini |
| APPS_SCRIPT_URL | URL del Apps Script de Google Sheets |

## Estado

- [x] Webhook de WhatsApp funcional
- [x] Búsqueda de productos por texto
- [x] Extracción de datos desde imagen con Gemini
- [x] Guardado automático en Google Sheets
- [ ] Apps Script de búsqueda (en desarrollo)
- [ ] Scraper automático de supermercados