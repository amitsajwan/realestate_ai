import { distinctPhotos } from '@/components/site/ProfilePictures'
import type { ProfilePicture } from '@/lib/site/profile'

// the eight photos on /projects/godrej-ivara-pune (2026-10-25); the 2nd and 5th are the same pool render, 17 bits apart
const IVARA = ['1701086a6a6ff73f', '9d0e0e4d29202c29', '5251626343a382a0', '0b0b92929a2b3b1f',
  'cc1d0e0e4929202c', '91e48e8b35061a58', 'e87071a7a22a36de', '986ae7c647c7c383']
const pic = (h: string, extra: Partial<ProfilePicture> = {}): ProfilePicture => ({
  url: `/uploads/project_media/pr1260002502426/${h}.webp`, width: 1600, height: 900, alt: '', site: null, page_url: null,
  source: 'builder', ...extra,
} as ProfilePicture)
const names = (ps: ProfilePicture[]) => ps.map((p) => p.url.slice(-21, -5))

describe('project gallery', () => {
  it('shows a render saved twice once, and every different picture', () => {
    expect(names(distinctPhotos(IVARA.map((h) => pic(h))))).toEqual(IVARA.filter((h) => h !== 'cc1d0e0e4929202c'))
  })

  it("keeps the builder's copy, else the larger, in the first copy's place", () => {
    expect(names(distinctPhotos([pic(IVARA[0]), pic(IVARA[1], { width: 1200, height: 675 }), pic(IVARA[4])]))).toEqual([IVARA[0], IVARA[4]])
    expect(distinctPhotos([pic(IVARA[1], { source: 'brochure' }), pic(IVARA[4], { width: 800, height: 450 })])[0].source).toBe('builder')
  })

  it('never merges pictures not named by their hash (brochure pages, AI illustrations)', () => {
    const brochure = [0, 1, 2].map((i) => ({ ...pic('x'), url: `/uploads/brochures/b/page-${i}.webp`, source: 'brochure' } as ProfilePicture))
    expect(distinctPhotos(brochure)).toEqual(brochure)
  })
})
