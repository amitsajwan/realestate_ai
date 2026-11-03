import { arrivalLine, recentLeads } from '@/lib/app/leads'
import type { Lead } from '@/lib/app/types'

const NOW = new Date('2026-11-01T12:00:00Z')
const lead = (id: string, created_at: string, last_activity_at: string) => ({ id, name: id, created_at, last_activity_at }) as Lead

describe('recent leads', () => {
  it('keeps the last 7 days and orders them by when they came in, not by last activity', () => {
    const leads = [
      lead('old-but-busy', '2026-10-01T09:00:00', '2026-11-01T11:55:00'),
      lead('yesterday', '2026-10-31T10:00:00', '2026-10-31T10:00:00'),
      lead('this-morning', '2026-11-01T08:00:00', '2026-11-01T08:00:00'),
      lead('six-days', '2026-10-26T13:00:00Z', '2026-10-30T10:00:00'),
      lead('eight-days', '2026-10-24T10:00:00', '2026-10-24T10:00:00'),
    ]
    expect(recentLeads(leads, NOW).map((l) => l.id)).toEqual(['this-morning', 'yesterday', 'six-days'])
  })

  it('says when a lead came in, and when it was last active only if that was later', () => {
    expect(arrivalLine(lead('a', '2026-11-01T10:00:00', '2026-11-01T10:20:00'), NOW)).toBe('Came in 2h ago')
    expect(arrivalLine(lead('b', '2026-10-29T12:00:00', '2026-11-01T10:00:00'), NOW)).toBe('Came in 3d ago · active 2h ago')
  })
})
