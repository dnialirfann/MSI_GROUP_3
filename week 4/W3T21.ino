#include <Servo.h>
Servo servo;
int servoPosition = 90;
void setup() {
servo.attach(9);
servo.write(servoPosition);
pinMode(4, OUTPUT); // Green LED
pinMode(3, OUTPUT); // Red LED
Serial.begin(9600);
}
void loop() {
if (Serial.available() > 0) {
char command = Serial.read();
if (command == 'A') {
servo.write(180); // Unlock
digitalWrite(4, HIGH);
digitalWrite(3, LOW);
} else if (command == 'D') {
servo.write(90); // Lock
digitalWrite(4, LOW);
digitalWrite(3, HIGH);
}
}
}
