class SmartPropertiesComponent {
    constructor() {
        this.properties = [];
        this.currentProperty = null;
        this.facebookConfig = null;
    }

    render() {
        return `
            <div class="row">
                <div class="col-lg-8">
                    <div class="modern-card card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <div>
                                <h5 class="mb-0">🤖 Smart Properties</h5>
                                <small class="text-muted">AI-powered property management with Facebook posting</small>
                            </div>
                            <button class="btn btn-primary" onclick="smartProperties.showCreateModal()">
                                <i class="fas fa-plus"></i> Create Smart Property
                            </button>
                        </div>
                        <div class="card-body">
                            <!-- Facebook Status -->
                            <div id="facebook-status-bar" class="alert alert-info mb-3" style="display: none;">
                                <i class="fab fa-facebook me-2"></i>
                                <span id="facebook-status-text">Loading Facebook status...</span>
                                <button id="facebook-connect-btn" class="btn btn-sm btn-outline-primary ms-2" style="display: none;">
                                    Connect Facebook
                                </button>
                            </div>
                            
                            <div id="properties-grid" class="row">
                                <!-- Properties will be loaded here -->
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="modern-card card mb-3">
                        <div class="card-header">
                            <h6 class="mb-0">📈 Quick Stats</h6>
                        </div>
                        <div class="card-body">
                            <div class="d-flex justify-content-between mb-3">
                                <span>Total Properties</span>
                                <strong id="total-properties">0</strong>
                            </div>
                            <div class="d-flex justify-content-between mb-3">
                                <span>AI Generated</span>
                                <strong id="ai-generated">0</strong>
                            </div>
                            <div class="d-flex justify-content-between">
                                <span>Posted to Facebook</span>
                                <strong id="posted-facebook">0</strong>
                            </div>
                        </div>
                    </div>

                    <!-- Facebook Integration Card -->
                    <div class="modern-card card">
                        <div class="card-header">
                            <h6 class="mb-0">📘 Facebook Integration</h6>
                        </div>
                        <div class="card-body" id="facebook-integration-body">
                            <div class="text-center">
                                <i class="fab fa-facebook fa-2x text-muted mb-2"></i>
                                <p class="text-muted">Loading Facebook status...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Create Property Modal with Enhanced Facebook Features -->
            <div class="modal fade" id="createPropertyModal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header border-0">
                            <h5 class="modal-title">🤖 Create Smart Property</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body p-0">
                            <div class="row g-0">
                                <!-- Form Section -->
                                <div class="col-lg-6 p-4">
                                    <form id="smart-property-form">
                                        <div class="mb-3">
                                            <label class="form-label">Property Address *</label>
                                            <input type="text" class="form-control" name="address" required>
                                        </div>
                                        
                                        <div class="row">
                                            <div class="col-md-6 mb-3">
                                                <label class="form-label">Price *</label>
                                                <div class="input-group">
                                                    <span class="input-group-text">₹</span>
                                                    <input type="text" class="form-control" name="price" required>
                                                </div>
                                            </div>
                                            <div class="col-md-6 mb-3">
                                                <label class="form-label">Type *</label>
                                                <select class="form-select" name="property_type" required>
                                                    <option value="">Select Type</option>
                                                    <option value="apartment">🏢 Apartment</option>
                                                    <option value="condo">🏠 Condo</option>
                                                    <option value="townhouse">🏘️ Townhouse</option>
                                                    <option value="single_family">🏡 Single Family</option>
                                                    <option value="villa">🏰 Villa</option>
                                                </select>
                                            </div>
                                        </div>

                                        <div class="row">
                                            <div class="col-md-6 mb-3">
                                                <label class="form-label">Bedrooms *</label>
                                                <select class="form-select" name="bedrooms" required>
                                                    <option value="">Select</option>
                                                    <option value="1">1 Bedroom</option>
                                                    <option value="2">2 Bedrooms</option>
                                                    <option value="3">3 Bedrooms</option>
                                                    <option value="4">4 Bedrooms</option>
                                                    <option value="5">5+ Bedrooms</option>
                                                </select>
                                            </div>
                                            <div class="col-md-6 mb-3">
                                                <label class="form-label">Bathrooms *</label>
                                                <select class="form-select" name="bathrooms" required>
                                                    <option value="">Select</option>
                                                    <option value="1">1 Bathroom</option>
                                                    <option value="1.5">1.5 Bathrooms</option>
                                                    <option value="2">2 Bathrooms</option>
                                                    <option value="2.5">2.5 Bathrooms</option>
                                                    <option value="3">3+ Bathrooms</option>
                                                </select>
                                            </div>
                                        </div>

                                        <!-- Enhanced Features Section -->
                                        <div class="mb-3">
                                            <label class="form-label">Key Features</label>
                                            <div class="feature-tags mb-2" id="selected-features">
                                                <!-- Selected features will appear here -->
                                            </div>
                                            <div class="feature-options">
                                                <div class="btn-group flex-wrap" role="group">
                                                    <input type="checkbox" class="btn-check" id="feat-pool" value="Swimming Pool">
                                                    <label class="btn btn-outline-primary btn-sm" for="feat-pool">🏊 Pool</label>
                                                    
                                                    <input type="checkbox" class="btn-check" id="feat-gym" value="Gym">
                                                    <label class="btn btn-outline-primary btn-sm" for="feat-gym">💪 Gym</label>
                                                    
                                                    <input type="checkbox" class="btn-check" id="feat-parking" value="Parking">
                                                    <label class="btn btn-outline-primary btn-sm" for="feat-parking">🅿️ Parking</label>
                                                    
                                                    <input type="checkbox" class="btn-check" id="feat-balcony" value="Balcony">
                                                    <label class="btn btn-outline-primary btn-sm" for="feat-balcony">🌅 Balcony</label>
                                                    
                                                    <input type="checkbox" class="btn-check" id="feat-security" value="24/7 Security">
                                                    <label class="btn btn-outline-primary btn-sm" for="feat-security">🔒 Security</label>
                                                    
                                                    <input type="checkbox" class="btn-check" id="feat-garden" value="Garden">
                                                    <label class="btn btn-outline-primary btn-sm" for="feat-garden">🌳 Garden</label>
                                                </div>
                                            </div>
                                            <div class="mt-2">
                                                <input type="text" class="form-control" placeholder="Add custom feature..." id="custom-feature">
                                                <button type="button" class="btn btn-outline-secondary btn-sm mt-1" onclick="smartProperties.addCustomFeature()">Add Feature</button>
                                            </div>
                                        </div>

                                        <div class="mb-3">
                                            <div class="form-check form-switch">
                                                <input class="form-check-input" type="checkbox" id="ai-generate" checked>
                                                <label class="form-check-label" for="ai-generate">
                                                    🤖 Auto-generate AI content
                                                </label>
                                            </div>
                                        </div>
                                    </form>
                                </div>
                                
                                <!-- Preview & Posting Section -->
                                <div class="col-lg-6 bg-light p-4">
                                    <h6 class="mb-3">🔮 Live Preview</h6>
                                    <div id="live-preview" class="border rounded p-3 bg-white mb-3">
                                        <div class="text-center text-muted">
                                            <i class="fas fa-magic fa-2x mb-2"></i>
                                            <p>Fill in property details to see AI-generated content</p>
                                        </div>
                                    </div>
                                    
                                    <!-- Real Facebook Posting Options -->
                                    <div id="posting-options" style="display: none;">
                                        <h6 class="mb-3">📱 Post to Social Media</h6>
                                        
                                        <!-- Facebook Post Option -->
                                        <div class="card mb-3" id="facebook-post-card">
                                            <div class="card-header d-flex align-items-center">
                                                <i class="fab fa-facebook text-primary me-2"></i>
                                                <span>Facebook</span>
                                                <div class="form-check form-switch ms-auto">
                                                    <input class="form-check-input" type="checkbox" id="post-to-facebook" checked>
                                                </div>
                                            </div>
                                            <div class="card-body" id="facebook-post-body">
                                                <div id="facebook-status-indicator" class="text-muted">
                                                    <i class="fas fa-spinner fa-spin"></i> Checking Facebook status...
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Other Social Media (Future) -->
                                        <div class="card mb-3 opacity-50">
                                            <div class="card-header">
                                                <i class="fab fa-instagram text-danger me-2"></i>
                                                <span>Instagram</span>
                                                <small class="text-muted ms-auto">Coming Soon</small>
                                            </div>
                                        </div>

                                        <div class="d-flex gap-2">
                                            <button class="btn btn-outline-secondary flex-fill" onclick="smartProperties.copyToClipboard()">
                                                <i class="fas fa-copy"></i> Copy
                                            </button>
                                            <button class="btn btn-outline-success flex-fill" onclick="smartProperties.shareWhatsApp()">
                                                <i class="fab fa-whatsapp"></i> WhatsApp
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer border-0">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-success" id="create-and-post-btn" onclick="smartProperties.createAndPost()">
                                <i class="fas fa-magic"></i> Create & Post
                            </button>
                            <button type="button" class="btn btn-primary" onclick="smartProperties.createProperty()">
                                <i class="fas fa-save"></i> Create Only
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Facebook Page Selection Modal -->
            <div class="modal fade" id="facebookPageModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">📘 Select Facebook Page</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div id="facebook-pages-list">
                                <div class="text-center">
                                    <i class="fas fa-spinner fa-spin fa-2x mb-3"></i>
                                    <p>Loading your Facebook pages...</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    
async load() {
    document.getElementById('component-container').innerHTML = this.render();
    
    // Auto-refresh Facebook status on load (especially after OAuth return)
    await this.loadFacebookStatus();
    
    // If we just returned from Facebook OAuth, force a refresh after a short delay
    if (window.location.search.includes('facebook') || document.referrer.includes('facebook.com')) {
        console.log('🔄 Detected return from Facebook OAuth, refreshing status...');
        setTimeout(async () => {
            await this.loadFacebookStatus();
        }, 1000);
    }
    
    await this.loadProperties();
    this.setupEventListeners();
}

async loadFacebookStatus() {
    try {
        console.log('🔍 Loading Facebook integration status...');
        
        const response = await fetch('/api/facebook/config', {
            headers: {
                'Authorization': `Bearer ${dashboardCore.getAuthToken()}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            console.log('📘 Facebook config response:', data);
            
            this.facebookConfig = data;
            this.updateFacebookUI();
        } else {
            console.warn('❌ Facebook config failed:', response.status);
            const errorData = await response.text();
            console.warn('Error details:', errorData);
            
            this.facebookConfig = { connected: false };
            this.updateFacebookUI();
        }
    } catch (error) {
        console.error('❌ Error loading Facebook status:', error);
        this.facebookConfig = { connected: false };
        this.updateFacebookUI();
    }
}

    updateFacebookUI() {
        const statusBar = document.getElementById('facebook-status-bar');
        const statusText = document.getElementById('facebook-status-text');
        const connectBtn = document.getElementById('facebook-connect-btn');
        const integrationBody = document.getElementById('facebook-integration-body');
        const facebookPostBody = document.getElementById('facebook-post-body');
        
        if (this.facebookConfig.connected) {
            // Connected state
            statusBar.className = 'alert alert-success mb-3';
            statusText.innerHTML = `✅ Connected to Facebook Page: <strong>${this.facebookConfig.page_name}</strong>`;
            connectBtn.style.display = 'none';
            
            integrationBody.innerHTML = `
                <div class="text-center">
                    <i class="fab fa-facebook fa-2x text-primary mb-2"></i>
                    <h6 class="text-success">Connected!</h6>
                    <p class="small text-muted">${this.facebookConfig.page_name}</p>
                    <div class="d-flex gap-2 justify-content-center">
                        <button class="btn btn-outline-info btn-sm" onclick="smartProperties.refreshFacebookStatus()">
                            <i class="fas fa-sync"></i> Refresh
                        </button>
                        <button class="btn btn-outline-danger btn-sm" onclick="smartProperties.disconnectFacebook()">
                            <i class="fas fa-unlink"></i> Disconnect
                        </button>
                    </div>
                </div>
            `;

            if (facebookPostBody) {
                facebookPostBody.innerHTML = `
                    <div class="text-success small">
                        <i class="fas fa-check-circle me-1"></i>
                        Ready to post to: <strong>${this.facebookConfig.page_name}</strong>
                    </div>
                `;
            }
        } else {
            // Not connected state
            statusBar.className = 'alert alert-warning mb-3';
            statusText.textContent = '⚠️ Facebook not connected';
            connectBtn.style.display = 'inline-block';
            connectBtn.onclick = () => this.connectFacebook();
            
            integrationBody.innerHTML = `
                <div class="text-center">
                    <i class="fab fa-facebook fa-2x text-muted mb-2"></i>
                    <h6 class="text-muted">Not Connected</h6>
                    <p class="small text-muted">Connect your Facebook page to post properties directly</p>
                    <div class="d-flex gap-2 justify-content-center">
                        <button class="btn btn-primary btn-sm" onclick="smartProperties.connectFacebook()">
                            <i class="fab fa-facebook me-1"></i> Connect Facebook
                        </button>
                        <button class="btn btn-outline-info btn-sm" onclick="smartProperties.refreshFacebookStatus()">
                            <i class="fas fa-sync"></i> Refresh
                        </button>
                    </div>
                </div>
            `;

            if (facebookPostBody) {
                facebookPostBody.innerHTML = `
                    <div class="text-warning small">
                        <i class="fas fa-exclamation-triangle me-1"></i>
                        Connect Facebook to enable posting
                    </div>
                `;
            }
        }
        
        statusBar.style.display = 'block';
    }

    // Add this method to SmartPropertiesComponent
    async refreshFacebookStatus() {
        console.log('🔄 Manually refreshing Facebook status...');
        dashboardCore.showToast('info', 'Refreshing...', 'Checking Facebook connection status');
        await this.loadFacebookStatus();
    }


    async connectFacebook() {
        try {
            const token = dashboardCore.getAuthToken();
            // Use existing Facebook OAuth flow
            window.location.href = `/auth/facebook/login?token=${token}`;
        } catch (error) {
            dashboardCore.showToast('error', 'Connection Failed', 'Failed to connect to Facebook');
        }
    }

    async disconnectFacebook() {
        // Implement disconnect functionality
        dashboardCore.showToast('info', 'Disconnect', 'Facebook disconnect functionality will be implemented');
    }

    setupEventListeners() {
        // Real-time form updates
        const form = document.getElementById('smart-property-form');
        if (form) {
            form.addEventListener('input', () => this.updateLivePreview());
            form.addEventListener('change', () => this.updateLivePreview());
        }

        // Feature selection
        const featureInputs = document.querySelectorAll('.btn-check');
        featureInputs.forEach(input => {
            input.addEventListener('change', () => this.updateSelectedFeatures());
        });
    }

    updateSelectedFeatures() {
        const selectedContainer = document.getElementById('selected-features');
        const checkboxes = document.querySelectorAll('.btn-check:checked');
        
        const features = Array.from(checkboxes).map(cb => cb.value);
        
        selectedContainer.innerHTML = features.map(feature => 
            `<span class="badge bg-primary me-1 mb-1">${feature} <i class="fas fa-times ms-1" onclick="smartProperties.removeFeature('${feature}')"></i></span>`
        ).join('');

        this.updateLivePreview();
    }

    removeFeature(feature) {
        const checkbox = document.querySelector(`input[value="${feature}"]`);
        if (checkbox) {
            checkbox.checked = false;
            this.updateSelectedFeatures();
        }
    }

    addCustomFeature() {
        const input = document.getElementById('custom-feature');
        const feature = input.value.trim();
        
        if (feature) {
            const selectedContainer = document.getElementById('selected-features');
            selectedContainer.innerHTML += `<span class="badge bg-success me-1 mb-1">${feature} <i class="fas fa-times ms-1" onclick="smartProperties.removeCustomFeature('${feature}')"></i></span>`;
            input.value = '';
            this.updateLivePreview();
        }
    }

    removeCustomFeature(feature) {
        const badges = document.querySelectorAll('.badge');
        badges.forEach(badge => {
            if (badge.textContent.trim().startsWith(feature)) {
                badge.remove();
            }
        });
        this.updateLivePreview();
    }

    async updateLivePreview() {
        const form = document.getElementById('smart-property-form');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        const features = this.getSelectedFeatures();

        if (data.address && data.price && data.property_type) {
            const preview = document.getElementById('live-preview');
            const postingOptions = document.getElementById('posting-options');
            
            try {
                const response = await fetch('/api/listings/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${dashboardCore.getAuthToken()}`
                    },
                    body: JSON.stringify({
                        address: data.address,
                        city: "Mumbai",
                        state: "Maharashtra",
                        price: data.price,
                        property_type: data.property_type,
                        bedrooms: parseInt(data.bedrooms) || 1,
                        bathrooms: parseFloat(data.bathrooms) || 1,
                        features: features,
                        template: "just_listed",
                        language: "en"
                    })
                });

                if (response.ok) {
                    const result = await response.json();
                    this.currentGeneratedContent = result;
                    
                    preview.innerHTML = `
                        <div class="preview-content">
                            <div class="d-flex align-items-center mb-2">
                                <i class="fas fa-robot text-primary me-2"></i>
                                <small class="text-muted">AI Generated Content</small>
                            </div>
                            <div class="preview-text p-3 border-start border-4 border-primary">
                                ${result.caption.replace(/\n/g, '<br>')}
                            </div>
                            <div class="mt-2">
                                <small class="text-muted">
                                    ${result.hashtags.join(' ')}
                                </small>
                            </div>
                        </div>
                    `;
                    postingOptions.style.display = 'block';
                } else {
                    preview.innerHTML = `
                        <div class="text-center text-muted">
                            <i class="fas fa-exclamation-triangle fa-2x mb-2 text-warning"></i>
                            <p>Unable to generate preview</p>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Preview generation error:', error);
            }
        }
    }

    getSelectedFeatures() {
        const features = [];
        
        const checkboxes = document.querySelectorAll('.btn-check:checked');
        checkboxes.forEach(cb => features.push(cb.value));
        
        const customBadges = document.querySelectorAll('.badge.bg-success');
        customBadges.forEach(badge => {
            const text = badge.textContent.replace('×', '').trim();
            if (text) features.push(text);
        });
        
        return features;
    }

    showCreateModal() {
        const modal = new bootstrap.Modal(document.getElementById('createPropertyModal'));
        modal.show();
        // Refresh Facebook status when modal opens
        this.loadFacebookStatus();
    }

    async createProperty() {
        const propertyData = this.getPropertyFormData();

        try {
            const response = await fetch('/api/smart-properties', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${dashboardCore.getAuthToken()}`
                },
                body: JSON.stringify(propertyData)
            });

            if (response.ok) {
                const result = await response.json();
                
                dashboardCore.showToast('success', 'Property Created!', `Property at ${result.address} created successfully.`);
                
                this.closeModal();
                await this.loadProperties();
                
                return result;
            } else {
                const error = await response.json();
                dashboardCore.showToast('error', 'Creation Failed', error.detail || 'Failed to create property');
                return null;
            }
        } catch (error) {
            console.error('Error creating property:', error);
            dashboardCore.showToast('error', 'Network Error', 'Unable to create property. Please try again.');
            return null;
        }
    }

    async createAndPost() {
        const postToFacebook = document.getElementById('post-to-facebook').checked;
        
        // First create the property
        const property = await this.createProperty();
        
        if (property && postToFacebook && this.facebookConfig.connected && this.currentGeneratedContent) {
            // Post to Facebook using existing API
            await this.postPropertyToFacebook(property, this.currentGeneratedContent);
        }
    }

    async postPropertyToFacebook(property, content) {
        try {
            console.log('Posting to Facebook:', { property, content });
            
            // Use the existing Facebook posting endpoint
            const response = await fetch('/api/facebook/post', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${dashboardCore.getAuthToken()}`
                },
                body: JSON.stringify({
                    message: content.caption + '\n\n' + content.hashtags.join(' '),
                    image_url: null // Could add image URL here if needed
                })
            });

            if (response.ok) {
                const result = await response.json();
                dashboardCore.showToast('success', 'Posted to Facebook!', 
                    `Property successfully posted to ${this.facebookConfig.page_name}`);
                
                // Update stats
                this.updateStats();
                
            } else {
                const error = await response.json();
                dashboardCore.showToast('error', 'Facebook Post Failed', 
                    error.detail || 'Failed to post to Facebook');
            }
        } catch (error) {
            console.error('Facebook posting error:', error);
            dashboardCore.showToast('error', 'Posting Error', 'Network error while posting to Facebook');
        }
    }

    getPropertyFormData() {
        const form = document.getElementById('smart-property-form');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        const features = this.getSelectedFeatures();
        
        return {
            address: data.address,
            price: data.price,
            property_type: data.property_type,
            bedrooms: parseInt(data.bedrooms) || 0,
            bathrooms: parseFloat(data.bathrooms) || 0,
            features: features.join(', '),
            ai_generate: document.getElementById('ai-generate').checked,
            template: 'just_listed',
            language: 'en'
        };
    }

    closeModal() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('createPropertyModal'));
        if (modal) {
            modal.hide();
        }
        
        const form = document.getElementById('smart-property-form');
        if (form) {
            form.reset();
        }
        
        document.getElementById('selected-features').innerHTML = '';
        document.getElementById('live-preview').innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-magic fa-2x mb-2"></i>
                <p>Fill in property details to see AI-generated content</p>
            </div>
        `;
        document.getElementById('posting-options').style.display = 'none';
    }

    async loadProperties() {
        try {
            const response = await fetch('/api/smart-properties', {
                headers: {
                    'Authorization': `Bearer ${dashboardCore.getAuthToken()}`
                }
            });

            if (response.ok) {
                this.properties = await response.json();
                this.renderProperties();
                this.updateStats();
            }
        } catch (error) {
            console.error('Error loading properties:', error);
        }
    }

    renderProperties() {
        const grid = document.getElementById('properties-grid');
        if (!grid) return;

        if (this.properties.length === 0) {
            grid.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fas fa-home fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">No properties yet</h5>
                    <p class="text-muted">Create your first smart property with Facebook posting</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = this.properties.map(property => `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card modern-card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title">${property.address}</h6>
                            <span class="badge bg-primary">${property.property_type}</span>
                        </div>
                        <p class="text-muted small mb-2">₹${property.price}</p>
                        <div class="d-flex gap-2 mb-3">
                            <span class="badge bg-light text-dark">🛏️ ${property.bedrooms}</span>
                            <span class="badge bg-light text-dark">🚿 ${property.bathrooms}</span>
                        </div>
                        ${property.ai_content ? `
                            <div class="ai-preview mb-3">
                                <small class="text-muted d-flex align-items-center">
                                    <i class="fas fa-robot me-1"></i> AI Generated
                                </small>
                                <p class="small">${property.ai_content.substring(0, 100)}...</p>
                            </div>
                        ` : ''}
                        <div class="d-flex gap-1">
                            <button class="btn btn-sm btn-outline-primary flex-fill" onclick="smartProperties.viewProperty('${property.id}')">
                                <i class="fas fa-eye"></i>
                            </button>
                            ${this.facebookConfig?.connected ? `
                                <button class="btn btn-sm btn-outline-primary" onclick="smartProperties.postExistingToFacebook('${property.id}')" title="Post to Facebook">
                                    <i class="fab fa-facebook"></i>
                                </button>
                            ` : ''}
                            <button class="btn btn-sm btn-outline-success" onclick="smartProperties.shareProperty('${property.id}')">
                                <i class="fas fa-share"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    updateStats() {
        document.getElementById('total-properties').textContent = this.properties.length;
        document.getElementById('ai-generated').textContent = this.properties.filter(p => p.ai_content).length;
        // You could track Facebook posts in property metadata
        document.getElementById('posted-facebook').textContent = '0'; // Placeholder
    }

    async postExistingToFacebook(propertyId) {
        if (!this.facebookConfig.connected) {
            dashboardCore.showToast('warning', 'Facebook Not Connected', 'Please connect your Facebook page first');
            return;
        }

        const property = this.properties.find(p => p.id === propertyId);
        if (!property) {
            dashboardCore.showToast('error', 'Property Not Found', 'Unable to find property');
            return;
        }

        // Generate content for this property
        try {
            const response = await fetch('/api/listings/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${dashboardCore.getAuthToken()}`
                },
                body: JSON.stringify({
                    address: property.address,
                    city: "Mumbai",
                    state: "Maharashtra",
                    price: property.price,
                    property_type: property.property_type,
                    bedrooms: property.bedrooms,
                    bathrooms: property.bathrooms,
                    features: property.features ? property.features.split(', ') : [],
                    template: "just_listed",
                    language: "en"
                })
            });

            if (response.ok) {
                const content = await response.json();
                await this.postPropertyToFacebook(property, content);
            } else {
                dashboardCore.showToast('error', 'Content Generation Failed', 'Unable to generate content for posting');
            }
        } catch (error) {
            console.error('Error posting existing property:', error);
            dashboardCore.showToast('error', 'Posting Failed', 'Network error while posting to Facebook');
        }
    }

    // Utility methods
    async copyToClipboard() {
        const preview = document.querySelector('.preview-text');
        if (preview && this.currentGeneratedContent) {
            const text = this.currentGeneratedContent.caption + '\n\n' + this.currentGeneratedContent.hashtags.join(' ');
            await navigator.clipboard.writeText(text);
            dashboardCore.showToast('success', 'Copied!', 'Content copied to clipboard');
        }
    }

    async shareWhatsApp() {
        if (this.currentGeneratedContent) {
            const text = encodeURIComponent(this.currentGeneratedContent.caption + '\n\n' + this.currentGeneratedContent.hashtags.join(' '));
            window.open(`https://wa.me/?text=${text}`, '_blank');
        }
    }

    viewProperty(id) {
        dashboardCore.showToast('info', 'View Property', `Viewing property ${id}`);
    }

    shareProperty(id) {
        dashboardCore.showToast('info', 'Share Property', `Sharing property ${id}`);
    }
}

// Initialize Smart Properties Component  
const smartProperties = new SmartPropertiesComponent();
