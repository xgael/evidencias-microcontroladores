# Proyecto Final — Estación de Monitoreo Ambiental IoT (ESP32)

Estación IoT sobre **ESP32 DevKit-C v4** (simulada en **Wokwi**) que integra sensores,
un semáforo térmico con alarma y un **servidor web embebido** para monitoreo y control remotos.

## Estructura
```
codigo/      sketch.ino  (firmware)  ·  diagram.json  (circuito Wokwi)
diagramas/   diagrama_flujo.png  ·  diagrama_bloques.png
             diagrama_circuito_anotado.png  ·  circuito_wokwi.png
video/       Proyecto_Final_IoT_ESP32_Demo.mp4  (2:05)
reporte/     Reporte_Proyecto_Final_IoT_ESP32.pdf
```

## Conexiones
| Pin | Componente | Tipo |
|---|---|---|
| GPIO34 | Sensor NTC (temperatura) | Entrada analógica (ADC) |
| GPIO35 | Fotorresistencia LDR (luz) | Entrada analógica (ADC) |
| GPIO19 | Botón "Silenciar" | Entrada digital (pull-up) |
| GPIO25 / 26 / 27 | LED verde / amarillo / rojo | Salidas (semáforo, 220 Ω) |
| GPIO14 | LED azul (actuador remoto) | Salida (220 Ω) |
| GPIO18 | Buzzer | Salida (tono 1 kHz) |

## Servidor web (puerto 80)
| Ruta | Función |
|---|---|
| `GET /` | Dashboard HTML |
| `GET /data` | Telemetría JSON (polling cada 1 s) |
| `GET /led?state=on\|off` | Enciende/apaga el LED remoto |
| `GET /umbral?c=NN` | Cambia el umbral de alarma |
| `GET /silenciar` | Silencia la alarma activa |

## Ejecutar en Wokwi
1. Abrir <https://wokwi.com/projects/new/esp32>.
2. Pegar `codigo/sketch.ino` en `sketch.ino` y `codigo/diagram.json` en `diagram.json`.
3. Iniciar la simulación (el monitor serial muestra la conexión WiFi y el arranque del servidor).
