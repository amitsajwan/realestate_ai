import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import { ApiError } from '@/lib/app/api'
import { MarketingPackView } from '@/components/app/MarketingPackView'
import { SocialPublishSection } from '@/components/app/SocialPublishSection'
import { createFixtureApi } from '@/lib/app/fixtures'
import type { MarketingPack, Publication, SocialStatus } from '@/lib/app/types'

const getSocialStatus = jest.fn()
const publishToSocial = jest.fn()
const listPublications = jest.fn()
const retryPublication = jest.fn()
jest.mock('@/lib/app/client', () => ({
  api: {
    getSocialStatus: (...a: unknown[]) => getSocialStatus(...a),
    publishToSocial: (...a: unknown[]) => publishToSocial(...a),
    listPublications: (...a: unknown[]) => listPublications(...a),
    retryPublication: (...a: unknown[]) => retryPublication(...a),
  },
  errorMessage: (e: Error) => e.message,
  isFixtureMode: () => false,
}))

const CONSENT = 'I agree to post this listing, with my name and phone number, on the PUNE Property Page.'
const status = (over: Partial<SocialStatus> = {}, ch: Partial<SocialStatus['channels']> = {}): SocialStatus => ({
  dry_run: true,
  channels: { facebook_page: true, instagram: true, ...ch },
  brand: 'PUNE Property',
  media_url_ok: false,
  ...over,
})
const pub = (over: Partial<Publication> = {}): Publication => ({
  id: 'p1',
  listing_id: 'l1',
  agent_id: 'a1',
  channel: 'facebook_page',
  pack_version: 1,
  status: 'dry_run',
  external_id: null,
  permalink: null,
  error: null,
  consent: { given_at: '2026-09-29T10:00:00Z', text: CONSENT },
  approved_at: '2026-09-29T10:00:00Z',
  created_at: new Date(Date.now() - 3_600_000).toISOString(),
  updated_at: '2026-09-29T10:00:00Z',
  attempts: 1,
  payload: { text: 'x', image_urls: [] },
  ...over,
})

let pack: MarketingPack
beforeEach(async () => {
  ;[getSocialStatus, publishToSocial, listPublications, retryPublication].forEach((m) => m.mockReset())
  getSocialStatus.mockResolvedValue(status())
  listPublications.mockResolvedValue([])
  pack = await createFixtureApi({ getItem: () => null, setItem: () => undefined }).createMarketingPack('l1')
})

async function ready() {
  render(<SocialPublishSection pack={pack} />)
  await screen.findByRole('checkbox', { name: 'Facebook Page' })
}
const fb = () => screen.getByRole('checkbox', { name: 'Facebook Page' })
const ig = () => screen.getByRole('checkbox', { name: 'Instagram' })
const consent = () => screen.getByRole('checkbox', { name: CONSENT })
const postBtn = (name = 'Approve and test post') => screen.getByRole('button', { name })

describe('SocialPublishSection: gating and test mode', () => {
  it('explains itself and sends nothing on load', async () => {
    await ready()
    expect(screen.getByRole('region', { name: 'Post to PUNE Property' })).toHaveTextContent(
      'We can post this on the PUNE Property Facebook Page and Instagram. Your name and phone number appear in the post.',
    )
    expect(getSocialStatus).toHaveBeenCalledTimes(1)
    expect(listPublications).toHaveBeenCalledWith('l1')
    expect(publishToSocial).not.toHaveBeenCalled()
  })

  it('keeps the button disabled until a channel AND the consent are chosen', async () => {
    await ready()
    expect(postBtn()).toBeDisabled()
    fireEvent.click(fb())
    expect(postBtn()).toBeDisabled() // channel only
    fireEvent.click(fb())
    fireEvent.click(consent())
    expect(postBtn()).toBeDisabled() // consent only
    fireEvent.click(ig())
    expect(postBtn()).toBeEnabled()
    fireEvent.click(consent())
    expect(postBtn()).toBeDisabled()
    expect(publishToSocial).not.toHaveBeenCalled()
  })

  it('shows the test-mode banner and "Approve and test post" when dry_run is true', async () => {
    await ready()
    expect(screen.getByTestId('social-test-banner')).toHaveTextContent('Test mode: nothing is posted publicly.')
    expect(screen.getByRole('button', { name: 'Approve and test post' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Approve and post' })).toBeNull()
  })

  it('has no banner and "Approve and post" when dry_run is false', async () => {
    getSocialStatus.mockResolvedValue(status({ dry_run: false }))
    await ready()
    expect(screen.queryByTestId('social-test-banner')).toBeNull()
    expect(screen.getByRole('button', { name: 'Approve and post' })).toBeInTheDocument()
  })

  it('disables a channel that is not set up, with "Not set up yet"', async () => {
    getSocialStatus.mockResolvedValue(status({}, { instagram: false }))
    await ready()
    expect(ig()).toBeDisabled()
    expect(screen.getByText('Not set up yet')).toBeInTheDocument()
    expect(fb()).toBeEnabled()
    fireEvent.click(ig())
    fireEvent.click(consent())
    expect(postBtn()).toBeDisabled()
  })

  it('shows a friendly retry when the status cannot be loaded', async () => {
    getSocialStatus.mockRejectedValueOnce(new ApiError(500, 'boom')).mockResolvedValueOnce(status())
    render(<SocialPublishSection pack={pack} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('could not load the posting options')
    expect(screen.queryByRole('checkbox', { name: 'Facebook Page' })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('checkbox', { name: 'Facebook Page' })).toBeInTheDocument()
  })
})

describe('SocialPublishSection: posting', () => {
  it('sends the request only on the tap, with the chosen channels, approve, consent and force false', async () => {
    publishToSocial.mockResolvedValue([pub({ id: 'n1', channel: 'facebook_page' }), pub({ id: 'n2', channel: 'instagram', status: 'published', permalink: 'https://instagram.com/p/abc' })])
    await ready()
    fireEvent.click(fb())
    fireEvent.click(ig())
    fireEvent.click(consent())
    expect(publishToSocial).not.toHaveBeenCalled()
    fireEvent.click(postBtn())
    await screen.findByTestId('social-results')
    expect(publishToSocial).toHaveBeenCalledTimes(1)
    expect(publishToSocial).toHaveBeenCalledWith('l1', { channels: ['facebook_page', 'instagram'], approve: true, consent: true, force: false })

    const rows = within(screen.getByTestId('social-results'))
    expect(within(screen.getByTestId('pub-n1')).getByText('Test post')).toBeInTheDocument()
    expect(within(screen.getByTestId('pub-n2')).getByText('Posted')).toBeInTheDocument()
    expect(rows.getByRole('link', { name: 'View post' })).toHaveAttribute('href', 'https://instagram.com/p/abc')
    // approval is per post: consent and channels reset
    expect(consent()).not.toBeChecked()
  })

  it('shows a failed row with a friendly reason and retries it', async () => {
    publishToSocial.mockResolvedValue([pub({ id: 'f1', channel: 'instagram', status: 'failed', error: 'channel not configured' })])
    retryPublication.mockResolvedValue(pub({ id: 'f1', channel: 'instagram', status: 'published', permalink: 'https://instagram.com/p/z', attempts: 2 }))
    await ready()
    fireEvent.click(ig())
    fireEvent.click(consent())
    fireEvent.click(postBtn())
    const row = await screen.findByTestId('pub-f1')
    expect(within(row).getByText('Failed')).toBeInTheDocument()
    expect(row).toHaveTextContent('This channel is not set up yet')
    fireEvent.click(within(row).getByRole('button', { name: 'Try again' }))
    await waitFor(() => expect(retryPublication).toHaveBeenCalledWith('f1'))
    await waitFor(() => expect(within(screen.getByTestId('pub-f1')).getByText('Posted')).toBeInTheDocument())
    expect(within(screen.getByTestId('pub-f1')).queryByRole('button', { name: 'Try again' })).toBeNull()
  })

  it('shows a queued row', async () => {
    publishToSocial.mockResolvedValue([pub({ id: 'q1', status: 'queued' })])
    await ready()
    fireEvent.click(fb())
    fireEvent.click(consent())
    fireEvent.click(postBtn())
    expect(within(await screen.findByTestId('pub-q1')).getByText('Queued')).toBeInTheDocument()
  })

  it('shows a friendly message on 409 and keeps the choices so the agent can try again', async () => {
    publishToSocial.mockRejectedValue(new ApiError(409, 'Listing is not live'))
    await ready()
    fireEvent.click(fb())
    fireEvent.click(consent())
    fireEvent.click(postBtn())
    expect(await screen.findByRole('alert')).toHaveTextContent('This listing cannot be posted yet')
    expect(fb()).toBeChecked()
    expect(consent()).toBeChecked()
    expect(postBtn()).toBeEnabled()
  })
})

describe('SocialPublishSection: already posted and history', () => {
  it('shows an already-posted channel as done and disabled, and Post again sends force', async () => {
    listPublications.mockResolvedValue([pub({ id: 'h1', channel: 'facebook_page', status: 'published', pack_version: pack.version })])
    publishToSocial.mockResolvedValue([pub({ id: 'n9', channel: 'facebook_page', status: 'published' })])
    await ready()
    expect(fb()).toBeDisabled()
    expect(screen.getByText('Done')).toBeInTheDocument()
    expect(ig()).toBeEnabled()

    fireEvent.click(screen.getByRole('button', { name: 'Post again Facebook Page' }))
    expect(fb()).toBeEnabled()
    expect(fb()).toBeChecked()
    fireEvent.click(consent())
    fireEvent.click(postBtn())
    await screen.findByTestId('pub-n9')
    expect(publishToSocial).toHaveBeenCalledWith('l1', { channels: ['facebook_page'], approve: true, consent: true, force: true })
  })

  it('does not treat a test post of an older pack version, or a failed post, as done', async () => {
    listPublications.mockResolvedValue([
      pub({ id: 'h1', channel: 'facebook_page', status: 'published', pack_version: pack.version + 5 }),
      pub({ id: 'h2', channel: 'instagram', status: 'failed', error: 'x' }),
    ])
    await ready()
    expect(fb()).toBeEnabled()
    expect(ig()).toBeEnabled()
    expect(screen.queryByText('Done')).toBeNull()
  })

  it('lists earlier publications in the order given (newest first) with status, link and a friendly failure', async () => {
    listPublications.mockResolvedValue([
      pub({ id: 'h3', channel: 'instagram', status: 'published', permalink: 'https://instagram.com/p/3', pack_version: 2 }),
      pub({ id: 'h2', channel: 'facebook_page', status: 'failed', error: 'OAuthException token expired' }),
      pub({ id: 'h1', channel: 'facebook_page', status: 'dry_run' }),
    ])
    await ready()
    const items = within(screen.getByTestId('social-history')).getAllByRole('listitem')
    expect(items.map((li) => li.getAttribute('data-testid'))).toEqual(['history-h3', 'history-h2', 'history-h1'])
    expect(within(items[0]).getByText('Posted')).toBeInTheDocument()
    expect(within(items[0]).getByRole('link', { name: 'View post' })).toHaveAttribute('href', 'https://instagram.com/p/3')
    expect(items[0]).toHaveTextContent('Version 2')
    expect(items[1]).toHaveTextContent('needs to be reconnected')
    expect(within(items[2]).getByText('Test post')).toBeInTheDocument()
  })

  it('says nothing has been posted yet when the history is empty', async () => {
    await ready()
    expect(screen.getByTestId('social-history')).toHaveTextContent('Nothing has been posted for this listing yet.')
  })
})

describe('MarketingPackView placement', () => {
  it('puts the social section above the "Publish everywhere" block, whose note is about connecting own accounts later', async () => {
    render(<MarketingPackView pack={pack} />)
    const social = await screen.findByRole('region', { name: 'Post to PUNE Property' })
    const publish = screen.getByRole('region', { name: 'Publish everywhere' })
    expect(social.compareDocumentPosition(publish) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(publish).toHaveTextContent(/connect your own Instagram, Facebook and WhatsApp Business accounts/i)
    expect(within(publish).getAllByRole('button').every((b) => (b as HTMLButtonElement).disabled)).toBe(true)
  })
})
