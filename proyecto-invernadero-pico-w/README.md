# Monitoreo Ambiental IoT para Invernadero — Raspberry Pi Pico W

Sistema de monitoreo y alertas en tiempo real para un invernadero, sobre **Raspberry Pi
Pico W** con **BME280** (temperatura, humedad y presión) y **LEDs R/G/B** de alerta,
programado en **MicroPython** (Thonny). Base elegida: **versión con servidor web**.

## Estructura
```
codigo/      main.py (firmware MicroPython) · diagram.json (circuito Wokwi)
diagramas/   diagrama_flujo.png · diagrama_bloques.png · mockup_interfaz.png
video/       Invernadero_PicoW_Demo.mp4 (≤ 1 min)
```

## Rangos definidos (invernadero de hortalizas)
| Variable | Aceptable 🟢 | Sospechoso 🟡 | Alerta 🔴 |
|---|---|---|---|
| Temperatura | 18–30 °C | 15–18 / 30–35 °C | <15 / >35 °C |
| Humedad | 40–70 % | 30–40 / 70–85 % | <30 / >85 % |
| Presión | 1000–1025 hPa | 980–1000 / 1025–1040 hPa | <980 / >1040 hPa |

El **nivel global = el peor de los tres** → LED: verde (GP13) · amarillo (GP13+GP14) ·
rojo (GP14). El azul (GP15) parpadea durante la conexión WiFi.

## Servidor web (puerto 80)
- `GET /` → dashboard con las 3 variables, badge por variable y semáforo virtual.
- `GET /data` → JSON `{temp, hum, pres, nivel, niveles}` (el navegador lo consulta cada 2 s).

## Conexiones
| Pin Pico W | Componente |
|---|---|
| GP0 / GP1 | BME280 SDA / SCL (I2C0 @ 400 kHz) |
| GP13 · GP14 · GP15 | LED verde · rojo · azul (220 Ω c/u) |
| 3V3 / GND | Alimentación del sensor |

## Nota de simulación (transparencia)
Wokwi no ofrece BME280 para Pico W + MicroPython, así que en la simulación el firmware
**autodetecta por I2C** y usa **BMP180** (temp + presión, 0x77) + **DHT22** (humedad,
GP16). En hardware real con BME280 (0x76) usa el driver BME280 incluido en `main.py`
— mismo pipeline de rangos, LEDs y servidor en ambos casos.

## Ejecutar en Wokwi
1. <https://wokwi.com/projects/new/micropython-pi-pico-w>
2. Pegar `codigo/main.py` y `codigo/diagram.json` en sus pestañas.
3. ▶ Iniciar; clic al BMP180 para mover la temperatura y ver el semáforo cambiar.
