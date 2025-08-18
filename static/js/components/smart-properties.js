class SmartPropertiesComponent {
    constructor() {
    this.properties = [];
    this.currentProperty = null;
    this.facebookConfig = null;
    this.currentGeneratedContent = null;  // Stores latest AI-generated post preview
    }


    render() {
    return `
        <div class="row">
            <!-- Main Content: Properties List -->
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
                        <!-- Facebook Status Bar -->
                        <div id="facebook-status" class="alert alert-info mb-3" style="display:none;">
                            <i class="fab fa-facebook me-2"></i>
                            <span id="facebook-status-text">Loading Facebook status...</span>
                            <button id="facebook-connect-btn" class="btn btn-sm btn-outline-primary" style="display:none;">
                                Connect Facebook
                            </button>
                        </div>
                        
                        <!-- Properties Grid -->
                        <div id="properties-grid" class="row">
                            <!-- Properties will be loaded here -->
                        </div>
                    </div>
                </div>
            </div>

            <!-- Sidebar: Stats & Facebook Integration -->
            <div class="col-lg-4">
                <!-- Stats Card -->
                <div class="modern-card card mb-3">
                    <div class="card-header">
                        <h6 class="mb-0">📊 Quick Stats</h6>
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
                        <div class="text-center text-muted" id="facebook-loading">
                            <i class="fas fa-spinner fa-spin"></i> Loading Facebook status...
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Create Smart Property Modal -->
        <div class="modal fade" id="createPropertyModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-fullscreen-lg-down modal-xl">
                <div class="modal-content">
                    <div class="modal-header border-0">
                        <h5 class="modal-title">🤖 Create Smart Property</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body p-0">
                        <div class="row g-0">
                            <!-- Left Panel: Property Form -->
                            <div class="col-lg-6 p-4">
                                <form id="smart-property-form">
                                    <!-- Basic Property Info -->
                                    <div class="mb-3">
                                        <label class="form-label fw-bold">Property Address *</label>
                                        <input type="text" class="form-control form-control-lg" name="address" 
                                               placeholder="e.g., 123 Palm Beach Road, Navi Mumbai" required>
                                    </div>
                                    
                                    <div class="row">
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label fw-bold">Price *</label>
                                            <div class="input-group">
                                                <span class="input-group-text">₹</span>
                                                <input type="text" class="form-control" name="price" 
                                                       placeholder="2.5 Cr" required>
                                            </div>
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label fw-bold">Property Type *</label>
                                            <select name="property_type" class="form-select" required>
                                                <option value="">Select Type</option>
                                                <option value="apartment">🏢 Apartment</option>
                                                <option value="villa">🏰 Villa</option>
                                                <option value="condo">🏠 Condo</option>
                                                <option value="townhouse">🏘️ Townhouse</option>
                                                <option value="single_family">🏡 Single Family Home</option>
                                                <option value="penthouse">🌆 Penthouse</option>
                                            </select>
                                        </div>
                                    </div>

                                    <!-- Bedrooms & Bathrooms -->
                                    <div class="row">
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label fw-bold">Bedrooms *</label>
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
                                            <label class="form-label fw-bold">Bathrooms *</label>
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

                                    <!-- Premium Features -->
                                    <div class="mb-3">
                                        <label class="form-label fw-bold">Premium Features</label>
                                        <div id="selected-features" class="mb-2">
                                            <!-- Selected features will appear here as badges -->
                                        </div>
                                        <div id="features-container" class="feature-grid">
                                            <label class="feature-option">
                                                <input type="checkbox" value="Swimming Pool">
                                                <span class="feature-badge">🏊 Pool</span>
                                            </label>
                                            <label class="feature-option">
                                                <input type="checkbox" value="Gym">
                                                <span class="feature-badge">💪 Gym</span>
                                            </label>
                                            <label class="feature-option">
                                                <input type="checkbox" value="Parking">
                                                <span class="feature-badge">🅿️ Parking</span>
                                            </label>
                                            <label class="feature-option">
                                                <input type="checkbox" value="Balcony">
                                                <span class="feature-badge">🌅 Balcony</span>
                                            </label>
                                            <label class="feature-option">
                                                <input type="checkbox" value="24/7 Security">
                                                <span class="feature-badge">🔒 Security</span>
                                            </label>
                                            <label class="feature-option">
                                                <input type="checkbox" value="Garden">
                                                <span class="feature-badge">🌳 Garden</span>
                                            </label>
                                            <label class="feature-option">
                                                <input type="checkbox" value="Club House">
                                                <span class="feature-badge">🏛️ Club</span>
                                            </label>
                                            <label class="feature-option">
                                                <input type="checkbox" value="Kids Play Area">
                                                <span class="feature-badge">🎮 Play Area</span>
                                            </label>
                                        </div>
                                        <div class="mt-2">
                                            <input type="text" id="custom-feature-input" class="form-control" 
                                                   placeholder="Add custom feature...">
                                            <button type="button" id="add-custom-feature-btn" class="btn btn-outline-secondary btn-sm mt-1">
                                                <i class="fas fa-plus"></i> Add Feature
                                            </button>
                                        </div>
                                    </div>

                                    <!-- AI & Posting Options -->
                                    <div class="row">
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label fw-bold">Post Tone</label>
                                            <select id="post-tone" class="form-select">
                                                <option value="Professional">🎯 Professional</option>
                                                <option value="Friendly">😊 Friendly</option>
                                                <option value="Luxurious">💎 Luxurious</option>
                                                <option value="Urgent">⚡ Urgent</option>
                                            </select>
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label fw-bold">Language</label>
                                            <select id="post-language" class="form-select">
                                                <option value="English">🇺🇸 English</option>
                                                <option value="Hindi">🇮🇳 Hindi</option>
                                                <option value="Marathi">🇮🇳 Marathi</option>
                                            </select>
                                        </div>
                                    </div>

                                    <!-- AI Generation Toggle -->
                                    <div class="mb-3">
                                        <div class="form-check form-switch">
                                            <input class="form-check-input" type="checkbox" id="ai-generate" checked>
                                            <label class="form-check-label fw-bold" for="ai-generate">
                                                🤖 Auto-generate AI content
                                            </label>
                                        </div>
                                    </div>
                                </form>
                            </div>
                            
                            <!-- Right Panel: Live Preview & Variations -->
                            <div class="col-lg-6 bg-gradient p-4" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);">
                                <h6 class="mb-3">🔮 Live Preview</h6>
                                
                                <!-- Main Preview Display -->
                                <div id="live-preview" class="preview-card border rounded-3 p-4 bg-white shadow-sm mb-4">
                                    <div class="text-center text-muted py-4">
                                        <i class="fas fa-magic fa-3x mb-3 text-primary opacity-50"></i>
                                        <h6>Magic Happens Here!</h6>
                                        <p class="mb-0">Fill in property details to see AI-generated content</p>
                                    </div>
                                </div>
                                
                                <!-- Post Variations -->
                                <div id="post-variations" style="display: none;">
                                    <div class="d-flex align-items-center justify-content-between mb-3">
                                        <h6 class="mb-0">📝 Choose Your Style</h6>
                                        <button type="button" class="btn btn-sm btn-outline-primary" onclick="smartProperties.refreshVariations()">
                                            <i class="fas fa-sync-alt"></i> Refresh
                                        </button>
                                    </div>
                                    <div id="variations-container" class="variations-grid">
                                        <!-- Variations will be populated here -->
                                    </div>
                                </div>
                                
                                <!-- Posting Options -->
                                <div id="posting-options" style="display: none;" class="mt-4">
                                    <h6 class="mb-3">📱 Posting Options</h6>
                                    
                                    <!-- Facebook Post Toggle -->
                                    <div class="posting-option-card p-3 rounded-3 border mb-3">
                                        <div class="d-flex align-items-center justify-content-between">
                                            <div class="d-flex align-items-center">
                                                <i class="fab fa-facebook fa-2x text-primary me-3"></i>
                                                <div>
                                                    <h6 class="mb-0">Facebook Page</h6>
                                                    <small id="facebook-page-name" class="text-muted">Connect your page</small>
                                                </div>
                                            </div>
                                            <div class="form-check form-switch">
                                                <input class="form-check-input" type="checkbox" id="post-to-facebook" checked>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <!-- Instagram (Coming Soon) -->
                                    <div class="posting-option-card p-3 rounded-3 border mb-3 opacity-50">
                                        <div class="d-flex align-items-center justify-content-between">
                                            <div class="d-flex align-items-center">
                                                <i class="fab fa-instagram fa-2x text-danger me-3"></i>
                                                <div>
                                                    <h6 class="mb-0">Instagram</h6>
                                                    <small class="text-muted">Coming Soon</small>
                                                </div>
                                            </div>
                                            <span class="badge bg-secondary">Soon</span>
                                        </div>
                                    </div>
                                    
                                    <!-- Quick Actions -->
                                    <div class="d-flex gap-2 mt-3">
                                        <button type="button" class="btn btn-outline-success btn-sm flex-fill" onclick="smartProperties.copyToClipboard()">
                                            <i class="fas fa-copy"></i> Copy
                                        </button>
                                        <button type="button" class="btn btn-outline-info btn-sm flex-fill" onclick="smartProperties.shareWhatsApp()">
                                            <i class="fab fa-whatsapp"></i> WhatsApp
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Modal Footer -->
                    <div class="modal-footer border-0 bg-light">
                        <div class="d-flex gap-2 w-100">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="fas fa-times"></i> Cancel
                            </button>
                            <button type="button" class="btn btn-primary flex-fill" id="create-only-btn">
                                <i class="fas fa-save"></i> Create Property
                            </button>
                            <button type="button" class="btn btn-success flex-fill" id="create-and-post-btn">
                                <i class="fas fa-magic"></i> Create & Post
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <style>
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 8px;
        }
        .feature-option {
            display: block;
            cursor: pointer;
        }
        .feature-option input[type="checkbox"] {
            display: none;
        }
        .feature-badge {
            display: block;
            padding: 8px 12px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            text-align: center;
            font-size: 0.85em;
            transition: all 0.2s ease;
            background: white;
        }
        .feature-option input[type="checkbox"]:checked + .feature-badge {
            background: #0d6efd;
            color: white;
            border-color: #0d6efd;
        }
        .feature-badge:hover {
            border-color: #0d6efd;
            transform: translateY(-1px);
        }
        .preview-card {
            min-height: 200px;
            transition: all 0.3s ease;
        }
        .variations-grid {
            display: grid;
            gap: 12px;
        }
        .posting-option-card {
            transition: all 0.2s ease;
        }
        .posting-option-card:hover {
            background-color: #f8f9fa;
        }
        .bg-gradient {
            position: relative;
        }
        .modern-card {
            box-shadow: 0 0 20px rgba(0,0,0,0.08);
            border: none;
        }
        </style>
    `;
}

    // Load data and initialize UI
    async load() {
    document.getElementById('component-container').innerHTML = this.render();

    await this.loadFacebookStatus();

    // Refresh status after Facebook login
    if (window.location.search.includes('facebook') || document.referrer.includes('facebook.com')) {
        setTimeout(() => {
        this.loadFacebookStatus();
        }, 1000);
    }

    await this.loadProperties();

    this.setupEventListeners();
    }

    // Fetch Facebook connection status
    async loadFacebookStatus() {
    try {
        const response = await fetch('/api/facebook/config', {
        headers: {
            'Authorization': `Bearer ${dashboardCore.getAuthToken()}`
        }
        });

        if (response.ok) {
        const data = await response.json();
        this.facebookConfig = data;
        this.updateFacebookUI();
        } else {
        this.facebookConfig = { connected: false };
        this.updateFacebookUI();
        }
    } catch {
        this.facebookConfig = { connected: false };
        this.updateFacebookUI();
    }
    }

    // Update Facebook status UI
    updateFacebookUI() {
    const statusBar = document.getElementById('facebook-status');
    const statusText = document.getElementById('facebook-status-text');
    const connectBtn = document.getElementById('facebook-connect-btn');
    const fbBody = document.getElementById('facebook-integration-body');

    if (this.facebookConfig?.connected) {
        statusBar.className = 'alert alert-success mb-3';
        statusText.innerHTML = `✅ Connected to Facebook page <strong>${this.facebookConfig.page_name}</strong>`;
        connectBtn.style.display = 'none';

        fbBody.innerHTML = `
        <div class="text-center">
            <i class="fab fa-facebook fa-2x mb-2 text-primary"></i>
            <p>Connected to ${this.facebookConfig.page_name}</p>
            <button class="btn btn-danger btn-sm" onclick="smartProperties.disconnectFacebook()">Disconnect</button>
            <button class="btn btn-secondary btn-sm ms-2" onclick="smartProperties.loadFacebookStatus()">Refresh</button>
        </div>
        `;
    } else {
        statusBar.className = 'alert alert-warning mb-3';
        statusText.textContent = '⚠️ Facebook not connected';
        connectBtn.style.display = 'inline-block';
        connectBtn.onclick = () => this.connectFacebook();

        fbBody.innerHTML = `
        <div class="text-center text-muted">
            <i class="fab fa-facebook fa-2x mb-2"></i>
            <p>Not connected. Connect to your Facebook page to post.</p>
            <button class="btn btn-primary" onclick="smartProperties.connectFacebook()">Connect Facebook</button>
            <button class="btn btn-secondary ms-2" onclick="smartProperties.loadFacebookStatus()">Refresh</button>
        </div>
        `;
    }

    statusBar.style.display = 'block';
    }

    // Connect Facebook
    connectFacebook() {
    const token = dashboardCore.getAuthToken();
    window.location.href = `/auth/facebook/login?token=${token}`;
    }

    // Disconnect Facebook (to implement)
    async disconnectFacebook() {
    try {
        const response = await fetch('/api/facebook/disconnect', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${dashboardCore.getAuthToken()}`
        }
        });
        if (response.ok) {
        this.facebookConfig = { connected: false };
        this.updateFacebookUI();
        dashboardCore.showToast('success', 'Disconnected', 'Facebook integration disconnected');
        } else {
        dashboardCore.showToast('error', 'Error', 'Failed to disconnect Facebook');
        }
    } catch {
        dashboardCore.showToast('error', 'Error', 'Failed to disconnect Facebook');
    }
    }

 
    setupEventListeners() {
    // Form input listeners for live preview
    const form = document.getElementById('smart-property-form');
    if (form) {
        // Listen to all form inputs for live preview
        form.addEventListener('input', () => this.updateLivePreview());
        form.addEventListener('change', () => this.updateLivePreview());
    }

    // Feature checkboxes
    const featureCheckboxes = document.querySelectorAll('#features-container input[type="checkbox"]');
    featureCheckboxes.forEach(cb => {
        cb.addEventListener('change', () => {
            this.updateSelectedFeatures();
            this.updateLivePreview(); // Trigger preview update
        });
    });

    // Custom feature button
    const addFeatureBtn = document.getElementById('add-custom-feature-btn');
    if (addFeatureBtn) {
        addFeatureBtn.addEventListener('click', () => this.addCustomFeature());
    }

    // Tone and language changes should also trigger preview
    const toneSelect = document.getElementById('post-tone');
    const languageSelect = document.getElementById('post-language');
    if (toneSelect) {
        toneSelect.addEventListener('change', () => this.updateLivePreview());
    }
    if (languageSelect) {
        languageSelect.addEventListener('change', () => this.updateLivePreview());
    }

    // Button event listeners
    const createAndPostBtn = document.getElementById('create-and-post-btn');
    if (createAndPostBtn) {
        createAndPostBtn.addEventListener('click', () => this.createAndPost());
    }

    const createOnlyBtn = document.getElementById('create-only-btn');
    if (createOnlyBtn) {
        createOnlyBtn.addEventListener('click', () => this.createProperty());
    }
}


    setupFeatureCheckboxListeners() {
    const featureCheckboxes = document.querySelectorAll('#features-container input[type="checkbox"]');
    featureCheckboxes.forEach(cb => {
        cb.addEventListener('change', () => this.updateSelectedFeatures());
    });
    }

    // Update selected features tags UI
    updateSelectedFeatures() {
    const container = document.getElementById('selected-features');
    if (!container) return; // Safeguard: only update if element exists
    const features = this.getSelectedFeatures();
    container.innerHTML = features.map(f => `<span class="badge bg-primary me-1">${f} <i class="fas fa-times" onclick="smartProperties.removeFeature('${f}')"></i></span>`).join('');
    this.updateLivePreview();
    }

    removeFeature(feature) {
    const cb = Array.from(document.querySelectorAll('#features-container input[type="checkbox"]'))
        .find(c => c.value === feature);
    if (cb) {
        cb.checked = false;
        this.updateSelectedFeatures();
    }
    // Also remove custom feature badges:
    this.removeCustomFeature(feature);
    }

    addCustomFeature() {
    const input = document.getElementById('custom-feature-input');
    const feature = input.value.trim();
    if (!feature) return;
    const container = document.getElementById('selected-features');
    // Prevent duplicates
    const existing = Array.from(container.querySelectorAll('span')).some(span => span.textContent.includes(feature));
    if (!existing) {
        container.innerHTML += `<span class="badge bg-success me-1">${feature} <i class="fas fa-times" onclick="smartProperties.removeCustomFeature('${feature}')"></i></span>`;
    }
    input.value = '';
    this.updateLivePreview();
    }

    removeCustomFeature(feature) {
    const badges = Array.from(document.querySelectorAll('#selected-features .badge.bg-success'));
    badges.forEach(badge => {
        if (badge.textContent.includes(feature)) badge.remove();
    });
    this.updateLivePreview();
    }

    getSelectedFeatures() {
    const features = [];
    const checkedFeatures = Array.from(document.querySelectorAll('#features-container input[type="checkbox"]:checked'));
    checkedFeatures.forEach(f => features.push(f.value));

    const customBadges = Array.from(document.querySelectorAll('#selected-features .badge.bg-success'));
    customBadges.forEach(custom => {
        const text = custom.textContent.replace('×', '').trim();
        if (text) features.push(text);
    });
    return features;
    }


async updateLivePreview() {
    const form = document.getElementById('smart-property-form');
    if (!form) return;

    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    const features = this.getSelectedFeatures();

    console.log('Form data:', data); // Debug log
    
    // More flexible validation - only require address and property type
    if (!data.address || !data.property_type) {
        const preview = document.getElementById('live-preview');
        if (preview) {
            preview.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-magic fa-3x mb-3 text-primary opacity-50"></i>
                    <h6>Almost There!</h6>
                    <p class="mb-0">Add address and property type to see the magic ✨</p>
                </div>
            `;
        }
        return;
    }

    // Show loading state
    const preview = document.getElementById('live-preview');
    if (preview) {
        preview.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-spinner fa-spin fa-2x text-primary mb-3"></i>
                <h6>AI is working its magic...</h6>
                <p class="mb-0">Generating amazing content for your property</p>
            </div>
        `;
    }

    try {
        // Get current tone and language
        const tone = document.getElementById('post-tone')?.value || 'Professional';
        const language = document.getElementById('post-language')?.value || 'English';

        console.log('Sending request to API...'); // Debug log

        // Build request payload with fallbacks
        const payload = {
            address: data.address,
            city: "Mumbai",
            state: "Maharashtra", 
            price: data.price || "Price on Request", // Fallback for empty price
            property_type: data.property_type,
            bedrooms: parseInt(data.bedrooms) || 2,
            bathrooms: parseFloat(data.bathrooms) || 1,
            features: features,
            template: "just_listed",
            tone: tone,
            language: language
        };

        console.log('Request payload:', payload); // Debug log

        const response = await fetch('/api/listings/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${dashboardCore.getAuthToken()}`
            },
            body: JSON.stringify(payload)
        });

        console.log('API response status:', response.status); // Debug log
        console.log('Response headers:', response.headers); // Debug log

        if (!response.ok) {
            const errorText = await response.text();
            console.error('API error response:', errorText);
            throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        console.log('API result:', result); // Debug log

        this.currentGeneratedContent = result;

        // Update preview with generated content
        if (preview) {
            preview.innerHTML = `
                <div class="preview-content">
                    <div class="d-flex align-items-center justify-content-between mb-3">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-robot fa-fw me-2 text-primary"></i>
                            <small class="text-muted fw-bold">AI Generated Content</small>
                        </div>
                        <span class="badge bg-success">Live Preview</span>
                    </div>
                    <div class="preview-text p-3 border-start border-4 border-primary bg-light rounded" style="white-space: pre-wrap;">
                        ${result.caption || "No caption generated"}
                    </div>
                    <div class="mt-3">
                        <small class="text-primary fw-bold">${(result.hashtags || []).join(' ')}</small>
                    </div>
                    ${!data.price ? '<div class="mt-2"><small class="text-warning"><i class="fas fa-info-circle"></i> Add price for better results</small></div>' : ''}
                </div>
            `;
        }

        // Show posting options
        const postingOptions = document.getElementById('posting-options');
        if (postingOptions) {
            postingOptions.style.display = 'block';
        }

    } catch (error) {
        console.error('Preview generation error:', error);
        if (preview) {
            preview.innerHTML = `
                <div class="text-center text-danger py-4">
                    <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
                    <h6>Oops! Magic failed</h6>
                    <p class="mb-0">Error: ${error.message}</p>
                    <button class="btn btn-sm btn-outline-primary mt-2" onclick="smartProperties.updateLivePreview()">
                        <i class="fas fa-redo"></i> Try Again
                    </button>
                </div>
            `;
        }
    }
}



async generatePostVariation(data, features, tone, language, template) {
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
            bedrooms: parseInt(data.bedrooms) || 0,
            bathrooms: parseFloat(data.bathrooms) || 0,
            features: features,
            template: template,
            tone: tone,
            language: language
        })
    });
    
    return response.ok ? await response.json() : null;
}

displayPostVariations(variations) {
    const container = document.getElementById('variations-container');
    if (!container) return;
    
    container.innerHTML = variations.filter(v => v).map((variation, index) => `
        <div class="card mb-2 variation-card" data-index="${index}">
            <div class="card-body p-2">
                <div class="form-check">
                    <input class="form-check-input" type="radio" name="post-variation" 
                           id="variation-${index}" ${index === 0 ? 'checked' : ''}>
                    <label class="form-check-label small" for="variation-${index}">
                        ${variation.caption.substring(0, 80)}...
                    </label>
                </div>
            </div>
        </div>
    `).join('');
    
    // Store variations for later use
    this.postVariations = variations;
    
    // Add click handlers to update preview
    container.querySelectorAll('input[name="post-variation"]').forEach((radio, index) => {
        radio.addEventListener('change', () => {
            if (radio.checked) {
                this.updatePreviewWithVariation(variations[index]);
            }
        });
    });
}

updatePreviewWithVariation(variation) {
    const preview = document.getElementById('live-preview');
    if (preview && variation) {
        preview.innerHTML = `
            <div class="preview-content">
                <div class="d-flex align-items-center mb-2">
                    <i class="fas fa-robot fa-fw me-2 text-primary"></i>
                    <small class="text-muted">AI-generated Content</small>
                </div>
                <div class="preview-text p-3 border-start border-4 border-primary" style="white-space: pre-wrap;">
                    ${variation.caption || ""}
                </div>
                <div class="mt-2">
                    <small>${(variation.hashtags || []).join(' ')}</small>
                </div>
            </div>
        `;
        this.currentGeneratedContent = variation;
    }
}
 
async createAndPost() {
    // Get the selected variation
    const selectedVariation = this.getSelectedVariation();
    
    const property = await this.createProperty();
    if (!property) return;
    
    const postToFacebook = document.getElementById('post-to-facebook')?.checked;
    
    if (postToFacebook && this.facebookConfig?.connected && selectedVariation) {
        const tone = document.getElementById('post-tone').value;
        const language = document.getElementById('post-language').value;
        
        await this.postVariationToFacebook(property, selectedVariation, tone, language);
    }
}

getSelectedVariation() {
    const selectedRadio = document.querySelector('input[name="post-variation"]:checked');
    if (selectedRadio && this.postVariations) {
        const index = parseInt(selectedRadio.dataset.index || selectedRadio.id.split('-')[1]);
        return this.postVariations[index];
    }
    return this.currentGeneratedContent;
}


    // Post property to Facebook using enhanced options
    async postPropertyToFacebook(property, tone, language) {
    try {
        // Generate message with backend AI (or local)
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
            features: property.features ? property.features.split(',') : [],
            template: "just_listed",
            tone: tone,
            language: language
        })
        });

        if (!response.ok) throw new Error('Failed to generate post content');

        const content = await response.json();

        // Post to Facebook
        const fbResponse = await fetch('/api/facebook/post', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${dashboardCore.getAuthToken()}`
        },
        body: JSON.stringify({
            property_id: property.id,
            tone: tone,
            language: language,
            message: content.caption + "\n\n" + (content.hashtags || []).join(' '),
            image_url: null  // Adjust to include image url if supported
        })
        });

        if (!fbResponse.ok) throw new Error('Failed to post to Facebook');

        const fbResult = await fbResponse.json();

        dashboardCore.showToast('success', 'Posted', `Facebook post created on ${fbResult.page_name}`);

        // Update UI stats or property list if you track posted status
        await this.loadProperties();

    } catch (err) {
        dashboardCore.showToast('error', 'Facebook Post Failed', err.message || 'Failed to post property');
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
    showCreateModal() {
        const modal = new bootstrap.Modal(document.getElementById('createPropertyModal'));
        modal.show();
        // Optionally, load Facebook status or reset form here if needed
        this.loadFacebookStatus();
    }

    async createProperty() {
    try {
        const propertyData = this.getPropertyFormData();
        
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
            
            return result; // Return the created property for use in createAndPost
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

}

// Initialize Smart Properties Component  
const smartProperties = new SmartPropertiesComponent();
