# DuneBugger Captive Portal

A Python-based HTTP web captive portal designed for Raspberry Pi that allows users to scan and connect to WiFi networks through a web interface.

## Features

- 🏜️ **DuneBugger Themed Interface** - Custom desert-themed UI
- 📡 **WiFi Network Scanning** - Automatically scans and displays available networks
- 🔒 **Security Support** - Handles both open and secured WiFi networks
- 🌐 **Web-based Interface** - No need for additional apps or software
- 🔄 **Real-time Updates** - Uses WebSocket for live status updates
- 🖥️ **Responsive Design** - Works on mobile, tablet, and desktop devices
- 🔧 **NetworkManager Integration** - Uses system NetworkManager for reliable connections
- 📱 **Mobile-Friendly** - Optimized for smartphone and tablet usage
- 🌐 **Offline Operation** - Works without internet connection (all assets served locally)

## Requirements

### Hardware
- Raspberry Pi (3B+ or newer recommended)
- WiFi adapter (built-in or USB)
- SD card (16GB or larger)

### Software
- Raspberry Pi OS (Bullseye or newer)
- Python 3.8+
- NetworkManager
- Root/sudo access

## Installation

### Quick Installation (Recommended)

1. Clone or download this repository to your Raspberry Pi:
   ```bash
   git clone <repository-url>
   cd axpop-captive-portal
   ```

2. Run the installation script as root:
   ```bash
   sudo ./install.sh
   ```

3. The script will:
   - Install required system packages
   - Set up Python virtual environment
   - Install Python dependencies
   - Configure systemd service
   - Optionally set up WiFi Access Point mode

### Manual Installation

1. **Install system dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-pip python3-venv network-manager wireless-tools wpasupplicant
   ```

2. **Create Python virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Python packages:**
   ```bash
   pip install flask flask-socketio requests
   ```

4. **Install systemd service:**
   ```bash
   sudo cp dunebugger-portal.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable dunebugger-portal
   sudo systemctl start dunebugger-portal
   ```

## Usage

### Running the Application

#### As a Service (Production)
```bash
sudo systemctl start dunebugger-portal
sudo systemctl status dunebugger-portal
```

#### Development Mode
```bash
source .venv/bin/activate
python app.py
```

#### Direct Run
```bash
sudo python run.py
```

### Accessing the Interface

1. **Local Access:** Open a web browser and navigate to:
   - `http://localhost` (if running locally)
   - `http://[raspberry-pi-ip]` (from other devices on the network)

2. **Access Point Mode:** If configured as an access point:
   - Connect to the "DuneBugger-Setup" WiFi network
   - Navigate to `http://192.168.50.1`

### Using the Portal

1. **Scan Networks:** Click the "🔄 Scan" button to discover available WiFi networks
2. **Select Network:** Click on any network from the list
3. **Enter Password:** For secured networks, enter the WiFi password
4. **Connect:** Click "Connect" to join the selected network
5. **Monitor Status:** View connection status in the status panel

## Configuration

### Environment Variables

- `FLASK_ENV`: Set to `development` for debug mode
- `CAPTIVE_PORTAL_PORT`: Port to run the server (default: 80)
- `CAPTIVE_PORTAL_HOST`: Host to bind to (default: 0.0.0.0)

### Access Point Configuration

If you want to use the Raspberry Pi as a WiFi access point for the captive portal:

1. **Edit hostapd configuration** (`/etc/hostapd/hostapd.conf`):
   ```
   interface=wlan0
   driver=nl80211
   ssid=DuneBugger-Setup
   hw_mode=g
   channel=7
   wmm_enabled=0
   macaddr_acl=0
   auth_algs=1
   ignore_broadcast_ssid=0
   wpa=0
   ```

2. **Configure DHCP** (`/etc/dnsmasq.conf`):
   ```
   interface=wlan0
   dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
   address=/#/192.168.50.1
   ```

3. **Set static IP** (`/etc/dhcpcd.conf`):
   ```
   interface wlan0
       static ip_address=192.168.50.1/24
       nohook wpa_supplicant
   ```

## API Endpoints

The application provides REST API endpoints for programmatic access:

- `GET /api/scan` - Scan for available networks
- `POST /api/connect` - Connect to a network
- `GET /api/status` - Get connection status
- `GET /api/disconnect` - Disconnect from current network

### Example API Usage

```bash
# Scan networks
curl http://localhost/api/scan

# Connect to network
curl -X POST http://localhost/api/connect \
  -H "Content-Type: application/json" \
  -d '{"ssid": "MyNetwork", "password": "mypassword"}'

# Check status
curl http://localhost/api/status
```

## File Structure

```
axpop-captive-portal/
├── app.py                    # Main Flask application
├── wifi_manager.py           # WiFi management logic
├── run.py                    # Production runner script
├── requirements.txt          # Python dependencies
├── install.sh               # Installation script
├── dunebugger-portal.service # Systemd service file
├── templates/
│   └── index.html           # Main web interface
├── static/
│   ├── css/
│   │   └── style.css        # Styling
│   └── js/
│       └── app.js           # JavaScript functionality
└── README.md                # This file
```

## Troubleshooting

### Service Issues

1. **Check service status:**
   ```bash
   sudo systemctl status dunebugger-portal
   ```

2. **View logs:**
   ```bash
   sudo journalctl -u dunebugger-portal -f
   ```

3. **Restart service:**
   ```bash
   sudo systemctl restart dunebugger-portal
   ```

### Permission Issues

- Ensure the service runs as root to access network interfaces
- Check that NetworkManager is running: `sudo systemctl status NetworkManager`

### Network Scanning Issues

1. **Check wireless interface:**
   ```bash
   iwconfig
   nmcli device status
   ```

2. **Manual scan test:**
   ```bash
   sudo iwlist wlan0 scan
   nmcli device wifi list
   ```

### Connection Issues

1. **Check NetworkManager:**
   ```bash
   sudo systemctl status NetworkManager
   ```

2. **Test manual connection:**
   ```bash
   nmcli device wifi connect "SSID" password "password"
   ```

### Port 80 Access

If you get permission errors on port 80:

1. **Run as root:** Use `sudo` when starting the application
2. **Use alternative port:** Modify the port in `run.py` to use port 8080 or similar
3. **Use authbind:** Install and configure authbind for non-root port 80 access

## Security Considerations

- The application requires root privileges to manage network connections
- Passwords are transmitted over HTTP (consider HTTPS for production)
- The service runs with elevated privileges - review security settings
- Access point mode creates an open network - consider adding WPA2 security

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on Raspberry Pi hardware
5. Submit a pull request

## License

This project is part of the DuneBugger project. Please refer to the project license.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the application logs
- Create an issue in the project repository

## Changelog

### Version 1.0.0
- Initial release
- WiFi scanning and connection
- Web-based interface
- Systemd service integration
- Access point configuration support