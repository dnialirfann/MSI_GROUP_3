#include <Servo.h>

Servo myservo;
const int potPin = A0;
const int ledPin = 8;
bool running = true;

void setup() {
  Serial.begin(9600);
  myservo.attach(9);
  pinMode(ledPin, OUTPUT);
}

void loop() {
  // keyboard commands from Python: q = stop, r = resume
  if (Serial.available() > 0) {
    char c = Serial.read();
    if (c == 'q') {
      running = false;
      myservo.detach();
      digitalWrite(ledPin, LOW);
    } else if (c == 'r' && !running) {
      running = true;
      myservo.attach(9);
    }
  }

  if (running) {
    int pot = analogRead(potPin);          // 0-1023
    int angle = map(pot, 0, 1023, 0, 180); // 0-180 deg
    myservo.write(angle);
    digitalWrite(ledPin, angle > 90 ? HIGH : LOW);

    Serial.print(pot);
    Serial.print(",");
    Serial.println(angle);
    delay(50);
  }
}
