import { boardTitle, shareText, type BoardCard } from '@/lib/app/leadBoard'
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
  const c = { areas: ['Wagholi'], genuine: 'talked' } as BoardCard
  const text = shareText([c, { ...c, areas: ['Kharadi'], genuine: 'number' }], 'https://avasetu.in/studio/lead-board')
  expect(text).toContain('2 buyer leads on Avasetu (Wagholi, Kharadi), 1 already spoke with us.')
  expect(text).toContain('https://avasetu.in/studio/lead-board')
})
