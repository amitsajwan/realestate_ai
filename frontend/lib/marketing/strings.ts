/** All English copy for the public pages (landing, invite request, legal). Plain language, no invented facts. */
import type { MarketingConfig } from './config'
import { BRAND_NAME, TAGLINE } from '@/lib/brand'

export const LEGAL_LAST_UPDATED_ISO = '2026-09-29'
export const LEGAL_LAST_UPDATED = '29 September 2026'
export const LEGAL_NOTICE =
  'This page is written in plain language to explain how the pilot works. It is not legal advice.'

export const PATHS = {
  home: '/',
  invite: '/request-invite',
  signIn: '/join',
  privacy: '/privacy',
  terms: '/terms',
  deletion: '/data-deletion',
} as const

export const NAV = {
  signIn: 'Sign in',
  requestInvite: 'Request an invite',
  primaryLabel: 'Main',
  footerLabel: 'Legal and help',
  legal: [
    { href: PATHS.privacy, label: 'Privacy' },
    { href: PATHS.terms, label: 'Terms' },
    { href: PATHS.deletion, label: 'Data deletion' },
  ],
}

export const FOOTER = {
  tagline: TAGLINE + '. A free pilot for real estate agents in Pune.',
  contactUnset: 'Contact details are shared when you request an invite.',
  contactHeading: 'Contact',
}

// ---------------------------------------------------------------------------------------------------------
// Landing
// ---------------------------------------------------------------------------------------------------------
export interface Shot { src: string; alt: string; caption: string; width: number; height: number }
const SHOT_W = 780
const SHOT_H = 1688
const shot = (file: string, alt: string, caption: string): Shot => ({ src: '/landing/' + file, alt, caption, width: SHOT_W, height: SHOT_H })

export const SHOTS = {
  home: shot('30-home-actions.jpg',
    'Phone screen "Your business today" with a suggested call to a hot buyer, a suggestion to create marketing for a 3 BHK in Wakad, and counts of new enquiries, hot buyers, site visits and follow-ups due.',
    'Your day at a glance'),
  create: shot('07-review-top.jpg',
    'Phone screen "Check and confirm" showing a property photo, the title "2 BHK for sale in Baner, Pune - 85 L", For Sale selected, a price of 85,00,000 and a Confirm and post button.',
    'Check the details, then post'),
  market: shot('22-marketing-ready.jpg',
    'Phone screen "Your property is ready" with English, Hindi and Marathi language buttons and an Instagram image card for a 2 BHK apartment in Baner priced at Rs 85 L.',
    'Share-ready posts in three languages'),
  site: shot('12-site-home.jpg',
    'An agent website on a phone: a blue header with the agent name, WhatsApp and Call buttons, and a Properties list with All, Buy and Rent filters.',
    'Your own website, ready to share'),
  lead: shot('19-lead-detail.jpg',
    'Phone screen for a buyer with a Hot score, an AI summary of what they want, a Schedule a site visit button, Call and WhatsApp buttons, and chips for what they want: 2 BHK, 80 lakh to 1.2 crore, Baner, in 1-3 months, home loan.',
    'A buyer, summarised'),
  match: shot('27-buyers-match.jpg',
    'Phone screen "2 of your buyers match this property" listing two buyers with a 100% match, why each one matches, and a Send on WhatsApp button for each.',
    'Which of your buyers fit a property'),
}

export const SAMPLE_NOTE = 'Screens show sample data.'

export const LANDING = {
  metaTitle: `${BRAND_NAME}: ${TAGLINE} | Free pilot for real estate agents in Pune`,
  metaDescription:
    'Your own website, builder projects checked on MahaRERA, posts and reels made for you, and every enquiry as a lead card that says who to call first. Free invite-only pilot for real estate agents in Pune.',
  metaOrgDescription: 'A free, invite-only pilot that helps real estate agents in Pune get buyer enquiries and follow them up.',
  hero: {
    eyebrow: 'For real estate agents in Pune',
    pilot: 'Free pilot',
    titleLines: ['Get more enquiries.', 'Know who to call first.'],
    lead:
      'Your own property website, posts and reels made for you, and every enquiry turned into a lead card that says what the buyer wants. Buyers reach you on WhatsApp.',
    cta: 'Join the free pilot',
    whatsapp: 'Ask us on WhatsApp',
    secondary: 'See an example agent page',
    facts: 'Free during the pilot · No app to install · Posts in English, हिंदी, मराठी',
    signInLead: 'Already invited?',
    signIn: 'Sign in',
  },
  problem: {
    heading: 'Sound familiar?',
    items: [
      { title: 'Comments with no names', body: '"Price?" and "interested" under your post, and no idea who wrote them.' },
      { title: 'Enquiries everywhere', body: 'Calls, WhatsApp, Instagram, Facebook. Nothing in one list, so the warm buyer waits.' },
      { title: 'Posts eat your evening', body: 'Writing the same property up again in English, Hindi and Marathi is slow work.' },
    ],
  },
  mock: {
    source: 'Instagram comment',
    comment: 'INTERESTED',
    name: 'Sample buyer',
    hot: 'Hot',
    summary: 'Wants a 2 BHK in Baner, moving in 1-3 months, will need a home loan.',
    fields: [
      { label: 'Area', value: 'Baner' },
      { label: 'Budget', value: '80 L - 1.2 Cr' },
      { label: 'Timing', value: '1-3 months' },
      { label: 'Loan', value: 'Yes' },
    ],
    nextLabel: 'Next step:',
    next: 'call today, offer a site visit.',
    call: 'Call',
    whatsapp: 'WhatsApp',
    sample: 'Sample data',
  },
  steps: {
    id: 'what-it-does',
    heading: 'Four steps. All working today.',
    items: [
      {
        key: 'create', label: 'Create', title: 'Add homes and projects',
        body: 'From your phone, or a builder project by its MahaRERA number. We fill in the details and read the public record for you.',
      },
      {
        key: 'attract', label: 'Get discovered', title: 'Posts and reels, made for you',
        body: 'Your own website, plus carousels and reels on your Instagram and Facebook Page, and on Avasetu\'s, after you approve each one.',
      },
      {
        key: 'qualify', label: 'Get qualified leads', title: 'Every enquiry becomes a lead card',
        body: 'Budget, bedrooms, area, timing and how warm the buyer is. Buyers tick a box to agree to be contacted.',
      },
      {
        key: 'close', label: 'Close', title: 'Call the right person first',
        body: 'Call or WhatsApp from the card, and see which buyers match a new property. Nothing is sent unless you tap send.',
      },
    ],
    noApp: 'Works in your phone\'s browser and with the WhatsApp you already use. No app to install.',
  },
  cost: {
    id: 'cost',
    title: 'Free during the pilot.',
    body: 'After it, a small monthly fee. We tell you the price first, and you decide.',
  },
  faq: {
    id: 'faq',
    heading: 'Questions',
    items: [
      {
        q: 'What happens after I ask for an invite?',
        a: 'We call you on the number you gave. When a place is free we send you a personal access code, then set up your website and pages with you.',
      },
      {
        q: 'Is it really free?',
        a: 'Yes, during the pilot. After it, Avasetu stays low-cost for agents: a small monthly fee, not a big subscription. We tell you the price before anything changes, and you decide whether to continue.',
      },
      {
        q: 'Do you post on my own Facebook and Instagram?',
        a: 'Yes. When you join, we connect your Facebook Page and Instagram with you, and posts go out there after you approve each one. They also go out on Avasetu\'s accounts, marked "Listed by" you, for extra reach.',
      },
      {
        q: 'Who sees my buyer leads?',
        a: 'Only you, the agent the buyer contacted. Buyers agree to be contacted when they enquire. We handle their details only to run the service, and we never sell them or share them with other agents.',
      },
      {
        q: 'Which languages work?',
        a: 'Posts and replies can be in English, Hindi and Marathi. This page is in English for now; more areas of Pune and more languages are next.',
      },
      {
        q: 'What about RERA?',
        a: 'For builder projects we read the public MahaRERA record and show it with the date we read it, next to the builder\'s own claims. You stay responsible for your own agent registration.',
      },
      {
        q: 'Do I need to install an app?',
        a: 'No. It works in your phone\'s browser.',
      },
    ],
    privacyLink: 'Read the privacy policy',
    deletionLink: 'Data deletion',
  },
  finalCta: {
    titleLines: ['See your own', 'lead cards.'],
    body: 'Pune agents only. Your name and mobile number is all we need; we call you back.',
    whatsapp: 'Or message us on WhatsApp',
    fullForm: 'Add your city or a note',
  },
  sticky: { cta: 'Join the free pilot', whatsapp: 'WhatsApp us' },
}

// ---------------------------------------------------------------------------------------------------------
// Request invite
// ---------------------------------------------------------------------------------------------------------
export const INVITE = {
  metaTitle: 'Request an invite | Pilot for real estate agents in Pune',
  metaDescription: 'Ask for a place in the free, invite-only pilot for real estate agents in Pune.',
  title: 'Request an invite',
  lead: 'The pilot is free and invite-only, for real estate agents in Pune. Tell us who you are and we will get in touch.',
  labels: {
    name: 'Your name',
    phone: 'Mobile number',
    city: 'City',
    message: 'Anything you would like us to know',
    optional: '(optional)',
    consent: 'OK to contact me about the pilot',
    submit: 'Send request',
    sending: 'Sending...',
  },
  hints: { phone: '10-digit Indian mobile, for example 98765 43210', message: 'For example, your area or how many properties you handle.' },
  errors: {
    name: 'Please enter your name (at least 2 letters).',
    phone: 'Enter a valid 10-digit Indian mobile number (starts with 6, 7, 8 or 9).',
    city: 'Please enter your city.',
    message: 'Please keep your note under 500 characters.',
    consent: 'Please tick the box so we can contact you about the pilot.',
    invalid: 'Some details were not accepted. Please check them and try again.',
    tooMany: 'Too many requests from this number or connection. Please wait an hour and try again.',
    network: 'We could not send your request. Please check your connection and try again.',
  },
  success: {
    title: (first: string) => (first ? 'Thank you, ' + first + '.' : 'Thank you.'),
    body: (phone: string) => 'We have your request and will contact you on ' + phone + ' about the pilot.',
    back: 'Back to the home page',
  },
  privacyNote: 'We use your details only to reply to your request.',
  privacyLink: 'Privacy',
  signInHint: 'Already have a code?',
  more: 'More details (city, a note)',
}

// ---------------------------------------------------------------------------------------------------------
// Legal
// ---------------------------------------------------------------------------------------------------------
export interface LegalSection {
  id: string
  heading: string
  paragraphs?: string[]
  bullets?: string[]
  /** Render the contact lines after the text. */
  contact?: boolean
}
export interface LegalDoc {
  metaTitle: string
  metaDescription: string
  title: string
  intro: string
  sections: LegalSection[]
}

export const CONTACT_UNSET = 'Contact details are shared when you request an invite.'

function channelsSentence(cfg: MarketingConfig): string {
  const parts: string[] = []
  if (cfg.email) parts.push('email ' + cfg.email)
  if (cfg.whatsappDisplay) parts.push('WhatsApp ' + cfg.whatsappDisplay)
  return parts.length ? parts.join(' or ') : CONTACT_UNSET
}

export function privacyDoc(cfg: MarketingConfig): LegalDoc {
  const n = cfg.businessName
  return {
    metaTitle: 'Privacy policy | ' + n,
    metaDescription: 'What personal data ' + n + ' collects, why, who sees it, how long we keep it and how to ask for it to be deleted.',
    title: 'Privacy policy',
    intro:
      'This explains, in plain language, what personal information ' + n + ' handles when you use our service or send an enquiry through an agent\'s website, and what your choices are.',
    sections: [
      {
        id: 'who-we-are', heading: 'Who we are',
        paragraphs: [
          n + ' ("we", "us") runs a free pilot in Pune that helps real estate agents publish properties, share them, and follow up buyer enquiries. We decide why and how the personal data described here is used.',
        ],
      },
      {
        id: 'what-we-collect', heading: 'What we collect',
        paragraphs: ['What we collect depends on who you are.'],
        bullets: [
          'Agents: name, mobile number, city, languages and specialities you choose, your photo, the properties you post (details and photos), and how you use the service.',
          'People who ask for an invite: name, mobile number, city, an optional note, and your consent. To prevent abuse we also keep a scrambled (hashed) version of your connection\'s IP address. We do not keep the IP address itself.',
          'Buyers who send an enquiry through an agent\'s website: name, mobile number, your message, and any preferences you choose to share (for example bedrooms, budget, timing, home loan).',
          'Buyers browsing an agent\'s website: which pages you view, linked to a random id stored in your browser (not your name), and the link you came from, so the agent can see which properties get attention.',
        ],
      },
      {
        id: 'why', heading: 'Why we use it',
        bullets: [
          'To connect buyers with the agent they contacted.',
          'To show agents their enquiries and what each buyer is looking for.',
          'To create and run agents\' websites and share-ready marketing.',
          'To reply to invite requests and run the pilot.',
          'To keep the service safe and to improve it.',
        ],
      },
      {
        id: 'consent', heading: 'Consent',
        paragraphs: [
          'Buyers are asked to agree to be contacted on the enquiry form before anything is sent. People who ask for an invite tick a box to agree we may contact them about the pilot. You can withdraw your consent at any time (see "Your rights").',
        ],
      },
      {
        id: 'who-sees-it', heading: 'Who sees your data',
        bullets: [
          'The agent you contacted sees your enquiry and details.',
          'We see it as the service provider running the platform.',
          'Service providers that help us run the service (for example hosting, and AI services that help agents write listing text or marketing from what the agent types or says) process data on our behalf.',
          'We do not sell your personal data.',
        ],
      },
      {
        id: 'social-posts', heading: 'Posts on our Facebook and Instagram pages',
        paragraphs: [
          'When an agent\'s property is posted to our Facebook or Instagram page, our team name appears in the post (never an agent\'s name or phone number), with that agent\'s consent. Those posts are public.',
        ],
      },
      {
        id: 'retention', heading: 'How long we keep it',
        paragraphs: [
          'We keep your data while your account or enquiry is active and for as long as needed to run the service. If you ask us to delete it, we delete it within 30 days, except where the law requires us to keep something (see the data deletion page).',
        ],
      },
      {
        id: 'rights', heading: 'Your rights',
        paragraphs: [
          'Under India\'s Digital Personal Data Protection Act, 2023 you can:',
        ],
        bullets: [
          'ask what personal data we hold about you (access);',
          'ask us to correct anything that is wrong or incomplete (correction);',
          'ask us to delete your data (erasure);',
          'withdraw your consent whenever you like.',
        ],
      },
      {
        id: 'children', heading: 'Children',
        paragraphs: [
          'The service is for adults and is not meant for children. We do not knowingly collect data from anyone under 18. If you think we have, contact us and we will delete it.',
        ],
      },
      {
        id: 'security', heading: 'Security',
        paragraphs: [
          'We use reasonable safeguards, such as encrypted connections and limiting who can reach the data. No system is completely secure, so we cannot promise absolute security.',
        ],
      },
      {
        id: 'changes', heading: 'Changes to this policy',
        paragraphs: ['If we change this policy, we will update the date at the top of this page.'],
      },
      {
        id: 'contact', heading: 'Contact and grievances',
        paragraphs: [
          'For questions, to use any of your rights, or to raise a grievance about how your data is handled, contact us. Write "Privacy" or "Grievance" so it reaches the right place.',
        ],
        contact: true,
      },
    ],
  }
}

export function termsDoc(cfg: MarketingConfig): LegalDoc {
  const n = cfg.businessName
  return {
    metaTitle: 'Terms of service | ' + n,
    metaDescription: 'Plain-language terms for the ' + n + ' pilot: who can use it, what agents are responsible for, and how the service is provided.',
    title: 'Terms of service',
    intro:
      'These are the terms for using the ' + n + ' pilot. By using the service you agree to them. If you do not agree, please do not use it.',
    sections: [
      {
        id: 'about', heading: 'About the pilot',
        paragraphs: [
          n + ' is a pilot service for real estate agents in Pune. It lets an agent post properties, get a website and share-ready marketing, and see buyer enquiries. It is free during the pilot and may change.',
        ],
      },
      {
        id: 'who-may-use', heading: 'Who may use it',
        bullets: [
          'Agents: real estate agents we have invited. Your invite and access code are personal; please do not share them.',
          'Buyers: anyone can browse an agent\'s website and send an enquiry.',
        ],
      },
      {
        id: 'agent-responsibilities', heading: 'What agents are responsible for',
        bullets: [
          'Post accurate listings: real price, size, location and availability.',
          'Use real photos of the property, and only photos you have the right to use.',
          'Follow the law, including RERA registration and display rules where they apply to you.',
          'Get the owner\'s and your own consent before a property is posted on our Facebook or Instagram page.',
          'Check anything written or suggested by AI before you post or send it. You are responsible for what you publish.',
        ],
      },
      {
        id: 'buyer-data', heading: 'How agents may use buyer data',
        paragraphs: ['Buyer details come to you because the buyer asked to be contacted. You may use them only to respond to that enquiry and to help the buyer with real estate. You must not:'],
        bullets: [
          'sell, share or publish buyers\' details;',
          'use them for unrelated marketing or spam;',
          'keep contacting a buyer who has asked you to stop.',
        ],
      },
      {
        id: 'no-misleading', heading: 'No misleading content',
        paragraphs: ['Do not post fake or unavailable listings, misleading prices or photos, or anything illegal, offensive or that infringes someone else\'s rights.'],
      },
      {
        id: 'your-content', heading: 'Your content',
        paragraphs: [
          'You keep ownership of the listings and photos you post. You allow us to store, display and format them so the service can work, including on your website, in the marketing we create for you, and, when you choose, on our social pages.',
        ],
      },
      {
        id: 'removal', heading: 'Removing content and accounts',
        paragraphs: ['We may remove listings or suspend or end accounts that break these terms or put others at risk. You can stop using the service, and ask us to delete your data, at any time.'],
      },
      {
        id: 'as-is', heading: 'Service provided as is',
        paragraphs: [
          'The pilot is provided "as is" and "as available". It may have errors, change or pause without notice. We do not promise a number of enquiries or any result for your business. We do not check listings and are not a party to any deal between an agent and a buyer.',
        ],
      },
      {
        id: 'liability', heading: 'Liability',
        paragraphs: [
          'To the extent the law allows, we are not responsible for indirect or business losses, such as lost deals or income, arising from using the pilot. Nothing here limits any right you have that cannot be limited by law.',
        ],
      },
      {
        id: 'law', heading: 'Governing law',
        paragraphs: ['These terms are governed by the laws of India. Courts in Pune have jurisdiction over any dispute.'],
      },
      {
        id: 'changes', heading: 'Changes',
        paragraphs: ['We may update these terms. We will change the date at the top of this page, and continuing to use the service means you accept the update.'],
      },
      {
        id: 'contact', heading: 'Contact',
        paragraphs: ['Questions about these terms? Contact us.'],
        contact: true,
      },
    ],
  }
}

export function deletionDoc(cfg: MarketingConfig): LegalDoc {
  const n = cfg.businessName
  const reach = channelsSentence(cfg)
  const hasChannel = !!(cfg.email || cfg.whatsappUrl)
  return {
    metaTitle: 'Data deletion | ' + n,
    metaDescription: 'How to ask ' + n + ' to delete your data, what we delete, and how long it takes.',
    title: 'Data deletion',
    intro: 'Anyone, whether you are an agent or a buyer, can ask us to delete the personal data we hold about you. This page explains how.',
    sections: [
      {
        id: 'how-to-ask', heading: 'Data deletion instructions',
        paragraphs: [
          'To delete your data from ' + n + ':',
        ],
        bullets: hasChannel
          ? [
              'Contact us on ' + reach + '.',
              'Write "Delete my data" and send it from the mobile number you used with us (or include that number).',
              'We will confirm your request and delete your data within 30 days.',
            ]
          : [
              CONTACT_UNSET + ' You can also use the "Request an invite" form: write "Delete my data" in the note.',
              'Include the mobile number you used with us.',
              'We will confirm your request and delete your data within 30 days.',
            ],
      },
      {
        id: 'what-we-need', heading: 'What we need from you',
        paragraphs: [
          'The mobile number you used, so we can find your data. We may ask you to confirm it is yours before we delete anything, to protect you from someone else asking on your behalf.',
        ],
      },
      {
        id: 'what-is-deleted', heading: 'What we delete',
        bullets: [
          'Agents: your account, profile, website, listings and photos, and the buyer enquiries in your account.',
          'Buyers: your enquiry details (name, mobile number, message, preferences) and the page views linked to you.',
          'Invite requests: your name, number, city and note.',
        ],
      },
      {
        id: 'facebook-instagram', heading: 'Facebook and Instagram',
        paragraphs: [
          'If you use a Facebook or Instagram account with our service, you can also remove our app from your Facebook or Instagram settings. To delete the data we hold about you, please still contact us as above.',
          'If a property with your details was posted on our Facebook or Instagram page, tell us and we will remove that post.',
        ],
      },
      {
        id: 'timeline', heading: 'How long it takes',
        paragraphs: ['We delete your data within 30 days of confirming your request.'],
      },
      {
        id: 'retained', heading: 'What we may keep',
        paragraphs: ['If the law requires us to keep something, for example records we must legally retain, we keep only that and only for as long as required. We tell you when this applies.'],
      },
      {
        id: 'contact', heading: 'Contact',
        paragraphs: ['You can also read how we handle data in the privacy policy.'],
        contact: true,
      },
    ],
  }
}

/** A real agent on Avasetu today (featured with their consent). Images are their published carousel slides. */
export const LIVE = {
  id: 'live',
  eyebrow: 'Example agent page',
  heading: 'See what an Avasetu agent gets',
  lead: 'A sample page we built for House Deal, Upper Kharadi: five builder projects in Wagholi and Upper Kharadi, each checked on MahaRERA, with carousels and reels made for each one.',
  cards: [
    { src: '/landing/live/maharera.jpg', alt: 'Carousel slide: Checked on MahaRERA, 71% of 143 homes booked, registration P52100078796, completion date filed 30 Apr 2029.',
      title: 'Checked on MahaRERA', body: 'Completion date filed and homes booked, read from the public record, with the date we read it.' },
    { src: '/landing/live/possession.jpg', alt: 'Carousel slide: When could you move in? Builder\'s target Dec 2028 next to the MahaRERA date 30 Aug 2030.',
      title: 'Both dates, explained', body: 'The builder\'s target next to the date filed with MahaRERA, in plain words, so buyers plan around the right one.' },
    { src: '/landing/live/posts.jpg', alt: 'Carousel cover: 5 projects, 59.99 lakh to 1.25 crore, checked on MahaRERA, House Deal.',
      title: 'Posts in the agent\'s name', body: 'Carousels and reels for every project, marked "Listed by" the agent, linking back to their page.' },
  ],
  links: { page: '/agent/house-deal', pageLabel: 'Open the example page', compare: '/agent/house-deal/projects/compare', compareLabel: 'Compare the 5 projects' },
}

/** One line for buyers who land on the agent-facing home page. */
export const BUYERS = {
  title: 'Buying a home in Kharadi or Wagholi?',
  body: 'Every project on Avasetu shows its MahaRERA record and the date we read it. Start with the area guides or the latest news.',
  guides: 'Area guides',
  news: 'News',
}
