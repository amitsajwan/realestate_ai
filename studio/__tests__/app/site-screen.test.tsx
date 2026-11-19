/** Studio > Site: what the owner edits on the public site, one tab each, out of Admin (2026-11-19). */
import { fireEvent, render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import SitePage from '@/app/studio/site/page'

let mockOwner = true
jest.mock('@/components/app/agents/useIsOwner', () => ({ useIsOwner: () => mockOwner }))
jest.mock('@/components/app/admin/SpotlightEditor', () => ({ SpotlightEditor: () => <p>banner editor</p> }))
jest.mock('@/components/app/admin/MapPinsReview', () => ({ MapPinsReview: () => <p>map pins</p> }))
jest.mock('@/components/app/admin/AreaPicturesReview', () => ({ AreaPicturesReview: () => <p>pictures from above</p> }))
jest.mock('@/components/app/admin/AreaPhotosScreen', () => ({ AreaPhotosScreen: ({ embedded }: { embedded?: boolean }) => <p>area photos{embedded ? ' (embedded)' : ''}</p> }))

beforeEach(() => { mockOwner = true; window.history.replaceState(null, '', '/studio/site') })

it('opens on the hot banner and shows one tool per tab, area photos without a second title', () => {
  render(<SitePage />)
  expect(screen.getByRole('heading', { name: 'Site' })).toBeInTheDocument()
  expect(screen.getByText('banner editor')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('tab', { name: 'Map pins' }))
  expect(screen.getByText('map pins')).toBeInTheDocument()
  expect(screen.queryByText('banner editor')).toBeNull()
  fireEvent.click(screen.getByRole('tab', { name: 'From above' }))
  expect(screen.getByText('pictures from above')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('tab', { name: 'Photos' }))
  expect(screen.getByText('area photos (embedded)')).toBeInTheDocument()
  expect(window.location.search).toBe('?tab=photos')
})

it('tells an agent the site is the owner\'s to edit', () => {
  mockOwner = false
  render(<SitePage />)
  expect(screen.getByText('Only the owner edits the site.')).toBeInTheDocument()
  expect(screen.queryByText('banner editor')).toBeNull()
})
