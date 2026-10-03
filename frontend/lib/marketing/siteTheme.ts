import type React from 'react'

/** The agent-site colour variables (see lib/site/theme.ts themeVars) set to Avasetu's navy and gold, for the agent-site
 *  components (project and listing cards, the MahaRERA box, the enquiry form) when they appear on Avasetu's own pages. */
export const AVASETU_SITE_VARS = {
  '--site-primary': '#0f2340', '--site-on-primary': '#ffffff',
  '--site-secondary': '#0f2340', '--site-on-secondary': '#ffffff',
  '--site-accent': '#f0b440', '--site-on-accent': '#0f2340', '--site-accent-text': '#9a5b00',
  '--site-radius': '0.75rem',
} as React.CSSProperties
