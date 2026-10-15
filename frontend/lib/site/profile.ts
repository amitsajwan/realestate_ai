import { serverApiBase, fixturesForced } from './api'

/** A project's profile (backend areastats/profile.py): highlights checked against the builder's site (or two sites), and
 *  pictures and floor plans from the builder's own project page. Read only while the project is being built. */
export interface ProfilePicture {
  /** our copy, served from /uploads */
  url: string
  width: number | null
  height: number | null
  alt: string
  /** the builder's site it came from, and the page it was on */
  site: string | null
  page_url: string | null
}

export interface ProjectProfile {
  read_at: string | null
  highlights: { topic: string; text: string; official: boolean; sources: { site: string; url: string }[] }[]
  photos: ProfilePicture[]
  plans: ProfilePicture[]
}

/** The profile for a registration (its tower group's), or null. Optional extra on a page: any failure just hides it. */
export async function getProfile(regno: string | null | undefined): Promise<ProjectProfile | null> {
  if (fixturesForced() || !regno) return null
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 4000)
  try {
    const res = await fetch(serverApiBase() + '/api/v1/public/register/profile/' + encodeURIComponent(regno), {
      headers: { Accept: 'application/json' }, next: { revalidate: 3600 }, signal: ctrl.signal,
    })
    if (!res.ok) return null
    const body = (await res.json()) as ProjectProfile
    return body && (body.highlights?.length || body.photos?.length || body.plans?.length) ? body : null
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}
