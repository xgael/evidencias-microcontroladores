# Evidencias — Curso de Microcontroladores

Repositorio **público** con las evidencias del curso: proyectos guiados y proyecto final.
Autor: **Xólotl Gael Chávez Zamora**.

## 🎯 Proyecto Final — Estación de Monitoreo Ambiental IoT (ESP32)

Microcontrolador **ESP32** que mide temperatura y luz, gestiona un **semáforo térmico**
con alarma, y expone monitoreo + control por un **servidor web embebido** (puerto 80).

| Recurso | Ubicación |
|---|---|
| 🎬 Video de demostración (2:05) | [`proyecto-final-iot-esp32/video/`](proyecto-final-iot-esp32/video/Proyecto_Final_IoT_ESP32_Demo.mp4) |
| 💻 Código (sketch + circuito Wokwi) | [`proyecto-final-iot-esp32/codigo/`](proyecto-final-iot-esp32/codigo) |
| 📐 Diagramas (flujo, bloques, circuito) | [`proyecto-final-iot-esp32/diagramas/`](proyecto-final-iot-esp32/diagramas) |
| 📄 Reporte de trabajo (PDF) | [`proyecto-final-iot-esp32/reporte/`](proyecto-final-iot-esp32/reporte/Reporte_Proyecto_Final_IoT_ESP32.pdf) |

### Funcionalidad
- **Sensores:** NTC de temperatura (GPIO34) + fotorresistencia LDR (GPIO35), leídos por ADC.
- **Semáforo térmico:** LED verde/amarillo/rojo (GPIO25/26/27) según la temperatura vs. umbral.
- **Alarma:** buzzer (GPIO18) al superar el umbral; se silencia con botón físico (GPIO19) o desde la web.
- **Actuador remoto:** LED azul (GPIO14) controlado únicamente desde el navegador.
- **Servidor web:** rutas `/`, `/data` (JSON), `/led`, `/umbral`, `/silenciar`.

## 🧪 Proyectos guiados
- [`01-blink`](proyectos-guiados/01-blink) — parpadeo de LED.
- [`02-semaforo`](proyectos-guiados/02-semaforo) — semáforo con temporización.
- [`03-luz-nocturna`](proyectos-guiados/03-luz-nocturna) — luz automática con LDR (entrada analógica).

## ▶️ Cómo abrir en Wokwi
Copiar el `sketch.ino` y el `diagram.json` de la carpeta correspondiente en un proyecto
nuevo de ESP32/Arduino en <https://wokwi.com>.
