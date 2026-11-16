// Cytron SHIELD-2AMOTOR - two motors with differential steering
// Motor 1 = LEFT, Motor 2 = RIGHT
const int DIR1 = 4;  // Motor 1 (left) direction
const int EN1  = 5;  // Motor 1 (left) PWM
const int DIR2 = 7;  // Motor 2 (right) direction
const int EN2  = 6;  // Motor 2 (right) PWM

// Drive one motor. speed: -255 (full reverse) to +255 (full forward)
void setMotor(int dirPin, int enPin, int speed) {
  speed = constrain(speed, -255, 255);
  digitalWrite(dirPin, speed >= 0 ? HIGH : LOW);  // HIGH = forward
  analogWrite(enPin, abs(speed));
}

// Differential steering.
// Positive = forward, negative = reverse, 0 = stop.
void driveRobot(int speedLeft, int speedRight) {
  setMotor(DIR1, EN1, speedLeft);
  setMotor(DIR2, EN2, speedRight);
}

void setup() {
  pinMode(DIR1, OUTPUT);
  pinMode(EN1, OUTPUT);
  pinMode(DIR2, OUTPUT);
  pinMode(EN2, OUTPUT);
}

void loop() {
  driveRobot(150, 150);    // straight forward
  delay(2000);

  driveRobot(180, 100);    // curve right (left wheel faster)
  delay(2000);

  driveRobot(100, 180);    // curve left (right wheel faster)
  delay(2000);

  driveRobot(150, -150);   // spin right on the spot
  delay(2000);

  driveRobot(-120, -120);  // straight backward
  delay(2000);

  driveRobot(0, 0);        // stop
  delay(1000);
}