'use client'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import React from 'react'
import { Btn, ErrorBox, PageTitle, Spinner, inputCls } from '@/components/app/ui'
import { errorMessage } from '@/lib/app/client'
import { BRAND_NAME } from '@/lib/brand'
import { timeAgo } from '@/lib/app/format'
import { CHANNEL_CHIP, CHANNEL_LABEL, inboxApi, isComment, type InboxMessage, type InboxThreadFull, type PassAgent, type PassResult } from '@/lib/app/inbox'

const STATUS: Record<string, string> = { failed: 'Not delivered', refused: 'Not sent', dry_run: 'Test mode, not sent' }

function Bubble({ m }: { m: InboxMessage }) {
  const them = m.from === 'them'
  const tone = them ? 'bg-white border border-gray-200 text-gray-900' : m.from === 'you' ? 'bg-green-100 text-green-950' : 'bg-blue-50 text-blue-950'
  const bad = m.status && STATUS[m.status]
  return (
    <li className={'flex ' + (them ? 'justify-start' : 'justify-end')}>
      <div className={'max-w-[85%] space-y-1 rounded-2xl px-3 py-2 ' + tone}>
        <p className="text-xs font-semibold opacity-70">{them ? 'They wrote' : m.from === 'you' ? 'You' : 'Bot'}{m.at ? ` · ${timeAgo(m.at)}` : ''}</p>
        <p className="whitespace-pre-wrap break-words text-sm">{m.text}</p>
        {bad && <p className="text-xs font-semibold text-red-700">{bad}{m.error ? `: ${m.error}` : ''}</p>}
      </div>
    </li>
  )
}

/**
 * Owner only: pass this buyer to an agent. The chat and lead move to the agent (he gets an alert in Studio), and the owner gets a
 * ready WhatsApp message to the agent with the buyer's details, sent from the owner's own WhatsApp.
 */
function PassBox({ id, onPassed }: { id: string; onPassed: (r: PassResult) => void }) {
  const [open, setOpen] = React.useState(false)
  const [agents, setAgents] = React.useState<PassAgent[] | null>(null)
  const [pick, setPick] = React.useState('')
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [done, setDone] = React.useState<PassResult | null>(null)

  React.useEffect(() => {
    if (open && !agents) inboxApi.agents().then(setAgents).catch((e) => setError(errorMessage(e)))
  }, [open, agents])

  async function pass() {
    setBusy(true)
    setError(null)
    try {
      const r = await inboxApi.pass(id, pick)
      setDone(r)
      onPassed(r)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  if (done) {
    return (
      <section aria-label="Passed" className="space-y-2 rounded-2xl border border-sky-200 bg-sky-50 p-3">
        <p className="text-sm font-semibold text-sky-900">Passed to {done.passed_to}. The chat and lead are now in their Studio.</p>
        {done.whatsapp_url ? (
          <a href={done.whatsapp_url} target="_blank" rel="noreferrer"
            className="flex min-h-[48px] items-center justify-center rounded-xl bg-green-600 px-4 font-semibold text-white">Send the details to {done.passed_to} on WhatsApp</a>
        ) : (
          <p className="text-sm text-gray-700">Their site has no mobile number, so call them with the buyer's details.</p>
        )}
      </section>
    )
  }
  if (!open) return <Btn variant="secondary" onClick={() => setOpen(true)}>Pass to an agent</Btn>
  return (
    <section aria-label="Pass to an agent" className="space-y-2 rounded-2xl border border-gray-200 bg-white p-3">
      <label htmlFor="pass-agent" className="text-sm font-semibold text-gray-800">Pass this buyer to</label>
      {!agents && !error ? <Spinner /> : (
        <select id="pass-agent" className={inputCls} value={pick} onChange={(e) => setPick(e.target.value)}>
          <option value="">Pick an agent</option>
          {(agents ?? []).map((a) => <option key={a.agent_id} value={a.agent_id}>{a.name}{a.has_whatsapp ? '' : ' (no mobile on site)'}</option>)}
        </select>
      )}
      {error && <p role="alert" className="text-sm font-semibold text-red-700">{error}</p>}
      <Btn disabled={busy || !pick} onClick={pass}>{busy ? 'Passing...' : 'Pass'}</Btn>
      <p className="text-xs text-gray-500">The chat and the lead move to the agent and they get an alert. You then send them the buyer's details on WhatsApp.</p>
    </section>
  )
}

/** One conversation in full, oldest first, with a reply box for WhatsApp while the 24-hour window is open. */
export default function InboxThreadPage() {
  const { id } = useParams<{ id: string }>()
  const [doc, setDoc] = React.useState<InboxThreadFull | null>(null)
  const [error, setError] = React.useState<string | null>(null)
  const [text, setText] = React.useState('')
  const [busy, setBusy] = React.useState(false)
  const [passed, setPassed] = React.useState<PassResult | null>(null)  // keeps the WhatsApp link on screen after the reload
  const end = React.useRef<HTMLDivElement>(null)

  const load = React.useCallback(() => {
    setError(null)
    inboxApi.thread(id).then(setDoc).catch((e) => setError(errorMessage(e)))
  }, [id])
  React.useEffect(load, [load])
  // braces: Chrome's scrollIntoView now returns a Promise, and an effect that returns one crashes the page on leaving it
  // ('destroy is not a function': every Inbox link from a conversation showed the error page)
  React.useEffect(() => { end.current?.scrollIntoView({ block: 'end' }) }, [doc?.thread.length])

  async function markDone() {
    setBusy(true)
    setError(null)
    try {
      setDoc(await inboxApi.done(id))
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  async function send() {
    if (!text.trim()) return
    setBusy(true)
    setError(null)
    try {
      setDoc(await inboxApi.reply(id, text.trim()))
      setText('')
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  if (error && !doc) return <ErrorBox message={error} onRetry={load} />
  if (!doc) return <Spinner />
  const name = doc.name || (doc.role === 'agent' ? 'Agent' : doc.channel === 'website' ? 'Website visitor' : 'Buyer')
  return (
    <div className="space-y-4">
      <Link href="/studio/inbox" className="inline-flex min-h-[44px] items-center font-semibold text-blue-700">&lsaquo; Inbox</Link>
      <PageTitle>{name}</PageTitle>
      <div className="flex flex-wrap items-center gap-1.5 text-sm">
        <span className={'rounded-full px-2 py-0.5 text-xs font-semibold ' + (CHANNEL_CHIP[doc.channel] ?? CHANNEL_CHIP.website)}>{CHANNEL_LABEL[doc.channel] ?? doc.channel}</span>
        <span className={'rounded-full px-2 py-0.5 text-xs font-semibold ' + (doc.role === 'agent' ? 'bg-sky-100 text-sky-800' : 'bg-orange-100 text-orange-800')}>{doc.role === 'agent' ? 'Agent' : 'Buyer'}</span>
        {doc.phone && <span className="text-gray-600">{doc.phone}</span>}
        {doc.lead_id && <Link href={`/studio/leads/${encodeURIComponent(doc.lead_id)}`} className="font-semibold text-blue-700 underline">Open lead</Link>}
      </div>
      {doc.summary && <p className="text-sm text-gray-700">Wants: {doc.summary}</p>}
      {doc.post_url && (
        <a href={doc.post_url} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-[44px] items-center font-semibold text-blue-700 underline">
          Open the post on {doc.channel === 'instagram_comment' ? 'Instagram' : 'Facebook'}
        </a>
      )}
      {doc.passed === 'out' && <p className="rounded-xl bg-gray-50 p-3 text-sm text-gray-700">Passed to {doc.passed_to_name || 'an agent'}{doc.passed_at ? ` ${timeAgo(doc.passed_at)}` : ''}. They handle this buyer now.</p>}
      {doc.passed === 'in' && <p className="rounded-xl bg-sky-50 p-3 text-sm font-semibold text-sky-900">{BRAND_NAME} passed this buyer to you. Call or message them soon.</p>}
      {(doc.can_pass || passed) && <PassBox id={id} onPassed={(r) => { setPassed(r); load() }} />}

      <ol className="space-y-2" aria-label="Messages">{doc.thread.map((m, i) => <Bubble key={i} m={m} />)}</ol>
      <div ref={end} />

      {isComment(doc.channel) ? (
        doc.needs_you ? (
          <section aria-label="Needs you" className="space-y-2 rounded-2xl border border-amber-300 bg-amber-50 p-3">
            <p className="text-sm font-semibold text-amber-900">Needs you: {doc.reason || 'please answer this one'}</p>
            <p className="text-sm text-amber-900">Answer under the post on {doc.channel === 'instagram_comment' ? 'Instagram' : 'Facebook'}, then tap Done.</p>
            {error && <p role="alert" className="text-sm font-semibold text-red-700">{error}</p>}
            <Btn disabled={busy} onClick={markDone}>{busy ? 'Saving...' : 'Done'}</Btn>
          </section>
        ) : (
          <p className="rounded-xl bg-gray-50 p-3 text-sm text-gray-700">Comments are answered by the bot. To add something, reply under the post itself.</p>
        )
      ) : doc.opted_out ? (
        <p className="rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-800">They replied STOP. Do not message them on WhatsApp.</p>
      ) : doc.can_reply ? (
        <section aria-label="Reply" className="space-y-2 rounded-2xl border border-gray-200 bg-white p-3">
          <label htmlFor="inbox-reply" className="text-sm font-semibold text-gray-800">Reply on WhatsApp</label>
          <textarea id="inbox-reply" rows={4} maxLength={1000} className={inputCls} value={text} onChange={(e) => setText(e.target.value)} placeholder="Write your message" />
          {error && <p role="alert" className="text-sm font-semibold text-red-700">{error}</p>}
          <Btn disabled={busy || !text.trim()} onClick={send}>{busy ? 'Sending...' : 'Send'}</Btn>
          <p className="text-xs text-gray-500">{doc.bot_paused_until ? 'The bot is quiet in this chat while you handle it.' : 'After you reply, the bot stays quiet in this chat for 12 hours.'}</p>
        </section>
      ) : doc.channel === 'whatsapp' ? (
        <p className="rounded-xl bg-gray-50 p-3 text-sm text-gray-700">More than 24 hours since they last wrote. WhatsApp lets us reply only after they write again.</p>
      ) : (
        <p className="rounded-xl bg-gray-50 p-3 text-sm text-gray-700">{doc.channel === 'website' ? 'Website chats are answered by the bot. If they leave a number, it is in Leads.' : 'Reply to this one from the Facebook or Instagram inbox.'}</p>
      )}
    </div>
  )
}
