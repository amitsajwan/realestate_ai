# 🏠 Property Forms Consolidation

A comprehensive property management system with unified forms, AI integration, and multi-language support.

## 🚀 **Quick Start**

### **Prerequisites**
- Node.js 18+
- Python 3.11+
- MongoDB
- npm/yarn

### **Installation**

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd property-forms-consolidation
   ```

2. **Install Frontend Dependencies**
   ```bash
   cd frontend
   npm install
   ```

3. **Install Backend Dependencies**
   ```bash
   cd ../backend
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

4. **Set up Environment Variables**
   ```bash
   # Copy environment files
   cp .env.example .env.local
   cp backend/.env.example backend/.env
   
   # Edit the files with your configuration
   ```

5. **Start the Development Servers**
   ```bash
   # Terminal 1: Backend
   cd backend
   python -m uvicorn app.main:app --reload
   
   # Terminal 2: Frontend
   cd frontend
   npm run dev
   ```

## 🏗️ **Architecture**

### **Frontend (Next.js + React)**
- **Unified Property Form**: Single component supporting multiple variants
- **Feature Flags**: A/B testing and gradual rollout
- **AI Integration**: Smart suggestions and content generation
- **Analytics**: Comprehensive tracking and monitoring
- **TypeScript**: Full type safety

### **Backend (FastAPI + Python)**
- **Unified API**: Consolidated endpoints for all property operations
- **MongoDB**: Document-based storage
- **AI Services**: Content generation and market insights
- **Migration Utilities**: Backward compatibility and data migration
- **Comprehensive Testing**: Unit, integration, and performance tests

## 📋 **Features**

### **Form Variants**
- **Simple Form**: Basic property creation
- **Wizard Form**: Step-by-step guided flow
- **AI-First Form**: AI-assisted generation

### **AI Integration**
- Smart content suggestions
- Market insights and analysis
- Quality scoring
- Multi-language support

### **Analytics & Monitoring**
- Real-time performance tracking
- User behavior analytics
- Error monitoring
- A/B testing support

## 🧪 **Testing**

### **Frontend Tests**
```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

### **Backend Tests**
```bash
cd backend

# Run all tests
pytest

# Run tests with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_unified_properties.py

# Run async tests
pytest -m asyncio
```

## 🚀 **Deployment**

### **Environment Configuration**
```bash
# Production environment variables
NEXT_PUBLIC_USE_UNIFIED_FORM=true
NEXT_PUBLIC_ENABLE_AI_FEATURES=true
NEXT_PUBLIC_ENABLE_MARKET_INSIGHTS=true
NEXT_PUBLIC_ROLLOUT_PERCENTAGE=100
```

### **Feature Flags**
- **USE_UNIFIED_FORM**: Enable/disable unified form
- **ENABLE_AI_FEATURES**: Enable/disable AI features
- **ENABLE_MARKET_INSIGHTS**: Enable/disable market insights
- **ROLLOUT_PERCENTAGE**: A/B testing percentage (0-100)

## 📊 **Performance Metrics**

### **Target Metrics**
- **Form Load Time**: <2 seconds
- **Bundle Size**: <500KB for form components
- **API Response**: <500ms
- **Test Coverage**: >80%

### **Monitoring**
- Real-time error tracking
- Performance monitoring
- User analytics
- A/B testing results

## 🔧 **Development**

### **Code Structure**
```
frontend/
├── components/property/          # Property form components
├── hooks/                       # Custom React hooks
├── utils/                       # Utility functions
├── types/                       # TypeScript definitions
└── __tests__/                   # Test files

backend/
├── app/
│   ├── api/v1/endpoints/        # API endpoints
│   ├── services/                # Business logic
│   ├── schemas/                 # Data models
│   └── utils/                   # Utilities
└── tests/                       # Test files
```

### **Adding New Features**
1. Create feature branch
2. Implement feature with tests
3. Update documentation
4. Submit pull request

## 🐛 **Troubleshooting**

### **Common Issues**

1. **Import Errors**
   ```bash
   # Check import paths
   # Use relative imports for local files
   ```

2. **Test Failures**
   ```bash
   # Clear Jest cache
   npm test -- --clearCache
   
   # Check test environment
   npm test -- --verbose
   ```

3. **API Connection Issues**
   ```bash
   # Check backend is running
   curl http://localhost:8000/health
   
   # Check environment variables
   echo $NEXT_PUBLIC_API_BASE_URL
   ```

## 📚 **Documentation**

- [Technical Analysis](TECHNICAL_ANALYSIS_DETAILED.md)
- [Testing Plan](QA_TESTING_PLAN.md)
- [UX Design Review](UX_DESIGN_REVIEW.md)
- [Implementation Guide](STEP_BY_STEP_IMPLEMENTATION.md)

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License.

## 🆘 **Support**

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting guide

---

**Built with ❤️ by the Property Forms Consolidation Team**