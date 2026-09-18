# Proyecto guiado 5 — Lectura de un potenciometro por ADC
from machine import Pin, ADC
import time

pot = ADC(Pin(26))   # ADC0

while True:
    crudo = pot.read_u16()               # 0..65535
    voltaje = crudo * 3.3 / 65535
    pct = crudo * 100 // 65535
    barra = "#" * (pct // 5)
    print("ADC=%5d  V=%.2f  %3d%% %s" % (crudo, voltaje, pct, barra))
    time.sleep(0.4)
