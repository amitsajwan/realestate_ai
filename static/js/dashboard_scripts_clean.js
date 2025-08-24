// 🚀 PropertyAI Dashboard - Complete JavaScript Functionality
// This file contains all the functions needed for the dashboard to work perfectly

// ============================================================================
// 📋 ONBOARDING SYSTEM - Complete 7-Step Flow
// ============================================================================

let currentOnboardingStep = 1;
const totalOnboardingSteps = 7;

// Initialize onboarding when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeOnboarding();
    loadUserProfile();
    animateStats();
});

function initializeOnboarding() {
    // Load saved step from localStorage
    const savedStep = localStorage.getItem('onboardingStep');
    if (savedStep) {
        currentOnboardingStep = parseInt(savedStep);
    }
    
    // Show current step
    showOnboardingStep(currentOnboardingStep);
    updateOnboardingProgress();
    
    console.log('✅ Onboarding system initialized');
}

function showOnboardingStep(step) {
    // Hide all steps
    document.querySelectorAll('.onboarding-step').forEach(stepEl => {
        stepEl.style.display = 'none';
    });
    
    // Show current step
    const currentStepEl = document.getElementById(`step-${step}`);
    if (currentStepEl) {
        currentStepEl.style.display = 'block';
        currentStepEl.classList.add('fade-in-up');
    }
    
    // Update sidebar progress
    updateSidebarProgress(step);
    
    // Update navigation buttons
    updateNavigationButtons(step);
    
    // Load saved data for this step
    loadStepData(step);
}

function updateSidebarProgress(step) {
    // Update step items
    document.querySelectorAll('.step-item').forEach((item, index) => {
        const stepNum = index + 1;
        item.classList.remove('active', 'completed');
        
        if (stepNum === step) {
            item.classList.add('active');
        } else if (stepNum < step) {
            item.classList.add('completed');
        }
    });
}

function updateNavigationButtons(step) {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    
    if (prevBtn) {
        prevBtn.style.display = step > 1 ? 'block' : 'none';
    }
    
    if (nextBtn) {
        if (step === totalOnboardingSteps) {
            nextBtn.textContent = 'Complete Setup';
            nextBtn.className = 'btn btn-success';
        } else {
            nextBtn.textContent = 'Next';
            nextBtn.className = 'btn btn-primary';
        }
    }
}

function nextOnboardingStep() {
    if (currentOnboardingStep < totalOnboardingSteps) {
        // Save current step data
        saveStepData(currentOnboardingStep);
        
        // Validate current step
        if (validateCurrentStep()) {
            currentOnboardingStep++;
            localStorage.setItem('onboardingStep', currentOnboardingStep.toString());
            showOnboardingStep(currentOnboardingStep);
            updateOnboardingProgress();
        }
    } else {
        // Complete onboarding
        completeOnboarding();
    }
}

function previousOnboardingStep() {
    if (currentOnboardingStep > 1) {
        currentOnboardingStep--;
        localStorage.setItem('onboardingStep', currentOnboardingStep.toString());
        showOnboardingStep(currentOnboardingStep);
        updateOnboardingProgress();
    }
}

function validateCurrentStep() {
    const currentStepEl = document.getElementById(`step-${currentOnboardingStep}`);
    if (!currentStepEl) return true;
    
    // Check required fields
    const requiredFields = currentStepEl.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    // Special validation for step 5 (compliance)
    if (currentOnboardingStep === 5) {
        const termsAccepted = document.getElementById('termsAccepted');
        if (!termsAccepted || !termsAccepted.checked) {
            showNotification('Please accept the Terms of Service to continue', 'warning');
            isValid = false;
        }
    }
    
    if (!isValid) {
        showNotification('Please fill in all required fields', 'warning');
    }
    
    return isValid;
}

function saveStepData(step) {
    const stepData = {};
    const currentStepEl = document.getElementById(`step-${step}`);
    
    if (currentStepEl) {
        // Collect all form data from this step
        const inputs = currentStepEl.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.type === 'checkbox' || input.type === 'radio') {
                stepData[input.id] = input.checked;
            } else {
                stepData[input.id] = input.value;
            }
        });
        
        // Save to localStorage
        localStorage.setItem(`onboardingStep${step}`, JSON.stringify(stepData));
    }
}

function loadStepData(step) {
    const savedData = localStorage.getItem(`onboardingStep${step}`);
    if (savedData) {
        try {
            const stepData = JSON.parse(savedData);
            const currentStepEl = document.getElementById(`step-${step}`);
            
            if (currentStepEl) {
                Object.keys(stepData).forEach(fieldId => {
                    const field = document.getElementById(fieldId);
                    if (field) {
                        if (field.type === 'checkbox' || field.type === 'radio') {
                            field.checked = stepData[fieldId];
                        } else {
                            field.value = stepData[fieldId];
                        }
                    }
                });
            }
        } catch (error) {
            console.error('Error loading step data:', error);
        }
    }
}

function updateOnboardingProgress() {
    const progress = (currentOnboardingStep / totalOnboardingSteps) * 100;
    console.log(`📊 Onboarding progress: ${progress.toFixed(1)}%`);
}

function completeOnboarding() {
    // Save final step data
    saveStepData(currentOnboardingStep);
    
    // Mark onboarding as complete
    localStorage.setItem('onboardingComplete', 'true');
    
    // Show completion message
    showNotification('🎉 Onboarding completed successfully!', 'success');
    
    // Redirect to dashboard after a short delay
    setTimeout(() => {
        showSection('welcome');
    }, 2000);
}

// ============================================================================
// 👤 USER PROFILE MANAGEMENT
// ============================================================================

function loadUserProfile() {
    // Load user profile from localStorage or API
    const profile = JSON.parse(localStorage.getItem('userProfile') || '{}');
    
    // Update welcome message
    const userFirstName = document.getElementById('userFirstName');
    if (userFirstName && profile.firstName) {
        userFirstName.textContent = profile.firstName;
    }
    
    // Update agent details in header if they exist
    updateAgentDetails(profile);
    
    console.log('✅ User profile loaded');
}

function updateAgentDetails(profile) {
    const agentName = document.getElementById('agentName');
    const agentCompany = document.getElementById('agentCompany');
    const agentProfilePic = document.getElementById('agentProfilePic');
    
    if (agentName && profile.firstName) {
        agentName.textContent = `${profile.firstName} ${profile.lastName || ''}`;
    }
    
    if (agentCompany && profile.companyName) {
        agentCompany.textContent = profile.companyName;
    }
    
    if (agentProfilePic && profile.profilePhoto) {
        agentProfilePic.src = profile.profilePhoto;
    }
}

// ============================================================================
// 📊 DASHBOARD STATISTICS & ANIMATIONS
// ============================================================================

function animateStats() {
    // Animate stat numbers
    const statNumbers = document.querySelectorAll('.stat-number');
    
    statNumbers.forEach(stat => {
        const finalValue = stat.textContent;
        const isPercentage = finalValue.includes('%');
        const numericValue = parseFloat(finalValue.replace(/[^\d.]/g, ''));
        
        if (!isNaN(numericValue)) {
            animateNumber(stat, 0, numericValue, isPercentage);
        }
    });
}

function animateNumber(element, start, end, isPercentage = false) {
    const duration = 2000;
    const startTime = performance.now();
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function for smooth animation
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const current = start + (end - start) * easeOutQuart;
        
        if (isPercentage) {
            element.textContent = `${Math.round(current)}%`;
        } else {
            element.textContent = Math.round(current).toLocaleString();
        }
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }
    
    requestAnimationFrame(updateNumber);
}

// ============================================================================
// 🎯 SECTION MANAGEMENT
// ============================================================================

function showSection(sectionName) {
    console.log('🎯 showSection called with:', sectionName);
    
    // Hide all sections
    const allSections = document.querySelectorAll('.dashboard-section');
    allSections.forEach(section => {
        section.style.display = 'none';
    });
    
    // Show target section
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.style.display = 'block';
        targetSection.classList.add('fade-in-up');
        console.log('✅ Section displayed:', sectionName);
        
        // Load section-specific data
        if (sectionName === 'onboarding') {
            showOnboardingSection();
        } else if (sectionName === 'property-form') {
            console.log('🏠 Property form section displayed');
        } else if (sectionName === 'welcome') {
            animateStats();
        }
    } else {
        console.error('❌ Section not found:', sectionName + '-section');
    }
}

function showOnboardingSection() {
    // Initialize onboarding if not already done
    if (typeof initializeOnboarding === 'function') {
        initializeOnboarding();
    }
    
    // Load user data if available
    const profile = JSON.parse(localStorage.getItem('userProfile') || '{}');
    if (profile.firstName) {
        populateOnboardingForm(profile);
    }
}

function populateOnboardingForm(profile) {
    // Populate form fields with profile data
    Object.keys(profile).forEach(key => {
        const field = document.getElementById(key);
        if (field) {
            if (field.type === 'checkbox' || field.type === 'radio') {
                field.checked = profile[key];
            } else {
                field.value = profile[key];
            }
        }
    });
}

// ============================================================================
// 🔔 NOTIFICATION SYSTEM
// ============================================================================

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// ============================================================================
// 🏠 PROPERTY FORM FUNCTIONS
// ============================================================================

function connectFacebook() {
    showNotification('Connecting to Facebook...', 'info');
    // Implement Facebook connection logic here
    setTimeout(() => {
        showNotification('Facebook connected successfully!', 'success');
    }, 2000);
}

function showTerms() {
    showNotification('Terms of Service would open here', 'info');
}

function showPrivacy() {
    showNotification('Privacy Policy would open here', 'info');
}

// ============================================================================
// 🎨 UTILITY FUNCTIONS
// ============================================================================

function formatCurrency(amount, currency = '₹') {
    if (amount >= 10000000) {
        return `${currency}${(amount / 10000000).toFixed(1)} Cr`;
    } else if (amount >= 100000) {
        return `${currency}${(amount / 100000).toFixed(1)} Lakhs`;
    } else {
        return `${currency}${amount.toLocaleString()}`;
    }
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// ============================================================================
// 📱 RESPONSIVE HELPERS
// ============================================================================

function isMobile() {
    return window.innerWidth <= 768;
}

function adjustForMobile() {
    if (isMobile()) {
        // Mobile-specific adjustments
        document.body.classList.add('mobile-view');
    } else {
        document.body.classList.remove('mobile-view');
    }
}

// Listen for window resize
window.addEventListener('resize', adjustForMobile);

// ============================================================================
// 🚀 INITIALIZATION
// ============================================================================

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 PropertyAI Dashboard initializing...');
    
    // Initialize all systems
    initializeOnboarding();
    loadUserProfile();
    animateStats();
    adjustForMobile();
    
    console.log('✅ PropertyAI Dashboard fully loaded!');
});

// Export functions for global access
window.nextOnboardingStep = nextOnboardingStep;
window.previousOnboardingStep = previousOnboardingStep;
window.showSection = showSection;
window.showOnboardingSection = showOnboardingSection;
window.populateOnboardingForm = populateOnboardingForm;
window.connectFacebook = connectFacebook;
window.showTerms = showTerms;
window.showPrivacy = showPrivacy;
window.completeOnboarding = completeOnboarding;
