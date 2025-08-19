import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { AgentProvider } from './contexts/AgentContext';
import { BrandingProvider } from './contexts/BrandingContext';
import { AuthProvider } from './contexts/AuthContext';

// Components
import Navbar from './components/layout/Navbar';
import MobileNav from './components/layout/MobileNav';
import LoadingSpinner from './components/common/LoadingSpinner';
import ToastContainer from './components/common/ToastContainer';

// Pages
import LandingPage from './pages/LandingPage';
import AgentOnboarding from './pages/AgentOnboarding';
import AgentDashboard from './pages/AgentDashboard';
import AgentProfile from './pages/AgentProfile';
import BrandingCustomization from './pages/BrandingCustomization';
import PropertyManagement from './pages/PropertyManagement';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

// Styles
import './styles/globals.css';
import './styles/components.css';
import './styles/responsive.css';

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    // Check if device is mobile
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);

    // Simulate loading time
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1500);

    return () => {
      window.removeEventListener('resize', checkMobile);
      clearTimeout(timer);
    };
  }, []);

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <ThemeProvider>
      <BrandingProvider>
        <AuthProvider>
          <AgentProvider>
            <Router>
              <div className="app">
                {/* Desktop Navigation */}
                <div className="hidden md:block">
                  <Navbar />
                </div>

                {/* Mobile Navigation */}
                {isMobile && <MobileNav />}

                {/* Main Content */}
                <main className="main-content">
                  <Routes>
                    {/* Public Routes */}
                    <Route path="/" element={<LandingPage />} />
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />
                    
                    {/* Protected Routes */}
                    <Route path="/onboarding" element={<AgentOnboarding />} />
                    <Route path="/dashboard" element={<AgentDashboard />} />
                    <Route path="/profile" element={<AgentProfile />} />
                    <Route path="/branding" element={<BrandingCustomization />} />
                    <Route path="/properties" element={<PropertyManagement />} />
                    
                    {/* Fallback */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </main>

                {/* Toast Notifications */}
                <ToastContainer />
              </div>
            </Router>
          </AgentProvider>
        </AuthProvider>
      </BrandingProvider>
    </ThemeProvider>
  );
}

export default App;