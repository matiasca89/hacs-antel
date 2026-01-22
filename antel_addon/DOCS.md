# Antel Consumo - Documentación

## Descripción

Este Add-on hace scraping de la página de Mi Antel para obtener el consumo de datos de internet y lo expone como sensores en Home Assistant.

## Configuración

| Opción | Descripción |
|--------|-------------|
| `username` | Tu cédula de identidad (usuario de Mi Antel) |
| `password` | Tu contraseña de Mi Antel |
| `scan_interval` | Intervalo de actualización en minutos (default: 60) |
| `service_id` | ID del servicio a monitorear (ej: "ZU3367"). Dejá vacío para auto-detectar |

## Sensores Creados

- `sensor.antel_datos_usados` - GB consumidos
- `sensor.antel_datos_totales` - GB totales del plan
- `sensor.antel_datos_restantes` - GB disponibles
- `sensor.antel_porcentaje_usado` - Porcentaje consumido
- `sensor.antel_consumo_hoy` - Consumo del día actual
- `sensor.antel_dias_para_renovar` - Días hasta renovación del pack
- `sensor.antel_fin_contrato` - Fecha fin de contrato
- `sensor.antel_plan` - Nombre del plan
- `sensor.antel_periodo_facturacion` - Período actual

## Consumo Diario

El sensor `sensor.antel_consumo_hoy` se resetea automáticamente a medianoche y muestra cuántos GB consumiste hoy.

## Notas

- El primer scrape puede tardar 2-3 minutos
- Los datos se persisten en `/data/` para sobrevivir reinicios
- El Add-on usa Playwright con Chromium headless
