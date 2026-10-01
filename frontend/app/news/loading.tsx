import React from 'react'
import MarketingShell from '@/components/marketing/MarketingShell'
import { NewsSkeleton } from '@/components/news/NewsGrid'
import { NEWS_TEXT } from '@/lib/news/data'

export default function Loading() {
  return (
    <MarketingShell showInviteCta={false}>
      <section className="py-8 sm:py-14">
        <div className="mx-auto max-w-3xl px-4">
          <h1 className="text-3xl font-extrabold tracking-tight text-[#0f2340] sm:text-4xl">{NEWS_TEXT.heading}</h1>
          <div className="mt-8"><NewsSkeleton count={4} /></div>
        </div>
      </section>
    </MarketingShell>
  )
}
