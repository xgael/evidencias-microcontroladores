# Proyecto guiado 6 — Control de un servo SG90 con un potenciometro
from machine import Pin, ADC, PWM
import time

pot = ADC(Pin(26))
servo = PWM(Pin(15))
servo.freq(50)

def angulo_a_ns(ang):
    # SG90: 0 grados = 500 us, 180 grados = 2400 us
    return int((500 + (2400 - 500) * ang / 180) * 1000)

while True:
    ang = pot.read_u16() * 180 // 65535
    servo.duty_ns(angulo_a_ns(ang))
    print("Potenciometro -> servo: %3d grados" % ang)
    time.sleep(0.15)
