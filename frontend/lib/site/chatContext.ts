/**
 * What the visitor is looking at, taken from the page path, so the chat assistant can answer about THAT home or area.
 * /agent/<slug>/listings/<id> (also /agent/<slug>/<id>)  ->  { listing_id }
 * /localities/<slug>                                    ->  { locality }
 * /projects/<slug>                                      ->  { project }
 * The server re-checks every value; this only reads the URL.
 */
export interface ChatContext { listing_id?: string; locality?: string; post_id?: string; project?: string }

const ID = /^[A-Za-z0-9_-]{1,64}$/
const SLUG = /^[a-z][a-z-]{1,39}$/
const PROJECT = /^[a-z0-9][a-z0-9-]{1,119}$/

export function chatContextFromPath(pathname: string | null | undefined): ChatContext | undefined {
  const parts = (pathname || '').split('?')[0].split('#')[0].split('/').filter(Boolean)
  if (parts[0] === 'agent' && parts.length >= 3) {
    const id = parts[2] === 'listings' ? parts[3] : parts[2]
    if (id && ID.test(id)) return { listing_id: id }
  }
  if (parts[0] === 'localities' && parts[1] && SLUG.test(parts[1])) return { locality: parts[1] }
  // a project page (not /projects/area/... lists): the chat answers about that project, and does not ask which area
  if (parts[0] === 'projects' && parts.length === 2 && PROJECT.test(parts[1])) return { project: parts[1] }
  return undefined
}
