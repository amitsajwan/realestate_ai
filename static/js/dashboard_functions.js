// Dashboard Functions - Business logic and feature implementations
// This file contains all the specific functionality for different dashboard features

// User Profile Management
let userProfile = null;

function loadUserProfile() {
    console.log('👤 Loading user profile...');
    
    const storedProfile = localStorage.getItem('userProfile');
    if (storedProfile) {
        try {
            userProfile = JSON.parse(storedProfile);
            console.log('✅ User profile loaded from storage');
        } catch (e) {
            console.warn('⚠️ Failed to parse stored profile');
        }
    }
    
    if (!userProfile) {
        userProfile = {
            name: 'Property Agent',
            company: 'Real Estate Agency',
            email: 'agent@example.com',
            phone: '+91 98765 43210',
            city: 'Mumbai',
            experience: '5+ years'
        };
        // Save default profile to localStorage so onboarding form can find it
        localStorage.setItem('userProfile', JSON.stringify(userProfile));
        console.log('✅ Default user profile created and saved to localStorage');
    }
    
    updateUserProfileDisplay();
}

function updateUserProfileDisplay() {
    if (!userProfile) return;
    
    const companyNameElement = document.getElementById('welcomeCompanyName');
    if (companyNameElement && userProfile.company) {
        companyNameElement.textContent = userProfile.company;
    }
    
    console.log('✅ User profile display updated');
}

// Dashboard Statistics
function loadDashboardStats() {
    console.log('📊 Loading dashboard stats...');
    
    fetch('/api/v1/dashboard/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.stats) {
                updateDashboardStats(data.stats);
                console.log('✅ Stats loaded from API');
            } else {
                console.warn('⚠️ API returned no stats, using fallback');
                loadFallbackStats();
            }
        })
        .catch(error => {
            console.warn('⚠️ Failed to load stats from API, using fallback:', error);
            loadFallbackStats();
        });
}

function loadFallbackStats() {
    console.log('📊 Loading fallback stats...');
    
    const fallbackStats = {
        total_properties: 24,
        active_listings: 18,
        pending_posts: 6,
        total_views: 2847,
        monthly_leads: 45,
        revenue: "₹85,00,000"
    };
    
    updateDashboardStats(fallbackStats);
}

function updateDashboardStats(stats) {
    const activeListings = document.getElementById('nextgenActiveListings');
    if (activeListings) activeListings.textContent = stats.active_listings || 0;
    
    const aiGenerated = document.getElementById('nextgenAiGenerated');
    if (aiGenerated) aiGenerated.textContent = stats.total_views || 0;
    
    const socialPosts = document.getElementById('nextgenSocialPosts');
    if (socialPosts) socialPosts.textContent = stats.pending_posts || 0;
    
    const newLeads = document.getElementById('nextgenNewLeads');
    if (newLeads) newLeads.textContent = stats.monthly_leads || 0;
    
    console.log('✅ Dashboard stats updated');
}

// Property Management
function loadUserProperties() {
    console.log('🏠 Loading user properties...');
    
    const sampleProperties = [
        {
            id: 1,
            type: 'Apartment',
            city: 'Mumbai',
            area: 'Andheri West',
            price: '₹85,00,000',
            bedrooms: '2 BHK',
            status: 'Active'
        },
        {
            id: 2,
            type: 'Villa',
            city: 'Pune',
            area: 'Koregaon Park',
            price: '₹2,50,00,000',
            bedrooms: '4 BHK',
            status: 'Active'
        }
    ];
    
    const propertiesGrid = document.getElementById('propertiesGrid');
    if (propertiesGrid) {
        propertiesGrid.innerHTML = sampleProperties.map(property => 
            '<div class="col-md-6 col-lg-4 mb-4">' +
                '<div class="card h-100">' +
                    '<div class="card-body">' +
                        '<h5 class="card-title">' + property.type + ' - ' + property.bedrooms + '</h5>' +
                        '<p class="card-text">' +
                            '<strong>Location:</strong> ' + property.area + ', ' + property.city + '<br>' +
                            '<strong>Price:</strong> ' + property.price + '<br>' +
                            '<span class="badge bg-success">' + property.status + '</span>' +
                        '</p>' +
                    '</div>' +
                '</div>' +
            '</div>'
        ).join('');
        
        console.log('✅ Properties grid updated');
    }
}

// Facebook Integration
function loadFacebookPages() {
    console.log('📘 Loading Facebook pages...');
    // TODO: Implement Facebook pages loading
}

function loadFacebookStatus() {
    console.log('📘 Loading Facebook status...');
    // TODO: Implement Facebook status loading
}

function loadPostingHistory() {
    console.log('📘 Loading posting history...');
    // TODO: Implement posting history loading
}

// Onboarding Functions - Removed duplicates (functions are defined in dashboard_scripts.html)
// These functions are now handled by the dashboard_scripts.html include

// Utility Functions
function showAddPropertyModal() {
    const modalElement = document.getElementById('addPropertyModal');
    if (modalElement && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    } else {
        console.error('❌ Bootstrap Modal not available');
        if (window.dashboardCore && window.dashboardCore.showAlert) {
            window.dashboardCore.showAlert('Modal functionality not available', 'warning');
        }
    }
}

function hideAddPropertyModal() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('addPropertyModal'));
    if (modal) modal.hide();
}

// Export functions for global access
window.dashboardFunctions = {
    loadUserProfile,
    updateUserProfileDisplay,
    loadDashboardStats,
    updateDashboardStats,
    loadUserProperties,
    loadFacebookPages,
    loadFacebookStatus,
    loadPostingHistory,
    showAddPropertyModal,
    hideAddPropertyModal
};
