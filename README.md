# AhorraAI

MVP SaaS hiperlocal para Vigo con dos caras sobre una sola base de datos:

- `B2C`: un asistente conversacional para ciudadanos.
- `B2B`: un asistente para negocios locales que publica y sincroniza oferta al marketplace.

La idea no es construir una arquitectura enterprise desde el dia 1. La idea es construir una base que:

- se entienda facil
- permita desplegar rapido
- sea barata de operar
- y no obligue a rehacer todo cuando llegue WhatsApp, web, scraping o RAG

## Que incluye esta iteracion

- `FastAPI` como backend principal
- `aiogram 3` para Telegram
- `PostgreSQL` como base de datos central, compatible con Supabase
- flujo minimo funcional:
  1. un usuario entra al bot
  2. elige rol `ciudadano` o `negocio`
  3. un negocio publica una oferta
  4. la oferta se guarda en base de datos
  5. un ciudadano puede verla

## Estado actual

La base activa y preparada para evolucionar vive en `src/ahorraai_vigo/`.

- `FastAPI` expone API, web y webhook de Telegram
- `aiogram 3` gestiona el bot modular
- `PostgreSQL` centraliza ciudadanos, negocios y ofertas
- `bot_telegram.py` se conserva como prototipo legacy con ideas de producto todavia no migradas

Mas detalle tecnico en `docs/architecture.md`.

## Estructura del repositorio

```text
src/ahorraai_vigo/
  api/              FastAPI routes
  bot/              aiogram handlers, estados y teclados
  core/             configuracion y logging
  db/               engine, sesiones y bootstrap
  modules/          dominios del MVP: users, businesses, offers
  services/         logica de negocio orquestada
  scrapers/         contratos base para scrapers modulares

infra/sql/          esquema SQL inicial para PostgreSQL/Supabase
requirements/       instalacion base y dev
tests/              tests del flujo minimo
.github/workflows/  CI basica
```

## Quickstart local

1. Crea el entorno:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements/dev.txt
```

2. Copia la configuracion:

```bash
copy .env.example .env
```

3. Levanta la app y PostgreSQL con Docker:

```bash
docker compose up --build
```

4. Configura el webhook del bot de Telegram apuntando a:

```text
https://tu-dominio.com/webhooks/telegram
```

5. Comprueba la salud del backend:

```text
http://localhost:8000/health
```

## Probar el bot nuevo en local

Si quieres notar cambios inmediatos en Telegram sin depender de un webhook publico, usa el runner modular por polling:

```bash
python run_bot_polling.py
```

Hazlo con `bot_telegram.py` parado. Si los dos intentan usar el mismo token a la vez, seguiras viendo comportamiento confuso o inestable.

Si quieres tener catalogo demo listo para probar antes de publicar ofertas manualmente:

```bash
docker compose exec api python -m ahorraai_vigo.dev.seed_demo_main
```

## Desarrollo sin Docker

```bash
uvicorn ahorraai_vigo.main:app --reload
python -m pytest
python -m ruff check src tests
```

## Variables de entorno clave

- `DATABASE_URL`: para local o Supabase
- `TELEGRAM_BOT_TOKEN`: token del bot
- `TELEGRAM_WEBHOOK_SECRET`: secreto del webhook
- `OPENAI_API_KEY`: preparado para la capa IA futura
- `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY`: preparados para integracion futura

## Publicacion y portfolio

- Guia de despliegue: `docs/deployment.md`
- Flujo de contribucion: `CONTRIBUTING.md`
- Al publicar, usa `APP_ENV=prod` con token y webhook secret reales
- No subas `.env` ni `credenciales.json`

## Flujo de trabajo recomendado

- rama principal: `main`
- desarrollo diario: ramas tipo `feat/...`, `fix/...`, `chore/...`
- commits cortos y especificos
- PR pequena siempre que puedas

## Proximo paso natural

Despues de este MVP base, lo mas sensato es construir una de estas tres piezas:

1. `catalogo local real` con importacion o scraping de negocios
2. `panel web interno` para gestionar ofertas y negocios
3. `router IA` para clasificar intenciones y enviar a tools concretas
