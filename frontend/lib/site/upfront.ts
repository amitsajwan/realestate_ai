/** The cash a buyer pays from their own pocket when the rest is a home loan: the part a bank may not lend (RBI limits: 90% for
 *  a loan up to ₹30 L, 80% up to ₹75 L, 75% above) plus stamp duty (7% in Pune; 6% when a woman buys) and registration (1%,
 *  at most ₹30,000), which no bank lends. GST is not added: an all-in quote already has it. */
export function ownCash(price: number): number {
  const loan = Math.max(Math.min(0.9 * price, 30e5), Math.min(0.8 * price, 75e5), 0.75 * price)
  return Math.round(price - loan + 0.07 * price + Math.min(0.01 * price, 30000))
}

/** The example EMI the agent's offer card shows (backend propertyfacts/calc.py EMI_LOAN_SHARE, EMI_RATE, EMI_YEARS): kept the same
 *  here, so a page with only published prices states it the same way. */
export const EMI_LOAN_SHARE = 0.8
export const EMI_RATE = 8.5
export const EMI_YEARS = 20

/** { emi, loan, rate, years } for a home at `price`: 80% of it as a loan at EMI_RATE over EMI_YEARS; null for no price. */
export function emiFor(price: number | null | undefined): { emi: number; loan: number; rate: number; years: number } | null {
  if (!price || price <= 0) return null
  const loan = price * EMI_LOAN_SHARE
  const r = EMI_RATE / 12 / 100
  const n = EMI_YEARS * 12
  return { emi: Math.round((loan * r * (1 + r) ** n) / ((1 + r) ** n - 1)), loan: Math.round(loan), rate: EMI_RATE, years: EMI_YEARS }
}

export const OWN_CASH_NOTE = 'Your own cash, about: the part banks may not lend (RBI: 75% to 90% of the price is the most a home loan covers), '
  + 'stamp duty 7% (6% if a woman buys) and registration up to ₹30,000. Add GST (5% on homes being built) if the price leaves it out.'
