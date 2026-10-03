/**
 * Copy for /for-agents, the agent brochure. Plain and honest: no invented numbers, no testimonials, no "verified" claims.
 * Kept apart from the page so tests can pin what we promise.
 */
import { BRAND_NAME } from '@/lib/brand'

export const FOR_AGENTS = {
  metaTitle: `For agents: what ${BRAND_NAME} does for you | Free pilot in Pune`,
  metaDescription:
    `${BRAND_NAME} for real estate agents in Pune: add a home from your phone, get designed posts, reels and your own branded page, and see every enquiry as a lead card with who to call first. Free during the pilot.`,
  eyebrow: 'For real estate agents in Pune',
  pilot: 'Free pilot, invite-only',
  title: 'Every enquiry in one place, and the right buyer to call first.',
  lead:
    `${BRAND_NAME} turns the homes you list into posts, reels and your own branded page, and turns every buyer who shows interest into a lead card you can act on.`,
  summaries: [
    { lang: 'hi', label: 'हिंदी', text: 'घर फ़ोन से जोड़ें, पोस्ट और आपका अपना पेज तैयार; हर पूछताछ एक लीड कार्ड में, ताकि आप सही खरीदार को पहले कॉल करें।' },
    { lang: 'mr', label: 'मराठी', text: 'फोनवरून घर जोडा, पोस्ट आणि तुमचं स्वतःचं पेज तयार; प्रत्येक चौकशी एका लीड कार्डवर, म्हणजे योग्य खरेदीदाराला आधी कॉल करा.' },
  ],
  problem: {
    heading: 'The problem every agent knows',
    items: [
      { title: 'Enquiries are scattered', body: 'Comments on posts, WhatsApp messages, missed calls. Nothing sits in one list.' },
      { title: 'Every enquiry looks the same', body: '"Price?" and "interested" tell you nothing about budget, BHK or when they want to move.' },
      { title: 'Follow-ups slip', body: 'The warm buyer gets a late reply while you chase the ones who were only browsing.' },
    ],
  },
  steps: {
    heading: 'What Avasetu does, in four steps',
    items: [
      { key: 'create', label: 'Create', title: 'Add a home from your phone', body: 'Photos and a few details. We fill in the listing for you to check before anything goes live.' },
      { key: 'attract', label: 'Attract', title: 'Posts, reels and your page', body: 'Designed posts, short reels with a Hindi voice-over, your own branded page, and a tap-to-show-interest link on every post.' },
      { key: 'qualify', label: 'Qualify', title: 'Every enquiry becomes a lead card', body: 'BHK, budget, timing and how warm the buyer is, in a few lines. Buyers tick a box to agree to be contacted.' },
      { key: 'close', label: 'Close', title: 'Call the right buyer first', body: 'Call or WhatsApp from the card, starting with the warmest buyer. You decide who to contact and when.' },
    ],
  },
  gets: {
    heading: 'What you get',
    items: [
      { title: 'Your own branded page', body: 'Your logo, your colours, your business name and your RERA agent number, with your homes and an enquiry form.' },
      { title: 'Your listings, posted for you', body: `Posts and reels on your own Instagram and Facebook Page, and on ${BRAND_NAME}'s, after you approve each one.` },
      { title: 'Leads in your inbox', body: 'Every buyer who taps interest or writes in arrives as a lead card in your studio, on your phone.' },
      { title: 'Weekly results', body: 'Each week: how many people viewed your homes, how many enquired, and what to do next.' },
    ],
  },
  cost: {
    heading: 'What it costs',
    title: 'Free during the pilot',
    body: 'No charge during the pilot. After it, Avasetu stays low-cost: a small monthly fee, not a big subscription. We tell you the price before anything changes.',
  },
  coming: {
    heading: 'Set up with you',
    items: [
      'Your own WhatsApp number connected, so buyer messages reach you directly.',
      'Your own Facebook Page and Instagram connected, so posts go out in your name.',
    ],
    note: 'We do the setup with you when you join: it takes one short call.',
  },
  trust: {
    heading: 'How we keep it honest',
    items: [
      'Nothing is sent to a buyer without you.',
      'Sample homes are always labelled as samples.',
      'No invented AI percentages or made-up numbers.',
      "Buyers' consent to be contacted is recorded.",
    ],
  },
  live: {
    heading: 'See it live',
    lead: 'Open these on your phone.',
  },
  cta: {
    heading: 'Request an invite',
    body: 'Places in the pilot are limited to agents in Pune. Your name and mobile number is all we need; we will get back to you.',
    button: 'Request an invite',
    demo: 'See a demo agent page',
    qr: 'Scan to request an invite',
  },
} as const
