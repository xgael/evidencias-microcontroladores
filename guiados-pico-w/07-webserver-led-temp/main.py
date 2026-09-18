# Proyecto guiado 7 — Control de LED y monitoreo de temperatura via servidor web
import network, socket, time, json
import dht
from machine import Pin

sensor = dht.DHT22(Pin(16))
led = Pin(15, Pin.OUT)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("Wokwi-GUEST", "")
while not wlan.isconnected():
    print("Conectando a WiFi..."); time.sleep(0.5)
print("WiFi conectado:", wlan.ifconfig()[0])

PAGINA = """<!DOCTYPE html><html><head><meta charset='utf-8'><title>LED + Temp</title></head>
<body style='font-family:sans-serif;background:#101820;color:#eee;text-align:center;padding-top:40px'>
<h1>Pico W — LED y temperatura</h1>
<p>Temperatura: <b>%s C</b> &middot; Humedad: <b>%s %%</b></p>
<p>LED: <b>%s</b></p>
<a href='/led/on'>Encender</a> &middot; <a href='/led/off'>Apagar</a>
</body></html>"""

srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("0.0.0.0", 80)); srv.listen(2); srv.settimeout(0.3)
print("Servidor web iniciado en el puerto 80.")

ultima = 0; t = h = 0
while True:
    if time.ticks_diff(time.ticks_ms(), ultima) > 2000:
        try:
            sensor.measure(); t, h = sensor.temperature(), sensor.humidity()
            print("T=%.1f C  H=%.1f %%  LED=%s" % (t, h, "ON" if led.value() else "OFF"))
        except Exception as e:
            print("Error DHT22:", e)
        ultima = time.ticks_ms()
    try:
        cli, _ = srv.accept()
    except OSError:
        continue
    try:
        req = cli.recv(512).decode()
        if "GET /led/on" in req: led.value(1); print("LED encendido desde la web")
        if "GET /led/off" in req: led.value(0); print("LED apagado desde la web")
        cli.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
        cli.sendall(PAGINA % (t, h, "ON" if led.value() else "OFF"))
    except Exception as e:
        print("Error cliente:", e)
    finally:
        cli.close()
