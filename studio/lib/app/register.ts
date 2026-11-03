/** The project register as Studio uses it (the owner's spotlight editor): Studio's copy of the browser half of the site's
 *  frontend/lib/site/register.ts. The site's module also renders the register pages on the server, so it stays with the site;
 *  keep the two in step when the search API changes. */

/** The name buyers know the project by: how they search for it (search_name), else the marketed name, else MahaRERA's. */
export function displayName(p: { name: string; marketed_name?: string | null; search_name?: string | null }): string {
  return (p.search_name || '').trim() || (p.marketed_name || '').trim() || p.name
}

/** One hit from GET /api/v1/public/register/search. */
export interface RegisterSearchHit {
  slug: string
  name: string
  marketed_name?: string | null
  regno: string
  promoter?: string | null
  area?: string | null
  place_name?: string | null
  completion_now?: string | null
  units_total?: number | null
  units_booked?: number | null
  checked?: number | null
  checks_total?: number
  active?: boolean
  /** months the possession date moved later since registration (0: not moved; null: unknown): the project check's pill */
  months_later?: number | null
}

/** Search the register by name (marketed, legal or alias), builder or MahaRERA number. In the browser (the public API base, as shared/config/api); any failure gives an empty list. */
export async function searchRegister(q: string, limit = 20, signal?: AbortSignal): Promise<RegisterSearchHit[]> {
  const t = q.trim()
  if (t.length < 2) return []
  const base = (process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || '').replace(/\/+$/, '')
  try {
    const res = await fetch(`${base}/api/v1/public/register/search?q=${encodeURIComponent(t.slice(0, 80))}&limit=${limit}`,
      { headers: { Accept: 'application/json' }, signal })
    if (!res.ok) return []
    const data = await res.json()
    return Array.isArray(data) ? (data as RegisterSearchHit[]) : []
  } catch {
    return []
  }
}
