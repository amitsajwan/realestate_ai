# 🌍 World Glass Gen AI Property CRM

A world-class, AI-powered Property CRM solution with intelligent agent onboarding, dynamic branding, and mobile-first design.

## ✨ Features

### 🤖 AI-Powered Onboarding
- **GROQ AI Integration**: Uses GROQ API for intelligent branding suggestions
- **Personalized CRM Strategy**: AI-generated recommendations based on agent profile
- **Smart Content Suggestions**: Automated marketing content ideas
- **Property Insights**: AI-powered market analysis and recommendations

### 🎨 Dynamic Branding System
- **Custom Color Schemes**: Primary, secondary, accent, text, and background colors
- **Logo Management**: Upload and manage brand logos
- **Brand Guidelines**: Customizable branding rules and preferences
- **Real-time UI Updates**: Branding changes reflect immediately in the interface

### 📱 Mobile-First Design
- **Responsive Interface**: Optimized for all device sizes
- **Touch-Friendly**: Designed for mobile and tablet use
- **Modern UX**: Smooth animations and intuitive navigation
- **Progressive Web App**: Fast loading and offline capabilities

### 📊 Smart CRM Features
- **Lead Management**: Intelligent lead scoring and nurturing
- **Client Segmentation**: AI-powered client categorization
- **Automation**: Automated follow-up sequences and notifications
- **Performance Analytics**: Comprehensive reporting and insights

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- GROQ API Key

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd world-glass-gen-ai-property-crm
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your GROQ_API_KEY
   ```

4. **Initialize database**
   ```bash
   python -c "from app.dependencies import init_db; init_db()"
   ```

5. **Run the backend**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Open in browser**
   ```
   http://localhost:5173
   ```

## 🏗️ Architecture

### Backend Structure
```
app/
├── config.py              # Configuration and settings
├── main.py               # FastAPI application entry point
├── dependencies.py       # Database and service dependencies
├── models/
│   └── agent.py         # Agent data model
├── services/
│   ├── ai_service.py    # GROQ AI integration
│   └── agent_service.py # Agent business logic
└── routes/
    └── agent_routes.py  # API endpoints
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/
│   │   └── AgentOnboarding.jsx  # Main onboarding component
│   ├── App.jsx                   # Root application component
│   └── main.jsx                  # Application entry point
├── package.json                  # Dependencies and scripts
└── tailwind.config.js           # Tailwind CSS configuration
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional
DATABASE_URL=sqlite:///./property_crm.db
SECRET_KEY=your_secret_key_here
DEBUG=false
```

### AI Settings
```python
# app/config.py
GROQ_MODEL = "llama3-8b-8192"  # GROQ model to use
MAX_TOKENS = 4096               # Maximum tokens per request
TEMPERATURE = 0.7               # AI creativity level
```

## 📱 Agent Onboarding Flow

### 1. Profile Setup
- Basic information (name, email, phone)
- Company details and license information
- Experience and bio

### 2. Branding Configuration
- Brand name and tagline
- Logo upload and management
- Custom color scheme selection
- AI-powered branding suggestions

### 3. Specialties Definition
- Property type specializations
- Service area selection
- Price range preferences
- Target market identification

### 4. CRM Setup
- AI communication preferences
- Notification settings
- Automation preferences
- Lead management strategy

### 5. Verification
- Document upload (license, ID)
- Account verification process
- Compliance checks

## 🎨 Branding System

### Color Scheme
- **Primary Color**: Main brand color for buttons and highlights
- **Secondary Color**: Supporting color for secondary elements
- **Accent Color**: Attention-grabbing color for CTAs
- **Text Color**: Primary text color for readability
- **Background Color**: Main background color

### Dynamic UI Updates
The branding system automatically applies colors to:
- Buttons and interactive elements
- Headers and navigation
- Forms and input fields
- Progress indicators
- Success/error messages

## 🔌 API Endpoints

### Agent Management
- `POST /api/agents/onboarding/start` - Start onboarding process
- `POST /api/agents/onboarding/{agent_id}/step/{step}` - Complete onboarding step
- `GET /api/agents/onboarding/{agent_id}/progress` - Get onboarding progress
- `PUT /api/agents/{agent_id}/branding` - Update agent branding
- `GET /api/agents/{agent_id}/branding` - Get agent branding
- `POST /api/agents/{agent_id}/upload-logo` - Upload agent logo
- `POST /api/agents/{agent_id}/upload-documents` - Upload verification documents
- `GET /api/agents/{agent_id}/ai-suggestions` - Get AI-powered suggestions
- `GET /api/agents/{agent_id}/dashboard` - Get agent dashboard

## 🤖 AI Integration

### GROQ AI Features
- **Branding Suggestions**: Intelligent brand name and tagline recommendations
- **CRM Strategy**: Personalized customer relationship management strategies
- **Content Generation**: Marketing content ideas and suggestions
- **Property Insights**: Market analysis and pricing recommendations

### AI Prompts
The system uses carefully crafted prompts to:
- Analyze agent profiles and preferences
- Generate relevant branding suggestions
- Create personalized CRM strategies
- Provide market insights and recommendations

## 📱 Mobile-First Design

### Responsive Features
- **Grid Layouts**: Adaptive grid systems for different screen sizes
- **Touch Targets**: Appropriately sized buttons and interactive elements
- **Gesture Support**: Swipe and touch-friendly navigation
- **Performance**: Optimized for mobile network conditions

### Design Principles
- **Accessibility**: WCAG compliant design
- **Usability**: Intuitive navigation and clear visual hierarchy
- **Performance**: Fast loading and smooth animations
- **Consistency**: Unified design language across all components

## 🧪 Testing

### Backend Testing
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_agent_service.py

# Run with coverage
python -m pytest --cov=app
```

### Frontend Testing
```bash
cd frontend

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage
```

## 🚀 Deployment

### Backend Deployment
```bash
# Production build
pip install -r requirements.txt

# Run with production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend Deployment
```bash
cd frontend

# Build for production
npm run build

# Deploy dist/ folder to your hosting service
```

## 🔒 Security

### Authentication & Authorization
- JWT-based authentication
- Role-based access control
- Secure password handling
- API rate limiting

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection

## 📈 Performance

### Backend Optimization
- Database query optimization
- Caching strategies
- Async/await patterns
- Connection pooling

### Frontend Optimization
- Code splitting and lazy loading
- Image optimization
- Bundle size optimization
- Progressive enhancement

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🔮 Roadmap

### Phase 1: Core Platform ✅
- [x] Agent onboarding system
- [x] Dynamic branding
- [x] Basic CRM functionality
- [x] AI integration

### Phase 2: Advanced Features 🚧
- [ ] Property management system
- [ ] Lead scoring and automation
- [ ] Advanced analytics dashboard
- [ ] Mobile app development

### Phase 3: Enterprise Features 📋
- [ ] Multi-tenant architecture
- [ ] Advanced reporting
- [ ] Integration APIs
- [ ] White-label solutions

---

**Built with ❤️ by the World Glass Gen AI Team**
