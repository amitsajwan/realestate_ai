const { htmlLimitedBots } = require('../next.config.js')

// A reader on this list gets the title in <head> even on a slow render; anyone else may get it late, in <body>.
describe('htmlLimitedBots', () => {
  test.each([
    'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
    'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot',
    'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot',
    'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot',
    'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; Claude-User/1.0; +Claude-User@anthropic.com',
    'AvasetuSeoAudit-Google/1.0 (+https://github.com/amitsajwan/realestate_ai)',
  ])('search and AI readers get the title in the head: %s', (agent) => {
    expect(htmlLimitedBots.test(agent)).toBe(true)
  })

  test('a person on a phone still gets the page streamed', () => {
    expect(htmlLimitedBots.test('Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36')).toBe(false)
  })
})
