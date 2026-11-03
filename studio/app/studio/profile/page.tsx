'use client'
import React from 'react'
import { BrandEditor } from '@/components/app/BrandEditor'
import { PhoneAppCard } from '@/components/app/PhoneApp'
import { SiteCard } from '@/components/app/SiteCard'
import { PageTitle } from '@/components/app/ui'
import { brandingApi } from '@/lib/app/branding'
import { turnOffAlerts } from '@/lib/app/phone'
import { useSession } from '@/lib/app/session'
import { t } from '@shared/strings'

const load = () => brandingApi.load()
const save = (patch: Parameters<typeof brandingApi.save>[0]) => brandingApi.save(patch)
const upload = (file: File) => brandingApi.uploadFile(file)

/** The agent's own brand: how his public page looks (logo, banner, colours, texts, RERA agent number). */
export default function ProfilePage() {
  const { siteUrl, logout } = useSession(false)
  // a phone that signs out stops ringing for this agent (another agent may sign in on it); never blocks the sign-out
  const signOut = async () => {
    await turnOffAlerts().catch(() => undefined)
    logout()
  }
  return (
    <div className="space-y-4">
      <PageTitle>My brand</PageTitle>
      <p className="text-sm text-gray-600">This is how your website looks to buyers. Changes show on your page straight after you save.</p>
      {siteUrl && <SiteCard siteUrl={siteUrl} />}
      <BrandEditor loadBranding={load} saveBranding={save} uploadImage={upload} />
      <PhoneAppCard place="profile" />
      <button type="button" onClick={() => void signOut()} className="min-h-[48px] w-full rounded-xl border border-gray-300 bg-white text-sm font-semibold text-gray-700">
        {t('logout')}
      </button>
    </div>
  )
}
