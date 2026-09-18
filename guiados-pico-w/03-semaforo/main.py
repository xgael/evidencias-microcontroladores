# Proyecto guiado 3 — Semaforo con temporizacion
from machine import Pin
import time

rojo = Pin(13, Pin.OUT)
amarillo = Pin(14, Pin.OUT)
verde = Pin(15, Pin.OUT)

def fase(r, a, v, nombre, seg):
    rojo.value(r); amarillo.value(a); verde.value(v)
    print("Semaforo:", nombre)
    time.sleep(seg)

while True:
    fase(0, 0, 1, "VERDE", 4)
    fase(0, 1, 0, "AMARILLO", 1.5)
    fase(1, 0, 0, "ROJO", 4)
