# 🧪 Test Data Attributes Guide

## **📋 Required Data Attributes for E2E Testing**

To ensure our Playwright tests work correctly, we need to add specific `data-testid` attributes to our components.

### **🏠 Main Layout Components**

```tsx
// Main content wrapper
<div data-testid="main-content">
  {/* Main content */}
</div>

// Navigation components
<nav data-testid="desktop-navigation">
  {/* Desktop nav */}
</nav>

<nav data-testid="mobile-navigation">
  {/* Mobile nav */}
</nav>

<button data-testid="mobile-menu-toggle">
  {/* Mobile menu button */}
</button>

// Navigation items
<button data-testid="nav-crm">CRM</button>
<button data-testid="nav-analytics">Analytics</button>
<button data-testid="nav-team-management">Team Management</button>
<button data-testid="mobile-nav-crm">CRM</button>
<button data-testid="mobile-nav-analytics">Analytics</button>
<button data-testid="mobile-nav-team-management">Team Management</button>
```

### **👥 CRM Component**

```tsx
// CRM Dashboard
<div data-testid="crm-dashboard">
  {/* CRM content */}
</div>

// Statistics section
<div data-testid="crm-stats">
  <div className="crm-stats-grid">
    {/* Stats cards */}
  </div>
</div>

// Search and filters
<div data-testid="crm-search">
  <input data-testid="search-input" placeholder="Search leads..." />
  <button data-testid="filters-button">Filters</button>
  <select data-testid="status-filter">
    {/* Status options */}
  </select>
</div>

// Leads list
<div data-testid="crm-leads-list">
  <div data-testid="lead-item">
    {/* Lead card */}
  </div>
</div>

// Lead actions
<button data-testid="lead-view-button">View</button>
<button data-testid="lead-edit-button">Edit</button>

// Lead detail modal
<div data-testid="lead-detail-modal">
  {/* Modal content */}
</div>

// Loading states
<div data-testid="loading-spinner" className="crm-spinner">
  {/* Loading spinner */}
</div>

<div data-testid="error-message">
  {/* Error message */}
</div>
```

### **📊 Analytics Component**

```tsx
// Analytics Dashboard
<div data-testid="analytics-dashboard">
  {/* Analytics content */}
</div>

// Metrics section
<div data-testid="analytics-metrics">
  <div data-testid="metrics-grid">
    <div data-testid="metric-card">
      {/* Metric card */}
    </div>
  </div>
</div>

// Charts section
<div data-testid="analytics-charts">
  <div data-testid="charts-grid">
    <div data-testid="chart-container">
      {/* Chart */}
    </div>
  </div>
</div>

// Status breakdown
<div data-testid="analytics-status-breakdown">
  {/* Status breakdown */}
</div>

// Period selector
<select data-testid="period-selector">
  {/* Period options */}
</select>
```

### **👥 Team Management Component**

```tsx
// Team Management Dashboard
<div data-testid="team-management">
  {/* Team management content */}
</div>

// Team statistics
<div data-testid="team-stats">
  {/* Team stats */}
</div>

// Team members list
<div data-testid="team-members-list">
  <div data-testid="team-member-item">
    {/* Team member card */}
  </div>
</div>

// Member actions
<select data-testid="member-role-select">
  {/* Role options */}
</select>

// Invite member
<button data-testid="invite-member-button">Invite Member</button>

// Invite modal
<div data-testid="invite-modal">
  <input data-testid="invite-email" />
  <select data-testid="invite-role">
    {/* Role options */}
  </select>
  <button data-testid="modal-close">Close</button>
</div>

// Success/Error messages
<div data-testid="success-message">
  {/* Success message */}
</div>
```

### **📱 Responsive Design**

```tsx
// Mobile navigation
<nav data-testid="mobile-navigation">
  <div data-testid="mobile-nav-item">CRM</div>
  <div data-testid="mobile-nav-item">Analytics</div>
  <div data-testid="mobile-nav-item">Team Management</div>
</nav>

// Tablet navigation
<nav data-testid="tablet-navigation">
  {/* Tablet nav */}
</nav>

// Mobile menu toggle
<button data-testid="mobile-menu-toggle">
  {/* Mobile menu button */}
</button>
```

### **🎨 CSS Classes for Visual Testing**

```tsx
// Glass morphism effects
<div className="crm-glass-card">
<div className="analytics-glass-card">
<div className="team-glass-card">

// Grid layouts
<div className="crm-stats-grid">
<div className="analytics-metrics-grid">
<div className="team-stats-grid">

// Animation classes
<div className="crm-spinner">
<div className="analytics-spinner">
<div className="team-spinner">

// Hover effects
<div className="crm-stat-card">
<div className="analytics-metric-card">
<div className="team-stat-card">
```

### **♿ Accessibility Attributes**

```tsx
// ARIA labels
<button aria-label="Add new lead">+</button>
<button aria-label="Filter leads">Filter</button>
<button aria-label="Search leads">Search</button>

// Form labels
<label htmlFor="search-input">Search leads</label>
<label htmlFor="status-filter">Filter by status</label>
<label htmlFor="invite-email">Email address</label>

// Role attributes
<main role="main">
<nav role="navigation">
<button role="button">
<select role="combobox">
```

### **🔧 Implementation Checklist**

- [ ] Add `data-testid` attributes to all major components
- [ ] Ensure consistent naming convention
- [ ] Add ARIA labels for accessibility
- [ ] Include loading and error states
- [ ] Add mobile-specific test IDs
- [ ] Include modal and overlay elements
- [ ] Add form input test IDs
- [ ] Include navigation elements
- [ ] Add success/error message test IDs
- [ ] Include responsive breakpoint elements

### **📝 Naming Convention**

- **Component**: `component-name` (e.g., `crm-dashboard`)
- **Element**: `element-type` (e.g., `search-input`, `filter-button`)
- **State**: `state-description` (e.g., `loading-spinner`, `error-message`)
- **Action**: `action-description` (e.g., `add-lead-button`, `invite-member-button`)
- **Mobile**: `mobile-element-name` (e.g., `mobile-nav-crm`)

This ensures our Playwright tests can reliably find and interact with elements across all components and screen sizes.