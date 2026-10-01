import React from 'react'
import type { Metadata } from 'next'
import { getMarketingConfig } from '@/lib/marketing/config'
import { getHub, type Hub, type HubItem } from '@/lib/interest/api'
import WhatsAppButton from '@/components/site/WhatsAppButton'

export const revalidate = 60

export function generateMetadata(): Metadata {
  const cfg = getMarketingConfig()
  const title = `${cfg.businessName}: latest homes and posts`
  const description = 'Tap I am interested on any home or post and we will get back to you.'
  const image = cfg.siteUrl + '/brand/og.jpg'
  return {
    title, description, alternates: { canonical: cfg.siteUrl + '/go' },
    openGraph: { title, description, url: cfg.siteUrl + '/go', siteName: cfg.businessName, type: 'website', locale: 'en_IN', images: [{ url: image, width: 1200, height: 630 }] },
    twitter: { card: 'summary_large_image', title, description, images: [image] },
  }
}

const pill = 'flex min-h-[44px] items-center justify-center rounded-full border border-[#cdbf99] bg-white px-4 text-sm font-semibold text-[#0f2340] no-underline'

function Card({ item }: { item: HubItem }) {
  return (
    <li className="overflow-hidden rounded-2xl border border-[#ead9ae] bg-white shadow-sm">
      {item.image_url && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={item.image_url} alt={item.sample ? 'Photo of a sample home, for illustration' : ''} loading="lazy" className="aspect-[16/10] w-full object-cover" />
      )}
      <div className="p-4">
        {item.sample && <p className="mb-2 inline-block rounded-full bg-[#0f2340] px-3 py-1 text-xs font-bold tracking-wide text-[#f0b440]">SAMPLE HOME</p>}
        {!item.sample && item.kind !== 'listing' && <p className="mb-1 text-xs font-bold uppercase tracking-wide text-[#a87a12]">Latest post</p>}
        <h2 className="text-lg font-bold leading-snug text-[#0f2340]">{item.title}</h2>
        {item.subtitle && <p className="mt-1 text-sm leading-relaxed text-slate-600">{item.subtitle}</p>}
        <div className="mt-3 flex flex-col gap-2">
          {item.interest_code && (
            <a href={`/i/${item.interest_code}`} className="flex min-h-[52px] items-center justify-center rounded-xl bg-[#f0b440] px-4 text-base font-bold text-[#0f2340] no-underline">
              I am interested
            </a>
          )}
          {item.interest_code && <WhatsAppButton title={item.title} code={item.interest_code} />}
          {item.permalink && (
            <a href={item.permalink} target="_blank" rel="noopener noreferrer" className={pill}>See the post</a>
          )}
        </div>
      </div>
    </li>
  )
}

export default async function GoPage() {
  const cfg = getMarketingConfig()
  const hub: Hub | null = await getHub()
  const links = hub?.links || { website: cfg.siteUrl, invite: cfg.siteUrl + '/request-invite', facebook: null, instagram: null }
  const items = hub?.items || []
  return (
    <div className="mx-auto min-h-screen max-w-md">
      <header className="bg-[#0f2340] px-4 pb-6 pt-5 text-center text-white">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/brand/logo.png" alt="" width={64} height={64} className="mx-auto h-16 w-16 rounded-full ring-2 ring-[#f0b440]" />
        <h1 className="mt-3 text-2xl font-bold">{hub?.brand || cfg.businessName}</h1>
        <p className="mx-auto mt-1 max-w-xs text-sm leading-relaxed text-white/85">
          {hub?.line || 'Homes and guides for Pune buyers.'}
        </p>
      </header>

      <nav aria-label="Our pages" className="grid grid-cols-2 gap-2 px-4 pt-4">
        <a href={links.website} className={pill + ' col-span-2 !bg-[#0f2340] !text-white'}>Visit the website</a>
        {links.facebook && <a href={links.facebook} target="_blank" rel="noopener noreferrer" className={pill}>Facebook Page</a>}
        {links.instagram && <a href={links.instagram} target="_blank" rel="noopener noreferrer" className={pill}>Instagram</a>}
      </nav>

      <section aria-labelledby="latest" className="px-4 pb-6 pt-5">
        <h2 id="latest" className="mb-3 text-sm font-bold uppercase tracking-wide text-[#a87a12]">Latest homes and posts</h2>
        {items.length ? (
          <ul className="m-0 flex list-none flex-col gap-4 p-0">{items.map((i) => <Card key={i.kind + i.ref} item={i} />)}</ul>
        ) : (
          <p className="rounded-2xl border border-[#ead9ae] bg-white p-4 text-sm text-slate-700">Fresh homes and posts are on the way. Visit the website in the meantime.</p>
        )}
      </section>

      <section className="mx-4 mb-8 rounded-2xl bg-[#0f2340] p-5 text-white">
        <h2 className="text-lg font-bold">Are you an agent?</h2>
        <p className="mt-1 text-sm leading-relaxed text-white/85">List your homes free and let buyers tap to show interest.</p>
        <a href={links.invite} className="mt-3 flex min-h-[48px] items-center justify-center rounded-xl bg-[#f0b440] px-4 font-bold text-[#0f2340] no-underline">Request an invite</a>
      </section>
    </div>
  )
}
