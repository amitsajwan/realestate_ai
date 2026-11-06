import React from 'react'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { claimHref } from '@/lib/marketing/trial'

/** The guide for agents and channel partners: what they get, and every step on their own, from sending TRIAL to a buyer's enquiry. Screenshots
 *  of the live screens are in public/guide/. Sent to trial agents on WhatsApp (template agent_guide_v1), so it speaks to the agent and says
 *  nothing about how we run it. Everything here must stay true: keep it in step with the trial reply (backend onboarding/trial.py), the join
 *  screens (components/app/JoinFlow.tsx), the new listing flow (studio NewListingFlow) and where leads land (docs/plan/listing-flow.md). */
export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: 'Avasetu guide for Pune agents and channel partners',
  description: 'What you get on Avasetu and how to use it on your own: list a project in minutes, get a page and posts, and work every buyer lead. Step by step, with pictures.',
  path: '/for-agents/guide',
  // agents reach it from /agents, Studio, our posts and WhatsApp; out of search so it never stands for the brand (buyers first, 2026-10-29)
  noindex: true,
})

const HELP = '+91 98342 56406'

const GET = [
  ['Most Pune projects, ready', 'Over 12,000 project pages with MahaRERA facts. Pick your project instead of typing it.'],
  ['Your own page', 'avasetu.in/agent/your-name, with your name, photo, colours and every property you sell.'],
  ['A link for each listing', 'The full project page in your colours, with your prices and your enquiry form. Share it anywhere.'],
  ['Posts and a Reel', 'Made for each property and posted on Avasetu’s Facebook and Instagram with your name, when you say so.'],
  ['Lead cards', 'Each enquiry shows BHK, budget, timing, how warm the buyer is and which projects they looked at.'],
  ['Lead Board', 'Buyers who asked Avasetu about a home. See what they want, then ask for the ones you can serve.'],
  ['An assistant for buyers', 'It answers questions on your page and asks for their number, so a buyer is not left waiting.'],
  ['Results', 'How many people saw, clicked and enquired, for each property and post.'],
]

const STEPS = [
  ['Claim the trial', 'Send TRIAL to us on WhatsApp'],
  ['Sign in', 'Your number plus the code on WhatsApp'],
  ['Set up your page', 'Name, photo, colours. Live in a minute'],
  ['List a project', 'Pick it, check your prices, post'],
  ['Market it', 'Posts and a Reel, your link for your groups'],
  ['Buyers enquire', 'On your link, on WhatsApp, in the chat'],
  ['Follow up', 'Every buyer is waiting in Studio'],
]

const ROUTES = [
  ['Fills the enquiry form on your page or your listing link', 'Their name, number, BHK, budget, move-in date and payment plan are saved, with the properties they looked at', 'Yours, at once: Leads, and at the top of Studio Home'],
  ['Taps the WhatsApp button on your page', 'Their WhatsApp opens a chat with you', 'Yours: your own WhatsApp'],
  ['Chats on your page', 'Our assistant answers questions about your properties and asks for their number', 'Yours: Inbox and Leads'],
  ['Messages Avasetu on WhatsApp, Instagram or Facebook about your property', 'Our assistant answers first, then passes the buyer to you', 'Yours: Studio Home, “buyer was passed to you”'],
  ['Enquires on Avasetu’s own project page', 'The page shows your name, prices and photos, but no agent’s number. The Avasetu team follows up', 'Avasetu’s lead. It may be passed to you, or appear on the Lead Board'],
]

const SCREENS = [
  ['Home', '“Needs you now”: new buyers, buyers to call today, buyers passed to you, posts waiting for your OK. Start here every day.'],
  ['Leads', 'Every buyer with their budget and needs, their chats and your call notes. Send a WhatsApp follow-up from here and mark each one Won or Lost when it is settled.'],
  ['Lead Board', 'Buyers who asked Avasetu, with no name or number. Ask for the ones you can serve.'],
  ['Inbox', 'Website chats and comments that need your answer.'],
  ['Listings', 'Add properties, add photos, confirm they are still available.'],
  ['Results', 'How many people saw, clicked and enquired about each property and post.'],
  ['Profile', 'Your photo, the WhatsApp number buyers see, logo, colours and MahaRERA number.'],
]

const FAQ: [string, React.ReactNode][] = [
  ['What does it cost?', <p key="cost">The first month is free for the first 20 Pune agents, with no card. After that it is a small monthly fee, and we tell you the price before anything changes. On the Lead Board an offer is your choice, and you can ask for a lead with no offer at all.</p>],
  ['Who can see my leads?', <p key="own">Leads that come to you are yours: other agents never see them. We never sell a buyer’s details, and buyers tick a box agreeing to be contacted about their enquiry.</p>],
  ['Another agent lists the same project', <p key="two">That is allowed, and each of you keeps your own page and link. Avasetu’s project page shows the most complete listing: more sizes with prices come first, then more photos. So add every size, price and photo you can.</p>],
  ['Is my phone number shown on Avasetu’s project pages?', <p key="num">No agent’s number is shown there. Buyers who enquire there reach the Avasetu team. Your own page and your listing links carry your WhatsApp button, so share those.</p>],
  ['I do not have a MahaRERA agent number', <p key="rera">You need one for a public page, because the law requires it to market projects. Without it your page does not stay live, but you can still see the Lead Board and sign in. Add it in Studio → Profile → My brand.</p>],
  ['I want to use a different phone number', <>
    <p><b>For buyers to contact you:</b> keep signing in as now and change the WhatsApp number under Studio → Profile.</p>
    <p className="mt-2"><b>To sign in with:</b> send TRIAL from WhatsApp on the new number and you get a code for it. Do this before you set up your page: a new sign-in number starts a fresh, empty account.</p>
  </>],
  ['I did not get a code', <p key="code">Your trial code is still in our WhatsApp chat, so scroll up. If you cannot find it, send TRIAL again from the same number. An hour after your last code, a new one comes for the same account.</p>],
  ['It says “too many wrong attempts”', <p key="wrong">Wait 30 minutes and try again. If it says your invite is locked, message us on WhatsApp and we will send a new code.</p>],
  ['Can I test my enquiry form?', <p key="test">Yes. Ask a friend to fill it on their phone, then check that it appears under Leads. A test from your own number also shows as a lead: mark it Lost so it does not stay on your list.</p>],
  ['Do I need to install an app?', <p key="app">No. Studio works in your phone browser at avasetu.in/studio. Add it to your home screen from the browser menu to open it in one tap, and turn on its alerts so a new buyer rings your phone.</p>],
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
          <p className="text-xs font-bold uppercase tracking-wide text-[#f0b440]">For Pune agents and channel partners</p>
          <h1 className="mt-3 text-[2rem] font-extrabold leading-[1.15] tracking-tight sm:text-5xl">Your guide to Avasetu</h1>
          <p className="mt-4 max-w-2xl text-base leading-relaxed text-slate-100 sm:text-lg">
            Pick a project, add your prices and it is live: your page, your link, posts and a Reel. Every buyer who enquires becomes a lead card
            on your phone. Here is what you get and how to do it all yourself, step by step.
          </p>
          <p className="mt-4 text-sm text-slate-300">1 month free for the first 20 agents · No card · No app to install</p>
        </div>
      </section>

      <div className={`${wrap} grid gap-6 py-10`}>
        <section className="grid gap-4" aria-labelledby="get-title">
          <h2 id="get-title" className={h2}>What you get</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {GET.map(([t, s]) => (
              <div key={t} className="rounded-xl border border-slate-200 bg-white p-4">
                <b className="text-[#0f2340]">{t}</b>
                <p className="mt-1 text-[15px] leading-snug text-slate-600">{s}</p>
              </div>
            ))}
          </div>
        </section>

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
          <p>Open avasetu.in/trial and tap <b>Claim your free trial</b>. WhatsApp opens with TRIAL already typed to our number, <b>{HELP}</b>. Send it, and our reply comes within seconds with your 6-digit sign-up code.</p>
          <p className={note}><b>Send TRIAL from the number you want to sign in with.</b> Your code works only with the WhatsApp number that sent TRIAL. That is how we know the account is really yours.</p>
          <p><a href={claim} className="font-semibold text-[#0f2340] underline">Claim your free trial on WhatsApp</a></p>
        </Step>

        <Step n="Step 2 · Sign in" title="Your number, then the code from WhatsApp"
          shot={<Phone src="/guide/join.jpg" caption="avasetu.in/join" alt="The avasetu.in/join page with a mobile number field and a blue button." />}>
          <p>Tap the link in our WhatsApp message. Your number is already filled in.</p>
          <ul className="grid list-disc gap-1 pl-5">
            <li>Tap the blue button. It says <b>Send OTP</b>, but no SMS comes: the code comes on WhatsApp.</li>
            <li>Type the 6-digit code. The code in our first message also works.</li>
            <li>You stay signed in on that phone for 30 days. There is no password to remember.</li>
          </ul>
          <p className={note}>Keep your code private. Anyone with your phone number and your code can open your account and see your buyers.</p>
        </Step>

        <Step n="Step 3 · Set up your page" title="“Tell us about you”, and your page is live"
          shot={<Phone src="/guide/agent-page.jpg" caption="A live agent page" alt="A sample agent page with the agent's photo, area badge, headline and I'm interested button." />}>
          <p>Add your name, area or pincode, a photo, your business name, what you deal in, your languages and a colour. Your page goes live straight away at avasetu.in/agent/your-name, with a short bio written for you. You can change anything later under Profile.</p>
          <p className={note}><b>Add your MahaRERA agent number within 7 days</b> in Studio → Profile → My brand. Your public page needs it, and it shows on your page and posts so buyers can trust you.</p>
          <p className={note}><b>The number buyers see can be different.</b> You sign in with the number that sent TRIAL. Under Profile you can set another WhatsApp number for buyers, such as your office number.</p>
        </Step>

        <Step n="Step 4 · List a project" title="Pick the project. Most of it is already done"
          shot={<Phone src="/guide/list-project.jpg" caption="Studio → Listings → Add" alt="The new listing screen: a search box asking which project you are selling, with Godrej Ivara in the results." />}>
          <p>Most Pune projects already have a page on Avasetu, so you start from it instead of typing.</p>
          <ol className="grid list-decimal gap-1 pl-5">
            <li>In Studio, open <b>Listings → Add</b>.</li>
            <li>Search by project name, area or MahaRERA number, and tap your project.</li>
            <li>The check screen opens with the MahaRERA facts, the title, the page’s photos and any sizes and prices published online.</li>
            <li><b>Change the prices to what you are selling at today.</b> Add every size and your payment plan.</li>
            <li>Untick any photo you do not want, add your own, and tap to post.</li>
          </ol>
          <p>It goes live at once on your page, and Avasetu’s project page shows your name, prices and photos.</p>
          <p className={note}>On a project page, signed in? Tap <b>List this project</b> under its name and you land on the same check screen.</p>
        </Step>

        <Step n="Resale, rent, or a project we do not have" title="Describe it, and we fill in the form"
          shot={<Phone src="/guide/list-check.jpg" caption="The check screen" alt="The check screen with a table of home sizes and prices to change, a payment plan and the photos from the project page." />}>
          <p>On the first screen tap <b>Resale or rent flat, or a project not listed here</b>. Type or say the details the way you would tell a buyer, such as “2 BHK in Baner, 85 lakh, 950 sq ft carpet, 7th floor, ready to move”, add photos and tap Next. Check what we read, then post.</p>
          <p className={note}>Selling a new project? It needs a MahaRERA number before it can be marketed. Put the number in your description and we fill in the rest from MahaRERA’s public record.</p>
        </Step>

        <Step n="Step 5 · Market it" title="One property becomes posts, a Reel and a link to share">
          <p>After posting, tap <b>Start marketing</b>. We prepare:</p>
          <ul className="grid list-disc gap-1 pl-5">
            <li>a photo post and a details post with the price table, for Facebook and Instagram,</li>
            <li>a Reel,</li>
            <li>a ready-made WhatsApp message to forward to your buyers and groups.</li>
          </ul>
          <p>With one tap they go live on Avasetu’s Facebook and Instagram with your name. Nothing is posted until you say so.</p>
          <p className={note}><b>Always share your own link.</b> The link on your listing is your copy of the page, with your name, your form and your WhatsApp button. Enquiries from it come straight to you.</p>
        </Step>

        <section className="grid gap-4">
          <p className={eyebrow}>Step 6 · Buyers enquire</p>
          <h2 className={h2}>How buyers reach you, and whose lead it is</h2>
          <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
            <table className="w-full min-w-[640px] border-collapse text-[15px]">
              <thead>
                <tr className="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-500">
                  <th className="p-3">The buyer</th><th className="p-3">What happens</th><th className="p-3">Whose lead, and where</th>
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
          <p className={note}><b>Turn on alerts in Studio</b> so a new buyer rings your phone, and open Studio at least once a day. New enquiries wait at the top of Studio Home. Alerts come from Studio, not as a WhatsApp message. Call new buyers the same day, while they are still looking.</p>
        </Step>

        <Step n="The Lead Board" title="More buyers than your own listings bring"
          shot={<Phone src="/guide/lead-board.jpg" caption="Studio → Leads → Lead Board" alt="A Lead Board card showing what a buyer wants, with no name or number, and an Ask for this lead button." />}>
          <p>Buyers ask Avasetu about homes every day. Open <b>Leads</b> in Studio and tap <b>Lead Board</b> at the top to see them, newest first.</p>
          <ul className="grid list-disc gap-1 pl-5">
            <li>Each card shows the project or area, BHK, budget, timing, how old the lead is and why it looks genuine.</li>
            <li>You also see what the buyer read on the site. Their name, number and words stay hidden.</li>
            <li>Tap <b>Ask for this lead</b>. You can add an offer, a fee or a share of your brokerage when it closes, or send no offer at all.</li>
            <li>Offers are sealed: other agents see how many asked, never what anyone offered.</li>
            <li>The Avasetu team gives each lead to one agent. If it is you, it arrives in your Leads with everything we know.</li>
          </ul>
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

        <p className={note}><b>Need help?</b> Message us on WhatsApp at <b>{HELP}</b> and the Avasetu team will reply. Ready to start? <a href="/studio" className="font-semibold underline">Open Studio</a>.</p>
      </div>
    </MarketingShell>
  )
}
