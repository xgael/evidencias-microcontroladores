# ============================================================
#  Tank Monitoring IoT — Raspberry Pi Pico W (IoT Masters)
#  MicroPython · DHT22 (temp/humedad) + HC-SR04 (nivel de tanque)
# ============================================================
#  Funcionalidad:
#   1. Lee DHT22 (temperatura, humedad) y HC-SR04 (distancia al líquido).
#   2. LED RGB según rango de temperatura:
#        AZUL  = frío     (t < 18 °C)
#        VERDE = moderado (18–28 °C)
#        ROJO  = caliente (t > 28 °C)
#   3. LED rojo de tanque: encendido si distancia < 10 cm (casi vacío).
#      (El sensor mira al líquido desde el fondo del tanque simulado:
#       distancia corta = poco líquido.)
#   4. LED de BOMBA controlado desde el servidor web (botón ON/OFF).
#   5. Servidor web puerto 80: dashboard en vivo (auto-actualiza cada 5 s)
#      + /data en JSON + /pump para encender/apagar la bomba.
# ============================================================

import network
import socket
import time
import json
import dht
from machine import Pin, time_pulse_us

# ---------------- Hardware ----------------
sensor_dht = dht.DHT22(Pin(16))
TRIG = Pin(17, Pin.OUT)
ECHO = Pin(18, Pin.IN)

led_r = Pin(11, Pin.OUT)   # RGB rojo
led_g = Pin(12, Pin.OUT)   # RGB verde
led_b = Pin(13, Pin.OUT)   # RGB azul
led_tanque = Pin(14, Pin.OUT)   # rojo: tanque casi vacío
led_bomba  = Pin(15, Pin.OUT)   # bomba simulada (control web)

# ---------------- Sensores (con manejo de errores) ----------------
def leer_dht():
    try:
        sensor_dht.measure()
        return sensor_dht.temperature(), sensor_dht.humidity()
    except Exception as e:
        print("Error DHT22:", e)
        return None, None

def leer_distancia():
    try:
        TRIG.value(0); time.sleep_us(2)
        TRIG.value(1); time.sleep_us(10)
        TRIG.value(0)
        t = time_pulse_us(ECHO, 1, 30000)   # timeout 30 ms
        if t < 0:
            return None
        return round(t * 0.0343 / 2, 1)     # cm
    except Exception as e:
        print("Error HC-SR04:", e)
        return None

# ---------------- Lógica de rangos ----------------
def rango_temp(t):
    if t is None: return "sin dato"
    if t < 18: return "frio"
    if t <= 28: return "moderado"
    return "caliente"

def poner_rgb(rango):
    led_r.value(1 if rango == "caliente" else 0)
    led_g.value(1 if rango == "moderado" else 0)
    led_b.value(1 if rango == "frio" else 0)

# ---------------- WiFi ----------------
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("Wokwi-GUEST", "")
print("Conectando a WiFi", end="")
while not wlan.isconnected():
    print(".", end=""); time.sleep(0.4)
print("\nWiFi conectado. Dashboard: http://%s/" % wlan.ifconfig()[0])

# ---------------- Estado ----------------
estado = {"temp": None, "hum": None, "dist": None,
          "rango": "sin dato", "tanque_bajo": False, "bomba": False}

def medir():
    t, h = leer_dht()
    d = leer_distancia()
    estado["temp"], estado["hum"], estado["dist"] = t, h, d
    estado["rango"] = rango_temp(t)
    estado["tanque_bajo"] = (d is not None and d < 10)
    poner_rgb(estado["rango"])
    led_tanque.value(1 if estado["tanque_bajo"] else 0)
    led_bomba.value(1 if estado["bomba"] else 0)
    print("T=%s C  H=%s %%  D=%s cm  [%s]%s%s" % (
        estado["temp"], estado["hum"], estado["dist"], estado["rango"].upper(),
        "  TANQUE BAJO!" if estado["tanque_bajo"] else "",
        "  BOMBA ON" if estado["bomba"] else ""))

# ---------------- Dashboard (HTML embebido) ----------------
PAGINA = """<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tank Monitoring IoT</title><style>
body{background:#0b1420;color:#e8f1fb;font-family:system-ui,sans-serif;margin:0;padding:22px}
h1{font-size:21px;margin:0}.sub{color:#7fa3c9;font-size:13px;margin:4px 0 18px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;max-width:900px}
.card{background:#122236;border:1px solid#23415f;border-radius:14px;padding:16px}
.lbl{color:#7fa3c9;font-size:11px;text-transform:uppercase;letter-spacing:1.2px}
.val{font-size:34px;font-weight:700;margin:8px 0 2px}
.badge{display:inline-block;font-size:11px;font-weight:800;padding:3px 10px;border-radius:99px;margin-top:6px}
.b-frio{background:#0f2f4a;color:#5ab8ff}.b-moderado{background:#0f3a24;color:#4ade80}
.b-caliente{background:#3a1212;color:#f87171}.b-off{background:#26324a;color:#93a7c4}
.alerta{color:#f87171;font-weight:800}
button{background:#1c72d3;color:#fff;border:0;border-radius:10px;padding:12px 18px;
font-size:14px;font-weight:700;cursor:pointer;margin-top:10px}
button.on{background:#16a34a}
.tanque{height:14px;background:#0b1420;border:1px solid #23415f;border-radius:99px;overflow:hidden;margin-top:10px}
.tanque i{display:block;height:100%;background:linear-gradient(90deg,#1c72d3,#5ab8ff);border-radius:99px}
</style></head><body>
<h1>&#128167; Tank Monitoring IoT</h1>
<div class="sub">Raspberry Pi Pico W &middot; DHT22 + HC-SR04 &middot; actualiza cada 5 s</div>
<div class="grid">
 <div class="card"><div class="lbl">&#127777; Temperatura</div>
  <div class="val"><span id="t">--</span> &deg;C</div>
  <span id="bt" class="badge b-off">--</span></div>
 <div class="card"><div class="lbl">&#128167; Humedad</div>
  <div class="val"><span id="h">--</span> %</div></div>
 <div class="card"><div class="lbl">&#128207; Nivel del tanque (distancia)</div>
  <div class="val"><span id="d">--</span> cm</div>
  <div class="tanque"><i id="niv" style="width:0%"></i></div>
  <div id="bajo" class="alerta" style="display:none">&#9888;&#65039; TANQUE CASI VAC&Iacute;O</div></div>
 <div class="card"><div class="lbl">&#9881; Bomba de llenado</div>
  <div class="val" id="bst">OFF</div>
  <button id="btn" onclick="bomba()">Encender bomba</button></div>
</div>
<script>
let on=false;
function pinta(d){
 document.getElementById("t").textContent=d.temp==null?"--":d.temp.toFixed(1);
 document.getElementById("h").textContent=d.hum==null?"--":d.hum.toFixed(1);
 document.getElementById("d").textContent=d.dist==null?"--":d.dist.toFixed(1);
 const b=document.getElementById("bt");b.textContent=d.rango.toUpperCase();
 b.className="badge b-"+(["frio","moderado","caliente"].includes(d.rango)?d.rango:"off");
 document.getElementById("bajo").style.display=d.tanque_bajo?"block":"none";
 const pct=d.dist==null?0:Math.max(0,Math.min(100,(d.dist/40)*100));
 document.getElementById("niv").style.width=pct+"%";
 on=d.bomba;
 document.getElementById("bst").textContent=on?"ON":"OFF";
 const btn=document.getElementById("btn");
 btn.textContent=on?"Apagar bomba":"Encender bomba";btn.className=on?"on":"";
}
function carga(){fetch("/data").then(r=>r.json()).then(pinta).catch(()=>{})}
function bomba(){fetch("/pump?on="+(on?0:1)).then(r=>r.json()).then(pinta).catch(()=>{})}
carga();setInterval(carga,5000);
</script></body></html>"""

# ---------------- Servidor web ----------------
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("0.0.0.0", 80))
srv.listen(2)
srv.settimeout(0.3)
print("Servidor web iniciado en el puerto 80.")

def responder(cli, cuerpo, tipo="text/html"):
    cli.send("HTTP/1.1 200 OK\r\nContent-Type: %s\r\nConnection: close\r\n\r\n" % tipo)
    cli.sendall(cuerpo)

ultima = 0
medir()
while True:
    # medición cada 5 s (requisito: actualizar datos cada 5 s)
    if time.ticks_diff(time.ticks_ms(), ultima) > 5000:
        medir()
        ultima = time.ticks_ms()
    try:
        cli, addr = srv.accept()
    except OSError:
        continue
    try:
        req = cli.recv(1024).decode()
        linea = req.split("\r\n")[0] if req else ""
        if "GET /data" in linea:
            responder(cli, json.dumps(estado), "application/json")
        elif "GET /pump" in linea:
            estado["bomba"] = ("on=1" in linea)
            led_bomba.value(1 if estado["bomba"] else 0)
            print("Bomba %s (desde el servidor web)" % ("ENCENDIDA" if estado["bomba"] else "APAGADA"))
            responder(cli, json.dumps(estado), "application/json")
        else:
            responder(cli, PAGINA)
    except Exception as e:
        print("Error atendiendo cliente:", e)
    finally:
        cli.close()
