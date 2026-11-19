/** Studio screens only the owner can use: the server refuses their data to everyone else, so an agent who opens one by a link
 *  or an old bookmark is told so instead of seeing a server error (2026-11-19). */
export const OWNER_PATHS = ['/studio/admin', '/studio/seo', '/studio/newsroom', '/studio/press', '/studio/site', '/studio/agents']

export function ownerOnlyPath(path: string): boolean {
  return OWNER_PATHS.some((p) => path === p || path.startsWith(p + '/'))
}
