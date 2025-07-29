"""
🔥 Amazon Bedrock Integration - Multi-Model Elite Crew System
Leverage multiple Bedrock models (Claude, Llama, Titan, etc.) for the elite crew
"""

import boto3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp
from botocore.exceptions import ClientError, BotoCoreError

from langchain_aws import ChatBedrock
from langchain.schema import HumanMessage, SystemMessage
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool

logger = logging.getLogger(__name__)

class BedrockModel(Enum):
    """Available Amazon Bedrock models"""
    # Anthropic Claude models
    CLAUDE_3_5_SONNET = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    CLAUDE_3_HAIKU = "anthropic.claude-3-haiku-20240307-v1:0"
    CLAUDE_3_OPUS = "anthropic.claude-3-opus-20240229-v1:0"
    CLAUDE_INSTANT = "anthropic.claude-instant-v1"
    
    # Meta Llama models
    LLAMA_3_70B = "meta.llama3-70b-instruct-v1:0"
    LLAMA_3_8B = "meta.llama3-8b-instruct-v1:0"
    LLAMA_2_70B = "meta.llama2-70b-chat-v1"
    LLAMA_2_13B = "meta.llama2-13b-chat-v1"
    
    # Amazon Titan models
    TITAN_TEXT_G1_LARGE = "amazon.titan-text-lite-v1"
    TITAN_TEXT_G1_EXPRESS = "amazon.titan-text-express-v1"
    
    # AI21 Jurassic models
    JURASSIC_2_MID = "ai21.j2-mid-v1"
    JURASSIC_2_ULTRA = "ai21.j2-ultra-v1"
    
    # Cohere Command models
    COMMAND_TEXT = "cohere.command-text-v14"
    COMMAND_LIGHT = "cohere.command-light-text-v14"

@dataclass
class ModelConfig:
    """Configuration for a specific Bedrock model"""
    model_id: BedrockModel
    max_tokens: int = 4000
    temperature: float = 0.7
    top_p: float = 0.9
    stop_sequences: List[str] = None
    region: str = "us-east-1"
    use_case: str = "general"  # general, code, analysis, creative
    cost_per_1k_tokens: float = 0.0  # For cost tracking

class BedrockModelManager:
    """Manage multiple Bedrock models for different use cases"""
    
    def __init__(self, aws_region: str = "us-east-1", aws_profile: str = None):
        self.aws_region = aws_region
        self.aws_profile = aws_profile
        
        # Initialize Bedrock client
        session = boto3.Session(profile_name=aws_profile) if aws_profile else boto3.Session()
        self.bedrock_runtime = session.client(
            service_name='bedrock-runtime',
            region_name=aws_region
        )
        self.bedrock_client = session.client(
            service_name='bedrock',
            region_name=aws_region
        )
        
        # Model configurations for different agent types
        self.model_configs = self._setup_model_configurations()
        self.usage_stats = {}
        
    def _setup_model_configurations(self) -> Dict[str, ModelConfig]:
        """Setup optimal model configurations for different agent roles"""
        return {
            # Frontend specialist - needs creativity and UI/UX understanding
            "frontend": ModelConfig(
                model_id=BedrockModel.CLAUDE_3_5_SONNET,
                max_tokens=3000,
                temperature=0.8,
                use_case="creative",
                cost_per_1k_tokens=0.003
            ),
            
            # Backend developer - needs precision and technical accuracy
            "backend": ModelConfig(
                model_id=BedrockModel.CLAUDE_3_5_SONNET,
                max_tokens=4000,
                temperature=0.3,
                use_case="code",
                cost_per_1k_tokens=0.003
            ),
            
            # QA engineer - needs analytical thinking
            "qa": ModelConfig(
                model_id=BedrockModel.CLAUDE_3_HAIKU,  # Fast and efficient for testing
                max_tokens=2000,
                temperature=0.2,
                use_case="analysis",
                cost_per_1k_tokens=0.00025
            ),
            
            # AI/ML specialist - needs advanced reasoning
            "ml": ModelConfig(
                model_id=BedrockModel.CLAUDE_3_OPUS,  # Most capable for complex ML tasks
                max_tokens=4000,
                temperature=0.4,
                use_case="analysis",
                cost_per_1k_tokens=0.015
            ),
            
            # DevOps engineer - needs practical solutions
            "devops": ModelConfig(
                model_id=BedrockModel.LLAMA_3_70B,  # Good for infrastructure tasks
                max_tokens=3000,
                temperature=0.3,
                use_case="code",
                cost_per_1k_tokens=0.0008
            ),
            
            # Coordinator - needs general intelligence
            "coordinator": ModelConfig(
                model_id=BedrockModel.CLAUDE_3_5_SONNET,
                max_tokens=3000,
                temperature=0.5,
                use_case="general",
                cost_per_1k_tokens=0.003
            ),
            
            # High-performance option for time-critical tasks
            "fast": ModelConfig(
                model_id=BedrockModel.CLAUDE_3_HAIKU,
                max_tokens=1500,
                temperature=0.3,
                use_case="general",
                cost_per_1k_tokens=0.00025
            ),
            
            # Cost-effective option for simple tasks
            "economical": ModelConfig(
                model_id=BedrockModel.TITAN_TEXT_G1_EXPRESS,
                max_tokens=2000,
                temperature=0.5,
                use_case="general",
                cost_per_1k_tokens=0.0002
            )
        }
    
    def get_model_for_agent(self, agent_role: str) -> ModelConfig:
        """Get the optimal model configuration for an agent role"""
        role_key = agent_role.lower().replace(" ", "_").replace("-", "_")
        
        # Map common role variations
        role_mapping = {
            "frontend_specialist": "frontend",
            "backend_developer": "backend",
            "quality_assurance": "qa",
            "qa_engineer": "qa",
            "ai_ml_specialist": "ml",
            "ml_engineer": "ml",
            "devops_engineer": "devops",
            "central_coordinator": "coordinator"
        }
        
        mapped_role = role_mapping.get(role_key, role_key)
        return self.model_configs.get(mapped_role, self.model_configs["coordinator"])
    
    def create_langchain_chat_model(self, config: ModelConfig) -> ChatBedrock:
        """Create a LangChain ChatBedrock instance with the specified configuration"""
        model_kwargs = {
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p
        }
        
        if config.stop_sequences:
            model_kwargs["stop_sequences"] = config.stop_sequences
        
        return ChatBedrock(
            model_id=config.model_id.value,
            client=self.bedrock_runtime,
            model_kwargs=model_kwargs,
            region_name=config.region
        )
    
    async def invoke_model_async(self, config: ModelConfig, messages: List[Dict], 
                                system_prompt: str = None) -> Dict[str, Any]:
        """Asynchronously invoke a Bedrock model"""
        try:
            # Format messages based on model family
            if "claude" in config.model_id.value:
                formatted_prompt = self._format_claude_prompt(messages, system_prompt)
                body = {
                    "prompt": formatted_prompt,
                    "max_tokens_to_sample": config.max_tokens,
                    "temperature": config.temperature,
                    "top_p": config.top_p,
                    "stop_sequences": config.stop_sequences or []
                }
            elif "llama" in config.model_id.value:
                formatted_prompt = self._format_llama_prompt(messages, system_prompt)
                body = {
                    "prompt": formatted_prompt,
                    "max_gen_len": config.max_tokens,
                    "temperature": config.temperature,
                    "top_p": config.top_p
                }
            elif "titan" in config.model_id.value:
                body = {
                    "inputText": self._format_titan_prompt(messages, system_prompt),
                    "textGenerationConfig": {
                        "maxTokenCount": config.max_tokens,
                        "temperature": config.temperature,
                        "topP": config.top_p,
                        "stopSequences": config.stop_sequences or []
                    }
                }
            else:
                # Generic format
                body = {
                    "prompt": self._format_generic_prompt(messages, system_prompt),
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                    "top_p": config.top_p
                }
            
            # Invoke the model
            response = self.bedrock_runtime.invoke_model(
                modelId=config.model_id.value,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Track usage
            self._track_usage(config, response_body)
            
            return {
                "success": True,
                "response": self._extract_response_text(response_body, config.model_id),
                "model_id": config.model_id.value,
                "usage": response_body.get("usage", {}),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "config": config.__dict__
                }
            }
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Bedrock model invocation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "model_id": config.model_id.value
            }
    
    def _format_claude_prompt(self, messages: List[Dict], system_prompt: str = None) -> str:
        """Format prompt for Claude models"""
        prompt = ""
        
        if system_prompt:
            prompt += f"\n\nHuman: {system_prompt}\n\nAssistant: I understand.\n\n"
        
        for message in messages:
            if message["role"] == "user":
                prompt += f"Human: {message['content']}\n\n"
            elif message["role"] == "assistant":
                prompt += f"Assistant: {message['content']}\n\n"
        
        prompt += "Assistant:"
        return prompt
    
    def _format_llama_prompt(self, messages: List[Dict], system_prompt: str = None) -> str:
        """Format prompt for Llama models"""
        prompt = ""
        
        if system_prompt:
            prompt += f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n"
        else:
            prompt += "<s>[INST] "
        
        for i, message in enumerate(messages):
            if message["role"] == "user":
                if i == 0 and system_prompt:
                    prompt += f"{message['content']} [/INST]"
                else:
                    prompt += f"<s>[INST] {message['content']} [/INST]"
            elif message["role"] == "assistant":
                prompt += f" {message['content']} </s>"
        
        return prompt
    
    def _format_titan_prompt(self, messages: List[Dict], system_prompt: str = None) -> str:
        """Format prompt for Amazon Titan models"""
        prompt = ""
        
        if system_prompt:
            prompt += f"System: {system_prompt}\n\n"
        
        for message in messages:
            if message["role"] == "user":
                prompt += f"User: {message['content']}\n"
            elif message["role"] == "assistant":
                prompt += f"Assistant: {message['content']}\n"
        
        prompt += "Assistant:"
        return prompt
    
    def _format_generic_prompt(self, messages: List[Dict], system_prompt: str = None) -> str:
        """Generic prompt formatting"""
        prompt = ""
        
        if system_prompt:
            prompt += f"{system_prompt}\n\n"
        
        for message in messages:
            prompt += f"{message['role'].title()}: {message['content']}\n"
        
        return prompt
    
    def _extract_response_text(self, response_body: Dict, model_id: BedrockModel) -> str:
        """Extract response text from model response"""
        if "claude" in model_id.value:
            return response_body.get("completion", "")
        elif "llama" in model_id.value:
            return response_body.get("generation", "")
        elif "titan" in model_id.value:
            results = response_body.get("results", [])
            return results[0].get("outputText", "") if results else ""
        elif "jurassic" in model_id.value:
            completions = response_body.get("completions", [])
            return completions[0].get("data", {}).get("text", "") if completions else ""
        elif "command" in model_id.value:
            generations = response_body.get("generations", [])
            return generations[0].get("text", "") if generations else ""
        else:
            # Try common response fields
            return (response_body.get("completion") or 
                   response_body.get("generation") or 
                   response_body.get("text") or 
                   str(response_body))
    
    def _track_usage(self, config: ModelConfig, response_body: Dict):
        """Track model usage for cost and performance monitoring"""
        model_id = config.model_id.value
        
        if model_id not in self.usage_stats:
            self.usage_stats[model_id] = {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "average_latency": 0.0
            }
        
        stats = self.usage_stats[model_id]
        stats["total_requests"] += 1
        
        # Extract token usage if available
        usage = response_body.get("usage", {})
        tokens_used = (usage.get("input_tokens", 0) + 
                      usage.get("output_tokens", 0) or
                      usage.get("total_tokens", 0))
        
        if tokens_used > 0:
            stats["total_tokens"] += tokens_used
            stats["total_cost"] += (tokens_used / 1000) * config.cost_per_1k_tokens
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics"""
        return {
            "total_models_used": len(self.usage_stats),
            "models": self.usage_stats,
            "total_cost": sum(stats["total_cost"] for stats in self.usage_stats.values()),
            "total_requests": sum(stats["total_requests"] for stats in self.usage_stats.values()),
            "timestamp": datetime.now().isoformat()
        }
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available models in the current region"""
        try:
            response = self.bedrock_client.list_foundation_models()
            return [
                {
                    "model_id": model["modelId"],
                    "model_name": model["modelName"],
                    "provider_name": model["providerName"],
                    "input_modalities": model.get("inputModalities", []),
                    "output_modalities": model.get("outputModalities", []),
                    "supported_customizations": model.get("customizationsSupported", [])
                }
                for model in response.get("modelSummaries", [])
                if "TEXT" in model.get("inputModalities", [])
            ]
        except Exception as e:
            logger.error(f"Error listing Bedrock models: {e}")
            return []

class BedrockAgent(Agent):
    """Enhanced CrewAI Agent with Bedrock model integration"""
    
    def __init__(self, role: str, goal: str, backstory: str, tools: List[BaseTool] = None,
                 bedrock_manager: BedrockModelManager = None, model_preference: str = None, **kwargs):
        
        self.bedrock_manager = bedrock_manager or BedrockModelManager()
        
        # Get optimal model configuration for this agent's role
        if model_preference:
            model_config = self.bedrock_manager.model_configs.get(model_preference)
        else:
            model_config = self.bedrock_manager.get_model_for_agent(role)
        
        if not model_config:
            model_config = self.bedrock_manager.model_configs["coordinator"]
        
        # Create LangChain ChatBedrock instance
        llm = self.bedrock_manager.create_langchain_chat_model(model_config)
        
        # Initialize the agent with Bedrock model
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools or [],
            llm=llm,
            **kwargs
        )
        
        self.model_config = model_config
        
        logger.info(f"🤖 Bedrock Agent '{role}' initialized with model: {model_config.model_id.value}")

class EliteBedrockCrew:
    """Elite Crew System powered by Amazon Bedrock models"""
    
    def __init__(self, aws_region: str = "us-east-1", aws_profile: str = None):
        self.bedrock_manager = BedrockModelManager(aws_region, aws_profile)
        self.agents = {}
        self.crew = None
        
        logger.info(f"🔥 Elite Bedrock Crew initialized in region: {aws_region}")
    
    def create_elite_agents(self, tools_factory=None) -> Dict[str, BedrockAgent]:
        """Create the elite agents with Bedrock models"""
        
        # Import tools if factory provided
        if tools_factory:
            alpha_tools = tools_factory.get_frontend_tools()
            beta_tools = tools_factory.get_backend_tools()
            gamma_tools = tools_factory.get_qa_tools()
            delta_tools = tools_factory.get_ml_tools()
            epsilon_tools = tools_factory.get_devops_tools()
            coordinator_tools = tools_factory.get_coordinator_tools()
        else:
            alpha_tools = beta_tools = gamma_tools = delta_tools = epsilon_tools = coordinator_tools = []
        
        # Agent Alpha - Frontend Specialist (Claude 3.5 Sonnet for creativity)
        self.agents["alpha"] = BedrockAgent(
            role="Frontend Specialist",
            goal="Build responsive, intuitive user interfaces with modern frameworks",
            backstory="""You are Agent Alpha, an elite frontend developer powered by Claude 3.5 Sonnet. 
            You excel at creating beautiful, accessible interfaces with React, Vue, and Angular. 
            Your code is clean, performant, and follows the latest UI/UX best practices.""",
            tools=alpha_tools,
            bedrock_manager=self.bedrock_manager,
            model_preference="frontend",
            verbose=True,
            allow_delegation=True
        )
        
        # Agent Beta - Backend Developer (Claude 3.5 Sonnet for precision)
        self.agents["beta"] = BedrockAgent(
            role="Backend Developer",
            goal="Design scalable server architecture and robust APIs",
            backstory="""You are Agent Beta, a backend engineering master powered by Claude 3.5 Sonnet. 
            You build secure, high-performance server systems with Node.js, Python, and cloud technologies. 
            Your APIs are well-documented and your databases are optimized for scale.""",
            tools=beta_tools,
            bedrock_manager=self.bedrock_manager,
            model_preference="backend",
            verbose=True,
            allow_delegation=True
        )
        
        # Agent Gamma - Quality Assurance (Claude 3 Haiku for speed)
        self.agents["gamma"] = BedrockAgent(
            role="Quality Assurance Engineer",
            goal="Ensure bulletproof code quality through comprehensive testing",
            backstory="""You are Agent Gamma, a QA specialist powered by Claude 3 Haiku for rapid testing. 
            You write comprehensive test suites, hunt down bugs with precision, and ensure every line 
            of code meets the highest quality standards. Your testing strategies are legendary.""",
            tools=gamma_tools,
            bedrock_manager=self.bedrock_manager,
            model_preference="qa",
            verbose=True,
            allow_delegation=True
        )
        
        # Agent Delta - AI/ML Specialist (Claude 3 Opus for complex reasoning)
        self.agents["delta"] = BedrockAgent(
            role="AI/ML Specialist",
            goal="Integrate intelligent features and machine learning capabilities",
            backstory="""You are Agent Delta, an AI/ML wizard powered by Claude 3 Opus for maximum intelligence. 
            You work with advanced algorithms, create smart features, and build ML pipelines that deliver 
            accurate predictions. Your models are optimized and your data processing is flawless.""",
            tools=delta_tools,
            bedrock_manager=self.bedrock_manager,
            model_preference="ml",
            verbose=True,
            allow_delegation=True
        )
        
        # Agent Epsilon - DevOps Engineer (Llama 3 70B for infrastructure)
        self.agents["epsilon"] = BedrockAgent(
            role="DevOps Engineer",  
            goal="Automate deployment and maintain rock-solid infrastructure",
            backstory="""You are Agent Epsilon, a DevOps maestro powered by Llama 3 70B for infrastructure expertise. 
            You orchestrate containers, manage cloud resources, and build CI/CD pipelines that never fail. 
            Your monitoring systems catch issues before users notice.""",
            tools=epsilon_tools,
            bedrock_manager=self.bedrock_manager,
            model_preference="devops",
            verbose=True,
            allow_delegation=True
        )
        
        # Central Coordinator (Claude 3.5 Sonnet for leadership)
        self.agents["coordinator"] = BedrockAgent(
            role="Central Coordinator",
            goal="Orchestrate the elite team to deliver exceptional software solutions",
            backstory="""You are the Central Coordinator, powered by Claude 3.5 Sonnet for strategic thinking. 
            You see the big picture, coordinate complex workflows, and ensure every agent delivers their best work. 
            You're the conductor of this elite coding symphony.""",
            tools=coordinator_tools,
            bedrock_manager=self.bedrock_manager,
            model_preference="coordinator",
            verbose=True,
            allow_delegation=True
        )
        
        logger.info(f"✅ Created {len(self.agents)} elite agents with Bedrock models")
        return self.agents
    
    def create_crew(self, agents: List[BedrockAgent], tasks: List[Task]) -> Crew:
        """Create a crew with Bedrock-powered agents"""
        self.crew = Crew(
            agents=agents,
            tasks=tasks,
            verbose=2,
            process=Process.hierarchical if "coordinator" in [a.role for a in agents] else Process.sequential,
            manager_agent=next((a for a in agents if "coordinator" in a.role.lower()), None)
        )
        
        return self.crew
    
    def get_model_usage_report(self) -> Dict[str, Any]:
        """Get comprehensive usage and cost report"""
        usage_stats = self.bedrock_manager.get_usage_statistics()
        
        # Add model efficiency analysis
        model_efficiency = {}
        for model_id, stats in usage_stats["models"].items():
            if stats["total_requests"] > 0:
                model_efficiency[model_id] = {
                    "avg_cost_per_request": stats["total_cost"] / stats["total_requests"],
                    "avg_tokens_per_request": stats["total_tokens"] / stats["total_requests"] if stats["total_tokens"] > 0 else 0,
                    "efficiency_score": (stats["total_tokens"] / stats["total_cost"]) if stats["total_cost"] > 0 else 0
                }
        
        return {
            **usage_stats,
            "model_efficiency": model_efficiency,
            "recommendations": self._generate_cost_recommendations(usage_stats)
        }
    
    def _generate_cost_recommendations(self, usage_stats: Dict) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        total_cost = usage_stats["total_cost"]
        
        if total_cost > 50:
            recommendations.append("Consider using more economical models for simple tasks")
        
        # Find most expensive model
        if usage_stats["models"]:
            most_expensive = max(usage_stats["models"].items(), key=lambda x: x[1]["total_cost"])
            if most_expensive[1]["total_cost"] > total_cost * 0.5:
                recommendations.append(f"Consider optimizing usage of {most_expensive[0]} - highest cost contributor")
        
        if not recommendations:
            recommendations.append("Current model usage is optimized")
        
        return recommendations

def main():
    """Demo the Bedrock Elite Crew System"""
    import os
    from elite_tools import EliteToolFactory
    
    print("🔥 ELITE BEDROCK CREW SYSTEM - MULTI-MODEL POWER! 🔥")
    print("=" * 70)
    
    # Check AWS credentials
    if not (os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_PROFILE")):
        print("⚠️ AWS credentials not found. Please set up AWS credentials:")
        print("   - Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        print("   - Or configure AWS profile with 'aws configure'")
        print("   - Or set AWS_PROFILE environment variable")
        return
    
    # Initialize Bedrock crew
    bedrock_crew = EliteBedrockCrew(aws_region=os.getenv("AWS_REGION", "us-east-1"))
    
    # List available models
    print("\n📋 Available Bedrock Models:")
    available_models = bedrock_crew.bedrock_manager.list_available_models()
    for model in available_models[:10]:  # Show first 10
        print(f"   🤖 {model['model_name']} ({model['provider_name']})")
    
    # Create elite agents with tools
    tools_factory = EliteToolFactory()
    agents = bedrock_crew.create_elite_agents(tools_factory)
    
    print("\n🤖 Elite Agents Created:")
    for agent_id, agent in agents.items():
        model_name = agent.model_config.model_id.value.split('.')[-1]
        print(f"   {agent.role}: {model_name}")
    
    # Demo task
    demo_task = Task(
        description="""Create a modern web application with the following features:
        - Responsive design with React components
        - REST API with Node.js backend
        - User authentication system
        - Real-time features with WebSockets
        - Comprehensive test suite
        - CI/CD deployment pipeline
        
        Each agent should contribute their expertise using their specialized Bedrock model.""",
        agent=agents["coordinator"],
        expected_output="Complete web application with all requested features"
    )
    
    # Create and execute crew
    crew = bedrock_crew.create_crew(
        agents=list(agents.values()),
        tasks=[demo_task]
    )
    
    print("\n🚀 Executing Elite Bedrock Crew...")
    try:
        result = crew.kickoff()
        print(f"\n✅ Crew execution completed!")
        print(f"Result: {result}")
        
        # Show usage report
        usage_report = bedrock_crew.get_model_usage_report()
        print(f"\n💰 Cost Report:")
        print(f"Total Cost: ${usage_report['total_cost']:.4f}")
        print(f"Total Requests: {usage_report['total_requests']}")
        print(f"Models Used: {usage_report['total_models_used']}")
        
        print(f"\n📊 Model Efficiency:")
        for model_id, efficiency in usage_report['model_efficiency'].items():
            model_name = model_id.split('.')[-1]
            print(f"   {model_name}: ${efficiency['avg_cost_per_request']:.4f} per request")
        
        print(f"\n💡 Recommendations:")
        for rec in usage_report['recommendations']:
            print(f"   • {rec}")
        
    except Exception as e:
        print(f"❌ Error executing crew: {e}")
        logger.error(f"Crew execution error: {e}")
    
    print("\n🎯 Bedrock Elite Crew system is absolutely fire! 🔥")

if __name__ == "__main__":
    main()