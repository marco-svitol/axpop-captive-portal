# DuneBugger Captive Portal

A Flask-based WiFi captive portal for Raspberry Pi with automatic access point management.

## Features

### Captive Portal
- Web-based WiFi network scanning and connection
- Real-time status updates via WebSocket
- Responsive mobile-friendly interface
- Support for WPA/WPA2 and open networks

### Access Point Management (NEW)
- **Automatic connectivity monitoring** - Checks WiFi/Ethernet connectivity every minute
- **Automatic AP setup** - Creates access point when no internet connection is available
- **Automatic AP teardown** - Removes access point when connectivity is restored
- **Configurable AP settings** - SSID, password, IP address, and monitoring interval
- **Manual AP control** - Start/stop access point manually via web interface

## Requirements

- Raspberry Pi with WiFi capability
- NetworkManager (nmcli command)
- Python 3.7+
- Root privileges for network management

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd axpop-captive-portal
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Make the install script executable and run it:
```bash
chmod +x install.sh
sudo ./install.sh
```

## Configuration

### Access Point Configuration

The access point can be configured via:

1. **Web Interface**: Use the "Configure" button in the Access Point panel
2. **Configuration File**: Edit `ap_config.json` directly

Default configuration:
```json
{
  "ap_ssid": "DuneBugger-Setup",
  "ap_password": "dunebugger123", 
  "ap_ip": "192.168.4.1",
  "ap_netmask": "255.255.255.0",
  "ap_channel": 7,
  "monitor_interval": 60,
  "connection_timeout": 10
}
```

### Configuration Options

- `ap_ssid`: Name of the access point network
- `ap_password`: WiFi password (leave empty for open network)
- `ap_ip`: IP address of the access point
- `ap_netmask`: Network mask for the AP subnet
- `ap_channel`: WiFi channel (1-11)
- `monitor_interval`: How often to check connectivity (seconds)
- `connection_timeout`: Timeout for connectivity checks (seconds)

## Usage

### Running the Application

```bash
# Run directly
python app.py

# Or using the systemd service
sudo systemctl start dunebugger-portal
sudo systemctl enable dunebugger-portal  # Auto-start on boot
```

The web interface will be available at:
- http://localhost:8080 (local access)
- http://192.168.4.1:8080 (when connected to AP)

### Access Point Behavior

The application automatically:

1. **Monitors connectivity** every 60 seconds (configurable)
2. **Sets up AP** when no WiFi or Ethernet connection is detected
3. **Tears down AP** when connectivity is restored
4. **Provides captive portal** for WiFi configuration when AP is active

### Manual Control

Via the web interface you can:
- View current connectivity status
- Monitor access point status
- Manually start/stop the access point
- Configure AP settings
- Scan and connect to WiFi networks

### API Endpoints

#### WiFi Management (Original)
- `GET /api/scan` - Scan for WiFi networks
- `POST /api/connect` - Connect to a network
- `GET /api/status` - Get connection status
- `GET /api/disconnect` - Disconnect from current network

#### Access Point Management (NEW)
- `GET /api/ap/status` - Get AP status and monitoring state
- `POST /api/ap/start` - Manually start access point
- `POST /api/ap/stop` - Manually stop access point
- `GET /api/ap/config` - Get AP configuration
- `POST /api/ap/config` - Update AP configuration
- `POST /api/ap/monitoring/start` - Start connectivity monitoring
- `POST /api/ap/monitoring/stop` - Stop connectivity monitoring

## Architecture

The application is organized into separate modules:

- `app.py` - Main Flask application and API endpoints
- `wifi_manager.py` - WiFi scanning and connection management
- `access_point_manager.py` - **NEW** - AP setup/teardown and connectivity monitoring
- `ap_config.json` - **NEW** - Access point configuration file

## NetworkManager Commands

The access point functionality uses NetworkManager via `nmcli`:

```bash
# Create AP connection
nmcli connection add type wifi ifname wlan0 con-name DuneBugger-AP ssid "DuneBugger-Setup"

# Configure as access point
nmcli connection modify DuneBugger-AP 802-11-wireless.mode ap 802-11-wireless.band bg 802-11-wireless.channel 7

# Set IP and enable sharing
nmcli connection modify DuneBugger-AP ipv4.method shared ipv4.addresses 192.168.4.1/24

# Add WPA2 security
nmcli connection modify DuneBugger-AP 802-11-wireless-security.key-mgmt wpa-psk 802-11-wireless-security.psk "password"

# Start/stop AP
nmcli connection up DuneBugger-AP
nmcli connection down DuneBugger-AP
```

## Troubleshooting

### Access Point Issues

1. **No WiFi device found**
   - Check that WiFi hardware is available: `nmcli device status`
   - Ensure NetworkManager is running: `systemctl status NetworkManager`

2. **AP fails to start**
   - Check system logs: `journalctl -u dunebugger-portal`
   - Verify device isn't in use: `nmcli connection show --active`

3. **Connectivity monitoring not working**
   - Check internet connectivity: `ping 8.8.8.8`
   - Verify NetworkManager connections: `nmcli connection show --active`

### Permission Issues

Ensure the service runs with proper privileges:
```bash
sudo systemctl edit dunebugger-portal
```

Add:
```ini
[Service]
User=root
Group=root
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly on actual hardware
5. Submit a pull request

## Hardware Testing

This application is designed for Raspberry Pi hardware. For development/testing without hardware:
- Mock data will be returned for network operations
- AP functionality will log commands but not execute them
- Web interface remains fully functional for UI testing