import React from 'react'
import Link from 'next/link'

export default function AgentNotFound() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center gap-4 bg-white px-4 text-center">
      <h1 className="text-3xl font-extrabold text-slate-900">This page could not be found</h1>
      <p className="max-w-md text-slate-600">The agent website or property you are looking for does not exist, or is no longer available.</p>
      <Link href="/" className="inline-flex min-h-[48px] items-center rounded-xl bg-slate-900 px-6 font-semibold text-white no-underline">Go to home</Link>
    </div>
  )
}
