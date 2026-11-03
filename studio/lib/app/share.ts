/** WhatsApp share + copy helpers. */

export function whatsappShareUrl(text: string): string {
  return `https://wa.me/?text=${encodeURIComponent(text)}`
}

/** Link to chat with a specific number, optionally with a pre-filled message. */
export function whatsappChatUrl(digits: string, text?: string): string {
  return `https://wa.me/${digits}${text ? `?text=${encodeURIComponent(text)}` : ''}`
}

/** site_url + /listings/{id}?src=whatsapp (site_url may or may not end in a slash). */
export function listingLink(siteUrl: string | null | undefined, listingId: string, src = 'whatsapp'): string {
  const base = (siteUrl ?? '').replace(/\/+$/, '')
  return `${base}/listings/${listingId}?src=${src}`
}

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    try {
      const ta = document.createElement('textarea')
      ta.value = text
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      const ok = document.execCommand('copy')
      document.body.removeChild(ta)
      return ok
    } catch {
      return false
    }
  }
}
