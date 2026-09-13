/*
 * PROYECTO GUIADO 3 — Luz nocturna automática
 * Placa: Arduino UNO (simulada en Wokwi)
 * Lee una fotorresistencia (LDR) por entrada analógica y enciende
 * un LED automáticamente cuando el nivel de luz baja del umbral.
 * Demuestra: entradas analógicas (ADC) y toma de decisiones.
 */

const int PIN_LDR = A0;   // salida analógica del módulo LDR
const int PIN_LED = 9;    // LED indicador
const int UMBRAL  = 300;  // valor ADC bajo = oscuridad (0-1023)

void setup() {
  Serial.begin(9600);
  pinMode(PIN_LED, OUTPUT);
  Serial.println("Proyecto guiado 3: Luz nocturna automatica");
}

void loop() {
  int nivel = analogRead(PIN_LDR);      // 0 (oscuro) a 1023 (muy iluminado)
  bool oscuro = nivel < UMBRAL;
  digitalWrite(PIN_LED, oscuro);

  Serial.print("Nivel de luz (ADC): ");
  Serial.print(nivel);
  Serial.print("  -> LED ");
  Serial.println(oscuro ? "ENCENDIDO (esta oscuro)" : "apagado");
  delay(500);
}
