/** SEO → Audit: every page with its group and action, filtered by group, read again on demand, downloadable as CSV. */
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import AuditTab, { auditCsv } from '@/app/studio/seo/AuditTab'
import type { AuditRow, AuditView } from '@/lib/app/insights'

const mockAudit = jest.fn()
jest.mock('@/lib/app/insights', () => ({ getAudit: (...a: unknown[]) => mockAudit(...a) }))

const row = (over: Partial<AuditRow> = {}): AuditRow => ({
  path: '/projects/godrej-ivara', kind: 'project', bucket: 'earning', action: 'Earns clicks: keep it steady', clicks: 9,
  impressions: 300, ctr: 0.03, position: 4.2, impressions_before: 100, trend: 'rising', index_state: 'Submitted and indexed',
  in_sitemap: true, top_search: 'godrej ivara price', top_search_impressions: 90, ...over,
})
const view = (rows: AuditRow[], over: Partial<AuditView> = {}): AuditView => ({
  configured: true, at: '2026-11-19T09:00:00Z', error: null, pages: rows.length,
  buckets: [{ key: 'earning', label: 'Earning clicks', pages: rows.filter((r) => r.bucket === 'earning').length },
    { key: 'not_indexed', label: 'Not indexed', pages: rows.filter((r) => r.bucket === 'not_indexed').length }],
  by_kind: { project: { clicks: 9 } }, rows, ...over,
})

beforeEach(() => mockAudit.mockReset())

it('shows each page with its numbers, top search and action', async () => {
  mockAudit.mockResolvedValue(view([row()]))
  render(<AuditTab />)
  expect(await screen.findByText('/projects/godrej-ivara')).toBeInTheDocument()
  expect(screen.getByText('Found for "godrej ivara price" (90)')).toBeInTheDocument()
  expect(screen.getByText('Earns clicks: keep it steady')).toBeInTheDocument()
  expect(screen.getByText(/rising \(100 before\)/)).toBeInTheDocument()
})

it('filters to one group at a press', async () => {
  mockAudit.mockResolvedValue(view([row(), row({ path: '/builders/x', kind: 'builder', bucket: 'not_indexed', action: 'Request indexing' })]))
  render(<AuditTab />)
  fireEvent.click(await screen.findByRole('button', { name: 'Not indexed 1' }))
  expect(screen.getByText('/builders/x')).toBeInTheDocument()
  expect(screen.queryByText('/projects/godrej-ivara')).not.toBeInTheDocument()
})

it('reads Google again only when asked', async () => {
  mockAudit.mockResolvedValueOnce(view([row()])).mockResolvedValueOnce(view([row({ clicks: 12 })]))
  render(<AuditTab />)
  fireEvent.click(await screen.findByRole('button', { name: 'Read again now' }))
  await waitFor(() => expect(mockAudit).toHaveBeenLastCalledWith(true))
  expect(await screen.findByText(/12 clicks/)).toBeInTheDocument()
})

it('says what is missing when the server has no Search Console key', async () => {
  mockAudit.mockResolvedValue(view([], { configured: false }))
  render(<AuditTab />)
  expect(await screen.findByText(/needs the Search Console key/)).toBeInTheDocument()
})

it('keeps a comma or a quote inside its CSV cell', () => {
  const csv = auditCsv([row({ top_search: 'flats, "kharadi"' })]).split('\n')
  expect(csv[0].startsWith('path,kind,bucket')).toBe(true)
  expect(csv[1]).toContain('"flats, ""kharadi"""')
})
