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

@app.get("/project/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: str):
    """Project detail page"""
    return templates.TemplateResponse("project_detail.html", {"request": request, "project_id": project_id})

@app.get("/api/system/status")
async def get_system_status():
    """Get current system status"""
    if not orchestrator:
        return {"error": "System not initialized"}
    
    status = await orchestrator.get_real_time_status()
    return status

@app.get("/api/projects")
async def get_projects(limit: int = 10, offset: int = 0):
    """Get list of projects from database"""
    try:
        from sqlalchemy import select, func
        from database import Project
        
        async with database.get_session() as session:
            # Get total count
            count_result = await session.execute(select(func.count(Project.id)))
            total = count_result.scalar() or 0
            
            # Get projects with pagination
            result = await session.execute(
                select(Project)
                .order_by(Project.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            
            projects = []
            for project in result.scalars().all():
                # Calculate progress based on tasks (placeholder logic)
                progress = 0
                if project.status == "completed":
                    progress = 100
                elif project.status == "in_progress":
                    progress = 50
                elif project.status == "planning":
                    progress = 10
                
                projects.append({
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "status": project.status,
                    "complexity": project.complexity,
                    "progress": progress,
                    "estimated_hours": project.estimated_hours,
                    "actual_hours": project.actual_hours,
                    "created_at": project.created_at.isoformat() if project.created_at else None,
                    "started_at": project.started_at.isoformat() if project.started_at else None,
                    "completed_at": project.completed_at.isoformat() if project.completed_at else None
                })
        
        return {
            "projects": projects,
            "total": total,
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
    """Create a new project directly in database"""
    try:
        from database import Project
        
        async with database.get_session() as session:
            project = Project(
                name=project_data.get("name", "New Project"),
                description=project_data.get("description", ""),
                complexity=project_data.get("complexity", "medium"),
                estimated_hours=float(project_data.get("estimated_hours", 0))
            )
            session.add(project)
            await session.flush()
            await session.refresh(project)
            
            # Extract data while still in session
            project_data_result = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "complexity": project.complexity,
                "estimated_hours": project.estimated_hours,
                "created_at": project.created_at.isoformat() if project.created_at else None
            }
            
            logger.info(f"📋 Project created: {project.name} ({project.id})")
        
        return {"success": True, "project": project_data_result}
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        return {"error": str(e)}

@app.get("/api/projects/{project_id}/tasks")
async def get_project_tasks(project_id: str):
    """Get tasks for a specific project"""
    try:
        from sqlalchemy import select
        from database import Task
        
        async with database.get_session() as session:
            result = await session.execute(
                select(Task)
                .where(Task.project_id == project_id)
                .order_by(Task.created_at.desc())
            )
            
            tasks = []
            for task in result.scalars().all():
                tasks.append({
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "agent_id": task.agent_id,
                    "estimated_hours": task.estimated_hours,
                    "actual_hours": task.actual_hours,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                })
        
        return {"tasks": tasks}
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        return {"error": str(e)}

@app.post("/api/projects/{project_id}/tasks/create")
async def create_task(project_id: str, task_data: dict):
    """Create a new task for a project"""
    try:
        from database import Task
        
        async with database.get_session() as session:
            task = Task(
                project_id=project_id,
                title=task_data.get("title", "New Task"),
                description=task_data.get("description", ""),
                priority=int(task_data.get("priority", 2)),
                estimated_hours=float(task_data.get("estimated_hours", 0)),
                agent_id=task_data.get("agent_id")
            )
            session.add(task)
            await session.flush()
            await session.refresh(task)
            
            # Extract data while still in session
            task_result = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "agent_id": task.agent_id,
                "estimated_hours": task.estimated_hours,
                "created_at": task.created_at.isoformat() if task.created_at else None
            }
            
            logger.info(f"📝 Task created: {task.title} ({task.id})")
        
        return {"success": True, "task": task_result}
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return {"error": str(e)}

@app.post("/api/projects/{project_id}/execute")
async def execute_project(project_id: str):
    """Execute project - send tasks to agents"""
    try:
        from database import ProjectStatus
        
        # Update project status to in_progress  
        await database.update_project_status(project_id, ProjectStatus.IN_PROGRESS)
        
        # Get project tasks
        from sqlalchemy import select
        from database import Task, Agent
        
        async with database.get_session() as session:
            # Get all pending tasks for this project
            task_result = await session.execute(
                select(Task).where(
                    Task.project_id == project_id,
                    Task.status == 'pending'
                )
            )
            pending_tasks = task_result.scalars().all()
            
            # Get available agents
            agent_result = await session.execute(
                select(Agent).where(Agent.status == 'online')
            )
            online_agents = agent_result.scalars().all()
            
            if not online_agents:
                return {"error": "No agents available"}
            
            if not pending_tasks:
                return {"error": "No pending tasks to execute"}
            
            # Assign tasks to agents (simple round-robin for now)
            assignments = []
            agent_index = 0
            
            for task in pending_tasks:
                if not task.agent_id:  # Only assign if not already assigned
                    selected_agent = online_agents[agent_index % len(online_agents)]
                    task.agent_id = selected_agent.id
                    task.status = 'in_progress'
                    task.started_at = datetime.utcnow()
                    
                    assignments.append({
                        "task_id": task.id,
                        "task_title": task.title,
                        "agent_id": selected_agent.id,
                        "agent_name": selected_agent.name
                    })
                    
                    agent_index += 1
            
            await session.commit()
            
            logger.info(f"🚀 Project {project_id} execution started with {len(assignments)} task assignments")
            
            return {
                "success": True,
                "message": f"Project execution started! {len(assignments)} tasks assigned to agents.",
                "assignments": assignments
            }
            
    except Exception as e:
        logger.error(f"Error executing project: {e}")
        return {"error": str(e)}

@app.post("/api/tasks/{task_id}/status")
async def update_task_status(task_id: str, status_data: dict):
    """Update task status (for agents to report progress)"""
    try:
        from database import TaskStatus
        
        status = status_data.get("status")
        notes = status_data.get("notes", "")
        
        if status not in ["pending", "in_progress", "completed", "failed", "blocked"]:
            return {"error": "Invalid status"}
        
        await database.update_task_status(task_id, TaskStatus(status), notes)
        
        return {"success": True, "message": f"Task {task_id} status updated to {status}"}
        
    except Exception as e:
        logger.error(f"Error updating task status: {e}")
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

        .projects-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }

        .project-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }

        .project-card:hover {
            transform: translateY(-2px);
        }

        .project-name {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .project-description {
            color: rgba(255, 255, 255, 0.8);
            margin-bottom: 15px;
            font-size: 0.9em;
        }

        .project-status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }

        .project-status.planning {
            background: rgba(59, 130, 246, 0.3);
            color: #93c5fd;
        }

        .project-status.in_progress {
            background: rgba(34, 197, 94, 0.3);
            color: #86efac;
        }

        .project-status.completed {
            background: rgba(16, 185, 129, 0.3);
            color: #6ee7b7;
        }

        .btn-sm {
            font-size: 0.8em;
            padding: 4px 8px;
            background: rgba(59, 130, 246, 0.2);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: #93c5fd;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-sm:hover {
            background: rgba(59, 130, 246, 0.3);
            transform: translateY(-1px);
        }

        .project-tasks {
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding-top: 10px;
        }

        .task-item {
            transition: transform 0.2s ease;
        }

        .task-item:hover {
            transform: translateY(-1px);
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

            <!-- Projects Section -->
            <div class="status-card">
                <h3>📋 Projects</h3>
                <div class="projects-grid" id="projectsGrid">
                    <!-- Project cards will be dynamically populated -->
                </div>
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
                
            // Load projects
            loadProjects();
        }

        async function loadProjects() {
            try {
                const response = await fetch('/api/projects');
                const data = await response.json();
                
                const projectsGrid = document.getElementById('projectsGrid');
                projectsGrid.innerHTML = '';
                
                if (data.projects && data.projects.length > 0) {
                    data.projects.forEach(project => {
                        const projectCard = document.createElement('div');
                        projectCard.className = 'project-card';
                        projectCard.style.cursor = 'pointer';
                        projectCard.innerHTML = `
                            <div class="project-name">${project.name}</div>
                            <div class="project-description">${project.description || 'No description'}</div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px;">
                                <span class="project-status ${project.status}">${project.status}</span>
                                <div style="font-size: 0.9em; color: rgba(255, 255, 255, 0.7);">
                                    Progress: ${project.progress}%
                                </div>
                            </div>
                            <div style="margin-top: 10px; font-size: 0.8em; color: rgba(255, 255, 255, 0.6);">
                                Created: ${new Date(project.created_at).toLocaleDateString()}
                            </div>
                            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.2);">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-size: 0.9em; color: rgba(255, 255, 255, 0.8);">
                                        📝 Tasks: <span id="taskCount-${project.id}">Loading...</span>
                                    </span>
                                    <button class="btn btn-sm" onclick="createTask('${project.id}')" style="font-size: 0.8em; padding: 4px 8px;">
                                        ➕ Add Task
                                    </button>
                                </div>
                            </div>
                            <div id="tasks-${project.id}" class="project-tasks" style="display: none; margin-top: 15px;">
                                <!-- Tasks will be loaded here -->
                            </div>
                        `;
                        projectCard.onclick = (e) => {
                            if (e.target.tagName !== 'BUTTON') {
                                window.location.href = `/project/${project.id}`;
                            }
                        };
                        projectsGrid.appendChild(projectCard);
                        
                        // Load task count
                        loadTaskCount(project.id);
                    });
                } else {
                    projectsGrid.innerHTML = '<div style="text-align: center; color: rgba(255, 255, 255, 0.6); padding: 20px;">No projects yet. Create your first project!</div>';
                }
            } catch (error) {
                console.error('Error loading projects:', error);
                const projectsGrid = document.getElementById('projectsGrid');
                projectsGrid.innerHTML = '<div style="text-align: center; color: #ef4444; padding: 20px;">Error loading projects</div>';
            }
        }

        async function loadTaskCount(projectId) {
            try {
                const response = await fetch(`/api/projects/${projectId}/tasks`);
                const data = await response.json();
                const taskCount = data.tasks ? data.tasks.length : 0;
                const completedTasks = data.tasks ? data.tasks.filter(t => t.status === 'completed').length : 0;
                document.getElementById(`taskCount-${projectId}`).textContent = `${completedTasks}/${taskCount}`;
            } catch (error) {
                console.error('Error loading task count:', error);
                document.getElementById(`taskCount-${projectId}`).textContent = 'Error';
            }
        }

        async function toggleProjectTasks(projectId) {
            const tasksDiv = document.getElementById(`tasks-${projectId}`);
            
            if (tasksDiv.style.display === 'none') {
                // Show tasks
                tasksDiv.style.display = 'block';
                await loadProjectTasks(projectId);
            } else {
                // Hide tasks
                tasksDiv.style.display = 'none';
            }
        }

        async function loadProjectTasks(projectId) {
            try {
                const response = await fetch(`/api/projects/${projectId}/tasks`);
                const data = await response.json();
                const tasksDiv = document.getElementById(`tasks-${projectId}`);
                
                if (data.tasks && data.tasks.length > 0) {
                    tasksDiv.innerHTML = '<div style="font-weight: bold; margin-bottom: 10px;">📋 Project Tasks:</div>' +
                        data.tasks.map(task => `
                            <div class="task-item" style="background: rgba(255,255,255,0.05); margin: 5px 0; padding: 10px; border-radius: 8px; border-left: 3px solid ${getTaskColor(task.status)};">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <div style="font-weight: bold;">${task.title}</div>
                                        <div style="font-size: 0.8em; color: rgba(255,255,255,0.7);">${task.description || 'No description'}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div class="task-status ${task.status}" style="font-size: 0.7em; padding: 2px 6px; border-radius: 10px; background: rgba(255,255,255,0.1);">
                                            ${task.status.toUpperCase()}
                                        </div>
                                        <div style="font-size: 0.7em; color: rgba(255,255,255,0.5); margin-top: 2px;">
                                            Priority: ${task.priority} | ${task.estimated_hours}h
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('');
                } else {
                    tasksDiv.innerHTML = '<div style="text-align: center; color: rgba(255,255,255,0.6); padding: 20px;">No tasks yet. Add your first task!</div>';
                }
            } catch (error) {
                console.error('Error loading project tasks:', error);
                const tasksDiv = document.getElementById(`tasks-${projectId}`);
                tasksDiv.innerHTML = '<div style="color: #ef4444; text-align: center; padding: 20px;">Error loading tasks</div>';
            }
        }

        function getTaskColor(status) {
            switch(status) {
                case 'completed': return '#10b981';
                case 'in_progress': return '#f59e0b';
                case 'failed': return '#ef4444';
                case 'blocked': return '#6b7280';
                default: return '#3b82f6';
            }
        }

        async function createTask(projectId) {
            const taskTitle = prompt('Enter task title:');
            if (!taskTitle) return;
            
            const taskDescription = prompt('Enter task description:');
            const priority = prompt('Enter priority (1=low, 2=medium, 3=high, 4=critical):', '2');
            const estimatedHours = prompt('Enter estimated hours:', '1');
            
            try {
                const response = await fetch(`/api/projects/${projectId}/tasks/create`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        title: taskTitle,
                        description: taskDescription,
                        priority: parseInt(priority) || 2,
                        estimated_hours: parseFloat(estimatedHours) || 1
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('✅ Task created successfully!');
                    loadTaskCount(projectId);
                    // Refresh tasks if they're currently visible
                    const tasksDiv = document.getElementById(`tasks-${projectId}`);
                    if (tasksDiv.style.display !== 'none') {
                        loadProjectTasks(projectId);
                    }
                } else {
                    alert('❌ Error creating task: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                alert('❌ Network error: ' + error.message);
            }
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
            loadProjects();
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
            loadProjects();
            
            // Refresh data every 30 seconds
            setInterval(refreshData, 30000);
        });
    </script>
</body>
</html>
"""

# Create project detail HTML template
project_detail_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Detail - Elite Crew System</title>
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

        .container {
            padding: 20px;
            max-width: 1200px;
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

        .nav-back {
            display: inline-block;
            margin-bottom: 20px;
            padding: 8px 16px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            text-decoration: none;
            color: #fff;
            transition: transform 0.2s ease;
        }

        .nav-back:hover {
            transform: translateY(-2px);
            background: rgba(255, 255, 255, 0.2);
        }

        .project-header {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }

        .project-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
        }

        .tab {
            padding: 12px 24px;
            background: rgba(255, 255, 255, 0.1);
            border: none;
            border-radius: 8px;
            color: #fff;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .tab.active {
            background: rgba(59, 130, 246, 0.3);
            color: #93c5fd;
        }

        .tab-content {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            min-height: 400px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.9);
        }

        .form-input, .form-textarea, .form-select {
            width: 100%;
            padding: 12px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            font-size: 14px;
        }

        .form-input::placeholder, .form-textarea::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s ease;
            margin-right: 10px;
        }

        .btn-primary {
            background: rgba(59, 130, 246, 0.3);
            color: #93c5fd;
            border: 1px solid rgba(59, 130, 246, 0.5);
        }

        .btn-primary:hover {
            background: rgba(59, 130, 246, 0.5);
            transform: translateY(-2px);
        }

        .btn-success {
            background: rgba(34, 197, 94, 0.3);
            color: #86efac;
            border: 1px solid rgba(34, 197, 94, 0.5);
        }

        .task-list {
            display: grid;
            gap: 15px;
        }

        .task-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            border-left: 4px solid;
            transition: transform 0.2s ease;
        }

        .task-card:hover {
            transform: translateY(-2px);
        }

        .task-card.pending { border-left-color: #3b82f6; }
        .task-card.in_progress { border-left-color: #f59e0b; }
        .task-card.completed { border-left-color: #10b981; }
        .task-card.failed { border-left-color: #ef4444; }

        .requirements-list {
            list-style: none;
            padding: 0;
        }

        .requirements-list li {
            background: rgba(255, 255, 255, 0.05);
            margin: 8px 0;
            padding: 12px;
            border-radius: 8px;
            border-left: 3px solid #3b82f6;
        }

        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .grid-3 {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }

        .status-badge.planning {
            background: rgba(59, 130, 246, 0.3);
            color: #93c5fd;
        }

        .status-badge.in_progress {
            background: rgba(234, 179, 8, 0.3);
            color: #fde047;
        }

        .status-badge.completed {
            background: rgba(34, 197, 94, 0.3);
            color: #86efac;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="nav-back">← Back to Dashboard</a>
        
        <div class="project-header" id="projectHeader">
            <h1 id="projectName">Loading...</h1>
            <p id="projectDescription">Loading project details...</p>
            <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span class="status-badge" id="projectStatus">loading</span>
                    <span style="margin-left: 15px; color: rgba(255,255,255,0.7);">
                        Progress: <span id="projectProgress">0</span>%
                    </span>
                </div>
                <div>
                    <button class="btn btn-success" id="executeBtn" onclick="executeProject()" style="display: none;">
                        🚀 Execute Project
                    </button>
                    <button class="btn" id="stopBtn" onclick="stopProject()" style="display: none;">
                        ⏹️ Stop Project
                    </button>
                </div>
            </div>
        </div>

        <div class="project-tabs">
            <button class="tab active" onclick="showTab('overview')">📊 Overview</button>
            <button class="tab" onclick="showTab('tasks')">📝 Tasks</button>
            <button class="tab" onclick="showTab('requirements')">📋 Requirements</button>
            <button class="tab" onclick="showTab('settings')">⚙️ Settings</button>
        </div>

        <div class="tab-content">
            <!-- Overview Tab -->
            <div id="overview-content" class="tab-pane active">
                <h3>Project Overview</h3>
                <div class="grid-2" style="margin-top: 20px;">
                    <div>
                        <h4>Project Statistics</h4>
                        <div style="margin-top: 15px;">
                            <p>📝 Total Tasks: <span id="totalTasks">0</span></p>
                            <p>✅ Completed: <span id="completedTasks">0</span></p>
                            <p>🔄 In Progress: <span id="inProgressTasks">0</span></p>
                            <p>⏱️ Estimated Hours: <span id="estimatedHours">0</span></p>
                            <p>📅 Created: <span id="createdDate">-</span></p>
                        </div>
                    </div>
                    <div>
                        <h4>Recent Activity</h4>
                        <div id="recentActivity" style="margin-top: 15px;">
                            <p style="color: rgba(255,255,255,0.6);">Loading activity...</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tasks Tab -->
            <div id="tasks-content" class="tab-pane" style="display: none;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3>Project Tasks</h3>
                    <button class="btn btn-primary" onclick="showAddTaskForm()">➕ Add New Task</button>
                </div>
                
                <div id="addTaskForm" style="display: none; background: rgba(255,255,255,0.1); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                    <h4>Add New Task</h4>
                    <div class="grid-2" style="margin-top: 15px;">
                        <div class="form-group">
                            <label class="form-label">Task Title</label>
                            <input type="text" id="taskTitle" class="form-input" placeholder="Enter task title">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Priority</label>
                            <select id="taskPriority" class="form-select">
                                <option value="1">Low</option>
                                <option value="2" selected>Medium</option>
                                <option value="3">High</option>
                                <option value="4">Critical</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Description</label>
                        <textarea id="taskDescription" class="form-textarea" rows="3" placeholder="Describe the task..."></textarea>
                    </div>
                    <div class="grid-3">
                        <div class="form-group">
                            <label class="form-label">Estimated Hours</label>
                            <input type="number" id="taskHours" class="form-input" placeholder="1" min="0.5" step="0.5">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Assign Agent</label>
                            <select id="taskAgent" class="form-select">
                                <option value="">Auto-assign</option>
                            </select>
                        </div>
                        <div class="form-group" style="display: flex; align-items: end; gap: 10px;">
                            <button class="btn btn-success" onclick="createTask()">Create Task</button>
                            <button class="btn" onclick="hideAddTaskForm()">Cancel</button>
                        </div>
                    </div>
                </div>

                <div id="tasksList" class="task-list">
                    <p style="color: rgba(255,255,255,0.6);">Loading tasks...</p>
                </div>
            </div>

            <!-- Requirements Tab -->
            <div id="requirements-content" class="tab-pane" style="display: none;">
                <h3>Project Requirements</h3>
                <div style="margin-top: 20px;">
                    <div class="form-group">
                        <label class="form-label">Add Requirement</label>
                        <div style="display: flex; gap: 10px;">
                            <input type="text" id="newRequirement" class="form-input" placeholder="Enter project requirement...">
                            <button class="btn btn-primary" onclick="addRequirement()">Add</button>
                        </div>
                    </div>
                    <ul id="requirementsList" class="requirements-list">
                        <!-- Requirements will be loaded here -->
                    </ul>
                </div>
            </div>

            <!-- Settings Tab -->
            <div id="settings-content" class="tab-pane" style="display: none;">
                <h3>Project Settings</h3>
                <div style="margin-top: 20px;">
                    <div class="grid-2">
                        <div class="form-group">
                            <label class="form-label">Project Name</label>
                            <input type="text" id="settingsName" class="form-input">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Complexity</label>
                            <select id="settingsComplexity" class="form-select">
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Description</label>
                        <textarea id="settingsDescription" class="form-textarea" rows="4"></textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Estimated Hours</label>
                        <input type="number" id="settingsHours" class="form-input" min="1" step="1">
                    </div>
                    <button class="btn btn-success" onclick="updateProject()">Save Changes</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        const projectId = '{{ project_id }}';
        let currentProject = null;

        // Tab management
        function showTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.style.display = 'none';
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab content
            document.getElementById(tabName + '-content').style.display = 'block';
            
            // Add active class to selected tab
            event.target.classList.add('active');
        }

        // Load project data
        async function loadProject() {
            try {
                const response = await fetch(`/api/projects`);
                const data = await response.json();
                
                currentProject = data.projects.find(p => p.id === projectId);
                if (!currentProject) {
                    document.getElementById('projectName').textContent = 'Project Not Found';
                    return;
                }
                
                // Update header
                document.getElementById('projectName').textContent = currentProject.name;
                document.getElementById('projectDescription').textContent = currentProject.description || 'No description';
                document.getElementById('projectStatus').textContent = currentProject.status;
                document.getElementById('projectStatus').className = `status-badge ${currentProject.status}`;
                document.getElementById('projectProgress').textContent = currentProject.progress;
                
                // Update overview
                document.getElementById('estimatedHours').textContent = currentProject.estimated_hours || 0;
                document.getElementById('createdDate').textContent = new Date(currentProject.created_at).toLocaleDateString();
                
                // Update settings form
                document.getElementById('settingsName').value = currentProject.name;
                document.getElementById('settingsDescription').value = currentProject.description || '';
                document.getElementById('settingsComplexity').value = currentProject.complexity || 'medium';
                document.getElementById('settingsHours').value = currentProject.estimated_hours || 0;
                
                // Show appropriate execution button
                updateExecutionButtons(currentProject.status);
                
                // Load tasks
                await loadTasks();
                
            } catch (error) {
                console.error('Error loading project:', error);
            }
        }

        // Load tasks
        async function loadTasks() {
            try {
                const response = await fetch(`/api/projects/${projectId}/tasks`);
                const data = await response.json();
                const tasks = data.tasks || [];
                
                // Update overview stats
                const completedTasks = tasks.filter(t => t.status === 'completed');
                const inProgressTasks = tasks.filter(t => t.status === 'in_progress');
                
                document.getElementById('totalTasks').textContent = tasks.length;
                document.getElementById('completedTasks').textContent = completedTasks.length;
                document.getElementById('inProgressTasks').textContent = inProgressTasks.length;
                
                // Update tasks list
                const tasksList = document.getElementById('tasksList');
                if (tasks.length === 0) {
                    tasksList.innerHTML = '<p style="color: rgba(255,255,255,0.6);">No tasks yet. Add your first task!</p>';
                } else {
                    tasksList.innerHTML = tasks.map(task => `
                        <div class="task-card ${task.status}">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h4>${task.title}</h4>
                                    <p style="color: rgba(255,255,255,0.7); margin: 8px 0;">${task.description || 'No description'}</p>
                                    <div style="font-size: 0.8em; color: rgba(255,255,255,0.6);">
                                        Priority: ${task.priority} | Estimated: ${task.estimated_hours}h
                                        ${task.agent_id ? ` | Agent: ${task.agent_id}` : ''}
                                    </div>
                                </div>
                                <div class="status-badge ${task.status}">
                                    ${task.status.replace('_', ' ')}
                                </div>
                            </div>
                        </div>
                    `).join('');
                }
            } catch (error) {
                console.error('Error loading tasks:', error);
            }
        }

        // Task management
        function showAddTaskForm() {
            document.getElementById('addTaskForm').style.display = 'block';
        }

        function hideAddTaskForm() {
            document.getElementById('addTaskForm').style.display = 'none';
            // Clear form
            document.getElementById('taskTitle').value = '';
            document.getElementById('taskDescription').value = '';
            document.getElementById('taskHours').value = '';
            document.getElementById('taskPriority').value = '2';
            document.getElementById('taskAgent').value = '';
        }

        async function createTask() {
            const title = document.getElementById('taskTitle').value;
            const description = document.getElementById('taskDescription').value;
            const priority = document.getElementById('taskPriority').value;
            const hours = document.getElementById('taskHours').value;
            const agentId = document.getElementById('taskAgent').value;
            
            if (!title) {
                alert('Please enter a task title');
                return;
            }
            
            try {
                const response = await fetch(`/api/projects/${projectId}/tasks/create`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        title: title,
                        description: description,
                        priority: parseInt(priority),
                        estimated_hours: parseFloat(hours) || 1,
                        agent_id: agentId || null
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('✅ Task created successfully!');
                    hideAddTaskForm();
                    await loadTasks();
                } else {
                    alert('❌ Error creating task: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                alert('❌ Network error: ' + error.message);
            }
        }

        // Requirements management
        function addRequirement() {
            const requirement = document.getElementById('newRequirement').value;
            if (!requirement) return;
            
            const requirementsList = document.getElementById('requirementsList');
            const li = document.createElement('li');
            li.innerHTML = `
                ${requirement}
                <button style="float: right; background: rgba(239,68,68,0.3); border: none; color: #fca5a5; padding: 2px 8px; border-radius: 4px; cursor: pointer;" onclick="this.parentElement.remove()">
                    Remove
                </button>
            `;
            requirementsList.appendChild(li);
            document.getElementById('newRequirement').value = '';
        }

        // Project settings
        async function updateProject() {
            // This would update the project settings
            alert('Project settings updated! (Feature coming soon)');
        }

        // Project execution
        function updateExecutionButtons(status) {
            const executeBtn = document.getElementById('executeBtn');
            const stopBtn = document.getElementById('stopBtn');
            
            if (status === 'planning') {
                executeBtn.style.display = 'inline-block';
                stopBtn.style.display = 'none';
            } else if (status === 'in_progress') {
                executeBtn.style.display = 'none';
                stopBtn.style.display = 'inline-block';
            } else {
                executeBtn.style.display = 'none';
                stopBtn.style.display = 'none';
            }
        }

        async function executeProject() {
            if (!confirm('Start project execution? This will assign tasks to available agents.')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/projects/${projectId}/execute`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const data = await response.json();
                if (data.success) {
                    alert(`✅ ${data.message}\\n\\nTask Assignments:\\n${data.assignments.map(a => `• ${a.task_title} → ${a.agent_name}`).join('\\n')}`);
                    
                    // Refresh project data
                    await loadProject();
                } else {
                    alert('❌ Error executing project: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                alert('❌ Network error: ' + error.message);
            }
        }

        async function stopProject() {
            if (!confirm('Stop project execution? This will pause all active tasks.')) {
                return;
            }
            
            alert('⏸️ Project stopping functionality coming soon!');
        }

        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            loadProject();
        });
    </script>
</body>
</html>
"""

# Write the dashboard HTML template
with open(templates_dir / "dashboard.html", "w") as f:
    f.write(dashboard_html)

# Write the project detail HTML template
with open(templates_dir / "project_detail.html", "w") as f:
    f.write(project_detail_html)

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