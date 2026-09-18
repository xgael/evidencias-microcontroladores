# Proyecto guiado 4 — Lectura del sensor DHT22 (temperatura y humedad)
from machine import Pin
import dht
import time

sensor = dht.DHT22(Pin(16))

while True:
    try:
        sensor.measure()
        print("Temperatura: %.1f C   Humedad: %.1f %%" % (sensor.temperature(), sensor.humidity()))
    except Exception as e:
        print("Error leyendo DHT22:", e)
    time.sleep(2)
