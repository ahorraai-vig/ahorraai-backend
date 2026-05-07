# Mapa de descubrimiento

## Como sacar un mapa completo sin perderte

No empieces por "lista de negocios". Empieza por una matriz de necesidad.

## Paso 1: define ejes

Cruza estas cuatro dimensiones:

- `usuario`: residente, trabajador, turista, estudiante, senior, familia
- `momento`: ahora, hoy, esta semana, recurrente
- `accion`: comprar, reservar, pedir presupuesto, contratar, descubrir, comparar
- `vertical`: comida, restauracion, hogar, legal, seguros, deporte, ocio, movilidad, mascotas, salud

## Paso 2: crea un inventario de verticales

Minimo:

- alimentacion
- restaurantes y desayunos
- reformas y mantenimiento del hogar
- abogados y asesoria
- seguros
- ocio gratis y ocio de pago
- deporte y alquiler o reserva de pistas
- actividades locales de barrio

## Paso 3: para cada vertical, lista microcasos

Ejemplos:

- `alimentacion`: compra diaria, semanal, urgente, oficina, entrega, dieta concreta
- `restauracion`: reserva, grupo, terraza, menu del dia, desayuno rapido
- `hogar`: presupuesto, urgencia, comparativa, visita tecnica
- `deporte`: encontrar pista, encontrar partido, reservar, comparar horarios
- `ocio`: que hacer hoy, gratis, con ninos, cerca de una zona

## Paso 4: documenta los atributos que necesita el catalogo

Cada negocio o recurso debe tener como minimo:

- nombre
- categoria
- subcategoria
- barrio o zona
- resumen
- canales disponibles
- acciones soportadas
- etiquetas
- rango de precio
- si permite reserva
- si acepta pedido
- si ofrece atencion prioritaria
- enlace de contacto

## Paso 5: crea una hoja de huecos

No basta con lo que si tienes. Tienes que medir lo que falta:

- vertical sin negocios
- barrio sin cobertura
- accion sin flujo operativo
- informacion desactualizada
- negocio sin canal digital

## Paso 6: prioriza por densidad de dolor

Prioriza donde coincidan estas tres cosas:

- necesidad frecuente
- friccion alta
- negocio dispuesto a responder rapido

## Fuentes practicas para llenar el mapa

- Google Maps y categorias locales
- directorios empresariales y asociaciones
- webs de negocios individuales
- perfiles de Instagram y Telegram de negocios
- portales municipales y turisticos
- federaciones o clubes deportivos
- marketplaces y portales de reserva
- entrevistas cortas con 10 usuarios y 10 negocios

## Fuentes concretas para Vigo

- Open Data del Concello de Vigo: https://datos.vigo.org/es/
- Catalogo de datasets de Vigo: https://datos-ckan.vigo.org/
- Agenda oficial de Turismo de Vigo: https://turismo.vigo.org/es/agenda
- Area municipal de comercio: https://hoxe.vigo.org/movemonos/comercio.php?lang=es
- Instalaciones deportivas de Vigo: https://deportes.vigo.org/es/instalacions-deportivas
- Reserva de instalaciones deportivas: https://deportes.vigo.org/es/reserva-instalacions

## Salida esperada

Tu mapa final no es un texto. Es un sistema de hojas:

- `businesses`
- `offers`
- `intents`
- `coverage_gaps`
- `neighborhoods`
- `sources`

Usa las plantillas de `data/templates/` para empezar.
