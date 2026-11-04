/** How each area list is made, in the words both the list pages (app/projects/area/[place]/[...facet]) and the About page say
 *  it: one text, so the method a list shows and the one we publish never drift apart. Mirrors backend seo/facets.py. */
export const HOW_PATH = '/about#how-we-check'

export const HOW: Record<string, string> = {
  'new-launches': 'Projects registered with MahaRERA in the last 12 months, newest first.',
  top: 'Projects still being built or finished within a year that have 10 or more homes not booked and 40 or more homes in all, one row per project, ranked by homes booked in the last 90 days where two of our readings of MahaRERA show it, else by homes booked a month since registration (a project registered under six months counts as six months old). Each row says whether the builder moved the completion date and how many of the builder\'s Pune projects kept theirs. Booked counts are the builders\' own, filed on MahaRERA each quarter. Projects with fewer homes open are listed apart, never ranked. Offices and shops are left out.',
  'ready-to-move': 'Projects whose completion date filed with MahaRERA passed in the last three years and that still have 10 or more homes not booked, newest first. Offices and shops are left out. MahaRERA does not show the occupancy certificate, so ask the builder for it.',
  all: 'Projects still being built, earliest filed completion date first.',
}
