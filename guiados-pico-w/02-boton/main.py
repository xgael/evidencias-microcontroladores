# Proyecto guiado 2 — Control de un LED externo con push button
from machine import Pin
import time

led = Pin(15, Pin.OUT)
boton = Pin(14, Pin.IN, Pin.PULL_DOWN)
print("Esperando boton... (presiona para encender el LED)")

while True:
    if boton.value():
        led.value(1)
        print("Boton PRESIONADO -> LED ON")
    else:
        led.value(0)
    time.sleep(0.05)
