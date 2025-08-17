class DashboardCore {
    constructor() {
        this.authToken = localStorage.getItem('authToken') || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZGVtb191c2VyIiwiZW1haWwiOiJkZW1vQG11bWJhaS5jb20iLCJuYW1lIjoiRGVtbyBVc2VyIn0.demo_token';
        this.currentComponent = 'dashboard';
    }

    getAuthToken() {
        return this.authToken;
    }

    getApiHeaders() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.authToken}`
        };
    }

    showToast(type, title, message) {
        // Create toast container if it doesn't exist
        if (!document.getElementById('toast-container')) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        const toastId = 'toast-' + Date.now();
        const iconClass = {
            'success': 'fas fa-check-circle text-success',
            'error': 'fas fa-exclamation-circle text-danger',
            'info': 'fas fa-info-circle text-info',
            'warning': 'fas fa-exclamation-triangle text-warning'
        }[type] || 'fas fa-info-circle text-info';

        const toastHtml = `
            <div id="${toastId}" class="toast" role="alert">
                <div class="toast-header">
                    <i class="${iconClass} me-2"></i>
                    <strong class="me-auto">${title}</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">${message}</div>
            </div>
        `;

        document.getElementById('toast-container').insertAdjacentHTML('beforeend', toastHtml);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 4000 });
        toast.show();

        // Remove from DOM after hiding
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
}

// Global instance
const dashboardCore = new DashboardCore();

// Component loading function
async function loadComponent(componentName) {
    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    event.target.classList.add('active');

    dashboardCore.currentComponent = componentName;

    // Load component
    switch (componentName) {
        case 'smart-properties':
            await smartProperties.load();
            break;
        case 'dashboard':
            await loadDashboardOverview();
            break;
        case 'leads':
            await loadLeadsManager();
            break;
        case 'settings':
            await loadSettings();
            break;
        default:
            document.getElementById('component-container').innerHTML = '<div class="text-center py-5"><h4>Component not found</h4></div>';
    }
}

// Initialize dashboard on load
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Modular Dashboard Initialized');
    loadComponent('dashboard');
});
