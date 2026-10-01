import type { NewsItem } from './data'

/** Sample news for local review and tests (SITE_USE_FIXTURES=1). Written for design review, not live news. */
const DISCLAIMER = 'Approvals and project status change, so check the sources before you decide. This is general information, not investment or legal advice.'
const GOOGLE = (id: string) => `https://news.google.com/rss/articles/CBMi${id}Pq3Jf0lX8vN2mWk9TgYh7QdLr5sUe1aOcZbV4xEiMuHnR6yKtDjSwB?oc=5`
const media = (id: string) => `https://media.example.com/uploads/news/${id}-fb.jpg`
const K = { slug: 'kharadi', name: 'Kharadi' }
const W = { slug: 'wagholi', name: 'Wagholi' }
const UK = { slug: 'upper-kharadi', name: 'Upper Kharadi' }

const base = { kind: 'story' as const, permalinks: [], items: [], tip: '', disclaimer: DISCLAIMER, our_view: '' }

export const FIXTURE_NEWS: NewsItem[] = [
  {
    ...base, id: 'a1b2c3d4e5', headline: 'Pune Ring Road: ₹10,502 crore approved for the 32 km eastern stretch',
    summary: 'The eastern stretch of the Pune Ring Road is 32 km long. ₹10,502 crore has been approved for this stretch.',
    pillar: 'infrastructure', pillar_label: 'Infrastructure', areas: [K, W], source_name: 'Times of India', source_url: GOOGLE('a1b2c3d4e5'),
    as_of: '2026-09-29T06:30:00+00:00', image_url: media('a1b2c3d4e5'), published_at: '2026-09-29T09:00:00+00:00',
    our_view: 'It may matter to people who commute between east Pune and the highways, but approval is not the same as work on the ground.',
    what_to_check: 'Read the official notice for the latest status before you decide.',
    permalinks: [{ channel: 'facebook', url: 'https://www.facebook.com/PunePropertyHub/posts/1' }],
  },
  {
    ...base, id: 'b2c3d4e5f6', headline: 'PMC starts land acquisition for Kharadi roads, ₹27.14 crore deposited',
    summary: 'PMC has deposited ₹27.14 crore to acquire land for road widening in Kharadi. Land acquisition for the Kharadi roads has started.',
    pillar: 'infrastructure', pillar_label: 'Infrastructure', areas: [K], source_name: 'Hindustan Times',
    source_url: 'https://www.hindustantimes.com/cities/pune-news/kharadi-roads-land-acquisition-101.html',
    as_of: '2026-09-28T06:30:00+00:00', image_url: media('b2c3d4e5f6'), published_at: '2026-09-28T10:00:00+00:00',
    what_to_check: 'Ask the PMC ward office which roads and plots are covered before you rely on the widening.',
  },
  {
    ...base, id: 'c3d4e5f6a7', headline: 'Metro corridor 2B Ramwadi to Wagholi approved, not running yet',
    summary: 'Metro corridor 2B from Ramwadi to Wagholi has been approved. The line is not running yet and no opening date is given.',
    pillar: 'infrastructure', pillar_label: 'Infrastructure', areas: [W, K], source_name: 'The Indian Express', source_url: GOOGLE('c3d4e5f6a7'),
    as_of: '2026-09-27T06:30:00+00:00', image_url: media('c3d4e5f6a7'), published_at: '2026-09-27T10:00:00+00:00',
    what_to_check: 'Check the official metro notice for the construction status before you plan around the line.',
  },
  {
    ...base, id: 'd4e5f6a7b8', headline: 'Three new projects registered with MahaRERA in Kharadi this week',
    summary: 'Three new residential projects were registered with MahaRERA in Kharadi this week. Each listing carries its own registration number.',
    pillar: 'new_supply', pillar_label: 'New supply', areas: [K], source_name: 'MahaRERA', source_url: 'https://maharera.maharashtra.gov.in/',
    as_of: '2026-09-26T06:30:00+00:00', image_url: media('d4e5f6a7b8'), published_at: '2026-09-26T10:00:00+00:00',
    what_to_check: 'Look up the registration number on the MahaRERA website before you pay any token amount.',
  },
  {
    ...base, id: 'e5f6a7b8c9', headline: 'RBI keeps the repo rate at 5.5 percent, home-loan rates stay put',
    summary: 'The RBI kept the repo rate unchanged at 5.5 percent. Banks linked to the repo rate are not expected to change home-loan rates today.',
    pillar: 'rules_money', pillar_label: 'Rules and money', areas: [K, W], source_name: 'ET Realty', source_url: GOOGLE('e5f6a7b8c9'),
    as_of: '2026-09-25T06:30:00+00:00', image_url: null, published_at: '2026-09-25T10:00:00+00:00',
    what_to_check: 'Ask your bank which rate your loan is linked to and when it resets.',
  },
  {
    ...base, id: 'f6a7b8c9d0', headline: 'New traffic signals planned at three Kharadi IT park junctions',
    summary: 'PMC plans new traffic signals at three junctions near the Kharadi IT park. Work is expected to be tendered first.',
    pillar: 'locality_life', pillar_label: 'Locality life', areas: [K], source_name: 'Punekar News', source_url: 'https://www.punekarnews.in/kharadi-signals',
    as_of: '2026-09-24T06:30:00+00:00', image_url: media('f6a7b8c9d0'), published_at: '2026-09-24T10:00:00+00:00',
    what_to_check: 'Check the tender notice for the junctions and the timeline.',
  },
  {
    ...base, id: 'digest-2026-w40', kind: 'digest', headline: 'Kharadi and Wagholi this week',
    summary: 'Kharadi and Wagholi this week', pillar: 'digest', pillar_label: 'This week', areas: [K, W, UK], source_name: 'PUNE Property team', source_url: null,
    as_of: '2026-09-27T12:30:00+00:00', image_url: media('digest-2026-w40'), published_at: '2026-09-27T13:00:00+00:00',
    items: [
      { id: 'a1b2c3d4e5', headline: 'Pune Ring Road: ₹10,502 crore approved for the 32 km eastern stretch', source_name: 'Times of India', line: '' },
      { id: 'c3d4e5f6a7', headline: 'Metro corridor 2B Ramwadi to Wagholi approved, not running yet', source_name: 'The Indian Express', line: '' },
      { id: 'd4e5f6a7b8', headline: 'Three new projects registered with MahaRERA in Kharadi this week', source_name: 'MahaRERA', line: '' },
    ],
    tip: 'Ask for the project\'s MahaRERA registration number and look it up on the MahaRERA website before you pay any token amount.',
    what_to_check: '',
  },
]
