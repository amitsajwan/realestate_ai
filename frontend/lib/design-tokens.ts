/**
 * PropertyAI Design Tokens
 * TypeScript definitions for design system tokens
 */

export const designTokens = {
  // Typography
  typography: {
    fontFamily: {
      primary: 'var(--font-family-primary)',
      mono: 'var(--font-family-mono)',
      display: 'var(--font-family-display)',
    },
    fontSize: {
      'display-large': 'var(--text-display-large)',
      'display-medium': 'var(--text-display-medium)',
      'display-small': 'var(--text-display-small)',
      'headline-large': 'var(--text-headline-large)',
      'headline-medium': 'var(--text-headline-medium)',
      'headline-small': 'var(--text-headline-small)',
      'title-large': 'var(--text-title-large)',
      'title-medium': 'var(--text-title-medium)',
      'title-small': 'var(--text-title-small)',
      'label-large': 'var(--text-label-large)',
      'label-medium': 'var(--text-label-medium)',
      'label-small': 'var(--text-label-small)',
      'body-large': 'var(--text-body-large)',
      'body-medium': 'var(--text-body-medium)',
      'body-small': 'var(--text-body-small)',
    },
    lineHeight: {
      display: 'var(--line-height-display)',
      headline: 'var(--line-height-headline)',
      title: 'var(--line-height-title)',
      label: 'var(--line-height-label)',
      body: 'var(--line-height-body)',
      tight: 'var(--line-height-tight)',
      loose: 'var(--line-height-loose)',
    },
    fontWeight: {
      thin: 'var(--font-weight-thin)',
      extralight: 'var(--font-weight-extralight)',
      light: 'var(--font-weight-light)',
      normal: 'var(--font-weight-normal)',
      medium: 'var(--font-weight-medium)',
      semibold: 'var(--font-weight-semibold)',
      bold: 'var(--font-weight-bold)',
      extrabold: 'var(--font-weight-extrabold)',
      black: 'var(--font-weight-black)',
    },
  },

  // Colors
  colors: {
    primary: {
      50: 'var(--color-primary-50)',
      100: 'var(--color-primary-100)',
      200: 'var(--color-primary-200)',
      300: 'var(--color-primary-300)',
      400: 'var(--color-primary-400)',
      500: 'var(--color-primary-500)',
      600: 'var(--color-primary-600)',
      700: 'var(--color-primary-700)',
      800: 'var(--color-primary-800)',
      900: 'var(--color-primary-900)',
      950: 'var(--color-primary-950)',
    },
    secondary: {
      50: 'var(--color-secondary-50)',
      100: 'var(--color-secondary-100)',
      200: 'var(--color-secondary-200)',
      300: 'var(--color-secondary-300)',
      400: 'var(--color-secondary-400)',
      500: 'var(--color-secondary-500)',
      600: 'var(--color-secondary-600)',
      700: 'var(--color-secondary-700)',
      800: 'var(--color-secondary-800)',
      900: 'var(--color-secondary-900)',
      950: 'var(--color-secondary-950)',
    },
    tertiary: {
      50: 'var(--color-tertiary-50)',
      100: 'var(--color-tertiary-100)',
      200: 'var(--color-tertiary-200)',
      300: 'var(--color-tertiary-300)',
      400: 'var(--color-tertiary-400)',
      500: 'var(--color-tertiary-500)',
      600: 'var(--color-tertiary-600)',
      700: 'var(--color-tertiary-700)',
      800: 'var(--color-tertiary-800)',
      900: 'var(--color-tertiary-900)',
      950: 'var(--color-tertiary-950)',
    },
    neutral: {
      50: 'var(--color-neutral-50)',
      100: 'var(--color-neutral-100)',
      200: 'var(--color-neutral-200)',
      300: 'var(--color-neutral-300)',
      400: 'var(--color-neutral-400)',
      500: 'var(--color-neutral-500)',
      600: 'var(--color-neutral-600)',
      700: 'var(--color-neutral-700)',
      800: 'var(--color-neutral-800)',
      900: 'var(--color-neutral-900)',
      950: 'var(--color-neutral-950)',
    },
    semantic: {
      success: {
        50: 'var(--color-success-50)',
        100: 'var(--color-success-100)',
        200: 'var(--color-success-200)',
        300: 'var(--color-success-300)',
        400: 'var(--color-success-400)',
        500: 'var(--color-success-500)',
        600: 'var(--color-success-600)',
        700: 'var(--color-success-700)',
        800: 'var(--color-success-800)',
        900: 'var(--color-success-900)',
      },
      warning: {
        50: 'var(--color-warning-50)',
        100: 'var(--color-warning-100)',
        200: 'var(--color-warning-200)',
        300: 'var(--color-warning-300)',
        400: 'var(--color-warning-400)',
        500: 'var(--color-warning-500)',
        600: 'var(--color-warning-600)',
        700: 'var(--color-warning-700)',
        800: 'var(--color-warning-800)',
        900: 'var(--color-warning-900)',
      },
      error: {
        50: 'var(--color-error-50)',
        100: 'var(--color-error-100)',
        200: 'var(--color-error-200)',
        300: 'var(--color-error-300)',
        400: 'var(--color-error-400)',
        500: 'var(--color-error-500)',
        600: 'var(--color-error-600)',
        700: 'var(--color-error-700)',
        800: 'var(--color-error-800)',
        900: 'var(--color-error-900)',
      },
      info: {
        50: 'var(--color-info-50)',
        100: 'var(--color-info-100)',
        200: 'var(--color-info-200)',
        300: 'var(--color-info-300)',
        400: 'var(--color-info-400)',
        500: 'var(--color-info-500)',
        600: 'var(--color-info-600)',
        700: 'var(--color-info-700)',
        800: 'var(--color-info-800)',
        900: 'var(--color-info-900)',
      },
    },
    surface: {
      primary: 'var(--color-surface)',
      variant: 'var(--color-surface-variant)',
      container: 'var(--color-surface-container)',
      containerHigh: 'var(--color-surface-container-high)',
      containerHighest: 'var(--color-surface-container-highest)',
    },
    text: {
      primary: 'var(--color-text-primary)',
      secondary: 'var(--color-text-secondary)',
      tertiary: 'var(--color-text-tertiary)',
      disabled: 'var(--color-text-disabled)',
      inverse: 'var(--color-text-inverse)',
      inverseSecondary: 'var(--color-text-inverse-secondary)',
      inverseTertiary: 'var(--color-text-inverse-tertiary)',
    },
    border: {
      default: 'var(--color-border)',
      variant: 'var(--color-border-variant)',
      focus: 'var(--color-border-focus)',
      error: 'var(--color-border-error)',
      success: 'var(--color-border-success)',
      warning: 'var(--color-border-warning)',
    },
  },

  // Spacing
  spacing: {
    0: 'var(--space-0)',
    px: 'var(--space-px)',
    0.5: 'var(--space-0-5)',
    1: 'var(--space-1)',
    1.5: 'var(--space-1-5)',
    2: 'var(--space-2)',
    2.5: 'var(--space-2-5)',
    3: 'var(--space-3)',
    3.5: 'var(--space-3-5)',
    4: 'var(--space-4)',
    5: 'var(--space-5)',
    6: 'var(--space-6)',
    7: 'var(--space-7)',
    8: 'var(--space-8)',
    9: 'var(--space-9)',
    10: 'var(--space-10)',
    11: 'var(--space-11)',
    12: 'var(--space-12)',
    14: 'var(--space-14)',
    16: 'var(--space-16)',
    20: 'var(--space-20)',
    24: 'var(--space-24)',
    28: 'var(--space-28)',
    32: 'var(--space-32)',
    36: 'var(--space-36)',
    40: 'var(--space-40)',
    44: 'var(--space-44)',
    48: 'var(--space-48)',
    52: 'var(--space-52)',
    56: 'var(--space-56)',
    60: 'var(--space-60)',
    64: 'var(--space-64)',
    72: 'var(--space-72)',
    80: 'var(--space-80)',
    96: 'var(--space-96)',
  },

  // Border Radius
  borderRadius: {
    none: 'var(--radius-none)',
    xs: 'var(--radius-xs)',
    sm: 'var(--radius-sm)',
    md: 'var(--radius-md)',
    lg: 'var(--radius-lg)',
    xl: 'var(--radius-xl)',
    '2xl': 'var(--radius-2xl)',
    '3xl': 'var(--radius-3xl)',
    full: 'var(--radius-full)',
  },

  // Shadows
  boxShadow: {
    xs: 'var(--shadow-xs)',
    sm: 'var(--shadow-sm)',
    md: 'var(--shadow-md)',
    lg: 'var(--shadow-lg)',
    xl: 'var(--shadow-xl)',
    '2xl': 'var(--shadow-2xl)',
    inner: 'var(--shadow-inner)',
  },

  // Transitions
  transition: {
    none: 'var(--transition-none)',
    all: 'var(--transition-all)',
    colors: 'var(--transition-colors)',
    opacity: 'var(--transition-opacity)',
    shadow: 'var(--transition-shadow)',
    transform: 'var(--transition-transform)',
    fast: 'var(--transition-fast)',
    slow: 'var(--transition-slow)',
  },

  // Z-Index
  zIndex: {
    0: 'var(--z-index-0)',
    10: 'var(--z-index-10)',
    20: 'var(--z-index-20)',
    30: 'var(--z-index-30)',
    40: 'var(--z-index-40)',
    50: 'var(--z-index-50)',
    auto: 'var(--z-index-auto)',
    dropdown: 'var(--z-dropdown)',
    sticky: 'var(--z-sticky)',
    fixed: 'var(--z-fixed)',
    modal: 'var(--z-modal)',
    popover: 'var(--z-popover)',
    tooltip: 'var(--z-tooltip)',
  },

  // Breakpoints
  breakpoints: {
    xs: 'var(--breakpoint-xs)',
    sm: 'var(--breakpoint-sm)',
    md: 'var(--breakpoint-md)',
    lg: 'var(--breakpoint-lg)',
    xl: 'var(--breakpoint-xl)',
    '2xl': 'var(--breakpoint-2xl)',
  },

  // Touch Targets
  touchTarget: {
    min: 'var(--touch-target-min)',
    comfortable: 'var(--touch-target-comfortable)',
    large: 'var(--touch-target-large)',
  },

  // Focus Rings
  focusRing: {
    width: 'var(--focus-ring-width)',
    offset: 'var(--focus-ring-offset)',
    color: 'var(--focus-ring-color)',
    opacity: 'var(--focus-ring-opacity)',
  },
} as const;

// Type definitions for better TypeScript support
export type DesignTokens = typeof designTokens;
export type ColorScale = 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 | 950;
export type SpacingScale = keyof typeof designTokens.spacing;
export type TypographyScale = keyof typeof designTokens.typography.fontSize;
export type ShadowScale = keyof typeof designTokens.boxShadow;
export type BorderRadiusScale = keyof typeof designTokens.borderRadius;

// Utility functions for design tokens
export const getColor = (color: string, scale?: ColorScale) => {
  if (scale) {
    return `var(--color-${color}-${scale})`;
  }
  return `var(--color-${color})`;
};

export const getSpacing = (size: SpacingScale) => {
  return designTokens.spacing[size];
};

export const getTypography = (scale: TypographyScale) => {
  return designTokens.typography.fontSize[scale];
};

export const getShadow = (scale: ShadowScale) => {
  return designTokens.boxShadow[scale];
};

export const getBorderRadius = (scale: BorderRadiusScale) => {
  return designTokens.borderRadius[scale];
};