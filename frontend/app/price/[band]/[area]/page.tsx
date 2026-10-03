import type { Metadata } from 'next'
import FilterPage, { filterMetadata } from '@/components/marketing/FilterPage'
import { type AnyFilter, BANDS } from '@/lib/site/filters'

export const revalidate = 300

type Props = { params: Promise<{ band: string; area: string }> }

function filter(slug: string): AnyFilter | null {
  const band = BANDS.find((b) => b.slug === slug)
  return band ? { kind: 'band', band } : null
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { band, area } = await params
  return filterMetadata(filter(band), area)
}

export default async function Page({ params }: Props) {
  const { band, area } = await params
  return <FilterPage filter={filter(band)} areaSlug={area} />
}
