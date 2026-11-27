'use client'
import React, { useState } from 'react'
import { LinkOut } from '@/components/app/list'
import { ErrorBox, Spinner } from '@/components/app/ui'
import { getAnswers } from '@/lib/app/insights'
import type { AnswerItem } from '@/lib/app/insights'
import { useAsync } from '@/lib/app/useAsync'

// SEO → Answers (docs/plan/visibility-base.md step 1): Google puts Reddit and Quora threads first for "is <project> delayed"
// questions, where our young site does not show yet. Each week, ten questions buyers ask about our areas' projects, with the
// answer the page already holds and a draft to post by hand. Nothing is posted from Studio.
const card = 'list-none rounded-2xl bg-white p-3'
const btn = 'min-h-[44px] rounded-xl border border-gray-300 px-3 text-sm font-semibold text-[#0f2340] active:bg-gray-100'

function AnswerRow({ a }: { a: AnswerItem }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(a.draft)
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    } catch { /* the draft stays selectable */ }
  }
  return (
    <li className={card} data-testid="answer-row">
      <p className="font-semibold text-gray-900">{a.question}</p>
      <p className="text-xs text-gray-600">{a.project} · {a.area} · MahaRERA {a.regno}</p>
      <textarea readOnly value={a.draft} rows={5} onFocus={(e) => e.currentTarget.select()} aria-label={`Draft answer: ${a.question}`}
        className="mt-2 block w-full rounded-lg border border-gray-300 bg-gray-50 p-2 text-sm text-gray-800" />
      <div className="mt-2 flex flex-wrap items-center gap-3">
        <button type="button" className={btn} onClick={copy}>{copied ? 'Copied' : 'Copy the draft'}</button>
        <LinkOut href={a.find.reddit} label={`${a.project} on Reddit`}>Find on r/pune</LinkOut>
        <LinkOut href={a.find.quora} label={`${a.project} on Quora`}>Find on Quora</LinkOut>
        <LinkOut href={a.page} label={a.project}>Open page</LinkOut>
      </div>
    </li>
  )
}

export default function AnswersTab() {
  const q = useAsync(() => getAnswers(), [])
  if (q.loading && !q.data) return <Spinner />
  if (q.error) return <ErrorBox message={q.error} onRetry={q.reload} />
  const d = q.data!
  return (
    <>
      <div className="rounded-2xl bg-white p-4 text-sm text-gray-700">
        <p className="font-semibold text-gray-900">Answers to post, week {d.week}</p>
        <p className="mt-1">
          2 or 3 a week is enough. Find a thread that asks the question, write the answer in your own words to fit it, keep the
          one link, and say you are with Avasetu. Never paste the same text twice, and never post where the thread is not asking.
        </p>
      </div>
      {d.items.length === 0 ? (
        <p className="rounded-2xl bg-white p-4 text-sm text-gray-600">No questions with an answer yet: they come from the Google searches the page doctor reads for our areas&apos; projects.</p>
      ) : (
        <ul className="space-y-2 p-0">{d.items.map((a) => <AnswerRow key={a.regno} a={a} />)}</ul>
      )}
    </>
  )
}
