/**
 * Copy for /for-agents, the agent brochure. Plain and honest: no invented numbers, no testimonials. "MahaRERA verified" is said
 * only of the check we really make (onboarding/verification.py). Joining is open and free (2026-11-27): no trial, no offer and no
 * "first N agents", because every shared link shows the title and description. Kept apart from the page so tests can pin what
 * we promise.
 */
import { BRAND_NAME } from '@/lib/brand'

export const FOR_AGENTS = {
  metaTitle: `For agents: join the ${BRAND_NAME} network in Pune | Open and free`,
  metaDescription:
    `${BRAND_NAME} for real estate agents anywhere in Pune: your own page with your MahaRERA number checked on the register, posts and reels made for you, every enquiry as a lead card, and a lead board of Pune buyers you can ask for. Open and free to join.`,
  eyebrow: 'For real estate agents in Pune',
  pilot: 'Open and free to join',
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
      { title: 'Your listings, posted for you', body: `Posts and reels on ${BRAND_NAME}'s Instagram and Facebook with your name, after you approve each one, and a link and WhatsApp message to share yourself.` },
      { title: 'Leads in your inbox', body: 'Every buyer who taps interest or writes in arrives as a lead card in your studio, on your phone.' },
      { title: 'The Pune lead board', body: `Buyers who asked ${BRAND_NAME}, from across Pune: what they want, their budget band and the pages they read, with no name or number. Ask for the ones that fit you, free. The ${BRAND_NAME} team passes each buyer to one agent.` },
      { title: 'Your MahaRERA number, checked', body: 'We check your MahaRERA agent number on the register. Once it is checked, your page says "MahaRERA verified" and the lead board opens for you.' },
      { title: 'Weekly results', body: 'Each week: how many people viewed your homes, how many enquired, and what to do next.' },
    ],
  },
  cost: {
    heading: 'What it costs',
    title: 'Open and free to join',
    body: 'No card, and nothing to pay to join or to ask for a buyer on the lead board. If we ever charge for something, we tell you the price before anything changes, and you decide.',
  },
  coming: {
    heading: 'Set up with you',
    items: [
      'Your own WhatsApp number on your page, so buyer messages reach you directly.',
      'Your name, photo and MahaRERA number on your page and posts.',
    ],
    note: 'You can do it all yourself in a few minutes, and the guide at avasetu.in/for-agents/guide shows every step.',
  },
  trust: {
    heading: 'How we keep it honest',
    items: [
      'Nobody can pay for a higher place on the lead board.',
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
    heading: 'Join the network',
    body: 'For agents anywhere in Pune. Open avasetu.in/trial and send the sign-up word on WhatsApp: your sign-up code comes back at once. Then add your MahaRERA agent number, and we check it on the register.',
    button: 'Join free',
    demo: 'See a sample agent page',
    qr: 'Scan to join',
  },
} as const
