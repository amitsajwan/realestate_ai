import { activityLine, areaCounts, boardTitle, shareText, type BoardCard } from '@/lib/app/leadBoard'
import { nextAfterLogin } from '@/lib/app/session'

test('after signing in, only a Studio path in ?next= is followed', () => {
  expect(nextAfterLogin('?next=%2Fstudio%2Flead-board')).toBe('/studio/lead-board')
  expect(nextAfterLogin('?next=https%3A%2F%2Fevil.example')).toBe('/studio')
  expect(nextAfterLogin('?next=%2F%2Fevil.example')).toBe('/studio')
  expect(nextAfterLogin('')).toBe('/studio')
})

test('a card is titled by its project, else by what and where', () => {
  expect(boardTitle({ project: 'Mansha Phase-II', bhk: '2 BHK', areas: ['Wagholi'] })).toBe('Mansha Phase-II')
  expect(boardTitle({ project: null, bhk: '2 BHK', areas: ['Wagholi', 'Kharadi'] })).toBe('2 BHK in Wagholi, Kharadi')
  expect(boardTitle({ project: null, bhk: null, areas: [] })).toBe('A home in Pune')
})

test('the share text counts the buyers and names the areas', () => {
  const c = { areas: ['Wagholi'], genuine: 'replied' } as BoardCard
  const text = shareText([c, { ...c, areas: ['Kharadi'], genuine: 'number' }], 'https://avasetu.in/studio/lead-board')
  expect(text).toContain('2 buyer leads on Avasetu (Wagholi, Kharadi), 1 already replied to us.')
  expect(text).toContain('https://avasetu.in/studio/lead-board')
})

test('the activity line reads visits, days, reading, device and city, leaving out what is unknown', () => {
  const a = { pages: [], more_pages: 0, page_count: 0, projects_seen: 0, visits: 2, days: 2, read_min: 9, device: 'Phone' as const,
    city: 'Wagholi', taps: [], enquiries: 1 }
  expect(activityLine(a)).toBe('2 visits on 2 days · 9 min reading · Phone · Wagholi')
  expect(activityLine({ ...a, visits: 1, days: 1, read_min: 0, city: null })).toBe('1 visit · Phone')
})

test('area chips count leads per area, busiest first', () => {
  expect(areaCounts([{ areas: ['Kharadi'] }, { areas: ['Wagholi', 'Kharadi'] }, { areas: ['Wagholi'] }, { areas: ['Baner'] }, { areas: [] }]))
    .toEqual([{ area: 'Kharadi', count: 2 }, { area: 'Wagholi', count: 2 }, { area: 'Baner', count: 1 }])
})


test('the message to one agent greets them by name', () => {
  const text = shareText([{ areas: ['Moshi'], genuine: 'replied' } as BoardCard], 'https://avasetu.in/studio/lead-board', 'Stavan')
  expect(text.startsWith('Namaste Stavan ji, Avasetu team here.')).toBe(true)
  expect(text).toContain('1 buyer lead on Avasetu (Moshi), 1 already replied to us.')
})
