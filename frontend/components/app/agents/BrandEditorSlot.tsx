'use client'
import React from 'react'
import { api } from '@/lib/app/client'
import { conciergeApi } from '@/lib/app/concierge'
import { compressImage } from '@/lib/app/imageCompress'
import { BrandEditor } from '../BrandEditor'
import type { BrandingDoc } from '@/lib/app/branding'

/** The brand editor wired to one agent: loads and saves through the concierge, uploads through the shared image upload. */
export function AgentBrandEditor({ agentId, onSaved }: { agentId: string; onSaved?: () => void }) {
  return (
    <BrandEditor
      agentId={agentId}
      loadBranding={async () => {
        const flat = (await conciergeApi.getBranding(agentId)) as Record<string, unknown>
        return { ...flat, branding_data: flat } as unknown as BrandingDoc  // the concierge returns the branding fields flat
      }}
      saveBranding={async (data) => {
        await conciergeApi.saveBranding(agentId, data as Record<string, unknown>)
        const flat = (await conciergeApi.getBranding(agentId)) as Record<string, unknown>
        onSaved?.()
        return { ...flat, branding_data: flat } as unknown as BrandingDoc
      }}
      uploadImage={async (file) => (await api.uploadImages([await compressImage(file)]))[0].url}
    />
  )
}
