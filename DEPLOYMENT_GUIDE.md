# IoT Gateway System Deployment Guide

This document provides complete deployment instructions for the IoT gateway system, including configuration and deployment of the Python gateway, Android app, and device units.

## 📋 Table of Contents

- [System Architecture](#system-architecture)
- [Environment Preparation](#environment-preparation)
- [Python Gateway Deployment](#python-gateway-deployment)
- [Android App Deployment](#android-app-deployment)
- [Device Unit Deployment](#device-unit-deployment)
- [System Testing](#system-testing)
- [Common Issues](#common-issues)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    IoT Gateway System Architecture          │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │   Android    │
                    │     App      │
                    │  (Port 9301) │
                    └──────┬───────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Python Gateway Server                          │
│                                                             │
│  ┌─────────────────────────────────────────────────┐        │
│  │  • Device Communication Module (Port 9300)      │        │
│  │  • Android Communication Module (Port 9301)     │        │
│  │  • Database Server Connection (Port 9302)       │        │
│  │  • Intelligent Decision Logic                   │        │
│  │  • Alibaba Cloud IoT Upload                     │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
        │               │               │
        ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  AC Unit    │  │Curtain Unit │  │  Door Unit  │
│ (A1_tem_hum)│  │(A1_curtain) │  │(A1_security)│
└─────────────┘  └─────────────┘  └─────────────┘
```

---

## Environment Preparation

### 1. Hardware Requirements

- **Server**: Computer or server running Python 3.8+
- **Network**: All devices on the same LAN
- **Device Units**:
  - ESP8266 development boards × 3 (AC, curtain, door security)
  - Sensor modules (DHT11 temperature/humidity, BH1750 light intensity, RFID reader)
  - Actuator modules (LED lights, servos, relays, etc.)
  - OLED display (optional, for local display)

### 2. Software Requirements

- **Python Gateway**: Python 3.8+, MySQL 8.0+, dependencies (see `Python/requirements.txt`)
- **Android App**: Android Studio, Android SDK API 21+, Android device API 21+
- **Device Units**: Arduino IDE 1.8+, ESP8266 board support package, required Arduino libraries

### 3. Python Dependency Installation

```bash
cd Python
pip install -r requirements.txt
```

Main dependencies:
```
paho-mqtt>=1.6.0
mysql-connector-python>=8.0.0
pyyaml>=5.4.0
```

---

## Python Gateway Deployment

### 1. Configure Gateway Parameters

Edit `Python/Gate/GateConfig.txt`:

```
192.168.1.107          # Gateway IP (local IP)
192.168.1.107          # Database server IP (usually same as gateway)
9300                   # Device unit communication port
9301                   # Android app communication port
9302                   # Database server communication port
root                   # MySQL username
1234                   # MySQL password
gate_database          # Database name
```

### 2. Configure User Information

Edit `Python/Gate/UserConfig.txt` (can be left empty for first deployment):

```
username
password
device_key
```

### 3. Initialize Database

```bash
cd "Database Server"
python database_process_server.py
```

### 4. Start Gateway

```bash
cd Python/Gate
python gate.py
```

Expected output:
```
INFO - Gateway configuration loaded successfully: Gateway IP=192.168.1.107, Device port=9300, Android port=9301
INFO - Database server connection successful: 192.168.1.107:9302
INFO - Device node communication port opened: 192.168.1.107:9300
INFO - Mobile app communication port opened: 192.168.1.107:9301
INFO - Thread 'sensor-listener' started
INFO - Thread 'android-listener' started
INFO - Thread 'aliyun-uploader' started
INFO - Gateway ready
```

### 5. Verify Gateway Operation

```bash
cd Python/scripts
python health_check.py
```

---

## Android App Deployment

### 1. Configure Gateway Connection

Edit `Android IoT APP/app/src/main/assets/config.properties`:

```
ip = 192.168.1.107    # Python gateway IP
port = 9301           # Android communication port (Note: 9301, not 3001)
```

⚠️ **Important**: Make sure the port is 9301, consistent with the Python gateway configuration!

### 2. Build APK

Using Android Studio:

1. Open project: `Android IoT APP`
2. Wait for Gradle sync to complete
3. Build → Generate Signed Bundle / APK
4. Select APK, create or select signing key
5. Select release build

Or use command line:

```bash
cd "Android IoT APP"
./gradlew assembleRelease
```

APK output location: `app/build/outputs/apk/release/app-release.apk`

### 3. Install on Device

```bash
adb install app/build/outputs/apk/release/app-release.apk
```

---

## Device Unit Deployment

### 1. Configuration Generation

**Method 1: Use Configuration Generator (Recommended)**

```bash
cd Python/scripts
python generate_device_config.py
```

**Method 2: Manual Configuration**

Edit `Device Unit code/config_template.h`, then rename to `config.h`:

```c
#define WIFI_SSID           "your_wifi_name"
#define WIFI_PASSWORD       "your_wifi_password"
#define GATEWAY_IP          "192.168.1.107"
#define GATEWAY_PORT        9300
#define DEVICE_ID           "A1_tem_hum"  // Modify based on device type
```

### 2. Arduino IDE Configuration

1. Install ESP8266 board support:
   - File → Preferences → Additional Boards Manager URLs
   - Add: `http://arduino.esp8266.com/stable/package_esp8266com_index.json`
   - Tools → Board → Boards Manager → Search "ESP8266" → Install

2. Install required libraries:
   - `Adafruit_SSD1306` (OLED display)
   - `Adafruit_GFX` (Graphics library)
   - `DHT_sensor_library` (Temperature/humidity sensor)
   - `BH1750` (Light intensity sensor)
   - `MFRC522` (RFID reader)
   - `ArduinoJson` (JSON processing)
   - `PubSubClient` (MQTT, for Alibaba Cloud)

3. Select board: Tools → Board → ESP8266 Boards → Generic ESP8266 Module

4. Configure upload parameters:
   - Flash Size: 4MB (FS:2MB OTA:~1019KB)
   - CPU Frequency: 80 MHz
   - Upload Speed: 115200

### 3. Upload Firmware

**AC Unit**: Open `Device Unit code/esp8266_airconditioner_unit/esp8266_airconditioner_unit.ino` in Arduino IDE and upload.

**Curtain Unit**: Open `Device Unit code/esp8266_curtain_unit/esp8266_curtain_unit.ino` and upload.

**Door Security Unit**: Open `Device Unit code/esp8266_doorsecurity_unit/esp8266_doorsecurity_unit.ino` and upload.

### 4. Verify Device Connection

After successful upload, check connection logs in the Python gateway console:

```
INFO - Device node connected: ('192.168.1.xxx', xxxxx)
INFO - Device node 'A1_tem_hum' connected to gateway
```

Device OLED should display:
```
T: 25.0
H: 60.0
S: 10
```

---

## System Testing

### 1. Unit Testing

**Python Gateway Testing**:
```bash
cd Python/Database Server
python -c "import database_process_server; print('OK')"
cd Gate
python gate.py
```

**Android App Testing**: Launch app, test login/registration, view sensor data.

**Device Unit Testing**: Observe OLED display, check Serial Monitor (baud rate 115200), verify sensor data upload.

### 2. Integration Testing

1. **Device → Gateway → Android**: Change environment near device, observe Android app updates
2. **Android → Gateway → Device**: Adjust thresholds in Android app, observe device control actions
3. **Database Sync**: Query historical data in MySQL
   ```sql
   USE gate_database;
   SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 10;
   ```

### 3. Stress Testing

```bash
python scripts/stress_test.py  # If available
top  # Linux/Mac - monitor resources
taskmgr  # Windows - monitor resources
```

---

## Common Issues

### Q1: Device Unit Cannot Connect to Gateway

**Symptom**: ESP8266 serial output shows "Connection failed"

**Causes & Solutions**:
- WiFi password incorrect → Check `config.h`
- Gateway IP incorrect → Confirm `GATEWAY_IP`
- Port incorrect → Confirm `GATEWAY_PORT = 9300`
- Firewall blocking → Check if port 9300 is open
- Gateway not started → Check if `gate.py` is running

### Q2: Android App Cannot Connect to Gateway

**Symptom**: Login shows "Connection failed"

**Causes & Solutions**:
- Port configuration incorrect → Confirm `port = 9301` in `config.properties`
- Gateway IP incorrect → Confirm IP address is correct
- Network unreachable → Check phone and gateway are on the same network
- Gateway not started → Check gateway logs

### Q3: Sensor Data Inaccurate

**Symptom**: Temperature/humidity/light values abnormal

**Causes & Solutions**:
- Sensor not calibrated → Refer to sensor documentation for calibration
- Wiring error → Check I2C/Wire connections
- Power unstable → Check 3.3V/5V power supply

### Q4: Device Control Not Responding

**Symptom**: No device action after Android sends command

**Causes & Solutions**:
- Threshold not triggered → Check intelligent decision logic
- Device ID incorrect → Confirm `DEVICE_ID` is correct
- JSON format error → Check serial monitor output

### Q5: Database Connection Failed

**Symptom**: "Database server connection failed" at gateway startup

**Causes & Solutions**:
- MySQL not started → Start MySQL service
- Password incorrect → Check `GateConfig.txt`
- Port incorrect → Confirm MySQL port is 3306
- Firewall blocking → Open port 9302

---

## Maintenance & Monitoring

### Log Viewing

**Gateway Logs**:
```bash
tail -f Python/Gate/gateway.log
grep ERROR Python/Gate/gateway.log
```

**Database Logs**:
```bash
tail -f Python/Database Server/database.log
```

### Backup

**Database Backup**:
```bash
mysqldump -u root -p gate_database > backup_$(date +%Y%m%d).sql
```

**Configuration Backup**:
```bash
tar -czf config_backup_$(date +%Y%m%d).tar.gz Python/Gate/*.txt
```

### Performance Monitoring

```bash
# View network connections
netstat -an | grep -E '9300|9301|9302'

# View process resources
ps aux | grep python
```

---

## Appendix

### A. Port Allocation

| Service | Port | Purpose |
|---------|------|---------|
| Device Unit Communication | 9300 | ESP8266 device connection |
| Android App | 9301 | Mobile app connection |
| Database Server | 9302 | Database process communication |
| MySQL | 3306 | Database connection |
| Alibaba Cloud MQTT | 1883 | IoT cloud platform |

### B. Device ID Mapping

| Device | Device ID | Function |
|--------|-----------|----------|
| Smart AC | A1_tem_hum | Temperature/humidity monitoring |
| Smart Curtain | A1_curtain | Light monitoring, curtain control |
| Smart Door | A1_security | Door access control |

### C. Data Field Description

| Field Name | Description | Unit |
|------------|-------------|------|
| Light_TH | AC light status | 0/1 |
| Temperature | Temperature | °C |
| Humidity | Humidity | % |
| Light_CU | Indoor light status | 0/1 |
| Brightness | Light intensity | Lux |
| Curtain_status | Curtain status | 0/1 |
| Door_Security_Status | Door security status | 0/1 |

---

## Technical Support

Having issues?

1. Run health check: `python scripts/health_check.py`
2. Check log files
3. Review common issues section
4. Contact technical support

---

**Document Version**: 1.0
**Last Updated**: 2026
**Maintainer**: IoT Development Team
