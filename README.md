# Antel Consumo Internet - Home Assistant Add-on

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Add-on de Home Assistant para monitorear el consumo de datos de internet de Antel (Uruguay).

## Características

- 📊 Monitoreo del consumo de datos de internet
- 📈 Datos usados, totales y restantes en GB
- 📅 **Consumo diario** (se resetea automáticamente a medianoche)
- 📉 Porcentaje de consumo
- 📝 Nombre del plan y período de facturación
- 🔄 Actualización automática configurable

## Requisitos

- Home Assistant OS o Supervised
- Cuenta de Mi Antel (https://aplicaciones.antel.com.uy/miAntel)

## Instalación

### Como Add-on (Recomendado)

1. Ve a **Settings** → **Add-ons** → **Add-on Store**
2. Menú (⋮) → **Repositories**
3. Agrega: `https://github.com/matiasca89/hacs-antel`
4. Busca **"Antel Consumo"** e instálalo
5. Configura el Add-on (ver sección Configuración)
6. Inicia el Add-on

### Instalación Manual (Custom Component)

> ⚠️ **Nota:** La instalación como Custom Component requiere Python 3.12 o anterior. Home Assistant 2024.2+ usa Python 3.13 que no es compatible con Playwright. Se recomienda usar el **Add-on**.

## Configuración

En la pestaña **Configuration** del Add-on:

```yaml
username: "tu_cedula"
password: "tu_contraseña"
scan_interval: 60
service_id: "ZU3367"
renewal_day: 25
timezone: "America/Montevideo"
```

| Opción | Descripción | Default |
|--------|-------------|---------|
| `username` | Cédula de identidad (usuario Mi Antel) | (requerido) |
| `password` | Contraseña de Mi Antel | (requerido) |
| `scan_interval` | Intervalo de actualización en minutos | 60 |
| `service_id` | ID del servicio a monitorear (ej: "ZU3367"). Dejá vacío para buscar automáticamente "Fibra" | "" |
| `renewal_day` | Día del mes en que renueva el saldo de datos (1-31) | 1 |
| `timezone` | Zona horaria para cálculos de fecha (ej: America/Montevideo) | America/Montevideo |

## Sensores

> Nota: estos sensores **no tienen unique_id** porque se crean vía REST (Add-on). Para entidades editables en la UI, hay que usar una integración nativa o crear sensores Template/MQTT con unique_id.

El Add-on crea los siguientes sensores automáticamente:

| Sensor | Descripción | Unidad |
|--------|-------------|--------|
| `sensor.antel_datos_usados` | Datos consumidos en el período | GB |
| `sensor.antel_datos_totales` | Total de datos del plan | GB |
| `sensor.antel_datos_restantes` | Datos disponibles (incluye recargas) | GB |
| `sensor.antel_saldo_recargas` | Saldo de recargas disponible (si no hay, muestra 0) | GB |
| `sensor.antel_recargas_vence` | Vencimiento del saldo de recargas | - |
| `sensor.antel_porcentaje_usado` | Porcentaje consumido | % |
| `sensor.antel_consumo_hoy` | **Consumo del día actual** (se resetea a medianoche) | GB |
| `sensor.antel_fecha_renovacion` | Fecha de renovación del saldo (calculada) | - |
| `sensor.antel_dias_hasta_renovacion` | Días restantes hasta la renovación | días |
| `sensor.antel_dias_pasados_del_contrato` | Días pasados desde la última renovación | días |
| `sensor.antel_promedio_uso_diario` | Promedio de uso diario (GB usados / días pasados) | GB/día |
| `sensor.antel_promedio_restante_diario` | Promedio disponible diario (GB restantes / días hasta renovación) | GB/día |
| `sensor.antel_plan` | Nombre del plan contratado | - |
| `sensor.antel_periodo_facturacion` | Período de facturación actual | - |

### Sensor de Consumo Diario

El sensor `sensor.antel_consumo_hoy` trackea automáticamente cuántos GB consumiste hoy:

- Se resetea a **0** a medianoche
- Calcula la diferencia entre el consumo actual y el valor al inicio del día
- Útil para gráficos y alertas de consumo diario

## Ejemplos de Automatización

### Alerta de consumo alto

```yaml
automation:
  - alias: "Alerta de consumo alto"
    trigger:
      - platform: numeric_state
        entity_id: sensor.antel_porcentaje_usado
        above: 80
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ Alerta de Consumo Antel"
          message: "Has consumido más del 80% de tus datos de internet"
```

### Alerta de consumo diario excesivo

```yaml
automation:
  - alias: "Alerta consumo diario alto"
    trigger:
      - platform: numeric_state
        entity_id: sensor.antel_consumo_hoy
        above: 10
    action:
      - service: notify.mobile_app
        data:
          title: "📊 Consumo Alto Hoy"
          message: "Llevas más de 10 GB consumidos hoy"
```

### Dashboard Card

```yaml
type: entities
title: Consumo Antel
entities:
  - entity: sensor.antel_datos_usados
    name: Usados
  - entity: sensor.antel_datos_restantes
    name: Restantes
  - entity: sensor.antel_consumo_hoy
    name: Hoy
  - entity: sensor.antel_porcentaje_usado
    name: Porcentaje
```

## Utility Meter (Opcional)

Si querés trackear consumo semanal o mensual además del diario, podés crear un Utility Meter en `configuration.yaml`:

```yaml
utility_meter:
  antel_consumo_semanal:
    source: sensor.antel_datos_usados
    cycle: weekly
  antel_consumo_mensual:
    source: sensor.antel_datos_usados
    cycle: monthly
```

## Solución de Problemas

### El Add-on no inicia

1. Verificá los logs del Add-on en la pestaña **Log**
2. Asegurate de que las credenciales sean correctas
3. El primer inicio puede tardar unos minutos mientras descarga dependencias

### Los sensores no aparecen

- Los sensores se crean automáticamente después del primer scrape exitoso
- Revisá **Developer Tools** → **States** y buscá "antel"
- El scrape inicial puede tardar 2-3 minutos

### Error de login

- Verificá que podés acceder a https://aplicaciones.antel.com.uy/miAntel con tus credenciales
- Si tenés múltiples servicios, especificá el `service_id` correcto

### El consumo diario no se resetea

- El reset ocurre cuando cambia el día (medianoche hora del servidor)
- El Add-on guarda el baseline en `/data/daily_tracking.json`

## Logs

Para ver logs detallados, revisá la pestaña **Log** del Add-on en Home Assistant.

## Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request en GitHub.

## Licencia

MIT License
