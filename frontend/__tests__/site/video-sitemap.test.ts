import { videoSitemapXml } from '@/lib/site/videoSitemap'

describe('the video sitemap', () => {
  it('lists each project page with its from-space video, escaped, and skips pages with no video', () => {
    const xml = videoSitemapXml('https://avasetu.in', [
      { slug: 'yashwin', name: 'VJ Yashwin & Co', place: 'Upper Kharadi', story: 'Ground cleared <then> built.', picture: '/uploads/from_above/p1/2026.webp',
        video: { src: '/uploads/from_above/p1/months.mp4', poster: '/uploads/from_above/p1/months.webp', from: '2021-01-01', to: '2026-11-01', months: 43 },
        years: [2021, 2026], updated: '2026-11-20', seasons: 17 },
      { slug: 'none', name: 'No video', place: null, story: 'x', picture: '/uploads/from_above/p2/2026.webp', video: null,
        years: [2021, 2026], updated: null, seasons: 0 },
    ])
    expect(xml).toContain('xmlns:video="http://www.google.com/schemas/sitemap-video/1.1"')
    expect(xml).toContain('<loc>https://avasetu.in/projects/yashwin</loc>')
    expect(xml).toContain('<video:content_loc>https://avasetu.in/uploads/from_above/p1/months.mp4</video:content_loc>')
    expect(xml).toContain('<video:title>VJ Yashwin &amp; Co from space, 2021 to 2026</video:title>')
    expect(xml).toContain('Ground cleared &lt;then&gt; built.')
    expect(xml).not.toContain('/projects/none')
  })
})
