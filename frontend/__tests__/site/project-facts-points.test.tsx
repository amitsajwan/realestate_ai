import { render, screen } from '@testing-library/react'
import ProjectProfile from '@/components/site/ProjectProfile'

const point = (topic: string, text: string, official: boolean, sites: number) => ({
  topic, text, official, sources: Array.from({ length: sites }, (_, i) => ({ site: `s${i}.com`, url: official ? `https://s${i}.com` : null })),
})

const profile = {
  read_at: '2026-11-04', photos: [], plans: [],
  highlights: [point('parking', 'Covered parking', false, 2), point('open_space', 'Project spans 12 acres', false, 2), point('security', 'CCTV at the gate', false, 1), point('clubhouse', 'Three-storey clubhouse', true, 1)],
}

describe('the project facts and amenities', () => {
  it('puts land with the project facts, apart from the amenities', () => {
    render(<ProjectProfile profile={profile as never} name="Rose Court" part="highlights" />)
    expect(screen.getByRole('heading', { name: 'Project facts' })).toBeTruthy()
    expect(screen.getByRole('heading', { name: 'Amenities' })).toBeTruthy()
  })

  // one site's word stays on the record, not the page (2026-11-20; it was shown marked "(not yet confirmed)")
  it("says the source only for the builder, and leaves out what one property site alone says", () => {
    render(<ProjectProfile profile={profile as never} name="Rose Court" part="highlights" />)
    expect(screen.queryByText(/2 property sites/)).toBeNull()
    expect(screen.queryByText(/not yet confirmed/)).toBeNull()
    expect(screen.queryByText(/CCTV at the gate/)).toBeNull()
    expect(screen.getByText(/Covered parking/)).toBeTruthy()
    expect(screen.getByText(/the builder.s site\s*\)?/i, { selector: 'a' })).toBeTruthy()
  })
})
