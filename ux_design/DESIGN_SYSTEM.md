# Real Estate AI CRM - Design System & Component Library

## 🎨 Design System Foundation

### Brand Identity
```
Brand Values:
- Trust & Reliability
- Innovation & Intelligence  
- Simplicity & Efficiency
- Growth & Success
- Indian Market Focus

Visual Personality:
- Professional yet approachable
- Modern and tech-forward
- Clean and organized
- Energetic and optimistic
- Culturally relevant
```

## 🎯 Color System

### Primary Palette
```css
/* Primary Colors */
--primary-50: #EFF6FF;   /* Light backgrounds */
--primary-100: #DBEAFE;  /* Subtle accents */
--primary-200: #BFDBFE;  /* Disabled states */
--primary-300: #93C5FD;  /* Borders */
--primary-400: #60A5FA;  /* Hover states */
--primary-500: #3B82F6;  /* Primary brand */
--primary-600: #2563EB;  /* Primary actions */
--primary-700: #1D4ED8;  /* Active states */
--primary-800: #1E40AF;  /* Dark mode */
--primary-900: #1E3A8A;  /* Dark accents */

/* Success Colors */
--success-50: #ECFDF5;
--success-100: #D1FAE5;
--success-500: #10B981;  /* Success actions */
--success-600: #059669;  /* Success hover */
--success-700: #047857;  /* Success active */

/* Warning Colors */
--warning-50: #FFFBEB;
--warning-100: #FEF3C7;
--warning-500: #F59E0B;  /* Warning actions */
--warning-600: #D97706;  /* Warning hover */
--warning-700: #B45309;  /* Warning active */

/* Error Colors */
--error-50: #FEF2F2;
--error-100: #FEE2E2;
--error-500: #EF4444;    /* Error actions */
--error-600: #DC2626;    /* Error hover */
--error-700: #B91C1C;    /* Error active */

/* Neutral Colors */
--gray-50: #F9FAFB;      /* Light backgrounds */
--gray-100: #F3F4F6;     /* Card backgrounds */
--gray-200: #E5E7EB;     /* Borders */
--gray-300: #D1D5DB;     /* Disabled elements */
--gray-400: #9CA3AF;     /* Placeholder text */
--gray-500: #6B7280;     /* Secondary text */
--gray-600: #4B5563;     /* Body text */
--gray-700: #374151;     /* Headings */
--gray-800: #1F2937;     /* Dark headings */
--gray-900: #111827;     /* Emphasis text */
```

### Semantic Colors
```css
/* Lead Priority Colors */
--lead-hot: #EF4444;      /* Hot leads - Red */
--lead-warm: #F59E0B;     /* Warm leads - Orange */
--lead-cold: #3B82F6;     /* Cold leads - Blue */
--lead-new: #8B5CF6;      /* New leads - Purple */

/* Source Colors */
--facebook: #1877F2;      /* Facebook blue */
--instagram: #E4405F;     /* Instagram pink */
--whatsapp: #25D366;      /* WhatsApp green */
--website: #2563EB;       /* Website blue */
--phone: #F59E0B;         /* Phone orange */
--referral: #8B5CF6;      /* Referral purple */

/* Status Colors */
--status-active: #10B981;    /* Active/Online */
--status-inactive: #6B7280;  /* Inactive/Offline */
--status-pending: #F59E0B;   /* Pending/Processing */
--status-error: #EF4444;     /* Error/Failed */
```

## 📝 Typography System

### Font Families
```css
/* Primary Font - Inter */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Secondary Font - Poppins */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

:root {
  --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  --font-secondary: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  --font-mono: 'Fira Code', 'Monaco', 'Cascadia Code', monospace;
}
```

### Typography Scale
```css
/* Typography Scale */
--text-xs: 0.75rem;      /* 12px - Captions, labels */
--text-sm: 0.875rem;     /* 14px - Small text, metadata */
--text-base: 1rem;       /* 16px - Body text */
--text-lg: 1.125rem;     /* 18px - Large body text */
--text-xl: 1.25rem;      /* 20px - Small headings */
--text-2xl: 1.5rem;      /* 24px - Section headings */
--text-3xl: 1.875rem;    /* 30px - Page headings */
--text-4xl: 2.25rem;     /* 36px - Display headings */
--text-5xl: 3rem;        /* 48px - Hero headings */

/* Line Heights */
--leading-tight: 1.25;   /* Tight line height */
--leading-normal: 1.5;   /* Normal line height */
--leading-relaxed: 1.625; /* Relaxed line height */
--leading-loose: 2;      /* Loose line height */

/* Font Weights */
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
--font-extrabold: 800;
```

### Typography Components
```css
/* Heading Styles */
.heading-1 {
  font-family: var(--font-secondary);
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  color: var(--gray-900);
  margin-bottom: 1rem;
}

.heading-2 {
  font-family: var(--font-secondary);
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
  color: var(--gray-800);
  margin-bottom: 0.75rem;
}

.heading-3 {
  font-family: var(--font-primary);
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-normal);
  color: var(--gray-700);
  margin-bottom: 0.5rem;
}

/* Body Text Styles */
.body-large {
  font-family: var(--font-primary);
  font-size: var(--text-lg);
  font-weight: var(--font-normal);
  line-height: var(--leading-relaxed);
  color: var(--gray-600);
}

.body-normal {
  font-family: var(--font-primary);
  font-size: var(--text-base);
  font-weight: var(--font-normal);
  line-height: var(--leading-normal);
  color: var(--gray-600);
}

.body-small {
  font-family: var(--font-primary);
  font-size: var(--text-sm);
  font-weight: var(--font-normal);
  line-height: var(--leading-normal);
  color: var(--gray-500);
}

/* Utility Text Styles */
.text-caption {
  font-family: var(--font-primary);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  line-height: var(--leading-normal);
  color: var(--gray-400);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.text-link {
  color: var(--primary-600);
  text-decoration: none;
  font-weight: var(--font-medium);
  transition: color 0.2s ease;
}

.text-link:hover {
  color: var(--primary-700);
  text-decoration: underline;
}
```

## 📏 Spacing System

### Spacing Scale
```css
/* Spacing Scale (based on 4px grid) */
--space-px: 1px;
--space-0: 0;
--space-1: 0.25rem;      /* 4px */
--space-2: 0.5rem;       /* 8px */
--space-3: 0.75rem;      /* 12px */
--space-4: 1rem;         /* 16px */
--space-5: 1.25rem;      /* 20px */
--space-6: 1.5rem;       /* 24px */
--space-8: 2rem;         /* 32px */
--space-10: 2.5rem;      /* 40px */
--space-12: 3rem;        /* 48px */
--space-16: 4rem;        /* 64px */
--space-20: 5rem;        /* 80px */
--space-24: 6rem;        /* 96px */
--space-32: 8rem;        /* 128px */

/* Component Spacing */
--spacing-component-xs: var(--space-2);  /* 8px */
--spacing-component-sm: var(--space-4);  /* 16px */
--spacing-component-md: var(--space-6);  /* 24px */
--spacing-component-lg: var(--space-8);  /* 32px */
--spacing-component-xl: var(--space-12); /* 48px */

/* Layout Spacing */
--spacing-layout-xs: var(--space-4);     /* 16px */
--spacing-layout-sm: var(--space-6);     /* 24px */
--spacing-layout-md: var(--space-8);     /* 32px */
--spacing-layout-lg: var(--space-12);    /* 48px */
--spacing-layout-xl: var(--space-16);    /* 64px */
```

## 🔲 Border Radius System

```css
/* Border Radius Scale */
--radius-none: 0;
--radius-sm: 0.125rem;    /* 2px */
--radius-base: 0.25rem;   /* 4px */
--radius-md: 0.375rem;    /* 6px */
--radius-lg: 0.5rem;      /* 8px */
--radius-xl: 0.75rem;     /* 12px */
--radius-2xl: 1rem;       /* 16px */
--radius-3xl: 1.5rem;     /* 24px */
--radius-full: 9999px;    /* Fully rounded */

/* Component Radius */
--radius-button: var(--radius-lg);
--radius-card: var(--radius-xl);
--radius-input: var(--radius-md);
--radius-badge: var(--radius-full);
--radius-avatar: var(--radius-full);
```

## 🌊 Shadow System

```css
/* Shadow Scale */
--shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
--shadow-base: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
--shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
--shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
--shadow-xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);

/* Colored Shadows */
--shadow-primary: 0 4px 14px 0 rgba(59, 130, 246, 0.15);
--shadow-success: 0 4px 14px 0 rgba(16, 185, 129, 0.15);
--shadow-warning: 0 4px 14px 0 rgba(245, 158, 11, 0.15);
--shadow-error: 0 4px 14px 0 rgba(239, 68, 68, 0.15);

/* Component Shadows */
--shadow-card: var(--shadow-sm);
--shadow-card-hover: var(--shadow-md);
--shadow-modal: var(--shadow-xl);
--shadow-dropdown: var(--shadow-lg);
--shadow-button: var(--shadow-xs);
--shadow-button-hover: var(--shadow-sm);
```

## 🔘 Button Components

### Button Variants
```css
/* Base Button */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-button);
  font-family: var(--font-primary);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  line-height: 1;
  text-decoration: none;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

/* Primary Button */
.btn-primary {
  background: var(--primary-600);
  color: white;
  box-shadow: var(--shadow-button);
}

.btn-primary:hover {
  background: var(--primary-700);
  box-shadow: var(--shadow-button-hover);
  transform: translateY(-1px);
}

.btn-primary:active {
  background: var(--primary-800);
  transform: translateY(0);
}

/* Secondary Button */
.btn-secondary {
  background: white;
  color: var(--primary-600);
  border-color: var(--primary-200);
  box-shadow: var(--shadow-button);
}

.btn-secondary:hover {
  background: var(--primary-50);
  border-color: var(--primary-300);
  box-shadow: var(--shadow-button-hover);
}

/* Success Button */
.btn-success {
  background: var(--success-600);
  color: white;
}

.btn-success:hover {
  background: var(--success-700);
}

/* Warning Button */
.btn-warning {
  background: var(--warning-500);
  color: white;
}

.btn-warning:hover {
  background: var(--warning-600);
}

/* Error Button */
.btn-error {
  background: var(--error-500);
  color: white;
}

.btn-error:hover {
  background: var(--error-600);
}

/* Ghost Button */
.btn-ghost {
  background: transparent;
  color: var(--gray-600);
  border: none;
}

.btn-ghost:hover {
  background: var(--gray-100);
  color: var(--gray-700);
}
```

### Button Sizes
```css
/* Button Sizes */
.btn-xs {
  padding: var(--space-1) var(--space-2);
  font-size: var(--text-xs);
}

.btn-sm {
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-sm);
}

.btn-md {
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-sm);
}

.btn-lg {
  padding: var(--space-4) var(--space-6);
  font-size: var(--text-base);
}

.btn-xl {
  padding: var(--space-5) var(--space-8);
  font-size: var(--text-lg);
}

/* Full Width Button */
.btn-full {
  width: 100%;
}

/* Loading State */
.btn-loading {
  position: relative;
  color: transparent;
}

.btn-loading::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: translate(-50%, -50%) rotate(360deg);
  }
}
```

## 📊 Card Components

### Base Card
```css
.card {
  background: white;
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.card:hover {
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
}

.card-body {
  padding: var(--spacing-component-md);
}

.card-header {
  padding: var(--spacing-component-md);
  border-bottom: 1px solid var(--gray-200);
}

.card-footer {
  padding: var(--spacing-component-md);
  border-top: 1px solid var(--gray-200);
  background: var(--gray-50);
}
```

### Lead Card Component
```css
.lead-card {
  background: white;
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-component-md);
  border-left: 4px solid var(--gray-200);
  transition: all 0.2s ease;
}

.lead-card:hover {
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
}

.lead-card.hot {
  border-left-color: var(--lead-hot);
}

.lead-card.warm {
  border-left-color: var(--lead-warm);
}

.lead-card.cold {
  border-left-color: var(--lead-cold);
}

.lead-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-3);
}

.lead-card-name {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--gray-800);
  margin: 0;
}

.lead-card-score {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.lead-card-details {
  display: grid;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.lead-card-property {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--gray-600);
}

.lead-card-actions {
  display: flex;
  gap: var(--space-2);
}
```

## 📝 Form Components

### Input Fields
```css
.form-group {
  margin-bottom: var(--spacing-component-sm);
}

.form-label {
  display: block;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--gray-700);
  margin-bottom: var(--space-2);
}

.form-input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-input);
  font-size: var(--text-base);
  color: var(--gray-700);
  background: white;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input:invalid {
  border-color: var(--error-500);
}

.form-input:disabled {
  background: var(--gray-100);
  color: var(--gray-400);
  cursor: not-allowed;
}

.form-error {
  display: block;
  font-size: var(--text-sm);
  color: var(--error-500);
  margin-top: var(--space-1);
}

.form-help {
  display: block;
  font-size: var(--text-sm);
  color: var(--gray-500);
  margin-top: var(--space-1);
}
```

### Select Components
```css
.form-select {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-input);
  font-size: var(--text-base);
  color: var(--gray-700);
  background: white url("data:image/svg+xml;charset=utf-8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><path fill='none' stroke='%23374151' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='m2 5 6 6 6-6'/></svg>") no-repeat right var(--space-3) center/16px 16px;
  appearance: none;
  cursor: pointer;
}

.form-select:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
```

## 🏷️ Badge Components

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  border-radius: var(--radius-badge);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.badge-primary {
  background: var(--primary-100);
  color: var(--primary-700);
}

.badge-success {
  background: var(--success-100);
  color: var(--success-700);
}

.badge-warning {
  background: var(--warning-100);
  color: var(--warning-700);
}

.badge-error {
  background: var(--error-100);
  color: var(--error-700);
}

.badge-gray {
  background: var(--gray-100);
  color: var(--gray-700);
}

/* Lead Status Badges */
.badge-hot {
  background: rgba(239, 68, 68, 0.1);
  color: var(--error-700);
}

.badge-warm {
  background: rgba(245, 158, 11, 0.1);
  color: var(--warning-700);
}

.badge-cold {
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary-700);
}
```

## 📱 Mobile Optimizations

### Touch Targets
```css
/* Minimum touch target size */
.touch-target {
  min-height: 44px;
  min-width: 44px;
}

/* Mobile-specific spacing */
@media (max-width: 768px) {
  .mobile-padding {
    padding: var(--space-4);
  }
  
  .mobile-gap {
    gap: var(--space-3);
  }
  
  .mobile-text {
    font-size: var(--text-base);
  }
  
  .mobile-button {
    padding: var(--space-4) var(--space-6);
    font-size: var(--text-base);
  }
}
```

### Responsive Utilities
```css
/* Responsive visibility */
.hidden-mobile {
  display: block;
}

.hidden-desktop {
  display: none;
}

@media (max-width: 768px) {
  .hidden-mobile {
    display: none;
  }
  
  .hidden-desktop {
    display: block;
  }
}

/* Responsive grid */
.grid-responsive {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-6);
}

@media (max-width: 768px) {
  .grid-responsive {
    grid-template-columns: 1fr;
    gap: var(--space-4);
  }
}
```

## 🎬 Animation System

### Transition Utilities
```css
.transition-fast {
  transition: all 0.15s ease;
}

.transition-normal {
  transition: all 0.2s ease;
}

.transition-slow {
  transition: all 0.3s ease;
}

/* Common animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(10px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes scaleIn {
  from { 
    opacity: 0;
    transform: scale(0.9);
  }
  to { 
    opacity: 1;
    transform: scale(1);
  }
}

.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}

.animate-slide-up {
  animation: slideUp 0.3s ease-out;
}

.animate-scale-in {
  animation: scaleIn 0.2s ease-out;
}
```

This comprehensive design system provides:
- **Consistent visual language** across all components
- **Mobile-first responsive design** principles
- **Accessibility-compliant** color contrasts and touch targets
- **Scalable component library** for development teams
- **Indian market-focused** design considerations
- **Performance-optimized** CSS with minimal bundle size

**Ready for UI developers to implement this world-class design system!** 🎨
