// DuneBugger Captive Portal JavaScript

class CaptivePortal {
    constructor() {
        this.socket = null;
        this.currentNetworks = [];
        this.selectedNetwork = null;
        this.isConnecting = false;
        
        this.init();
    }
    
    init() {
        this.initializeSocket();
        this.bindEvents();
        this.updateStatus();
        this.updateAPStatus();
        this.scanNetworks();
        this.updateDeviceInfo();
    }
    
    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.showMessage('Connected to DuneBugger Portal', 'success');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.showMessage('Disconnected from server', 'warning');
        });
        
        this.socket.on('scan_result', (data) => {
            this.handleScanResult(data);
        });
        
        this.socket.on('status', (data) => {
            console.log('Status update:', data);
        });
    }
    
    bindEvents() {
        // Scan button
        document.getElementById('scan-btn').addEventListener('click', () => {
            this.scanNetworks();
        });
        
        // Disconnect button
        document.getElementById('disconnect-btn').addEventListener('click', () => {
            this.disconnect();
        });
        
        // WiFi form submission
        document.getElementById('wifi-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.connectToNetwork();
        });
        
        // Cancel connection
        document.getElementById('cancel-btn').addEventListener('click', () => {
            this.hideConnectionForm();
        });
        
        // Password visibility toggle
        document.getElementById('toggle-password').addEventListener('click', () => {
            this.togglePasswordVisibility();
        });
        
        // AP Control buttons
        document.getElementById('ap-start-btn').addEventListener('click', () => {
            this.startAccessPoint();
        });
        
        document.getElementById('ap-stop-btn').addEventListener('click', () => {
            this.stopAccessPoint();
        });
        
        document.getElementById('ap-config-btn').addEventListener('click', () => {
            this.showAPConfigModal();
        });
        
        // AP Configuration modal
        document.getElementById('ap-config-close').addEventListener('click', () => {
            this.hideAPConfigModal();
        });
        
        document.getElementById('ap-config-cancel').addEventListener('click', () => {
            this.hideAPConfigModal();
        });
        
        document.getElementById('ap-config-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveAPConfig();
        });
        
        // Auto-refresh status every 10 seconds
        setInterval(() => {
            if (!this.isConnecting) {
                this.updateStatus();
                this.updateAPStatus();
            }
        }, 10000);
    }
    
    async scanNetworks() {
        this.showLoading(true);
        this.setButtonLoading('scan-btn', true);
        
        try {
            const response = await fetch('/api/scan');
            const data = await response.json();
            
            if (data.success) {
                this.displayNetworks(data.networks);
            } else {
                this.showMessage(`Scan failed: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Scan error:', error);
            this.showMessage('Failed to scan networks', 'error');
        } finally {
            this.showLoading(false);
            this.setButtonLoading('scan-btn', false);
        }
    }
    
    async updateStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.success) {
                this.displayStatus(data.status);
            }
        } catch (error) {
            console.error('Status update error:', error);
        }
    }
    
    displayStatus(status) {
        const indicator = document.getElementById('status-indicator');
        const text = document.getElementById('status-text');
        const disconnectBtn = document.getElementById('disconnect-btn');
        const statusPanel = document.getElementById('status-panel');
        
        // Remove previous status classes
        statusPanel.classList.remove('status-connected', 'status-disconnected', 'status-connecting');
        
        if (status.connected_network) {
            indicator.textContent = '✅';
            text.textContent = `Connected to: ${status.connected_network}`;
            disconnectBtn.style.display = 'inline-block';
            statusPanel.classList.add('status-connected');
        } else if (status.state === 'connecting') {
            indicator.textContent = '🔄';
            text.textContent = 'Connecting...';
            disconnectBtn.style.display = 'none';
            statusPanel.classList.add('status-connecting');
        } else {
            indicator.textContent = '❌';
            text.textContent = 'Not connected';
            disconnectBtn.style.display = 'none';
            statusPanel.classList.add('status-disconnected');
        }
    }
    
    displayNetworks(networks) {
        this.currentNetworks = networks;
        const container = document.getElementById('networks-list');
        
        if (networks.length === 0) {
            container.innerHTML = `
                <div class="no-networks">
                    <p>No networks found. Try scanning again.</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = networks.map(network => this.createNetworkItem(network)).join('');
        
        // Bind click events to network items
        container.querySelectorAll('.network-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                this.selectNetwork(networks[index]);
            });
        });
    }
    
    createNetworkItem(network) {
        const signalBars = this.createSignalBars(network.signal_strength);
        const securityIcon = network.security === 'open' ? '🔓' : '🔒';
        const securityClass = network.security === 'open' ? 'security-open' : 'security-secured';
        
        return `
            <div class="network-item" data-ssid="${network.ssid}">
                <div class="network-info">
                    <div class="network-icon">${securityIcon}</div>
                    <div class="network-details">
                        <h3>${this.escapeHtml(network.ssid)}</h3>
                    </div>
                </div>
                <div class="network-meta">
                    <div class="signal-strength">
                        ${signalBars}
                        <span>${network.signal_strength}%</span>
                    </div>
                    <div class="security-badge ${securityClass}">
                        ${network.security}
                    </div>
                </div>
            </div>
        `;
    }
    
    createSignalBars(strength) {
        const bars = [];
        const level = Math.ceil((parseInt(strength) || 0) / 25);
        
        for (let i = 1; i <= 4; i++) {
            const active = i <= level ? 'active' : '';
            bars.push(`<div class="signal-bar ${active}"></div>`);
        }
        
        return `<div class="signal-bars">${bars.join('')}</div>`;
    }
    
    selectNetwork(network) {
        this.selectedNetwork = network;
        
        // Update UI to show selection
        document.querySelectorAll('.network-item').forEach(item => {
            item.classList.remove('selected');
        });
        document.querySelector(`[data-ssid="${network.ssid}"]`).classList.add('selected');
        
        // Show connection form
        this.showConnectionForm(network);
    }
    
    showConnectionForm(network) {
        const form = document.getElementById('connection-form');
        const ssidInput = document.getElementById('selected-ssid');
        const passwordGroup = document.getElementById('password-group');
        const passwordInput = document.getElementById('password');
        
        ssidInput.value = network.ssid;
        
        // Hide password field for open networks
        if (network.security === 'open') {
            passwordGroup.style.display = 'none';
            passwordInput.value = '';
        } else {
            passwordGroup.style.display = 'block';
            passwordInput.focus();
        }
        
        form.style.display = 'block';
        form.scrollIntoView({ behavior: 'smooth' });
    }
    
    hideConnectionForm() {
        document.getElementById('connection-form').style.display = 'none';
        document.querySelectorAll('.network-item').forEach(item => {
            item.classList.remove('selected');
        });
        this.selectedNetwork = null;
    }
    
    async connectToNetwork() {
        if (!this.selectedNetwork) return;
        
        const password = document.getElementById('password').value;
        const ssid = this.selectedNetwork.ssid;
        
        this.isConnecting = true;
        this.setButtonLoading('connect-btn', true);
        this.showMessage('Connecting to network...', 'info');
        
        try {
            const response = await fetch('/api/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ssid: ssid,
                    password: password
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showMessage(data.message, 'success');
                this.hideConnectionForm();
                setTimeout(() => this.updateStatus(), 2000);
            } else {
                this.showMessage(`Connection failed: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Connection error:', error);
            this.showMessage('Failed to connect to network', 'error');
        } finally {
            this.isConnecting = false;
            this.setButtonLoading('connect-btn', false);
        }
    }
    
    async disconnect() {
        this.setButtonLoading('disconnect-btn', true);
        
        try {
            const response = await fetch('/api/disconnect');
            const data = await response.json();
            
            if (data.success) {
                this.showMessage(data.message, 'success');
                setTimeout(() => this.updateStatus(), 1000);
            } else {
                this.showMessage(`Disconnect failed: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Disconnect error:', error);
            this.showMessage('Failed to disconnect', 'error');
        } finally {
            this.setButtonLoading('disconnect-btn', false);
        }
    }
    
    togglePasswordVisibility() {
        const passwordInput = document.getElementById('password');
        const toggleBtn = document.getElementById('toggle-password');
        
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            toggleBtn.textContent = '🙈';
        } else {
            passwordInput.type = 'password';
            toggleBtn.textContent = '👁️';
        }
    }
    
    showLoading(show) {
        const loading = document.getElementById('loading');
        const networksList = document.getElementById('networks-list');
        
        if (show) {
            loading.style.display = 'block';
            networksList.style.display = 'none';
        } else {
            loading.style.display = 'none';
            networksList.style.display = 'block';
        }
    }
    
    setButtonLoading(buttonId, loading) {
        const button = document.getElementById(buttonId);
        const originalText = button.textContent;
        
        if (loading) {
            button.disabled = true;
            button.dataset.originalText = originalText;
            if (buttonId === 'scan-btn') {
                button.innerHTML = '🔄 Scanning...';
            } else if (buttonId === 'connect-btn') {
                button.textContent = 'Connecting...';
            } else if (buttonId === 'disconnect-btn') {
                button.textContent = 'Disconnecting...';
            }
        } else {
            button.disabled = false;
            if (button.dataset.originalText) {
                button.textContent = button.dataset.originalText;
                delete button.dataset.originalText;
            } else {
                button.textContent = originalText;
            }
        }
    }
    
    showMessage(message, type = 'info') {
        const container = document.getElementById('messages');
        const messageId = 'msg-' + Date.now();
        
        const messageDiv = document.createElement('div');
        messageDiv.id = messageId;
        messageDiv.className = `message message-${type}`;
        messageDiv.innerHTML = `
            ${this.escapeHtml(message)}
            <button class="message-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        container.appendChild(messageDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            const element = document.getElementById(messageId);
            if (element) {
                element.remove();
            }
        }, 5000);
    }
    
    handleScanResult(data) {
        if (data.success) {
            this.displayNetworks(data.networks);
        } else {
            this.showMessage(`WebSocket scan failed: ${data.error}`, 'error');
        }
    }
    
    updateDeviceInfo() {
        // Get basic device information
        const deviceInfo = document.getElementById('device-info');
        const userAgent = navigator.userAgent;
        let deviceType = 'Unknown Device';
        
        if (/Mobi|Android/i.test(userAgent)) {
            deviceType = 'Mobile Device';
        } else if (/Tablet|iPad/i.test(userAgent)) {
            deviceType = 'Tablet';
        } else {
            deviceType = 'Desktop/Laptop';
        }
        
        deviceInfo.textContent = `${deviceType} (${navigator.platform})`;
    }
    
    // Access Point Management Methods
    async updateAPStatus() {
        try {
            const response = await fetch('/api/ap/status');
            const data = await response.json();
            
            if (data.success) {
                this.displayAPStatus(data.status);
            }
        } catch (error) {
            console.error('AP status update error:', error);
        }
    }
    
    displayAPStatus(status) {
        const indicator = document.getElementById('ap-status-indicator');
        const text = document.getElementById('ap-status-text');
        const info = document.getElementById('ap-info');
        const ssidSpan = document.getElementById('ap-ssid');
        const monitoringSpan = document.getElementById('ap-monitoring');
        const apInterfaceSpan = document.getElementById('ap-interface');
        const clientInterfaceSpan = document.getElementById('client-interface');
        const startBtn = document.getElementById('ap-start-btn');
        const stopBtn = document.getElementById('ap-stop-btn');
        const panel = document.getElementById('ap-panel');
        
        // Remove previous status classes
        panel.classList.remove('status-connected', 'status-disconnected');
        
        if (status.ap_active) {
            indicator.textContent = '📶';
            text.textContent = `Access Point Active: ${status.ap_ssid}`;
            info.style.display = 'block';
            ssidSpan.textContent = status.ap_ssid;
            monitoringSpan.textContent = status.monitoring ? 'Active' : 'Inactive';
            apInterfaceSpan.textContent = status.ap_device || 'Unknown';
            clientInterfaceSpan.textContent = status.client_interface || 'Unknown';
            startBtn.style.display = 'none';
            stopBtn.style.display = 'inline-block';
            panel.classList.add('status-connected');
        } else {
            indicator.textContent = '📴';
            text.textContent = 'Access Point Inactive';
            info.style.display = 'block';  // Show interface info even when AP is off
            ssidSpan.textContent = status.ap_ssid;
            monitoringSpan.textContent = status.monitoring ? 'Active' : 'Inactive';
            apInterfaceSpan.textContent = status.ap_device || 'Unknown';
            clientInterfaceSpan.textContent = status.client_interface || 'Unknown';
            startBtn.style.display = 'inline-block';
            stopBtn.style.display = 'none';
            panel.classList.add('status-disconnected');
        }
    }
    
    async startAccessPoint() {
        this.setButtonLoading('ap-start-btn', true);
        
        try {
            const response = await fetch('/api/ap/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showMessage(data.message, 'success');
                this.updateAPStatus();
            } else {
                this.showMessage(`Failed to start AP: ${data.message}`, 'error');
            }
        } catch (error) {
            console.error('Start AP error:', error);
            this.showMessage('Failed to start access point', 'error');
        } finally {
            this.setButtonLoading('ap-start-btn', false);
        }
    }
    
    async stopAccessPoint() {
        this.setButtonLoading('ap-stop-btn', true);
        
        try {
            const response = await fetch('/api/ap/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showMessage(data.message, 'success');
                this.updateAPStatus();
            } else {
                this.showMessage(`Failed to stop AP: ${data.message}`, 'error');
            }
        } catch (error) {
            console.error('Stop AP error:', error);
            this.showMessage('Failed to stop access point', 'error');
        } finally {
            this.setButtonLoading('ap-stop-btn', false);
        }
    }
    
    async showAPConfigModal() {
        // Load current configuration
        try {
            const response = await fetch('/api/ap/config');
            const data = await response.json();
            
            if (data.success) {
                const config = data.config;
                document.getElementById('ap-ssid-input').value = config.ap_ssid || '';
                document.getElementById('ap-password-input').value = ''; // Don't show password
                document.getElementById('ap-ip-input').value = config.ap_ip || '';
                document.getElementById('monitor-interval-input').value = config.monitor_interval || 60;
                document.getElementById('ap-wlan-input').value = config.ap_wlan_interface || 'wlan1';
                document.getElementById('client-wlan-input').value = config.client_wlan_interface || 'wlan0';
            }
        } catch (error) {
            console.error('Failed to load AP config:', error);
        }
        
        document.getElementById('ap-config-modal').style.display = 'flex';
    }
    
    hideAPConfigModal() {
        document.getElementById('ap-config-modal').style.display = 'none';
    }
    
    async saveAPConfig() {
        const form = document.getElementById('ap-config-form');
        const formData = new FormData(form);
        const config = {};
        
        for (let [key, value] of formData.entries()) {
            config[key] = value;
        }
        
        // Convert monitor_interval to number
        config.monitor_interval = parseInt(config.monitor_interval);
        
        try {
            const response = await fetch('/api/ap/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showMessage(data.message, 'success');
                this.hideAPConfigModal();
                this.updateAPStatus();
            } else {
                this.showMessage(`Failed to save config: ${data.message}`, 'error');
            }
        } catch (error) {
            console.error('Save AP config error:', error);
            this.showMessage('Failed to save configuration', 'error');
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CaptivePortal();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        // Page became visible, refresh status
        setTimeout(() => {
            if (window.captivePortal) {
                window.captivePortal.updateStatus();
            }
        }, 1000);
    }
});

// Handle network online/offline events
window.addEventListener('online', () => {
    console.log('Network came online');
});

window.addEventListener('offline', () => {
    console.log('Network went offline');
});