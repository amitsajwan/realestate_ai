import { agentJsonLd, agentMetadata, listingMetadata } from '@/lib/site/seo'
import type { AgentProfile, PublicListing } from '@/lib/site/types'

const agent = {
  slug: 'kausar-patanwala', agent_name: 'Kausar Patanwala', bio: 'I am a RERA certified Real Estate Consultant.', languages: [],
  branding_data: { business_name: 'Royal Estate', areas: ['Undri', 'NIBM'], rera_agent_no: 'A011262605235' },
} as unknown as AgentProfile

const listing = (over: Partial<PublicListing>) => ({
  id: 'L1', title: '2 BHK for sale', project_name: 'KP Supernova', bhk: 2, property_type: 'apartment', locality: 'Mohammadwadi', city: 'Pune',
  price_inr: 8000000, transaction: 'sale', description: {}, media: [], ...over,
}) as unknown as PublicListing

test('an agent page is titled by the business and the areas it serves', () => {
  const md = agentMetadata(agent, [listing({})], 'Pune')
  expect(md.title).toEqual(expect.stringContaining('Royal Estate | Real estate agent in Undri, NIBM, Pune'))
  expect(md.description).toContain('MahaRERA agent A011262605235')
  expect(md.description).toContain('1 live listing')
})

test('an agent with no areas keeps the plain title', () => {
  const md = agentMetadata({ ...agent, branding_data: { business_name: 'Royal Estate' } } as unknown as AgentProfile, [], 'Pune')
  expect(md.title).toEqual(expect.stringContaining('Royal Estate | Real estate in Pune'))
})

test('a listing title reads as what a buyer searches', () => {
  expect(listingMetadata(agent, listing({})).title).toEqual(expect.stringContaining('KP Supernova 2 BHK in Mohammadwadi, Pune: '))
})

test('a shop is titled as a shop', () => {
  const md = listingMetadata(agent, listing({ project_name: 'UBC', bhk: null, property_type: 'office' } as Partial<PublicListing>))
  expect(md.title).toEqual(expect.stringContaining('UBC shops and offices in Mohammadwadi, Pune: '))
})

test('a listing with no project keeps its own title and adds the place once', () => {
  const md = listingMetadata(agent, listing({ project_name: undefined, title: 'Shops for Sale in Undri, Pune' } as Partial<PublicListing>))
  expect(md.title).toEqual(expect.stringContaining('Shops for Sale in Undri, Pune: '))
})

test('search engines read the agent\'s areas and MahaRERA number', () => {
  const ld = agentJsonLd(agent, 'Pune') as { areaServed: { name: string }[]; identifier: { value: string } }
  expect(ld.areaServed.map((a) => a.name)).toEqual(['Undri', 'NIBM'])
  expect(ld.identifier.value).toBe('A011262605235')
})
