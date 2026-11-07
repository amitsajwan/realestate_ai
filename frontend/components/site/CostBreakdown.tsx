import React from 'react'
import { allInCost, BUILDER_CHARGES_NOTE, type Stage } from '@/lib/site/allin'
import { formatPrice } from '@/lib/site/format'

/** The all-in cost of one price, folded under it: price, GST, stamp duty, registration, then what only the builder's cost sheet
 *  has (lib/site/allin.ts). `what` names the home ("the 2 BHK") so a page with several prices says which one this is. */
export default function CostBreakdown({ price, stage, sqft, what, commercial }: { price: number; stage: Stage; sqft?: number | null; what: string; commercial?: boolean }) {
  const c = allInCost(price, stage, sqft, commercial)
  return (
    <details className="mt-2 rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm" data-testid="all-in">
      <summary className="min-h-[44px] cursor-pointer py-2 font-semibold text-slate-900">
        All-in cost of {what}: about {formatPrice(c.total)}{c.gstLeftOut ? (commercial ? ' + GST' : ' + GST if any') : ''}
      </summary>
      <table className="mt-1 w-full text-left">
        <tbody>
          {c.lines.map((l) => (
            <tr key={l.key} className="border-b border-slate-200 align-top last:border-0">
              <th scope="row" className="py-1.5 pr-3 font-medium text-slate-800">
                {l.label}
                {l.note && <span className="block text-xs font-normal text-slate-600">{l.note}</span>}
              </th>
              <td className="whitespace-nowrap py-1.5 text-right font-semibold text-slate-900">{l.amount != null ? formatPrice(l.amount) : 'Ask'}</td>
            </tr>
          ))}
          <tr>
            <th scope="row" className="pt-2 pr-3 font-bold text-slate-900">Total before the builder&apos;s charges</th>
            <td className="whitespace-nowrap pt-2 text-right font-bold text-slate-900" data-testid="all-in-total">{formatPrice(c.total)}</td>
          </tr>
        </tbody>
      </table>
      <p className="mt-2 text-xs text-slate-600">{BUILDER_CHARGES_NOTE}</p>
    </details>
  )
}
