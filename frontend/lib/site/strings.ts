/** Copy for the public enquiry form's optional qualification block. */
export const QUALIFY_STRINGS = {
  title: (agentFirstName: string) => `Help ${agentFirstName} find the right property (optional)`,
  hint: 'Skip anything you like. It only helps with better options.',
  budget: 'Budget',
  timeline: 'Move in',
  financing: 'Payment',
  bhk: 'BHK',
  savedNote: "Thanks - we've noted your preferences.",
  savedNoteBudgetTimeline: "Thanks - we've noted your budget and timeline.",
}

export function firstName(full: string): string {
  return (full || '').trim().split(/\s+/)[0] || 'the agent'
}
