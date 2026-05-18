# Deployment Guide

## Objetivo

Esta base esta preparada para dos escenarios:

- entorno local con `Docker Desktop` y PostgreSQL
- despliegue publico como proyecto de portfolio con una sola app FastAPI

## Local con Docker

1. Crea `.env` a partir de `.env.example`.
2. Levanta la base de datos y la API:

```bash
docker compose up --build
```

3. Comprueba la salud del sistema:

```text
http://localhost:8000/health
```

## Variables recomendadas para publicar

- `APP_ENV=prod`
- `DB_AUTO_CREATE=false`
- `DATABASE_URL=<postgres gestionado>`
- `TELEGRAM_BOT_TOKEN=<token real>`
- `TELEGRAM_WEBHOOK_SECRET=<secreto largo y aleatorio>`
- `OPENAI_API_KEY=<si usas capa IA>`

## Checklist de portfolio

- No subas `.env` ni `credenciales.json`.
- Usa una base de datos gestionada o una instancia PostgreSQL separada de tu maquina.
- Configura un dominio o subdominio dedicado para el webhook.
- Explica en el README que `bot_telegram.py` es un prototipo legacy y que la base activa vive en `src/ahorraai_vigo/`.
- Enseña capturas o una demo corta del flujo: alta de negocio, publicacion de oferta y consulta ciudadana.

## Siguiente paso recomendado

Para publicar una version convincente, el siguiente bloque natural es migrar la logica util de `bot_telegram.py` al backend modular:

1. busqueda de catalogo
2. lista de compra
3. pedidos y pago
