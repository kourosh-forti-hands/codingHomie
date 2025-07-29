# ⚙️ Configuration Guide - Master Your Elite Bedrock System

Complete guide to configuring and customizing your Elite Multi-Agent System with Amazon Bedrock.

## 📋 **Table of Contents**

1. [Quick Configuration](#quick-configuration)
2. [Environment Variables](#environment-variables)
3. [Profile Configuration](#profile-configuration)
4. [AWS Setup](#aws-setup)
5. [Budget Controls](#budget-controls)
6. [Custom Agent Configuration](#custom-agent-configuration)
7. [Advanced Settings](#advanced-settings)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 **Quick Configuration**

### **1. Initial Setup**
```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env

# Run interactive setup
python bedrock_elite_system.py
```

### **2. Minimal .env Configuration**
```env
# Required settings
AWS_PROFILE=your-aws-profile
AWS_REGION=us-east-1
BEDROCK_OPTIMIZATION_PROFILE=balanced
BEDROCK_DAILY_BUDGET=10.00
```

### **3. Test Configuration**
```bash
# Validate setup
python -c "from bedrock_elite_system import ConfigurableBedrockSystem; s = ConfigurableBedrockSystem(); print('✅ Configuration valid!' if s.validate_aws_access() else '❌ Configuration invalid')"
```

---

## 🌍 **Environment Variables**

### **AWS Authentication**
```env
# Method 1: AWS Profile (Recommended)
AWS_PROFILE=elite-crew
AWS_REGION=us-east-1

# Method 2: Direct Credentials  
# AWS_ACCESS_KEY_ID=AKIA...
# AWS_SECRET_ACCESS_KEY=...
# AWS_REGION=us-east-1

# Method 3: IAM Roles (for EC2/ECS/Lambda)
# No credentials needed - uses instance role
AWS_REGION=us-east-1
```

### **Bedrock Configuration**
```env
# Optimization profile
BEDROCK_OPTIMIZATION_PROFILE=balanced
# Options: cost_optimized, performance_optimized, balanced, creative, analytical

# Budget controls
BEDROCK_DAILY_BUDGET=10.00
BEDROCK_COST_ALERT_THRESHOLD=75
BEDROCK_AUTO_SHUTDOWN_ENABLED=true

# Performance settings
BEDROCK_MAX_CONCURRENT_REQUESTS=5
BEDROCK_DEFAULT_TIMEOUT=120
BEDROCK_RETRY_ATTEMPTS=3
```

### **System Configuration**
```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./elite_crew.db

# Web Dashboard
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8000

# Logging
LOG_LEVEL=INFO
ENABLE_METRICS=true

# Security
SECRET_KEY=your-secret-key-here
```

---

## 🎯 **Profile Configuration**

### **Using Pre-built Profiles**
```env
# Set in .env file
BEDROCK_OPTIMIZATION_PROFILE=balanced

# Or set programmatically
python -c "
from bedrock_config import EliteBedrockConfig, AgentOptimizationProfile
config = EliteBedrockConfig(AgentOptimizationProfile.PERFORMANCE_OPTIMIZED)
"
```

### **Profile Comparison**
| Setting | Cost Optimized | Balanced | Performance | Creative | Analytical |
|---------|----------------|----------|-------------|----------|------------|
| Daily Budget | $1-3 | $3-8 | $10-25 | $5-12 | $8-15 |
| Primary Models | Haiku, Llama 8B | Sonnet, Haiku | Opus, Sonnet | Sonnet, Opus | Opus, Sonnet |
| Max Tokens | 1500-3000 | 2000-3500 | 3000-4000 | 3000-4000 | 3000-4000 |
| Temperature | 0.2-0.5 | 0.2-0.8 | 0.2-0.8 | 0.7-0.9 | 0.1-0.3 |

### **Creating Custom Profiles**
```python
# In bedrock_config.py
def _create_custom_profile(self) -> Dict[str, BedrockAgentConfig]:
    return {
        "frontend": BedrockAgentConfig(
            agent_role="Frontend Specialist",
            primary_model=BedrockModel.CLAUDE_3_5_SONNET,
            fallback_model=BedrockModel.CLAUDE_3_HAIKU,
            max_tokens=3000,
            temperature=0.8,
            max_cost_per_hour=5.0
        ),
        # ... other agents
    }
```

---

## 🔧 **AWS Setup**

### **1. AWS Account Preparation**
```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure --profile elite-crew
# AWS Access Key ID: [Enter your key]
# AWS Secret Access Key: [Enter your secret]
# Default region name: us-east-1
# Default output format: json
```

### **2. Request Bedrock Model Access**
1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Navigate to "Model access" 
3. Click "Request model access"
4. Select models:
   - ✅ Anthropic Claude 3.5 Sonnet
   - ✅ Anthropic Claude 3 Haiku  
   - ✅ Anthropic Claude 3 Opus
   - ✅ Meta Llama 3 70B
   - ✅ Meta Llama 3 8B
   - ✅ Amazon Titan Text

### **3. IAM Permissions**
Required permissions for your AWS user/role:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:ListFoundationModels",
                "bedrock:GetModelInvocationLoggingConfiguration"
            ],
            "Resource": "*"
        }
    ]
}
```

### **4. Test AWS Access**
```bash
# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1 --profile elite-crew

# Should return a list of available models
```

---

## 💰 **Budget Controls**

### **Basic Budget Configuration**
```env
# Daily spending limit
BEDROCK_DAILY_BUDGET=25.00

# Alert when reaching percentage of budget
BEDROCK_COST_ALERT_THRESHOLD=75

# Automatically shutdown when budget exceeded
BEDROCK_AUTO_SHUTDOWN_ENABLED=true

# Emergency stop threshold
BEDROCK_EMERGENCY_STOP_THRESHOLD=95
```

### **Advanced Budget Controls**
```python
# In user_bedrock_config.json
{
  "budget_settings": {
    "daily_limit": 25.0,
    "weekly_limit": 150.0,
    "monthly_limit": 500.0,
    "alert_threshold_percentage": 75,
    "auto_shutdown_enabled": true,
    "cost_tracking_enabled": true,
    "budget_reset_time": "00:00",
    "emergency_contact": "admin@company.com"
  }
}
```

### **Per-Agent Budget Limits**
```python
{
  "agent_budget_limits": {
    "frontend": 5.0,    # $5/hour max
    "backend": 8.0,     # $8/hour max  
    "qa": 3.0,          # $3/hour max
    "ml": 15.0,         # $15/hour max
    "devops": 4.0,      # $4/hour max
    "coordinator": 3.0  # $3/hour max
  }
}
```

### **Budget Monitoring**
```python
# Check current budget status
from bedrock_elite_system import ConfigurableBedrockSystem
system = ConfigurableBedrockSystem()
budget_status = system.check_budget_status()

print(f"Used: ${budget_status['current_cost']:.2f}")
print(f"Remaining: ${budget_status['remaining_budget']:.2f}")
print(f"Percentage: {budget_status['percentage_used']:.1f}%")
```

---

## 🤖 **Custom Agent Configuration**

### **Per-Agent Model Override**
```json
{
  "model_preferences": {
    "custom_model_assignments": {
      "frontend": "anthropic.claude-3-5-sonnet-20240620-v1:0",
      "backend": "meta.llama3-70b-instruct-v1:0",
      "qa": "anthropic.claude-3-haiku-20240307-v1:0",
      "ml": "anthropic.claude-3-opus-20240229-v1:0",
      "devops": "meta.llama3-8b-instruct-v1:0",
      "coordinator": "anthropic.claude-3-5-sonnet-20240620-v1:0"
    }
  }
}
```

### **Agent-Specific Parameters**
```json
{
  "agent_configurations": {
    "frontend": {
      "max_tokens": 3000,
      "temperature": 0.8,
      "timeout_seconds": 60,
      "max_cost_per_hour": 8.0,
      "retry_attempts": 3,
      "fallback_models": [
        "anthropic.claude-3-haiku-20240307-v1:0"
      ]
    },
    "backend": {
      "max_tokens": 4000,
      "temperature": 0.3,
      "timeout_seconds": 90,
      "max_cost_per_hour": 10.0,
      "retry_attempts": 2,
      "fallback_models": [
        "meta.llama3-8b-instruct-v1:0"
      ]
    }
  }
}
```

### **Role-Specific Configurations**
```json
{
  "role_specific_configs": {
    "frontend": {
      "ui_framework_preference": "React with TypeScript",
      "styling_approach": "Tailwind CSS + Styled Components",
      "state_management": "Zustand",
      "testing_framework": "Vitest + Testing Library",
      "build_tool": "Vite"
    },
    "backend": {
      "preferred_language": "Node.js with TypeScript",
      "framework": "Fastify",
      "database": "PostgreSQL with Prisma",
      "caching": "Redis",
      "api_style": "GraphQL + REST",
      "auth_strategy": "JWT + OAuth2"
    },
    "qa": {
      "testing_strategy": "comprehensive",
      "coverage_target": 90,
      "frameworks": ["Jest", "Playwright", "k6"],
      "automation_level": "high",
      "reporting": "Allure"
    }
  }
}
```

---

## ⚙️ **Advanced Settings**

### **Circuit Breaker Configuration**
```json
{
  "circuit_breaker_settings": {
    "failure_threshold": 5,
    "recovery_timeout": 300,
    "success_threshold": 3,
    "enabled": true
  }
}
```

### **Retry Logic Configuration**
```json
{
  "retry_settings": {
    "max_attempts": 3,
    "base_delay": 1.0,
    "max_delay": 60.0,
    "strategy": "exponential",
    "backoff_multiplier": 2.0,
    "jitter": true
  }
}
```

### **Performance Monitoring**
```json
{
  "monitoring_settings": {
    "enable_metrics": true,
    "enable_logging": true,
    "log_level": "INFO",
    "metrics_retention_days": 30,
    "performance_alerts": {
      "response_time_threshold": 10.0,
      "error_rate_threshold": 0.05,
      "cost_spike_threshold": 2.0
    }
  }
}
```

### **Multi-Region Configuration**
```json
{
  "multi_region_settings": {
    "primary_region": "us-east-1",
    "fallback_regions": ["us-west-2", "eu-west-1"],
    "auto_failover": true,
    "region_selection_strategy": "lowest_latency"
  }
}
```

---

## 🔧 **Configuration Files**

### **Main Configuration File Structure**
```
user_bedrock_config.json
├── version: "1.0"
├── user_info: {...}
├── aws_settings: {...}
├── optimization_profile: "balanced"
├── budget_settings: {...}
├── project_settings: {...}
├── model_preferences: {...}
└── notification_settings: {...}
```

### **Environment-Specific Configs**
```bash
# Development
cp user_bedrock_config.json user_bedrock_config.dev.json

# Staging  
cp user_bedrock_config.json user_bedrock_config.staging.json

# Production
cp user_bedrock_config.json user_bedrock_config.prod.json

# Load specific config
BEDROCK_CONFIG_FILE=user_bedrock_config.prod.json python bedrock_elite_system.py
```

### **Team Configuration**
```json
{
  "team_settings": {
    "shared_budget": 100.0,
    "budget_allocation": {
      "frontend_team": 0.3,
      "backend_team": 0.4,
      "qa_team": 0.2,
      "devops_team": 0.1
    },
    "shared_preferences": {
      "optimization_profile": "balanced",
      "fallback_strategy": "cost_effective"
    }
  }
}
```

---

## 🐛 **Troubleshooting**

### **Common Configuration Issues**

#### **AWS Access Denied**
```bash
# Check credentials
aws sts get-caller-identity --profile elite-crew

# Verify region
aws configure get region --profile elite-crew

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1 --profile elite-crew
```

#### **Model Access Issues**
```bash
# Check model access status
aws bedrock list-foundation-models --region us-east-1 | grep -A 5 "claude-3"

# Request access in console if needed
echo "Go to: https://console.aws.amazon.com/bedrock/home#/modelaccess"
```

#### **Budget Configuration Problems**
```python
# Validate budget settings
from bedrock_elite_system import ConfigurableBedrockSystem
system = ConfigurableBedrockSystem()
budget = system.check_budget_status()
print(f"Budget valid: {budget['daily_limit'] > 0}")
```

### **Configuration Validation**
```python
# Comprehensive config validation
def validate_configuration():
    try:
        system = ConfigurableBedrockSystem()
        
        # Test AWS access
        if not system.validate_aws_access():
            return "❌ AWS access failed"
        
        # Test budget settings
        budget = system.check_budget_status()
        if budget['daily_limit'] <= 0:
            return "❌ Invalid budget settings"
        
        # Test agent creation
        agents = asyncio.run(system.create_optimized_crew())
        if len(agents) < 5:
            return "❌ Agent creation failed"
        
        return "✅ Configuration valid"
        
    except Exception as e:
        return f"❌ Configuration error: {e}"

print(validate_configuration())
```

### **Debugging Commands**
```bash
# Show current configuration
python -c "
from bedrock_elite_system import ConfigurableBedrockSystem
import json
system = ConfigurableBedrockSystem()
print(json.dumps(system.user_config, indent=2))
"

# Test model access
python -c "
from bedrock_integration import BedrockModelManager
manager = BedrockModelManager()
models = manager.list_available_models()
print(f'Available models: {len(models)}')
for model in models[:5]:
    print(f'  - {model[\"model_name\"]}')
"

# Check usage statistics
python -c "
from bedrock_elite_system import ConfigurableBedrockSystem
system = ConfigurableBedrockSystem()
print('Usage stats:', system.usage_tracker)
"
```

---

## 📋 **Configuration Checklist**

### **Initial Setup**
- [ ] AWS CLI installed and configured
- [ ] AWS profile created with correct credentials
- [ ] Bedrock model access requested and approved
- [ ] Environment variables set in `.env` file
- [ ] Budget limits configured appropriately
- [ ] Optimization profile selected

### **Testing**
- [ ] AWS access validation passed
- [ ] Model listing returns available models
- [ ] Agent creation succeeds
- [ ] Budget monitoring works
- [ ] Cost tracking functions properly

### **Production Readiness**
- [ ] Production-appropriate budget limits set
- [ ] Monitoring and alerting configured
- [ ] Error handling and retry logic tested
- [ ] Fallback strategies validated
- [ ] Team access and permissions configured
- [ ] Backup and recovery procedures documented

### **Ongoing Maintenance**
- [ ] Regular budget usage reviews
- [ ] Performance metrics monitoring
- [ ] Configuration updates for new models
- [ ] Cost optimization reviews
- [ ] Security settings audits

---

## 🚀 **Best Practices**

### **Configuration Management**
1. **Version control** your configuration files
2. **Use environment-specific** configs for dev/staging/prod
3. **Regular backups** of working configurations
4. **Document changes** and reasons for modifications
5. **Test configurations** thoroughly before deployment

### **Security**
1. **Never commit** AWS credentials to version control
2. **Use IAM roles** when possible instead of access keys
3. **Rotate credentials** regularly
4. **Monitor access** and usage patterns
5. **Enable CloudTrail** for audit logging

### **Cost Management**
1. **Start with conservative** budget limits
2. **Monitor spending** patterns regularly
3. **Optimize model selection** based on actual usage
4. **Set up alerts** for unusual spending
5. **Review and adjust** budgets monthly

---

**⚙️ Master your configuration, and your Elite Crew will deliver consistent fire! 🔥**