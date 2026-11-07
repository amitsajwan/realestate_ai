/** What a new home in Pune costs in all, worked out from its price (owner 2026-10-24: "correct prices ... stamp duty etc.").
 *
 *  The price is taken as the agreement value, before taxes: that is how builders and property sites quote. Code adds the parts
 *  the law fixes, so they are exact once the price is known:
 *  - GST: 5% while the home is being built, 1% for an affordable home (up to ₹45 L and 90 sq m carpet: Pune is outside the six
 *    metro cities, where the limit is 60 sq m), none once the builder has the occupancy certificate (OC).
 *  - Stamp duty: 7% inside PMC and PCMC limits (5% duty, 1% local body tax, 1% metro cess), 6% when a woman buys. Charged on the
 *    agreement value or the ready reckoner value, whichever is higher, so 7% of the price is the least it can be.
 *  - Registration: 1%, at most ₹30,000.
 *  - A shop or office pays neither home rate, so its GST is left for the builder to state.
 *  What the builder adds (parking, club house, maintenance deposit, legal and society charges) differs by project and is never
 *  guessed: only the builder's cost sheet has it. */

export const GST_BUILDING = 0.05
export const GST_AFFORDABLE = 0.01
export const AFFORDABLE_MAX_PRICE = 45e5
export const AFFORDABLE_MAX_SQFT = 968          // 90 sq m
export const STAMP_DUTY = 0.07
export const REGISTRATION = 0.01
export const REGISTRATION_CAP = 30000

/** 'building': MahaRERA's filed completion date has not passed. 'completion_passed': it has, so the OC decides the GST. */
export type Stage = 'building' | 'completion_passed'

export interface CostLine {
  key: 'price' | 'gst' | 'stamp' | 'registration'
  label: string
  /** null when it cannot be known from the page (GST after the completion date: it depends on the OC) */
  amount: number | null
  note: string
}

export interface AllIn {
  lines: CostLine[]
  /** price + every line with an amount; the builder's own charges come on top */
  total: number
  /** true when GST is left out of the total because it depends on the OC */
  gstLeftOut: boolean
}

const rupees = (n: number) => Math.round(n)

/** A listing's property type that is a shop or office: home loan sums and the home GST rates do not apply to it. */
export const isCommercial = (type: string | null | undefined) => /office|shop|commercial/i.test(type || '')

/** `sqft`: the home's size when known. It may be the saleable area (sites mix them), which is never smaller than the carpet
 *  area, so a size within the limit always means the carpet is within it too; a larger one leaves the question open. */
export function allInCost(price: number, stage: Stage, sqft?: number | null, commercial = false): AllIn {
  const lines: CostLine[] = [{ key: 'price', label: 'Price (agreement value)', amount: rupees(price), note: 'As quoted, before taxes.' }]

  const cheap = price <= AFFORDABLE_MAX_PRICE
  const small = sqft != null && sqft > 0 && sqft <= AFFORDABLE_MAX_SQFT
  if (commercial) {
    lines.push({ key: 'gst', label: 'GST', amount: null,
      note: 'Shops and offices do not get the home rates of 1% or 5%: ask the builder for the GST on this unit.' })
  } else if (stage === 'completion_passed') {
    lines.push({ key: 'gst', label: 'GST', amount: null,
      note: `None if the builder has the occupancy certificate (OC). Without it, ${cheap ? '1% or 5%' : '5%'} as for a home being built.` })
  } else if (cheap && small) {
    lines.push({ key: 'gst', label: 'GST (1%)', amount: rupees(GST_AFFORDABLE * price),
      note: 'The affordable-home rate: up to ₹45 L and 90 sq m (968 sq ft) carpet.' })
  } else {
    lines.push({ key: 'gst', label: 'GST (5%)', amount: rupees(GST_BUILDING * price),
      note: cheap ? 'On a home being built. 1% instead if the carpet area is 90 sq m (968 sq ft) or less.' : 'On a home being built.' })
  }

  lines.push({ key: 'stamp', label: 'Stamp duty (7%)', amount: rupees(STAMP_DUTY * price),
    note: 'The rate inside PMC and PCMC limits; 6% if a woman buys. Charged on the ready reckoner value instead when that is higher.' })
  lines.push({ key: 'registration', label: 'Registration (1%, at most ₹30,000)', amount: rupees(Math.min(REGISTRATION * price, REGISTRATION_CAP)), note: '' })

  const total = lines.reduce((sum, l) => sum + (l.amount ?? 0), 0)
  return { lines, total, gstLeftOut: commercial || stage === 'completion_passed' }
}

export const BUILDER_CHARGES_NOTE = 'Not included: parking, club house, maintenance deposit, legal and society charges. They differ by '
  + 'project: ask the builder for the full cost sheet. If a price already includes GST or stamp duty, do not add them twice.'
