import { fromListings } from '@/lib/site/finderItems'
import type { RegisterListItem } from '@/lib/site/register'
import type { PublicListing } from '@/lib/site/types'

const listing = (x: Partial<PublicListing>) => ({ id: 'l1', title: 'Offices', property_type: 'office', price_inr: 5_500_000, rera_no: 'PC1', media: [], ...x }) as PublicListing
const record = { regno: 'PC1', slug: 'ubc', name: 'UBC', place_name: 'Mohammadwadi', area: null, completion_now: '2028-04-30' } as unknown as RegisterListItem

it('a listing named only for its kind of building takes the record name of its number; a real name stays', () => {
  expect(fromListings([listing({ project_name: 'Commercial Complex' })], 'a', [record])[0].name).toBe('UBC')
  expect(fromListings([listing({ project_name: 'Bathiya Plaza' })], 'a', [record])[0].name).toBe('Bathiya Plaza')
  expect(fromListings([listing({ project_name: 'Commercial Complex', rera_no: null })], 'a', [record])[0].name).toBe('Commercial Complex')
})

it('the card shows the same place as the page behind it, unless one name sits inside the other', () => {
  expect(fromListings([listing({ locality: 'Undri' })], 'a', [record])[0].area).toBe('Mohammadwadi')
  expect(fromListings([listing({ locality: 'Upper Mohammadwadi' })], 'a', [record])[0].area).toBe('Upper Mohammadwadi')
  expect(fromListings([listing({ locality: 'Undri', rera_no: null })], 'a', [record])[0].area).toBe('Undri')
})
