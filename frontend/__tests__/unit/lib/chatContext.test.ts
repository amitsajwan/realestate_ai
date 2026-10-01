import { chatContextFromPath } from '@/lib/site/chatContext'

describe('chatContextFromPath', () => {
  it('reads the listing id from a listing page', () => {
    expect(chatContextFromPath('/agent/rahul/listings/64f0a1b2c3')).toEqual({ listing_id: '64f0a1b2c3' })
    expect(chatContextFromPath('/agent/rahul/64f0a1b2c3/')).toEqual({ listing_id: '64f0a1b2c3' })
  })
  it('reads the locality from an area page', () => {
    expect(chatContextFromPath('/localities/upper-kharadi')).toEqual({ locality: 'upper-kharadi' })
  })
  it('sends nothing for other pages or odd values', () => {
    expect(chatContextFromPath('/agent/rahul')).toBeUndefined()
    expect(chatContextFromPath('/insights/some-guide')).toBeUndefined()
    expect(chatContextFromPath('/agent/rahul/listings/<script>')).toBeUndefined()
    expect(chatContextFromPath('/localities/UPPER')).toBeUndefined()
    expect(chatContextFromPath(null)).toBeUndefined()
  })
})
