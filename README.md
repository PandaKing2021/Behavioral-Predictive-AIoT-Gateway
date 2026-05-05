# Edge Computing Smart Home Gateway System

> **EdgeIntelliHome** - Edge Computing-based Intelligent Behavior Prediction and Home Control Gateway System

---

## 🌟 Project Overview

This project is a complete edge computing smart home system that integrates **AI behavior prediction**, **edge-cloud collaborative inference**, **dual-dataset validation**, and **real-time device linkage**. The system utilizes a 1DCNN-LSTM deep learning model to achieve intelligent user behavior prediction and device pre-control, performing inference on local edge nodes to ensure low latency and high privacy protection.

### Core Features

- 🧠 **AI Behavior Prediction** - Based on 1DCNN-LSTM model, achieving 92.34% accuracy
- ⚡ **Edge Inference** - Inference latency of only 2.45ms, fully local execution
- 🔄 **Edge-Cloud Collaboration** - Sentinel framework for intelligent collaboration between edge and cloud
- 📊 **Dual-Dataset Validation** - Excellent performance on both CASAS and local datasets
- 🏠 **Smart Linkage** - Supports automated control of air conditioner, curtains, door security, and more
- 📱 **Mobile Control** - Android app for remote monitoring and control
- 🌐 **Cloud-Edge Integration** - Supports Alibaba Cloud IoT platform data upload

---

## 📋 System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│            Edge Computing Smart Home System Architecture       │
└────────────────────────────────────────────────────────────────┘

        ┌─────────────┐
        │   Android   │ (Port 9301)
        │  Mobile App │
        └──────┬──────┘
               │ TCP
               ▼
┌──────────────────────────────────────────────────────────────┐
│                  Python Edge Gateway Server                  │
│                                                              │
│  ┌────────────────────────────────────────────────────┐      │
│  │  • Device Communication Module (Port 9300)         │      │
│  │  • Android Communication Module (Port 9301)        │      │
│  │  • Database Server Connection (Port 9302)          │      │
│  │  • AI Behavior Prediction Engine (1DCNN-LSTM +     │      │
│  │    Sentinel Framework)                             │      │
│  │  • Intelligent Decision Logic                      │      │
│  │  • Alibaba Cloud IoT Upload                        │      │
│  └────────────────────────────────────────────────────┘      │
│                                                              │
│  Edge AI Inference Engine:                                   │
│  ┌──────────────┐      ┌──────────────┐                      │
│  │  Edge Model  │ ◄───►│   Sentinel   │                      │
│  │ (~15K params)│      │   Model      │                      │
│  └──────────────┘      │  (~1K params)│                      │
│                        └──────────────┘                      │
└──────────────────────────┬───────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Smart AC    │    │Smart Curtain│    │Smart Door   │
│ A1_tem_hum  │    │ A1_curtain  │    │ A1_security │
│ DHT11 Temp  │    │ BH1750 Light│    │ MFRC522 RFID│
└─────────────┘    └─────────────┘    └─────────────┘
```

---

## 🚀 Quick Start

### Requirements

- **Python**: 3.8+
- **MySQL**: 8.0+
- **ESP8266**: Development board and Arduino IDE
- **Android**: SDK API 21+

### Quick Deployment

1. **Run Health Check**
   ```bash
   cd Python/scripts
   python health_check.py
   ```

2. **Start Database Server (Optional)**
   ```bash
   cd Python/Database\ Server
   python database_process_server.py
   ```

3. **Start Edge Gateway**
   ```bash
   cd Python/Gate
   python gate.py
   ```

4. **Configure and Upload Device Firmware**
   ```bash
   cd Python/scripts
   python generate_device_config.py
   # Then upload each device firmware using Arduino IDE
   ```

5. **Install Android App**
   - Build APK and install on Android device
   - Configure gateway IP and port in `config.properties`

---

## 📁 Project Structure

```
edge computing home/
├── Android IoT APP/              # Android mobile application
├── Device Unit code/              # Device unit firmware
│   ├── esp8266_airconditioner_unit/
│   ├── esp8266_curtain_unit/
│   └── esp8266_doorsecurity_unit/
├── Python/                       # Edge gateway core code
│   ├── Gate/                     # Gateway main program
│   │   ├── gate.py              # Production mode entry
│   │   ├── gate_test.py         # Test mode entry
│   │   ├── sensor_handler.py    # Device communication & AI inference
│   │   ├── android_handler.py   # Android communication
│   │   ├── database.py          # Local database operations
│   │   └── precontroller.py     # Pre-controller
│   ├── Database Server/         # Database server
│   ├── common/                  # Common modules
│   └── scripts/                 # Utility scripts
│       ├── health_check.py      # Health check tool
│       └── generate_device_config.py  # Configuration generator
├── DEPLOYMENT_GUIDE.md          # Detailed deployment guide
├── DEVELOPER_GUIDE.md           # Developer documentation
└── README.md                    # This file
```

---

## 🧠 AI Behavior Prediction System

### Technical Architecture

The system adopts an **edge-cloud collaborative inference framework**, with the core components:

1. **Edge Model (Edge1DCLSTM)**
   - Parameters: ~15K
   - Inference speed: 2.45ms
   - Memory footprint: 7.38MB
   - Accuracy: 92.34%

2. **Sentinel Model (SentinelLSTM)**
   - Parameters: ~1K
   - Used for cloud collaboration and anomaly detection

### Core Modules

- **DataCollector** - Data collector, real-time sensor data acquisition
- **DataPreprocessor** - Data preprocessor, normalization and feature extraction
- **ONNXModelInference** - ONNX model inference engine
- **Precontroller** - Pre-controller, executes device pre-control

### Model Performance

| Metric | Value |
|--------|-------|
| Inference Latency | 2.45ms |
| Memory Footprint | 7.38MB |
| Model Accuracy | 92.34% |
| Training Datasets | CASAS + Local Dataset |

---

## 🎯 Device Features

### Supported Devices

| Device | Device ID | Function | Sensor |
|--------|-----------|----------|--------|
| Smart AC | A1_tem_hum | Temperature/humidity monitoring, AC control | DHT11 |
| Smart Curtain | A1_curtain | Light intensity monitoring, curtain control | BH1750 |
| Smart Door | A1_security | Door access control, RFID verification | MFRC522 |

### Port Allocation

| Port | Service | Description |
|------|---------|-------------|
| 9300 | Device Unit | ESP8266 device connection |
| 9301 | Android App | Mobile application connection |
| 9302 | Database Server | Database process communication |
| 3306 | MySQL | Database connection |
| 1883 | Alibaba Cloud MQTT | IoT cloud platform |

---

## 📱 Android App Features

- ✅ User login/registration
- ✅ Real-time sensor data viewing
- ✅ Temperature/humidity/light threshold settings
- ✅ Smart device control (on/off)
- ✅ Historical data query
- ✅ Door security status viewing
- ✅ Scenario-based operation support

---

## 🔧 Configuration

### Gateway Configuration (Python/Gate/GateConfig.txt)

```
Gateway IP          # Local IP address
Database Server IP  # Database server IP
Device Port         # Device unit communication port (9300)
Android Port        # Android application port (9301)
Database Server Port # Database communication port (9302)
MySQL Username
MySQL Password
Database Name
```

### Device Configuration

Manage all device configurations centrally by modifying `UNIFIED_CONFIG` in `Python/scripts/generate_device_config.py`:

```python
UNIFIED_CONFIG = {
    "wifi": {
        "ssid": "your_wifi_name",
        "password": "your_wifi_password"
    },
    "gateway": {
        "ip": "192.168.1.107",
        "port": 9300
    },
    "communication": {
        "send_interval": 3,
        "recv_interval": 3
    }
}
```

### Android Configuration (Android IoT APP/app/src/main/assets/config.properties)

```properties
ip = 192.168.1.107  # Gateway IP
port = 9301           # Android port
```

---

## 🧪 Testing & Validation

### Health Check

```bash
cd Python/scripts
python health_check.py
```

Expected output: `✓ All checks passed! System is well configured.`

### Testing Tools

- **Device Simulator** - Simulates ESP8266 device communication with gateway
- **Android Simulator** - Simulates Android client communication with gateway
- **Comprehensive Test Suite** - 29 comprehensive test cases

### Test Results

- ✅ Passed: 27
- ⚠️ Warnings: 0
- ❌ Errors: 0

---

## 📊 Data Flow

### Sensor Data Flow

```
Device Unit (ESP8266)
  ↓ JSON data: {"device_id": "xxx", "Temperature": 25.0, ...}
Python Edge Gateway
  ↓ Update state
  ↓ AI behavior prediction
  ↓ Intelligent decision
  ↓ Forward data
Android App
  ↓ Display data
User Interface
```

### Control Command Flow

```
Android App
  ↓ Control command: {"op": "light_th_open", "data": "1", "status": "1"}
Python Edge Gateway
  ↓ Update threshold
  ↓ AI prediction & pre-control
  ↓ Send control
Device Unit
  ↓ Execute control
Hardware Device
```

---

## 🛠️ Utility Scripts

### health_check.py

System health check tool, automatically detects:
- ✓ Configuration file existence and format
- ✓ Port configuration consistency
- ✓ Device unit configuration
- ✓ Python dependencies
- ✓ Network connectivity

```bash
python Python/scripts/health_check.py
```

### generate_device_config.py

Device configuration generator, automatically generates configuration header files for each device.

```bash
python Python/scripts/generate_device_config.py
```

---

## 📖 Detailed Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Detailed deployment guide
- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Developer documentation

### Experiment Reports (located in `meterials/reports/`)

- Complete experiment reports (HTML and Markdown formats)
- Database server test report
- Gateway test report
- Optimization report
- Test final summary
- Quick reference documentation
- Project migration report

---

## 🔍 Troubleshooting

### Device Cannot Connect
1. Check if WiFi password is correct
2. Check gateway IP configuration
3. Confirm gateway service is running
4. Run health check

### Android Cannot Connect
1. Check if port is 9301
2. Confirm gateway IP configuration
3. Check network connection

### AI Prediction Issues
1. Check if model file is loaded
2. Confirm sensor data is being collected normally
3. Check inference output in gateway logs

### Configuration Errors
1. Run `python health_check.py`
2. View detailed check results
3. Fix issues according to prompts
4. Regenerate configuration (if needed)

---

## 🎯 System Features

### Edge Computing Advantages

- ⚡ **Low Latency** - Local inference, response time <3ms
- 🔒 **Privacy Protection** - No need to upload data to cloud
- 💾 **Bandwidth Saving** - Only upload necessary data
- 🌐 **Offline Operation** - Can still operate without network

### AI Prediction Capabilities

- 📈 **High Accuracy** - 92.34% prediction accuracy
- 🔄 **Real-time** - Continuous learning of user behavior patterns
- 🎯 **Personalized** - Customized based on user historical data
- 🤖 **Intelligent** - Automatically trigger device linkage

---

## 📝 Version History

| Version | Date | Description |
|---------|------|-------------|
| 3.0 | 2026-04 | Integrated AI behavior prediction system, edge inference engine |
| 2.0 | 2024-04 | Configuration management optimization, new utility scripts |
| 1.0 | - | Initial version |

---

## 📄 License

This project is under development and translation, for learning and research purposes only.

---

## 🙏 Acknowledgments

- CASAS dataset providers
- ESP8266 open-source community
- ONNX Runtime team

---

**System Status**: ✅ Production Ready
**Last Updated**: April 15, 2026
