export interface BrandTheme {
  primary: string;
  secondary: string;
  accent: string;
}

const THEME_STORAGE_KEY = 'brand_theme';

export const defaultBrandTheme = (): BrandTheme => ({
  primary: '#3b82f6',
  secondary: '#64748b', 
  accent: '#10b981'
});

export const saveBrandTheme = (theme: BrandTheme): void => {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(theme));
  } catch (error) {
    console.warn('Failed to save brand theme:', error);
  }
};

export const loadBrandTheme = (): BrandTheme | null => {
  if (typeof window === 'undefined') return null;
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    return stored ? JSON.parse(stored) : null;
  } catch (error) {
    console.warn('Failed to load brand theme:', error);
    return null;
  }
};

export const applyBrandTheme = (theme: BrandTheme, persist: boolean = true): void => {
  if (typeof window === 'undefined') return;
  
  const root = document.documentElement;
  root.style.setProperty('--brand-primary', theme.primary);
  root.style.setProperty('--brand-secondary', theme.secondary);
  root.style.setProperty('--brand-accent', theme.accent);
  
  console.log('Applied brand theme:', theme);
  console.log('CSS variables set:', {
    primary: root.style.getPropertyValue('--brand-primary'),
    secondary: root.style.getPropertyValue('--brand-secondary'),
    accent: root.style.getPropertyValue('--brand-accent')
  });
  
  if (persist) {
    saveBrandTheme(theme);
  }
};

export const initializeBrandTheme = (): void => {
  if (typeof window === 'undefined') return;
  
  const savedTheme = loadBrandTheme();
  if (savedTheme) {
    console.log('Loading saved brand theme:', savedTheme);
    applyBrandTheme(savedTheme, false); // Don't re-save when initializing
  } else {
    console.log('No saved theme found, using default');
    applyBrandTheme(defaultBrandTheme(), false);
  }
};

export const clearBrandTheme = (): void => {
  if (typeof window === 'undefined') return;
  try {
    localStorage.removeItem(THEME_STORAGE_KEY);
    applyBrandTheme(defaultBrandTheme(), false);
  } catch (error) {
    console.warn('Failed to clear brand theme:', error);
  }
};

export const getBrandTheme = (): BrandTheme => {
  const root = document.documentElement;
  const computedStyle = getComputedStyle(root);
  
  return {
    primary: computedStyle.getPropertyValue('--brand-primary') || defaultBrandTheme().primary,
    secondary: computedStyle.getPropertyValue('--brand-secondary') || defaultBrandTheme().secondary,
    accent: computedStyle.getPropertyValue('--brand-accent') || defaultBrandTheme().accent
  };
};