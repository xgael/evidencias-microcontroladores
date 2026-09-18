# Proyecto guiado 1 — Blink: parpadeo del LED integrado y un LED externo
from machine import Pin
import time

led_ext = Pin(15, Pin.OUT)
led_int = Pin("LED", Pin.OUT)

while True:
    led_ext.toggle()
    led_int.toggle()
    print("LED:", "ON " if led_ext.value() else "OFF")
    time.sleep(0.5)
