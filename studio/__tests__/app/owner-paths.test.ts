import { ownerOnlyPath } from '@/lib/app/owner'

it('names the owner screens and their sub-pages, and nothing an agent uses', () => {
  for (const p of ['/studio/admin', '/studio/seo', '/studio/newsroom', '/studio/newsroom/projects', '/studio/press', '/studio/site', '/studio/agents', '/studio/agents/a1/listings/new'])
    expect(ownerOnlyPath(p)).toBe(true)
  for (const p of ['/studio', '/studio/leads', '/studio/listings/l1', '/studio/content', '/studio/radar', '/studio/area-photos', '/studio/lead-board', '/studio/profile', '/studio/seoul'])
    expect(ownerOnlyPath(p)).toBe(false)
})
