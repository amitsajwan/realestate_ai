import React from 'react'
import { render, screen } from '@testing-library/react'
import InsightPage from '@/app/insights/[slug]/page'
import { INSIGHTS, getInsight } from '@/lib/marketing/insights'

jest.mock('next/navigation', () => ({ useRouter: () => ({ push: jest.fn() }), usePathname: () => '/insights', notFound: jest.fn() }))

const SLUG = 'ai-real-estate-data-verification'

// the website version of the LinkedIn article (owner 2026-11-21): our own page, linking the live project pages it uses as examples
describe('the how-we-use-AI article', () => {
  it('names its team as the author and links the two example project pages and the way to report a wrong page', async () => {
    const { container } = render(await InsightPage({ params: Promise.resolve({ slug: SLUG }) }))
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/without letting it make things up/)
    expect(screen.getByText(/^By the Avasetu team/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Kohinoor Kaleido, Wagholi/ })).toHaveAttribute('href', '/projects/kohinoor-kaleido-wagholi')
    expect(screen.getByRole('link', { name: /Venkatesh Vanaya, Kharadi/ })).toHaveAttribute('href', '/projects/venkatesh-vanaya-wing-i-j-phase-2-kharadi')
    expect(screen.getByRole('link', { name: /Tell us a page is wrong/ })).toHaveAttribute('href', '/contact')
    // the LinkedIn version is a source, opened in a new tab
    const linkedin = screen.getByRole('link', { name: /on LinkedIn/ })
    expect(linkedin).toHaveAttribute('target', '_blank')
    expect(linkedin.getAttribute('href')).toMatch(/^https:\/\/www\.linkedin\.com\/pulse\//)
    const ld = Array.from(container.querySelectorAll('script[type="application/ld+json"]')).map((s) => JSON.parse(s.innerHTML))
    expect(ld.find((x) => x['@type'] === 'Article')).toMatchObject({ author: { name: 'Avasetu team' }, dateModified: '2026-11-21' })
  })

  it("is about how we work, so it is kept off agents' lists of buyer guides", () => {
    expect(getInsight(SLUG)?.aboutUs).toBe(true)
    expect(INSIGHTS.filter((a) => a.aboutUs).map((a) => a.slug)).toEqual([SLUG])
    // and it never states a price, as the other guides do not
    expect(JSON.stringify(getInsight(SLUG))).not.toMatch(/₹|guarantee|appreciat/i)
  })
})
