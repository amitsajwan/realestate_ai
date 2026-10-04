import React from 'react'
import { render, screen } from '@testing-library/react'

jest.mock('@/components/site/ChatWidget', () => ({ __esModule: true, default: () => null }))
const mockRedirect = jest.fn((url: string) => { throw new Error('REDIRECT ' + url) })
const mockNotFound = jest.fn(() => { throw new Error('NOT_FOUND') })
jest.mock('next/navigation', () => ({
  permanentRedirect: (u: string) => mockRedirect(u),
  notFound: () => mockNotFound(),
  usePathname: () => '/posts/x',
  useRouter: () => ({ push: jest.fn() }),
}))

import PostPage, { generateMetadata } from '@/app/posts/[slug]/page'
import PostsGrid from '@/components/site/PostsGrid'
import { cleanPost, cleanPosts, fetchPost, fetchPosts, postPath, type PublicPost } from '@/lib/posts/data'
import { postJsonLd } from '@/lib/posts/seo'
import { ownPath, postParagraphs, projectPath, withoutTitle } from '@/lib/posts/text'
import { buildMarketingConfig } from '@/lib/marketing/config'

const SLUG = 'wagholi-41-projects-in-maharera-records'
const FULL = {
  id: 'r1', slug: SLUG, area: 'wagholi', audience: 'buyers', kind: 'post', channel: 'facebook', channels: ['facebook', 'instagram'],
  title: 'Wagholi: 41 projects in MahaRERA records', excerpt: 'Listed or updated this month.',
  image_url: 'https://avasetu.in/uploads/a/1.jpg', images: ['https://avasetu.in/uploads/a/1.jpg', 'https://avasetu.in/uploads/a/2.jpg'],
  site_url: 'https://avasetu.in/agent/house-deal/projects/amco-equa', permalink: 'https://fb/1',
  links: [{ channel: 'facebook', url: 'https://fb/1' }, { channel: 'instagram', url: 'https://ig/1' }],
  published_at: '2026-10-03T06:00:00Z', sample: false,
  text: 'Wagholi: 41 projects in MahaRERA records\n\nListed or updated this month.\nEvery fact: https://avasetu.in/localities/wagholi.\n\nSee https://evil.example/x too',
}

let calls: string[] = []
function mockApi(status: number, body: unknown) {
  calls = []
  global.fetch = jest.fn(async (url: string) => {
    calls.push(String(url))
    return { ok: status < 400, status, json: async () => body } as Response
  }) as unknown as typeof fetch
}

beforeEach(() => {
  process.env.NEXT_PUBLIC_SITE_URL = 'https://avasetu.in'
  mockRedirect.mockClear(); mockNotFound.mockClear()
})

describe('posts data', () => {
  it('keeps slug, area and audience, and drops malformed ones', () => {
    const [p, q] = cleanPosts([FULL, { ...FULL, id: 'r2', slug: 'Bad Slug/../x', area: 'Wagholi!', audience: 'x' }])
    expect(p).toMatchObject({ slug: SLUG, area: 'wagholi', audience: 'buyers' })
    expect(q).toMatchObject({ slug: null, area: null, audience: 'buyers' })
    expect(cleanPosts([{ ...FULL, audience: 'agents' }])[0].audience).toBe('agents')
    expect(cleanPost({ ...FULL, slug: undefined })).toBeNull()
    expect(cleanPost(FULL)?.text).toContain('41 projects')
    expect(postPath(SLUG)).toBe('/posts/' + SLUG)
  })

  it('fetchPosts passes the area; fetchPost says notFound only on a 404', async () => {
    mockApi(200, [FULL])
    const res = await fetchPosts(6, 'wagholi')
    expect(res.ok && res.posts[0].slug).toBe(SLUG)
    expect(calls[0]).toMatch(/\/api\/v1\/public\/posts\?limit=6&area=wagholi$/)
    mockApi(404, null)
    expect(await fetchPost('nope')).toEqual({ ok: false, notFound: true })
    mockApi(500, null)
    expect(await fetchPost('nope')).toEqual({ ok: false, notFound: false })
    expect(await fetchPost('../etc')).toEqual({ ok: false, notFound: true })
  })
})

describe('post text', () => {
  it('links only our own site, as site paths', () => {
    expect(ownPath('https://avasetu.in/localities/wagholi', 'https://avasetu.in')).toBe('/localities/wagholi')
    expect(ownPath('https://avasetu.in.evil.com/x', 'https://avasetu.in')).toBeNull()
    expect(ownPath('https://avasetu.in//evil.com', 'https://avasetu.in')).toBeNull()
    expect(projectPath('https://avasetu.in/agent/house-deal/projects/amco-equa', 'https://avasetu.in')).toBe('/agent/house-deal/projects/amco-equa')
    expect(projectPath('https://avasetu.in/projects/amco-equa', 'https://avasetu.in')).toBe('/projects/amco-equa')
    expect(projectPath('https://avasetu.in/localities/wagholi', 'https://avasetu.in')).toBeNull()
    const paras = postParagraphs(withoutTitle(FULL.text, FULL.title), 'https://avasetu.in')
    expect(paras).toHaveLength(2)
    expect(paras[0][1]).toEqual([{ text: 'Every fact: ' }, { text: 'avasetu.in/localities/wagholi', href: '/localities/wagholi' }, { text: '.' }])
    expect(paras[1][0]).toEqual([{ text: 'See https://evil.example/x too' }])
  })
})

describe('/posts/<slug> page', () => {
  it('shows the title, slides, text, date, links to its area, its project and Facebook/Instagram', async () => {
    mockApi(200, FULL)
    render(await PostPage({ params: Promise.resolve({ slug: SLUG }) }))
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Wagholi: 41 projects in MahaRERA records')
    expect(screen.getByTestId('slide-strip').querySelectorAll('img')).toHaveLength(2)
    expect(screen.getByText('3 Oct 2026')).toBeInTheDocument()
    const text = screen.getByTestId('post-text')
    expect(text.textContent).not.toContain('41 projects') // the title is the heading, not repeated
    expect(screen.getByRole('link', { name: 'avasetu.in/localities/wagholi' })).toHaveAttribute('href', '/localities/wagholi')
    expect(screen.queryByRole('link', { name: /evil/ })).toBeNull()
    expect(screen.getByTestId('post-area-link')).toHaveAttribute('href', '/localities/wagholi')
    expect(screen.getByTestId('post-area-link')).toHaveTextContent('More about Wagholi')
    expect(screen.getByTestId('post-project-link')).toHaveAttribute('href', '/agent/house-deal/projects/amco-equa')
    expect(screen.getByRole('link', { name: /View on Instagram/ })).toHaveAttribute('href', 'https://ig/1')
    const ld = Array.from(document.querySelectorAll('script[type="application/ld+json"]')).map((s) => JSON.parse(s.innerHTML))
    expect(ld[0]).toMatchObject({ '@type': 'Article', mainEntityOfPage: 'https://avasetu.in/posts/' + SLUG, datePublished: FULL.published_at })
  })

  it('has its own title, description and canonical address', async () => {
    mockApi(200, FULL)
    const meta = await generateMetadata({ params: Promise.resolve({ slug: SLUG }) })
    expect(meta.title).toBe('Wagholi: 41 projects in MahaRERA records | Avasetu')
    expect(meta.alternates?.canonical).toBe('https://avasetu.in/posts/' + SLUG)
    expect(String(meta.description)).toMatch(/^Listed or updated this month\./)
    expect(String(meta.description)).not.toContain('http')
  })

  it('a post without an area or project shows no such links; an older address redirects; unknown is a 404', async () => {
    mockApi(200, { ...FULL, area: null, site_url: null })
    render(await PostPage({ params: Promise.resolve({ slug: SLUG }) }))
    expect(screen.queryByTestId('post-area-link')).toBeNull()
    expect(screen.queryByTestId('post-project-link')).toBeNull()
    mockApi(200, FULL)
    await expect(PostPage({ params: Promise.resolve({ slug: SLUG + '-r1abcd' }) })).rejects.toThrow('REDIRECT /posts/' + SLUG)
    mockApi(404, null)
    await expect(PostPage({ params: Promise.resolve({ slug: 'gone' }) })).rejects.toThrow('NOT_FOUND')
  })

  it('Article data names the area as a place', () => {
    const post = cleanPost(FULL)!
    expect(postJsonLd(buildMarketingConfig({}), post, 'Wagholi').contentLocation).toEqual({ '@type': 'Place', name: 'Wagholi, Pune' })
  })
})

describe('PostCard opens the post page', () => {
  it('links the title (and a single picture) to /posts/<slug>, keeping See the project and Facebook', () => {
    const [p] = cleanPosts([{ ...FULL, images: [] }]) as PublicPost[]
    render(<PostsGrid posts={[p]} />)
    expect(screen.getByTestId('post-page-link')).toHaveAttribute('href', '/posts/' + SLUG)
    expect(document.querySelector(`a[href="/posts/${SLUG}"] img`)).not.toBeNull()
    expect(screen.getByTestId('post-site-link')).toHaveAttribute('href', FULL.site_url)
    expect(screen.getByRole('link', { name: /^Facebook/ })).toHaveAttribute('href', 'https://fb/1')
  })

  it('a row without a slug has no page link', () => {
    const [p] = cleanPosts([{ ...FULL, slug: null }])
    render(<PostsGrid posts={[p]} />)
    expect(screen.queryByTestId('post-page-link')).toBeNull()
  })
})

describe('sitemap', () => {
  it('lists every post page, dated by its post', async () => {
    const { default: sitemap } = await import('@/app/sitemap')
    calls = []
    global.fetch = jest.fn(async (url: string) => {
      calls.push(String(url))
      const posts = String(url).includes('/public/posts')
      return { ok: posts, status: posts ? 200 : 503, json: async () => [FULL, { ...FULL, id: 'r2', slug: null }] } as unknown as Response
    }) as unknown as typeof fetch
    const map = await sitemap()
    const entry = map.find((e) => e.url === 'https://avasetu.in/posts/' + SLUG)
    expect(entry?.lastModified).toEqual(new Date(FULL.published_at))
    expect(map.filter((e) => e.url.includes('/posts/'))).toHaveLength(1)
    expect(calls.some((u) => /\/public\/posts\?limit=500$/.test(u))).toBe(true)
  })
})
