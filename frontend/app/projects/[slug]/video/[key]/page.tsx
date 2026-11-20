import type { Metadata } from 'next'
import { WatchPage, watchMetadata } from '../watch'

export const revalidate = 3600
export const dynamicParams = true

type Props = { params: Promise<{ slug: string; key: string }> }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug, key } = await params
  return watchMetadata(slug, key)
}

/** One more of the agent's videos of the project on a page of its own (../watch.tsx). */
export default async function ProjectAgentVideoPage({ params }: Props) {
  const { slug, key } = await params
  return WatchPage({ slug, key })
}
