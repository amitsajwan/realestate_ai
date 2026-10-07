'use client'
import Link from 'next/link'
import React from 'react'
import { BrandEditor } from '@/components/app/BrandEditor'
import { PageTitle } from '@/components/app/ui'
import { brandingApi } from '@/lib/app/branding'
import { getSiteUrl } from '@/lib/app/session'

const load = () => brandingApi.load()
const save = (patch: Parameters<typeof brandingApi.save>[0]) => brandingApi.save(patch)
const upload = (file: File) => brandingApi.uploadFile(file)

/** The agent's own brand: how his public page looks (logo, banner, colours, texts, RERA agent number). */
export default function ProfilePage() {
  const siteUrl = getSiteUrl()
  return (
    <div className="space-y-4">
      <PageTitle>My brand</PageTitle>
      <p className="text-sm text-gray-600">This is how your website looks to buyers. Changes show on your page straight after you save.</p>
      {siteUrl && <Link href={siteUrl} target="_blank" className="block text-sm font-semibold text-blue-700 underline">View my website</Link>}
      <BrandEditor loadBranding={load} saveBranding={save} uploadImage={upload} />
    </div>
  )
}
