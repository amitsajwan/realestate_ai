/* Studio's service worker (scope /studio; registered by lib/app/phone.ts, served by next.config.js with Service-Worker-Allowed).
 *
 * It does three things and nothing else:
 *  - push: shows the alert the backend sent (app/modules/notifications/push.py: {title, body, url, tag}).
 *  - notificationclick: opens that Studio screen, in the Studio window already open if there is one.
 *  - offline: a Studio page that cannot load shows a short note instead of the browser's error. Nothing is cached, so Studio
 *    never shows old leads or old prices.
 */
const ICON = '/brand/icon-192.png'

const OFFLINE = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Studio is offline</title><style>body{margin:0;font-family:system-ui,sans-serif;background:#f9fafb;color:#0f172a}
div{max-width:420px;margin:0 auto;padding:64px 20px}h1{font-size:22px}p{font-size:17px;line-height:1.5;color:#334155}
button{min-height:52px;width:100%;border:0;border-radius:12px;background:#0f2340;color:#fff;font-size:16px;font-weight:600}</style></head>
<body><div><h1>No internet right now</h1><p>Studio needs the internet to show your leads. It opens again as soon as your phone is back online.</p>
<button onclick="location.reload()">Try again</button></div><script>addEventListener('online',()=>location.reload())</script></body></html>`

self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()))

self.addEventListener('fetch', (event) => {
  if (event.request.mode !== 'navigate') return   // scripts, styles and the API go to the network as always
  event.respondWith(fetch(event.request).catch(() => new Response(OFFLINE, { headers: { 'Content-Type': 'text/html; charset=utf-8' } })))
})

function studioUrl(url) {
  return typeof url === 'string' && url.startsWith('/studio') ? url : '/studio'
}

self.addEventListener('push', (event) => {
  let data = {}
  try {
    data = event.data ? event.data.json() : {}
  } catch (e) {
    data = { body: event.data ? event.data.text() : '' }
  }
  event.waitUntil(self.registration.showNotification(data.title || 'Studio', {
    body: data.body || '',
    icon: ICON,
    badge: ICON,
    tag: data.tag || undefined,
    renotify: Boolean(data.tag),   // a newer alert about the same buyer replaces the old one and still rings
    data: { url: studioUrl(data.url) },
  }))
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const url = new URL(studioUrl(event.notification.data && event.notification.data.url), self.location.origin).href
  event.waitUntil((async () => {
    const open = await self.clients.matchAll({ type: 'window', includeUncontrolled: true })
    const studio = open.find((w) => new URL(w.url).pathname.startsWith('/studio'))
    if (studio) {
      await studio.focus()
      if ('navigate' in studio) await studio.navigate(url)
      return
    }
    await self.clients.openWindow(url)
  })())
})
