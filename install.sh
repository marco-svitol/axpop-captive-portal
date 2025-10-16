#!/bin/bash

# DuneBugger Captive Portal Installation Script for Raspberry Pi
# This script sets up the captive portal as a system service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="dunebugger-portal"
PROJECT_DIR="/home/marco/localGits/dunebugger-app/axpop-captive-portal"
SERVICE_FILE="dunebugger-portal.service"
LOG_FILE="/var/log/dunebugger-portal.log"

echo -e "${GREEN}DuneBugger Captive Portal Installation${NC}"
echo "========================================"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Update system packages
print_status "Updating system packages..."
apt-get update -y

# Install required system packages
print_status "Installing required system packages..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    network-manager \
    wireless-tools \
    wpasupplicant \
    dnsmasq \
    hostapd \
    iptables-persistent

# Ensure NetworkManager is running
print_status "Starting NetworkManager..."
systemctl enable NetworkManager
systemctl start NetworkManager

# Create log file with proper permissions
print_status "Setting up log file..."
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"

# Install Python dependencies if not already installed
print_status "Checking Python dependencies..."
cd "$PROJECT_DIR"

if [ ! -d ".venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv .venv
fi

print_status "Installing Python packages..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# Make run.py executable
chmod +x run.py

# Install systemd service
print_status "Installing systemd service..."
cp "$SERVICE_FILE" "/etc/systemd/system/"
systemctl daemon-reload

# Enable and start the service
print_status "Enabling and starting the service..."
systemctl enable "$SERVICE_NAME"

# Check if service is already running and stop it
if systemctl is-active --quiet "$SERVICE_NAME"; then
    print_status "Stopping existing service..."
    systemctl stop "$SERVICE_NAME"
fi

systemctl start "$SERVICE_NAME"

# Wait a moment and check status
sleep 3
if systemctl is-active --quiet "$SERVICE_NAME"; then
    print_status "Service started successfully!"
    systemctl status "$SERVICE_NAME" --no-pager -l
else
    print_error "Service failed to start. Checking logs..."
    journalctl -u "$SERVICE_NAME" --no-pager -l
    exit 1
fi

# Optional: Configure as WiFi Access Point
echo ""
read -p "Do you want to configure this Raspberry Pi as a WiFi Access Point? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Configuring WiFi Access Point..."
    
    # Backup original configurations
    cp /etc/hostapd/hostapd.conf /etc/hostapd/hostapd.conf.backup 2>/dev/null || true
    cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup 2>/dev/null || true
    
    # Configure hostapd
    cat > /etc/hostapd/hostapd.conf << EOF
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
EOF

    # Configure dnsmasq
    cat >> /etc/dnsmasq.conf << EOF

# DuneBugger Captive Portal Configuration
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
address=/#/192.168.4.1
EOF

    # Configure network interface
    cat >> /etc/dhcpcd.conf << EOF

# DuneBugger Access Point Configuration
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
EOF

    # Enable services
    systemctl enable hostapd
    systemctl enable dnsmasq
    
    print_status "Access Point configuration complete!"
    print_warning "Please reboot the Raspberry Pi to apply network changes."
fi

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo "========================================"
echo "Service name: $SERVICE_NAME"
echo "Service status: systemctl status $SERVICE_NAME"
echo "View logs: journalctl -u $SERVICE_NAME -f"
echo "Web interface: http://$(hostname -I | awk '{print $1}')"
echo ""
echo "To uninstall:"
echo "  sudo systemctl stop $SERVICE_NAME"
echo "  sudo systemctl disable $SERVICE_NAME"
echo "  sudo rm /etc/systemd/system/$SERVICE_FILE"
echo "  sudo systemctl daemon-reload"