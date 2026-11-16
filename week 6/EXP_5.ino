// Cytron SHIELD-2AMOTOR Pin Definitions for Motor 1
const int DIR1 = 4; // Direction pin
const int EN1 = 5;  // PWM speed control pin

void setup() {
  pinMode(DIR1, OUTPUT);
  pinMode(EN1, OUTPUT);
}

void loop() {
  // Run forward for 5 seconds
  digitalWrite(DIR1, HIGH); // Set direction forward
  analogWrite(EN1, 200);    // Speed: 0 to 255 (Adjust as needed)
  delay(5000);              // Run for 5000 milliseconds (5 seconds)

  // Stop for 1 second
  analogWrite(EN1, 0);      // Turn speed to 0 (stop)
  delay(1000);              // Wait for 1000 milliseconds (1 second)
}