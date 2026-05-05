# IoT Smart Gateway System - Developer Documentation

**Version**: v1.0  
**Last Updated**: April 6, 2026  
**Scope**: Edge Computing IoT Gateway System

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Three-End Interaction Guide](#2-three-end-interaction-guide)
3. [Network Port Configuration](#3-network-port-configuration)
4. [Communication Protocol Details](#4-communication-protocol-details)
5. [Data Format and Codes](#5-data-format-and-codes)
6. [Database Server](#6-database-server)
7. [Startup Methods](#7-startup-methods)
8. [Development Guide](#8-development-guide)
9. [API Reference](#9-api-reference)
10. [Troubleshooting](#10-troubleshooting)
11. [Appendix](#11-appendix)

---

## 1. System Architecture Overview

### 1.1 System Components

The IoT Smart Gateway System consists of three main endpoints:

```
┌────────────────────────────────────────────────────────────────┐
│                  IoT Smart Gateway System Architecture         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────┐         ┌───────────────┐          ┌────────┐ │
│  │  Android    │◄────────┤  Edge Gateway │─────────►│ Device │ │
│  │  (Mobile)   │   TCP   │  (Python)     │   TCP    │ (ESP)  │ │
│  └─────────────┘         └───────────────┘          └────────┘ │
│         │                        │                       │     │
│         │                        │                       │     │
│         ▼                        ▼                       ▼     │
│  User Interface Control    Data Processing & Forward  Sensor   │
│  Threshold Settings        Smart Decision Logic       Device   │
│  Data Visualization        Data Storage               Control  │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              External Services                       │      │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │      │
│  │  │   MySQL     │  │ Alibaba IoT │  │  DB Server  │   │      │
│  │  │   Local DB  │  │   MQTT      │  │  (Remote)   │   │      │
│  │  └─────────────┘  └─────────────┘  └─────────────┘   │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Responsibilities of Each End

#### Android End (Mobile Application)
- **Responsibilities**:
  - User login and registration
  - Real-time display of sensor data
  - Send control commands to the gateway
  - Set sensor thresholds
  - Control device on/off states
- **Tech Stack**: Android (Java/Kotlin)
- **Configuration File**: `app/src/main/assets/config.properties`

#### Edge Gateway End (Python)
- **Responsibilities**:
  - Manage device connections and authentication
  - Receive sensor data and store it
  - Execute smart decision logic
  - Forward control commands to devices
  - Push data to Android and Alibaba Cloud IoT
  - Communicate with the database server
- **Tech Stack**: Python 3.x
- **Main Modules**: 
  - `gate.py` / `gate_test.py` (main program)
  - `sensor_handler.py` (device communication)
  - `android_handler.py` (Android communication)
  - `aliyun_handler.py` (Alibaba Cloud IoT communication)
  - `database.py` (local database operations)

#### Device End (ESP8266)
- **Responsibilities**:
  - Collect sensor data (temperature, humidity, light, etc.)
  - Send data to the gateway
  - Receive control commands
  - Execute device control (LEDs, relays, etc.)
- **Tech Stack**: Arduino C++ (ESP8266)
- **Device Types**:
  - `A1_tem_hum` - Smart AC Unit
  - `A1_curtain` - Smart Curtain Unit
  - `A1_security` - Door Security Unit

### 1.3 Data Flow

```
┌─────────┐
│ Device  │
│ ESP8266 │
└────┬────┘
     │ TCP:9300
     │ 1. Send device ID
     │ 2. Receive "start" response
     │ 3. Send sensor data (every 3s)
     │ 4. Receive control commands (every 3s)
     ▼
┌──────────────┐
│ Edge Gateway │
│   Python     │
└────┬───────┬─┘
     │       │
     │       │ TCP:9301
     │       │ 1. Send login request
     │       │ 2. Receive login response
     │       │ 3. Receive sensor data (every 2s)
     │       │ 4. Send control commands
     │       ▼
     │   ┌─────────┐
     │   │ Android │
     │   └─────────┘
     │
     │ MySQL (Local Storage)
     │ MQTT (Alibaba Cloud IoT)
     │ TCP:9302 (Database Server)
     ▼
┌──────────────────┐
│  External Layer  │
└──────────────────┘
```

---

## 2. Three-End Interaction Guide

### 2.1 Device End → Gateway End

#### Connection Establishment Flow

```
Device End (ESP8266)               Gateway End (Python)
      │                                  │
      │  1. TCP connection request       │
      │─────────────────────────────────►│
      │                                  │
      │  2. Send device ID + "\n"        │
      │─────────────────────────────────►│
      │   "A1_tem_hum\n"                 │
      │                                  │  3. Verify device permission
      │                                  │  (check allowed device list)
      │                                  │
      │  4. Receive response + "\n"      │
      │◄─────────────────────────────────│
      │   "start\n"                      │  Device authorized, start communication
      │                                  │
      │  5. Start bidirectional comm     │
      │    - Send sensor data (every 3s) │
      │    - Receive control commands    │
```

#### Device ID Verification Rules

- **Verification Condition**: Device ID must be in the allowed device list
- **Allowed Device List**: Retrieved from the database server (test mode uses default list)
- **Default Device List**: `["A1_tem_hum", "A1_curtain", "A1_security"]`
- **Verification Results**:
  - ✅ Pass: Send `"start\n"`, start bidirectional communication
  - ❌ Fail: Close connection, deny service

#### Sensor Data Transmission

**Transmission Frequency**: Every 3 seconds (configurable)  
**Data Format**: JSON object + "\n"

**Example Data**:
```json
{
  "device_id": "A1_tem_hum",
  "Light_TH": 0,
  "Temperature": 25.5,
  "Humidity": 60.5,
  "Light_CU": 0,
  "Brightness": 500.0,
  "Curtain_status": 1
}
```

**Data Field Description**:
| Field | Type | Description | Range |
|-------|------|-------------|-------|
| device_id | string | Device unique ID | - |
| Light_TH | int | AC light state | 0=Off, 1=On |
| Temperature | float | Temperature value | 0.0-100.0 |
| Humidity | float | Humidity value | 0.0-100.0 |
| Light_CU | int | Light sensor state | 0=Off, 1=On |
| Brightness | float | Brightness value | 0.0-65535.0 |
| Curtain_status | int | Curtain state | 0=Closed, 1=Open |

#### Control Command Reception

**Reception Frequency**: Every 3 seconds (configurable)  
**Data Format**: JSON object + "\n"

**Example Data**:
```json
{
  "Light_TH": 1,
  "Temperature": -1,
  "Humidity": -1,
  "Light_CU": 0,
  "Brightness": 500.0,
  "Curtain_status": 1
}
```

**Device Response**: 
- Parse JSON data
- Update local control variables
- Execute device control (e.g., LED on/off)

---

### 2.2 Android End → Gateway End

#### Connection Establishment Flow

```
Android End                           Gateway End
     │                                  │
     │  1. TCP connection request       │
     │─────────────────────────────────►│
     │                                  │
     │  2. Send login request (JSON)    │
     │─────────────────────────────────►│
     │   {                              │
     │     "op": "login",               │
     │     "data": {                    │
     │       "account": "Jiang",        │
     │       "password": "pwd",         │
     │       "device_Key": "A1"         │
     │     },                           │
     │     "status": "1"                │
     │   }                              │
     │                                  │  3. Verify user credentials
     │                                  │  (check UserConfig.txt)
     │                                  │
     │  4. Receive login response       │
     │◄─────────────────────────────────│
     │   {                              │  Login successful
     │     "status": 1                  │  status=1
     │   }                              │
     │                                  │
     │  5. Wait for device connection   │
     │  (wait for sensor_data to be     │
     │   available)                     │
     │                                  │  6. Start bidirectional comm
     │  7. Receive sensor data (every 2s)│
     │◄─────────────────────────────────│
     │                                  │  Push data snapshot
     │  8. Send control command         │
     │─────────────────────────────────►│
     │   {                              │
     │     "op": "light_th_open",       │
     │     "data": "1",                 │
     │     "status": "1"                │
     │   }                              │
     │                                  │  9. Update threshold data
     │                                  │  10. Push new threshold to device
```

#### User Login

**Request Format**:
```json
{
  "op": "login",
  "data": {
    "account": "username",
    "password": "password",
    "device_Key": "device_key"
  },
  "status": "1"
}
```

**Response Format**:
```json
{
  "status": 1
}
```

**Response Codes**:
| status | Description |
|--------|-------------|
| 1 | Login successful |
| 0 | Login failed (incorrect username or password) |

#### User Registration

**Request Format**:
```json
{
  "op": "register",
  "data": {
    "account": "username",
    "password": "password",
    "device_Key": "device_key"
  },
  "status": "1"
}
```

**Response Format**:
```json
{
  "status": 1
}
```

**Registration Flow**:
1. Gateway receives registration request
2. Forward to database server
3. Database server creates user record
4. Gateway updates local UserConfig.txt
5. Return response to Android

#### Sensor Data Reception

**Reception Frequency**: Every 2 seconds (configurable)  
**Data Format**: JSON object + "\n"

**Example Data**:
```json
{
  "Light_TH": 0,
  "Temperature": 25.5,
  "Humidity": 60.5,
  "Light_CU": 0,
  "Brightness": 500.0,
  "Curtain_status": 1
}
```

**Android Processing**:
- Parse JSON data
- Update UI display
- Draw real-time charts
- Display device status

#### Control Command Transmission

**Command Format**:
```json
{
  "op": "operation_code",
  "data": "data_value",
  "status": "1"
}
```

**Supported Commands**:
| Operation Code | Data Value | Description |
|----------------|------------|-------------|
| light_th_open | "1" | Turn on smart AC |
| light_th_close | "1" | Turn off smart AC |
| change_temperature_threshold | "28" | Modify temperature threshold |
| change_humidity_threshold | "60" | Modify humidity threshold |
| curtain_open | "1" | Open curtains |
| curtain_close | "1" | Close curtains |
| change_brightness_threshold | "500" | Modify brightness threshold |

---

### 2.3 Gateway End → Database Server

#### Connection Establishment Flow

```
Gateway End                       Database Server
     │                                  │
     │  1. TCP connection (port 9302)   │
     │─────────────────────────────────►│
     │                                  │
     │  2. Connection established       │
     │                                  │
     │  3. Send request (JSON)          │
     │─────────────────────────────────►│
     │   {                              │
     │     "op": "check_device_id",     │
     │     "data": "A1",                │
     │     "status": 1                  │
     │   }                              │
     │                                  │  4. Process request
     │                                  │  (query database)
     │                                  │
     │  5. Receive response (JSON)      │
     │◄─────────────────────────────────│
     │   {                              │
     │     "op": "check_device_id",     │
     │     "data": ["A1_tem_hum",...],  │
     │     "status": 1                  │
     │   }                              │
```

#### Supported Operations

| Operation Code | Description | Request Data | Response Data |
|----------------|-------------|--------------|---------------|
| check_device_id | Get allowed device list | device_key | Device ID array |
| check_userconfig_illegal | Check user config | {"username":...} | Corrected user info |
| add_new_user | Add new user | {"username":...} | status: 1=success, 0=fail, 2=error |

---

## 3. Network Port Configuration

### 3.1 Port Allocation Table

| Port | Usage | Protocol | Description |
|------|-------|----------|-------------|
| **9300** | Device communication | TCP | ESP8266 device connection |
| **9301** | Android communication | TCP | Android app connection |
| **9302** | Database server | TCP | Database server communication |
| **1883** | Alibaba Cloud IoT MQTT | TCP | MQTT protocol communication |
| **3306** | MySQL database | TCP | Local database |

### 3.2 Configuration Files

#### Gateway Configuration File (GateConfig.txt)

**Location**: `Python/Gate/GateConfig.txt`  
**Format**: Plain text, one configuration item per line

```
Gateway IP
Database Server IP
Device Port
Android Port
Database Server Port
MySQL Username
MySQL Password
Database Name
```

**Example**:
```
192.168.1.107
192.168.1.107
9300
9301
9302
root
1234
gate_database
```

#### User Configuration File (UserConfig.txt)

**Location**: `Python/Gate/UserConfig.txt`  
**Format**: Plain text, one configuration item per line

```
Username
Password
Device Key
```

**Example**:
```
Jiang
pwd
A1
```

#### Android Configuration File (config.properties)

**Location**: `Android IoT APP/app/src/main/assets/config.properties`  
**Format**: key=value format

```properties
ip = 192.168.1.107
port = 9301
```

#### Device Configuration File (config.h)

**Location**: `Device Unit code/*/config.h`  
**Format**: C++ Macro Definition

```cpp
#define DEVICE_ID "A1_tem_hum"
#define GATEWAY_IP "192.168.1.107"
#define GATEWAY_PORT 9300
#define WIFI_SSID "your_wifi_ssid"
#define WIFI_PASSWORD "your_wifi_password"
```

### 3.3 Configuration Generation Tool

**Tool**: `Python/scripts/generate_device_config.py`

**Purpose**: Automatically generate device configuration files

**Usage**:
```bash
cd "d:\projects\ai_generate\edge computing home"
python Python/scripts/generate_device_config.py
```

---

## 4. Communication Protocol Details

### 4.1 Protocol Overview

All TCP communication uniformly uses **JSON format**, with messages delimited by **`\n` (LF)**.

#### Message Format

**Type 1: Command/Response Messages**
```json
{
  "op": "operation_code",
  "data": "data_payload",
  "status": "status_code"
}
```

**Type 2: Data Stream Push Messages**
```json
{
  "field1": "value1",
  "field2": "value2",
  ...
}
```

### 4.2 Message Terminator

**Terminator**: `\n` (Line Feed, ASCII 10)  
**Purpose**: Separate independent messages  
**Handling**: 
- Automatically append `\n` when sending
- Read until `\n` when receiving

### 4.3 JSON Encoding Specifications

#### Character Encoding
- **Encoding Format**: UTF-8
- **Unicode Characters**: Allowed, serialize with `ensure_ascii=False`

#### Data Type Mapping

| JSON Type | Python Type | Description |
|-----------|-------------|-------------|
| string | str | Text string |
| number | int/float | Numeric value |
| boolean | bool | Boolean value |
| array | list | Array |
| object | dict | Object |

### 4.4 Communication Function Library

#### Python End (common/protocol.py)

**Send JSON Data**:
```python
from common.protocol import send_json

send_json(socket, {"key": "value"})
# Actually sends: {"key": "value"}\n
```

**Receive JSON Data**:
```python
from common.protocol import recv_json

data = recv_json(socket)
# Returns: {"key": "value"}
```

**Send Text Line**:
```python
from common.protocol import send_line

send_line(socket, "start")
# Actually sends: start\n
```

**Receive Text Line**:
```python
from common.protocol import recv_line

line = recv_line(socket)
# Returns: "start"
```

#### Device Side (ESP8266)

**Send JSON Data**:
```cpp
#include <ArduinoJson.h>

StaticJsonDocument<200> doc;
doc["device_id"] = "A1_tem_hum";
doc["Temperature"] = 25.5;

String jsonStr;
serializeJson(doc, jsonStr);
client.println(jsonStr);  // Auto-appends \n
```

**Receive JSON Data**:
```cpp
StaticJsonDocument<200> doc;
String jsonStr = client.readStringUntil('\n');

deserializeJson(doc, jsonStr);
int temperature = doc["Temperature"];
```

#### Android Side (Java)

**Send JSON Data**:
```java
JSONObject json = new JSONObject();
json.put("op", "login");
json.put("data", userData);

String jsonString = json.toString();
outputStream.write((jsonString + "\n").getBytes());
```

**Receive JSON Data**:
```java
BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream));
String line = reader.readLine();  // Reads until \n

JSONObject json = new JSONObject(line);
String status = json.getString("status");
```

---

## 5. Data Format and Codes

### 5.1 Operation Code (op) List

#### Android → Gateway

| Operation Code | Purpose | data Type | status |
|----------------|---------|-----------|--------|
| login | User login | JSONObject | "1" |
| register | User registration | JSONObject | "1" |
| light_th_open | Turn on AC | "1" | "1" |
| light_th_close | Turn off AC | "1" | "1" |
| change_temperature_threshold | Change temperature threshold | "28" | "1" |
| change_humidity_threshold | Change humidity threshold | "60" | "1" |
| curtain_open | Open curtain | "1" | "1" |
| curtain_close | Close curtain | "1" | "1" |
| change_brightness_threshold | Change brightness threshold | "500" | "1" |

#### Gateway → Database Server

| Operation Code | Purpose | data Type | status |
|----------------|---------|-----------|--------|
| check_device_id | Get allowed device list | "A1" | 1 |
| check_userconfig_illegal | Check user configuration | JSONObject | 1 |
| add_new_user | Add new user | JSONObject | 1 |

### 5.2 Data Field Descriptions

#### Sensor Data Fields

| Field Name | Type | Description | Default | Range |
|------------|------|-------------|---------|-------|
| Light_TH | int | Smart AC light status | 0 | 0=Off, 1=On |
| Temperature | float | Temperature value | 0.0 | 0.0-100.0 (°C) |
| Humidity | float | Humidity value | 0.0 | 0.0-100.0 (%) |
| Light_CU | int | Light sensor status | 0 | 0=Off, 1=On |
| Brightness | float | Brightness level | 0.0 | 0.0-65535.0 |
| Curtain_status | int | Curtain status | 1 | 0=Closed, 1=Open |

#### Access Control Data Fields

| Field Name | Type | Description | Default | Range |
|------------|------|-------------|---------|-------|
| Door_Security_Status | int | Door status | 0 | 0=Denied, 1=Granted |
| Door_Secur_Card_id | string | Card ID | "" | - |

#### Threshold Data Fields

| Field Name | Type | Description | Default | Special Values |
|------------|------|-------------|---------|---------------|
| Temperature | float | Temperature threshold | 30.0 | -1=Unlimited |
| Humidity | float | Humidity threshold | 65.0 | -1=Unlimited |
| Brightness | float | Brightness threshold | 500.0 | -2=Unlimited, 65535=No Trigger |

### 5.3 Status Code Explanation

#### Common Status Codes

| Value | Description | Usage Scenario |
|-------|-------------|----------------|
| 0 | Failure | Login failure, registration failure, data format error |
| 1 | Success | Operation successful, data correct |
| 2 | Error | Database server error, exception |

#### Access Control Status Codes

| Value | Description | Constant |
|-------|-------------|----------|
| 0 | Denied | `DOOR_DENIED` |
| 1 | Granted | `DOOR_GRANTED` |

### 5.4 Data Examples

#### Login Request Example

**Request**:
```json
{
  "op": "login",
  "data": {
    "account": "Jiang",
    "password": "pwd",
    "device_Key": "A1"
  },
  "status": "1"
}
```

**Response**:
```json
{
  "status": 1
}
```

#### Sensor Data Example

**Device Sends**:
```json
{
  "device_id": "A1_tem_hum",
  "Light_TH": 0,
  "Temperature": 25.5,
  "Humidity": 60.5,
  "Light_CU": 0,
  "Brightness": 500.0,
  "Curtain_status": 1
}
```

**Gateway Storage** (MySQL):
```sql
INSERT INTO gate_local_data 
(timestamp, light_th, temperature, humidity, light_cu, brightness, curtain_status)
VALUES 
('2026-04-06 13:16:23', 0, 25.5, 60.5, 0, 500.0, 1);
```

#### Control Command Example

**Android Sends**:
```json
{
  "op": "light_th_open",
  "data": "1",
  "status": "1"
}
```

**Gateway Processing**:
```python
# Update thresholds
state.set_threshold(FIELD_TEMPERATURE, -1)
state.set_threshold(FIELD_HUMIDITY, -1)

# Push to device
# Device receives:
{
  "Light_TH": 1,
  "Temperature": -1,
  "Humidity": -1,
  ...
}
```

#### Intelligent Decision Example

**Trigger Condition**:
```
Temperature = 31.5 >= Threshold = 30.0
Humidity = 68.0 >= Threshold = 65.0
```

**Decision Result**:
```json
{
  "Light_TH": 1,  // Turn on AC
  "Temperature": 31.5,
  "Humidity": 68.0,
  ...
}
```

---

## 6. Database Server

### 6.1 Server Overview

The database server is the central data management component of the system, responsible for:
- User registration and authentication
- User configuration validation and correction
- Device key management
- Device list querying
- Remote data persistence

**Tech Stack**: Python + MySQL  
**Communication Protocol**: TCP (Port 9302)  
**Data Format**: JSON

### 6.2 Server Architecture

```
┌───────────────────────────────────────────────────────────┐
│                   Database Server Architecture              │
├───────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐      ┌──────────────┐              │
│  │  Gateway     │◄─────│  DB Server   │              │
│  │  (Python)    │ TCP   │ (Python)     │              │
│  └──────────────┘ 9302  └──────┬───────┘              │
│                               │                        │
│                               │ MySQL                  │
│                               ▼                        │
│                      ┌───────────────┐                │
│                      │  MySQL DB     │                │
│                      │  (user_test)  │                │
│                      └───────┬───────┘                │
│                              │                        │
│          ┌───────────────────┼───────────────────┐    │
│          ▼                   ▼                   ▼    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │  users_data │    │  device_key │    │ device_data │ │
│  │  User Table │    │  Key Table  │    │ Device Table│ │
│  └─────────────┘    └─────────────┘    └─────────────┘ │
│                                                          │
└───────────────────────────────────────────────────────────┘
```

### 6.3 Database Table Structure

#### users_data - User Data Table

Stores user account information and associated device keys.

| Field Name | Type | Description | Constraint |
|------------|------|-------------|------------|
| username | VARCHAR(50) | Username | PRIMARY KEY |
| password | VARCHAR(100) | Password | NOT NULL |
| owned_device_key | VARCHAR(50) | Owned device key | UNIQUE KEY |

**SQL Creation Statement**:
```sql
CREATE TABLE IF NOT EXISTS `users_data` (
  `username` VARCHAR(50) NOT NULL,
  `password` VARCHAR(100) NOT NULL,
  `owned_device_key` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`username`),
  UNIQUE KEY `owned_device_key` (`owned_device_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### device_key - Device Key Table

Stores device key allocation and usage status.

| Field Name | Type | Description | Constraint |
|------------|------|-------------|------------|
| key_id | VARCHAR(50) | Key ID | PRIMARY KEY |
| owned_by_user | VARCHAR(50) | Owning user | DEFAULT NULL |
| is_used | TINYINT(1) | Whether used | DEFAULT 0 |

**SQL Creation Statement**:
```sql
CREATE TABLE IF NOT EXISTS `device_key` (
  `key_id` VARCHAR(50) NOT NULL,
  `owned_by_user` VARCHAR(50) DEFAULT NULL,
  `is_used` TINYINT(1) DEFAULT 0,
  PRIMARY KEY (`key_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### device_data - Device Data Table

Stores device names and bound keys.

| Field Name | Type | Description | Constraint |
|------------|------|-------------|------------|
| device_name | VARCHAR(50) | Device name | PRIMARY KEY |
| bind_device_key | VARCHAR(50) | Bound key | NOT NULL |

**SQL Creation Statement**:
```sql
CREATE TABLE IF NOT EXISTS `device_data` (
  `device_name` VARCHAR(50) NOT NULL,
  `bind_device_key` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`device_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 6.4 Communication Protocol

#### Connection Flow

```
Gateway                         Database Server
     │                                  │
     │  1. TCP Connection Request (Port 9302)  │
     │─────────────────────────────────►│
     │                                  │  2. Accept Connection
     │                                  │     Create Dedicated Thread
     │                                  │
     │  3. Send Request (JSON)          │
     │─────────────────────────────────►│
     │   {                              │
     │     "op": "check_device_id",      │  4. Parse Request
     │     "data": "A1",               │     Identify Operation Code
     │     "status": 1                  │
     │   }                              │
     │                                  │  5. Execute SQL Query
     │                                  │     SELECT ...
     │                                  │
     │  6. Receive Response (JSON)      │
     │◄─────────────────────────────────│
     │   {                              │  6. Build Response
     │     "op": "check_device_id",     │     Query Result
     │     "data": ["A1_tem_hum",...],   │
     │     "status": 1                  │
     │   }                              │
     │                                  │
     │  7. Continue Sending Next Request... │
     │─────────────────────────────────►│
```

#### Message Format

**Request Format**:
```json
{
  "op": "operation_code",
  "data": "data_payload",
  "status": 1
}
```

**Response Format**:
```json
{
  "op": "operation_code",
  "data": "response_data",
  "status": 1
}
```

#### Communication Features

- **Protocol**: TCP
- **Port**: 9302
- **Message Format**: JSON
- **Delimiter**: `\n` (Line Feed)
- **Encoding**: UTF-8
- **Concurrency**: Multi-threaded, each gateway connection has its own thread

### 6.5 Operation Code Details

#### 6.5.1 check_device_id - Query Device List

**Purpose**: Query all device names bound to a given device key

**Request Example**:
```json
{
  "op": "check_device_id",
  "data": "A1",
  "status": 1
}
```

**Request Parameters**:
| Field Name | Type | Description |
|------------|------|-------------|
| op | string | Fixed value: "check_device_id" |
| data | string | Device key (e.g., "A1") |
| status | int | Fixed value: 1 |

**SQL Query**:
```sql
SELECT device_name FROM device_data WHERE bind_device_key = %s
```

**Response Example** (Success):
```json
{
  "op": "check_device_id",
  "data": ["A1_tem_hum", "A1_curtain", "A1_security"],
  "status": 1
}
```

**Response Example** (Failure):
```json
{
  "op": "check_device_id",
  "data": "Device key does not exist",
  "status": 0
}
```

**Response Codes**:
| status | Description |
|--------|-------------|
| 1 | Query successful, returns device list |
| 0 | Query failed, returns error message |
| 2 | Database exception |

**Use Cases**:
- Gateway retrieves allowed device list on startup
- User retrieves owned devices on login
- Query device ownership during device management

#### 6.5.2 check_userconfig_illegal - User Configuration Validation

**Purpose**: Validate whether the gateway's local user configuration is legal, and attempt to correct it if abnormal

**Request Example**:
```json
{
  "op": "check_userconfig_illegal",
  "data": {
    "username": "Jiang",
    "password": "pwd",
    "device_key": "A1"
  },
  "status": 1
}
```

**Request Parameters**:
| Field Name | Type | Description |
|------------|------|-------------|
| op | string | Fixed value: "check_userconfig_illegal" |
| data | object | User info object |
| data.username | string | Username |
| data.password | string | Password |
| data.device_key | string | Device key |
| status | int | Fixed value: 1 |

**SQL Query**:
```sql
SELECT * FROM users_data 
WHERE username = %s AND password = %s AND owned_device_key = %s
```

**Response Example 1** (Valid Configuration):
```json
{
  "op": "check_userconfig_illegal",
  "data": "NULL",
  "status": 1
}
```

**Response Example 2** (Abnormal, Corrected):
```json
{
  "op": "check_userconfig_illegal",
  "data": {
    "username": "Jiang",
    "password": "correct_pwd",
    "device_key": "A1"
  },
  "status": 1
}
```

**Response Example 3** (User Not Registered):
```json
{
  "op": "check_userconfig_illegal",
  "data": "NULL",
  "status": 0
}
```

**Response Codes**:
| status | Description | Follow-up Action |
|--------|-------------|------------------|
| 1 | Config valid or corrected | Gateway updates config |
| 0 | Config invalid, cannot correct | Gateway logs warning |
| 2 | Database exception | Gateway logs error |

**Processing Flow**:
```
1. Receive user configuration
   ↓
2. Query database for validation
   ↓
3a. Config matches → Return status=1
   ↓
3b. Config mismatch → Return status=0
   ↓
4. Attempt correction: query by username
   ↓
5a. User found → Return correct config (status=1)
   ↓
5b. User not found → Return status=0
```

#### 6.5.3 add_new_user - Add New User

**Purpose**: Register a new user and associate a device key

**Request Example**:
```json
{
  "op": "add_new_user",
  "data": {
    "username": "test_user",
    "password": "test_password",
    "device_key": "A2"
  },
  "status": 1
}
```

**Request Parameters**:
| Field Name | Type | Description |
|------------|------|-------------|
| op | string | Fixed value: "add_new_user" |
| data | object | User info object |
| data.username | string | Username |
| data.password | string | Password |
| data.device_key | string | Device key |
| status | int | Fixed value: 1 |

**SQL Operations** (Transaction):
```sql
-- 1. Insert user data
INSERT INTO users_data (username, password, owned_device_key) 
VALUES (%s, %s, %s);

-- 2. Update device key ownership
UPDATE device_key SET owned_by_user = %s WHERE key_id = %s;

-- 3. Mark key as used
UPDATE device_key SET is_used = 1 WHERE owned_by_user = %s;
```

**Response Example** (Success):
```json
{
  "op": "add_new_user",
  "data": "NULL",
  "status": 1
}
```

**Response Example** (Failure - User Already Exists):
```json
{
  "op": "add_new_user",
  "data": "NULL",
  "status": 0
}
```

**Response Example** (Database Exception):
```json
{
  "op": "add_new_user",
  "data": "Duplicate entry 'test_user' for key 'PRIMARY'",
  "status": 2
}
```

**Response Codes**:
| status | Description |
|--------|-------------|
| 1 | User added successfully |
| 0 | User addition failed (primary key or unique key conflict) |
| 2 | Database exception, returns error message |

**Transaction Handling**:
```python
try:
    cursor.execute(sql1, (username, password, device_key))
    cursor.execute(sql2, (username, device_key))
    cursor.execute(sql3, (username,))
    db.commit()  # Commit transaction
except Exception:
    db.rollback()  # Rollback transaction
```

### 6.6 Various Case Handling

#### Case 1: Gateway Configuration Correct

**Scenario**: Gateway's `UserConfig.txt` matches the database

**Request**:
```json
{
  "op": "check_userconfig_illegal",
  "data": {"username": "Jiang", "password": "pwd", "device_key": "A1"},
  "status": 1
}
```

**Response**:
```json
{
  "op": "check_userconfig_illegal",
  "data": "NULL",
  "status": 1
}
```

**Gateway Behavior**: Configuration valid, continue running

---

#### Case 2: Incorrect Gateway Password

**Scenario**: User modified the password in the gateway configuration file

**Request**:
```json
{
  "op": "check_userconfig_illegal",
  "data": {"username": "Jiang", "password": "wrong_pwd", "device_key": "A1"},
  "status": 1
}
```

**First Response**:
```json
{
  "op": "check_userconfig_illegal",
  "data": "NULL",
  "status": 0
}
```

**Correction Request**: Query database by username

**Correction Response**:
```json
{
  "op": "check_userconfig_illegal",
  "data": {"username": "Jiang", "password": "pwd", "device_key": "A1"},
  "status": 1
}
```

**Gateway Behavior**: 
1. Receives status=0, logs warning
2. Receives correct configuration, updates `UserConfig.txt`
3. Restarts gateway or reloads configuration

---

#### Case 3: User Not Registered

**Scenario**: New gateway or user has been deleted

**Request**:
```json
{
  "op": "check_userconfig_illegal",
  "data": {"username": "new_user", "password": "pwd", "device_key": "A1"},
  "status": 1
}
```

**First Response**:
```json
{
  "op": "check_userconfig_illegal",
  "data": "NULL",
  "status": 0
}
```

**Correction Attempt**: Query by username

**Correction Response**:
```json
{
  "op": "check_userconfig_illegal",
  "data": "NULL",
  "status": 0
}
```

**Gateway Behavior**: 
1. Logs error
2. Denies service
3. Prompts user to register first

---

#### Case 4: Device Key Does Not Exist

**Scenario**: Querying a non-existent device key

**Request**:
```json
{
  "op": "check_device_id",
  "data": "A99",
  "status": 1
}
```

**Response**:
```json
{
  "op": "check_device_id",
  "data": [],
  "status": 1
}
```

**Gateway Behavior**: 
1. Returns empty list
2. Logs: No devices found
3. Gateway cannot connect to any device

---

#### Case 5: User Already Exists

**Scenario**: Attempting to register with an existing username

**Request**:
```json
{
  "op": "add_new_user",
  "data": {"username": "Jiang", "password": "new_pwd", "device_key": "A2"},
  "status": 1
}
```

**Response**:
```json
{
  "op": "add_new_user",
  "data": "NULL",
  "status": 0
}
```

**Gateway Behavior**: 
1. Receives status=0
2. Returns registration failure message to Android
3. Prompts user: Username already exists

---

#### Case 6: Device Key Already In Use

**Scenario**: Attempting to register with an already assigned key

**Request**:
```json
{
  "op": "add_new_user",
  "data": {"username": "new_user", "password": "pwd", "device_key": "A1"},
  "status": 1
}
```

**Response**:
```json
{
  "op": "add_new_user",
  "data": "NULL",
  "status": 0
}
```

**Gateway Behavior**: 
1. Receives status=0
2. Returns registration failure message to Android
3. Prompts user: Device key already in use

---

#### Case 7: Database Connection Failure

**Scenario**: MySQL service is not started or network is interrupted

**Request**: Send any request

**Response**: No response (connection timeout)

**Gateway Behavior**: 
1. Catches connection exception
2. Logs error
3. Production mode: Exits program
4. Test mode: Continues running, uses default configuration

---

#### Case 8: Database Query Exception

**Scenario**: SQL syntax error or table does not exist

**Request**:
```json
{
  "op": "check_device_id",
  "data": "A1",
  "status": 1
}
```

**Response**:
```json
{
  "op": "check_device_id",
  "data": "Table 'user_test.device_data' doesn't exist",
  "status": 0
}
```

**Gateway Behavior**: 
1. Receives status=0
2. Logs error message and stack trace
3. Returns empty list or error prompt

---

### 6.7 Configuration Files

#### serverConfig.txt

**Location**: `Python/Database Server/serverConfig.txt`

**Format**:
```
<Listen IP>
<Listen Port>
```

**Example**:
```
0.0.0.0
9302
```

**Configuration Notes**:
- **Listen IP**: 
  - `0.0.0.0`: Listen on all network interfaces (recommended)
  - `127.0.0.1`: Local access only
  - `192.168.x.x`: Specify IP (only valid when the IP exists)
- **Listen Port**: 9302 (default)

**Important Notes**:
- ⚠️ Do not use a non-existent IP address (e.g., `192.168.1.107` may not exist locally)
- ⚠️ Port 9302 must not be occupied
- ⚠️ Restart the server after modifying the configuration

### 6.8 Starting the Database Server

#### Method 1: Direct Start

```bash
cd "d:\projects\ai_generate\edge computing home\Python\Database Server"
python database_process_server.py
```

#### Method 2: Using Test Script

```bash
cd "d:\projects\ai_generate\edge computing home"
python Python/scripts/test_database_server.py
```

#### Method 3: Running in Background

**Windows**:
```bash
start /B python database_process_server.py > server.log 2>&1
```

**Linux/Mac**:
```bash
nohup python database_process_server.py > server.log 2>&1 &
```

### 6.9 Database Initialization

#### Initialize Database and Tables

```bash
mysql -u root -p1234 < Python/Database\ Server/init_database.sql
```

#### Manual Initialization

```sql
-- Create database
CREATE DATABASE IF NOT EXISTS `user_test` 
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `user_test`;

-- Create tables (see Section 6.3)

-- Insert sample data
INSERT INTO users_data (username, password, owned_device_key)
VALUES ('Jiang', 'pwd', 'A1');
```

### 6.10 Test Tools

#### Test Script

**Location**: `Python/scripts/test_database_server.py`

**Features**:
- Test database connection
- Start database server
- Test server connection
- Test device list query
- Test user configuration validation
- Test adding new user

**Run Tests**:
```bash
python Python/scripts/test_database_server.py
```

**Expected Output**:
```
============================================================
Database Server and Gateway Connection Test
============================================================

============================================================
Test 1: Database Connection
============================================================
✓ Database 'user_test' exists
✓ Found 3 tables:
  - device_data
  - device_key
  - users_data

============================================================
Test 2: Start Database Server
============================================================
✓ Configuration loaded successfully:
  - Server IP: 0.0.0.0
  - Listen Port: 9302
✓ Database server started successfully

============================================================
Test Results Summary
============================================================
Database Connection: ✓ Passed
Server Startup: ✓ Passed
Server Connection: ✓ Passed
Device List Query: ✓ Passed
User Config Validation: ✓ Passed
Add New User: ✓ Passed

✅ Core tests passed! Database server is running normally
```

### 6.11 Logs and Debugging

#### Log Files

**Location**: `Python/Database Server/serverLogs.log`

**Log Format**:
```
[2026-04-06 13:37:10,805][INFO][__main__][database_process_server.py:60] Database connection successful
[2026-04-06 13:37:11,123][INFO][__main__][database_process_server.py:78] Gateway ('192.168.1.108', 54321) connected
[2026-04-06 13:37:11,456][INFO][__main__][database_process_server.py:104] Processing check_device_id request
[2026-04-06 13:37:11,457][INFO][__main__][database_process_server.py:238] Found 3 devices
```

#### Log Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| DEBUG | Debug information | Development debugging |
| INFO | General information | Normal operation |
| WARNING | Warning information | Configuration anomaly |
| ERROR | Error information | Operation failure |

#### Debugging Tips

**1. View real-time logs**:
```bash
tail -f Python/Database\ Server/serverLogs.log
```

**2. Check database connection**:
```python
import mysql.connector
conn = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="1234",
    database="user_test"
)
print("Connection successful")
```

**3. Test SQL query**:
```bash
mysql -u root -p1234 user_test -e "SELECT * FROM users_data;"
```

### 6.12 Frequently Asked Questions

#### Q1: Database Server Cannot Start

**Symptoms**: `OSError: [WinError 10049] The requested address is not valid in its context`

**Cause**: The listening IP does not exist or is unavailable

**Solution**:
```bash
# Modify serverConfig.txt
# Change 192.168.1.107 to 0.0.0.0
```

#### Q2: Gateway Cannot Connect to Database Server

**Symptoms**: Connection timeout or connection refused

**Causes**: 
1. Server not started
2. Incorrect IP address configuration
3. Firewall blocking

**Solution**:
```bash
# 1. Check if the server is running
netstat -ano | findstr "9302"

# 2. Test port connectivity
telnet 127.0.0.1 9302

# 3. Check firewall (Windows)
netsh advfirewall firewall show rule name=all
```

#### Q3: Database Connection Failed

**Symptoms**: `mysql.connector.Error: Access denied for user`

**Cause**: Incorrect username or password

**Solution**:
```bash
# Test connection
mysql -u root -p1234

# Modify configuration
# Ensure user_test database exists
# Ensure root user password is 1234
```

---

## 7. Startup Guide

### 7.1 Environment Requirements

#### Python Environment
- **Python Version**: 3.7+
- **Dependencies**:
  ```bash
  pip install -r requirements.txt
  ```

**requirements.txt**:
```
mysql-connector-python
aliyun-iot-linkkit
```

#### MySQL Environment
- **MySQL Version**: 5.7+
- **Database**: gate_database
- **User Privileges**: CREATE, INSERT, SELECT

#### ESP8266 Environment
- **IDE**: Arduino IDE
- **Board**: ESP8266 (NodeMCU/Wemos)
- **Required Libraries**:
  - ESP8266WiFi
  - ArduinoJson
  - DHT_sensor_library
  - Adafruit_SSD1306
  - Adafruit_GFX

#### Android Environment
- **Android Studio**: 4.0+
- **Min SDK Version**: API 21 (Android 5.0)
- **Target SDK Version**: API 33 (Android 13)

### 7.2 Gateway Startup

#### Production Mode

```bash
cd "d:\projects\ai_generate\edge computing home\Python\Gate"
python gate.py
```

**Production mode features**:
- Connects to the database server
- Validates user configuration
- Retrieves the allowed device list
- All features fully enabled

#### Test Mode

```bash
cd "d:\projects\ai_generate\edge computing home\Python\Gate"
python gate_test.py --test
```

**Test mode features**:
- ⚠️ Skips database server connection
- Uses default device list
- Skips user configuration validation
- Suitable for development and testing

**Environment variable method**:
```bash
# Windows
set TEST_MODE=true
python gate.py

# Linux/Mac
export TEST_MODE=true
python gate.py
```

#### Running in Background

**Windows**:
```bash
start /B python gate.py > gateway.log 2>&1
```

**Linux/Mac**:
```bash
nohup python gate.py > gateway.log 2>&1 &
```

### 7.3 Device Startup

#### Uploading Firmware to ESP8266

1. **Configure device parameters**
   - Copy `config_template.h` to `config.h`
   - Modify WiFi credentials
   - Update the gateway IP and port

2. **Upload via Arduino IDE**
   - Open the `.ino` file
   - Select board: NodeMCU 1.0
   - Select port: COMx
   - Click the upload button

3. **Monitor Serial Output**
   - Baud rate: 115200
   - Observe connection status
   - Confirm successful gateway connection

#### Auto-Start

**Devices start automatically on power-up**:
1. Connect to WiFi
2. Connect to the gateway
3. Send device ID
4. Begin data communication

### 7.4 Android App Startup

#### Development Environment Setup

1. **Open Android Studio**
2. **Import Project**: `Android IoT APP`
3. **Configure Network**: Ensure `app/src/main/assets/config.properties` is correctly set
4. **Run the App**: Click the run button

#### Installing APK

1. **Build APK**
   - Build > Generate Signed Bundle / APK
   - Select APK
   - Choose debug or release

2. **Install to Device**
   ```bash
   adb install app-release.apk
   ```

3. **Configure Gateway Address**
   - Open the app
   - Enter gateway IP and port
   - Click connect

### 7.5 Startup Sequence

**Recommended Startup Order**:

```
1. Start MySQL database service
   ↓
2. Start database server (optional)
   ↓
3. Start gateway (Python)
   ↓
4. Start ESP8266 devices (multiple devices can run in parallel)
   ↓
5. Start Android app
```

**Important Notes**:
- ⚠️ The gateway must be started before devices and Android
- ⚠️ If device or Android connection fails, check if the gateway is running properly
- ⚠️ Test mode can skip steps 1 and 2

### 7.6 Health Check

**Using the Health Check Tool**:
```bash
cd "d:\projects\ai_generate\edge computing home"
python Python/scripts/health_check.py
```

**Check Items**:
- Configuration file integrity
- Gateway process status
- Network port availability
- Database connection status
- Device connection status

---

## 8. Development Guide

### 8.1 Adding New Devices

#### Step 1: Create Device Firmware

1. **Copy existing device code**
   ```bash
   cp -r "Device Unit code/esp8266_airconditioner_unit" \
         "Device Unit code/esp8266_new_device"
   ```

2. **Modify device ID**
   ```cpp
   // config.h
   #define DEVICE_ID "A1_new_device"
   ```

3. **Add sensor code**
   - Add libraries according to sensor type
   - Implement data collection functions
   - Update JSON data format

4. **Upload to ESP8266**

#### Step 2: Update Gateway Configuration

1. **Add device to allowed list**
   - Add in the database server
   - Test mode: Modify the default list in `gate_test.py`

   ```python
   # gate_test.py:142
   return ["A1_tem_hum", "A1_curtain", "A1_security", "A1_new_device"]
   ```

2. **Restart gateway**

#### Step 3: Test New Device

```bash
# Test using device simulator
python Python/scripts/simulator_device.py
```

### 8.2 Adding New Sensors

#### Adding Sensors on the Device Side

1. **Include sensor library**
   ```cpp
   #include <SensorLibrary.h>
   ```

2. **Initialize sensor**
   ```cpp
   Sensor sensor(SENSOR_PIN);
   void setup() {
     sensor.begin();
   }
   ```

3. **Collect data**
   ```cpp
   float getSensorData() {
     return sensor.read();
   }
   ```

4. **Add to JSON data**
   ```cpp
   void sendMsgToGate() {
     StaticJsonDocument<200> msg;
     msg["device_id"] = device_id;
     msg["NewSensor"] = getSensorData();
     // ...
   }
   ```

#### Adding Fields on the Gateway Side

1. **Define field constants**
   ```python
   # common/constants.py
   FIELD_NEW_SENSOR = "NewSensor"
   
   DEFAULT_SENSOR_DATA = {
       # ...
       FIELD_NEW_SENSOR: 0.0,
   }
   ```

2. **Update database table**
   ```sql
   ALTER TABLE gate_local_data
   ADD COLUMN new_sensor FLOAT(5) NULL;
   ```

### 8.3 Adding New Control Commands

#### Adding Commands on Android

1. **Add button UI**
   ```xml
   <Button
       android:id="@+id/btn_new_control"
       android:layout_width="wrap_content"
       android:layout_height="wrap_content"
       android:text="New Control" />
   ```

2. **Add click event**
   ```java
   btnNewControl.setOnClickListener(v -> {
       sendControl("new_control_op", "1");
   });
   ```

3. **Send command**
   ```java
   void sendControl(String op, String data) {
       JSONObject json = new JSONObject();
       json.put("op", op);
       json.put("data", data);
       json.put("status", "1");
       // Send to gateway...
   }
   ```

#### Adding Processing on the Gateway Side

1. **Add operation code handling**
   ```python
   # android_handler.py
   elif operation == "new_control_op":
       # Handle new command
       logger.info("Received new control command: %s", operation_value)
       # Update status or threshold
   ```

#### Adding Control on the Device Side

1. **Receive control data**
   ```cpp
   void getMsgFromGate() {
       if(client.available()){
           StaticJsonDocument<200> msg;
           String jsonStr = client.readStringUntil('\n');
           deserializeJson(msg, jsonStr);
           
           // Receive new control field
           int newControl = msg["NewControl"];
           Serial.println("RECV:" + jsonStr);
       }
   }
   ```

2. **Execute control**
   ```cpp
   void controlDevice() {
       if(newControl == 1) {
           digitalWrite(NEW_PIN, HIGH);
       } else {
           digitalWrite(NEW_PIN, LOW);
       }
   }
   ```

### 8.4 Modifying Communication Frequency

#### Modify Device Send Frequency

```cpp
// config.h
#define SEND_INTERVAL 3  // Change to 3 seconds

// Or modify in code
SendTicker.attach(SEND_INTERVAL, sendMsgToGate);
```

#### Modify Gateway Receive Frequency

```python
# common/constants.py
SENSOR_RECV_INTERVAL = 3  # Change to 3 seconds
SENSOR_SEND_INTERVAL = 3
```

#### Modify Android Receive Frequency

```python
# common/constants.py
ANDROID_SEND_INTERVAL = 3  # Change to 3 seconds
```

### 8.5 Debugging Tips

#### Python Gateway Debugging

1. **Enable verbose logging**
   ```python
   # log_setup.py
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **View log files**
   ```bash
   tail -f Python/Gate/gate.log
   ```

3. **Use test mode**
   ```bash
   python gate_test.py --test
   ```

#### Device Side Debugging

1. **Use serial monitor**
   - Baud rate: 115200
   - Observe output information

2. **Add debug output**
   ```cpp
   Serial.println("Debug: current value = " + String(value));
   ```

#### Android Side Debugging

1. **View Logcat**
   ```bash
   adb logcat | grep MyApplication
   ```

2. **Add logging**
   ```java
   Log.d("MyTag", "Debug message");
   ```

---

## 9. API Reference

### 9.1 Python Gateway API

#### Core Modules

##### gateway_state.py

```python
class GatewayState:
    """Gateway shared state management"""
    
    def __init__(self):
        """Initialize state"""
        
    def update_data(self, data: dict) -> None:
        """Update sensor data"""
        
    def set_threshold(self, field: str, value) -> None:
        """Set threshold"""
        
    def get_data_snapshot(self) -> dict:
        """Get data snapshot"""
        
    def is_device_permitted(self, device_id: str) -> bool:
        """Check if device is permitted to connect"""
```

##### sensor_handler.py

```python
def sensor_handler(gate_config, state: GatewayState) -> None:
    """Main listening thread for device node communication"""
    
def sensor_client_handler(cs: socket.socket, state: GatewayState) -> None:
    """Handle a single device node connection"""
```

##### android_handler.py

```python
class AndroidHandler:
    """Mobile application communication handler"""
    
    def __init__(self, db_socket: socket.socket, config_dir):
        """Initialize handler"""
        
    def android_handler(self, gate_network_config, state: GatewayState) -> None:
        """Main listening thread for mobile application communication"""
```

##### database.py

```python
def init_gate_database(db_config: GateDbConfig) -> MySQLConnection:
    """Initialize the gateway local database"""
    
def save_sensor_data(conn: MySQLConnection, data: dict) -> None:
    """Save sensor data to local database"""
```

#### Communication Protocol API

```python
from common.protocol import send_json, recv_json, send_line, recv_line

def send_json(sock: socket.socket, obj: Any) -> None:
    """Send JSON data"""
    
def recv_json(sock: socket.socket, bufsize: int = 4096) -> Any:
    """Receive JSON data"""
    
def send_line(sock: socket.socket, message: str) -> None:
    """Send text line"""
    
def recv_line(sock: socket.socket, bufsize: int = 4096) -> str:
    """Receive text line"""
```

### 9.2 Device Side API

#### Core Functions

```cpp
// WiFi initialization
void wifiInit(const char *ssid, const char *password);

// Door access monitoring
void listen_door_secur_access();

// Send data to gateway
void sendMsgToGate();

// Receive data from gateway
void getMsgFromGate();

// Control device
void controlDevice();

// Temperature and humidity collection
void getTemperature_Humidity();

// Light status retrieval
void getLightStatus();
```

#### Configuration Macros

```cpp
#define DEVICE_ID "A1_tem_hum"
#define GATEWAY_IP "192.168.1.107"
#define GATEWAY_PORT 9300
#define WIFI_SSID "your_wifi_ssid"
#define WIFI_PASSWORD "your_wifi_password"

// Sensor configuration
#define DHT_PIN D7
#define DHT_TYPE DHT11
#define LED_PIN D6
#define SEND_INTERVAL 3
#define RECV_INTERVAL 3
```

### 9.3 Android Side API

#### Network Communication

```java
public class GatewayClient {
    // Connect to gateway
    public boolean connect(String ip, int port);
    
    // Send login request
    public boolean login(String username, String password);
    
    // Send control command
    public void sendControl(String operation, String data);
    
    // Receive sensor data
    public JSONObject receiveSensorData();
    
    // Disconnect
    public void disconnect();
}
```

#### Configuration Management

```java
public class ConfigManager {
    // Load configuration
    public Properties loadConfig(Context context);
    
    // Save configuration
    public void saveConfig(Context context, String ip, int port);
}
```

---

## 10. Troubleshooting

### 10.1 Common Issues

#### Gateway Fails to Start

**Symptom**: Python script fails to run

**Possible Causes**:
1. Port is occupied
2. Configuration file error
3. Database connection failure

**Solutions**:
```bash
# Check port usage
netstat -ano | findstr "9300"
netstat -ano | findstr "9301"

# Check configuration file
cat Python/Gate/GateConfig.txt

# Check database connection
mysql -u root -p1234 -e "USE gate_database; SELECT * FROM gate_local_data LIMIT 1;"
```

#### Device Cannot Connect to Gateway

**Symptom**: ESP8266 displays "Gateway connection failed"

**Possible Causes**:
1. WiFi connection failed
2. Gateway IP is incorrect
3. Port is incorrect
4. Gateway is not running

**Solutions**:
```cpp
// Check WiFi connection
Serial.print("WiFi status: ");
Serial.println(WiFi.status());  // WL_CONNECTED = 3

// Check gateway IP
Serial.print("Gateway IP: ");
Serial.println(GATEWAY_IP);

// Check port
Serial.print("Gateway port: ");
Serial.println(GATEWAY_PORT);
```

#### Android Cannot Connect to Gateway

**Symptom**: Connection timeout or connection refused

**Possible Causes**:
1. Network unreachable
2. Incorrect IP or port
3. Gateway is not running
4. Firewall blocking

**Solutions**:
```bash
# Test network connectivity
ping 192.168.1.107

# Test port availability
telnet 192.168.1.107 9301

# Check firewall
# Windows
netsh advfirewall firewall show rule name=all

# Linux
sudo iptables -L
```

#### Database Connection Failure

**Symptom**: "Database connection failed" error

**Possible Causes**:
1. MySQL service is not running
2. Incorrect username or password
3. Database does not exist

**Solutions**:
```bash
# Check MySQL service
# Windows
sc query MySQL

# Linux
sudo systemctl status mysql

# Test connection
mysql -u root -p1234 -e "SHOW DATABASES;"

# Create database
mysql -u root -p1234 -e "CREATE DATABASE IF NOT EXISTS gate_database;"
```

### 10.2 Log Analysis

#### Gateway Log Location

```
Python/Gate/gate.log
Python/Gate/gate_test.log
```

#### Key Log Information

**Device Connection**:
```
INFO Device node communication port opened: 192.168.1.107:9300
INFO Device node connected: ('192.168.1.108', 12345)
INFO Device node 'A1_tem_hum' connected to gateway
```

**Android Connection**:
```
INFO Mobile application communication port opened: 192.168.1.107:9301
INFO Mobile application connected: ('192.168.1.109', 54321)
INFO User 'Jiang' logged in successfully
```

**Error Logs**:
```
ERROR Device node receive data connection disconnected: [Errno 10054] An existing connection was forcibly closed by the remote host
ERROR Mobile application send connection disconnected: [Errno 10053] Software caused connection abort
ERROR JSON parsing failed: Expecting property name enclosed in double quotes
```

### 10.3 Debugging Tools

#### Integration Test Tool

```bash
# Run integration test
python Python/scripts/run_integration_test.py
```

#### Health Check Tool

```bash
# Run health check
python Python/scripts/health_check.py
```

#### Device Simulator

```bash
# Simulate device connection
python Python/scripts/simulator_device.py

# Simulate Android connection
python Python/scripts/simulator_android.py
```

---

## 11. Appendix

### 11.1 Configuration File Templates

#### GateConfig.txt Template

```
192.168.1.107
192.168.1.107
9300
9301
9302
root
1234
gate_database
```

#### UserConfig.txt Template

```
Jiang
pwd
A1
```

#### config.h Template

```cpp
#ifndef CONFIG_H
#define CONFIG_H

// Device configuration
#define DEVICE_ID "A1_tem_hum"
#define GATEWAY_IP "192.168.1.107"
#define GATEWAY_PORT 9300

// WiFi configuration
#define WIFI_SSID "your_wifi_ssid"
#define WIFI_PASSWORD "your_wifi_password"

// Sensor configuration
#define DHT_PIN D7
#define DHT_TYPE DHT11
#define LED_PIN D6

// Communication interval (seconds)
#define SEND_INTERVAL 3
#define RECV_INTERVAL 3

// OLED configuration
#define OLED_SDA_PIN D2
#define OLED_SCL_PIN D1
#define OLED_RESET_PIN -1

#endif
```

### 11.2 Database Table Structure

#### gate_local_data Table

```sql
CREATE TABLE IF NOT EXISTS `gate_local_data` (
  `timestamp` datetime NOT NULL,
  `light_th` int NULL,
  `temperature` float(5) NULL,
  `humidity` float(5) NULL,
  `light_cu` int NULL,
  `brightness` float(5) NULL,
  `curtain_status` int NULL
);
```

### 11.3 Constant Definitions

```python
# common/constants.py

# TCP ports
PORT_SENSOR = 9300
PORT_ANDROID = 9301
PORT_DB_SERVER = 9302

# Message terminator
MSG_TERMINATOR = "\n"

# Buffer sizes
BUFFER_SIZE_SMALL = 1024
BUFFER_SIZE_MEDIUM = 10240
BUFFER_SIZE_LARGE = 4096

# Listen backlog
LISTEN_BACKLOG = 128

# Database
DB_HOST = "localhost"
DB_PORT = 3306

# Communication intervals (seconds)
SENSOR_SEND_INTERVAL = 3
SENSOR_RECV_INTERVAL = 3
ANDROID_SEND_INTERVAL = 3
ANDROID_RECV_INTERVAL = 3
ALIYUN_UPLOAD_INTERVAL = 5

# MQTT port
ALIYUN_MQTT_PORT = 1883

# Door access status
DOOR_DENIED = 0
DOOR_GRANTED = 1

# Data fields
FIELD_DOOR_CARD_ID = "Door_Secur_Card_id"
FIELD_DOOR_STATUS = "Door_Security_Status"
FIELD_LIGHT_TH = "Light_TH"
FIELD_TEMPERATURE = "Temperature"
FIELD_HUMIDITY = "Humidity"
FIELD_LIGHT_CU = "Light_CU"
FIELD_BRIGHTNESS = "Brightness"
FIELD_CURTAIN_STATUS = "Curtain_status"
FIELD_DEVICE_KEY = "device_key"

# Default data
DEFAULT_SENSOR_DATA = {
    FIELD_DOOR_CARD_ID: "",
    FIELD_DOOR_STATUS: 0,
    FIELD_LIGHT_TH: 0,
    FIELD_TEMPERATURE: 0,
    FIELD_HUMIDITY: 0,
    FIELD_LIGHT_CU: 0,
    FIELD_BRIGHTNESS: 0,
    FIELD_CURTAIN_STATUS: 1,
}

DEFAULT_THRESHOLD_DATA = {
    FIELD_LIGHT_TH: 0,
    FIELD_TEMPERATURE: 30.0,
    FIELD_HUMIDITY: 65.0,
    FIELD_BRIGHTNESS: 500.0,
}
```

### 11.4 Related Documents

- [README.md](README.md) - Project Overview
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment Guide
- [GATEWAY_TEST_REPORT.md](GATEWAY_TEST_REPORT.md) - Test Report
- [OPTIMIZATION_REPORT.md](OPTIMIZATION_REPORT.md) - Optimization Report

### 11.5 Technical Support

**Issue Reporting**: Submit issues to the project repository  
**Documentation Updates**: Developer documentation is updated regularly  
**Version Releases**: Follows semantic versioning

---

**Document Version**: v1.0  
**Last Updated**: April 6, 2026  
**Maintainer**: IoT Development Team
