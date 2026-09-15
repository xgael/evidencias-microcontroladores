# ============================================================
#  Monitoreo Ambiental IoT para Invernadero — Raspberry Pi Pico W
#  MicroPython · Sensor BME280 (temperatura, humedad, presión)
# ============================================================
#  Base elegida: versión con SERVIDOR WEB (opción A del módulo).
#
#  Funcionalidad:
#   1. Lee el BME280 por I2C cada 2 s (temp °C, humedad %, presión hPa).
#   2. Clasifica cada variable en ACEPTABLE / SOSPECHOSO / ALERTA según
#      rangos de invernadero, y enciende el LED correspondiente:
#        VERDE    (GP13)          -> todo en rango aceptable
#        AMARILLO (GP13 + GP14)   -> alguna variable en rango sospechoso
#        ROJO     (GP14)          -> alguna variable en rango de alerta
#      (Amarillo = rojo + verde encendidos a la vez, como pide la práctica
#       cuando se usan LEDs Rojo/Verde/Azul discretos.)
#      AZUL (GP15) parpadea al arrancar: indica "conectando a WiFi".
#   3. Servidor web en el puerto 80: dashboard en vivo + /data en JSON.
#
#  Rangos definidos para un invernadero de hortalizas (jitomate/pepino):
#   Temperatura:  aceptable 18–30 °C · sospechoso 15–18 o 30–35 · alerta <15 o >35
#   Humedad:      aceptable 40–70 %  · sospechoso 30–40 o 70–85 · alerta <30 o >85
#   Presión:      aceptable 1000–1025 hPa · sospechoso 980–1000 o 1025–1040
#                 · alerta <980 o >1040  (caídas bruscas anticipan tormenta)
# ============================================================

import network
import socket
import time
import json
from machine import Pin, I2C

# ---------------- Driver BME280 (compensación oficial Bosch, integrado
# en este archivo para que el proyecto sea de UN solo archivo) ----------------
class BME280:
    def __init__(self, i2c, addr=0x76):
        self.i2c = i2c
        self.addr = addr
        self.i2c.writeto_mem(self.addr, 0xF2, b'\x01')   # hum oversampling x1
        self.i2c.writeto_mem(self.addr, 0xF4, b'\x27')   # temp/pres x1, modo normal
        c = self.i2c.readfrom_mem(self.addr, 0x88, 26)
        h1 = self.i2c.readfrom_mem(self.addr, 0xA1, 1)
        h2 = self.i2c.readfrom_mem(self.addr, 0xE1, 7)

        def u16(b, i): return b[i] | (b[i+1] << 8)
        def s16(b, i):
            v = u16(b, i)
            return v - 65536 if v > 32767 else v

        self.T1 = u16(c, 0);  self.T2 = s16(c, 2);  self.T3 = s16(c, 4)
        self.P1 = u16(c, 6);  self.P2 = s16(c, 8);  self.P3 = s16(c, 10)
        self.P4 = s16(c, 12); self.P5 = s16(c, 14); self.P6 = s16(c, 16)
        self.P7 = s16(c, 18); self.P8 = s16(c, 20); self.P9 = s16(c, 22)
        self.H1 = h1[0]
        self.H2 = s16(h2, 0); self.H3 = h2[2]
        self.H4 = (h2[3] << 4) | (h2[4] & 0x0F)
        self.H5 = (h2[5] << 4) | (h2[4] >> 4)
        self.H6 = h2[6] - 256 if h2[6] > 127 else h2[6]

    def leer(self):
        d = self.i2c.readfrom_mem(self.addr, 0xF7, 8)
        pres_raw = (d[0] << 12) | (d[1] << 4) | (d[2] >> 4)
        temp_raw = (d[3] << 12) | (d[4] << 4) | (d[5] >> 4)
        hum_raw  = (d[6] << 8) | d[7]

        # temperatura (fórmula Bosch en enteros)
        v1 = ((temp_raw >> 3) - (self.T1 << 1)) * self.T2 >> 11
        v2 = (((((temp_raw >> 4) - self.T1) * ((temp_raw >> 4) - self.T1)) >> 12) * self.T3) >> 14
        t_fine = v1 + v2
        temp = ((t_fine * 5 + 128) >> 8) / 100

        # presión
        p1 = t_fine - 128000
        p2 = p1 * p1 * self.P6
        p2 += (p1 * self.P5) << 17
        p2 += self.P4 << 35
        p1 = ((p1 * p1 * self.P3) >> 8) + ((p1 * self.P2) << 12)
        p1 = ((1 << 47) + p1) * self.P1 >> 33
        if p1 == 0:
            pres = 0
        else:
            p = 1048576 - pres_raw
            p = ((p << 31) - p2) * 3125 // p1
            v1 = (self.P9 * (p >> 13) * (p >> 13)) >> 25
            v2 = (self.P8 * p) >> 19
            pres = ((p + v1 + v2) >> 8) + (self.P7 << 4)
            pres = pres / 25600   # hPa

        # humedad
        h = t_fine - 76800
        h = (((((hum_raw << 14) - (self.H4 << 20) - (self.H5 * h)) + 16384) >> 15)
             * (((((((h * self.H6) >> 10) * (((h * self.H3) >> 11) + 32768)) >> 10) + 2097152)
                * self.H2 + 8192) >> 14))
        h -= (((((h >> 15) * (h >> 15)) >> 7) * self.H1) >> 4)
        h = max(0, min(h, 419430400))
        hum = (h >> 12) / 1024

        return temp, hum, pres



# ---------------- Driver BMP180 (temp + presión, addr 0x77) ----------------
# Se usa en la SIMULACIÓN (Wokwi no ofrece BME280 para Pico W); en hardware real
# el sistema detecta el BME280 automáticamente y usa ese. La humedad, en el modo
# simulación, la da un DHT22 en GP16.
class BMP180:
    def __init__(self, i2c, addr=0x77):
        self.i2c = i2c; self.addr = addr
        c = self.i2c.readfrom_mem(addr, 0xAA, 22)
        def s16(i):
            v = (c[i] << 8) | c[i+1]
            return v - 65536 if v > 32767 else v
        def u16(i): return (c[i] << 8) | c[i+1]
        self.AC1=s16(0); self.AC2=s16(2); self.AC3=s16(4)
        self.AC4=u16(6); self.AC5=u16(8); self.AC6=u16(10)
        self.B1=s16(12); self.B2=s16(14); self.MC=s16(18); self.MD=s16(20)

    def leer(self):
        self.i2c.writeto_mem(self.addr, 0xF4, b'\x2e'); time.sleep_ms(6)
        d = self.i2c.readfrom_mem(self.addr, 0xF6, 2)
        UT = (d[0] << 8) | d[1]
        X1 = ((UT - self.AC6) * self.AC5) >> 15
        X2 = (self.MC << 11) // (X1 + self.MD)
        B5 = X1 + X2
        temp = ((B5 + 8) >> 4) / 10

        self.i2c.writeto_mem(self.addr, 0xF4, b'\x34'); time.sleep_ms(6)
        d = self.i2c.readfrom_mem(self.addr, 0xF6, 3)
        UP = ((d[0] << 16) | (d[1] << 8) | d[2]) >> 8
        B6 = B5 - 4000
        X1 = (self.B2 * ((B6 * B6) >> 12)) >> 11
        X2 = (self.AC2 * B6) >> 11
        B3 = ((self.AC1 * 4 + X1 + X2) + 2) >> 2
        X1 = (self.AC3 * B6) >> 13
        X2 = (self.B1 * ((B6 * B6) >> 12)) >> 16
        X3 = ((X1 + X2) + 2) >> 2
        B4 = (self.AC4 * (X3 + 32768)) >> 15
        B7 = (UP - B3) * 50000
        p = (B7 * 2) // B4 if B7 < 0x80000000 else (B7 // B4) * 2
        X1 = (p >> 8) * (p >> 8)
        X1 = (X1 * 3038) >> 16
        X2 = (-7357 * p) >> 16
        pres = (p + ((X1 + X2 + 3791) >> 4)) / 100   # hPa
        return temp, pres

# ---------------- Rangos del invernadero ----------------
RANGOS = {
    "temp": {"acept": (18, 30), "sosp": (15, 35)},   # fuera de sosp = alerta
    "hum":  {"acept": (40, 70), "sosp": (30, 85)},
    "pres": {"acept": (1000, 1025), "sosp": (980, 1040)},
}

def clasificar(valor, r):
    """0 = aceptable, 1 = sospechoso, 2 = alerta."""
    if r["acept"][0] <= valor <= r["acept"][1]:
        return 0
    if r["sosp"][0] <= valor <= r["sosp"][1]:
        return 1
    return 2

# ---------------- Hardware ----------------
led_verde = Pin(13, Pin.OUT)
led_rojo  = Pin(14, Pin.OUT)
led_azul  = Pin(15, Pin.OUT)

i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
dispositivos = i2c.scan()
print("I2C detectado:", [hex(a) for a in dispositivos])
if 0x76 in dispositivos:                      # hardware real con BME280
    sensor = BME280(i2c, 0x76)
    dht22 = None
    print("Sensor: BME280 (temperatura, humedad y presion)")
else:                                          # simulación Wokwi: BMP180 + DHT22
    import dht
    sensor = BMP180(i2c, 0x77)
    dht22 = dht.DHT22(Pin(16))
    print("Sensor: BMP180 (temp/presion) + DHT22 (humedad) [modo simulacion]")

def poner_leds(nivel):
    """Verde=aceptable · Amarillo(V+R)=sospechoso · Rojo=alerta."""
    led_verde.value(nivel <= 1)      # verde prende en 0 y en 1 (amarillo)
    led_rojo.value(nivel >= 1)       # rojo prende en 1 (amarillo) y en 2
    led_azul.value(0)

# ---------------- WiFi ----------------
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("Wokwi-GUEST", "")
print("Conectando a WiFi", end="")
while not wlan.isconnected():
    led_azul.toggle()                # azul parpadea mientras conecta
    print(".", end="")
    time.sleep(0.3)
led_azul.value(0)
ip = wlan.ifconfig()[0]
print("\nWiFi conectado. Dashboard: http://%s/" % ip)

# ---------------- Estado global ----------------
estado = {"temp": 0.0, "hum": 0.0, "pres": 0.0,
          "nivel": 0, "niveles": {"temp": 0, "hum": 0, "pres": 0}}
NOMBRES = ("OK ", "SOSP", "ALRT")

def medir():
    if dht22 is None:
        t, h, p = sensor.leer()               # BME280: todo en uno
    else:
        t, p = sensor.leer()                  # BMP180: temp + presión
        dht22.measure()
        h = dht22.humidity()                  # DHT22: humedad
    nt = clasificar(t, RANGOS["temp"])
    nh = clasificar(h, RANGOS["hum"])
    np_ = clasificar(p, RANGOS["pres"])
    nivel = max(nt, nh, np_)         # manda la variable en peor estado
    estado.update(temp=round(t, 1), hum=round(h, 1), pres=round(p, 1),
                  nivel=nivel, niveles={"temp": nt, "hum": nh, "pres": np_})
    poner_leds(nivel)
    print("T=%5.1fC[%s] H=%5.1f%%[%s] P=%7.1fhPa[%s] -> LED %s" % (
        t, NOMBRES[nt].strip(), h, NOMBRES[nh].strip(), p, NOMBRES[np_].strip(),
        ("VERDE", "AMARILLO", "ROJO")[nivel]))

# ---------------- Dashboard web ----------------
PAGINA = """<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Invernadero IoT</title><style>
body{background:#0d1b12;color:#eafbea;font-family:system-ui,sans-serif;margin:0;padding:22px}
h1{font-size:21px;margin:0}.sub{color:#8fbc9b;font-size:13px;margin:4px 0 18px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;max-width:860px}
.card{background:#14291b;border:1px solid #24513a;border-radius:12px;padding:16px}
.lbl{color:#8fbc9b;font-size:11px;text-transform:uppercase;letter-spacing:1px}
.val{font-size:36px;font-weight:700;margin:4px 0}.un{font-size:16px;color:#8fbc9b}
.badge{display:inline-block;padding:3px 10px;border-radius:99px;font-size:12px;font-weight:700}
.b0{background:#123c24;color:#4ade80}.b1{background:#3c3512;color:#fbbf24}.b2{background:#3c1212;color:#f87171}
.semaforo{display:flex;gap:10px;margin-top:16px}
.foco{width:34px;height:34px;border-radius:50%;background:#1c1c1c;border:2px solid #333}
.foco.on-v{background:#22c55e;box-shadow:0 0 18px #22c55e}
.foco.on-a{background:#eab308;box-shadow:0 0 18px #eab308}
.foco.on-r{background:#ef4444;box-shadow:0 0 18px #ef4444}
footer{margin-top:18px;color:#8fbc9b;font-size:11px}
</style></head><body>
<h1>🌱 Invernadero — Monitoreo Ambiental IoT</h1>
<div class="sub">Raspberry Pi Pico W · BME280 · actualiza cada 2 s</div>
<div class="grid">
 <div class="card"><div class="lbl">🌡 Temperatura</div>
  <div class="val"><span id="t">—</span><span class="un"> °C</span></div>
  <span id="bt" class="badge b0">—</span></div>
 <div class="card"><div class="lbl">💧 Humedad</div>
  <div class="val"><span id="h">—</span><span class="un"> %</span></div>
  <span id="bh" class="badge b0">—</span></div>
 <div class="card"><div class="lbl">🧭 Presión</div>
  <div class="val"><span id="p">—</span><span class="un"> hPa</span></div>
  <span id="bp" class="badge b0">—</span></div>
 <div class="card"><div class="lbl">🚦 Estado global</div>
  <div class="semaforo">
   <div id="fv" class="foco"></div><div id="fa" class="foco"></div><div id="fr" class="foco"></div>
  </div><div id="msg" style="margin-top:10px;font-weight:700">—</div></div>
</div>
<footer>Rangos: T 18–30 °C · H 40–70 % · P 1000–1025 hPa (aceptables) — sistema de alertas del proyecto</footer>
<script>
const N=["ACEPTABLE","SOSPECHOSO","ALERTA"],C=["b0","b1","b2"];
function pinta(id,val,niv){document.getElementById(id.slice(1)).textContent=val;
 const b=document.getElementById("b"+id.slice(1));b.textContent=N[niv];b.className="badge "+C[niv];}
setInterval(()=>fetch("/data").then(r=>r.json()).then(d=>{
 pinta("#t",d.temp.toFixed(1),d.niveles.temp);
 pinta("#h",d.hum.toFixed(1),d.niveles.hum);
 pinta("#p",d.pres.toFixed(1),d.niveles.pres);
 fv.className="foco"+(d.nivel==0?" on-v":"");
 fa.className="foco"+(d.nivel==1?" on-a":"");
 fr.className="foco"+(d.nivel==2?" on-r":"");
 msg.textContent=["✅ Todo en rango","⚠️ Rango sospechoso","🚨 ALERTA"][d.nivel];
}),2000);
</script></body></html>"""

def atender(cliente):
    peticion = cliente.recv(1024).decode()
    if "GET /data" in peticion:
        cuerpo = json.dumps(estado)
        cliente.send("HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n" + cuerpo)
    else:
        cliente.send("HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n" + PAGINA)
    cliente.close()

servidor = socket.socket()
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
servidor.bind(("0.0.0.0", 80))
servidor.listen(2)
servidor.settimeout(0.2)             # no bloquear el ciclo de medición
print("Servidor web iniciado en el puerto 80.")

# ---------------- Ciclo principal ----------------
ultima = 0
while True:
    if time.ticks_diff(time.ticks_ms(), ultima) >= 2000:
        ultima = time.ticks_ms()
        medir()
    try:
        cliente, _ = servidor.accept()
        atender(cliente)
    except OSError:
        pass                          # timeout sin clientes: seguir midiendo
