const int potPin = A0;   // potentiometer middle pin
const int ledPin = 9;    // LED (with resistor) on pin 9

void setup() {
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);    // same baud rate as your Python script
}

void loop() {
  int potValue = analogRead(potPin);   // 0 to 1023

  if (potValue >= 512) {               // knob at half or more
    digitalWrite(ledPin, HIGH);
  } else {
    digitalWrite(ledPin, LOW);
  }

  Serial.println(potValue);            // Python can still read this
  delay(100);
}
