'use client'
import React, { useState } from 'react'
import {
  downloadImage,
  hashtagsLine,
  imageFilename,
  instagramCopyText,
  reelScriptText,
  shareImage,
  whatsappPackUrl,
} from '@/lib/app/marketing'
import { copyText } from '@/lib/app/share'
import { t } from '@/lib/app/strings'
import type { MarketingPack } from '@/lib/app/types'
import { Btn, LinkBtn } from './ui'

export function CopyBtn({ text, label, variant = 'secondary' }: { text: string; label: string; variant?: 'primary' | 'secondary' }) {
  const [copied, setCopied] = useState(false)
  return (
    <Btn
      variant={variant}
      onClick={async () => {
        const ok = await copyText(text)
        setCopied(ok)
        if (ok) setTimeout(() => setCopied(false), 2000)
      }}
    >
      {copied ? t('copied') : label}
    </Btn>
  )
}

function Card({ title, children, testId }: { title: string; children: React.ReactNode; testId: string }) {
  return (
    <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4" aria-label={title} data-testid={testId}>
      <h2 className="text-lg font-bold text-gray-900">{title}</h2>
      {children}
    </section>
  )
}

const textBox = 'whitespace-pre-wrap break-words rounded-xl bg-gray-50 p-3 text-sm text-gray-900'

function InstagramCard({ pack }: { pack: MarketingPack }) {
  const { images, caption, hashtags } = pack.instagram
  const [active, setActive] = useState(0)
  const [note, setNote] = useState('')
  const current = images[Math.min(active, Math.max(0, images.length - 1))]
  const full = instagramCopyText(pack.instagram)

  return (
    <Card title={t('instagram')} testId="card-instagram">
      {images.length > 0 && (
        <>
          <div
            className="flex snap-x snap-mandatory gap-3 overflow-x-auto pb-2"
            data-testid="carousel"
            onScroll={(e) => {
              const el = e.currentTarget
              if (el.clientWidth > 0) setActive(Math.round(el.scrollLeft / (el.clientWidth * 0.86)))
            }}
          >
            {images.map((img) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                key={img.kind}
                src={img.url}
                alt={`Instagram ${img.kind} card`}
                width={img.width}
                height={img.height}
                className="aspect-square w-[86%] flex-none snap-center rounded-xl bg-gray-100 object-cover"
              />
            ))}
          </div>
          <p className="text-center text-xs text-gray-500" aria-live="polite">
            {Math.min(active, images.length - 1) + 1} / {images.length}
          </p>
        </>
      )}
      <p className={textBox} data-testid="ig-caption">{caption}</p>
      {hashtags.length > 0 && <p className="break-words text-sm text-blue-700" data-testid="ig-hashtags">{hashtagsLine(hashtags)}</p>}
      <CopyBtn text={full} label={t('copyCaption')} variant="primary" />
      {current && (
        <div className="grid grid-cols-2 gap-3">
          <Btn
            variant="secondary"
            onClick={async () => {
              const r = await shareImage(current, imageFilename(current, pack.listing_id), full)
              setNote(r === 'downloaded' ? 'Image saved. Add it to your post.' : r === 'opened' ? 'Image opened. Save it, then post.' : '')
            }}
          >
            {t('shareImage')}
          </Btn>
          <Btn variant="secondary" onClick={() => downloadImage(current, imageFilename(current, pack.listing_id))}>
            {t('downloadImage')}
          </Btn>
        </div>
      )}
      {note && <p role="status" className="text-center text-sm text-gray-600">{note}</p>}
    </Card>
  )
}

export function MarketingPackView({ pack }: { pack: MarketingPack }) {
  const statusImage = pack.whatsapp.status_image
  const waText = pack.whatsapp.message
  return (
    <div className="space-y-4" data-testid="pack">
      <div className="rounded-2xl bg-blue-50 p-4">
        <p className="text-sm text-blue-900">{pack.angle}</p>
        <p className="mt-1 font-bold text-blue-950">{pack.headline}</p>
      </div>

      <InstagramCard pack={pack} />

      <Card title={t('facebook')} testId="card-facebook">
        <p className={textBox} data-testid="fb-post">{pack.facebook.post}</p>
        <CopyBtn text={pack.facebook.post} label={t('copyPost')} variant="primary" />
      </Card>

      <Card title="WhatsApp" testId="card-whatsapp">
        <p className={textBox} data-testid="wa-message">{waText}</p>
        <LinkBtn variant="whatsapp" href={whatsappPackUrl(waText)} target="_blank" rel="noopener noreferrer">
          {t('sendOnWhatsapp')}
        </LinkBtn>
        <CopyBtn text={waText} label={t('copyMessage')} />
        <div className="space-y-2 border-t border-gray-100 pt-3">
          <p className="text-sm font-semibold text-gray-700">{t('whatsappStatus')}</p>
          <p className={textBox} data-testid="wa-status">{pack.whatsapp.status_text}</p>
          {statusImage && (
            <Btn variant="secondary" onClick={() => downloadImage(statusImage, imageFilename(statusImage, pack.listing_id))}>
              {t('downloadStatusImage')}
            </Btn>
          )}
        </div>
      </Card>

      <Card title={t('reel')} testId="card-reel">
        <p className="text-sm">
          <b>{t('reelHook')}:</b> {pack.reel.hook}
        </p>
        <ol className="list-decimal space-y-2 pl-5 text-sm" data-testid="reel-beats">
          {pack.reel.beats.map((b, i) => (
            <li key={i}>
              <span className="text-xs font-semibold text-gray-500">{/s$/.test(b.seconds) ? b.seconds : b.seconds + 's'}</span> {b.text}
              <span className="block text-xs text-gray-500">Show: {b.visual}</span>
            </li>
          ))}
        </ol>
        <p className="text-sm">
          <b>{t('reelCta')}:</b> {pack.reel.cta}
        </p>
        <CopyBtn text={reelScriptText(pack.reel)} label={t('copyScript')} variant="primary" />
      </Card>

      <PublishEverywhere />
    </div>
  )
}

/** Honest placeholder: no publishing exists yet, so the connect buttons are disabled and labelled. */
export function PublishEverywhere() {
  const items = [t('connectInstagram'), t('connectFacebook'), t('connectWhatsappBusiness')]
  return (
    <section className="space-y-3 rounded-2xl border border-dashed border-gray-300 bg-gray-50 p-4" aria-label={t('publishEverywhere')}>
      <h2 className="text-lg font-bold text-gray-900">{t('publishEverywhere')}</h2>
      <p className="text-sm text-gray-600">{t('publishNote')}</p>
      {items.map((label) => (
        <button
          key={label}
          type="button"
          disabled
          className="flex min-h-[52px] w-full items-center justify-between rounded-xl border border-gray-200 bg-white px-4 text-base font-semibold text-gray-400"
        >
          <span>{label}</span>
          <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs">{t('comingSoon')}</span>
        </button>
      ))}
    </section>
  )
}
