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

# Function to check WiFi interfaces
check_wifi_interfaces() {
    print_status "Checking WiFi interfaces..."
    
    wifi_count=$(nmcli device status | grep -c wifi || true)
    
    if [ "$wifi_count" -lt 2 ]; then
        print_warning "Found only $wifi_count WiFi interface(s)"
        print_warning "DuneBugger requires 2 WiFi interfaces for optimal operation:"
        print_warning "  - One for Access Point mode"
        print_warning "  - One for client WiFi connections"
        echo ""
        print_warning "Recommended hardware setup:"
        print_warning "  - Raspberry Pi with built-in WiFi + USB WiFi adapter"
        print_warning "  - Or two USB WiFi adapters"
        echo ""
        read -p "Continue installation anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Installation cancelled"
            exit 1
        fi
    else
        print_status "Found $wifi_count WiFi interfaces - sufficient for dual-mode operation"
    fi
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
    iptables-persistent

# Ensure NetworkManager is running
print_status "Starting NetworkManager..."
systemctl enable NetworkManager
systemctl start NetworkManager

# Check WiFi interfaces
check_wifi_interfaces

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

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo "========================================"
echo "Service name: $SERVICE_NAME"
echo "Service status: systemctl status $SERVICE_NAME"
echo "View logs: journalctl -u $SERVICE_NAME -f"
echo "Web interface: http://$(hostname -I | awk '{print $1}'):80"
echo ""
echo ""
echo "🏜️ DuneBugger Captive Portal Features:"
echo "  📡 Automatic WiFi scanning and connection"
echo "  🔄 Automatic access point setup when no internet"
echo "  ⚙️  Configurable AP settings via web interface"
echo "  📱 Mobile-friendly captive portal"
echo "  🔧 Dual WiFi interface support"
echo ""
echo "📋 Configuration:"
echo "  - Config file: $PROJECT_DIR/ap_config.json"
echo "  - Web interface: Configure button in Access Point panel"
echo "  - Default AP: wlan1 (DuneBugger-Setup)"
echo "  - Default client: wlan0"
echo ""
echo "🔍 Current WiFi interfaces:"
nmcli device status | grep wifi | while read -r line; do
    echo "  📶 $line"
done
echo ""
echo "📖 Usage:"
echo "  - Access web interface at: http://$(hostname -I | awk '{print $1}'):80"
echo "  - When no internet: AP appears as 'DuneBugger-Setup'"
echo "  - Configure WiFi through captive portal"
echo "  - Monitor status via web interface"
echo ""
echo "To uninstall:"
echo "  sudo systemctl stop $SERVICE_NAME"
echo "  sudo systemctl disable $SERVICE_NAME"
echo "  sudo rm /etc/systemd/system/$SERVICE_FILE"
echo "  sudo systemctl daemon-reload"