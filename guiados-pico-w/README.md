# Proyectos guiados — Raspberry Pi Pico W (MicroPython)

Evidencias de los 8 proyectos guiados del módulo. Cada carpeta trae `main.py`,
`diagram.json` (circuito Wokwi) y `video.mp4` (≤30 s) mostrando el circuito y el
programa funcionando, con el letrero de identificación requerido.

| # | Proyecto | Qué se ve en el video |
|---|---|---|
| 01 | Blink | LED externo + LED integrado parpadeando; serial ON/OFF |
| 02 | LED con push button | Al presionar el botón enciende el LED; serial "PRESIONADO" |
| 03 | Semáforo | Ciclo verde → amarillo → rojo con temporización |
| 04 | Lectura del DHT22 | Temperatura/humedad por serial; cambia al mover el sensor |
| 05 | Potenciómetro (ADC) | ADC 0→100%→49% con voltaje y barra de progreso |
| 06 | Servo SG90 + potenciómetro | El ángulo del servo sigue al potenciómetro (0–180°) |
| 07 | Web server: LED + temperatura | Servidor en :80 y lecturas DHT22 en vivo |
| 08 | Web server: LED RGB | Servidor en :80 y RGB ciclando rojo/verde/azul |

## Ejecutar cualquiera en Wokwi
<https://wokwi.com/projects/new/micropython-pi-pico-w> → pegar `main.py` y
`diagram.json` de la carpeta → ▶ iniciar.
