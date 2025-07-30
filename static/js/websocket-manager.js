/**
 * WebSocket Manager for Elite Crew Dashboard
 * Handles real-time communication with the backend
 */

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 2000;
        this.clientId = 'dashboard_' + Math.random().toString(36).substr(2, 9);
        this.onStatusChange = null;
        this.onMessage = null;
        this.heartbeatInterval = null;
    }

    connect() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${this.clientId}`;
            
            console.log(`🔌 Connecting to WebSocket: ${wsUrl}`);
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = this.handleOpen.bind(this);
            this.ws.onmessage = this.handleMessage.bind(this);
            this.ws.onclose = this.handleClose.bind(this);
            this.ws.onerror = this.handleError.bind(this);
            
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.scheduleReconnect();
        }
    }

    handleOpen(event) {
        console.log('🔌 WebSocket connected');
        this.reconnectAttempts = 0;
        
        if (this.onStatusChange) {
            this.onStatusChange('connected');
        }
        
        // Start heartbeat
        this.startHeartbeat();
        
        // Request initial status
        this.requestStatus();
    }

    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'pong') {
                // Heartbeat response received
                return;
            }
            
            if (this.onMessage) {
                this.onMessage(data);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }

    handleClose(event) {
        console.log('🔌 WebSocket disconnected', event.code, event.reason);
        
        if (this.onStatusChange) {
            this.onStatusChange('disconnected');
        }
        
        this.stopHeartbeat();
        this.scheduleReconnect();
    }

    handleError(error) {
        console.error('WebSocket error:', error);
    }

    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectInterval * this.reconnectAttempts;
            
            console.log(`🔄 Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
            
            setTimeout(() => {
                if (this.ws?.readyState !== WebSocket.OPEN) {
                    this.connect();
                }
            }, delay);
        } else {
            console.error('❌ Max reconnection attempts reached');
            if (this.onStatusChange) {
                this.onStatusChange('failed');
            }
        }
    }

    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.ws?.readyState === WebSocket.OPEN) {
                this.send({ type: 'ping' });
            }
        }, 30000); // Send ping every 30 seconds
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    send(data) {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected, cannot send message:', data);
        }
    }

    requestStatus() {
        this.send({ type: 'request_status' });
    }

    disconnect() {
        this.stopHeartbeat();
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Make it globally available
window.WebSocketManager = WebSocketManager;