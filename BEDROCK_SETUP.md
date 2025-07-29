# 🔥 Amazon Bedrock Setup Guide - Your AWS, Your Elite Crew! 🔥

This guide will help you configure the Elite Multi-Agent System to use **your own AWS account** with Amazon Bedrock models instead of traditional LLM APIs.

## 🌟 **Why Use Amazon Bedrock?**

✨ **Access Multiple Models**: Claude, Llama, Titan, Jurassic, Command - all in one place  
💰 **Cost Control**: Pay only for what you use with your own AWS billing  
🔒 **Security**: Your data stays in your AWS account  
⚡ **Performance**: Optimized model routing based on task complexity  
📊 **Monitoring**: Full visibility into usage and costs  
🛡️ **Compliance**: Enterprise-grade security and compliance controls  

## 🚀 **Quick Setup (5 Minutes)**

### 1. **AWS Account Setup**

If you don't have an AWS account:
```bash
# Create account at: https://aws.amazon.com/
# Enable Bedrock service in your preferred region
```

### 2. **Request Model Access**

**Important**: You must request access to Bedrock models first!

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Navigate to "Model access" in the left sidebar
3. Click "Request model access"
4. Select the models you want to use:
   - ✅ **Anthropic Claude 3.5 Sonnet** (Recommended)
   - ✅ **Anthropic Claude 3 Haiku** (Fast & economical)
   - ✅ **Anthropic Claude 3 Opus** (Most capable)
   - ✅ **Meta Llama 3 70B** (Great for code)
   - ✅ **Amazon Titan Text** (Cost-effective)
   - ✅ **AI21 Jurassic-2** (Alternative option)
   - ✅ **Cohere Command** (Good for specific tasks)

5. Submit requests and wait for approval (usually instant for most models)

### 3. **Configure AWS Credentials**

Choose **ONE** of these methods:

#### 📋 **Method 1: AWS CLI Profile (Recommended)**
```bash
# Install AWS CLI
pip install awscli

# Configure your profile
aws configure --profile elite-crew
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key  
# Default region: us-east-1 (or your preferred region)
# Default output format: json

# Test access
aws bedrock list-foundation-models --profile elite-crew --region us-east-1
```

#### 🔑 **Method 2: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID=your_access_key_here
export AWS_SECRET_ACCESS_KEY=your_secret_key_here
export AWS_REGION=us-east-1
```

#### 🏢 **Method 3: IAM Roles (For AWS Infrastructure)**
If running on EC2, ECS, or Lambda, use IAM roles - no credentials needed!

### 4. **Setup Elite Crew System**

```bash
# Clone the repository
git clone https://github.com/your-repo/MyCrewRunsDeep
cd MyCrewRunsDeep

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env file with your settings
nano .env
```

### 5. **Configure Your Preferences**

Edit `.env` file:
```env
# AWS Configuration
AWS_PROFILE=elite-crew
AWS_REGION=us-east-1

# Optimization Profile
BEDROCK_OPTIMIZATION_PROFILE=balanced

# Budget Controls
BEDROCK_DAILY_BUDGET=10.00
BEDROCK_COST_ALERT_THRESHOLD=75
```

### 6. **Run the System!**

```bash
# Interactive setup (first time)
python bedrock_elite_system.py

# Or use the web dashboard
python web_dashboard.py
# Visit: http://localhost:8000
```

## 🎯 **Optimization Profiles Explained**

### 💰 **Cost Optimized**
- **Best for**: Development, testing, simple projects
- **Models**: Claude 3 Haiku, Llama 3 8B, Titan Text
- **Estimated cost**: $1-3 per day for typical usage
- **Speed**: Fast
- **Quality**: Good

### 🚀 **Performance Optimized** 
- **Best for**: Production, complex projects, critical tasks
- **Models**: Claude 3 Opus, Claude 3.5 Sonnet, Llama 3 70B
- **Estimated cost**: $10-25 per day for typical usage
- **Speed**: Variable
- **Quality**: Excellent

### ⚖️ **Balanced (Recommended)**
- **Best for**: Most projects, daily development
- **Models**: Claude 3.5 Sonnet, Claude 3 Haiku, Llama 3 70B
- **Estimated cost**: $3-8 per day for typical usage
- **Speed**: Good
- **Quality**: Very good

### 🎨 **Creative**
- **Best for**: UI/UX design, creative writing, innovation
- **Models**: Claude 3.5 Sonnet, Claude 3 Opus (high temperature)
- **Estimated cost**: $5-12 per day for typical usage
- **Focus**: Creativity and innovation

### 📊 **Analytical**
- **Best for**: Data analysis, research, precision tasks
- **Models**: Claude 3 Opus, Claude 3.5 Sonnet (low temperature)
- **Estimated cost**: $8-15 per day for typical usage
- **Focus**: Accuracy and analysis

## 💰 **Cost Management**

### **Typical Usage Costs**
- **Small project** (2-3 agents, 1 hour): $0.50 - $2.00
- **Medium project** (5 agents, 3 hours): $2.00 - $8.00  
- **Large project** (5 agents, 8 hours): $5.00 - $20.00

### **Cost Control Features**
- ✅ Daily budget limits with auto-shutdown
- ✅ Real-time cost tracking and alerts
- ✅ Model usage analytics and optimization recommendations
- ✅ Per-agent cost attribution
- ✅ Smart model routing based on budget remaining

### **Budget Recommendations**
- **Learning/Testing**: $5-10/day
- **Development**: $15-25/day
- **Production**: $25-50/day
- **Enterprise**: $50+/day

## 🔧 **Advanced Configuration**

### **Custom Model Assignment**
```python
# In your user_bedrock_config.json
{
  "model_preferences": {
    "custom_model_assignments": {
      "frontend": "anthropic.claude-3-5-sonnet-20240620-v1:0",
      "backend": "meta.llama3-70b-instruct-v1:0",
      "qa": "anthropic.claude-3-haiku-20240307-v1:0"
    }
  }
}
```

### **Region Selection**
Choose your region based on:
- **Latency**: Closest to your location
- **Model availability**: Not all models in all regions
- **Cost**: Slight variations between regions
- **Compliance**: Data residency requirements

**Recommended regions**:
- `us-east-1` (N. Virginia) - Most models, lowest cost
- `us-west-2` (Oregon) - Good model selection
- `eu-west-1` (Ireland) - European users
- `ap-southeast-2` (Sydney) - Asia-Pacific users

### **Multi-Region Setup**
```env
# Primary region
AWS_REGION=us-east-1

# Fallback regions (for redundancy)
BEDROCK_FALLBACK_REGIONS=us-west-2,eu-west-1
```

## 🛠️ **Troubleshooting**

### **Common Issues**

#### ❌ "No models available"
```bash
# Check model access
aws bedrock list-foundation-models --region us-east-1

# Request model access in AWS Console
# Wait 5-10 minutes after approval
```

#### ❌ "Access denied"
```bash
# Check IAM permissions - you need:
# - bedrock:InvokeModel
# - bedrock:ListFoundationModels
# - bedrock:GetModelInvocationLoggingConfiguration

# Add Bedrock permissions to your IAM user/role
```

#### ❌ "Region not supported"
```bash
# Check available regions:
aws bedrock list-foundation-models --region us-east-1
aws bedrock list-foundation-models --region us-west-2
aws bedrock list-foundation-models --region eu-west-1
```

#### ❌ "Budget exceeded"
```bash
# Check your daily usage:
python -c "from bedrock_elite_system import ConfigurableBedrockSystem; s = ConfigurableBedrockSystem(); print(s.check_budget_status())"

# Increase budget in .env file:
BEDROCK_DAILY_BUDGET=25.00
```

### **Getting Help**

1. **AWS Documentation**: [Bedrock User Guide](https://docs.aws.amazon.com/bedrock/)
2. **AWS Support**: Use your AWS support plan
3. **Community**: GitHub Issues or discussions
4. **Elite Crew Logs**: Check logs for detailed error messages

## 🎉 **You're Ready!**

Your Elite Multi-Agent System is now configured to use **your own AWS account** with Amazon Bedrock! 

### **What's Next?**

1. **Start with a simple project** to test everything works
2. **Monitor your costs** in the first few days
3. **Adjust optimization profile** based on your needs
4. **Scale up** as you get comfortable with the system

### **Pro Tips**

- 🔥 Start with **Balanced** profile - it's optimized for most use cases
- 💰 Set a **low daily budget** initially ($5-10) while learning
- 📊 Use the **web dashboard** to monitor real-time usage
- ⚡ Enable **auto-shutdown** to prevent budget overruns
- 🛡️ Keep your **AWS credentials secure** - never commit them to git

---

**🔥 Welcome to the future of AI development with your own Elite Crew! 🔥**

The streets are hot, and your crew is ready to deliver absolute fire! 🚀