# Vaidya - Medical Chatbot System

A comprehensive medical chatbot system that provides accurate healthcare information through an intelligent conversational interface using RAG (Retrieval-Augmented Generation) architecture.

## 🏥 Features

- **Medical Knowledge Base**: Processes authoritative medical documents and creates semantic embeddings
- **RAG Architecture**: Combines vector search with LLM generation for accurate responses
- **Real-time Chat**: WebSocket-based chat interface with typing indicators
- **Medical Compliance**: HIPAA-compliant with appropriate medical disclaimers
- **Mobile-First**: Responsive design with PWA capabilities
- **Multi-modal**: Text and voice input support
- **Secure**: End-to-end encryption and comprehensive audit trails

## 🏗️ Architecture

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configurations
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # React.js frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── utils/          # Utility functions
│   ├── public/             # Static assets
│   └── package.json        # Node dependencies
├── mobile/                 # React Native app
├── docs/                   # Documentation
├── scripts/                # Automation scripts
└── docker-compose.yml      # Container orchestration
```

## 🚀 Quick Start

1. **Setup Environment**
   ```bash
   ./scripts/setup.sh
   ```

2. **Start Development**
   ```bash
   docker-compose up -d
   ```

3. **Access Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 🔧 Configuration

Create `.env` files with required environment variables:
- OpenAI API key
- Pinecone API key
- Database credentials
- Security keys

## 📚 Documentation

- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Security Guide](docs/security.md)
- [Medical Compliance](docs/compliance.md)

## ⚠️ Medical Disclaimer

This system is for informational purposes only and should not replace professional medical advice, diagnosis, or treatment.

## 📄 License

MIT License - See LICENSE file for details.
