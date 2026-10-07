# 🏠 Avasetu - Next.js Frontend

A modern, AI-powered real estate platform built with Next.js 14, TypeScript, and Tailwind CSS.

## ✨ Features

### ✅ **Production Ready**
- **Real Backend Integration**: Full API integration with FastAPI backend
- **Authentication**: JWT-based authentication with automatic token refresh
- **Type Safety**: Complete TypeScript implementation with proper interfaces
- **Error Handling**: Comprehensive error boundaries and user feedback
- **Form Validation**: Zod schemas with type-safe validation
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Performance**: React.memo optimization and code splitting

### 🚀 **Core Features**
- **Dashboard**: Real-time statistics from MongoDB
- **Property Management**: Create, view, and manage properties
- **AI Integration**: AI-powered property suggestions and content generation
- **Facebook Integration**: OAuth and posting capabilities
- **User Profiles**: Complete user profile management
- **Analytics**: Performance tracking and insights
- **CRM**: Lead management and customer relationship tools

### 🔧 **Technical Stack**
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom design system
- **Forms**: React Hook Form with Zod validation
- **Animations**: Framer Motion
- **Icons**: Heroicons
- **Notifications**: React Hot Toast
- **State Management**: Zustand (ready for implementation)

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn
- FastAPI backend running on localhost:8000

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd realestate_ai/nextjs-app
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env.local
   
   # Edit .env.local with your configuration
   NEXT_PUBLIC_APP_NAME=Avasetu
   NEXT_PUBLIC_APP_VERSION=2.0.0
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

5. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## 📁 Project Structure

```
nextjs-app/
├── app/                    # Next.js App Router
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Dashboard page
│   ├── login/             # Authentication pages
│   └── onboarding/        # Onboarding flow
├── components/            # Reusable components
│   ├── DashboardStats.tsx # Dashboard statistics
│   ├── PropertyForm.tsx   # Property creation form
│   ├── ErrorBoundary.tsx  # Error handling
│   └── LoadingSpinner.tsx # Loading states
├── lib/                   # Utilities and services
│   ├── api.ts            # API service layer
│   ├── auth.ts           # Authentication management
│   ├── validation.ts     # Form validation schemas
│   └── env.ts            # Environment configuration
└── types/                # TypeScript type definitions
```

## 🔗 API Integration

### ✅ **Working Endpoints**
- **Authentication**: `/api/v1/auth/login`, `/api/v1/auth/register`
- **Dashboard**: `/api/v1/dashboard/stats` (real MongoDB data)
- **Properties**: `/api/v1/properties/` (create, read, delete)
- **AI**: `/api/v1/property/ai_suggest` (AI suggestions)
- **User Profiles**: `/api/v1/user/profile/*`
- **Facebook**: `/api/v1/facebook/*` (OAuth and posting)
- **Health**: `/health` (backend status)

### 🔄 **Mock Endpoints** (Development)
- **Leads**: CRM functionality with mock data
- **Analytics**: Dashboard analytics with mock data
- **File Upload**: Image upload simulation
- **Onboarding**: Profile updates for onboarding flow

## 🔐 Authentication

### Features
- **JWT Tokens**: Secure token-based authentication
- **Auto Refresh**: Automatic token refresh before expiration
- **Session Management**: Persistent login sessions
- **Security**: Token expiration handling and auto-logout

### Usage
```typescript
import { authManager } from '@/lib/auth'

// Login
await authManager.login(email, password)

// Check authentication status
const state = authManager.getState()

// Logout
authManager.logout()
```

## 🎨 Design System

### Components
- **Glass Cards**: Modern glassmorphism design
- **Buttons**: Primary, secondary, and outline variants
- **Forms**: Validated input fields with error states
- **Loading States**: Spinners and skeleton loaders
- **Error Boundaries**: Graceful error handling

### Colors
- **Primary**: Blue gradient (`from-blue-500 to-blue-600`)
- **Secondary**: Orange gradient (`from-secondary-500 to-secondary-600`)
- **Success**: Green (`green-500`)
- **Error**: Red (`red-500`)
- **Background**: Dark gradient (`from-slate-900 via-purple-900 to-slate-900`)

## 🧪 Testing

### Current Status
- ✅ **TypeScript**: Full type checking
- ✅ **Build**: Successful production builds
- ✅ **Linting**: ESLint configuration
- ⏳ **Unit Tests**: Ready for implementation
- ⏳ **Integration Tests**: Ready for implementation
- ⏳ **E2E Tests**: Ready for implementation

### Running Tests
```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Build
npm run build
```

## 🚀 Deployment

### Vercel (Recommended)
1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

### Manual Deployment
```bash
# Build for production
npm run build

# Start production server
npm start
```

## 🔧 Development

### Available Scripts
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript check
```

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_APP_NAME` | Application name | ✅ |
| `NEXT_PUBLIC_APP_VERSION` | Application version | ✅ |
| `NEXT_PUBLIC_API_BASE_URL` | Backend API URL | ✅ |
| `NEXT_PUBLIC_FACEBOOK_APP_ID` | Facebook App ID | ❌ |
| `NEXT_PUBLIC_GOOGLE_ANALYTICS_ID` | Google Analytics ID | ❌ |

## 📊 Performance

### Optimizations
- **Code Splitting**: Automatic route-based splitting
- **Image Optimization**: Next.js Image component
- **Bundle Analysis**: Ready for webpack-bundle-analyzer
- **Caching**: Static generation and ISR
- **React.memo**: Component memoization

### Metrics
- **First Load JS**: ~156 kB
- **Bundle Size**: Optimized with tree shaking
- **Build Time**: Fast incremental builds
- **Runtime Performance**: Optimized React rendering

## 🔒 Security

### Implemented
- **JWT Authentication**: Secure token management
- **Token Refresh**: Automatic token renewal
- **Error Boundaries**: Graceful error handling
- **Input Validation**: Zod schema validation
- **CORS**: Proper cross-origin handling

### Recommendations
- **HTTPS**: Use HTTPS in production
- **Rate Limiting**: Implement API rate limiting
- **CSRF Protection**: Add CSRF tokens
- **Content Security Policy**: Implement CSP headers

## 🤝 Contributing

### Development Workflow
1. Create feature branch from `main`
2. Make changes with proper TypeScript types
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

### Code Standards
- **TypeScript**: Strict type checking enabled
- **ESLint**: Follow linting rules
- **Prettier**: Consistent code formatting
- **Conventional Commits**: Use conventional commit messages

## 📈 Roadmap

### Phase 1: Core Features ✅
- [x] Authentication system
- [x] Dashboard with real data
- [x] Property management
- [x] AI integration
- [x] Error handling

### Phase 2: Enhanced Features 🚧
- [ ] Real-time notifications
- [ ] Advanced analytics
- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Advanced AI features

### Phase 3: Enterprise Features 📋
- [ ] Team collaboration
- [ ] Advanced reporting
- [ ] API rate limiting
- [ ] Advanced security features
- [ ] White-label solutions

## 🐛 Troubleshooting

### Common Issues

**Build Errors**
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run build
```

**API Connection Issues**
```bash
# Check backend is running
curl http://localhost:8000/health

# Verify environment variables
echo $NEXT_PUBLIC_API_BASE_URL
```

**Authentication Issues**
```bash
# Clear browser storage
localStorage.clear()

# Check token validity
# Open browser dev tools and check Application > Local Storage
```

## 📞 Support

### Getting Help
- **Documentation**: Check this README and inline code comments
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub discussions for questions
- **Email**: Contact the development team

### Resources
- [Next.js Documentation](https://nextjs.org/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [React Hook Form](https://react-hook-form.com)

---

**Avasetu** - Building the future of real estate with AI 🚀
