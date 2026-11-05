import { datedHubs, type Grouped } from '@/lib/site/sitemap'

const B = 'https://avasetu.in'
const e = (group: string, path: string, d?: string) => ({ group, entry: { url: B + path, lastModified: d ? new Date(d) : undefined } })
const dateOf = (out: Grouped, path: string) => {
  const d = out.find((g) => g.entry.url === B + path)?.entry.lastModified
  return d ? new Date(d).toISOString() : undefined
}

test('an area page is dated by the newest page in its own area sitemap', () => {
  const out = datedHubs([
    e('area-kharadi', '/projects/area/kharadi'),
    e('area-kharadi', '/projects/a', '2026-10-01T00:00:00Z'),
    e('area-kharadi', '/projects/area/kharadi/3-bhk', '2026-10-20T00:00:00Z'),
    e('area-baner', '/projects/b', '2026-11-01T00:00:00Z'),   // another area does not move Kharadi's page
  ])
  expect(dateOf(out, '/projects/area/kharadi')).toBe('2026-10-20T00:00:00.000Z')
})

test('the list pages take their newest item and pages listing nothing dated stay undated', () => {
  const out = datedHubs([
    e('core', '/'), e('core', '/projects'), e('core', '/news'), e('core', '/builders'), e('core', '/insights'),
    e('core', '/news/7', '2026-11-04T08:00:00Z'), e('core', '/news/6', '2026-11-02T08:00:00Z'),
    e('area-baner', '/projects/b', '2026-11-01T00:00:00Z'), e('projects', '/projects/c', '2026-11-03T00:00:00Z'),
    e('agents', '/agent/x', '2026-11-05T00:00:00Z'),   // an agent's page is not on /projects
    e('builders', '/builders/kolte-patil', '2026-10-30T00:00:00Z'),
  ])
  expect(dateOf(out, '/projects')).toBe('2026-11-03T00:00:00.000Z')
  expect(dateOf(out, '/news')).toBe('2026-11-04T08:00:00.000Z')
  expect(dateOf(out, '/builders')).toBe('2026-10-30T00:00:00.000Z')
  expect(dateOf(out, '/insights')).toBeUndefined()
  expect(dateOf(out, '/')).toBeUndefined()
})

test('a page that already has its own date keeps it', () => {
  const out = datedHubs([e('core', '/news', '2026-09-01T00:00:00Z'), e('core', '/news/7', '2026-11-04T00:00:00Z')])
  expect(dateOf(out, '/news')).toBe('2026-09-01T00:00:00.000Z')
})
