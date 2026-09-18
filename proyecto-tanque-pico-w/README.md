# Tank Monitoring IoT — Raspberry Pi Pico W

Prototipo IoT (encargo "IoT Masters"): mide **temperatura, humedad** (DHT22) y **nivel de
líquido de un tanque** (HC-SR04), muestra todo en un **servidor web en tiempo real** y
gestiona alertas con LEDs. Programado en **MicroPython** (Thonny).

## Estructura
```
codigo/   main.py (firmware MicroPython) · diagram.json (circuito Wokwi)
video/    Tank_Monitoring_Demo.mp4 (2:02)
```

## Funcionalidad
| Requisito | Implementación |
|---|---|
| Temperatura y humedad | DHT22 en GP16, lectura cada 5 s con manejo de errores |
| Nivel del tanque | HC-SR04 (TRIG GP17 / ECHO GP18), distancia en cm |
| LED RGB por rango de temperatura | 🔵 frío `<18 °C` · 🟢 moderado `18–28` · 🔴 caliente `>28` (GP11/12/13) |
| Alerta tanque casi vacío | LED rojo (GP14) si distancia `< 10 cm` |
| Bomba simulada | LED amarillo (GP15) con botón ON/OFF **desde el servidor web** |
| Servidor web en tiempo real | Puerto 80: dashboard (`/`), `GET /data` JSON, `GET /pump?on=1\|0` |
| Actualización cada 5 s | Bucle de medición + polling AJAX del dashboard |
| Robustez | `try/except` en sensores y clientes; timeout en `accept()` y en el pulso del HC-SR04 |

## Conexiones
| Pin Pico W | Componente |
|---|---|
| GP16 | DHT22 (datos) |
| GP17 / GP18 | HC-SR04 TRIG / ECHO |
| GP11 · GP12 · GP13 | LED RGB (R · G · B, 220 Ω c/u, cátodo común) |
| GP14 | LED rojo "tanque bajo" (220 Ω) |
| GP15 | LED amarillo "bomba" (220 Ω) |
| 3V3 / GND | Alimentación de sensores |

## Ejecutar en Wokwi
1. <https://wokwi.com/projects/new/micropython-pi-pico-w>
2. Pegar `codigo/main.py` y `codigo/diagram.json` en sus pestañas y ▶ iniciar.
3. Clic al DHT22 para mover la temperatura (cambia el RGB) y al HC-SR04 para bajar la
   distancia a menos de 10 cm (enciende la alerta de tanque).

## Nota de simulación (transparencia)
El plan gratuito de Wokwi no permite entrar por el navegador al servidor que corre dentro
de la simulación (gateway privado de paga), así que el segmento del dashboard del video se
grabó contra una instancia local que sirve el MISMO HTML embebido del firmware con la misma
API (`/data`, `/pump`). El firmware real corre completo en la simulación (se ve el serial:
WiFi + "Servidor web iniciado en el puerto 80" + lecturas).
