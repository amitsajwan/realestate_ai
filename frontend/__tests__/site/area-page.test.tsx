/**
 * One page per area (components/area/AreaPage, 2026-11-23): a guide about an area is that area's page, the locality page sends
 * there, and the page's sections are tabs that jump, never tabs that hide.
 */
import fs from 'fs'
import path from 'path'
import React from 'react'
import { fireEvent, render, screen, within } from '@testing-library/react'
import SectionNav from '@/components/area/SectionNav'
import { KeyFigures, areaFaqs } from '@/components/area/AreaPage'
import { pageLocality } from '@/components/area/pageLocality'
import type { AreaStats } from '@/components/localities/areaStats'
import { LOCALITIES } from '@/lib/marketing/localities'
import { AREA_GUIDES } from '@/lib/site/areaGuide'
import type { Topic } from '@/lib/site/topics'

const TOPICS = path.join(__dirname, '..', '..', '..', 'backend', 'app', 'modules', 'calendar', 'topics')

test('every guide written about one of our areas is that area\'s one page, and every such page has its guide', () => {
  // a topic about an area left out of AREA_GUIDES would be a second page for the area, beside a locality page that does not redirect
  const topics = fs.readdirSync(TOPICS).filter((f) => f.endsWith('.json')).map((f) => f.replace(/\.json$/, ''))
  const areas = new Set(LOCALITIES.map((l) => l.slug))
  expect(new Set(topics.filter((t) => areas.has(t)))).toEqual(AREA_GUIDES)
})

describe('the section bar', () => {
  const items = [{ id: 'map', label: 'Map' }, { id: 'guide', label: 'Guide' }, { id: 'questions', label: 'Questions' }]

  test('is a list of links to the sections on the page, so it works before JavaScript and each section can be shared', () => {
    render(<SectionNav items={items} />)
    const nav = screen.getByRole('navigation', { name: 'On this page' })
    expect(within(nav).getAllByRole('link').map((a) => [a.textContent, a.getAttribute('href')]))
      .toEqual([['Map', '#map'], ['Guide', '#guide'], ['Questions', '#questions']])
  })

  test('marks the first section, then the one picked', () => {
    render(<SectionNav items={items} />)
    expect(screen.getByRole('link', { name: 'Map' })).toHaveAttribute('aria-current', 'location')
    fireEvent.click(screen.getByRole('link', { name: 'Questions' }))
    expect(screen.getByRole('link', { name: 'Questions' })).toHaveAttribute('aria-current', 'location')
    expect(screen.getByRole('link', { name: 'Map' })).not.toHaveAttribute('aria-current')
  })

  test('is left out when the page has one section or none', () => {
    const { container } = render(<SectionNav items={[items[0]]} />)
    expect(container.innerHTML).toBe('')
  })
})

describe('the key figures at the top', () => {
  const stats = (over: Partial<AreaStats>): AreaStats => ({
    area: { key: 'upper_kharadi', name: 'Upper Kharadi', slug: 'upper-kharadi', tier: 'affordable' }, as_of: '2026-11-20', projects: 9,
    completing: [], registered: [], units_total: 6668, units_booked: 3794, recent: [], source: 'MahaRERA public records', ...over,
  })

  test('say projects, homes and the share booked, dated, with the count linking every project', () => {
    render(<KeyFigures stats={stats({})} allHref="/projects/area/upper-kharadi" />)
    const box = screen.getByTestId('key-figures')
    expect(box.textContent).toContain('9 projects on MahaRERA')
    expect(box.textContent).toContain('6,668 homes registered')
    expect(box.textContent).toContain('57% of those homes booked')
    expect(box.textContent).toContain('MahaRERA register, as of 20 November 2026')
    expect(within(box).getByRole('link', { name: '9' })).toHaveAttribute('href', '/projects/area/upper-kharadi')
  })

  test('never give a booked share without a total it fits inside', () => {
    render(<KeyFigures stats={stats({ units_booked: 7000 })} allHref={null} />)
    expect(screen.getByTestId('key-figures').textContent).not.toContain('booked')
    render(<KeyFigures stats={stats({ units_total: null })} allHref={null} />)
    expect(screen.getAllByTestId('key-figures')[1].textContent).not.toMatch(/registered|booked/)
  })

  test('are left out without MahaRERA figures', () => {
    const { container } = render(<KeyFigures stats={stats({ projects: 0 })} allHref={null} />)
    expect(container.innerHTML).toBe('')
  })
})

test('the questions are asked once: the guide\'s, the area\'s, then the ones its figures answer', () => {
  const l = pageLocality('upper-kharadi')
  const topic = { lang: 'en', faq: [{ q: { en: 'What is the difference between Kharadi and Upper Kharadi?' }, a: { en: 'From the guide.' } }] } as unknown as Topic
  const qs = areaFaqs(l, topic, [{ q: 'Is there a metro station near Upper Kharadi?', a: 'Ramwadi.' }])
  expect(qs.filter((f) => /difference between Kharadi/.test(f.q))).toEqual([{ q: 'What is the difference between Kharadi and Upper Kharadi?', a: 'From the guide.' }])
  expect(qs[qs.length - 1].q).toBe('Is there a metro station near Upper Kharadi?')
})

test("a guide in Marathi asks only its own questions, not the area's English ones", () => {
  const topic = { lang: 'mr', faq: [{ q: { mr: 'प्रश्न', en: 'Question' }, a: { mr: 'उत्तर', en: 'Answer' } }] } as unknown as Topic
  expect(areaFaqs(pageLocality('upper-kharadi'), topic, [{ q: 'Is there a metro?', a: 'No.' }])).toEqual([{ q: 'प्रश्न', a: 'उत्तर' }])
})
