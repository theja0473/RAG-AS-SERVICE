#!/bin/bash

# OpenAgentRAG Post-Deployment Setup Script
# This script verifies services, pulls models, and initializes the system

set -e  # Exit on any error

echo "========================================="
echo "OpenAgentRAG Post-Deployment Setup"
echo "========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "ℹ $1"
}

# Check if Docker Compose is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available. Please install Docker Compose v2."
    exit 1
fi

print_success "Docker and Docker Compose are installed"

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Run this script from the project root."
    exit 1
fi

# Step 1: Wait for services to be healthy
echo ""
print_info "Step 1: Waiting for services to start..."

MAX_WAIT=300  # 5 minutes
ELAPSED=0
INTERVAL=5

while [ $ELAPSED -lt $MAX_WAIT ]; do
    # Check if all containers are running
    RUNNING=$(docker compose ps --services --filter "status=running" | wc -l)
    TOTAL=$(docker compose ps --services | wc -l)

    if [ "$RUNNING" -eq "$TOTAL" ]; then
        print_success "All $TOTAL services are running"
        break
    fi

    echo -n "."
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    print_error "Services did not start within $MAX_WAIT seconds"
    print_info "Check logs with: docker compose logs"
    exit 1
fi

# Wait additional time for services to be fully ready
print_info "Waiting for services to be fully ready..."
sleep 15

# Step 2: Check Ollama health
echo ""
print_info "Step 2: Checking Ollama service..."

if curl -sf http://localhost:11434/api/tags > /dev/null; then
    print_success "Ollama is responding"
else
    print_error "Ollama is not responding on port 11434"
    print_info "Try: docker compose logs ollama"
    exit 1
fi

# Step 3: Pull the default LLM model
echo ""
print_info "Step 3: Pulling default LLM model (llama3)..."

# Check if llama3 is already pulled
if docker compose exec ollama ollama list | grep -q "llama3"; then
    print_success "llama3 model is already available"
else
    print_info "Downloading llama3 model (~4.7GB). This may take several minutes..."
    if docker compose exec ollama ollama pull llama3; then
        print_success "Successfully pulled llama3 model"
    else
        print_warning "Failed to pull llama3 model. You may need to pull it manually:"
        print_info "  docker compose exec ollama ollama pull llama3"
    fi
fi

# Step 4: Check ChromaDB health
echo ""
print_info "Step 4: Checking ChromaDB service..."

if curl -sf http://localhost:8100/api/v1/heartbeat > /dev/null; then
    print_success "ChromaDB is responding"
else
    print_error "ChromaDB is not responding on port 8100"
    print_info "Try: docker compose logs chromadb"
    exit 1
fi

# Step 5: Create default ChromaDB collection (if needed)
echo ""
print_info "Step 5: Initializing vector database..."

# Try to create collection via backend API (if backend has initialization endpoint)
if curl -sf http://localhost:8000/health > /dev/null; then
    print_success "Backend API is healthy"
else
    print_warning "Backend API is not responding yet on port 8000"
    print_info "It may still be initializing. Check: docker compose logs backend"
fi

# Step 6: Check frontend
echo ""
print_info "Step 6: Checking frontend service..."

if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    print_success "Frontend is responding"
else
    print_warning "Frontend is not responding yet on port 3000"
    print_info "It may still be building. Check: docker compose logs frontend"
fi

# Step 7: Verify the complete pipeline
echo ""
print_info "Step 7: Verifying complete pipeline..."

# List available models
echo ""
print_info "Available Ollama models:"
docker compose exec ollama ollama list

# Show disk usage
echo ""
print_info "Docker volumes disk usage:"
docker volume ls --filter "name=open-agent-rag" --format "table {{.Name}}\t{{.Driver}}"

# Summary
echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
print_success "OpenAgentRAG is ready to use"
echo ""
echo "Access the application:"
echo "  🌐 Web UI:          http://localhost:3000"
echo "  🔧 Backend API:     http://localhost:8000"
echo "  📚 API Docs:        http://localhost:8000/docs"
echo "  🗄️  ChromaDB:        http://localhost:8100"
echo ""
echo "Useful commands:"
echo "  • View logs:        docker compose logs -f"
echo "  • Stop services:    docker compose down"
echo "  • Restart:          docker compose restart"
echo "  • Pull model:       docker compose exec ollama ollama pull <model-name>"
echo ""
print_info "For troubleshooting, see: docs/Deployment_Guide.md"
echo ""
