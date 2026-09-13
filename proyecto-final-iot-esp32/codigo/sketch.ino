/*
 * ============================================================
 *  PROYECTO FINAL — Estación de Monitoreo Ambiental IoT
 *  Placa: ESP32 DevKit-C v4  (simulada en Wokwi)
 *  Autor: Xólotl Gael Chávez Zamora
 * ============================================================
 *  Funcionalidad:
 *   1. Lee temperatura (sensor NTC, GPIO34) y nivel de luz
 *      (fotorresistencia LDR, GPIO35) cada 500 ms.
 *   2. Semáforo térmico con 3 LEDs:
 *        VERDE   (GPIO25) -> temperatura normal  (< umbral - 5 °C)
 *        AMARILLO(GPIO26) -> advertencia          (a 5 °C del umbral)
 *        ROJO    (GPIO27) -> alarma               (>= umbral)
 *   3. Buzzer (GPIO18) suena cuando la temperatura alcanza el
 *      umbral; se puede silenciar con el botón físico (GPIO19)
 *      o desde el dashboard web.
 *   4. LED AZUL "actuador remoto" (GPIO14) controlado únicamente
 *      desde el navegador (encender / apagar).
 *   5. SERVIDOR WEB (puerto 80) con:
 *        GET /            -> dashboard HTML responsivo
 *        GET /data        -> telemetría JSON (polling cada 1 s)
 *        GET /led?state=  -> controla el LED remoto (on/off)
 *        GET /umbral?c=   -> cambia el umbral de alarma
 *        GET /silenciar   -> silencia la alarma activa
 *  No usa librerías externas: WiFi.h y WebServer.h son parte
 *  del core de Arduino-ESP32.
 * ============================================================
 */

#include <WiFi.h>
#include <WebServer.h>
#include <math.h>

// ---------- Pines ----------
const int PIN_NTC     = 34;  // ADC1_CH6 — sensor de temperatura NTC
const int PIN_LDR     = 35;  // ADC1_CH7 — fotorresistencia (módulo, salida AO)
const int PIN_LED_V   = 25;  // LED verde   — temperatura normal
const int PIN_LED_A   = 26;  // LED amarillo— advertencia
const int PIN_LED_R   = 27;  // LED rojo    — alarma
const int PIN_LED_REM = 14;  // LED azul    — actuador remoto (web)
const int PIN_BUZZER  = 18;  // buzzer de alarma
const int PIN_BOTON   = 19;  // botón para silenciar alarma (pull-up interno)

// ---------- Red WiFi (red simulada de Wokwi) ----------
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASS = "";

// ---------- Estado global ----------
WebServer server(80);
float tempC        = 0.0;   // temperatura actual en °C
float lux          = 0.0;   // iluminancia estimada en lux
float umbralAlarma = 40.0;  // umbral de alarma (configurable desde la web)
bool  ledRemoto    = false; // estado del LED azul controlado por web
bool  alarmaActiva = false; // true cuando temp >= umbral
bool  silenciada   = false; // alarma silenciada por el usuario
unsigned long tUltimaLectura = 0;

// ============================================================
//  LECTURA DE SENSORES
// ============================================================
// Conversión ADC -> °C para el NTC de Wokwi (Beta = 3950, R25 = 10k)
float leerTemperatura() {
  int adc = analogRead(PIN_NTC);
  if (adc <= 0) adc = 1;
  if (adc >= 4095) adc = 4094;
  const float BETA = 3950.0;
  return 1.0 / (log(1.0 / (4095.0 / adc - 1.0)) / BETA + 1.0 / 298.15) - 273.15;
}

// Conversión ADC -> lux para el módulo LDR de Wokwi
float leerLux() {
  int adc = analogRead(PIN_LDR);
  float voltaje = adc / 4095.0 * 3.3;
  if (voltaje >= 3.29) voltaje = 3.29;
  const float GAMMA = 0.7;
  const float RL10  = 50.0;
  float resistencia = 2000.0 * voltaje / (1.0 - voltaje / 3.3);
  return pow(RL10 * 1e3 * pow(10, GAMMA) / resistencia, (1.0 / GAMMA));
}

// ============================================================
//  LÓGICA DE ALARMA Y SEMÁFORO
// ============================================================
void actualizarSemaforo() {
  bool normal      = tempC < umbralAlarma - 5.0;
  bool advertencia = !normal && tempC < umbralAlarma;
  bool alarma      = tempC >= umbralAlarma;

  digitalWrite(PIN_LED_V, normal);
  digitalWrite(PIN_LED_A, advertencia);
  digitalWrite(PIN_LED_R, alarma);

  if (alarma && !alarmaActiva) {          // flanco de subida de la alarma
    alarmaActiva = true;
    silenciada   = false;
    Serial.printf("[ALARMA] Temperatura %.1f C >= umbral %.1f C\n", tempC, umbralAlarma);
  } else if (!alarma && alarmaActiva) {   // la temperatura volvió a la normalidad
    alarmaActiva = false;
    silenciada   = false;
    Serial.println("[ALARMA] Temperatura normalizada. Alarma apagada.");
  }

  // El buzzer suena solo si hay alarma y no fue silenciada
  if (alarmaActiva && !silenciada) {
    tone(PIN_BUZZER, 1000);
  } else {
    noTone(PIN_BUZZER);
  }
}

void revisarBoton() {
  // Botón con pull-up: LOW = presionado. Silencia la alarma local.
  if (digitalRead(PIN_BOTON) == LOW && alarmaActiva && !silenciada) {
    silenciada = true;
    Serial.println("[BOTON] Alarma silenciada desde el boton fisico.");
    delay(200); // anti-rebote simple
  }
}

// ============================================================
//  SERVIDOR WEB
// ============================================================
const char PAGINA[] PROGMEM = R"HTML(
<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Estacion IoT — ESP32</title><style>
:root{--bg:#0b1220;--card:#141d31;--ink:#eef2ff;--dim:#93a0bf;--ok:#34d399;--warn:#fbbf24;--bad:#f87171;--acc:#60a5fa}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:system-ui,Segoe UI,Roboto,sans-serif;min-height:100vh;padding:24px}
h1{font-size:22px;letter-spacing:.5px}
.sub{color:var(--dim);font-size:13px;margin:4px 0 20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;max-width:980px}
.card{background:var(--card);border:1px solid #223052;border-radius:14px;padding:18px}
.lbl{color:var(--dim);font-size:12px;text-transform:uppercase;letter-spacing:1px}
.val{font-size:42px;font-weight:700;margin:6px 0}
.un{font-size:18px;color:var(--dim)}
.bar{height:8px;background:#0e1526;border-radius:99px;overflow:hidden;margin-top:8px}
.bar i{display:block;height:100%;background:var(--acc);width:0%;transition:width .4s}
.badge{display:inline-block;padding:4px 12px;border-radius:99px;font-size:13px;font-weight:600}
.b-ok{background:#0c2b22;color:var(--ok)}.b-warn{background:#2e2410;color:var(--warn)}.b-bad{background:#331414;color:var(--bad)}
button{cursor:pointer;border:0;border-radius:10px;padding:12px 18px;font-size:15px;font-weight:600;width:100%;margin-top:10px}
.on{background:var(--acc);color:#04101f}.off{background:#223052;color:var(--ink)}
.sil{background:var(--bad);color:#fff}
input{width:100%;padding:10px;border-radius:10px;border:1px solid #223052;background:#0e1526;color:var(--ink);font-size:16px;margin-top:8px}
footer{margin-top:22px;color:var(--dim);font-size:12px}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--ok);margin-right:6px;animation:p 1.6s infinite}
@keyframes p{50%{opacity:.25}}
</style></head><body>
<h1>🌡️ Estación de Monitoreo Ambiental IoT</h1>
<div class="sub"><span class="dot"></span>ESP32 · Servidor web embebido · <span id="up">—</span></div>
<div class="grid">
 <div class="card"><div class="lbl">Temperatura</div>
   <div class="val"><span id="t">—</span><span class="un"> °C</span></div>
   <span id="estado" class="badge b-ok">NORMAL</span>
   <div class="bar"><i id="tb"></i></div></div>
 <div class="card"><div class="lbl">Nivel de luz</div>
   <div class="val"><span id="l">—</span><span class="un"> lx</span></div>
   <span id="ldia" class="badge b-ok">—</span>
   <div class="bar"><i id="lb"></i></div></div>
 <div class="card"><div class="lbl">Actuador remoto (LED azul)</div>
   <div class="val" id="ledtxt" style="font-size:28px">APAGADO</div>
   <button id="btn" class="on" onclick="toggleLed()">Encender LED</button></div>
 <div class="card"><div class="lbl">Umbral de alarma (°C)</div>
   <input id="u" type="number" step="1" min="0" max="80">
   <button class="off" onclick="setUmbral()">Guardar umbral</button>
   <button class="sil" onclick="fetch('/silenciar').then(rf)">🔕 Silenciar alarma</button></div>
</div>
<footer>Proyecto final — Curso de Microcontroladores · Simulación en Wokwi · GET /data devuelve la telemetría JSON</footer>
<script>
let led=false, uSet=false;
function rf(){refrescar()}
function refrescar(){fetch('/data').then(r=>r.json()).then(d=>{
 t.textContent=d.temp.toFixed(1); l.textContent=Math.round(d.lux);
 tb.style.width=Math.min(100,d.temp/80*100)+'%';
 lb.style.width=Math.min(100,Math.log10(Math.max(1,d.lux))/5*100)+'%';
 ldia.textContent=d.lux>5000?'DÍA / MUCHA LUZ':(d.lux>50?'INTERIOR':'OSCURO');
 ldia.className='badge '+(d.lux>50?'b-ok':'b-warn');
 estado.textContent=d.alarma?(d.silenciada?'ALARMA (silenciada)':'🚨 ALARMA'):(d.temp>=d.umbral-5?'ADVERTENCIA':'NORMAL');
 estado.className='badge '+(d.alarma?'b-bad':(d.temp>=d.umbral-5?'b-warn':'b-ok'));
 led=d.led; ledtxt.textContent=led?'ENCENDIDO':'APAGADO'; ledtxt.style.color=led?'#60a5fa':'';
 btn.textContent=led?'Apagar LED':'Encender LED'; btn.className=led?'off':'on';
 if(!uSet){u.value=d.umbral; uSet=true}
 up.textContent='uptime '+d.uptime+' s';
})}
function toggleLed(){fetch('/led?state='+(led?'off':'on')).then(rf)}
function setUmbral(){fetch('/umbral?c='+u.value).then(rf)}
setInterval(refrescar,1000); refrescar();
</script></body></html>
)HTML";

void handleRoot() {
  server.send_P(200, "text/html", PAGINA);
}

void handleData() {
  char json[200];
  snprintf(json, sizeof(json),
    "{\"temp\":%.1f,\"lux\":%.0f,\"led\":%s,\"umbral\":%.1f,"
    "\"alarma\":%s,\"silenciada\":%s,\"uptime\":%lu}",
    tempC, lux, ledRemoto ? "true" : "false", umbralAlarma,
    alarmaActiva ? "true" : "false", silenciada ? "true" : "false",
    millis() / 1000UL);
  server.send(200, "application/json", json);
}

void handleLed() {
  String estado = server.arg("state");
  ledRemoto = (estado == "on");
  digitalWrite(PIN_LED_REM, ledRemoto);
  Serial.printf("[WEB] LED remoto -> %s\n", ledRemoto ? "ENCENDIDO" : "APAGADO");
  server.send(200, "text/plain", ledRemoto ? "on" : "off");
}

void handleUmbral() {
  float c = server.arg("c").toFloat();
  if (c >= 0 && c <= 80) {
    umbralAlarma = c;
    Serial.printf("[WEB] Nuevo umbral de alarma: %.1f C\n", umbralAlarma);
  }
  server.send(200, "text/plain", String(umbralAlarma));
}

void handleSilenciar() {
  if (alarmaActiva) {
    silenciada = true;
    Serial.println("[WEB] Alarma silenciada desde el dashboard.");
  }
  server.send(200, "text/plain", "ok");
}

// ============================================================
//  SETUP Y LOOP
// ============================================================
void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED_V, OUTPUT);
  pinMode(PIN_LED_A, OUTPUT);
  pinMode(PIN_LED_R, OUTPUT);
  pinMode(PIN_LED_REM, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_BOTON, INPUT_PULLUP);

  Serial.println("\n=============================================");
  Serial.println("  ESTACION DE MONITOREO AMBIENTAL IoT - ESP32");
  Serial.println("=============================================");
  Serial.printf("Conectando a WiFi \"%s\"", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println(" conectado!");
  Serial.print("Direccion IP del servidor web: http://");
  Serial.println(WiFi.localIP());

  server.on("/",          handleRoot);
  server.on("/data",      handleData);
  server.on("/led",       handleLed);
  server.on("/umbral",    handleUmbral);
  server.on("/silenciar", handleSilenciar);
  server.begin();
  Serial.println("Servidor web iniciado en el puerto 80.");
  Serial.printf("Umbral de alarma inicial: %.1f C\n", umbralAlarma);
}

void loop() {
  server.handleClient();
  revisarBoton();

  if (millis() - tUltimaLectura >= 500) {
    tUltimaLectura = millis();
    tempC = leerTemperatura();
    lux   = leerLux();
    actualizarSemaforo();

    static int contador = 0;
    if (++contador >= 6) {   // log en serial cada 3 s
      contador = 0;
      Serial.printf("Temp: %5.1f C | Luz: %7.0f lx | Umbral: %.0f C | LED web: %s%s\n",
                    tempC, lux, umbralAlarma, ledRemoto ? "ON" : "OFF",
                    alarmaActiva ? (silenciada ? " | ALARMA(sil.)" : " | ALARMA!") : "");
    }
  }
}
