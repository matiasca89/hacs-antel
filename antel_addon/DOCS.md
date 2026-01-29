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
| `renewal_day` | Día del mes en que renueva el saldo (1-31) |
| `timezone` | Zona horaria (default: America/Montevideo) |

## Sensores Creados

> Nota: estos sensores **no tienen unique_id** porque se crean vía REST (Add-on). Para entidades editables en la UI, usar Template/MQTT con unique_id.

- `sensor.antel_datos_usados` - GB consumidos
- `sensor.antel_datos_totales` - GB totales del plan
- `sensor.antel_datos_restantes` - GB disponibles
- `sensor.antel_porcentaje_usado` - Porcentaje consumido
- `sensor.antel_consumo_hoy` - Consumo del día actual
- `sensor.antel_fecha_renovacion` - Fecha de renovación del saldo
- `sensor.antel_dias_hasta_renovacion` - Días restantes hasta renovar
- `sensor.antel_dias_pasados_del_contrato` - Días pasados desde última renovación
- `sensor.antel_promedio_uso_diario` - Promedio de uso diario (GB usados / días pasados)
- `sensor.antel_promedio_restante_diario` - Promedio disponible diario (GB restantes / días hasta renovación)
- `sensor.antel_plan` - Nombre del plan
- `sensor.antel_periodo_facturacion` - Período actual

## Consumo Diario

El sensor `sensor.antel_consumo_hoy` se resetea automáticamente a medianoche y muestra cuántos GB consumiste hoy.

## Notas

- El primer scrape puede tardar 2-3 minutos
- Los datos se persisten en `/data/` para sobrevivir reinicios
- El Add-on usa Playwright con Chromium headless
