# IoT Smart Gateway System

An IoT (Internet of Things) smart gateway system featuring a dual-layer gateway-database server architecture, supporting device node data collection, mobile (Android) remote control, and Alibaba Cloud IoT platform data upload.

## Project Structure

```
Python/
├── MyComm.py                          # Communication protocol codec between gateway and database server
├── requirements.txt                   # Python dependencies list
├── common/                            # Common modules
│   ├── config.py                      # Configuration management
│   ├── models.py                      # Thread-safe state models
│   └── constants.py                   # Constants definition
├── Gate/                              # Gateway program
│   ├── gate.py                        # Gateway main entry
│   ├── sensor_handler.py              # Device node communication
│   ├── android_handler.py             # Mobile application communication
│   ├── aliyun_handler.py              # Alibaba Cloud IoT communication
│   ├── database.py                    # Local database operations
│   ├── GateConfig.txt                 # Gateway configuration file
│   └── UserConfig.txt                 # Local authorized user information
└── Database Server/                   # Database server
    ├── database_process_server.py     # Database server main program
    └── serverConfig.txt               # Server configuration file
```

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start Database Server

```bash
cd "Database Server"
python database_process_server.py
```

### Start Gateway

```bash
cd Gate
python gate.py
```

## Communication Protocol

### Gateway and Database Server

Communication format: `command_code|data_code|status_code`, delimiter `|`

- Gateway → Server: Store new user: `add_new_user|{username+password+deviceKey}|1`
- Server → Gateway: Success: `add_new_user|NULL|1` Failure: `add_new_user|NULL|0`
- Gateway → Server: Check user configuration: `check_userconfig_illegal|{username+password+deviceKey}|1`
- Gateway → Server: Query device: `check_device_id|{deviceKey}|1`

### Gateway and Device Nodes

- TCP Port: 3000
- Data Format: JSON (Device→Gateway), Python dict str + `\n` (Gateway→Device)

### Gateway and Mobile Application

- TCP Port: 3001
- Communication Format: `command_code|data_code|status_code`

## Configuration Files

### GateConfig.txt (one configuration item per line)

```
Gateway IP
Database Server IP
Device Node Communication Port
Mobile Application Communication Port
Database Server Port
MySQL Username
MySQL Password
Database Name
```

### UserConfig.txt (three lines)

```
Username
Password
Device Key
```

### serverConfig.txt (two lines)

```
Database Server IP
Listen Port
```
