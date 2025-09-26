# PropertyAI Design System

A comprehensive, Google-level centralized design system built with modern CSS and accessibility in mind.

## Overview

This design system provides a complete set of design tokens, components, and utilities that ensure consistency, accessibility, and maintainability across the PropertyAI application.

## Architecture

### Core Principles
- **Atomic Design**: Components are built using atomic design principles
- **Accessibility First**: All components meet WCAG 2.1 AA standards
- **Mobile First**: Responsive design with mobile-first approach
- **Performance**: Optimized for speed and efficiency
- **Maintainability**: Centralized tokens and consistent patterns

### File Structure
```
styles/
├── design-system.css      # Main design system file
├── design-tokens.css      # Design tokens and variables
├── typography.css         # Typography system
├── colors.css            # Color system
├── spacing.css           # Spacing system
├── components.css        # Component system
├── mobile.css           # Mobile-specific styles
└── README.md            # This documentation
```

## Design Tokens

### Typography Scale
- **Display**: Large (56px), Medium (45px), Small (36px)
- **Headline**: Large (32px), Medium (28px), Small (24px)
- **Title**: Large (22px), Medium (16px), Small (14px)
- **Label**: Large (14px), Medium (12px), Small (11px)
- **Body**: Large (16px), Medium (14px), Small (12px)

### Color System
- **Primary**: Blue scale (50-950)
- **Secondary**: Purple scale (50-950)
- **Tertiary**: Green scale (50-950)
- **Neutral**: Gray scale (50-950)
- **Semantic**: Success, Warning, Error, Info

### Spacing Scale
- **8px Grid System**: 0, 1px, 2px, 4px, 6px, 8px, 10px, 12px, 14px, 16px, 20px, 24px, 28px, 32px, 36px, 40px, 44px, 48px, 52px, 56px, 60px, 64px, 72px, 80px, 96px

### Border Radius
- **xs**: 2px, **sm**: 4px, **md**: 6px, **lg**: 8px, **xl**: 12px, **2xl**: 16px, **3xl**: 24px, **full**: 9999px

### Shadows
- **xs**: Subtle shadow, **sm**: Small shadow, **md**: Medium shadow, **lg**: Large shadow, **xl**: Extra large shadow, **2xl**: Maximum shadow

## Components

### Buttons
```css
.btn                    /* Base button */
.btn-primary           /* Primary button */
.btn-secondary         /* Secondary button */
.btn-outline           /* Outline button */
.btn-ghost             /* Ghost button */
.btn-success           /* Success button */
.btn-warning           /* Warning button */
.btn-error             /* Error button */

/* Sizes */
.btn-sm                /* Small button */
.btn-md                /* Medium button */
.btn-lg                /* Large button */
.btn-xl                /* Extra large button */
```

### Cards
```css
.card                  /* Base card */
.card-elevated         /* Elevated card */
.card-flat             /* Flat card */
.card-glass            /* Glass morphism card */
.card-interactive      /* Interactive card */
```

### Forms
```css
.form-group            /* Form group container */
.form-label            /* Form label */
.form-input            /* Text input */
.form-textarea         /* Textarea */
.form-select           /* Select dropdown */
.form-error            /* Error message */
.form-help             /* Help text */
```

### Layout
```css
.container             /* Container */
.grid                  /* Grid container */
.grid-cols-1           /* 1 column grid */
.grid-cols-2           /* 2 column grid */
.grid-cols-3           /* 3 column grid */
.grid-cols-4           /* 4 column grid */
.grid-cols-5           /* 5 column grid */
.grid-cols-6           /* 6 column grid */
```

## Typography

### Display Typography
```css
.text-display-large    /* 56px display text */
.text-display-medium   /* 45px display text */
.text-display-small    /* 36px display text */
```

### Headline Typography
```css
.text-headline-large   /* 32px headline */
.text-headline-medium  /* 28px headline */
.text-headline-small   /* 24px headline */
```

### Title Typography
```css
.text-title-large      /* 22px title */
.text-title-medium     /* 16px title */
.text-title-small      /* 14px title */
```

### Body Typography
```css
.text-body-large       /* 16px body text */
.text-body-medium      /* 14px body text */
.text-body-small       /* 12px body text */
```

### Label Typography
```css
.text-label-large      /* 14px label */
.text-label-medium     /* 12px label */
.text-label-small      /* 11px label */
```

## Colors

### Text Colors
```css
.text-primary          /* Primary text color */
.text-secondary        /* Secondary text color */
.text-tertiary         /* Tertiary text color */
.text-disabled         /* Disabled text color */
.text-inverse          /* Inverse text color */
```

### Background Colors
```css
.bg-surface            /* Surface background */
.bg-surface-variant   /* Surface variant background */
.bg-surface-container  /* Surface container background */
```

### Brand Colors
```css
.text-brand-primary    /* Primary brand color */
.text-brand-secondary  /* Secondary brand color */
.text-brand-tertiary   /* Tertiary brand color */
```

### Semantic Colors
```css
.text-success          /* Success color */
.text-warning          /* Warning color */
.text-error            /* Error color */
.text-info             /* Info color */
```

## Spacing

### Padding
```css
.p-0, .p-1, .p-2, .p-3, .p-4, .p-5, .p-6, .p-8, .p-10, .p-12, .p-16, .p-20, .p-24, .p-32, .p-40, .p-48, .p-56, .p-64, .p-72, .p-80, .p-96
```

### Margin
```css
.m-0, .m-1, .m-2, .m-3, .m-4, .m-5, .m-6, .m-8, .m-10, .m-12, .m-16, .m-20, .m-24, .m-32, .m-40, .m-48, .m-56, .m-64, .m-72, .m-80, .m-96
```

### Gap
```css
.gap-0, .gap-1, .gap-2, .gap-3, .gap-4, .gap-5, .gap-6, .gap-8, .gap-10, .gap-12, .gap-16, .gap-20, .gap-24, .gap-32, .gap-40, .gap-48, .gap-56, .gap-64, .gap-72, .gap-80, .gap-96
```

## Responsive Design

### Breakpoints
- **xs**: 0px
- **sm**: 640px
- **md**: 768px
- **lg**: 1024px
- **xl**: 1280px
- **2xl**: 1536px

### Responsive Utilities
```css
.sm:grid-cols-2        /* 2 columns on small screens */
.md:grid-cols-3        /* 3 columns on medium screens */
.lg:grid-cols-4        /* 4 columns on large screens */
```

## Accessibility

### Focus Management
- All interactive elements have visible focus indicators
- Focus rings use high contrast colors
- Keyboard navigation is fully supported

### Screen Reader Support
```css
.sr-only               /* Screen reader only content */
.not-sr-only          /* Not screen reader only */
```

### High Contrast Mode
- Automatic detection of high contrast preferences
- Enhanced contrast ratios for better visibility
- Improved shadow and border visibility

### Reduced Motion
- Respects user's motion preferences
- Smooth animations for users who want them
- Static alternatives for users who don't

## Dark Mode

### Automatic Detection
- Respects system preference
- Smooth transitions between modes
- Consistent color relationships

### Dark Mode Classes
```css
.dark                  /* Dark mode container */
.dark .text-primary    /* Dark mode text */
.dark .bg-surface      /* Dark mode background */
```

## Performance

### Optimizations
- CSS custom properties for efficient theming
- Minimal CSS bundle size
- Optimized animations with `will-change`
- Efficient selectors and specificity

### Loading States
```css
.loading-skeleton      /* Skeleton loading animation */
.animate-pulse         /* Pulse animation */
.animate-spin          /* Spin animation */
```

## Browser Support

### Modern Browsers
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Features
- CSS Grid
- CSS Custom Properties
- CSS Container Queries
- CSS Logical Properties
- Backdrop Filter

## Usage Examples

### Button
```html
<button class="btn btn-primary btn-lg">
  Primary Button
</button>
```

### Card
```html
<div class="card card-elevated">
  <div class="card-header">
    <h3 class="text-title-large">Card Title</h3>
  </div>
  <div class="card-body">
    <p class="text-body-medium">Card content goes here.</p>
  </div>
</div>
```

### Form
```html
<div class="form-group">
  <label class="form-label">Email</label>
  <input type="email" class="form-input" placeholder="Enter your email">
  <div class="form-help">We'll never share your email.</div>
</div>
```

### Grid Layout
```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <div class="card">Item 1</div>
  <div class="card">Item 2</div>
  <div class="card">Item 3</div>
</div>
```

## Migration Guide

### From Old System
1. Replace hard-coded colors with design tokens
2. Use semantic spacing classes
3. Implement proper typography scale
4. Add accessibility features
5. Test across all breakpoints

### Best Practices
1. Use semantic class names
2. Follow the 8px grid system
3. Implement proper focus management
4. Test with screen readers
5. Validate color contrast ratios

## Contributing

### Adding New Components
1. Follow atomic design principles
2. Include accessibility features
3. Add responsive behavior
4. Document usage examples
5. Test across browsers

### Modifying Tokens
1. Update all related components
2. Test dark mode compatibility
3. Verify accessibility standards
4. Update documentation
5. Test performance impact

## Resources

### Design Tools
- Figma design system
- Color contrast checker
- Accessibility testing tools
- Performance monitoring

### Documentation
- Component library
- Style guide
- Usage examples
- Best practices

---

This design system is continuously evolving to meet the needs of modern web applications while maintaining the highest standards of accessibility, performance, and user experience.