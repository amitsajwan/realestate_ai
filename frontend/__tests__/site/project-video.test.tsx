import { render, screen } from '@testing-library/react'
import React from 'react'
import ProjectVideo, { isoDuration, projectVideoJsonLd } from '@/components/site/ProjectVideo'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import { projectVideoSitemapXml } from '@/lib/site/projectVideos'
import type { PropertyFactsView } from '@/lib/site/types'
import type { MainVideo, RegisterProject } from '@/lib/site/register'

jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: () => <section id="enquire" /> }))

// owner 2026-11-20: the listing's marketing video belongs on our page, stored by us, so Google credits the page for it
const VIDEO: MainVideo = {
  url: '/api/v1/public/listing-video/L1-abc123.mp4', poster: '/api/v1/public/listing-video/L1-abc123.jpg', seconds: 24,
  headline: '2 BHK homes in Mundhwa from ₹1.26 Cr', uploaded_at: '2026-11-20',
}

const P = {
  slug: 'unique-uni-89-mundhwa', name: 'Unique UNI 89', regno: 'P52100055555', promoter: 'Unique Builders',
  area: { key: 'mundhwa', slug: 'mundhwa', name: 'Mundhwa' }, completion_now: '2030-04-30', units_total: 200, units_booked: 50,
  indexable: true, same_area: [], source: 'MahaRERA public records',
} as unknown as RegisterProject

const facts = (main_video?: MainVideo) =>
  ({ maharera: { rera_no: P.regno }, offer: { price_inr: 12600000, main_video } }) as unknown as PropertyFactsView

describe('the listing video on the project page', () => {
  it('plays our own file with its poster, loads nothing before play, and tells Google what it is', () => {
    const { container } = render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={facts(VIDEO)} />)
    const video = screen.getByTestId('project-video').querySelector('video')!
    expect(video).toHaveAttribute('src', VIDEO.url)
    expect(video).toHaveAttribute('poster', VIDEO.poster)
    expect(video).toHaveAttribute('preload', 'none')
    expect(screen.getByTestId('project-video')).toHaveTextContent('2 BHK homes in Mundhwa from ₹1.26 Cr · 24 seconds')
    const ld = Array.from(container.querySelectorAll('script[type="application/ld+json"]')).map((s) => JSON.parse(s.innerHTML))
    const vo = ld.find((x) => x['@type'] === 'VideoObject')
    expect(vo).toMatchObject({ contentUrl: 'https://avasetu.in' + VIDEO.url, thumbnailUrl: 'https://avasetu.in' + VIDEO.poster,
      uploadDate: '2026-11-20', duration: 'PT24S', url: 'https://avasetu.in/projects/unique-uni-89-mundhwa' })
  })

  it('shows no video section when the listing has none', () => {
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={facts()} />)
    expect(screen.queryByTestId('project-video')).toBeNull()
  })

  it('an agent copy of the page plays it without the structured data', () => {
    const { container } = render(<ProjectVideo video={VIDEO} shown="Unique UNI 89" siteUrl="https://avasetu.in" pageUrl="/x" ld={false} />)
    expect(container.querySelector('script')).toBeNull()
    expect(container.querySelector('video')).not.toBeNull()
  })

  it('Google gets no VideoObject without a picture or a date, and lengths read as ISO 8601', () => {
    expect(projectVideoJsonLd({ ...VIDEO, poster: null }, 'X', 'https://avasetu.in', '/x')).toBeNull()
    expect(projectVideoJsonLd({ ...VIDEO, uploaded_at: null }, 'X', 'https://avasetu.in', '/x')).toBeNull()
    expect([isoDuration(24), isoDuration(65), isoDuration(120), isoDuration(null)]).toEqual(['PT24S', 'PT1M5S', 'PT2M', undefined])
  })
})

describe('the listing videos sitemap', () => {
  it('names each watch page with its video, picture, length and date, and leaves out a video with no picture', () => {

    const xml = projectVideoSitemapXml('https://avasetu.in/', [
      { slug: 'unique-uni-89-mundhwa', name: 'Unique UNI 89 & Co', video: VIDEO },
      { slug: 'no-picture', name: 'X', video: { ...VIDEO, poster: null } },
    ])
    expect(xml).toContain('xmlns:video="http://www.google.com/schemas/sitemap-video/1.1"')
    expect(xml).toContain('<loc>https://avasetu.in/projects/unique-uni-89-mundhwa/video</loc>')
    expect(xml).toContain(`<video:content_loc>https://avasetu.in${VIDEO.url}</video:content_loc>`)
    expect(xml).toContain(`<video:thumbnail_loc>https://avasetu.in${VIDEO.poster}</video:thumbnail_loc>`)
    expect(xml).toContain('<video:title>Unique UNI 89 &amp; Co: homes, prices and MahaRERA details</video:title>')
    expect(xml).toContain('<video:duration>24</video:duration>')
    expect(xml).toContain('<video:publication_date>2026-11-20</video:publication_date>')
    expect(xml).not.toContain('no-picture')
  })

  it('the project page links the video to its own page', () => {
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={facts(VIDEO)} />)
    expect(screen.getByTestId('project-video-page')).toHaveAttribute('href', '/projects/unique-uni-89-mundhwa/video')
  })
})
