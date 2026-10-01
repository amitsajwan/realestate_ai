'use client'
import React from 'react'
import { api } from '@/lib/app/client'
import { conciergeApi } from '@/lib/app/concierge'
import { compressImage } from '@/lib/app/imageCompress'
// SWAP: when stream A1 merges, import the real editor instead (same props):
//   import { BrandEditor } from '../BrandEditor'
import { BrandEditor } from './BrandEditorStub'

/** The brand editor wired to one agent: loads and saves through the concierge, uploads through the shared image upload. */
export function AgentBrandEditor({ agentId, onSaved }: { agentId: string; onSaved?: () => void }) {
  return (
    <BrandEditor
      agentId={agentId}
      loadBranding={() => conciergeApi.getBranding(agentId)}
      saveBranding={async (data) => {
        const r = await conciergeApi.saveBranding(agentId, data)
        onSaved?.()
        return r
      }}
      uploadImage={async (file) => (await api.uploadImages([await compressImage(file)]))[0].url}
    />
  )
}
