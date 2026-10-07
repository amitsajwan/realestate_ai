import { redirect } from 'next/navigation'

/** The old pilot page: links already shared in groups and old reels keep working and land on the free-trial page, with their ?src= tag. */
export default async function PilotPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const src = (await searchParams).src
  const tag = typeof src === 'string' ? src.toLowerCase().replace(/[^a-z0-9_-]/g, '').slice(0, 40) : ''
  redirect(tag ? `/trial?src=${tag}` : '/trial')
}
