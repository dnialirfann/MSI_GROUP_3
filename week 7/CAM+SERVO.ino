/*
 * ============================================================
 *  ESP32-CAM CameraWebServer + Pushbutton Servo Panning
 * ============================================================
 *  WIRING:
 *    Servo signal  → GPIO 14
 *    Servo VCC     → 5V (use external 5V supply with shared GND)
 *    Servo GND     → GND
 *    Button leg 1  → GPIO 13
 *    Button leg 2  → GND
 *
 *  REQUIRED LIBRARY: ESP32Servo (Install via Library Manager)
 * ============================================================
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <ESP32Servo.h>

// Select camera model
#define CAMERA_MODEL_AI_THINKER // Has PSRAM
#include "camera_pins.h"

// WiFi credentials
const char* ssid     = "danial";
const char* password = "danial15";

// Servo & Pushbutton Config
const int SERVO_PIN  = 14;   // GPIO 14 → Servo signal wire
const int BUTTON_PIN = 13;   // GPIO 13 → Pushbutton (other leg to GND)

Servo panServo;               // Servo object from ESP32Servo library

int servoPos          = 0;    // Current servo angle (degrees)
int servoStep         = 1;    // Step size & direction (+1 or -1)
const int SERVO_MIN   = 0;    // Minimum pan angle
const int SERVO_MAX   = 180;  // Maximum pan angle
const int PAN_DELAY   = 1;   // Milliseconds between steps (controls speed)

unsigned long lastPanTime = 0; // Timestamp for non-blocking panning

void startCameraServer();
void setupLedFlash(int pin);

// Weak fallback for setupLedFlash to resolve missing linker symbol in app_httpd.cpp
void __attribute__((weak)) setupLedFlash(int pin) {
  pinMode(pin, OUTPUT);
  digitalWrite(pin, LOW);
}

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  // ----- Pushbutton Setup -----
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  // ----- Camera Configuration -----
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size   = FRAMESIZE_UXGA;
  config.pixel_format = PIXFORMAT_JPEG; // for streaming
  config.grab_mode    = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location  = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count     = 1;
  
  if (config.pixel_format == PIXFORMAT_JPEG) {
    if (psramFound()) {
      config.jpeg_quality = 10;
      config.fb_count     = 2;
      config.grab_mode    = CAMERA_GRAB_LATEST;
    } else {
      config.frame_size  = FRAMESIZE_SVGA;
      config.fb_location = CAMERA_FB_IN_DRAM;
    }
  } else {
    config.frame_size = FRAMESIZE_240X240;
#if CONFIG_IDF_TARGET_ESP32S3
    config.fb_count   = 2;
#endif
  }

#if defined(CAMERA_MODEL_ESP_EYE)
  pinMode(13, INPUT_PULLUP);
  pinMode(14, INPUT_PULLUP);
#endif

  // Init camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t * s = esp_camera_sensor_get();
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);       // flip it back
    s->set_brightness(s, 1);  // up the brightness just a bit
    s->set_saturation(s, -2); // lower the saturation
  }

  if (config.pixel_format == PIXFORMAT_JPEG) {
    s->set_framesize(s, FRAMESIZE_QVGA);
  }

#if defined(CAMERA_MODEL_M5STACK_WIDE) || defined(CAMERA_MODEL_M5STACK_ESP32CAM)
  s->set_vflip(s, 1);
  s->set_hmirror(s, 1);
#endif

#if defined(CAMERA_MODEL_ESP32S3_EYE)
  s->set_vflip(s, 1);
#endif

// Setup LED Flash if LED pin is defined in camera_pins.h
#if defined(LED_GPIO_NUM)
  setupLedFlash(LED_GPIO_NUM);
#endif

  WiFi.begin(ssid, password);
  WiFi.setSleep(false);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");

  startCameraServer();

  Serial.print("Camera Ready! Use 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("' to connect");

  // ----- Servo Setup -----
  panServo.attach(SERVO_PIN);
  panServo.write(servoPos);  // Start at 0 degrees
  Serial.println("Servo attached on GPIO 14 — press button on GPIO 13 to pan");
}

void loop() {
  // Pushbutton-controlled servo panning (Active-LOW: pressed = LOW)
  if (digitalRead(BUTTON_PIN) == LOW) {
    if (millis() - lastPanTime >= PAN_DELAY) {
      lastPanTime = millis();

      servoPos += servoStep;

      // Reverse direction at boundaries
      if (servoPos >= SERVO_MAX) {
        servoPos = SERVO_MAX;
        servoStep = -1;
      } else if (servoPos <= SERVO_MIN) {
        servoPos = SERVO_MIN;
        servoStep = 1;
      }

      panServo.write(servoPos);
    }
  }

  delay(1);  // Small yield for freeRTOS tasks
}