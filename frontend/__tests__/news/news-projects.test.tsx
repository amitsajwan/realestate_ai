// A news story links the project pages it names (docs/plan/insights-and-seo.md S4)
import React from 'react'
import { render, screen, within } from '@testing-library/react'
import NewsArticle from '@/components/news/NewsArticle'
import { cleanNewsItem } from '@/lib/news/data'
import { FIXTURE_NEWS } from '@/lib/news/fixtures'
import { storyProjects } from '@/lib/news/projects'

const pages: Record<string, unknown> = {
  'rohan-abhilasha-4-wagholi': { slug: 'rohan-abhilasha-4-wagholi', name: 'ROHAN ABHILASHA 4', marketed_name: 'Rohan Abhilasha 4', promoter: 'Rohan Builders',
    completion_now: '2029-10-30', units_total: 416, units_booked: 244 },
  // a second tower of the same project: its slug answers with the project's one page
  'gera-world-of-joy-tower-2': { slug: 'gera-world-of-joy', name: 'Geras World of Joy', marketed_name: 'Gera World of Joy', completion_now: null },
  'gera-world-of-joy': { slug: 'gera-world-of-joy', name: 'Geras World of Joy', marketed_name: 'Gera World of Joy', completion_now: null },
}
jest.mock('@/lib/site/register', () => ({
  ...jest.requireActual('@/lib/site/register'),
  getRegisterProject: async (slug: string) => {
    if (slug === 'down') throw new Error('Project data is temporarily unavailable')
    return pages[slug] ?? null
  },
}))

describe('projects a story names', () => {
  it('reads them from the API, dropping a malformed slug', () => {
    const item = cleanNewsItem({ id: '1', headline: 'H', projects: [{ regno: 'P1', slug: 'rohan-abhilasha-4-wagholi' }, { regno: 'P2', slug: '../x' }, { slug: 'y' }] })!
    expect(item.projects).toEqual([{ regno: 'P1', slug: 'rohan-abhilasha-4-wagholi' }])
    expect(cleanNewsItem({ id: '1', headline: 'H' })!.projects).toEqual([])
  })

  it('names each from its own page, once per project, leaving out a page that is gone or cannot be read', async () => {
    const got = await storyProjects({ projects: ['rohan-abhilasha-4-wagholi', 'gera-world-of-joy', 'gera-world-of-joy-tower-2', 'gone', 'down']
      .map((slug, i) => ({ regno: `P${i}`, slug })) })
    expect(got).toEqual([
      { slug: 'rohan-abhilasha-4-wagholi', name: 'Rohan Abhilasha 4', line: 'by Rohan Builders · possession Oct 2029 · 244/416 booked' },
      { slug: 'gera-world-of-joy', name: 'Gera World of Joy', line: '' },
    ])
    expect(await storyProjects({})).toEqual([])
  })

  it('the story page links them under their own heading, and shows nothing when it names none', () => {
    const { unmount } = render(<NewsArticle item={FIXTURE_NEWS[1]} projects={[{ slug: 'rohan-abhilasha-4-wagholi', name: 'Rohan Abhilasha 4', line: 'by Rohan Builders' }]} />)
    const box = screen.getByTestId('news-projects')
    expect(within(box).getByRole('heading')).toHaveTextContent('The project in this story')
    expect(within(box).getByRole('link', { name: 'Rohan Abhilasha 4' })).toHaveAttribute('href', '/projects/rohan-abhilasha-4-wagholi')
    expect(box).toHaveTextContent('by Rohan Builders')
    unmount()
    render(<NewsArticle item={FIXTURE_NEWS[1]} />)
    expect(screen.queryByTestId('news-projects')).toBeNull()
  })
})
