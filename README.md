# PropertyAI - AI-Powered Real Estate Platform

A modern real estate platform with AI content generation, Facebook integration, and multi-language support.

## ✨ Features

- 🤖 **AI Content Generation** - Multi-language property descriptions
- 📘 **Facebook Integration** - Automated social media posting
- 🔐 **Secure Authentication** - JWT-based user management
- 🌍 **Multi-language Support** - English, Hindi, Marathi, Gujarati
- 📱 **Responsive Design** - Modern web interface
- 🐳 **Docker Support** - Easy deployment

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- MongoDB
- Docker (optional)

### Local Development
```bash
# Clone repository
git clone <repository-url>
cd realestate_ai

# Start services
.\start-local.ps1
```

### Docker Deployment
```bash
# Start with Docker
.\start-docker.ps1
```

## 📁 Project Structure

```
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── e2e-tests/        # End-to-end tests
├── docker/          # Docker configuration
└── tests/           # Backend unit tests
```

## 🧪 Testing

```bash
# Backend tests
cd backend && python -m pytest

# Frontend tests
cd frontend && npm test

# E2E tests
cd frontend && npm run test:e2e
```

## 🚀 Deployment

- **Development**: `.\start-local.ps1`
- **Production**: `.\start-docker.ps1`
- **CI/CD**: GitHub Actions workflows included

## 📚 Documentation

- [Implementation Guide](IMPLEMENTATION_GUIDE.md)
- [API Documentation](openapi.json)
- [Deployment Guide](README-DEPLOYMENT.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `npm test && python -m pytest`
5. Submit a pull request

## 📄 License

MIT License