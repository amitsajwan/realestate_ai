/** Each page view says how it was reached, so Studio can tell a visit step by step: a tapped link and its words, Back, a reload. */
import { linkWords, readStep, watchNavigation } from '@/lib/site/tracking'

function go(path: string) {
  window.history.pushState({}, '', path)
}

function tap(href: string, html: string) {
  const a = document.createElement('a')
  a.href = href
  a.innerHTML = html
  a.addEventListener('click', (e) => e.preventDefault()) // jsdom would try to navigate
  document.body.appendChild(a)
  a.click()
  a.remove()
}

beforeEach(() => {
  window.sessionStorage.clear()
  go('/')
})

test('a visit is told step by step: the first page, a tapped link with its words, Back, a reload', () => {
  watchNavigation()
  go('/projects/godrej-ivara-pune')
  expect(readStep()).toEqual({})

  tap('/projects/area/kharadi', '<span>More projects</span>\n  in  Kharadi')
  go('/projects/area/kharadi')
  expect(readStep()).toEqual({ prev: '/projects/godrej-ivara-pune', via: 'link', link: 'More projects in Kharadi' })

  window.dispatchEvent(new PopStateEvent('popstate'))
  go('/projects/godrej-ivara-pune')
  expect(readStep()).toEqual({ prev: '/projects/area/kharadi', via: 'back' })

  expect(readStep()).toEqual({ via: 'reload' })
})

test('a stale tap or a tap on another page is not how they got here', () => {
  watchNavigation()
  let clock = Date.now() + 10_000 // well after the first test's Back press
  go('/')
  readStep(() => clock)
  tap('/guides/mhada-pune-lottery', 'MHADA guide')
  go('/projects')
  expect(readStep(() => clock)).toEqual({ prev: '/' }) // the link went elsewhere: moved some other way
  clock += 60_000
  go('/news')
  expect(readStep(() => clock)).toEqual({ prev: '/projects' })
})

test('a link without words is named by its label or picture', () => {
  const a = document.createElement('a')
  a.innerHTML = '<img alt="Godrej Ivara photo" src="x.jpg" />'
  expect(linkWords(a)).toBe('Godrej Ivara photo')
  a.setAttribute('aria-label', 'Open Godrej Ivara')
  expect(linkWords(a)).toBe('Open Godrej Ivara')
})
