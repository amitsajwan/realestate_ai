# PropertyAI - Next-Generation Real Estate CRM
*AI-Powered Real Estate Management with Facebook Integration*

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React Native](https://img.shields.io/badge/React_Native-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactnative.dev/)
[![GROQ](https://img.shields.io/badge/AI-GROQ%20LLM-orange?style=for-the-badge)](https://groq.com/)
[![Facebook](https://img.shields.io/badge/Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white)](https://developers.facebook.com/)

## 🏠 Overview

PropertyAI is a comprehensive, AI-powered real estate CRM solution designed specifically for Indian real estate agents. It combines modern web technologies with advanced AI capabilities to streamline property management, automate social media posting, and enhance agent productivity.

### ✨ Key Features

- **🤖 AI Content Generation**: Real LLM integration using GROQ for property descriptions and branding
- **📱 Modern Onboarding**: 7-step AI-powered agent onboarding with Facebook integration
- **🔗 Facebook Automation**: Complete OAuth flow, page management, and automated posting
- **🏠 Smart Properties**: AI-generated property listings with multi-language support
- **🌏 Localization**: Support for English, Hindi, Marathi, and Gujarati
- **📱 Mobile-Responsive**: Works seamlessly across all devices
- **🔐 Secure Authentication**: JWT-based auth with bcrypt password hashing

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+ (for testing)
- Facebook Developer Account (optional, for social media features)

### Installation

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd realestate_ai
   ```

2. **Setup Environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

3. **Initialize Database**
   ```bash
   python database_setup.py
   ```

4. **Start Application**
   ```bash
   python simple_backend.py
   ```

5. **Access Application**
   - Open http://localhost:8003
   - Login with demo@mumbai.com / password123

## 📖 Documentation

### 📚 **[Complete Guide](PROPERTYAI_COMPLETE_GUIDE.md)**
Comprehensive overview including features, installation, API documentation, and business value.

### 🔧 **[Technical Documentation](TECHNICAL_DOCUMENTATION.md)**
Detailed architecture, database schema, API specifications, and security implementation.

### 🚀 **[Deployment Guide](DEPLOYMENT_GUIDE.md)**
Production deployment, Docker configuration, cloud setup, and monitoring.

## 🧪 Testing

### Automated Testing with Playwright
```bash
# Install test dependencies
npm install
npx playwright install

# Run all tests
npx playwright test

# Run specific test suites
npx playwright test tests/auth.spec.ts
npx playwright test tests/modern-onboarding-flow.spec.ts
npx playwright test tests/facebook-connect-demo.spec.ts
```

### Test Coverage
- ✅ Authentication and login flow
- ✅ Complete 7-step onboarding process
- ✅ Facebook integration and OAuth
- ✅ Property management and AI content generation
- ✅ Mobile responsiveness
- ✅ API endpoint validation

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │  Mobile App     │    │  External APIs  │
│   (Bootstrap)   │    │ (React Native)  │    │ (Facebook, AI)  │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴───────────┐
                    │    FastAPI Backend      │
                    │   (simple_backend.py)   │
                    └─────────────┬───────────┘
                                  │
                    ┌─────────────┴───────────┐
                    │   SQLite Database       │
                    │   (propertyai.db)       │
                    └─────────────────────────┘
```

## 🔧 Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for Python
- **SQLite**: Lightweight database (PostgreSQL for production)
- **JWT**: Secure authentication tokens
- **bcrypt**: Password hashing

### Frontend
- **Bootstrap 5**: Responsive UI framework
- **Font Awesome**: Icon library
- **Modern JavaScript**: ES6+ features

### AI Integration
- **GROQ**: Real LLM for content generation
- **Multi-language**: Localized content support

### Social Media
- **Facebook Graph API**: Complete integration
- **OAuth 2.0**: Secure authentication
- **Token Encryption**: Secure credential storage

### Testing
- **Playwright**: End-to-end testing framework
- **TypeScript**: Type-safe test development

## 📱 Mobile Application

The project includes a React Native mobile application located in the `mobile-app/` directory. See the [mobile app README](mobile-app/README.md) for setup instructions.

## 🔐 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt for secure password storage
- **Token Encryption**: Fernet encryption for Facebook tokens
- **Input Validation**: Comprehensive data validation
- **CORS Protection**: Configurable cross-origin policies
- **Rate Limiting**: API endpoint protection

## 🌍 Localization

PropertyAI supports multiple Indian languages:
- **English**: Default language
- **Hindi (हिंदी)**: Full UI and content support
- **Marathi (मराठी)**: Regional language support
- **Gujarati (ગુજરાતી)**: Western India market focus

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Check the [Technical Documentation](TECHNICAL_DOCUMENTATION.md)
- Review the [Deployment Guide](DEPLOYMENT_GUIDE.md)
- Create an issue in the repository

## 🚀 Roadmap

### Upcoming Features
- **WhatsApp Integration**: Automated messaging and lead management
- **Instagram Integration**: Multi-platform social media posting
- **Advanced Analytics**: Detailed performance insights
- **Lead Scoring**: AI-powered prospect qualification
- **Voice Commands**: AI assistant for hands-free operation

### Technical Improvements
- **Real-time Notifications**: WebSocket implementation
- **Advanced Search**: Elasticsearch integration
- **Image Recognition**: Property photo analysis
- **Performance Monitoring**: Advanced observability

---

**PropertyAI** - Empowering Real Estate Professionals with Next-Generation AI Technology

*Built with ❤️ for the Indian Real Estate Market*