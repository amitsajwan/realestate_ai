import React from 'react'
import { poppins } from '@/lib/marketing/font'

/** Standalone brand surface: hides the app navigation the root layout adds around other pages. */
export default function InterestLayout({ children }: { children: React.ReactNode }) {
  return (
    <div data-surface="v2" lang="en" className={poppins.className + ' min-h-screen bg-[#fbf6ea] text-slate-900'}>
      <style>{'body > nav{display:none}'}</style>
      {children}
    </div>
  )
}
