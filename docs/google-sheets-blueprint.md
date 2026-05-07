# Google Sheets Blueprint

## Pestanas recomendadas

### `businesses`

Catalogo principal de negocios y recursos operables.

### `offers`

Promociones, menus, slots, precios especiales o disponibilidad temporal.

### `intents`

Ejemplos reales de lo que piden los usuarios y como lo clasificas.

### `coverage_gaps`

Huecos de cobertura para saber que te falta antes de crecer.

## Columna minima para `businesses`

```text
business_id,name,category,subcategory,neighborhood,summary,channels,actions,tags,price_level,delivery,booking,priority_service,contact_url,source_name,source_url,last_verified_at
```

## Convenciones utiles

- `channels`: separados por `|`
- `actions`: separados por `|`
- `tags`: separados por `|`
- `delivery`, `booking`, `priority_service`: `true` o `false`
- `business_id`: estable y en minusculas, por ejemplo `padel-navia-club`

## Cuando usar Drive

Solo si necesitas asociar:

- menus PDF
- tarifas
- catalogos
- folletos
- contratos
- fotos

Si todavia no necesitas eso, deja Drive fuera.
