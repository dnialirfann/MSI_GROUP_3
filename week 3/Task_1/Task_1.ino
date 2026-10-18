const int potPin = A0;
const int ledPin = 13;

void setup() {
  Serial.begin(9600);
  pinMode(ledPin, OUTPUT);
}

void loop() {
  int potValue = analogRead(potPin);

  Serial.println(potValue);

  if (Serial.available() > 0) {
    char command = Serial.read();

    if (command == '1') {
      digitalWrite(ledPin, HIGH);
    } 
    else if (command == '0') {
      digitalWrite(ledPin, LOW);
    }
  }

  delay(50);
}