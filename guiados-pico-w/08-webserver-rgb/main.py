# Proyecto guiado 8 — Servidor web para controlar un LED RGB
import network, socket, time
from machine import Pin

led_r = Pin(11, Pin.OUT); led_g = Pin(12, Pin.OUT); led_b = Pin(13, Pin.OUT)

def color(r, g, b, nombre):
    led_r.value(r); led_g.value(g); led_b.value(b)
    print("RGB ->", nombre)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("Wokwi-GUEST", "")
while not wlan.isconnected():
    print("Conectando a WiFi..."); time.sleep(0.5)
print("WiFi conectado:", wlan.ifconfig()[0])

PAGINA = """<!DOCTYPE html><html><head><meta charset='utf-8'><title>RGB</title></head>
<body style='font-family:sans-serif;background:#101820;color:#eee;text-align:center;padding-top:40px'>
<h1>Pico W — Control RGB</h1>
<a href='/rojo'>ROJO</a> &middot; <a href='/verde'>VERDE</a> &middot; <a href='/azul'>AZUL</a> &middot; <a href='/off'>APAGAR</a>
</body></html>"""

srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("0.0.0.0", 80)); srv.listen(2); srv.settimeout(0.3)
print("Servidor web iniciado en el puerto 80.")

# demo local: ciclo de colores mientras no llegan peticiones (visible en la simulacion)
SECUENCIA = [(1,0,0,"ROJO"), (0,1,0,"VERDE"), (0,0,1,"AZUL"), (0,0,0,"APAGADO")]
i = 0; ultima = time.ticks_ms()
while True:
    if time.ticks_diff(time.ticks_ms(), ultima) > 2500:
        color(*SECUENCIA[i % 4]); i += 1
        ultima = time.ticks_ms()
    try:
        cli, _ = srv.accept()
    except OSError:
        continue
    try:
        req = cli.recv(512).decode()
        if "GET /rojo" in req: color(1,0,0,"ROJO (web)")
        elif "GET /verde" in req: color(0,1,0,"VERDE (web)")
        elif "GET /azul" in req: color(0,0,1,"AZUL (web)")
        elif "GET /off" in req: color(0,0,0,"APAGADO (web)")
        cli.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
        cli.sendall(PAGINA)
    except Exception as e:
        print("Error cliente:", e)
    finally:
        cli.close()
