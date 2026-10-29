import { chatContextFromPath } from '@/lib/site/chatContext'

describe('chatContextFromPath', () => {
  it('reads the listing id from a listing page on an agent site', () => {
    expect(chatContextFromPath('/agent/rahul/listings/64f0a1b2c3')).toEqual({ page: 'listing', site: 'agent', listing_id: '64f0a1b2c3' })
    expect(chatContextFromPath('/agent/rahul/64f0a1b2c3/')).toEqual({ page: 'listing', site: 'agent', listing_id: '64f0a1b2c3' })
  })
  it('treats the rest of an agent site as that agent\'s buyer pages', () => {
    expect(chatContextFromPath('/agent/rahul')).toEqual({ page: 'home', site: 'agent' })
    expect(chatContextFromPath('/agent/rahul/projects/godrej-ivara')).toEqual({ page: 'home', site: 'agent' })
    expect(chatContextFromPath('/agent/rahul/listings/<script>')).toEqual({ page: 'home', site: 'agent' })
  })
  it('knows the home page', () => {
    expect(chatContextFromPath('/')).toEqual({ page: 'home' })
  })
  it('reads the project from a project page and its MahaRERA check, but not from the lists or coming-soon pages', () => {
    expect(chatContextFromPath('/projects/godrej-ivara-kharadi')).toEqual({ page: 'project', project: 'godrej-ivara-kharadi' })
    expect(chatContextFromPath('/check/godrej-ivara-kharadi')).toEqual({ page: 'project', project: 'godrej-ivara-kharadi' })
    expect(chatContextFromPath('/projects/upcoming/esbee-upper-kharadi')).toEqual({ page: 'other' })
    expect(chatContextFromPath('/projects')).toEqual({ page: 'other' })
  })
  it('reads the area, the list and the size from area list pages', () => {
    expect(chatContextFromPath('/projects/area/kharadi')).toEqual({ page: 'list', locality: 'kharadi' })
    expect(chatContextFromPath('/projects/area/kharadi/top')).toEqual({ page: 'list', locality: 'kharadi', list: 'top' })
    expect(chatContextFromPath('/projects/area/viman-nagar/new-launches/2-bhk')).toEqual({ page: 'list', locality: 'viman-nagar', list: 'new-launches', bhk: 2 })
    expect(chatContextFromPath('/projects/area/wagholi/possession-2027')).toEqual({ page: 'list', locality: 'wagholi' })
    expect(chatContextFromPath('/2-bhk/wagholi')).toEqual({ page: 'list', locality: 'wagholi', bhk: 2 })
    expect(chatContextFromPath('/3-bhk/kharadi')).toEqual({ page: 'list', locality: 'kharadi', bhk: 3 })
    expect(chatContextFromPath('/price/under-60-lakh/wagholi')).toEqual({ page: 'list', locality: 'wagholi' })
  })
  it('reads the place from locality pages and the topic from guides', () => {
    expect(chatContextFromPath('/localities/upper-kharadi')).toEqual({ page: 'area', locality: 'upper-kharadi' })
    expect(chatContextFromPath('/localities/kharadi/eon-it-park')).toEqual({ page: 'area', locality: 'kharadi' })
    expect(chatContextFromPath('/guides/upper-kharadi')).toEqual({ page: 'guide', topic: 'upper-kharadi' })
    expect(chatContextFromPath('/insights/some-guide')).toEqual({ page: 'guide', topic: 'some-guide' })
  })
  it('reads the builder from a builder page', () => {
    expect(chatContextFromPath('/builders/godrej-properties')).toEqual({ page: 'builder', builder: 'godrej-properties' })
  })
  it('knows news and tracker pages', () => {
    expect(chatContextFromPath('/news')).toEqual({ page: 'news' })
    expect(chatContextFromPath('/news/track/hinjawadi-metro')).toEqual({ page: 'news' })
    expect(chatContextFromPath('/pune-maharera-tracker')).toEqual({ page: 'news' })
  })
  it('marks only the pages for agents as agent pages', () => {
    for (const p of ['/agents', '/trial', '/request-invite', '/for-agents', '/for-agents/guide']) expect(chatContextFromPath(p)).toEqual({ page: 'agents' })
    expect(chatContextFromPath('/agentsx')).toEqual({ page: 'other' })
  })
  it('sends nothing it cannot read and no odd values', () => {
    expect(chatContextFromPath('/localities/UPPER')).toEqual({ page: 'other' })
    expect(chatContextFromPath('/builders/<b>')).toEqual({ page: 'other' })
    expect(chatContextFromPath(null)).toBeUndefined()
  })
})
