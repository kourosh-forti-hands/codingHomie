"""
🔥 Elite Web Dashboard - Real-time Monitoring and Control Interface
Beautiful, responsive dashboard for monitoring the elite crew system
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uvicorn
from pathlib import Path
import websockets
from contextlib import asynccontextmanager

from database import EliteDatabase, ProjectStatus, TaskStatus, AgentStatus
from async_elite_system import AsyncEliteOrchestrator

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_ids: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_ids[websocket] = client_id
        logger.info(f"🔌 WebSocket client {client_id} connected")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            client_id = self.connection_ids.pop(websocket, "unknown")
            logger.info(f"🔌 WebSocket client {client_id} disconnected")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

# Global instances
database = EliteDatabase()
orchestrator = None
websocket_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    global orchestrator
    
    # Startup
    await database.initialize()
    orchestrator = AsyncEliteOrchestrator(database)
    await orchestrator.initialize()
    
    # Start background tasks
    asyncio.create_task(broadcast_system_status())
    
    logger.info("🚀 Elite Web Dashboard started successfully!")
    
    yield
    
    # Shutdown
    if orchestrator:
        await orchestrator.shutdown()
    logger.info("🛑 Elite Web Dashboard shut down gracefully")

# Create FastAPI app
app = FastAPI(
    title="Elite Crew Dashboard",
    description="Real-time monitoring and control interface for the Elite Multi-Agent System",
    version="1.0.0",
    lifespan=lifespan
)

# Set up static files and templates
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

# Create directories if they don't exist
templates_dir.mkdir(exist_ok=True)
static_dir.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(templates_dir))

# Mount static files
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/system/status")
async def get_system_status():
    """Get current system status"""
    if not orchestrator:
        return {"error": "System not initialized"}
    
    status = await orchestrator.get_real_time_status()
    return status

@app.get("/api/projects")
async def get_projects(limit: int = 10, offset: int = 0):
    """Get list of projects"""
    try:
        # This would be implemented with proper database queries
        # For now, return mock data
        projects = []
        for i in range(limit):
            projects.append({
                "id": f"proj_{i+offset+1}",
                "name": f"Project {i+offset+1}",
                "status": "completed" if i % 3 == 0 else "in_progress",
                "progress": min(100, (i + offset + 1) * 10),
                "created_at": (datetime.now() - timedelta(days=i)).isoformat()
            })
        
        return {
            "projects": projects,
            "total": limit + offset + 10,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        return {"error": str(e)}

@app.get("/api/agents")
async def get_agents():
    """Get list of agents and their status"""
    if not orchestrator:
        return {"error": "System not initialized"}
    
    try:
        status = await orchestrator.get_real_time_status()
        return {"agents": status["agents"]}
    except Exception as e:
        logger.error(f"Error fetching agents: {e}")
        return {"error": str(e)}

@app.get("/api/metrics")
async def get_performance_metrics():
    """Get performance metrics"""
    try:
        # Generate sample metrics data
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system_performance": {
                "cpu_usage": 45.2,
                "memory_usage": 68.7,
                "disk_usage": 34.1,
                "network_io": 15.3
            },
            "agent_metrics": {
                "total_tasks_completed": 1247,
                "tasks_per_hour": 156,
                "average_response_time": 2.3,
                "success_rate": 94.8
            },
            "quality_metrics": {
                "code_coverage": 87.5,
                "bugs_found": 12,
                "bugs_fixed": 10,
                "security_score": 96.2
            }
        }
        return metrics
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        return {"error": str(e)}

@app.post("/api/projects/create")
async def create_project(project_data: dict):
    """Create a new project"""
    if not orchestrator:
        return {"error": "System not initialized"}
    
    try:
        result = await orchestrator.execute_project_async(
            project_name=project_data.get("name", "New Project"),
            project_description=project_data.get("description", ""),
            complexity=project_data.get("complexity", "medium")
        )
        return {"success": True, "project": result}
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        return {"error": str(e)}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "ping":
                await websocket_manager.send_personal_message(
                    json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}),
                    websocket
                )
            elif message_data.get("type") == "request_status":
                if orchestrator:
                    status = await orchestrator.get_real_time_status()
                    await websocket_manager.send_personal_message(
                        json.dumps({"type": "status_update", "data": status}),
                        websocket
                    )
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

async def broadcast_system_status():
    """Background task to broadcast system status updates"""
    while True:
        try:
            if orchestrator and websocket_manager.active_connections:
                status = await orchestrator.get_real_time_status()
                message = json.dumps({
                    "type": "status_update",
                    "data": status,
                    "timestamp": datetime.now().isoformat()
                })
                await websocket_manager.broadcast(message)
            
            await asyncio.sleep(5)  # Update every 5 seconds
            
        except Exception as e:
            logger.error(f"Error broadcasting system status: {e}")
            await asyncio.sleep(10)

# Create dashboard HTML template
dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔥 Elite Crew Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            min-height: 100vh;
        }

        .dashboard {
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }

        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .status-card {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .status-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        }

        .status-card h3 {
            margin-bottom: 15px;
            font-size: 1.3em;
            color: #fff;
        }

        .metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .metric:last-child {
            border-bottom: none;
        }

        .metric-value {
            font-weight: bold;
            color: #4ade80;
        }

        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }

        .agent-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
        }

        .agent-card.online {
            border-left: 4px solid #4ade80;
        }

        .agent-card.busy {
            border-left: 4px solid #fbbf24;
        }

        .agent-card.offline {
            border-left: 4px solid #ef4444;
        }

        .agent-name {
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .agent-status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            margin-bottom: 10px;
        }

        .status-online {
            background: #4ade80;
            color: #000;
        }

        .status-busy {
            background: #fbbf24;
            color: #000;
        }

        .status-offline {
            background: #ef4444;
            color: #fff;
        }

        .controls {
            text-align: center;
            margin-top: 30px;
        }

        .btn {
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: #fff;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            margin: 0 10px;
            transition: all 0.3s ease;
            font-size: 1em;
        }

        .btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }

        .btn-primary {
            background: #4ade80;
            color: #000;
        }

        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            transition: all 0.3s ease;
        }

        .connected {
            background: #4ade80;
            color: #000;
        }

        .disconnected {
            background: #ef4444;
            color: #fff;
        }

        .loading {
            text-align: center;
            padding: 50px;
            font-size: 1.2em;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .pulse {
            animation: pulse 2s infinite;
        }

        .charts-container {
            margin-top: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }

        .chart-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
        }

        .chart-card h4 {
            margin-bottom: 20px;
            text-align: center;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🔥 Elite Crew Dashboard</h1>
            <p>Real-time monitoring and control interface</p>
        </div>

        <div class="connection-status disconnected" id="connectionStatus">
            🔴 Disconnected
        </div>

        <div id="loadingIndicator" class="loading pulse">
            🚀 Initializing Elite Crew System...
        </div>

        <div id="dashboardContent" style="display: none;">
            <div class="status-grid">
                <div class="status-card">
                    <h3>📊 System Overview</h3>
                    <div class="metric">
                        <span>Total Agents:</span>
                        <span class="metric-value" id="totalAgents">-</span>
                    </div>
                    <div class="metric">
                        <span>Active Agents:</span>
                        <span class="metric-value" id="activeAgents">-</span>
                    </div>
                    <div class="metric">
                        <span>System Load:</span>
                        <span class="metric-value" id="systemLoad">-</span>
                    </div>
                    <div class="metric">
                        <span>Concurrent Tasks:</span>
                        <span class="metric-value" id="concurrentTasks">-</span>
                    </div>
                </div>

                <div class="status-card">
                    <h3>⚡ Performance Metrics</h3>
                    <div class="metric">
                        <span>Tasks Completed:</span>
                        <span class="metric-value" id="tasksCompleted">-</span>
                    </div>
                    <div class="metric">
                        <span>Success Rate:</span>
                        <span class="metric-value" id="successRate">-</span>
                    </div>
                    <div class="metric">
                        <span>Avg Response Time:</span>
                        <span class="metric-value" id="avgResponseTime">-</span>
                    </div>
                    <div class="metric">
                        <span>Last Update:</span>
                        <span class="metric-value" id="lastUpdate">-</span>
                    </div>
                </div>
            </div>

            <div class="agents-grid" id="agentsGrid">
                <!-- Agent cards will be dynamically populated -->
            </div>

            <div class="controls">
                <button class="btn btn-primary" onclick="createNewProject()">
                    🚀 Create New Project
                </button>
                <button class="btn" onclick="refreshData()">
                    🔄 Refresh Data
                </button>
                <button class="btn" onclick="exportMetrics()">
                    📊 Export Metrics
                </button>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;

        function connectWebSocket() {
            const clientId = 'dashboard_' + Math.random().toString(36).substr(2, 9);
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${clientId}`;

            ws = new WebSocket(wsUrl);

            ws.onopen = function(event) {
                console.log('🔌 WebSocket connected');
                document.getElementById('connectionStatus').className = 'connection-status connected';
                document.getElementById('connectionStatus').innerHTML = '🟢 Connected';
                reconnectAttempts = 0;
                
                // Send ping to keep connection alive
                setInterval(() => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({type: 'ping'}));
                    }
                }, 30000);
            };

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === 'status_update') {
                    updateDashboard(data.data);
                }
            };

            ws.onclose = function(event) {
                console.log('🔌 WebSocket disconnected');
                document.getElementById('connectionStatus').className = 'connection-status disconnected';
                document.getElementById('connectionStatus').innerHTML = '🔴 Disconnected';
                
                // Attempt to reconnect
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    setTimeout(connectWebSocket, 2000 * reconnectAttempts);
                }
            };

            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }

        function updateDashboard(data) {
            // Hide loading indicator and show content
            document.getElementById('loadingIndicator').style.display = 'none';
            document.getElementById('dashboardContent').style.display = 'block';

            // Update system metrics
            document.getElementById('totalAgents').textContent = data.total_agents || 0;
            document.getElementById('activeAgents').textContent = data.active_agents || 0;
            document.getElementById('systemLoad').textContent = (data.system_load || 0).toFixed(1) + '%';
            document.getElementById('concurrentTasks').textContent = data.total_concurrent_tasks || 0;

            // Calculate aggregate metrics
            let totalTasksCompleted = 0;
            let totalSuccessRate = 0;
            let totalAvgTime = 0;
            let agentCount = 0;

            const agentsGrid = document.getElementById('agentsGrid');
            agentsGrid.innerHTML = '';

            for (const [agentId, agentData] of Object.entries(data.agents || {})) {
                totalTasksCompleted += agentData.tasks_executed || 0;
                totalSuccessRate += agentData.success_rate || 0;
                totalAvgTime += agentData.average_execution_time || 0;
                agentCount++;

                // Create agent card
                const agentCard = document.createElement('div');
                agentCard.className = `agent-card ${agentData.status}`;
                agentCard.innerHTML = `
                    <div class="agent-name">${agentData.name}</div>
                    <div class="agent-status status-${agentData.status}">
                        ${agentData.status.toUpperCase()}
                    </div>
                    <div class="metric">
                        <span>Tasks:</span>
                        <span>${agentData.current_tasks}/${agentData.max_concurrent}</span>
                    </div>
                    <div class="metric">
                        <span>Completed:</span>
                        <span>${agentData.tasks_executed}</span>
                    </div>
                    <div class="metric">
                        <span>Success Rate:</span>
                        <span>${agentData.success_rate.toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span>Avg Time:</span>
                        <span>${agentData.average_execution_time.toFixed(2)}s</span>
                    </div>
                `;
                agentsGrid.appendChild(agentCard);
            }

            // Update aggregate metrics
            document.getElementById('tasksCompleted').textContent = totalTasksCompleted;
            document.getElementById('successRate').textContent = 
                agentCount > 0 ? (totalSuccessRate / agentCount).toFixed(1) + '%' : '0%';
            document.getElementById('avgResponseTime').textContent = 
                agentCount > 0 ? (totalAvgTime / agentCount).toFixed(2) + 's' : '0s';
            document.getElementById('lastUpdate').textContent = 
                new Date().toLocaleTimeString();
        }

        function createNewProject() {
            const projectName = prompt('Enter project name:');
            if (!projectName) return;

            const projectDescription = prompt('Enter project description:');
            if (!projectDescription) return;

            const complexity = prompt('Enter complexity (low/medium/high):', 'medium');

            fetch('/api/projects/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: projectName,
                    description: projectDescription,
                    complexity: complexity || 'medium'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('🎉 Project created successfully!');
                    refreshData();
                } else {
                    alert('❌ Error creating project: ' + data.error);
                }
            })
            .catch(error => {
                alert('❌ Network error: ' + error.message);
            });
        }

        function refreshData() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({type: 'request_status'}));
            }
        }

        function exportMetrics() {
            fetch('/api/metrics')
            .then(response => response.json())
            .then(data => {
                const blob = new Blob([JSON.stringify(data, null, 2)], {
                    type: 'application/json'
                });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `elite_metrics_${new Date().toISOString().slice(0, 10)}.json`;
                a.click();
                URL.revokeObjectURL(url);
            })
            .catch(error => {
                alert('❌ Error exporting metrics: ' + error.message);
            });
        }

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            connectWebSocket();
            
            // Refresh data every 30 seconds
            setInterval(refreshData, 30000);
        });
    </script>
</body>
</html>
"""

# Write the dashboard HTML template
with open(templates_dir / "dashboard.html", "w") as f:
    f.write(dashboard_html)

def run_dashboard(host: str = "127.0.0.1", port: int = 8000):
    """Run the elite web dashboard"""
    print("🔥 ELITE WEB DASHBOARD - REAL-TIME MONITORING IS FIRE! 🔥")
    print("=" * 60)
    print(f"🌐 Dashboard URL: http://{host}:{port}")
    print("📊 Features:")
    print("  - Real-time agent monitoring")
    print("  - Live performance metrics")
    print("  - WebSocket updates")
    print("  - Project management")
    print("  - Performance analytics")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    run_dashboard()