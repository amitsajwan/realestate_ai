/** SEO → To do: each list says what it means, and the decision buttons reach the server. */
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import TodoTab from '@/app/studio/seo/TodoTab'
import type { SplitProject } from '@/lib/app/insights'

const mockRankings = jest.fn()
const mockDecide = jest.fn()
jest.mock('@/lib/app/insights', () => ({
  getRankings: (...a: unknown[]) => mockRankings(...a),
  decideSplit: (...a: unknown[]) => mockDecide(...a),
}))

const row = (over: Partial<SplitProject> = {}): SplitProject => ({
  name: 'Aldea Annexo', where: '411045', ours: false, why: 'tower label', homes: 120, state: 'no_proof', hint: null, impressions: 12,
  searches: [{ phrase: 'aldea annexo phase 4', impressions: 6, position: 7.7 }],
  members: [{ regno: 'P1', name: 'Aldea Annexo C2', slug: 'a', impressions: 8, in_search: true }, { regno: 'P2', name: 'Aldea Annexo D', slug: 'b', impressions: 4, in_search: false }],
  ...over,
})
const data = (items: SplitProject[], decided: unknown[] = []) => ({
  split: { total: items.length, proved: 0, waiting: 0, no_proof: items.length, items, decided },
  request_indexing: [],
  conflicts: { at: null, total: 1, items: [{ phrase: 'rosewood park wagholi', impressions: 6, position: 9.7, kind: 'project_and_list',
    pages: [{ path: '/projects/area/wagholi', kind: 'area', label: 'Wagholi' }, { path: '/projects/rosewood', kind: 'project', label: 'Rosewood Park' }] }] },
})

beforeEach(() => { mockRankings.mockReset(); mockDecide.mockReset(); mockDecide.mockResolvedValue({ decision: 'same' }) })

it('says a search showing a project and its list is normal, with the pages named', async () => {
  mockRankings.mockResolvedValue(data([]))
  render(<TodoTab />)
  expect(await screen.findByText('Nothing to do here.')).toBeInTheDocument()
  expect(screen.getByText('A project page and a list page (1)')).toBeInTheDocument()
  expect(screen.getByText('Rosewood Park')).toBeInTheDocument()
})

it('tells what a split project shows and merges only after the question', async () => {
  mockRankings.mockResolvedValue(data([row()]))
  render(<TodoTab />)
  expect(await screen.findByText(/Buyers searched "aldea annexo phase 4"/)).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Same project' }))
  expect(mockDecide).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button', { name: 'Yes, merge' }))
  await waitFor(() => expect(mockDecide).toHaveBeenCalledWith(['P1', 'P2'], 'same'))
})

it('keeps towers separate at one press', async () => {
  mockRankings.mockResolvedValue(data([row()]))
  render(<TodoTab />)
  fireEvent.click(await screen.findByRole('button', { name: 'Keep separate' }))
  await waitFor(() => expect(mockDecide).toHaveBeenCalledWith(['P1', 'P2'], 'apart'))
})

it('quiet projects wait behind Show all', async () => {
  mockRankings.mockResolvedValue(data([row({ name: 'Quiet Towers', searches: [], impressions: 0 })]))
  render(<TodoTab />)
  fireEvent.click(await screen.findByRole('button', { name: 'Show all 1' }))
  expect(screen.getByText('Quiet Towers')).toBeInTheDocument()
})

it('a project the web proved has no merge button', async () => {
  mockRankings.mockResolvedValue(data([row({ state: 'proved' })]))
  render(<TodoTab />)
  fireEvent.click(await screen.findByRole('button', { name: 'Show all 1' }))
  expect(screen.getByRole('button', { name: 'Keep separate' })).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Same project' })).toBeNull()
})

it('a decision can be undone', async () => {
  mockRankings.mockResolvedValue(data([], [{ decision: 'same', name: 'Nivaan Grandeur', regnos: ['P1', 'P2'] }]))
  render(<TodoTab />)
  fireEvent.click(await screen.findByRole('button', { name: 'Undo' }))
  await waitFor(() => expect(mockDecide).toHaveBeenCalledWith(['P1', 'P2'], 'undo'))
})
