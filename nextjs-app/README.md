# PropertyAI - Next.js Frontend

A modern, React-based frontend for the PropertyAI real estate platform, built with Next.js 14, TypeScript, and Tailwind CSS.

## 🚀 Features

- **Modern UI/UX**: Glassmorphism design with smooth animations
- **Real-time Data**: Connected to your existing MongoDB backend
- **AI Integration**: Property form auto-fill with AI suggestions
- **Responsive Design**: Works perfectly on all devices
- **TypeScript**: Full type safety and better developer experience
- **Component-based**: Modular, reusable components

## 📋 Prerequisites

- Node.js 18+ 
- Your existing FastAPI backend running on `localhost:8000`
- MongoDB database with your real estate data

## 🛠️ Installation

1. **Navigate to the Next.js app directory:**
   ```bash
   cd nextjs-app
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser:**
   Navigate to `http://localhost:3000`

## 🔧 Configuration

The app is configured to proxy API requests to your FastAPI backend:

- **API Proxy**: All `/api/*` requests are forwarded to `http://localhost:8000/api/*`
- **MongoDB Integration**: Uses your existing `realestate_crm` database
- **Environment**: Development mode with hot reloading

## 📁 Project Structure

```
nextjs-app/
├── app/                    # Next.js 14 app directory
│   ├── globals.css        # Global styles with Tailwind
│   ├── layout.tsx         # Root layout component
│   └── page.tsx           # Main dashboard page
├── components/            # React components
│   ├── DashboardStats.tsx # Dashboard statistics
│   ├── PropertyForm.tsx   # Property addition form
│   ├── AIContentGenerator.tsx # AI content generation
│   ├── Analytics.tsx      # Analytics dashboard
│   ├── CRM.tsx           # Customer relationship management
│   ├── FacebookIntegration.tsx # Facebook integration
│   └── ProfileSettings.tsx # Profile management
├── package.json           # Dependencies and scripts
├── tailwind.config.js     # Tailwind CSS configuration
├── tsconfig.json          # TypeScript configuration
└── next.config.js         # Next.js configuration
```

## 🎨 Design System

### Colors
- **Primary**: Blue gradient (`#2563eb` to `#1d4ed8`)
- **Secondary**: Orange (`#f59e0b`)
- **Success**: Green (`#10b981`)
- **Background**: Dark gradient with glassmorphism

### Components
- **Glass Cards**: Semi-transparent cards with backdrop blur
- **Buttons**: Primary, secondary, and outline variants
- **Forms**: Consistent input styling with focus states
- **Animations**: Smooth transitions using Framer Motion

## 🔌 API Integration

The frontend connects to your existing FastAPI backend:

### Available Endpoints
- `GET /api/v1/dashboard/stats` - Dashboard statistics
- `POST /api/v1/property/ai_suggest` - AI property suggestions
- `GET /health` - Health check

### Data Flow
1. **Dashboard Stats**: Real-time data from MongoDB
2. **Property Form**: AI-powered auto-fill functionality
3. **Content Generation**: AI-assisted content creation

## 🚀 Deployment

### Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm start
```

### Environment Variables
Create a `.env.local` file:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🎯 Key Features

### 1. Dashboard Overview
- Real-time statistics from MongoDB
- Setup progress visualization
- Quick action buttons

### 2. Property Management
- Add new properties with AI assistance
- Auto-fill forms with AI-generated content
- Form validation and error handling

### 3. AI Content Generation
- Generate property descriptions
- Multiple content styles (Professional, Casual, Luxury)
- Copy-to-clipboard functionality

### 4. Analytics & CRM
- Lead management interface
- Performance tracking
- Customer relationship tools

### 5. Facebook Integration
- Social media posting
- Page management
- Content scheduling

## 🔄 Migration Benefits

### From FastAPI/HTML Templates to Next.js:

1. **Better Performance**
   - Server-side rendering
   - Optimized bundle sizes
   - Faster page loads

2. **Enhanced UX**
   - Smooth client-side navigation
   - Real-time updates
   - Better mobile experience

3. **Developer Experience**
   - TypeScript support
   - Hot reloading
   - Component reusability

4. **Scalability**
   - Modular architecture
   - Easy to extend
   - Better code organization

## 🐛 Troubleshooting

### Common Issues

1. **API Connection Error**
   - Ensure your FastAPI backend is running on port 8000
   - Check the proxy configuration in `next.config.js`

2. **MongoDB Connection**
   - Verify MongoDB is running on `localhost:27017`
   - Check your database connection in the backend

3. **Build Errors**
   - Clear `.next` folder: `rm -rf .next`
   - Reinstall dependencies: `npm install`

## 📞 Support

For issues or questions:
1. Check the FastAPI backend logs
2. Verify MongoDB connection
3. Review browser console for errors

## 🎉 Success!

Your PropertyAI application now has a modern, responsive Next.js frontend that seamlessly integrates with your existing MongoDB backend and AI functionality!
