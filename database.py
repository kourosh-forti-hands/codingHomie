"""
Elite Database Layer - Persistent Storage for the Elite Crew System
Advanced database management with SQLAlchemy and async support
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json
import logging
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid

logger = logging.getLogger(__name__)

Base = declarative_base()

class ProjectStatus(Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class AgentStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"

# Database Models

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default=ProjectStatus.PLANNING.value)
    complexity = Column(String)
    estimated_hours = Column(Float)
    actual_hours = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    project_metadata = Column(JSON, default=dict)
    
    # Relationships
    workflow_stages = relationship("WorkflowStage", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="project", cascade="all, delete-orphan")
    metrics = relationship("PerformanceMetric", back_populates="project", cascade="all, delete-orphan")

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    expertise = Column(JSON, default=list)
    status = Column(String, default=AgentStatus.OFFLINE.value)
    current_task_id = Column(String, ForeignKey("tasks.id"))
    performance_score = Column(Float, default=0.0)
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    online_since = Column(DateTime)
    last_active = Column(DateTime, default=datetime.utcnow)
    agent_metadata = Column(JSON, default=dict)
    
    # Relationships
    tasks = relationship("Task", back_populates="agent", foreign_keys="Task.agent_id")
    current_task = relationship("Task", foreign_keys=[current_task_id])
    sent_messages = relationship("Message", back_populates="sender_agent", foreign_keys="Message.sender_id")

class WorkflowStage(Base):
    __tablename__ = "workflow_stages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    stage_name = Column(String, nullable=False)
    status = Column(String, default=TaskStatus.PENDING.value)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    quality_gates_required = Column(JSON, default=list)
    quality_gates_completed = Column(JSON, default=list)
    blockers = Column(JSON, default=list)
    metrics = Column(JSON, default=dict)
    
    # Relationships
    project = relationship("Project", back_populates="workflow_stages")
    tasks = relationship("Task", back_populates="workflow_stage", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    workflow_stage_id = Column(String, ForeignKey("workflow_stages.id"))
    agent_id = Column(String, ForeignKey("agents.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default=TaskStatus.PENDING.value)
    priority = Column(Integer, default=2)  # 1=low, 2=medium, 3=high, 4=critical
    estimated_hours = Column(Float)
    actual_hours = Column(Float, default=0.0)
    dependencies = Column(JSON, default=list)
    quality_gates_passed = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    task_metadata = Column(JSON, default=dict)
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    workflow_stage = relationship("WorkflowStage", back_populates="tasks")
    agent = relationship("Agent", back_populates="tasks", foreign_keys=[agent_id])

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    sender_id = Column(String, ForeignKey("agents.id"), nullable=False)
    recipients = Column(JSON, default=list)
    message_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(Integer, default=2)
    requires_response = Column(Boolean, default=False)
    response_deadline = Column(DateTime)
    is_responded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    message_metadata = Column(JSON, default=dict)
    
    # Relationships
    project = relationship("Project", back_populates="messages")
    sender_agent = relationship("Agent", back_populates="sent_messages", foreign_keys=[sender_id])

class QualityGate(Base):
    __tablename__ = "quality_gates"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    criteria = Column(JSON, default=list)
    passed = Column(Boolean, default=False)
    validation_timestamp = Column(DateTime)
    validation_notes = Column(Text)
    project_id = Column(String, ForeignKey("projects.id"))
    gate_metadata = Column(JSON, default=dict)

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    metric_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String)
    threshold = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metric_metadata = Column(JSON, default=dict)
    
    # Relationships
    project = relationship("Project", back_populates="metrics")

class EliteDatabase:
    """Advanced database manager for the Elite Crew System"""
    
    def __init__(self, database_url: str = "sqlite+aiosqlite:///elite_crew.db"):
        self.database_url = database_url
        self.async_engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(self.async_engine, class_=AsyncSession)
        
    async def initialize(self):
        """Initialize database tables"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("🗄️ Elite database initialized successfully")
    
    @asynccontextmanager
    async def get_session(self):
        """Get async database session with proper cleanup"""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    # Project Management
    async def create_project(self, name: str, description: str, complexity: str = "medium", 
                           estimated_hours: float = 0) -> Project:
        """Create a new project"""
        async with self.get_session() as session:
            project = Project(
                name=name,
                description=description,
                complexity=complexity,
                estimated_hours=estimated_hours
            )
            session.add(project)
            await session.flush()
            await session.refresh(project)
            logger.info(f"📋 Project created: {project.name} ({project.id})")
            return project
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        async with self.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(Project).where(Project.id == project_id))
            return result.scalar_one_or_none()
    
    async def update_project_status(self, project_id: str, status: ProjectStatus, 
                                  actual_hours: float = None):
        """Update project status"""
        async with self.get_session() as session:
            from sqlalchemy import select, update
            
            update_data = {"status": status.value}
            
            if status == ProjectStatus.IN_PROGRESS:
                update_data["started_at"] = datetime.utcnow()
            elif status == ProjectStatus.COMPLETED:
                update_data["completed_at"] = datetime.utcnow()
            
            if actual_hours is not None:
                update_data["actual_hours"] = actual_hours
            
            await session.execute(
                update(Project).where(Project.id == project_id).values(**update_data)
            )
            logger.info(f"📊 Project {project_id} status updated to {status.value}")
    
    # Agent Management
    async def register_agent(self, agent_id: str, name: str, role: str, 
                           expertise: List[str]) -> Agent:
        """Register or update an agent"""
        async with self.get_session() as session:
            from sqlalchemy import select
            
            # Check if agent exists
            result = await session.execute(select(Agent).where(Agent.id == agent_id))
            agent = result.scalar_one_or_none()
            
            if agent:
                # Update existing agent
                agent.name = name
                agent.role = role
                agent.expertise = expertise
                agent.status = AgentStatus.ONLINE.value
                agent.online_since = datetime.utcnow()
                agent.last_active = datetime.utcnow()
            else:
                # Create new agent
                agent = Agent(
                    id=agent_id,
                    name=name,
                    role=role,
                    expertise=expertise,
                    status=AgentStatus.ONLINE.value,
                    online_since=datetime.utcnow()
                )
                session.add(agent)
            
            await session.flush()
            await session.refresh(agent)
            logger.info(f"🤖 Agent registered: {agent.name} ({agent.id})")
            return agent
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus, 
                                current_task_id: str = None):
        """Update agent status"""
        async with self.get_session() as session:
            from sqlalchemy import update
            
            update_data = {
                "status": status.value,
                "last_active": datetime.utcnow()
            }
            
            if current_task_id:
                update_data["current_task_id"] = current_task_id
            
            await session.execute(
                update(Agent).where(Agent.id == agent_id).values(**update_data)
            )
            logger.info(f"🔄 Agent {agent_id} status updated to {status.value}")
    
    async def get_online_agents(self) -> List[Agent]:
        """Get all online agents"""
        async with self.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Agent).where(Agent.status == AgentStatus.ONLINE.value)
            )
            return result.scalars().all()
    
    # Task Management
    async def create_task(self, project_id: str, title: str, description: str,
                         agent_id: str = None, workflow_stage_id: str = None,
                         priority: int = 2, estimated_hours: float = 0,
                         dependencies: List[str] = None) -> Task:
        """Create a new task"""
        async with self.get_session() as session:
            task = Task(
                project_id=project_id,
                workflow_stage_id=workflow_stage_id,
                agent_id=agent_id,
                title=title,
                description=description,
                priority=priority,
                estimated_hours=estimated_hours,
                dependencies=dependencies or []
            )
            session.add(task)
            await session.flush()
            await session.refresh(task)
            logger.info(f"📝 Task created: {task.title} ({task.id})")
            return task
    
    async def update_task_status(self, task_id: str, status: TaskStatus, 
                               error_message: str = None):
        """Update task status"""
        async with self.get_session() as session:
            from sqlalchemy import update
            
            update_data = {"status": status.value}
            
            if status == TaskStatus.IN_PROGRESS:
                update_data["started_at"] = datetime.utcnow()
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                update_data["completed_at"] = datetime.utcnow()
            
            if error_message and status == TaskStatus.FAILED:
                from sqlalchemy import select
                result = await session.execute(select(Task).where(Task.id == task_id))
                task = result.scalar_one_or_none()
                if task:
                    update_data["error_count"] = task.error_count + 1
                    update_data["last_error"] = error_message
            
            await session.execute(
                update(Task).where(Task.id == task_id).values(**update_data)
            )
            logger.info(f"📊 Task {task_id} status updated to {status.value}")
    
    # Message Management
    async def store_message(self, project_id: str, sender_id: str, recipients: List[str],
                          message_type: str, content: str, priority: int = 2,
                          requires_response: bool = False, 
                          response_deadline: datetime = None) -> Message:
        """Store a message"""
        async with self.get_session() as session:
            message = Message(
                project_id=project_id,
                sender_id=sender_id,
                recipients=recipients,
                message_type=message_type,
                content=content,
                priority=priority,
                requires_response=requires_response,
                response_deadline=response_deadline
            )
            session.add(message)
            await session.flush()
            await session.refresh(message)
            return message
    
    # Performance Metrics
    async def record_metric(self, project_id: str, metric_name: str, value: float,
                          unit: str = "", threshold: float = None) -> PerformanceMetric:
        """Record a performance metric"""
        async with self.get_session() as session:
            metric = PerformanceMetric(
                project_id=project_id,
                metric_name=metric_name,
                value=value,
                unit=unit,
                threshold=threshold
            )
            session.add(metric)
            await session.flush()
            await session.refresh(metric)
            return metric
    
    # Analytics and Reporting
    async def get_project_analytics(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive project analytics"""
        async with self.get_session() as session:
            from sqlalchemy import select, func
            
            # Get project info
            project_result = await session.execute(select(Project).where(Project.id == project_id))
            project = project_result.scalar_one_or_none()
            
            if not project:
                return {}
            
            # Task statistics
            task_stats = await session.execute(
                select(
                    func.count(Task.id).label("total_tasks"),
                    func.sum(func.case((Task.status == TaskStatus.COMPLETED.value, 1), else_=0)).label("completed"),
                    func.sum(func.case((Task.status == TaskStatus.FAILED.value, 1), else_=0)).label("failed"),
                    func.sum(Task.estimated_hours).label("estimated_hours"),
                    func.sum(Task.actual_hours).label("actual_hours")
                ).where(Task.project_id == project_id)
            )
            task_data = task_stats.first()
            
            # Agent performance
            agent_stats = await session.execute(
                select(
                    Agent.id,
                    Agent.name,
                    Agent.role,
                    func.count(Task.id).label("assigned_tasks"),
                    func.sum(func.case((Task.status == TaskStatus.COMPLETED.value, 1), else_=0)).label("completed_tasks")
                ).join(Task, Agent.id == Task.agent_id)\
                 .where(Task.project_id == project_id)\
                 .group_by(Agent.id, Agent.name, Agent.role)
            )
            
            return {
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "status": project.status,
                    "created_at": project.created_at.isoformat() if project.created_at else None,
                    "estimated_hours": project.estimated_hours,
                    "actual_hours": project.actual_hours
                },
                "tasks": {
                    "total": task_data.total_tasks or 0,
                    "completed": task_data.completed or 0,
                    "failed": task_data.failed or 0,
                    "completion_rate": (task_data.completed / task_data.total_tasks * 100) if task_data.total_tasks else 0,
                    "estimated_hours": task_data.estimated_hours or 0,
                    "actual_hours": task_data.actual_hours or 0
                },
                "agents": [
                    {
                        "id": row.id,
                        "name": row.name,
                        "role": row.role,
                        "assigned_tasks": row.assigned_tasks,
                        "completed_tasks": row.completed_tasks,
                        "completion_rate": (row.completed_tasks / row.assigned_tasks * 100) if row.assigned_tasks else 0
                    }
                    for row in agent_stats
                ]
            }
    
    async def cleanup_old_data(self, days_old: int = 30):
        """Clean up old project data"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        async with self.get_session() as session:
            from sqlalchemy import delete
            
            # Delete old projects and related data (cascade will handle relationships)
            await session.execute(
                delete(Project).where(
                    Project.completed_at < cutoff_date,
                    Project.status.in_([ProjectStatus.COMPLETED.value, ProjectStatus.FAILED.value])
                )
            )
            
            logger.info(f"🧹 Cleaned up project data older than {days_old} days")

# Global database instance
elite_db = EliteDatabase()

async def init_database():
    """Initialize the elite database"""
    await elite_db.initialize()
    logger.info("🔥 Elite database system is ready!")

def main():
    """Demo the elite database system"""
    async def demo():
        print("🔥 ELITE DATABASE SYSTEM - PERSISTENT STORAGE IS FIRE! 🔥")
        print("=" * 60)
        
        # Initialize database
        await init_database()
        
        # Create demo project
        project = await elite_db.create_project(
            name="AI Task Management Demo",
            description="Demo project for elite crew system",
            complexity="high",
            estimated_hours=100.0
        )
        
        # Register agents
        agents = [
            ("alpha", "Agent Alpha", "Frontend Specialist", ["React", "Vue", "UI/UX"]),
            ("beta", "Agent Beta", "Backend Developer", ["Node.js", "Python", "APIs"]),
            ("gamma", "Agent Gamma", "Quality Assurance", ["Testing", "QA", "Debugging"])
        ]
        
        for agent_id, name, role, expertise in agents:
            await elite_db.register_agent(agent_id, name, role, expertise)
        
        # Create demo tasks
        tasks = [
            ("Frontend Implementation", "Build React components", "alpha", 3, 20.0),
            ("API Development", "Create REST endpoints", "beta", 3, 25.0),
            ("Test Suite Creation", "Write comprehensive tests", "gamma", 2, 15.0)
        ]
        
        for title, desc, agent_id, priority, hours in tasks:
            await elite_db.create_task(
                project_id=project.id,
                title=title,
                description=desc,
                agent_id=agent_id,
                priority=priority,
                estimated_hours=hours
            )
        
        # Record some metrics
        metrics = [
            ("api_response_time", 1.2, "seconds", 2.0),
            ("memory_usage", 75.5, "MB", 100.0),
            ("cpu_utilization", 45.2, "percent", 80.0)
        ]
        
        for name, value, unit, threshold in metrics:
            await elite_db.record_metric(project.id, name, value, unit, threshold)
        
        # Get analytics
        analytics = await elite_db.get_project_analytics(project.id)
        
        print("\n📊 PROJECT ANALYTICS:")
        print(f"Project: {analytics['project']['name']}")
        print(f"Tasks: {analytics['tasks']['total']} total, {analytics['tasks']['completed']} completed")
        print(f"Completion Rate: {analytics['tasks']['completion_rate']:.1f}%")
        print(f"Agents: {len(analytics['agents'])} registered")
        
        for agent in analytics['agents']:
            print(f"  - {agent['name']}: {agent['completed_tasks']}/{agent['assigned_tasks']} tasks")
        
        print("\n🎯 Elite database system is absolutely fire! 🔥")
    
    asyncio.run(demo())

if __name__ == "__main__":
    main()