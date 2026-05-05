/**
 * IoT Device Unit Unified Configuration Template
 * 
 * Usage Instructions:
 * 1. Copy this file as config.h
 * 2. Modify configurations according to your network environment
 * 3. Upload to the corresponding ESP8266 device
 */

#ifndef CONFIG_H
#define CONFIG_H

// ========================================
// WiFi Network Configuration
// ========================================
#define WIFI_SSID           "Your_WiFi_SSID"
#define WIFI_PASSWORD       "Your_WiFi_Password"

// ========================================
// Gateway Server Configuration
// ========================================
#define GATEWAY_IP          "192.168.1.107"
#define GATEWAY_PORT        9300

// ========================================
// Device Identity Configuration
// ========================================
// Air Conditioner Unit: "A1_tem_hum"
// Curtain Unit: "A1_curtain"
// Door Security Unit: "A1_security"
#define DEVICE_ID           "A1_tem_hum"

// ========================================
// Communication Interval Configuration (seconds)
// ========================================
#define SEND_INTERVAL       3
#define RECV_INTERVAL       3

// ========================================
// Hardware Pin Configuration (modify according to specific device)
// ========================================
// OLED Display
#define OLED_SDA_PIN        D1
#define OLED_SCL_PIN        D2
#define OLED_RESET_PIN      -1

// LED Indicator
#define LED_PIN             LED_BUILTIN

// Temperature & Humidity Sensor (Air Conditioner Unit Only)
#define DHT_PIN             D5
#define DHT_TYPE            DHT11

// Light Intensity Sensor (Curtain Unit Only)
#define BH1750_ADDR         0x23

// Curtain Control Pins (Curtain Unit Only)
#define CURTAIN_PIN1        D3
#define CURTAIN_PIN2        D4

// Buzzer (Curtain Unit Only)
#define BUZZER_PIN          D5

#endif // CONFIG_H
