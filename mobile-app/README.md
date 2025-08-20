# PropertyAI - World's First Gen AI Property Solution & CRM

A revolutionary mobile-first real estate CRM solution powered by AI, designed specifically for real estate agents with comprehensive branding customization and intelligent automation.

## 🌟 Features

### 🤖 AI-Powered Assistance
- **GROQ Integration**: Lightning-fast AI responses using GROQ's advanced models
- **Smart Property Descriptions**: Generate compelling property listings automatically
- **Market Analysis**: AI-driven market insights and pricing recommendations
- **Client Communication**: Automated follow-ups and personalized messaging
- **Lead Qualification**: Intelligent lead scoring and prioritization

### 🎨 Dynamic Branding System
- **Custom Brand Colors**: Personalized color schemes that reflect throughout the app
- **Logo Integration**: Upload and display your brand logo across all screens
- **Brand Tags**: Customizable tags that define your market positioning
- **Theme Options**: Light/dark theme support with brand consistency
- **Personalized UI**: Every screen adapts to your brand identity

### 📱 Mobile-First Design
- **Responsive Layout**: Optimized for all screen sizes
- **Gesture Navigation**: Intuitive swipe and tap interactions
- **Offline Capability**: Core features work without internet connection
- **Push Notifications**: Real-time alerts for leads, messages, and opportunities
- **Fast Performance**: Optimized for speed and smooth animations

### 🏠 Complete Property Management
- **Property Listings**: Comprehensive property database with rich media
- **Market Analytics**: Real-time market data and trends
- **Virtual Tours**: Integrated virtual tour capabilities
- **Document Management**: Secure storage for contracts and documents

### 👥 Advanced CRM
- **Lead Management**: Complete lead lifecycle tracking
- **Client Relationships**: Detailed client profiles and interaction history
- **Pipeline Management**: Visual sales pipeline with stage tracking
- **Automated Follow-ups**: AI-scheduled follow-up reminders
- **Performance Analytics**: Detailed metrics and reporting

### 🔐 Security & Privacy
- **Secure Authentication**: Multi-factor authentication support
- **Data Encryption**: End-to-end encryption for sensitive data
- **GDPR Compliant**: Full compliance with privacy regulations
- **Secure Storage**: Encrypted local storage for offline data

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn
- Expo CLI
- iOS Simulator (for Mac users) or Android Emulator
- Physical device for testing (optional)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/realestate_ai.git
   cd realestate_ai/mobile-app
   ```

2. Run the setup script:
   ```bash
   # For Windows
   node scripts/setup.js
   
   # For macOS/Linux
   ./start-app.sh
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update the variables as needed

4. Start the development server:
   ```bash
   npm start
   ```

5. Run on your preferred platform:
   ```bash
   # iOS
   npm run ios
   
   # Android
   npm run android
   
   # Web
   npm run web
   ```

### Clean Installation

If you encounter any issues with dependencies or cached files:

```bash
# Clean the project and reinstall dependencies
npm run clean
npm install
```

## Project Structure

```
mobile-app/
├── assets/              # Static assets (images, fonts)
├── scripts/             # Setup and utility scripts
├── src/
│   ├── components/      # Reusable UI components
│   ├── config/          # Configuration files
│   ├── contexts/        # React contexts (Auth, Branding, Network)
│   ├── screens/         # Application screens
│   ├── services/        # API and utility services
│   └── utils/           # Helper functions
├── .env.example         # Example environment variables
├── app.config.js        # Expo configuration
├── App.js               # Main application component
└── package.json         # Dependencies and scripts
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
API_URL=http://localhost:8003
GROQ_API_KEY=your-groq-api-key
ENABLE_PUSH_NOTIFICATIONS=true
ENABLE_OFFLINE_MODE=true
```

## Available Scripts

- `npm start`: Start the Expo development server
- `npm run ios`: Run on iOS simulator
- `npm run android`: Run on Android emulator/device
- `npm run web`: Run in web browser
- `npm run clean`: Clean project dependencies and cache
- `npm run setup`: Run the setup script
- `npm run start:clean`: Clean and restart the project

## Troubleshooting

### Metro Bundler Issues

If you encounter Metro bundler errors:

```bash
# Clear Metro cache
npm start -- --reset-cache
```

### Dependency Issues

```bash
# Clean node_modules and reinstall
npm run clean
npm install
```

### Connection to Backend

Ensure the backend server is running and accessible at the URL specified in your `.env` file.
- Expo CLI
- React Native development environment
- GROQ API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mobile-app
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your GROQ API key and other configurations
   ```

4. **Start the development server**
   ```bash
   npm start
   ```

5. **Run on device/simulator**
   ```bash
   # For iOS
   npm run ios
   
   # For Android
   npm run android
   
   # For Web
   npm run web
   ```

## 🔧 Configuration

### GROQ API Setup
1. Get your API key from [GROQ Console](https://console.groq.com)
2. Add it to your `.env` file:
   ```
   GROQ_API_KEY=your_api_key_here
   ```

### Backend Integration
The app is designed to work with the existing FastAPI backend. Configure the API base URL in your environment:
```
API_BASE_URL=http://127.0.0.1:8003
```

## 📱 App Structure

```
src/
├── components/           # Reusable UI components
│   └── onboarding/      # Agent onboarding flow components
├── contexts/            # React Context providers
│   ├── AuthContext.js   # Authentication state management
│   └── BrandingContext.js # Dynamic branding system
├── navigation/          # App navigation configuration
├── screens/             # Main app screens
│   ├── onboarding/      # Onboarding flow screens
│   ├── DashboardScreen.js
│   ├── PropertiesScreen.js
│   ├── LeadsScreen.js
│   ├── ClientsScreen.js
│   └── AIAssistantScreen.js
├── services/            # External service integrations
│   └── groqService.js   # GROQ AI service integration
└── theme/               # App theming and styles
```

## 🎯 Key Features Deep Dive

### Agent Onboarding Flow
The app features a comprehensive 6-step onboarding process:

1. **Personal Information**: Basic agent details and profile setup
2. **Company Information**: Business details and professional background
3. **Brand Identity**: Custom logo, colors, and brand positioning
4. **Preferences**: Notification settings and workflow preferences
5. **AI Assistant Setup**: Configure AI personality and communication style
6. **Verification**: License verification and system integration

### Dynamic Branding System
- **Real-time Updates**: Brand changes reflect immediately across all screens
- **Color Harmony**: Automatic generation of complementary color schemes
- **Consistent Experience**: Brand elements maintain consistency throughout the app
- **Professional Appearance**: Every agent gets a unique, professional-looking app

### AI Integration
- **Context-Aware Responses**: AI understands real estate context and terminology
- **Personalized Communication**: AI adapts to agent's communication style
- **Multi-Modal Capabilities**: Text, voice, and image processing
- **Learning System**: AI improves responses based on agent feedback

## 🔄 Development Workflow

### Adding New Features
1. Create feature branch from `main`
2. Implement feature with proper testing
3. Update documentation
4. Submit pull request with detailed description

### Code Style
- Use ESLint and Prettier for code formatting
- Follow React Native best practices
- Implement proper error handling
- Add comprehensive comments for complex logic

### Testing
```bash
# Run tests
npm test

# Run E2E tests
npm run test:e2e
```

## 🚀 Deployment

### Building for Production

**iOS:**
```bash
npm run build:ios
```

**Android:**
```bash
npm run build:android
```

**Web:**
```bash
npm run build:web
```

## 📊 Performance Optimization

- **Lazy Loading**: Components load on demand
- **Image Optimization**: Automatic image compression and caching
- **Memory Management**: Efficient memory usage with proper cleanup
- **Network Optimization**: Request batching and caching strategies

## 🔒 Security Considerations

- **API Key Protection**: Environment variables for sensitive data
- **Secure Storage**: Encrypted storage for authentication tokens
- **Input Validation**: Comprehensive input sanitization
- **Network Security**: HTTPS enforcement and certificate pinning

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Contact the development team

## 🚀 Future Roadmap

- **Voice Commands**: Voice-controlled app navigation
- **AR Property Tours**: Augmented reality property viewing
- **Blockchain Integration**: Secure property transactions
- **Advanced Analytics**: Machine learning-powered insights
- **Multi-language Support**: International market support

---

Built with ❤️ for real estate professionals who demand the best technology to grow their business.