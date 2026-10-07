import { createFixtureApi, FIXTURE_STATE_KEY } from '@/lib/app/fixtures'
import {
  channelLabel,
  doneChannels,
  friendlyPublishError,
  publishRequestError,
  statusLabel,
} from '@/lib/app/social'
import { ApiError } from '@/lib/app/api'

const mem = () => {
  const m: Record<string, string> = {}
  return { m, getItem: (k: string) => m[k] ?? null, setItem: (k: string, v: string) => void (m[k] = v) }
}
const both = { channels: ['facebook_page', 'instagram'] as Array<'facebook_page' | 'instagram'>, approve: true, consent: true }

describe('fixture social publishing', () => {
  it('uses a bumped storage key', () => {
    expect(FIXTURE_STATE_KEY).toBe('app_fixture_state_v6')
  })

  it('reports dry run with both channels configured', async () => {
    const api = createFixtureApi(mem())
    expect(await api.getSocialStatus()).toEqual({
      dry_run: true,
      channels: { facebook_page: true, instagram: true },
      brand: 'Avasetu',
      media_url_ok: false,
    })
  })

  it('409s without a pack, and 422s without approval or consent', async () => {
    const api = createFixtureApi(mem())
    await expect(api.publishToSocial('l1', both)).rejects.toMatchObject({ status: 409 })
    await api.createMarketingPack('l1')
    await expect(api.publishToSocial('l1', { ...both, consent: false })).rejects.toMatchObject({ status: 422 })
    await expect(api.publishToSocial('l1', { ...both, approve: false })).rejects.toMatchObject({ status: 422 })
    await expect(api.publishToSocial('nope', both)).rejects.toMatchObject({ status: 404 })
    expect(await api.listPublications('l1')).toEqual([])
  })

  it('409s for a listing that is not live', async () => {
    const api = createFixtureApi(mem())
    await api.createMarketingPack('l1')
    await api.setListingStatus('l1', 'paused')
    await expect(api.publishToSocial('l1', both)).rejects.toMatchObject({ status: 409 })
  })

  it('records dry_run publications with a snapshot of what would be posted, newest first', async () => {
    const api = createFixtureApi(mem())
    const pack = await api.createMarketingPack('l1')
    const created = await api.publishToSocial('l1', both)
    expect(created.map((p) => p.channel)).toEqual(['facebook_page', 'instagram'])
    for (const p of created) {
      expect(p).toMatchObject({ listing_id: 'l1', status: 'dry_run', pack_version: pack.version, permalink: null, error: null, attempts: 1 })
      expect(p.consent.text).toMatch(/Avasetu Page/)
    }
    expect(created[0].payload.text).toContain(pack.share_url)
    expect(created[0].payload.image_urls).toHaveLength(1)
    expect(created[1].payload.image_urls).toHaveLength(pack.instagram.images.length)

    await api.publishToSocial('l1', { ...both, channels: ['instagram'], force: true })
    const items = await api.listPublications('l1')
    expect(items).toHaveLength(3)
    expect(items[0].channel).toBe('instagram')
    expect(new Set(items.map((p) => p.id)).size).toBe(3)
  })

  it('does not post the same channel and pack version twice unless forced', async () => {
    const api = createFixtureApi(mem())
    await api.createMarketingPack('l1')
    await api.publishToSocial('l1', { ...both, channels: ['instagram'] })
    await expect(api.publishToSocial('l1', { ...both, channels: ['instagram'] })).rejects.toMatchObject({ status: 409 })
    await expect(api.publishToSocial('l1', { ...both, channels: ['instagram'], force: true })).resolves.toHaveLength(1)
    // another channel is still fine
    await expect(api.publishToSocial('l1', { ...both, channels: ['facebook_page'] })).resolves.toHaveLength(1)
  })

  it('a new pack version can be posted again without force', async () => {
    const api = createFixtureApi(mem())
    await api.createMarketingPack('l1')
    await api.publishToSocial('l1', { ...both, channels: ['instagram'] })
    await api.createMarketingPack('l1')
    await expect(api.publishToSocial('l1', { ...both, channels: ['instagram'] })).resolves.toHaveLength(1)
  })

  it('retry works only for failed publications', async () => {
    const s = mem()
    const api = createFixtureApi(s)
    await api.createMarketingPack('l1')
    const [p] = await api.publishToSocial('l1', { ...both, channels: ['instagram'] })
    await expect(api.retryPublication(p.id)).rejects.toMatchObject({ status: 409 })
    await expect(api.retryPublication('nope')).rejects.toMatchObject({ status: 404 })

    const state = JSON.parse(s.m[FIXTURE_STATE_KEY])
    state.publications[0].status = 'failed'
    state.publications[0].error = 'channel not configured'
    s.m[FIXTURE_STATE_KEY] = JSON.stringify(state)
    const again = createFixtureApi(s)
    const retried = await again.retryPublication(p.id)
    expect(retried).toMatchObject({ id: p.id, status: 'dry_run', error: null, attempts: 2 })
    expect((await again.listPublications('l1'))[0].status).toBe('dry_run')
  })

  it('persists publications in storage', async () => {
    const s = mem()
    await createFixtureApi(s).createMarketingPack('l1')
    await createFixtureApi(s).publishToSocial('l1', both)
    expect(await createFixtureApi(s).listPublications('l1')).toHaveLength(2)
  })
})

describe('social helpers', () => {
  it('labels channels and statuses in plain language', () => {
    expect(channelLabel('facebook_page')).toBe('Facebook Page')
    expect(channelLabel('instagram')).toBe('Instagram')
    expect(statusLabel('published')).toBe('Posted')
    expect(statusLabel('dry_run')).toBe('Test post')
    expect(statusLabel('failed')).toBe('Failed')
    expect(statusLabel('queued')).toBe('Queued')
  })

  it('doneChannels counts published/dry_run of the current pack version only', () => {
    const p = (channel: 'facebook_page' | 'instagram', status: 'published' | 'failed' | 'dry_run', v: number) =>
      ({ channel, status, pack_version: v }) as never
    const set = doneChannels([p('facebook_page', 'published', 2), p('instagram', 'failed', 2), p('instagram', 'dry_run', 1)], 2)
    expect([...set]).toEqual(['facebook_page'])
  })

  it('turns technical errors into friendly ones', () => {
    expect(friendlyPublishError('channel not configured')).toMatch(/not set up yet/)
    expect(friendlyPublishError('OAuthException: token expired')).toMatch(/reconnected/)
    expect(friendlyPublishError('image_url could not be fetched')).toMatch(/photo/)
    expect(friendlyPublishError(null)).toMatch(/did not go through/)
    expect(publishRequestError(new ApiError(409, 'Listing is not live'))).toMatch(/cannot be posted yet/)
    expect(publishRequestError(new ApiError(409, 'Already posted'))).toMatch(/already posted/i)
    expect(publishRequestError(new ApiError(0, 'Cannot reach the server. Check your internet.'))).toMatch(/Cannot reach/)
    expect(publishRequestError(new Error('x'))).toMatch(/did not go through/)
  })
})
