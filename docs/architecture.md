# Arquitectura MVP

## Objetivo de esta base

No estamos montando un chatbot de juguete. Estamos montando el primer núcleo operativo de un sistema hiperlocal con dos frentes:

- `AhorraAI`: experiencia ciudadana.
- `Vigo-O-Matic`: experiencia para negocios.

Ambos escriben y leen de la misma base de datos para que cada alta de negocio, oferta o contenido útil pueda alimentar el marketplace central.

## Principios de diseño

- `Primero entender, luego sofisticar`.
- `Una sola app, varios módulos`.
- `Dominio separado de Telegram`.
- `Lógica de negocio separada de la capa IA`.
- `Preparado para crecer, pero sin pagar complejidad por adelantado`.

## Arquitectura actual

```text
Telegram -> FastAPI webhook -> aiogram dispatcher -> services -> PostgreSQL
                                                   -> repositories
                                                   -> future AI router

FastAPI -> API routes -> services -> PostgreSQL
```

## Módulos

- `api`: endpoints HTTP, health checks, listados de ofertas y webhook.
- `bot`: handlers, FSM, teclados y middlewares de Telegram.
- `core`: settings, logging y convenciones comunes.
- `db`: engine async, sesiones y bootstrap de tablas.
- `modules/users`: usuarios de la plataforma.
- `modules/businesses`: negocios locales.
- `modules/offers`: ofertas publicadas al marketplace.
- `services/marketplace.py`: casos de uso del MVP.
- `scrapers`: contrato base para scrapers modulares desplegables en Lambda.

## Por qué esta forma y no otra

### FastAPI + aiogram en la misma app

Te evita separar backend y bot demasiado pronto. Es más fácil para un fundador que aprende construyendo y reduce fricción de despliegue.

### PostgreSQL desde el principio

Tu visión necesita relaciones reales entre usuarios, negocios, ofertas, pedidos y scraping. Empezar con PostgreSQL evita una migración dolorosa cuando el producto ya tenga uso.

### ORM solo para el flujo activo

El bot del MVP solo necesita tres entidades vivas:

- `app_users`
- `businesses`
- `offers`

El resto de tablas están definidas en SQL para no perder la visión de plataforma, pero no metemos todavía lógica Python que no se usa.

## Qué queda preparado

- migración a `WhatsApp Cloud API`
- `Supabase` como Postgres gestionado
- scrapers por fuente
- agentes especializados
- RAG y memoria
- web app y app móvil
- multi-ciudad mediante `city_slug`

## Qué NO metemos todavía

- microservicios
- event bus
- multiagente complejo
- cola de jobs avanzada
- panel admin completo
- orquestación distribuida

Eso no es falta de ambición. Es disciplina de MVP.
