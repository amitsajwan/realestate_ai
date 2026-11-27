/** My website: the bio link is the site tagged src=bio, so a lead from an Instagram or WhatsApp bio says where it came from. */
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { SiteCard, bioLink } from '@/components/app/SiteCard'

const mockCopy = jest.fn()
jest.mock('@/lib/app/share', () => ({ copyText: (s: string) => mockCopy(s), whatsappShareUrl: (s: string) => 'https://wa.me/?text=' + s }))
jest.mock('@/lib/app/home', () => ({ markSiteShared: jest.fn() }))

it('tags the site link for a bio', () => {
  expect(bioLink('https://avasetu.in/agent/house-deal')).toBe('https://avasetu.in/agent/house-deal?src=bio')
  expect(bioLink('https://x.in/a?lang=mr')).toBe('https://x.in/a?lang=mr&src=bio')
})

it('copies the bio link', async () => {
  mockCopy.mockResolvedValue(true)
  render(<SiteCard siteUrl="https://avasetu.in/agent/house-deal" />)
  fireEvent.click(screen.getByTestId('copy-bio-link'))
  await waitFor(() => expect(mockCopy).toHaveBeenCalledWith('https://avasetu.in/agent/house-deal?src=bio'))
  expect(await screen.findByText('Copied!')).toBeInTheDocument()
})
