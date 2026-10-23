import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { claimHref } from '@/lib/marketing/trial'

/** The new agent's guide: from sending TRIAL to the first buyer's enquiry, with screenshots of the live screens (public/guide/).
 *  Sent to trial agents on WhatsApp (template agent_guide_v1), so it speaks to the agent and says nothing about how we run it.
 *  Keep it in step with the trial reply (backend onboarding/trial.py) and the join screens (components/app/JoinFlow.tsx). */
export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: 'Getting started on Avasetu: a guide for Pune agents',
  description: 'Claim your free trial, sign in, set up your page, add a property and see where buyer enquiries reach you. Step by step, with pictures.',
  path: '/for-agents/guide',
})

const HELP = '+91 98342 56406'

const STEPS = [
  ['Claim the trial', 'Send TRIAL to us on WhatsApp'],
  ['Sign in', 'Your number plus the code we send'],
  ['Set up your page', 'Name, photo, colours. Live in a minute'],
  ['Add a property', 'RERA number or details, plus photos'],
  ['We post it', 'Page, Facebook, Instagram, Reel, WhatsApp text'],
  ['Buyers enquire', 'On your page, on WhatsApp or through Avasetu'],
  ['You follow up', 'Every buyer is waiting in Studio'],
]

const ROUTES = [
  ['Fills the enquiry form on your page', 'Their name, number, BHK, budget, move-in date and payment plan are saved, with the properties they looked at', 'Leads, and at the top of Studio Home'],
  ['Taps the WhatsApp button on your page', 'Their WhatsApp opens a chat with you', 'Your own WhatsApp'],
  ['Chats on your website', 'Our assistant answers questions about your properties and asks for their number', 'Inbox and Leads'],
  ['Messages Avasetu on WhatsApp, Instagram or Facebook about your property', 'Our assistant answers first, then passes the buyer to you', 'Studio Home: “buyer was passed to you”'],
]

const SCREENS = [
  ['Home', '“Needs you now”: new buyers, buyers to call today, buyers passed to you, posts waiting for your OK. Start here every day.'],
  ['Leads', 'Every buyer with their budget and needs, their chats and your call notes. Send a WhatsApp follow-up from here and mark each one Won or Lost when it is settled.'],
  ['Inbox', 'Website chats and comments that need your answer.'],
  ['Listings', 'Add properties, add photos, confirm they are still available.'],
  ['Results', 'How many people saw, clicked and enquired about each property and post.'],
  ['Profile', 'Your photo, the WhatsApp number buyers see, logo, colours and MahaRERA number.'],
]

const FAQ: [string, React.ReactNode][] = [
  ['I want to use a different phone number', <>
    <p><b>For buyers to contact you:</b> keep signing in as now and change the WhatsApp number under Studio → Profile.</p>
    <p className="mt-2"><b>To sign in with:</b> send TRIAL from WhatsApp on the new number and you get a code for it. Do this before you set up your page: a new sign-in number starts a fresh, empty account.</p></>],
  ['I lost my code', <p>It is still in our WhatsApp chat, so scroll up. If you cannot find it, send TRIAL again from the same number. An hour after your last code, a new one comes for the same account.</p>],
  ['It says “too many wrong attempts”', <p>Wait 30 minutes and try again. If it says your invite is locked, message us on WhatsApp and we will send a new code.</p>],
  ['Can I test my enquiry form?', <p>Yes. Ask a friend to fill it on their phone, then check that it appears under Leads. A test from your own number also shows as a lead: mark it Lost so it does not stay on your list of buyers to call.</p>],
  ['Do I need to install an app?', <p>No. Studio works in your phone browser at avasetu.in/studio. Add it to your home screen from the browser menu to open it in one tap.</p>],
]

const wrap = 'mx-auto max-w-5xl px-4'
const card = 'rounded-2xl border border-slate-200 bg-white p-5 sm:p-6'
const note = 'rounded-r-xl border-l-4 border-[#f0b440] bg-[#fdf3dc] px-4 py-3 text-[15px] text-slate-800'
const eyebrow = 'text-xs font-bold uppercase tracking-wider text-[#b07a12]'
const h2 = 'text-2xl font-extrabold tracking-tight text-[#0f2340]'

function Phone({ src, alt, caption }: { src: string; alt: string; caption: string }) {
  return (
    <figure className="mx-auto w-full max-w-[260px]">
      <div className="overflow-hidden rounded-[26px] border-[8px] border-[#1b2333] bg-[#1b2333] shadow-xl">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={src} alt={alt} width={393} height={727} loading="lazy" className="block h-auto w-full" />
      </div>
      <figcaption className="mt-2 text-center text-sm text-slate-500">{caption}</figcaption>
    </figure>
  )
}

function Step({ n, title, children, shot }: { n: string; title: string; children: React.ReactNode; shot?: React.ReactNode }) {
  return (
    <section className={`${card} grid items-start gap-6 ${shot ? 'md:grid-cols-[minmax(0,1fr)_260px]' : ''}`}>
      <div className="grid min-w-0 gap-3 text-[16px] leading-relaxed text-slate-700">
        <p className={eyebrow}>{n}</p>
        <h2 className={h2}>{title}</h2>
        {children}
      </div>
      {shot}
    </section>
  )
}

export default function AgentGuidePage() {
  const claim = claimHref('guide', process.env.NEXT_PUBLIC_WHATSAPP_NUMBER)
  return (
    <MarketingShell hot={false}>
      <section className="bg-gradient-to-b from-[#0f2340] to-[#183a5d] text-white">
        <div className={`${wrap} py-10 sm:py-14`}>
          <p className="text-xs font-bold uppercase tracking-wide text-[#f0b440]">For Pune property agents · Free trial guide</p>
          <h1 className="mt-3 text-[2rem] font-extrabold leading-[1.15] tracking-tight sm:text-5xl">Getting started on Avasetu</h1>
          <p className="mt-4 max-w-2xl text-base leading-relaxed text-slate-100 sm:text-lg">
            Give us one property and it goes live: your own website, Facebook and Instagram posts, a Reel and a WhatsApp message.
            Buyers&apos; questions get answered and every enquiry comes to you. Here is how it works, step by step.
          </p>
          <p className="mt-4 text-sm text-slate-300">1 month free · No card · No app to install</p>
        </div>
      </section>

      <div className={`${wrap} grid gap-6 py-10`}>
        <section className="grid gap-4">
          <h2 className={h2}>Your first day, in 7 steps</h2>
          <ol className="m-0 grid list-none grid-cols-2 gap-3 p-0 sm:grid-cols-4 lg:grid-cols-7">
            {STEPS.map(([t, s], i) => (
              <li key={t} className="grid gap-1 rounded-xl border border-slate-200 bg-white p-3">
                <span className="grid h-6 w-6 place-items-center rounded-full bg-[#f0b440] text-xs font-extrabold text-[#0f2340]">{i + 1}</span>
                <b className="text-[15px] text-[#0f2340]">{t}</b>
                <span className="text-[13px] leading-snug text-slate-500">{s}</span>
              </li>
            ))}
          </ol>
        </section>

        <Step n="Step 1 · Claim the trial" title="Send TRIAL and your code comes back at once"
          shot={<Phone src="/guide/trial.jpg" caption="avasetu.in/trial" alt="The avasetu.in/trial page on a phone with a gold Claim your free trial button." />}>
          <p>Open avasetu.in/trial and tap <b>Claim your free trial</b>. WhatsApp opens with TRIAL already typed to our number, <b>{HELP}</b>. Send it, and our reply comes within seconds with your 6-digit sign-up code and a sign-in link.</p>
          <p className={note}><b>Send TRIAL from the number you want to sign in with.</b> Your code works only with the WhatsApp number that sent TRIAL. That is how we know the account is really yours.</p>
          <p><a href={claim} className="font-semibold text-[#0f2340] underline">Claim your free trial on WhatsApp</a></p>
        </Step>

        <Step n="Step 2 · Sign in" title="Your number, then the code from WhatsApp"
          shot={<Phone src="/guide/join.jpg" caption="avasetu.in/join" alt="The avasetu.in/join page with a mobile number field and a blue button." />}>
          <p>Tap the link in our WhatsApp message. Your number is already filled in.</p>
          <ul className="grid list-disc gap-1 pl-5">
            <li>Tap the blue button. It says <b>Send OTP</b>, but no SMS comes: the next screen asks for your code.</li>
            <li>Type the 6-digit code from our WhatsApp message.</li>
            <li>You stay signed in on that phone. There is no password to remember.</li>
          </ul>
          <p className={note}>Keep your code private. Anyone with your phone number and your code can open your account and see your buyers.</p>
        </Step>

        <Step n="Step 3 · Set up your page" title="“Tell us about you”, and your page is live"
          shot={<Phone src="/guide/agent-page.jpg" caption="A live agent page" alt="A sample agent page with the agent's photo, area badge, headline and I'm interested button." />}>
          <p>Add your name, area or pincode, a photo, your business name, what you deal in, your languages and a colour. Your page goes live straight away at avasetu.in/agent/your-name, with a short bio written for you. Share that link on your WhatsApp status, Instagram bio and visiting card.</p>
          <p className={note}><b>Add your MahaRERA agent number within 7 days</b> in Studio → Profile → My brand. It is needed to keep your account active, and it shows on your page and posts so buyers can see you are registered. Studio Home reminds you until it is done.</p>
          <p className={note}><b>The number buyers see can be different.</b> You sign in with the number that sent TRIAL. Under Profile you can set another WhatsApp number for buyers, such as your office number. Left empty, buyers see your sign-in number.</p>
        </Step>

        <Step n="Steps 4 and 5 · Add a property, we post it" title="One property becomes a page, posts and a Reel">
          <p>In Studio, open <b>Listings → Add</b>. Type or say the details, or just enter the project&apos;s MahaRERA number (it starts with P5) and we fill in the rest from MahaRERA&apos;s public record. Add photos and check one short screen. We make:</p>
          <ul className="grid list-disc gap-1 pl-5">
            <li>a property page on your website, with a green “Checked on MahaRERA” box,</li>
            <li>a photo post and a details post with the price table, for Facebook and Instagram,</li>
            <li>a Reel,</li>
            <li>a ready-made WhatsApp message to forward to your buyers and groups.</li>
          </ul>
          <p>With one tap it goes live on Avasetu&apos;s Facebook and Instagram with your name. Nothing is posted until you say so.</p>
          <p className={note}>Start with one property you know well. It takes about a minute, and it is what brings your first buyers.</p>
        </Step>

        <section className="grid gap-4">
          <p className={eyebrow}>Step 6 · Buyers enquire</p>
          <h2 className={h2}>How buyers reach you</h2>
          <p className="text-slate-600">A buyer can reach you in four ways. All four end with you.</p>
          <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
            <table className="w-full min-w-[640px] border-collapse text-[15px]">
              <thead>
                <tr className="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-500">
                  <th className="p-3">The buyer</th><th className="p-3">What happens</th><th className="p-3">Where you see it</th>
                </tr>
              </thead>
              <tbody>
                {ROUTES.map(([who, what, where]) => (
                  <tr key={who} className="border-t border-slate-200 align-top">
                    <td className="p-3 font-semibold text-[#0f2340]">{who}</td><td className="p-3 text-slate-700">{what}</td><td className="p-3 text-slate-700">{where}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <Step n="The enquiry form" title="Know their budget before you call"
          shot={<Phone src="/guide/agent-enquiry.jpg" caption="The enquiry form buyers fill" alt="The enquiry form with a consent checkbox and optional BHK, budget, move-in and payment choices." />}>
          <p>Buyers give their name and number and agree to be contacted. The questions below are optional, but most buyers answer them, so you know their BHK, budget and timeline before you call.</p>
          <p className={note}><b>Open Studio at least once a day.</b> New enquiries wait for you at the top of Studio Home. We do not send a WhatsApp alert for each one yet. Call new buyers the same day, while they are still looking.</p>
        </Step>

        <section className="grid gap-4">
          <p className={eyebrow}>Step 7 · You follow up</p>
          <h2 className={h2}>Your Studio, screen by screen</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {SCREENS.map(([t, s]) => (
              <div key={t} className="rounded-xl border border-slate-200 bg-white p-4">
                <b className="text-[#0f2340]">{t}</b>
                <p className="mt-1 text-[15px] leading-snug text-slate-600">{s}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="grid gap-3">
          <h2 className={h2}>Common questions</h2>
          {FAQ.map(([q, a], i) => (
            <details key={q} open={i === 0} className="rounded-xl border border-slate-200 bg-white px-4 py-3">
              <summary className="cursor-pointer font-bold text-[#0f2340]">{q}</summary>
              <div className="mt-2 text-[15px] leading-relaxed text-slate-700">{a}</div>
            </details>
          ))}
        </section>

        <p className={note}><b>Need help?</b> Message us on WhatsApp at <b>{HELP}</b> and the Avasetu team will reply. Ready to start? <Link href="/studio" className="font-semibold underline">Open Studio</Link>.</p>
      </div>
    </MarketingShell>
  )
}
