/**
 * Where a link to an area's guide goes. An area with a full guide of its own (`/guides/<slug>`, a topic page) has one page for
 * search: its locality page names the guide as canonical and leaves the sitemap (265ed70f). A canonical is only a hint, and
 * Google kept showing /localities/upper-kharadi beside the guide for "upper kharadi" because every link on the site still
 * pointed at the locality page (Search Console, 2026-11-23: 118 impressions on it, the guide linked from nowhere). So the
 * site's own links name the same page as the canonical.
 *
 * Kept here rather than read from the topics API because the links sit in pages that render without it; an area joins this
 * list when its topic page goes live.
 */
export const AREA_GUIDES: ReadonlySet<string> = new Set(['upper-kharadi'])

export const areaGuidePath = (slug: string): string =>
  AREA_GUIDES.has(slug) ? `/guides/${slug}` : `/localities/${slug}`
