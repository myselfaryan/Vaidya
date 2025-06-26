# 🏥 Vaidya Medical Chatbot - Getting Started Guide

Welcome to Vaidya, an AI-powered medical chatbot system built with FastAPI and React. This guide will help you get the project up and running.

## 📋 Prerequisites

Before starting, make sure you have the following installed:

### Required
- **Docker** (v20.0+) and **Docker Compose** (v2.0+)
  - [Install Docker](https://docs.docker.com/get-docker/)
  - [Install Docker Compose](https://docs.docker.com/compose/install/)

### Optional (for local development)
- **Python 3.11+** - [Install Python](https://python.org/)
- **Node.js 18+** and **npm** - [Install Node.js](https://nodejs.org/)

## 🚀 Quick Start (Recommended)

### 1. Clone and Setup
```bash
# Navigate to project directory
cd /home/aryan/Desktop/Vaidya

# Run the setup script
./setup.sh
```

### 2. Configure Environment Variables
Edit the `.env` file with your API keys:

```bash
# Open the environment file
nano .env
```

**Required API Keys:**
- `OPENAI_API_KEY`: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- `PINECONE_API_KEY`: Get from [Pinecone](https://app.pinecone.io/)
- `PINECONE_ENVIRONMENT`: Your Pinecone environment (e.g., "us-west1-gcp")

**Example .env configuration:**
```env
DEBUG=True
SECRET_KEY=your-generated-secret-key-here

DATABASE_URL=postgresql://vaidya_user:vaidya_password@localhost:5432/vaidya_db
REDIS_URL=redis://localhost:6379

OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4-turbo-preview

PINECONE_API_KEY=your-pinecone-key-here
PINECONE_ENVIRONMENT=us-west1-gcp

BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### 3. Start the Application
```bash
# Start all services with Docker Compose
docker-compose up -d

# Check if services are running
docker-compose ps
```

### 4. Access the Application
- **Frontend (React)**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🛠️ Development Setup

For local development without Docker:

### Backend Development
```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DEBUG` | Enable debug mode | No | `False` |
| `SECRET_KEY` | JWT secret key | Yes | - |
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `REDIS_URL` | Redis connection string | Yes | `redis://localhost:6379` |
| `OPENAI_API_KEY` | OpenAI API key | Yes | - |
| `OPENAI_MODEL` | OpenAI model to use | No | `gpt-4-turbo-preview` |
| `PINECONE_API_KEY` | Pinecone API key | Yes | - |
| `PINECONE_ENVIRONMENT` | Pinecone environment | Yes | - |

### Getting API Keys

#### OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

#### Pinecone API Key
1. Visit [Pinecone](https://app.pinecone.io/)
2. Sign up or log in
3. Create a new project
4. Go to API Keys section
5. Copy the API key and environment to your `.env` file

## 📊 Monitoring and Logs

### View Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
docker-compose logs redis

# Follow logs in real-time
docker-compose logs -f backend
```

### Health Checks
```bash
# Check API health
curl http://localhost:8000/health

# Check system info (debug mode only)
curl http://localhost:8000/system/info
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📚 API Usage

### Authentication
```bash
# Register a new user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass123"}'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
```

### Medical Queries
```bash
# Ask a medical question
curl -X POST "http://localhost:8000/api/v1/chat/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"question": "What are the symptoms of flu?"}'
```

## 🔒 Security Considerations

1. **Never commit API keys** to version control
2. **Use strong passwords** for database and Redis
3. **Enable HTTPS** in production
4. **Regularly update dependencies**
5. **Monitor for security vulnerabilities**

## 🚧 Troubleshooting

### Common Issues

#### "Permission denied" when running setup.sh
```bash
chmod +x setup.sh
./setup.sh
```

#### Docker services won't start
```bash
# Check Docker daemon
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# Check for port conflicts
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :3000
```

#### Database connection errors
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

#### Frontend build errors
```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Performance Issues

#### Slow AI responses
- Check OpenAI API rate limits
- Monitor Pinecone query performance
- Verify network connectivity

#### High memory usage
- Reduce batch sizes in vector processing
- Optimize database queries
- Monitor Docker container resources

## 📖 Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://react.dev/
- **OpenAI API Reference**: https://platform.openai.com/docs/api-reference
- **Pinecone Documentation**: https://docs.pinecone.io/
- **Docker Compose Guide**: https://docs.docker.com/compose/

## 🆘 Getting Help

If you encounter issues:

1. Check the logs: `docker-compose logs`
2. Verify your `.env` configuration
3. Ensure all API keys are valid
4. Check the troubleshooting section above
5. Review the API documentation at http://localhost:8000/docs

## 🎉 Next Steps

Once you have the basic system running:

1. **Upload Medical Documents**: Use the document management API
2. **Customize the Chat Interface**: Modify the React components
3. **Add Authentication**: Implement user registration and login
4. **Deploy to Production**: Set up cloud deployment
5. **Monitor Performance**: Add logging and monitoring

Happy coding! 🚀
