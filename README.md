# ThingsBoard Gateway Device Automation

This repository contains Python scripts to automate the creation and management of gateway devices in ThingsBoard. The scripts streamline the process of setting up device profiles, attributes, alarms, and retrieving access tokens for IoT devices.

## Features
- Automates the creation of gateway devices in ThingsBoard.
- Configures device profiles with alarms (e.g., gateway online, offline, and no data).
- Sets server-side attributes for devices.
- Retrieves and stores device access tokens in a configuration file.

## Files
- `create-gateway.py`: Main script to create a gateway device, configure attributes, and retrieve access tokens.
- `create-sensor.py`: Script to create and manage sensor devices.
- `config.ini`: Configuration file for ThingsBoard server details, device parameters, and attributes.

## Prerequisites
- Python 3.6 or higher
- ThingsBoard server instance
- Required Python packages: `requests`

## Setup
1. Clone this repository:
   ```bash
   git clone https://github.com/DarkHexBoy/thingsboard-gateway-automation.git
   cd thingsboard-gateway-automation
   ```
2. Install the required Python packages:
   ```bash
   pip install requests
   ```
3. Update the `config.ini` file with your ThingsBoard server details and device parameters.

## Usage
1. Run the `create-gateway.py` script to create a gateway device:
   ```bash
   python create-gateway.py
   ```
2. The script will:
   - Log in to the ThingsBoard server.
   - Check and create a device profile if it doesn't exist.
   - Create a gateway device and set its attributes.
   - Retrieve the device's access token and store it in `config.ini`.

## Configuration
The `config.ini` file contains the following sections:

### ThingsBoard Server Details
```ini
[ThingsBoard]
TB_HOST = http://<your-thingsboard-host>
USERNAME = <your-username>
PASSWORD = <your-password>
```

### Device Parameters
```ini
[Device]
device_name = <device-name>
device_profile_name = <device-profile-name>
```

### Device Attributes
```ini
[Attributes]
Model = <model>
Partnumber = <partnumber>
Region = <region>
Serial Number = <serial-number>
Firmware Version = <firmware-version>
Hardware Version = <hardware-version>
```

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Author
- **LockOn**
- GitHub: [DarkHexBoy](https://github.com/DarkHexBoy)
