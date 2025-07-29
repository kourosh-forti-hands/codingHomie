"""
Advanced Workflow Management System for Elite Multi-Agent Crew
Handles the 6-phase workflow execution with quality gates and monitoring
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, asdict
from config import EliteCrewConfig, WorkflowConfig

logger = logging.getLogger(__name__)

class StageStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class TaskItem:
    """Individual task within a workflow stage"""
    id: str
    title: str
    description: str
    agent_assigned: str
    priority: Priority
    estimated_hours: float
    dependencies: List[str]
    status: StageStatus = StageStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    quality_gates_passed: List[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.quality_gates_passed is None:
            self.quality_gates_passed = []

@dataclass 
class StageExecution:
    """Execution details for a workflow stage"""
    stage_name: str
    status: StageStatus
    tasks: List[TaskItem]
    quality_gates_required: List[str]
    quality_gates_completed: List[str]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    blockers: List[str] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.blockers is None:
            self.blockers = []
        if self.metrics is None:
            self.metrics = {}

class WorkflowOrchestrator:
    """Advanced workflow orchestration with real-time monitoring"""
    
    def __init__(self):
        self.config = EliteCrewConfig()
        self.active_stages: Dict[str, StageExecution] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {}
        self.quality_dashboard: Dict[str, Any] = {}
        
    def initialize_workflow(self, project_id: str, project_requirements: str) -> Dict[str, StageExecution]:
        """Initialize all workflow stages with tasks and dependencies"""
        logger.info(f"🚀 Initializing elite workflow for project: {project_id}")
        
        stages = {}
        
        # Phase 1: Project Initialization
        init_tasks = [
            TaskItem(
                id=f"{project_id}_init_001",
                title="Requirements Analysis",
                description="Analyze and validate project requirements",
                agent_assigned="coordinator",
                priority=Priority.CRITICAL,
                estimated_hours=2.0,
                dependencies=[]
            ),
            TaskItem(
                id=f"{project_id}_init_002", 
                title="Technical Architecture Design",
                description="Design system architecture and technology stack",
                agent_assigned="coordinator", 
                priority=Priority.HIGH,
                estimated_hours=3.0,
                dependencies=[f"{project_id}_init_001"]
            ),
            TaskItem(
                id=f"{project_id}_init_003",
                title="Resource Planning",
                description="Plan team resources and timeline",
                agent_assigned="coordinator",
                priority=Priority.HIGH, 
                estimated_hours=1.5,
                dependencies=[f"{project_id}_init_002"]
            )
        ]
        
        stages["initialization"] = StageExecution(
            stage_name="initialization",
            status=StageStatus.PENDING,
            tasks=init_tasks,
            quality_gates_required=self.config.WORKFLOW_STAGES["initialization"].quality_gates,
            quality_gates_completed=[]
        )
        
        # Phase 2: Task Distribution
        distribution_tasks = [
            TaskItem(
                id=f"{project_id}_dist_001",
                title="Frontend Task Assignment",
                description="Assign UI/UX development tasks to Agent Alpha",
                agent_assigned="coordinator",
                priority=Priority.HIGH,
                estimated_hours=1.0,
                dependencies=[f"{project_id}_init_003"]
            ),
            TaskItem(
                id=f"{project_id}_dist_002",
                title="Backend Task Assignment", 
                description="Assign API and database tasks to Agent Beta",
                agent_assigned="coordinator",
                priority=Priority.HIGH,
                estimated_hours=1.0,
                dependencies=[f"{project_id}_init_003"]
            ),
            TaskItem(
                id=f"{project_id}_dist_003",
                title="AI/ML Task Assignment",
                description="Assign intelligent features to Agent Delta",
                agent_assigned="coordinator", 
                priority=Priority.MEDIUM,
                estimated_hours=1.0,
                dependencies=[f"{project_id}_init_003"]
            )
        ]
        
        stages["task_distribution"] = StageExecution(
            stage_name="task_distribution",
            status=StageStatus.PENDING,
            tasks=distribution_tasks,
            quality_gates_required=self.config.WORKFLOW_STAGES["task_distribution"].quality_gates,
            quality_gates_completed=[]
        )
        
        # Phase 3: Development
        dev_tasks = [
            TaskItem(
                id=f"{project_id}_dev_001",
                title="Frontend Implementation",
                description="Build responsive UI components and user interface",
                agent_assigned="alpha",
                priority=Priority.HIGH,
                estimated_hours=20.0,
                dependencies=[f"{project_id}_dist_001"]
            ),
            TaskItem(
                id=f"{project_id}_dev_002",
                title="Backend API Development",
                description="Implement REST APIs and database integration",
                agent_assigned="beta",
                priority=Priority.HIGH, 
                estimated_hours=25.0,
                dependencies=[f"{project_id}_dist_002"]
            ),
            TaskItem(
                id=f"{project_id}_dev_003",
                title="AI Feature Integration",
                description="Implement machine learning capabilities",
                agent_assigned="delta",
                priority=Priority.MEDIUM,
                estimated_hours=15.0,
                dependencies=[f"{project_id}_dist_003", f"{project_id}_dev_002"]
            )
        ]
        
        stages["development"] = StageExecution(
            stage_name="development", 
            status=StageStatus.PENDING,
            tasks=dev_tasks,
            quality_gates_required=self.config.WORKFLOW_STAGES["development"].quality_gates,
            quality_gates_completed=[]
        )
        
        # Phase 4: Quality Assurance
        qa_tasks = [
            TaskItem(
                id=f"{project_id}_qa_001",
                title="Unit Testing Suite",
                description="Create comprehensive unit tests for all components",
                agent_assigned="gamma",
                priority=Priority.HIGH,
                estimated_hours=12.0,
                dependencies=[f"{project_id}_dev_001", f"{project_id}_dev_002"]
            ),
            TaskItem(
                id=f"{project_id}_qa_002",
                title="Integration Testing",
                description="Test component integration and API endpoints",
                agent_assigned="gamma",
                priority=Priority.HIGH,
                estimated_hours=8.0,
                dependencies=[f"{project_id}_qa_001"]
            ),
            TaskItem(
                id=f"{project_id}_qa_003",
                title="Performance & Security Testing",
                description="Conduct performance and security assessments",
                agent_assigned="gamma", 
                priority=Priority.CRITICAL,
                estimated_hours=10.0,
                dependencies=[f"{project_id}_qa_002"]
            )
        ]
        
        stages["quality_assurance"] = StageExecution(
            stage_name="quality_assurance",
            status=StageStatus.PENDING,
            tasks=qa_tasks,
            quality_gates_required=self.config.WORKFLOW_STAGES["quality_assurance"].quality_gates,
            quality_gates_completed=[]
        )
        
        # Phase 5: Integration & Deployment
        integration_tasks = [
            TaskItem(
                id=f"{project_id}_int_001",
                title="CI/CD Pipeline Setup",
                description="Configure automated build and deployment pipeline",
                agent_assigned="epsilon",
                priority=Priority.HIGH,
                estimated_hours=6.0,
                dependencies=[f"{project_id}_qa_003"]
            ),
            TaskItem(
                id=f"{project_id}_int_002",
                title="Production Deployment",
                description="Deploy to production environment with monitoring",
                agent_assigned="epsilon",
                priority=Priority.CRITICAL,
                estimated_hours=4.0,
                dependencies=[f"{project_id}_int_001"]
            ),
            TaskItem(
                id=f"{project_id}_int_003",
                title="Monitoring & Alerting",
                description="Set up comprehensive monitoring and alerting systems",
                agent_assigned="epsilon",
                priority=Priority.HIGH,
                estimated_hours=3.0,
                dependencies=[f"{project_id}_int_002"]
            )
        ]
        
        stages["integration"] = StageExecution(
            stage_name="integration",
            status=StageStatus.PENDING,
            tasks=integration_tasks,
            quality_gates_required=self.config.WORKFLOW_STAGES["integration"].quality_gates,
            quality_gates_completed=[]
        )
        
        # Phase 6: Retrospective
        retro_tasks = [
            TaskItem(
                id=f"{project_id}_retro_001",
                title="Performance Metrics Collection",
                description="Gather and analyze project performance data",
                agent_assigned="coordinator",
                priority=Priority.MEDIUM,
                estimated_hours=2.0,
                dependencies=[f"{project_id}_int_003"]
            ),
            TaskItem(
                id=f"{project_id}_retro_002",
                title="Lessons Learned Documentation",
                description="Document insights and improvement opportunities",
                agent_assigned="coordinator",
                priority=Priority.MEDIUM,
                estimated_hours=3.0,
                dependencies=[f"{project_id}_retro_001"]
            ),
            TaskItem(
                id=f"{project_id}_retro_003",
                title="Process Improvement Planning",
                description="Plan improvements for future projects",
                agent_assigned="coordinator",
                priority=Priority.LOW,
                estimated_hours=2.0,
                dependencies=[f"{project_id}_retro_002"]
            )
        ]
        
        stages["retrospective"] = StageExecution(
            stage_name="retrospective",
            status=StageStatus.PENDING,
            tasks=retro_tasks,
            quality_gates_required=self.config.WORKFLOW_STAGES["retrospective"].quality_gates,
            quality_gates_completed=[]
        )
        
        self.active_stages = stages
        logger.info(f"✅ Workflow initialized with {len(stages)} stages and {sum(len(s.tasks) for s in stages.values())} tasks")
        
        return stages
    
    def execute_stage(self, stage_name: str) -> Tuple[bool, List[str]]:
        """Execute a specific workflow stage with quality gate validation"""
        if stage_name not in self.active_stages:
            return False, [f"Stage '{stage_name}' not found"]
            
        stage = self.active_stages[stage_name]
        logger.info(f"🎯 Executing stage: {stage_name}")
        
        # Check dependencies
        if not self._validate_stage_dependencies(stage_name):
            return False, ["Stage dependencies not met"]
            
        stage.status = StageStatus.IN_PROGRESS
        stage.started_at = datetime.now()
        
        errors = []
        completed_tasks = 0
        
        # Execute tasks in dependency order
        for task in self._get_tasks_in_execution_order(stage.tasks):
            try:
                success = self._execute_task(task)
                if success:
                    completed_tasks += 1
                    logger.info(f"✅ Task completed: {task.title}")
                else:
                    errors.append(f"Task failed: {task.title}")
                    logger.error(f"❌ Task failed: {task.title}")
            except Exception as e:
                errors.append(f"Task error: {task.title} - {str(e)}")
                logger.error(f"💥 Task error: {task.title} - {str(e)}")
        
        # Validate quality gates
        quality_passed, quality_errors = self._validate_quality_gates(stage)
        errors.extend(quality_errors)
        
        if not errors and quality_passed:
            stage.status = StageStatus.COMPLETED
            stage.completed_at = datetime.now()
            stage.metrics.update({
                "tasks_completed": completed_tasks,
                "execution_time": (stage.completed_at - stage.started_at).total_seconds(),
                "success_rate": 100.0
            })
            logger.info(f"🎉 Stage completed successfully: {stage_name}")
            return True, []
        else:
            stage.status = StageStatus.FAILED
            stage.metrics.update({
                "tasks_completed": completed_tasks,
                "execution_time": (datetime.now() - stage.started_at).total_seconds(),
                "success_rate": (completed_tasks / len(stage.tasks)) * 100 if stage.tasks else 0,
                "errors": errors
            })
            logger.error(f"💀 Stage failed: {stage_name} - {len(errors)} errors")
            return False, errors
    
    def _validate_stage_dependencies(self, stage_name: str) -> bool:
        """Check if all dependencies for a stage are met"""
        stage_config = self.config.WORKFLOW_STAGES.get(stage_name)
        if not stage_config:
            return False
            
        for dep in stage_config.dependencies:
            if dep not in self.active_stages:
                return False
            if self.active_stages[dep].status != StageStatus.COMPLETED:
                return False
                
        return True
    
    def _get_tasks_in_execution_order(self, tasks: List[TaskItem]) -> List[TaskItem]:
        """Sort tasks by dependencies and priority"""
        # Simple dependency sorting (in production, use proper topological sort)
        sorted_tasks = sorted(tasks, key=lambda t: (len(t.dependencies), -t.priority.value))
        return sorted_tasks
    
    def _execute_task(self, task: TaskItem) -> bool:
        """Execute an individual task (simulate execution)"""
        task.status = StageStatus.IN_PROGRESS
        task.started_at = datetime.now()
        
        # Simulate task execution time
        import time
        time.sleep(0.1)  # Simulate work
        
        # Simulate success/failure (90% success rate)
        import random
        success = random.random() > 0.1
        
        if success:
            task.status = StageStatus.COMPLETED
            task.completed_at = datetime.now()
            # Mark quality gates as passed (simplified)
            task.quality_gates_passed = ["code_review", "testing"]
        else:
            task.status = StageStatus.FAILED
            
        return success
    
    def _validate_quality_gates(self, stage: StageExecution) -> Tuple[bool, List[str]]:
        """Validate all quality gates for a stage"""
        errors = []
        
        for gate in stage.quality_gates_required:
            if gate not in stage.quality_gates_completed:
                # Simulate quality gate validation
                import random
                if random.random() > 0.15:  # 85% pass rate
                    stage.quality_gates_completed.append(gate)
                else:
                    errors.append(f"Quality gate failed: {gate}")
        
        return len(errors) == 0, errors
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get comprehensive workflow status and metrics"""
        total_tasks = sum(len(stage.tasks) for stage in self.active_stages.values())
        completed_tasks = sum(
            len([t for t in stage.tasks if t.status == StageStatus.COMPLETED])
            for stage in self.active_stages.values()
        )
        
        stages_completed = len([s for s in self.active_stages.values() if s.status == StageStatus.COMPLETED])
        total_stages = len(self.active_stages)
        
        return {
            "workflow_progress": (stages_completed / total_stages) * 100 if total_stages else 0,
            "task_completion": (completed_tasks / total_tasks) * 100 if total_tasks else 0,
            "stages_status": {
                name: {
                    "status": stage.status.value,
                    "tasks_completed": len([t for t in stage.tasks if t.status == StageStatus.COMPLETED]),
                    "total_tasks": len(stage.tasks),
                    "quality_gates_passed": len(stage.quality_gates_completed),
                    "quality_gates_required": len(stage.quality_gates_required)
                }
                for name, stage in self.active_stages.items()
            },
            "performance_metrics": self.performance_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_workflow_report(self) -> str:
        """Generate a comprehensive workflow execution report"""
        status = self.get_workflow_status()
        
        report = f"""
🔥 ELITE CREW WORKFLOW EXECUTION REPORT 🔥
{'=' * 60}

OVERALL PROGRESS:
- Workflow Progress: {status['workflow_progress']:.1f}%
- Task Completion: {status['task_completion']:.1f}%
- Generated: {status['timestamp']}

STAGE BREAKDOWN:
"""
        
        for stage_name, stage_data in status['stages_status'].items():
            report += f"""
📋 {stage_name.upper()}:
   Status: {stage_data['status']}
   Tasks: {stage_data['tasks_completed']}/{stage_data['total_tasks']}
   Quality Gates: {stage_data['quality_gates_passed']}/{stage_data['quality_gates_required']}
"""
        
        report += f"""
{'=' * 60}
🎯 The elite crew is delivering absolute fire! 🔥
"""
        
        return report

def main():
    """Demo the workflow orchestrator"""
    orchestrator = WorkflowOrchestrator()
    
    # Initialize workflow for demo project
    project_id = "elite_demo_001"
    project_requirements = "AI-powered task management application"
    
    print("🚀 ELITE WORKFLOW ORCHESTRATOR - STREETS ARE HOT! 🚀")
    print("=" * 60)
    
    # Initialize workflow
    stages = orchestrator.initialize_workflow(project_id, project_requirements)
    print(f"📋 Initialized workflow with {len(stages)} stages")
    
    # Execute stages in order
    stage_order = ["initialization", "task_distribution", "development", "quality_assurance", "integration", "retrospective"]
    
    for stage_name in stage_order:
        print(f"\n🎯 Executing stage: {stage_name}")
        success, errors = orchestrator.execute_stage(stage_name)
        if success:
            print(f"✅ Stage completed: {stage_name}")
        else:
            print(f"❌ Stage failed: {stage_name}")
            for error in errors:
                print(f"   - {error}")
    
    # Generate final report
    print("\n" + orchestrator.generate_workflow_report())

if __name__ == "__main__":
    main()