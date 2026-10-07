import React from 'react'
import type { Metadata } from 'next'
import LegalPage from '@/components/marketing/LegalPage'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { PATHS, termsDoc } from '@/lib/marketing/strings'

export function generateMetadata(): Metadata {
  const cfg = getMarketingConfig()
  const d = termsDoc(cfg)
  return pageMetadata(cfg, { title: d.metaTitle, description: d.metaDescription, path: PATHS.terms })
}

export default function TermsPage() {
  const cfg = getMarketingConfig()
  return <LegalPage doc={termsDoc(cfg)} cfg={cfg} />
}
