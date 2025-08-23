# PropertyAI - Next-Gen AI Real Estate Dashboard

A modern, modular real estate platform with AI-powered content generation, Facebook integration, and multi-language support.

## 🚀 **Features**

### ✅ **Core Functionality**
- **AI Content Generation**: Multi-language real estate listing content
- **Facebook Integration**: OAuth, page management, and automated posting
- **User Management**: JWT authentication with Facebook OAuth support
- **Property Management**: Add, edit, and manage real estate listings
- **Multi-language Support**: English, Hindi, Marathi, Gujarati
- **Onboarding System**: 7-step user onboarding with branding

### ✅ **Technical Features**
- **Modular Architecture**: Clean, maintainable code structure
- **FastAPI Backend**: Modern, fast Python web framework
- **JWT Authentication**: Secure user sessions
- **Demo Mode**: Facebook integration simulation for testing
- **Responsive UI**: Bootstrap-based dashboard

## 🏗️ **Architecture**

```
app/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration and environment settings
├── utils.py               # Shared utilities (JWT, etc.)
├── routers/               # API route handlers
│   ├── auth.py           # Authentication and user management
│   ├── facebook.py       # Facebook OAuth and posting
│   ├── listings.py       # AI content generation
│   ├── properties.py     # Property management
│   ├── user_profile.py   # User onboarding and profiles
│   ├── dashboard.py      # Dashboard statistics
│   ├── crm.py           # CRM functionality
│   └── localization.py   # Multi-language support
└── templates/             # HTML templates
    ├── dashboard_modular.html      # Main dashboard
    └── components/                 # Dashboard components
        ├── dashboard_header.html   # Navigation header
        ├── dashboard_main.html     # Main content area
        ├── dashboard_scripts.html  # JavaScript functionality
        ├── dashboard_styles.html   # CSS styles
        ├── dashboard_welcome.html  # Welcome section
        ├── dashboard_properties.html # Properties section
        ├── dashboard_ai_content.html # AI content generation
        ├── dashboard_facebook.html   # Facebook integration
        ├── dashboard_onboarding.html # User onboarding
        └── dashboard_crm.html      # CRM section
```

## 🚀 **Quick Start**

### 1. **Environment Setup**
```bash
# Clone the repository
git clone <repository-url>
cd realestate_ai

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. **Environment Configuration**
Create a `.env` file:
```env
# Server Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True

# Facebook Integration (Optional - Demo mode works without these)
FB_APP_ID=your-facebook-app-id
FB_APP_SECRET=your-facebook-app-secret

# URL Configuration
NGROK_BASE_URL=https://your-ngrok-url.ngrok-free.app
LOCAL_BASE_URL=http://127.0.0.1:8003
```

### 3. **Start the Server**
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload
```

### 4. **Access the Application**
- **Dashboard**: http://127.0.0.1:8003/dashboard
- **API Docs**: http://127.0.0.1:8003/docs

## 🔧 **Usage**

### **Facebook Integration (Demo Mode)**
1. Navigate to the dashboard
2. Click "Connect Facebook" in the onboarding section
3. Complete the demo OAuth flow
4. Generate AI content for properties
5. Post content to Facebook (simulated in demo mode)

### **AI Content Generation**
1. Select a property from the dropdown
2. Choose languages (English, Hindi, Marathi, Gujarati)
3. Select tone and template
4. Click "Generate Content"
5. Review generated content in language tabs
6. Post to Facebook or copy content

### **User Onboarding**
1. Complete the 7-step onboarding process
2. Provide company information and branding
3. Set language preferences
4. Connect Facebook account
5. Save profile for future use

## 📁 **File Structure**

### **Core Files**
- `app/main.py` - Main FastAPI application
- `app/config.py` - Configuration management
- `app/utils.py` - Shared utilities

### **Routers**
- `app/routers/auth.py` - Authentication (365 lines)
- `app/routers/facebook.py` - Facebook integration (400 lines)
- `app/routers/listings.py` - AI content generation (232 lines)
- `app/routers/properties.py` - Property management (116 lines)
- `app/routers/user_profile.py` - User profiles (146 lines)
- `app/routers/dashboard.py` - Dashboard stats (59 lines)
- `app/routers/crm.py` - CRM functionality (559 lines)
- `app/routers/localization.py` - Localization (433 lines)

### **Templates**
- `templates/dashboard_modular.html` - Main dashboard template
- `templates/components/` - Modular dashboard components

## 🔒 **Security Features**

- **JWT Authentication**: Secure token-based authentication
- **OAuth State Verification**: CSRF protection for Facebook OAuth
- **Input Validation**: Pydantic models for data validation
- **Environment Variables**: Secure configuration management

## 🌐 **Multi-language Support**

- **English**: Primary language with full feature support
- **Hindi**: हिंदी content generation and display
- **Marathi**: मराठी content generation and display
- **Gujarati**: ગુજરાતી content generation and display

## 📊 **API Endpoints**

### **Authentication**
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration

### **Facebook Integration**
- `GET /api/v1/facebook/oauth` - Start OAuth flow
- `GET /api/v1/facebook/callback` - OAuth callback
- `POST /api/v1/facebook/post` - Post to Facebook
- `GET /api/v1/facebook/pages` - Get user's pages
- `GET /api/v1/facebook/config` - Get integration status

### **Content Generation**
- `POST /api/v1/listings/generate` - Generate AI content

### **Properties**
- `GET /api/v1/properties` - List properties
- `POST /api/v1/properties` - Add property

### **User Profile**
- `POST /api/v1/user/profile` - Save user profile
- `GET /api/v1/user/profile/{user_id}` - Get user profile

## 🧪 **Testing**

### **Demo Mode**
The system includes a comprehensive demo mode that simulates:
- Facebook OAuth flow
- Content generation
- Facebook posting
- User management

### **Manual Testing**
1. Start the server
2. Navigate to dashboard
3. Complete Facebook OAuth (demo mode)
4. Generate AI content
5. Post to Facebook
6. Verify all functionality

## 🚀 **Deployment**

### **Production Setup**
1. Set `DEBUG=False` in environment
2. Configure real Facebook app credentials
3. Set up proper database (currently using in-memory storage)
4. Configure production URLs
5. Set up SSL/TLS certificates

### **Docker Support**
```bash
# Build and run with Docker
docker build -t propertyai .
docker run -p 8003:8003 propertyai
```

## 📝 **Development Notes**

### **Code Quality**
- All files under 800 lines (as requested)
- Modular architecture for easy maintenance
- Comprehensive error handling
- Detailed logging throughout

### **Performance**
- Async/await for I/O operations
- Efficient database queries (when implemented)
- Optimized template rendering

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all tests pass
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License.

## 🆘 **Support**

For support and questions:
- Check the documentation
- Review the code comments
- Test in demo mode first
- Contact the development team

---

**PropertyAI** - Transforming Real Estate with AI 🏠✨