import type { Metadata } from 'next'
import { WatchPage, watchMetadata } from './watch'

export const revalidate = 3600
export const dynamicParams = true

type Props = { params: Promise<{ slug: string }> }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  return watchMetadata((await params).slug, null)
}

/** The project's first video on a page of its own (./watch.tsx). */
export default async function ProjectVideoPage({ params }: Props) {
  return WatchPage({ slug: (await params).slug, key: null })
}
