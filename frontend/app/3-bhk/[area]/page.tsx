import type { Metadata } from 'next'
import FilterPage, { filterMetadata } from '@/components/marketing/FilterPage'
import type { AnyFilter } from '@/lib/site/filters'

export const revalidate = 300

type Props = { params: Promise<{ area: string }> }
const FILTER: AnyFilter = { kind: 'bhk', bhk: 3 }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  return filterMetadata(FILTER, (await params).area)
}

export default async function Page({ params }: Props) {
  return <FilterPage filter={FILTER} areaSlug={(await params).area} />
}
