# Mobile-First Migration Guide

## Overview

This guide outlines the process for migrating to our new unified mobile-first design system.

## Key Changes

1. Consolidated mobile styles into `mobile-first-unified.css`
2. Implemented fluid typography using clamp()
3. Standardized touch targets (44px minimum)
4. Added mobile performance optimizations
5. Improved accessibility and dark mode support

## Migration Steps

### 1. Update Imports

Replace existing mobile CSS imports with the new unified file:

```css
@import "../styles/mobile-first-unified.css";
```

### 2. Component Updates

Update components to use new mobile-first classes:

#### Forms

```jsx
// Old
<input className="form-input" />

// New
<input className="form-input touch-target" />
```

#### Navigation

```jsx
// Old
<nav className="mobile-navigation">

// New
<nav className="mobile-nav">
  <div className="mobile-nav-items">
    <a className="mobile-nav-item">
```

#### Cards

```jsx
// Old
<div className="card mobile">

// New
<div className="mobile-card">
  <div className="mobile-card-header">
  <div className="mobile-card-content">
```

### 3. Typography

Use new fluid typography classes:

```jsx
<h1 className="text-h1">Title</h1>
<p className="text-body">Content</p>
```

### 4. Touch Targets

Ensure all interactive elements meet minimum touch target size:

```jsx
<button className="btn touch-target">
<input className="form-input touch-target">
```

### 5. Performance

Add performance classes where needed:

```jsx
<div className="use-gpu">Animated content</div>
<div className="optimize-paint">Frequently updated content</div>
```

## Testing Checklist

### Viewport Testing

- [ ] Test on 320px viewport
- [ ] Test on 375px viewport
- [ ] Test on 425px viewport
- [ ] Test on 768px tablet
- [ ] Verify safe areas on iOS

### Interaction Testing

- [ ] Verify touch targets are at least 44px
- [ ] Test all hover states
- [ ] Verify focus states are visible
- [ ] Test dark mode appearance
- [ ] Verify reduced motion preferences

### Performance Testing

- [ ] Check animation performance
- [ ] Verify scroll performance
- [ ] Test form input responsiveness
- [ ] Measure First Input Delay
- [ ] Verify no horizontal scroll

## Component Migration Priority

1. High Priority

   - Navigation components
   - Forms and inputs
   - Action buttons
   - List views

2. Medium Priority

   - Cards and containers
   - Typography
   - Icons and badges
   - Modals

3. Low Priority
   - Animations
   - Decorative elements
   - Legacy components

## Best Practices

1. Mobile-First Development

   - Start with mobile layout
   - Add complexity for larger screens
   - Use fluid units (rem, %, vw)

2. Performance

   - Minimize JS animations
   - Use GPU acceleration wisely
   - Implement lazy loading

3. Accessibility
   - Maintain color contrast
   - Provide touch targets
   - Support screen readers

## Common Issues and Solutions

### Issue: Text too small on mobile

```css
/* Avoid */
font-size: 12px;

/* Use */
font-size: clamp(0.875rem, 4vw, 1rem);
```

### Issue: Horizontal scroll

```css
/* Avoid */
width: 400px;

/* Use */
width: 100%;
max-width: 400px;
```

### Issue: Touch targets too small

```css
/* Avoid */
min-height: 32px;

/* Use */
min-height: var(--touch-target-size);
```

## Timeline

1. Week 1: High Priority Components

   - Update navigation
   - Convert forms
   - Fix critical touch targets

2. Week 2: Medium Priority Components

   - Implement card system
   - Update typography
   - Convert modals

3. Week 3: Low Priority & Testing
   - Update animations
   - Comprehensive testing
   - Performance optimization

## Support

For questions or issues during migration:

1. Check the component documentation
2. Review the testing checklist
3. Contact the UI team lead

## Monitoring and Metrics

Track these metrics during migration:

- Mobile viewport bugs
- Touch target violations
- Performance metrics
- Accessibility scores
