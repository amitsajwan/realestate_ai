import type { AgentProfile, ListingsPage, PublicListing } from './types'

// Realistic Pune fixtures for SITE_USE_FIXTURES=1 / dev fallback when the API is unreachable.
// Slugs served: FIXTURE_SLUGS. Anything else 404s (so the not-found page can be exercised).

export const FIXTURE_BRAND_SLUGS = ['rohan-kulkarni-aundh', 'meera-joshi-kothrud', 'sanjay-patil-hinjewadi', 'aditi-rao-koregaon', 'neha-kapoor-kharadi']
export const FIXTURE_SLUGS = ['priya-deshmukh-pune', 'demo', ...FIXTURE_BRAND_SLUGS]

const img = (seed: string, order = 0) => ({
  url: 'https://picsum.photos/seed/' + seed + '/1200/800',
  kind: 'image' as const,
  order,
})
const imgs = (seed: string, n = 3) => Array.from({ length: n }, (_, i) => img(seed + '-' + (i + 1), i))

export const FIXTURE_AGENT: AgentProfile = {
  agent_name: 'Priya Deshmukh',
  slug: 'priya-deshmukh-pune',
  bio:
    'Pune-based real estate advisor with 9 years of experience in Baner, Wakad, Hinjewadi and Kothrud. ' +
    'I help families and first-time buyers find the right home, with honest advice and clean paperwork.',
  photo: 'https://picsum.photos/seed/priya-agent/400/400',
  phone: '+91 98765 43210',
  email: 'priya@example.com',
  languages: ['English', 'Hindi', 'Marathi'],
  specialties: ['Apartments', 'Rentals', 'Under-construction projects'],
  office_address: 'Office 12, Balewadi High Street, Baner, Pune 411045',
  city: 'Pune',
  experience: '9 years',
  branding_data: {
    tagline: 'Find your home in Pune, without the hassle',
    colors: { primary: '#0f766e', secondary: '#134e4a', accent: '#f59e0b' },
  },
  view_count: 1284,
}

const base = { status: 'live', city: 'Pune', amenities: [] as string[] }

export const FIXTURE_LISTINGS: PublicListing[] = [
  {
    ...base,
    id: 'fx-baner-2bhk',
    transaction: 'sale',
    property_type: 'apartment',
    title: 'Spacious 2 BHK in Baner near Balewadi High Street',
    description: {
      en: 'Bright 2 BHK on the 7th floor with a balcony facing the hills. Covered parking, 24x7 security and a clubhouse. Five minutes from Balewadi High Street and schools.',
      hi: 'बाणेर में 7वीं मंज़िल पर हवादार 2 BHK, पहाड़ियों की ओर बालकनी। कवर्ड पार्किंग, 24x7 सुरक्षा और क्लबहाउस। बालेवाड़ी हाई स्ट्रीट और स्कूल पाँच मिनट की दूरी पर।',
      mr: 'बाणेरमध्ये ७ व्या मजल्यावर प्रशस्त 2 BHK, टेकड्यांकडे तोंड असलेली बाल्कनी. कव्हर्ड पार्किंग, २४x७ सुरक्षा आणि क्लबहाउस. बालेवाडी हाय स्ट्रीट आणि शाळा पाच मिनिटांवर.',
    },
    price_inr: 8500000,
    locality: 'Baner',
    project_name: 'Sky Heights',
    bhk: 2,
    carpet_sqft: 860,
    super_built_up_sqft: 1150,
    floor: 7,
    total_floors: 14,
    furnishing: 'semi',
    possession: 'ready',
    rera_no: 'P52100012345',
    amenities: ['Covered parking', 'Clubhouse', 'Gym', '24x7 security', 'Lift', 'Power backup'],
    media: imgs('baner-2bhk', 4),
    published_at: '2026-09-01T08:00:00Z',
  },
  {
    ...base,
    id: 'fx-wakad-3bhk',
    transaction: 'sale',
    property_type: 'apartment',
    title: '3 BHK with terrace garden in Wakad',
    description: {
      en: 'Corner 3 BHK with a private terrace garden, ready possession. Walking distance to Wakad chowk, D-Mart and the Mumbai-Pune expressway.',
      hi: 'वाकड में निजी टैरेस गार्डन वाला कॉर्नर 3 BHK, तुरंत कब्ज़ा। वाकड चौक, डी-मार्ट और एक्सप्रेसवे पास में।',
    },
    price_inr: 12500000,
    locality: 'Wakad',
    project_name: 'Green Meadows',
    bhk: 3,
    carpet_sqft: 1120,
    floor: 12,
    total_floors: 20,
    furnishing: 'unfurnished',
    possession: 'ready',
    rera_no: 'P52100067890',
    amenities: ['Terrace garden', 'Swimming pool', 'Kids play area', 'EV charging'],
    media: imgs('wakad-3bhk', 5),
    published_at: '2026-08-28T08:00:00Z',
  },
  {
    ...base,
    id: 'fx-kothrud-1bhk-rent',
    transaction: 'rent',
    property_type: 'apartment',
    title: '1 BHK fully furnished for rent in Kothrud',
    description: {
      en: 'Fully furnished 1 BHK, ideal for working professionals. Near Karve Road and metro. Bachelors and families welcome.',
      mr: 'कोथरूडमध्ये पूर्ण सुसज्ज 1 BHK भाड्याने, नोकरदारांसाठी उत्तम. कर्वे रोड आणि मेट्रोजवळ.',
    },
    price_inr: 22000,
    locality: 'Kothrud',
    bhk: 1,
    carpet_sqft: 520,
    floor: 3,
    total_floors: 5,
    furnishing: 'furnished',
    possession: 'ready',
    amenities: ['Wi-Fi', 'Washing machine', 'Geyser', 'Modular kitchen'],
    media: imgs('kothrud-1bhk', 3),
    published_at: '2026-09-10T08:00:00Z',
  },
  {
    ...base,
    id: 'fx-hinjewadi-2bhk-rent',
    transaction: 'rent',
    property_type: 'apartment',
    title: '2 BHK for rent in Hinjewadi Phase 1',
    description: {
      en: 'Semi-furnished 2 BHK five minutes from Rajiv Gandhi Infotech Park. Two balconies, gated society, ample visitor parking.',
      hi: 'हिंजवडी फेज 1 में सेमी-फर्निश्ड 2 BHK, इन्फोटेक पार्क से पाँच मिनट। दो बालकनी, गेटेड सोसाइटी।',
      mr: 'हिंजवडी फेज १ मध्ये सेमी-फर्निश्ड 2 BHK, इन्फोटेक पार्कपासून पाच मिनिटे. दोन बाल्कनी, गेटेड सोसायटी.',
    },
    price_inr: 32000,
    locality: 'Hinjewadi',
    project_name: 'Blue Ridge',
    bhk: 2,
    carpet_sqft: 940,
    floor: 5,
    total_floors: 18,
    furnishing: 'semi',
    possession: 'ready',
    amenities: ['Gated society', 'Gym', 'Visitor parking'],
    media: imgs('hinjewadi-2bhk', 4),
    published_at: '2026-09-15T08:00:00Z',
  },
  {
    ...base,
    id: 'fx-kharadi-2bhk-uc',
    transaction: 'sale',
    property_type: 'apartment',
    title: '2.5 BHK launch offer in Kharadi (RERA registered)',
    description: {
      en: 'New launch 2.5 BHK near EON IT Park. Possession December 2027. Flexible payment plan, bank loan approved project.',
      hi: 'खराडी में EON IT पार्क के पास नया 2.5 BHK। कब्ज़ा दिसंबर 2027। आसान भुगतान योजना।',
    },
    price_inr: 9800000,
    locality: 'Kharadi',
    project_name: 'Riverfront Residences',
    bhk: 2.5,
    carpet_sqft: 780,
    floor: 9,
    total_floors: 22,
    furnishing: 'unfurnished',
    possession: 'Dec 2027',
    rera_no: 'P52100099001',
    amenities: ['Clubhouse', 'Jogging track', 'Co-working lounge'],
    about: {
      project_name: 'Riverfront Residences',
      highlights: ['East facing', 'Corner flat', 'Park facing'],
      amenities: ['Lift', 'Gym', 'Play area', 'Clubhouse'],
      nearby: [{ type: 'school', name: 'School nearby' }, { type: 'office', name: 'EON Free Zone' }, { type: 'office', name: 'World Trade Center Pune' }],
      connectivity: ["On Pune's eastern IT corridor, close to large office campuses.", 'Metro Line 4 (Kharadi to Khadakwasla) is approved, not running yet. Check the latest status with Maha-Metro.'],
      water: '24x7 water supply', parking: '1 covered parking', power_backup: 'Full power backup', maintenance: '₹3,000 per month',
    },
    media: imgs('kharadi-25bhk', 3),
    published_at: '2026-09-20T08:00:00Z',
  },
  {
    ...base,
    id: 'fx-pashan-villa',
    transaction: 'sale',
    property_type: 'villa',
    title: 'Independent 4 BHK villa in Pashan with garden',
    description: {
      en: 'Independent villa on a 3,000 sq.ft plot with a lawn, two-car parking and rooftop terrace. Quiet lane near Pashan lake.',
      mr: 'पाषाण तलावाजवळ ३,००० चौ.फूट प्लॉटवर स्वतंत्र व्हिला, लॉन, दोन गाड्यांची पार्किंग आणि टेरेस.',
    },
    price_inr: 42000000,
    locality: 'Pashan',
    bhk: 4,
    carpet_sqft: 2400,
    floor: 0,
    total_floors: 3,
    furnishing: 'semi',
    possession: 'ready',
    amenities: ['Garden', 'Two-car parking', 'Terrace', 'Borewell'],
    media: imgs('pashan-villa', 5),
    published_at: '2026-08-15T08:00:00Z',
  },
]

// Fictional agents with different brand presets (names, numbers and registrations are invented) for visual review and tests.
const brandAgent = (a: Partial<AgentProfile> & Pick<AgentProfile, 'agent_name' | 'slug'>): AgentProfile => ({
  phone: '+91 98765 43211', email: null, city: 'Pune', languages: ['English', 'Hindi', 'Marathi'], specialties: ['Resale flats', 'New projects'],
  office_address: 'Pune', view_count: 0, ...a,
})

export const FIXTURE_BRAND_AGENTS: Record<string, AgentProfile> = {
  'rohan-kulkarni-aundh': brandAgent({
    agent_name: 'Rohan Kulkarni', slug: 'rohan-kulkarni-aundh', photo: '/uploads/images/fx-agent-m.jpg', bio: 'Pune advisor.',
    branding_data: { business_name: 'Kulkarni Homes', tagline: 'Aundh and Baner homes, explained properly', about: 'Twelve years of helping Pune families buy their first and second homes in Aundh, Baner and Pashan. I walk every flat myself before it reaches this page, and I tell you what I would check before paying a token amount.', preset: 'emerald', banner: '/uploads/images/fx-banner-aundh.jpg', rera_agent_no: 'A52100023456', areas: ['Aundh', 'Baner', 'Pashan', 'Balewadi'], languages: ['English', 'Hindi', 'Marathi'], years_experience: 12, social: { instagram: 'kulkarnihomes.pune' } },
  }),
  'meera-joshi-kothrud': brandAgent({
    agent_name: 'Meera Joshi', slug: 'meera-joshi-kothrud', photo: null, bio: 'Pune advisor.', languages: ['English', 'Marathi'],
    branding_data: { business_name: 'Joshi & Associates', tagline: 'Kothrud, Karve Nagar and Bavdhan, since 2011', about: 'A family-run property practice in west Pune. We handle resale, rentals and redevelopment flats, with clear paperwork and no pressure.', preset: 'terracotta', rera_agent_no: 'A52100031122', areas: ['Kothrud', 'Karve Nagar', 'Bavdhan', 'Erandwane', 'Warje'], languages: ['Marathi', 'English'], years_experience: 15 },
  }),
  'sanjay-patil-hinjewadi': brandAgent({
    agent_name: 'Sanjay Patil', slug: 'sanjay-patil-hinjewadi', photo: '/uploads/images/fx-agent-d.jpg', bio: 'Pune advisor.',
    branding_data: { business_name: 'Patil Prime Estates', tagline: 'Homes near Hinjewadi IT Park, without the guesswork', about: 'Rentals and purchases for IT professionals around Hinjewadi, Wakad and Tathawade. Commute times, society details and possession status, stated plainly.', preset: 'royal-purple', banner: '/uploads/images/fx-banner-hinjewadi.jpg', areas: ['Hinjewadi', 'Wakad', 'Tathawade', 'Ravet'], languages: ['English', 'Hindi'], years_experience: 7 },
  }),
  'aditi-rao-koregaon': brandAgent({
    agent_name: 'Aditi Rao', slug: 'aditi-rao-koregaon', photo: '/uploads/images/fx-agent-w.jpg', bio: 'Pune advisor.', languages: ['English', 'Hindi'],
    branding_data: { business_name: 'Rao & Co. Realty', tagline: 'Quietly good homes in Koregaon Park and Kalyani Nagar', about: 'A boutique practice for premium homes in central-east Pune. Fewer listings, each one visited and documented.', preset: 'cream-ink', rera_agent_no: 'A52100044567', areas: ['Koregaon Park', 'Kalyani Nagar', 'Viman Nagar'], languages: ['English', 'Hindi'], years_experience: 9 },
  }),
  'neha-kapoor-kharadi': brandAgent({
    agent_name: 'Neha Kapoor', slug: 'neha-kapoor-kharadi', photo: '/uploads/images/fx-agent-w2.jpg', bio: 'Pune advisor.',
    branding_data: { business_name: 'Studio Kharadi', tagline: 'Modern flats in Kharadi, Wagholi and Hadapsar', about: 'We help first-time buyers compare new projects and ready flats east of the river, with the possession and RERA details up front.', preset: 'slate-teal', banner: '/uploads/images/fx-banner-kharadi.jpg', rera_agent_no: 'A52100055678', areas: ['Kharadi', 'Wagholi', 'Hadapsar', 'Mundhwa', 'Magarpatta'], languages: ['English', 'Hindi'], years_experience: 5 },
  }),
}

export function fixtureAgent(slug: string): AgentProfile | null {
  if (FIXTURE_BRAND_AGENTS[slug]) return FIXTURE_BRAND_AGENTS[slug]
  return FIXTURE_SLUGS.indexOf(slug) >= 0 ? { ...FIXTURE_AGENT, slug } : null
}

export function fixtureListings(slug: string): ListingsPage | null {
  if (FIXTURE_SLUGS.indexOf(slug) < 0) return null
  const a = FIXTURE_BRAND_AGENTS[slug] || FIXTURE_AGENT
  const items = FIXTURE_LISTINGS.map((l) => ({
    ...l,
    agent: { slug, agent_name: a.agent_name, phone: a.phone, photo: a.photo },
  }))
  return { items, total: items.length }
}

export function fixtureListing(slug: string, id: string): PublicListing | null {
  const page = fixtureListings(slug)
  if (!page) return null
  return page.items.filter((l) => l.id === id)[0] || null
}
