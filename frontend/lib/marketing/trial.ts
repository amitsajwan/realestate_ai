import { waNumber } from '@/components/site/WhatsAppButton'
import { PATHS } from '@/lib/marketing/strings'

export const TRIAL_PATH = '/trial'

/** Where "Claim your free trial" goes: WhatsApp with "TRIAL" typed in (the reply carries the sign-up code), or, with no platform
 *  number configured, the request form carrying the ?src= tag. */
export function claimHref(src: string, rawNumber: string | undefined): string {
  const number = waNumber(rawNumber)
  if (number) return `https://wa.me/${number}?text=${encodeURIComponent('TRIAL')}`
  return `${PATHS.invite}?src=${encodeURIComponent(src)}`
}
