'use client'
import React from 'react'
import { TabBar, useUrlTab } from '@/components/app/list'
import { PageTitle } from '@/components/app/ui'
import { useIsOwner } from '../agents/useIsOwner'
import { AreaPhotosScreen } from './AreaPhotosScreen'
import { AreaPicturesReview } from './AreaPicturesReview'
import { MapPinsReview } from './MapPinsReview'
import { SpotlightEditor } from './SpotlightEditor'

const TABS = ['banner', 'pins', 'above', 'photos']
const LABEL: Record<string, string> = { banner: 'Hot banner', pins: 'Map pins', above: 'From above', photos: 'Photos' }
/** Studio > Site (owner only, 2026-11-19): what the owner edits on the public site, one tab each. It was four sections at the
 *  bottom of Admin, between the day's numbers and the system's health. */
export function SiteScreen() {
  const owner = useIsOwner()
  const [tab, setTab] = useUrlTab('tab', 'banner', TABS)
  if (!owner) return <p className="rounded-2xl bg-white p-4 text-sm text-gray-600">Only the owner edits the site.</p>
  return (
    <div className="space-y-3 pb-4" data-testid="site-screen">
      <PageTitle>Site</PageTitle>
      <TabBar label="Site" value={tab} onChange={setTab} tabs={TABS.map((k) => ({ key: k, label: LABEL[k] }))} />
      {tab === 'banner' ? <SpotlightEditor /> : tab === 'pins' ? <MapPinsReview /> : tab === 'above' ? <AreaPicturesReview /> : <AreaPhotosScreen embedded />}
    </div>
  )
}
