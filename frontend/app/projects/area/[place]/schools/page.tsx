import type { Metadata } from 'next'
import { ResearchPage, researchMetadata, type ResearchProps } from '@/components/site/research/PlaceResearchPage'

// /projects/area/<place>/schools: the place's schools research (components/site/research/PlaceResearchPage). A static segment, so it is
// served before the area lists' catch-all ([...facet]). Rendered on first visit, then kept for an hour like the research.
export const revalidate = 3600
export const dynamicParams = true
export async function generateStaticParams(): Promise<{ place: string }[]> {
  return []
}

export async function generateMetadata({ params }: ResearchProps): Promise<Metadata> {
  return researchMetadata('schools', params)
}

export default function Page({ params }: ResearchProps) {
  return <ResearchPage kind="schools" params={params} />
}
