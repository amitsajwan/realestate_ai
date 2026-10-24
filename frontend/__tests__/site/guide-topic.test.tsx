import React from 'react'
import fs from 'fs'
import path from 'path'
import { fireEvent, render, screen, within } from '@testing-library/react'
import { OPEN_CHAT_EVENT } from '@/lib/site/chatApi'

// The guide page reads the real topic file (backend calendar/topics/upper-kharadi.json) as the API would send it.
const TOPIC = JSON.parse(fs.readFileSync(path.join(__dirname, '../../../backend/app/modules/calendar/topics/upper-kharadi.json'), 'utf8'))
delete TOPIC.row_prefixes
jest.mock('@/lib/site/api', () => ({ serverApiBase: () => 'http://api' }))
jest.mock('@/lib/site/noCacheOnError', () => ({ dontCacheThisRender: async () => {} }))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
jest.mock('next/navigation', () => ({ notFound: () => { throw new Error('NOT_FOUND') } }))

import TopicPage from '@/app/guides/[slug]/page'

beforeEach(() => {
  global.fetch = jest.fn(async () => ({ ok: true, status: 200, json: async () => ({ ...TOPIC, updates: [] }) })) as unknown as typeof fetch
})

async function page() {
  render(await TopicPage({ params: Promise.resolve({ slug: 'upper-kharadi' }) }))
}

function section(heading: string): HTMLElement {
  return screen.getByRole('heading', { level: 2, name: heading }).closest('section') as HTMLElement
}

describe('Upper Kharadi guide', () => {
  it('splits the prices into locality averages and project specifics, with no project-table row among them', async () => {
    await page()
    const prices = section('What does it cost?')
    const tables = within(prices).getAllByRole('table')
    expect(within(prices).getAllByRole('heading', { level: 3 }).map((h) => h.textContent)).toEqual(['Locality averages', 'Project specifics'])
    expect(tables).toHaveLength(2)
    expect(prices).not.toHaveTextContent('World of Joy')
    for (const t of tables) for (const row of within(t).getAllByRole('row')) expect(row.children).toHaveLength(3)
    expect(within(tables[1]).getByRole('link', { name: 'Lodha Camelot 3 BHK' })).toHaveAttribute('href', '/projects/lodha-camelot')
  })

  it('bolds the lead-in of each "Where is Upper Kharadi?" item', async () => {
    await page()
    const where = section('Where is Upper Kharadi?')
    const leads = within(where).getAllByRole('listitem').map((li) => li.querySelector('strong')?.textContent)
    expect(leads[0]).toBe('PIN code reality:')
    expect(leads).toContain('The "New Kharadi" confusion:')
    expect(where).not.toHaveTextContent('**')
  })

  it('links every project name in the big table and tags it by how much is booked', async () => {
    await page()
    const table = within(section('The big projects and how much is already booked')).getByRole('table')
    expect(within(table).getByRole('link', { name: /Godrej Ivara/ })).toHaveAttribute('href', '/projects/godrej-ivara-pune')
    expect(within(table).getAllByRole('link', { name: 'Lodha Giardino (Lodha)' })).toHaveLength(2)
    const ivara = within(table).getByRole('link', { name: /Godrej Ivara/ }).closest('tr') as HTMLElement
    expect(ivara).toHaveTextContent('Under 30% booked: high availability')
    const worldOfJoy = within(table).getByRole('link', { name: /World of Joy/ }).closest('tr') as HTMLElement
    expect(worldOfJoy).toHaveTextContent('95%+ booked: mostly resale')
  })

  it('writes the unconfirmed metro date as a sentence and its state as its own capitalised tag', async () => {
    await page()
    const metro = screen.getByText(/Metro opening at Ubale Nagar/).closest('div') as HTMLElement
    expect(metro).toHaveTextContent(/four years to build\.\s*Not confirmed$/)
    expect(metro).not.toHaveTextContent('not confirmed')
  })

  it('puts a chat call to action after the seven questions that opens the chat with the question asked', async () => {
    await page()
    const heard: string[] = []
    const listen = (e: Event) => heard.push((e as CustomEvent<{ message: string }>).detail.message)
    window.addEventListener(OPEN_CHAT_EVENT, listen)
    fireEvent.click(within(section('Seven questions to ask before you pay a token')).getByRole('button', { name: 'Chat with us now' }))
    window.removeEventListener(OPEN_CHAT_EVENT, listen)
    expect(heard).toEqual(['I want the MahaRERA details for a tower in Upper Kharadi'])
  })
})
