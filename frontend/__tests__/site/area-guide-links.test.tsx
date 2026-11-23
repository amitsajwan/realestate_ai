/**
 * An area with its own guide (/guides/<slug>) has one page for search, and the site's links say so: they go to the guide, the
 * page the locality page names as canonical, not to the locality page Google kept showing beside it (2026-11-23).
 */
import { render } from '@testing-library/react'
import React from 'react'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import { areaGuidePath } from '@/lib/site/areaGuide'
import { registerProjectJsonLd } from '@/lib/site/projectSeo'
import type { RegisterProject } from '@/lib/site/register'

const SITE = 'https://avasetu.in'
const project = (slug: string, name: string): RegisterProject => ({
  slug: `sample-heights-${slug}`, name: 'SAMPLE HEIGHTS', regno: 'P52100011111', promoter: 'Sample Realty LLP', pincode: '412207',
  area: { key: slug.replace(/-/g, '_'), slug, name }, completion_now: '2030-06-30', completion_at_registration: '2030-06-30',
  units_total: 120, units_booked: 30, details_read_at: '2026-11-20', listed_or_updated: '2026-11-20', maharera_url: null,
  paragraph: '', indexable: true, same_area: [], source: 'MahaRERA public records',
})

describe('links to an area guide', () => {
  it('go to the full guide where the area has one, else to the locality page', () => {
    expect(areaGuidePath('upper-kharadi')).toBe('/guides/upper-kharadi')
    expect(areaGuidePath('kharadi')).toBe('/localities/kharadi')
  })

  it("name the guide in an Upper Kharadi project's breadcrumb", () => {
    const crumbs = registerProjectJsonLd({ p: project('upper-kharadi', 'Upper Kharadi'), siteUrl: SITE })
      .find((x) => x['@type'] === 'BreadcrumbList') as { itemListElement: { name: string; item: string }[] }
    expect(crumbs.itemListElement.map((i) => i.item)).toContain(`${SITE}/guides/upper-kharadi`)
    expect(JSON.stringify(crumbs)).not.toContain('/localities/upper-kharadi')
  })

  it('never link the locality page from an Upper Kharadi project page', () => {
    const { container } = render(<RegisterProjectPage p={project('upper-kharadi', 'Upper Kharadi')} siteUrl={SITE} facts={null} />)
    const hrefs = Array.from(container.querySelectorAll('a')).map((a) => a.getAttribute('href'))
    expect(hrefs).toContain('/guides/upper-kharadi')
    expect(hrefs).not.toContain('/localities/upper-kharadi')
  })

  it('keep the locality page for an area without a guide of its own', () => {
    const { container } = render(<RegisterProjectPage p={project('wagholi', 'Wagholi')} siteUrl={SITE} facts={null} />)
    expect(Array.from(container.querySelectorAll('a')).map((a) => a.getAttribute('href'))).toContain('/localities/wagholi')
  })
})
