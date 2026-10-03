/** Shared layout classes for the home page sections (navy/gold Avasetu surface). */
export const wrap = 'mx-auto max-w-5xl px-4'
export const h2 = 'text-2xl font-extrabold tracking-tight text-[#0f2340] sm:text-3xl'
export const moreLink = 'inline-flex min-h-[44px] items-center font-semibold text-[#0f2340] underline underline-offset-4'

/**
 * Where "Tell us what you are looking for" leads: the house agent site's enquiry form, the same target the locality
 * guides use (NEXT_PUBLIC_DEFAULT_AGENT_SLUG, inlined at build time).
 */
export const buyerEnquiryPath = (): string => `/agent/${process.env.NEXT_PUBLIC_DEFAULT_AGENT_SLUG || 'avasetu'}#enquire`
