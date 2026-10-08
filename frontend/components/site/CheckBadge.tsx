import React from 'react'

/** How far our crawler has checked a project page (areastats.enrich): all checks passed, some, or not reached yet.
 *  Every project is MahaRERA-registered; this badge is about the extra checks on top. */
export default function CheckBadge({ checked, total = 4, compact = false }: { checked?: number | null; total?: number; compact?: boolean }) {
  const [style, text, title] = checked == null
    ? ['bg-slate-100 text-slate-600 ring-slate-300', compact ? 'MahaRERA only' : 'MahaRERA only, not checked yet', 'Our crawler has not checked this project yet']
    : checked >= total
      ? ['bg-emerald-50 text-emerald-800 ring-emerald-200', compact ? 'Checked' : `Checked ${checked}/${total}`, 'Our crawler checked every part of this page']
      : ['bg-sky-50 text-sky-800 ring-sky-200', `Checked ${checked}/${total}`, `Our crawler confirmed ${checked} of ${total} checks`]
  return (
    <span title={title} className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 align-middle text-xs font-semibold ring-1 ring-inset ${style}`}>
      <span aria-hidden>{checked == null ? '·' : '✓'}</span>{text}
    </span>
  )
}
