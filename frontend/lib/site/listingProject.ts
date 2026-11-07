import type { CatalogProject, PublicListing } from './types'

const norm = (s: string | null | undefined): string => (s || '').trim().toLowerCase().replace(/\s+/g, ' ')

type Named = Pick<Partial<PublicListing>, 'project_name' | 'about'> & { rera_no?: string | null }

/** The shared project a listing belongs to: by MahaRERA number, else by name. The listing page shows that project's page, so its
 *  metadata and the sitemap ask the same question: a listing with no number matched by name was a whole copy of the project
 *  page naming itself as canonical. */
export function projectForListing(listing: Named, projects: CatalogProject[]): CatalogProject | null {
  const rera = norm(listing.rera_no)
  if (rera) {
    const byRera = projects.find((p) => norm(p.rera_no) === rera)
    if (byRera) return byRera
  }
  const name = norm(listing.project_name || listing.about?.project_name)
  return name ? projects.find((p) => norm(p.name) === name || p.agents.some((a) => norm(a.project_slug).replace(/-/g, ' ') === name)) || null : null
}
