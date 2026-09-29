import React from 'react'
import type { Metadata } from 'next'
import LegalPage from '@/components/marketing/LegalPage'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { PATHS, privacyDoc } from '@/lib/marketing/strings'

export function generateMetadata(): Metadata {
  const cfg = getMarketingConfig()
  const d = privacyDoc(cfg)
  return pageMetadata(cfg, { title: d.metaTitle, description: d.metaDescription, path: PATHS.privacy })
}

export default function PrivacyPage() {
  const cfg = getMarketingConfig()
  return <LegalPage doc={privacyDoc(cfg)} cfg={cfg} />
}
