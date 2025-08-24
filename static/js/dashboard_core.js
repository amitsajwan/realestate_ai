// Dashboard Core JavaScript - Core functionality only
// This file contains the essential dashboard functions without initialization conflicts

// Global state
let dashboardState = {
    currentSection: 'welcome',
    sections: {},
    userProfile: null,
    isInitialized: false
};

// Core section management
function showSection(sectionName) {
    console.log('🎯 showSection called with:', sectionName);
    
    // Update state
    dashboardState.currentSection = sectionName;
    
    // Hide all sections
    const allSections = document.querySelectorAll('.dashboard-section');
    allSections.forEach(section => {
        section.style.display = 'none';
        section.style.visibility = 'hidden';
        section.style.opacity = '0';
    });
    
    // Show target section
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.style.display = 'block';
        targetSection.style.visibility = 'visible';
        targetSection.style.opacity = '1';
        console.log('✅ Section displayed:', sectionName);
        
        // Load section-specific data
        loadSectionData(sectionName);
        
        // Update navigation
        updateNavigationActiveState(sectionName);
    } else {
        console.error('❌ Section not found:', sectionName + '-section');
    }
}

// Navigation management
function updateNavigationActiveState(sectionName) {
    // Update main navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    const clickedLink = document.querySelector(`[onclick*="showSection('${sectionName}')"]`);
    if (clickedLink) {
        clickedLink.classList.add('active');
    }
    
    // Update Next-Gen bottom navigation
    document.querySelectorAll('.nextgen-nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const nextgenNavItem = document.querySelector(`.nextgen-nav-item[onclick*="${sectionName}"]`);
    if (nextgenNavItem) {
        nextgenNavItem.classList.add('active');
    }
}

// Section data loading
function loadSectionData(sectionName) {
    console.log('📂 Loading data for section:', sectionName);
    
    try {
        switch(sectionName) {
            case 'welcome':
                // Welcome section data is already loaded
                break;
            case 'ai-content':
                if (typeof loadFacebookPages === 'function') loadFacebookPages();
                if (typeof loadUserProperties === 'function') loadUserProperties();
                break;
            case 'facebook':
                if (typeof loadFacebookStatus === 'function') loadFacebookStatus();
                if (typeof loadFacebookPages === 'function') loadFacebookPages();
                break;
            case 'properties':
                if (typeof loadUserProperties === 'function') loadUserProperties();
                break;
            case 'onboarding':
                if (typeof showOnboardingSection === 'function') {
                    showOnboardingSection();
                } else {
                    console.warn('⚠️ showOnboardingSection function not found');
                }
                break;
            default:
                console.log('⚠️ No specific data loading for section:', sectionName);
        }
    } catch (error) {
        console.error('❌ Error loading data for section', sectionName + ':', error);
    }
}

// Utility functions - showAlert is defined in dashboard_scripts.html

// Export functions for use in other files
window.dashboardCore = {
    showSection,
    updateNavigationActiveState,
    loadSectionData,
    state: dashboardState
};
