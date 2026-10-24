import React from 'react'
import { fireEvent, render, screen, within } from '@testing-library/react'

// The guide page reads its topic from the API: replaced here with a small Upper Kharadi-shaped topic.
const mockFetchTopic = jest.fn()
jest.mock('@/lib/site/topics', () => ({ ...jest.requireActual('@/lib/site/topics'), fetchTopic: (slug: string) => mockFetchTopic(slug) }))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
jest.mock('next/navigation', () => ({ notFound: () => { throw new Error('NOT_FOUND') } }))
jest.mock('@/components/site/PostsGrid', () => ({ __esModule: true, default: () => null }))

import TopicPage from '@/app/guides/[slug]/page'
import { OPEN_CHAT_EVENT } from '@/components/site/ChatWidget'

const en = (x: string) => ({ en: x })
const TOPIC = {
  slug: 'upper-kharadi', lang: 'en', status: null, checked_on: '2026-10-19',
  title: en('Upper Kharadi'), summary: en('Summary'), status_line: en('Status'), dates: [],
  sections: [
    { id: 'where', heading: en('Where is Upper Kharadi?'), items: { en: ['**PIN code reality:** Most projects carry 412207.'] } },
    {
      id: 'projects', heading: en('Projects'), items: { en: [] },
      table: {
        columns: ['Project', 'Booked'],
        rows: [
          { cells: ['Gera World of Joy M', '320 (100%)'], href: '/projects/geras-world-of-joy-m-wagholi', tag: 'resale' },
          { cells: ['Godrej Ivara', '489 (18%)'], href: '/projects/godrej-ivara-pune', tag: 'open' },
        ],
      },
    },
    {
      id: 'prices', heading: en('What does it cost?'), items: { en: [] },
      tables: [
        { title: en('Locality averages'), columns: ['What', 'Figure', 'Source'], rows: [{ cells: ['Kharadi', '₹14,199', 'Square Yards'] }] },
        { title: en('Project specifics'), columns: ['Project', 'Price', 'Source'], rows: [{ cells: ['Lodha Camelot 3 BHK', '₹2.21 crore', 'Homebazaar'], href: '/projects/lodha-camelot' }] },
      ],
    },
    {
      id: 'check', heading: en('Seven questions'), items: { en: ['What is the MahaRERA number?'] },
      cta: { text: en('Want the MahaRERA record?'), button: en('Chat with us now'), message: en('I want the MahaRERA details') },
    },
  ],
  results: null, faq: [], links: [], warning: en('Check papers'), sources: [], updates: [],
}

beforeEach(() => mockFetchTopic.mockResolvedValue({ ok: true, topic: TOPIC }))

async function page() {
  render(await TopicPage({ params: Promise.resolve({ slug: 'upper-kharadi' }) }))
}

test('an item lead-in is bold without its asterisks', async () => {
  await page()
  expect(screen.getByText('PIN code reality:').tagName).toBe('STRONG')
  expect(screen.queryByText(/\*\*/)).toBeNull()
})

test('project rows link our page and carry an availability chip and tint', async () => {
  await page()
  const row = screen.getByRole('link', { name: 'Godrej Ivara' }).closest('tr')!
  expect(row.getAttribute('data-tag')).toBe('open')
  expect(within(row).getByText('High availability')).toBeTruthy()
  const full = screen.getByRole('link', { name: 'Gera World of Joy M' }).closest('tr')!
  expect(within(full).getByText('Resale only')).toBeTruthy()
})

test('prices show two titled tables and no booking row', async () => {
  await page()
  expect(screen.getByRole('heading', { name: 'Locality averages' })).toBeTruthy()
  expect(screen.getByRole('heading', { name: 'Project specifics' })).toBeTruthy()
  expect(screen.getAllByRole('table')).toHaveLength(3)
})

test('the cta button opens the chat with its question', async () => {
  await page()
  const heard = jest.fn()
  window.addEventListener(OPEN_CHAT_EVENT, (e) => heard((e as CustomEvent).detail))
  fireEvent.click(screen.getByRole('button', { name: 'Chat with us now' }))
  expect(heard).toHaveBeenCalledWith({ message: 'I want the MahaRERA details' })
})
