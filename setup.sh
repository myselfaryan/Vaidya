#!/bin/bash

# Vaidya Medical Chatbot Setup Script

echo "🏥 Setting up Vaidya Medical Chatbot..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_status "Docker and Docker Compose are installed ✓"
}

# Check if Node.js is installed (for local development)
check_node() {
    if ! command -v node &> /dev/null; then
        print_warning "Node.js is not installed. You'll need it for local frontend development."
        echo "Visit: https://nodejs.org/"
    else
        NODE_VERSION=$(node --version)
        print_status "Node.js is installed: $NODE_VERSION ✓"
    fi
}

# Check if Python is installed (for local development)
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_warning "Python 3 is not installed. You'll need it for local backend development."
        echo "Visit: https://python.org/"
    else
        PYTHON_VERSION=$(python3 --version)
        print_status "Python is installed: $PYTHON_VERSION ✓"
    fi
}

# Create environment file
setup_env() {
    print_header "Setting up environment variables..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        print_status "Created .env file from template"
        print_warning "Please edit .env file with your actual API keys and configuration"
        echo ""
        echo "Required API keys:"
        echo "1. OpenAI API Key: https://platform.openai.com/api-keys"
        echo "2. Pinecone API Key: https://app.pinecone.io/"
        echo ""
    else
        print_status ".env file already exists"
    fi
}

# Install backend dependencies
setup_backend() {
    print_header "Setting up backend..."
    
    cd backend
    
    if command -v python3 &> /dev/null; then
        # Create virtual environment
        if [ ! -d "venv" ]; then
            python3 -m venv venv
            print_status "Created Python virtual environment"
        fi
        
        # Activate virtual environment and install dependencies
        source venv/bin/activate
        pip install -r requirements.txt
        print_status "Installed Python dependencies"
    else
        print_warning "Python not found. Backend dependencies will be installed via Docker."
    fi
    
    cd ..
}

# Install frontend dependencies
setup_frontend() {
    print_header "Setting up frontend..."
    
    cd frontend
    
    if command -v npm &> /dev/null; then
        npm install
        print_status "Installed Node.js dependencies"
    else
        print_warning "npm not found. Frontend dependencies will be installed via Docker."
    fi
    
    cd ..
}

# Create necessary directories
create_directories() {
    print_header "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p data/uploads
    mkdir -p data/medical_docs
    
    print_status "Created project directories"
}

# Generate secret key
generate_secret_key() {
    if command -v python3 &> /dev/null; then
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        echo "Generated SECRET_KEY: $SECRET_KEY"
        echo "Add this to your .env file:"
        echo "SECRET_KEY=$SECRET_KEY"
    else
        print_warning "Python not available to generate secret key. Please generate one manually."
    fi
}

# Main setup function
main() {
    print_header "🏥 Vaidya Medical Chatbot Setup"
    echo "========================================"
    
    # Check prerequisites
    check_docker
    check_node
    check_python
    
    # Setup project
    setup_env
    create_directories
    setup_backend
    setup_frontend
    
    echo ""
    print_header "🎉 Setup Complete!"
    echo "========================================"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file with your API keys"
    echo "2. Run: docker-compose up -d"
    echo "3. Visit: http://localhost:3000 (Frontend)"
    echo "4. API docs: http://localhost:8000/docs"
    echo ""
    echo "For development:"
    echo "- Backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
    echo "- Frontend: cd frontend && npm start"
    echo ""
    
    generate_secret_key
}

# Run main function
main
