import { metadata } from '@/app/layout'

// Google shows a page's picture large (Discover cards, image previews in results) only when the page allows it; a page that
// sets its own `robots` (noindex) replaces this whole object, which is what those pages want.
test('every page allows large image previews and full snippets unless it says otherwise', () => {
  expect(metadata.robots).toEqual({ index: true, follow: true, 'max-image-preview': 'large', 'max-snippet': -1, 'max-video-preview': -1 })
})
