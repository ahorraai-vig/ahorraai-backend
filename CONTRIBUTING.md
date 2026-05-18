# Contribuir a AhorraAI

Este repositorio esta organizado como un MVP modular para una plataforma hiperlocal en Vigo.

## Flujo de trabajo

- Rama principal: `main`
- Nuevas funcionalidades: `feat/<descripcion>`
- Correcciones: `fix/<descripcion>`
- Infraestructura o mantenimiento: `chore/<descripcion>`

## Entorno local

1. Crea un entorno virtual:

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Instala dependencias:

```bash
pip install -r requirements/dev.txt
```

3. Copia la configuracion:

```bash
copy .env.example .env
```

4. Ajusta las variables segun tu entorno.

## Desarrollo

Con Docker:

```bash
docker compose up --build
```

Sin Docker:

```bash
uvicorn ahorraai_vigo.main:app --reload
```

Pruebas:

```bash
python -m pytest
```

Lint:

```bash
python -m ruff check src tests
```

## Criterios de calidad

- Mantener el codigo simple y legible.
- Evitar complejidad innecesaria hasta que el producto la necesite.
- Mantener separadas las capas de API, bot, servicios, repositorios y acceso a datos.
- Acompanhar con tests cualquier logica nueva que cambie comportamiento.
