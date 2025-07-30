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
    return templates.TemplateResponse("pages/dashboard.html", {"request": request})

@app.get("/project/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: str):
    """Project detail page"""
    return templates.TemplateResponse("pages/project_detail.html", {"request": request, "project_id": project_id})

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