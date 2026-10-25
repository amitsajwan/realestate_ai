import { BRAND_NAME, TEAM } from '@/lib/brand'

/** Copy for the public enquiry form's optional qualification block. */
export const QUALIFY_STRINGS = {
  // the block sits behind a closed disclosure so a phone reaches the send button right after name, mobile and consent
  more: 'Add budget, move-in or a note (optional)',
  hint: 'Skip anything you like. It only helps with better options.',
  message: 'Note',
  budget: 'Budget',
  timeline: 'Move in',
  financing: 'Payment',
  bhk: 'BHK',
  savedNote: "Thanks - we've noted your preferences.",
  savedNoteBudgetTimeline: "Thanks - we've noted your budget and timeline.",
}

/** The one main action on a project page (design review 2026-10-25 found five names for it). The hero, the ask box, the form's
 *  heading and its send button all say it; `short` is for the phone's bottom bar, where the full label would wrap. */
export const PROJECT_CTA = {
  full: 'Get price sheet & floor plans',
  short: 'Get price & plans',
  formTitle: (name: string) => `Get the price sheet and floor plans for ${name}`,
  /** the register project page's main action: the price sheet is the day's, which is why a buyer asks rather than reads */
  today: "Get today's price sheet & floor plans",
  /** its second action, and the site-visit form it opens */
  visit: 'Book a site visit',
  visitTitle: (name: string) => `Book a site visit to ${name}`,
  /** under the published prices: they are the sites', the offer of the day is the builder's */
  offer: 'Ask for the current offer',
}

/** Who the buyer is told will contact them. Enquiries to the house account are followed up by the team, and messages to leads are
 *  signed "Avasetu team" with no personal names, so the form says the same. An agent's own name is used as it is. */
export function contactName(agentName: string): string {
  return agentName === BRAND_NAME ? `the ${TEAM}` : agentName
}

/** The same name at the start of a sentence. */
export function contactNameStart(agentName: string): string {
  const n = contactName(agentName)
  return n.charAt(0).toUpperCase() + n.slice(1)
}

export function firstName(full: string): string {
  return (full || '').trim().split(/\s+/)[0] || 'the agent'
}
