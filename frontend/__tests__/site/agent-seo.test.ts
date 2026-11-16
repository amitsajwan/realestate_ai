import { agentJsonLd, agentMetadata, listingJsonLd, listingMetadata, projectMetadata } from '@/lib/site/seo'
import { siteOrigin } from '@/lib/site/slug'
import type { AgentProfile, PublicListing, PublicProject } from '@/lib/site/types'

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

test('a site with no homes stays out of search and joins with its first listing or project', () => {
  expect(agentMetadata(agent, [], 'Pune').robots).toEqual({ index: false, follow: true })
  expect(agentMetadata(agent, [listing({ title: 'Sample: 2 BHK' })], 'Pune').robots).toEqual({ index: false, follow: true })
  expect(agentMetadata(agent, [listing({})], 'Pune').robots).toBeUndefined()
  expect(agentMetadata(agent, [], 'Pune', true).robots).toBeUndefined()
})

test("the team's own site keeps naming the home page, not noindex, with no listings of its own", () => {
  const md = agentMetadata({ ...agent, slug: 'avasetu' }, [], 'Pune')
  expect(md.robots).toBeUndefined()
  expect(md.alternates?.canonical).toBe(siteOrigin())
})

test('a listing with no price says none, in the title and the offer', () => {
  const free = listing({ price_inr: null as never })
  expect(listingMetadata(agent, free).title).toBe('KP Supernova 2 BHK in Mohammadwadi, Pune')
  expect(listingJsonLd(agent, free).offers).toBeUndefined()
  expect(listingJsonLd(agent, listing({})).offers).toMatchObject({ price: 8000000, seller: { name: 'Royal Estate' } })
})

test('an agent copy of a project goes by the business name, not the login', () => {
  const p = { name: 'KP Supernova', locality: 'Mohammadwadi', slug: 'kp', rera_no: 'P1', media: [] } as unknown as PublicProject
  expect(projectMetadata(agent, p, '₹80 L').title).toBe('KP Supernova, Mohammadwadi | Royal Estate')
})
