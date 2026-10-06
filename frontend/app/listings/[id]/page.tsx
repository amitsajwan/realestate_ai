import { notFound, permanentRedirect } from 'next/navigation'
import { getListingById } from '@/lib/site/api'
import { agentPath, normalizeSlug } from '@/lib/site/slug'

type Props = {
  params: Promise<{ id: string }>
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}

export default async function LegacyListingPage({ params, searchParams }: Props) {
  const { id } = await params
  const listing = await getListingById(id)
  const slug = normalizeSlug(listing?.agent?.slug)
  if (!listing || !slug) notFound()
  const src = (await searchParams).src
  const suffix = typeof src === 'string' && src ? `?src=${encodeURIComponent(src)}` : ''
  permanentRedirect(agentPath(slug, 'listings/' + listing.id) + suffix)
}
