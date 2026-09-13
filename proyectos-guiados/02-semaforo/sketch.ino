/*
 * PROYECTO GUIADO 2 — Semáforo
 * Placa: Arduino UNO (simulada en Wokwi)
 * Secuencia de semáforo vehicular: verde (4 s) -> amarillo (1.5 s)
 * -> rojo (4 s), con reporte de cada fase por el monitor serial.
 */

const int PIN_VERDE    = 4;
const int PIN_AMARILLO = 3;
const int PIN_ROJO     = 2;

void setup() {
  Serial.begin(9600);
  pinMode(PIN_VERDE, OUTPUT);
  pinMode(PIN_AMARILLO, OUTPUT);
  pinMode(PIN_ROJO, OUTPUT);
  Serial.println("Proyecto guiado 2: Semaforo");
}

void fase(int pin, const char* nombre, unsigned long ms) {
  digitalWrite(PIN_VERDE, pin == PIN_VERDE);
  digitalWrite(PIN_AMARILLO, pin == PIN_AMARILLO);
  digitalWrite(PIN_ROJO, pin == PIN_ROJO);
  Serial.print("Fase: ");
  Serial.println(nombre);
  delay(ms);
}

void loop() {
  fase(PIN_VERDE,    "VERDE - avanzar",   4000);
  fase(PIN_AMARILLO, "AMARILLO - precaucion", 1500);
  fase(PIN_ROJO,     "ROJO - alto",       4000);
}
