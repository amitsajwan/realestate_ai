class SmartPropertiesComponent {
    constructor() {
    this.properties = [];
    this.currentProperty = null;
    this.facebookConfig = null;
    this.currentGeneratedContent = null;  // Stores latest AI-generated post preview
    }

    // Main HTML render for the component (partial)
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
                <div id="facebook-status" class="alert alert-info mb-3" style="display:none;">
                <i class="fab fa-facebook me-2"></i>
                <span id="facebook-status-text">Loading Facebook status...</span>
                <button id="facebook-connect-btn" class="btn btn-sm btn-outline-primary" style="display:none;">
                    Connect Facebook
                </button>
                </div>
                <div id="properties-grid" class="row"></div>
            </div>
            </div>
        </div>
        <div class="col-lg-4">
            <!-- stats and facebook integration panel -->
            <div class="modern-card card mb-3">
            <div class="card-header"><h6>📊 Stats</h6></div>
            <div class="card-body">
                <div>Total Properties: <span id="total-properties">0</span></div>
                <div>AI Generated: <span id="ai-generated">0</span></div>
                <div>Facebook Posts: <span id="posted-facebook">0</span></div>
            </div>
            </div>
            <div class="modern-card card">
            <div class="card-header"><h6>Facebook Integration</h6></div>
            <div class="card-body" id="facebook-integration-body">
                <div class="text-center text-muted" id="facebook-loading">
                <i class="fas fa-spinner fa-spin"></i> Loading Facebook status...
                </div>
            </div>
            </div>
        </div>

        <!-- Create Property Modal -->
        <div class="modal fade" id="createPropertyModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-xl">
            <div class="modal-content">
                <div class="modal-header">
                <h5 class="modal-title">🤖 Create Property</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                <form id="smart-property-form">
                    <div class="mb-3">
                    <label>Address *</label>
                    <input type="text" class="form-control" name="address" required />
                    </div>
                    <div class="mb-3">
                    <label>Price *</label>
                    <input type="text" class="form-control" name="price" required />
                    </div>
                    <div class="mb-3">
                    <label>Property Type *</label>
                    <select name="property_type" class="form-select" required>
                        <option value="">Select</option>
                        <option value="apartment">Apartment</option>
                        <option value="villa">Villa</option>
                        <option value="condo">Condo</option>
                        <option value="townhouse">Townhouse</option>
                        <option value="single_family">Single Family</option>
                    </select>
                    </div>
                    <!-- Bedrooms and Bathrooms -->
                    <div class="mb-3 d-flex gap-2">
                    <div class="w-50">
                        <label>Bedrooms *</label>
                        <input type="number" min="0" name="bedrooms" class="form-control" required />
                    </div>
                    <div class="w-50">
                        <label>Bathrooms *</label>
                        <input type="number" min="0" step="0.5" name="bathrooms" class="form-control" required />
                    </div>
                    </div>

                    <!-- Features -->
                    <div class="mb-3">
                    <label>Features</label>
                    <div id="features-container">
                        <label><input type="checkbox" value="Swimming Pool" /> Swimming Pool</label>
                        <label><input type="checkbox" value="Gym" /> Gym</label>
                        <label><input type="checkbox" value="Parking" /> Parking</label>
                        <label><input type="checkbox" value="Balcony" /> Balcony</label>
                        <label><input type="checkbox" value="Security" /> Security</label>
                        <label><input type="checkbox" value="Garden" /> Garden</label>
                        <!-- add more features here -->
                    </div>
                    <input type="text" id="custom-feature-input" placeholder="Add custom feature" class="form-control mt-2" />
                    <button type="button" id="add-custom-feature-btn" class="btn btn-secondary btn-sm mt-1">Add Feature</button>
                    </div>

                    <!-- AI Options -->
                    <div class="mb-3">
                    <div class="form-check form-switch">
                        <input type="checkbox" class="form-check-input" id="ai-generate" checked />
                        <label class="form-check-label" for="ai-generate">Auto-generate content with AI</label>
                    </div>
                    </div>

                    <!-- Post Tone and Language -->
                    <div class="mb-3 d-flex gap-2">
                    <select id="post-tone" class="form-select">
                        <option value="Professional">Professional</option>
                        <option value="Friendly">Friendly</option>
                        <option value="Luxurious">Luxurious</option>
                        <option value="Urgent">Urgent</option>
                    </select>
                    <select id="post-language" class="form-select">
                        <option value="English">English</option>
                        <option value="Hindi">Hindi</option>
                        <option value="Marathi">Marathi</option>
                    </select>
                    </div>

                    <!-- Buttons -->
                    <div class="mt-3 text-end">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-success" id="create-and-post-btn">Create & Post</button>
                    <button type="button" class="btn btn-primary" id="create-only-btn">Create Only</button>
                    </div>
                </form>
                </div>
            </div>
            </div>
        </div>
        </div>
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

    // Listen to form inputs and features selection
    setupEventListeners() {
    const form = document.getElementById('smart-property-form');
    if (form) {
        form.addEventListener('input', () => this.updateLivePreview());
        form.addEventListener('change', () => this.updateLivePreview());
    }
    document.getElementById('add-custom-feature-btn').addEventListener('click', () => this.addCustomFeature());
    this.setupFeatureCheckboxListeners();
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

    // Update live AI-generated preview
    async updateLivePreview() {
    const form = document.getElementById('smart-property-form');
    if (!form) return;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    const features = this.getSelectedFeatures();

    if (data.address && data.price && data.property_type) {
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
            bedrooms: parseInt(data.bedrooms) || 0,
            bathrooms: parseFloat(data.bathrooms) || 0,
            features: features,
            template: "just_listed",
            language: "en"
            })
        });

        if (!response.ok) throw new Error('Failed to generate preview');

        this.currentGeneratedContent = await response.json();

        const preview = document.getElementById('live-preview');
        preview.innerHTML = `
            <div class="preview-content">
            <div class="d-flex align-items-center mb-2">
                <i class="fas fa-robot fa-fw me-2 text-primary"></i>
                <small class="text-muted">AI-generated Content</small>
            </div>
            <div class="preview-text p-3 border-start border-4 border-primary" style="white-space: pre-wrap;">
                ${this.currentGeneratedContent.caption || ""}
            </div>
            <div class="mt-2"><small>${(this.currentGeneratedContent.hashtags || []).join(' ')}</small></div>
            </div>
        `;

        // Show posting options to post to Facebook etc
        document.getElementById('posting-options').style.display = 'block';

        } catch (error) {
        console.error('Preview generation error:', error);
        const preview = document.getElementById('live-preview');
        preview.innerHTML = `<div class="text-danger">Error generating preview...</div>`;
        }
    }
    }

    // Create property & optionally post to Facebook
    async createAndPost() {
    const postToFacebook = document.getElementById('post-tone') && document.getElementById('post-language');

    const property = await this.createProperty();
    if (!property) return;

    // If Facebook connected and post checked, send post request
    if (document.getElementById('post-tone') && document.getElementById('post-language')) {
        const tone = document.getElementById('post-tone').value;
        const language = document.getElementById('post-language').value;
        const postChecked = document.getElementById('post-facebook-checkbox')?.checked ?? true; // adjust as per checkbox control

        if (postChecked && this.facebookConfig?.connected) {
        await this.postPropertyToFacebook(property, tone, language);
        }
    }
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

}

// Initialize Smart Properties Component  
const smartProperties = new SmartPropertiesComponent();
