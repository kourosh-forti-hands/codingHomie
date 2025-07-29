"""
Configuration for the Elite Multi-Agent Collaborative Coding System
"""

import os
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class AgentConfig:
    """Configuration for individual agents"""
    name: str
    role: str
    expertise: List[str]
    tools: List[str]
    max_iterations: int = 5
    temperature: float = 0.7

@dataclass
class WorkflowConfig:
    """Configuration for workflow stages"""
    stage_name: str
    dependencies: List[str]
    quality_gates: List[str]
    timeout_minutes: int = 30

class EliteCrewConfig:
    """Central configuration for the elite crew system"""
    
    # Agent configurations
    AGENTS = {
        "alpha": AgentConfig(
            name="Agent Alpha",
            role="Frontend Specialist", 
            expertise=["React", "Vue", "Angular", "HTML5", "CSS3", "JavaScript", "TypeScript", "UI/UX"],
            tools=["project_tracker", "code_review", "ui_validator", "accessibility_checker"]
        ),
        "beta": AgentConfig(
            name="Agent Beta",
            role="Backend Developer",
            expertise=["Node.js", "Python", "Java", "SQL", "NoSQL", "APIs", "Microservices", "Security"],
            tools=["project_tracker", "code_review", "api_tester", "db_optimizer"]
        ),
        "gamma": AgentConfig(
            name="Agent Gamma", 
            role="Quality Assurance Engineer",
            expertise=["Jest", "Pytest", "Selenium", "Performance Testing", "Security Testing", "Debugging"],
            tools=["project_tracker", "code_review", "test_runner", "bug_tracker", "performance_analyzer"]
        ),
        "delta": AgentConfig(
            name="Agent Delta",
            role="AI/ML Specialist", 
            expertise=["TensorFlow", "PyTorch", "scikit-learn", "Data Analysis", "MLOps", "NLP"],
            tools=["project_tracker", "code_review", "model_trainer", "data_processor", "ml_validator"]
        ),
        "epsilon": AgentConfig(
            name="Agent Epsilon",
            role="DevOps Engineer",
            expertise=["Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD", "Monitoring", "IaC"],
            tools=["project_tracker", "code_review", "deployment_manager", "infrastructure_monitor"]
        )
    }
    
    # Workflow stage configurations
    WORKFLOW_STAGES = {
        "initialization": WorkflowConfig(
            stage_name="Project Initialization",
            dependencies=[],
            quality_gates=["requirements_validated", "scope_defined", "timeline_approved"],
            timeout_minutes=15
        ),
        "task_distribution": WorkflowConfig(
            stage_name="Task Distribution", 
            dependencies=["initialization"],
            quality_gates=["tasks_assigned", "dependencies_mapped", "resources_allocated"],
            timeout_minutes=10
        ),
        "development": WorkflowConfig(
            stage_name="Collaborative Development",
            dependencies=["task_distribution"],
            quality_gates=["code_review_passed", "unit_tests_passed", "integration_ready"],
            timeout_minutes=120
        ),
        "quality_assurance": WorkflowConfig(
            stage_name="Quality Assurance",
            dependencies=["development"], 
            quality_gates=["all_tests_passed", "performance_validated", "security_cleared"],
            timeout_minutes=60
        ),
        "integration": WorkflowConfig(
            stage_name="Integration and Deployment",
            dependencies=["quality_assurance"],
            quality_gates=["integration_tests_passed", "deployment_successful", "monitoring_active"],
            timeout_minutes=45
        ),
        "retrospective": WorkflowConfig(
            stage_name="Retrospective and Improvement", 
            dependencies=["integration"],
            quality_gates=["metrics_collected", "lessons_documented", "improvements_identified"],
            timeout_minutes=20
        )
    }
    
    # Communication protocol settings
    COMMUNICATION_PROTOCOL = {
        "standup_frequency": "daily",
        "escalation_threshold": "immediate",
        "documentation_required": True,
        "knowledge_sharing": "weekly",
        "review_gates": ["peer_review", "lead_review", "final_approval"]
    }
    
    # Quality standards
    QUALITY_STANDARDS = {
        "code_coverage_minimum": 80,
        "performance_threshold": "95th_percentile_2s",
        "security_scan_required": True,
        "documentation_coverage": 90,
        "scalability_testing": True
    }
    
    # Success metrics
    SUCCESS_METRICS = {
        "functional_requirements_met": 100,
        "quality_gates_passed": 100,
        "timeline_adherence": 95,
        "team_satisfaction": 85,
        "maintainability_score": 90
    }
    
    @classmethod
    def get_agent_config(cls, agent_name: str) -> AgentConfig:
        """Get configuration for a specific agent"""
        return cls.AGENTS.get(agent_name)
    
    @classmethod
    def get_workflow_config(cls, stage_name: str) -> WorkflowConfig:
        """Get configuration for a specific workflow stage"""
        return cls.WORKFLOW_STAGES.get(stage_name)
    
    @classmethod
    def validate_quality_gates(cls, stage: str, completed_gates: List[str]) -> bool:
        """Validate that all quality gates for a stage are completed"""
        stage_config = cls.get_workflow_config(stage)
        if not stage_config:
            return False
        return all(gate in completed_gates for gate in stage_config.quality_gates)

# Environment variables for API keys and configurations
def load_environment():
    """Load environment variables for the system"""
    from dotenv import load_dotenv
    load_dotenv()
    
    return {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"), 
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN"),
        "PROJECT_ROOT": os.getenv("PROJECT_ROOT", os.getcwd()),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "MAX_CONCURRENT_AGENTS": int(os.getenv("MAX_CONCURRENT_AGENTS", "3")),
        "ENABLE_METRICS": os.getenv("ENABLE_METRICS", "true").lower() == "true"
    }