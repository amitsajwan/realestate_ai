import React from 'react'
import type { Plans3D as Data } from '@/lib/site/register'

const H2 = 'text-2xl font-bold tracking-tight text-slate-900'

/** "<name> in 3D" (backend areastats/plans3d.py, owner 2026-10-31): a 3D drawing of each floor plan we read and checked, made by AI
 *  from the plan itself and compared with it (same rooms, same places, no numbers drawn in). Open to everyone as a first look;
 *  the builder's exact plan sheets stay behind the form below (#floor-plans). Room sizes come from the checked reading of the
 *  plan, never from the drawing. */
export default function Plans3D({ data, name }: { data: Data | null | undefined; name: string }) {
  if (!data || !data.items.length) return null
  return (
    <section aria-labelledby="plans-3d-title" data-testid="plans-3d">
      <h2 id="plans-3d-title" className={H2}>{name} in 3D</h2>
      <p className="mt-2 text-slate-700">See how each home is laid out before you visit.</p>
      <div className="mt-4 space-y-6">
        {data.items.map((i) => (
          <figure key={i.url} className="m-0 overflow-hidden rounded-2xl border border-slate-200 bg-white" data-testid="plan-3d">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={i.url} alt={`3D view of the ${i.label} at ${name}`} width={i.width ?? undefined} height={i.height ?? undefined}
              loading="lazy" decoding="async" className="h-auto w-full bg-[#f7f5f0]" />
            <figcaption className="p-4">
              <p className="text-lg font-semibold text-slate-900">{i.label}</p>
              {i.rooms.length > 0 && (
                <details className="mt-2">
                  <summary className="inline-flex min-h-[44px] cursor-pointer items-center text-sm font-semibold text-[#0f2340] underline underline-offset-2">
                    Room sizes ({i.rooms.length} rooms)
                  </summary>
                  <table className="mt-2 w-full border-collapse text-left text-sm">
                    <thead>
                      <tr className="border-b border-slate-300 text-slate-600">
                        <th scope="col" className="py-1.5 pr-3 font-semibold">Room</th>
                        <th scope="col" className="py-1.5 pr-3 font-semibold">Area</th>
                        <th scope="col" className="hidden py-1.5 font-semibold sm:table-cell">Size</th>
                      </tr>
                    </thead>
                    <tbody>
                      {i.rooms.map((r) => (
                        <tr key={r.name} className="border-b border-slate-100">
                          <th scope="row" className="py-1.5 pr-3 font-medium text-slate-900">{roomName(r.name)}</th>
                          <td className="py-1.5 pr-3 text-slate-800">{r.sqft ? `${r.sqft.toLocaleString('en-IN')} sq ft` : '–'}</td>
                          <td className="hidden py-1.5 text-slate-600 sm:table-cell">{r.dims ?? ''}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </details>
              )}
              <p className="mt-2 text-xs text-slate-600">
                Drawn by Avasetu with AI from {i.kind === 'builder' ? `the builder's own plan (${i.site})` : `the plan on ${i.site}`}, then
                checked against it room by room. Furniture only shows the space. Sizes are as the plan prints them.{' '}
                <a href="#floor-plans" className="font-semibold text-[#0f2340] underline underline-offset-2">Get the builder&apos;s plan sheets</a>
              </p>
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
  )
}

/** "BEDROOM -02" -> "Bedroom 2", "M.TOILET" -> "M. Toilet": the plan's capitals read as words. */
export function roomName(s: string): string {
  return s
    .replace(/\s*-\s*0*(\d+)/g, ' $1')
    .replace(/\./g, '. ')
    .toLowerCase()
    .replace(/(^|[\s/])(\w)/g, (_m, a: string, b: string) => a + b.toUpperCase())
    .replace(/\s+/g, ' ')
    .trim()
}
