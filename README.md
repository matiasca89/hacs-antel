# Antel Consumo Internet - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Integración de Home Assistant para monitorear el consumo de datos de internet de Antel (Uruguay).

## Características

- Monitoreo del consumo de datos de internet
- Datos usados, totales y restantes en GB
- Porcentaje de consumo
- Nombre del plan
- Período de facturación
- Actualización automática cada hora

## Requisitos

- Home Assistant 2023.1 o superior
- Cuenta de Mi Antel (https://aplicaciones.antel.com.uy/miAntel)
- Chromium instalado en el sistema (para Playwright)

## Instalación

### HACS (Recomendado)

1. Abre HACS en Home Assistant
2. Ve a "Integraciones"
3. Haz clic en los tres puntos en la esquina superior derecha
4. Selecciona "Repositorios personalizados"
5. Agrega este repositorio: `https://github.com/tu-usuario/hacs_antel_consumo`
6. Categoría: Integración
7. Busca "Antel Consumo" e instálalo
8. Reinicia Home Assistant

### Manual

1. Descarga el contenido de este repositorio
2. Copia la carpeta `custom_components/antel_consumo` a tu carpeta `config/custom_components/`
3. Reinicia Home Assistant

### Instalación de Playwright

La integración usa Playwright para hacer web scraping. Necesitas instalar el navegador Chromium:

```bash
# En el contenedor de Home Assistant o en tu sistema
pip install playwright
playwright install chromium
```

Si usas Home Assistant OS o Docker, puede que necesites instalar dependencias adicionales:

```bash
playwright install-deps chromium
```

## Configuración

1. Ve a Configuración > Dispositivos y Servicios
2. Haz clic en "+ Agregar Integración"
3. Busca "Antel Consumo"
4. Ingresa tus credenciales de Mi Antel

## Sensores

La integración crea los siguientes sensores:

| Sensor | Descripción | Unidad |
|--------|-------------|--------|
| `sensor.antel_internet_datos_usados` | Datos consumidos | GB |
| `sensor.antel_internet_datos_totales` | Total de datos del plan | GB |
| `sensor.antel_internet_datos_restantes` | Datos disponibles | GB |
| `sensor.antel_internet_porcentaje_usado` | Porcentaje consumido | % |
| `sensor.antel_internet_nombre_del_plan` | Nombre del plan contratado | - |
| `sensor.antel_internet_periodo_de_facturacion` | Período actual | - |

## Ejemplo de Automatización

```yaml
automation:
  - alias: "Alerta de consumo alto"
    trigger:
      - platform: numeric_state
        entity_id: sensor.antel_internet_porcentaje_usado
        above: 80
    action:
      - service: notify.mobile_app
        data:
          title: "Alerta de Consumo Antel"
          message: "Has consumido más del 80% de tus datos de internet"
```

## Solución de Problemas

### La integración no puede conectarse

1. Verifica que tus credenciales sean correctas en Mi Antel
2. Asegúrate de que Chromium esté instalado correctamente
3. Revisa los logs de Home Assistant para más detalles

### Los datos no se actualizan

- La integración actualiza los datos cada hora por defecto
- Puedes forzar una actualización desde Herramientas de Desarrollador > Servicios > `homeassistant.update_entity`

### Error de scraping

Si los selectores CSS cambian en la página de Antel, los datos pueden no extraerse correctamente. Por favor, abre un issue en GitHub si esto ocurre.

## Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request en GitHub.

## Licencia

MIT License
