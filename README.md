# AhorraAI

MVP SaaS hiperlocal para Vigo con dos caras sobre una sola base de datos:

- `B2C`: un asistente conversacional para ciudadanos.
- `B2B`: un asistente para negocios locales que publica y sincroniza oferta al marketplace.

La idea no es construir una arquitectura enterprise desde el día 1. La idea es construir una base que:

- se entienda fácil,
- permita desplegar rápido,
- sea barata de operar,
- y no obligue a rehacer todo cuando llegue WhatsApp, web, scraping o RAG.

## Qué incluye esta iteración

- `FastAPI` como backend principal.
- `aiogram 3` para Telegram.
- `PostgreSQL` como base de datos central, compatible con Supabase.
- flujo mínimo funcional:
  1. un usuario entra al bot,
  2. elige rol `ciudadano` o `negocio`,
  3. un negocio publica una oferta,
  4. la oferta se guarda en base de datos,
  5. un ciudadano puede verla.

## Decisiones técnicas del MVP

- `Una sola app Python`: más fácil de entender y desplegar.
- `Una sola base de datos`: ciudadanos y negocios comparten el mismo marketplace.
- `ORM solo para lo que ya usamos`: `users`, `businesses` y `offers`.
- `SQL completo para el futuro`: el esquema inicial ya deja preparadas tablas de `products`, `services`, `orders`, `reservations` y `scraping`.
- `Sin multiagente real todavía`: preparamos la separación entre bot, servicios, scrapers y capa IA, pero no metemos complejidad innecesaria.

Más detalle técnico en [docs/architecture.md](/C:/Users/Oscar/.codex/ahorraai-vigo/docs/architecture.md).

## Estructura del repositorio

```text
src/ahorraai_vigo/
  api/              FastAPI routes
  bot/              aiogram handlers, estados y teclados
  core/             configuración y logging
  db/               engine, sesiones y bootstrap
  modules/          dominios del MVP: users, businesses, offers
  services/         lógica de negocio orquestada
  scrapers/         contratos base para scrapers modulares

infra/sql/          esquema SQL inicial para PostgreSQL/Supabase
requirements/       instalación base y dev
tests/              tests del flujo mínimo
.github/workflows/  CI básica
```

## Quickstart local

1. Crea el entorno:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements/dev.txt
```

2. Copia la configuración:

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

## Desarrollo sin Docker

```bash
uvicorn ahorraai_vigo.main:app --reload
pytest
ruff check src tests
```

## Variables de entorno clave

- `DATABASE_URL`: para local o Supabase.
- `TELEGRAM_BOT_TOKEN`: token del bot.
- `TELEGRAM_WEBHOOK_SECRET`: secreto del webhook.
- `OPENAI_API_KEY`: preparado para la capa IA futura.
- `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY`: preparados para integración futura.

## Flujo de trabajo recomendado

- rama principal: `main`
- desarrollo diario: ramas tipo `feat/...`, `fix/...`, `chore/...`
- commits cortos y específicos
- PR pequeña siempre que puedas

## Próximo paso natural

Después de este MVP base, lo más sensato es construir una de estas tres piezas:

1. `catálogo local real` con importación/scraping de negocios,
2. `panel web interno` para gestionar ofertas y negocios,
3. `router IA` para clasificar intenciones y enviar a tools concretas.
