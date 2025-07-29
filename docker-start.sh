#!/bin/bash

# 🔥 Elite Crew System - Docker Startup Script
# This script helps you get the Elite Multi-Agent System running with Docker

set -e

echo "🔥 ELITE CREW SYSTEM - DOCKER DEPLOYMENT 🔥"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

print_fire() {
    echo -e "${PURPLE}🔥 $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

# Check required ports
print_info "Checking port availability..."
REQUIRED_PORTS=(80 3000 5432 5601 6379 8000 9090 9100 9200)
UNAVAILABLE_PORTS=()

for port in "${REQUIRED_PORTS[@]}"; do
    if ! check_port $port; then
        UNAVAILABLE_PORTS+=($port)
    fi
done

if [ ${#UNAVAILABLE_PORTS[@]} -ne 0 ]; then
    print_warning "The following ports are already in use: ${UNAVAILABLE_PORTS[*]}"
    print_warning "You may need to stop other services or modify docker-compose.yml"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_status ".env file created from template"
        print_warning "Please edit .env file with your actual API keys and settings"
        read -p "Press Enter to continue after editing .env file..."
    else
        print_error ".env.example file not found. Cannot create .env file."
        exit 1
    fi
fi

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p logs data monitoring/dashboards nginx/ssl
print_status "Directories created"

# Create basic nginx configuration if it doesn't exist
if [ ! -f nginx/nginx.conf ]; then
    print_info "Creating nginx configuration..."
    mkdir -p nginx
    cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream elite_crew {
        server elite-crew:8000;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://elite_crew;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /ws/ {
            proxy_pass http://elite_crew;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF
    print_status "Nginx configuration created"
fi

# Create basic Prometheus configuration if it doesn't exist
if [ ! -f monitoring/prometheus.yml ]; then
    print_info "Creating Prometheus configuration..."
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'elite-crew'
    static_configs:
      - targets: ['elite-crew:8000']
  
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
  
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF
    print_status "Prometheus configuration created"
fi

# Create Grafana datasource configuration
if [ ! -f monitoring/grafana-datasources.yml ]; then
    print_info "Creating Grafana datasource configuration..."
    cat > monitoring/grafana-datasources.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF
    print_status "Grafana datasource configuration created"
fi

# Create Grafana dashboard provisioning configuration
if [ ! -f monitoring/grafana-dashboards.yml ]; then
    print_info "Creating Grafana dashboard configuration..."
    cat > monitoring/grafana-dashboards.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'elite-crew-dashboards'
    orgId: 1
    folder: 'Elite Crew'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF
    print_status "Grafana dashboard configuration created"
fi

# Function to show startup commands
show_commands() {
    echo
    print_fire "AVAILABLE COMMANDS:"
    echo "  🚀 Start all services:        ./docker-start.sh up"
    echo "  🛑 Stop all services:         ./docker-start.sh down"
    echo "  📊 View logs:                 ./docker-start.sh logs"
    echo "  🔄 Restart services:          ./docker-start.sh restart"
    echo "  🏗️ Build and start:           ./docker-start.sh build"
    echo "  🧹 Clean up:                  ./docker-start.sh clean"
    echo "  📈 Show status:               ./docker-start.sh status"
    echo
}

# Function to start services
start_services() {
    print_fire "Starting Elite Crew System..."
    
    # Use docker-compose if available, otherwise use docker compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    print_info "Pulling latest images..."
    $COMPOSE_CMD pull
    
    print_info "Starting services..."
    $COMPOSE_CMD up -d
    
    print_status "Services started successfully!"
    
    echo
    print_fire "🎯 ELITE CREW SYSTEM IS NOW RUNNING! 🎯"
    echo
    print_info "📊 Web Dashboard:      http://localhost:8000"
    print_info "📈 Grafana:           http://localhost:3000 (admin/eliteadmin)"
    print_info "🔍 Prometheus:        http://localhost:9090"
    print_info "📝 Kibana:            http://localhost:5601"
    print_info "🗄️ Database:          localhost:5432 (elitecrew/elitepass)"
    print_info "⚡ Redis:             localhost:6379"
    echo
    print_status "System is ready to deliver some fire! 🔥"
}

# Function to stop services
stop_services() {
    print_info "Stopping Elite Crew System..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    else
        docker compose down
    fi
    
    print_status "Services stopped successfully!"
}

# Function to show logs
show_logs() {
    if command -v docker-compose &> /dev/null; then
        docker-compose logs -f
    else
        docker compose logs -f
    fi
}

# Function to restart services
restart_services() {
    print_info "Restarting Elite Crew System..."
    stop_services
    start_services
}

# Function to build and start
build_and_start() {
    print_info "Building and starting Elite Crew System..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose build --no-cache
        docker-compose up -d
    else
        docker compose build --no-cache
        docker compose up -d
    fi
    
    print_status "Build and start completed!"
}

# Function to clean up
cleanup() {
    print_warning "This will remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleaning up..."
        
        if command -v docker-compose &> /dev/null; then
            docker-compose down -v --remove-orphans
        else
            docker compose down -v --remove-orphans
        fi
        
        docker system prune -f
        print_status "Cleanup completed!"
    else
        print_info "Cleanup cancelled"
    fi
}

# Function to show status
show_status() {
    print_info "Elite Crew System Status:"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi
}

# Main command handling
case "${1:-help}" in
    "up"|"start")
        start_services
        ;;
    "down"|"stop")
        stop_services
        ;;
    "logs")
        show_logs
        ;;
    "restart")
        restart_services
        ;;
    "build")
        build_and_start
        ;;
    "clean")
        cleanup
        ;;
    "status")
        show_status
        ;;
    "help"|*)
        show_commands
        ;;
esac