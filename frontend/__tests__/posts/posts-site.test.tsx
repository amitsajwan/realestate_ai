import React from 'react'
import { render, screen } from '@testing-library/react'
import PostsGrid, { PostsSkeleton } from '@/components/site/PostsGrid'
import SocialStrip from '@/components/site/SocialStrip'
import ContactBlock from '@/components/marketing/ContactBlock'
import { cleanPosts, formatPostDate, type PublicPost } from '@/lib/posts/data'
import { DEFAULT_FACEBOOK_URL, DEFAULT_INSTAGRAM_URL } from '@/lib/marketing/social'
import { buildMarketingConfig } from '@/lib/marketing/config'
import { organizationJsonLd } from '@/lib/marketing/seo'

const post = (o: Partial<PublicPost> = {}): PublicPost => ({
  id: 'a', kind: 'post', channel: 'facebook', channels: ['facebook'], title: 'Why carpet area matters', excerpt: 'Ask for carpet area under RERA.',
  image_url: 'https://media.example.com/uploads/a.jpg', images: [], site_url: null, permalink: 'https://www.facebook.com/p/1',
  links: [{ channel: 'facebook', url: 'https://www.facebook.com/p/1' }], published_at: '2026-10-02T06:00:00Z', sample: false, ...o,
})

describe('PostCard like Instagram', () => {
  it('shows every carousel slide to swipe, and leads with the page on our own site', () => {
    const images = [1, 2, 3, 4, 5].map((k) => `https://avasetu.in/uploads/hd/amco-${k}.jpg`)
    render(<PostsGrid posts={[post({ images, site_url: 'https://avasetu.in/agent/house-deal/projects/amco-equa' })]} />)
    expect(screen.getByTestId('slide-strip').querySelectorAll('img')).toHaveLength(5)
    expect(screen.getByAltText(/slide 3 of 5/)).toHaveAttribute('src', images[2])
    expect(screen.getByTestId('post-site-link')).toHaveAttribute('href', 'https://avasetu.in/agent/house-deal/projects/amco-equa')
    expect(screen.getByRole('link', { name: /^Facebook/ })).toHaveAttribute('target', '_blank')
  })

  it('drops slide and site urls that are not https', () => {
    const [p] = cleanPosts([{ id: 'x', title: 't', links: [{ channel: 'facebook', url: 'https://fb/1' }],
      images: ['https://ok/1.jpg', 'http://bad/2.jpg', 'javascript:alert(1)'], site_url: 'http://avasetu.in/x' }])
    expect(p.images).toEqual(['https://ok/1.jpg'])
    expect(p.site_url).toBeNull()
  })
})

describe('PostsGrid', () => {
  it('renders cards with new-tab, noopener links per channel', () => {
    render(<PostsGrid posts={[post({ channels: ['facebook', 'instagram'], links: [
      { channel: 'facebook', url: 'https://www.facebook.com/p/1' }, { channel: 'instagram', url: 'https://www.instagram.com/reel/x/' }] })]} />)
    const fb = screen.getByRole('link', { name: /View on Facebook/ })
    const ig = screen.getByRole('link', { name: /View on Instagram/ })
    for (const a of [fb, ig]) { expect(a).toHaveAttribute('target', '_blank'); expect(a.getAttribute('rel')).toContain('noopener') }
    expect(ig).toHaveAttribute('href', 'https://www.instagram.com/reel/x/')
    expect(screen.getByText('2 Oct 2026')).toBeInTheDocument()
    expect(screen.queryByText('Sample home')).toBeNull()
  })

  it('labels sample homes', () => {
    render(<PostsGrid posts={[post({ sample: true, kind: 'showcase' })]} />)
    expect(screen.getByText('Sample home')).toBeInTheDocument()
  })

  it('empty state is honest, with no cards', () => {
    render(<PostsGrid posts={[]} />)
    expect(screen.getByText('First posts going out now')).toBeInTheDocument()
    expect(screen.queryByTestId('post-card')).toBeNull()
  })

  it('an outage is not shown as "no posts yet"', () => {
    render(<PostsGrid posts={[]} failed />)
    expect(screen.getByText('Posts are not loading right now')).toBeInTheDocument()
  })

  it('skeleton is marked busy', () => {
    render(<PostsSkeleton count={2} />)
    expect(screen.getByTestId('posts-skeleton')).toHaveAttribute('aria-busy', 'true')
  })
})

describe('cleanPosts', () => {
  it('drops rows without an https link and non-https images', () => {
    const out = cleanPosts([
      { id: '1', links: [{ channel: 'facebook', url: 'javascript:alert(1)' }] },
      { id: '2', links: [{ channel: 'instagram', url: 'https://www.instagram.com/p/z/' }], image_url: 'http://x/y.jpg', sample: true, kind: 'showcase' },
      null, 'x',
    ])
    expect(out).toHaveLength(1)
    expect(out[0]).toMatchObject({ id: '2', channel: 'instagram', image_url: null, sample: true })
    expect(cleanPosts({})).toEqual([])
  })
  it('formats dates in IST and tolerates junk', () => {
    expect(formatPostDate('2026-10-02T20:00:00Z')).toBe('3 Oct 2026')
    expect(formatPostDate('nope')).toBe('')
  })
})

describe('social strip and contact block', () => {
  it('links to the real Facebook Page and Instagram in a new tab', () => {
    render(<SocialStrip />)
    expect(screen.getByRole('link', { name: /Facebook/ })).toHaveAttribute('href', DEFAULT_FACEBOOK_URL)
    expect(screen.getByRole('link', { name: /Instagram/ })).toHaveAttribute('href', 'https://www.instagram.com/avasetu_/')
    expect(DEFAULT_INSTAGRAM_URL).toBe('https://www.instagram.com/avasetu_/')
    for (const a of screen.getAllByRole('link')) expect(a.getAttribute('rel')).toContain('noopener')
  })

  it('contact block names the website, Facebook and Instagram and has no phone, email or person', () => {
    render(<ContactBlock />)
    const block = screen.getByTestId('contact-block')
    expect(block.textContent).toContain('Contact Avasetu via this website (tap I am interested on any home or use the chat; agents can request an invite), Facebook and Instagram.')
    expect(block.textContent).not.toMatch(/\d{5}|@|tel:|mailto:|whatsapp/i)
    expect(screen.getByRole('link', { name: 'request an invite' })).toHaveAttribute('href', expect.stringContaining('request-invite'))
  })

  it('Organization json-ld carries sameAs', () => {
    const ld = organizationJsonLd(buildMarketingConfig({}), 'd', [DEFAULT_FACEBOOK_URL, DEFAULT_INSTAGRAM_URL])
    expect(ld.sameAs).toEqual([DEFAULT_FACEBOOK_URL, DEFAULT_INSTAGRAM_URL])
    expect(organizationJsonLd(buildMarketingConfig({}), 'd').sameAs).toBeUndefined()
  })
})
