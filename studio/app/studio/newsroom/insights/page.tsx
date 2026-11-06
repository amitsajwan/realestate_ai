import { redirect } from 'next/navigation'

/** SEO left the Newsroom on 2026-11-06 (/studio/seo): old links, like the weekly note's, land on the same tab. */
export default async function OldInsights({ searchParams }: { searchParams: Promise<{ tab?: string }> }) {
  const { tab } = await searchParams
  redirect(tab ? `/studio/seo?tab=${encodeURIComponent(tab)}` : '/studio/seo')
}
