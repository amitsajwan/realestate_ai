import { render, screen } from '@testing-library/react'
import ProjectProfile from '@/components/site/ProjectProfile'

const point = (topic: string, text: string, official: boolean, sites: number) => ({
  topic, text, official, sources: Array.from({ length: sites }, (_, i) => ({ site: `s${i}.com`, url: official ? `https://s${i}.com` : null })),
})

const profile = {
  read_at: '2026-11-04', photos: [], plans: [],
  highlights: [point('parking', 'Covered parking', false, 2), point('open_space', 'Project spans 12 acres', false, 1), point('clubhouse', 'Three-storey clubhouse', true, 1)],
}

describe('the project facts and amenities', () => {
  it('puts land with the project facts, apart from the amenities', () => {
    render(<ProjectProfile profile={profile as never} name="Rose Court" part="highlights" />)
    expect(screen.getByRole('heading', { name: 'Rose Court project facts' })).toBeTruthy()
    expect(screen.getByRole('heading', { name: 'Rose Court amenities' })).toBeTruthy()
  })

  it('says the source only for the builder or a single site', () => {
    render(<ProjectProfile profile={profile as never} name="Rose Court" part="highlights" />)
    expect(screen.queryByText(/2 property sites/)).toBeNull()
    expect(screen.getByText('(one property site)')).toBeTruthy()
    expect(screen.getByText(/the builder.s site\s*\)?/i, { selector: 'a' })).toBeTruthy()
  })
})
