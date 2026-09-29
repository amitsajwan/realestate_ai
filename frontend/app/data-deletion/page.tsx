import React from 'react'
import type { Metadata } from 'next'
import LegalPage from '@/components/marketing/LegalPage'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { PATHS, deletionDoc } from '@/lib/marketing/strings'

export function generateMetadata(): Metadata {
  const cfg = getMarketingConfig()
  const d = deletionDoc(cfg)
  return pageMetadata(cfg, { title: d.metaTitle, description: d.metaDescription, path: PATHS.deletion })
}

export default function DataDeletionPage() {
  const cfg = getMarketingConfig()
  return <LegalPage doc={deletionDoc(cfg)} cfg={cfg} />
}
