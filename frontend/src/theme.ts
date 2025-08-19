export type BrandTheme = {
  primary: string;
  secondary: string;
  accent: string;
};

export function applyBrandTheme(theme: BrandTheme) {
  const root = document.documentElement;
  root.style.setProperty('--brand-primary', theme.primary);
  root.style.setProperty('--brand-secondary', theme.secondary);
  root.style.setProperty('--brand-accent', theme.accent);
}

export function defaultBrandTheme(): BrandTheme {
  return { primary: '#0ea5e9', secondary: '#0f172a', accent: '#f59e0b' };
}

