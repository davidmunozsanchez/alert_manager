# Ejemplos de Curl para API de Alerts
# Base URL: http://92.5.79.52

Esta base URL hay que cambiarla por la indicada en la entrega.

## ================================
## HEALTH CHECK
## ================================

# Health check del sistema
curl -X GET http://92.5.79.52/alerts/health

## ================================
## CREAR ALERTAS
## ================================

# Crear una alerta de tormenta
curl -X POST http://92.5.79.52/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Alerta de Tormenta Severa",
    "description": "Se prevé tormenta intensa con rayos y granizo",
    "level": "warning",
    "type": "weather",
    "region": "Madrid",
    "latitude": 40.4168,
    "longitude": -3.7038,
    "source": "api_meteorologia"
  }'

# Crear una alerta de emergencia
curl -X POST http://92.5.79.52/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Emergencia por inundación",
    "description": "Riesgo crítico de inundación en zona baja",
    "level": "emergency",
    "type": "natural_disaster",
    "region": "Levante",
    "latitude": 39.5,
    "longitude": -0.5
  }'

# Crear una alerta de tráfico
curl -X POST http://92.5.79.52/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Accidente en M-40",
    "description": "Accidente múltiple que afecta circulación",
    "level": "critical",
    "type": "traffic",
    "region": "Madrid",
    "latitude": 40.5,
    "longitude": -3.7
  }'

# Crear alerta con fecha de expiración
curl -X POST http://92.5.79.52/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Corte de carretera temporal",
    "description": "Cierre de A-3 por trabajos",
    "level": "warning",
    "type": "infrastructure",
    "region": "Cuenca",
    "expires_at": "2026-01-08T18:00:00Z"
  }'

## ================================
## OBTENER ALERTAS
## ================================

# Obtener todas las alertas
curl -X GET http://92.5.79.52/alerts

# Obtener alertas con paginación
curl -X GET "http://92.5.79.52/alerts?page=1&per_page=10"

# Obtener solo alertas activas
curl -X GET "http://92.5.79.52/alerts?active_only=true"

# Obtener alertas de alto nivel de prioridad
curl -X GET "http://92.5.79.52/alerts?high_priority_only=true"

# Filtrar por nivel de severidad
curl -X GET "http://92.5.79.52/alerts?level=warning"
curl -X GET "http://92.5.79.52/alerts?level=critical"
curl -X GET "http://92.5.79.52/alerts?level=emergency"

# Filtrar por tipo
curl -X GET "http://92.5.79.52/alerts?type=weather"
curl -X GET "http://92.5.79.52/alerts?type=traffic"
curl -X GET "http://92.5.79.52/alerts?type=natural_disaster"

# Filtrar por región
curl -X GET "http://92.5.79.52/alerts?region=Madrid"
curl -X GET "http://92.5.79.52/alerts?region=Levante"

# Filtrar por estado
curl -X GET "http://92.5.79.52/alerts?status=active"
curl -X GET "http://92.5.79.52/alerts?status=resolved"

# Múltiples filtros
curl -X GET "http://92.5.79.52/alerts?level=warning&type=weather&region=Madrid&per_page=5"

## ================================
## OBTENER UNA ALERTA ESPECÍFICA
## ================================

# Obtener alerta por ID (reemplaza 1 con el ID real)
curl -X GET http://92.5.79.52/alerts/1

## ================================
## ACTUALIZAR ALERTAS
## ================================

# Actualizar el estado de una alerta a resuelto
curl -X PUT http://92.5.79.52/alerts/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "resolved"
  }'

# Actualizar descripción y estado
curl -X PUT http://92.5.79.52/alerts/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "resolved",
    "description": "La tormenta ha pasado. Situación normalizada."
  }'

# Cambiar nivel de alerta
curl -X PUT http://92.5.79.52/alerts/1 \
  -H "Content-Type: application/json" \
  -d '{
    "level": "info"
  }'

## ================================
## ESTADÍSTICAS Y RESÚMENES
## ================================

# Obtener estadísticas generales
curl -X GET http://92.5.79.52/alerts/statistics/summary

# Ver estado de expiración de alertas
curl -X GET http://92.5.79.52/alerts/expire/status

# Procesar alertas expiradas
curl -X POST http://92.5.79.52/alerts/expire/check

## ================================
## ENDPOINTS DEBUG
## ================================

# Test simple
curl -X GET http://92.5.79.52/alerts/debug/simple

# Contar alertas en BD
curl -X GET http://92.5.79.52/alerts/debug/count

# Ver tipos de alertas
curl -X GET http://92.5.79.52/alerts/debug/types

# Ver alertas directas de BD
curl -X GET http://92.5.79.52/alerts/debug/raw

## ================================
## MAPA INTERACTIVO
## ================================

# Obtener mapa de alertas meteorológicas (abre en navegador)
curl -X GET http://92.5.79.52/alerts/map/weather-alerts > mapa_alertas.html

# Filtrar mapa por nivel
curl -X GET "http://92.5.79.52/alerts/map/weather-alerts?level=emergency" > mapa_emergencias.html

## ================================
## PARÁMETROS DE QUERY
## ================================

# page: Número de página (default: 1)
# per_page: Elementos por página (default: 20, max: 100)
# level: Filtrar por nivel (info, warning, critical, emergency)
# type: Filtrar por tipo (weather, traffic, natural_disaster, etc)
# region: Filtrar por región (string)
# status: Filtrar por estado (active, resolved, pending, cancelled)
# active_only: Solo alertas activas (true/false)
# high_priority_only: Solo alertas críticas/emergencia (true/false)
# check_expired: Verificar alertas expiradas (true/false)

## ================================
## EJEMPLO: FLUJO COMPLETO
## ================================

# 1. Crear una alerta
# curl -X POST http://localhost:8000/alerts ...

# 2. Obtener la alerta creada (y anotar el ID)
# curl -X GET http://localhost:8000/alerts/[ID]

# 3. Actualizar la alerta
# curl -X PUT http://localhost:8000/alerts/[ID] ...

# 4. Verificar cambios
# curl -X GET http://localhost:8000/alerts/[ID]

# 5. Ver estadísticas
# curl -X GET http://localhost:8000/alerts/statistics/summary
