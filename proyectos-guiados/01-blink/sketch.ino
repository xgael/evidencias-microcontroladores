/*
 * PROYECTO GUIADO 1 — Blink (Hola Mundo del microcontrolador)
 * Placa: Arduino UNO (simulada en Wokwi)
 * Enciende y apaga un LED externo cada 500 ms y reporta el
 * estado por el monitor serial.
 */

const int PIN_LED = 8;   // LED externo con resistencia de 220 ohms

void setup() {
  Serial.begin(9600);
  pinMode(PIN_LED, OUTPUT);
  Serial.println("Proyecto guiado 1: Blink");
}

void loop() {
  digitalWrite(PIN_LED, HIGH);   // enciende el LED
  Serial.println("LED: ENCENDIDO");
  delay(500);
  digitalWrite(PIN_LED, LOW);    // apaga el LED
  Serial.println("LED: APAGADO");
  delay(500);
}
