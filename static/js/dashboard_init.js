// Dashboard Initialization - Handles startup and section discovery
// This file is responsible for finding and initializing all dashboard sections

// Configuration
const DASHBOARD_CONFIG = {
    requiredSections: ['welcome', 'ai-content', 'facebook', 'properties', 'onboarding', 'crm', 'analytics'],
    maxInitAttempts: 10,
    retryDelay: 300,
    initDelay: 500
};

// Section discovery and validation
function discoverSections() {
    console.log('🔍 Discovering dashboard sections...');
    
    const foundSections = {};
    const missingSections = [];
    
    DASHBOARD_CONFIG.requiredSections.forEach(sectionName => {
        const sectionId = sectionName + '-section';
        const section = document.getElementById(sectionId);
        
        if (section) {
            foundSections[sectionName] = section;
            console.log('✅ Found section:', sectionId);
        } else {
            missingSections.push(sectionName);
            console.log('❌ Missing section:', sectionId);
        }
    });
    
    return { foundSections, missingSections };
}

// Initialize dashboard with retry mechanism
function initializeDashboard() {
    console.log('🚀 Initializing PropertyAI Dashboard...');
    
    const { foundSections, missingSections } = discoverSections();
    
    if (missingSections.length === 0) {
        console.log('✅ All required sections found!');
        completeInitialization(foundSections);
        return true;
    } else {
        console.warn('⚠️ Missing sections:', missingSections.join(', '));
        console.log('🔄 Will retry initialization...');
        return false;
    }
}

// Complete the initialization process
function completeInitialization(sections) {
    console.log('🔧 Completing dashboard initialization...');
    
    // Store sections in global state
    if (window.dashboardCore && window.dashboardCore.state) {
        window.dashboardCore.state.sections = sections;
        window.dashboardCore.state.isInitialized = true;
    }
    
    // Show welcome section by default
    if (window.dashboardCore && window.dashboardCore.showSection) {
        window.dashboardCore.showSection('welcome');
    }
    
    // Initialize stats
    if (typeof loadDashboardStats === 'function') {
        loadDashboardStats();
    }
    
    // Initialize user profile
    if (typeof loadUserProfile === 'function') {
        loadUserProfile();
    }
    
    console.log('✅ Dashboard initialization completed successfully');
}

// Retry initialization with exponential backoff
function retryInitialization(attempts = 0) {
    if (attempts >= DASHBOARD_CONFIG.maxInitAttempts) {
        console.error('❌ Dashboard initialization failed after all attempts');
        return;
    }
    
    console.log(`🔄 Retry attempt ${attempts + 1}/${DASHBOARD_CONFIG.maxInitAttempts}`);
    
    setTimeout(() => {
        if (initializeDashboard()) {
            console.log('✅ Dashboard initialized on retry attempt', attempts + 1);
        } else {
            retryInitialization(attempts + 1);
        }
    }, DASHBOARD_CONFIG.retryDelay * (attempts + 1));
}

// Main initialization function
function startDashboardInitialization() {
    console.log('🎯 Starting dashboard initialization...');
    
    // Wait for DOM to be fully ready
    setTimeout(() => {
        if (initializeDashboard()) {
            console.log('✅ Dashboard initialized successfully');
        } else {
            console.log('🔄 Starting retry mechanism...');
            retryInitialization();
        }
    }, DASHBOARD_CONFIG.initDelay);
}

// Export for use in main template
window.dashboardInit = {
    initializeDashboard,
    startDashboardInitialization,
    discoverSections
};
