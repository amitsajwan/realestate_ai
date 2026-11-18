import { fireEvent, render, screen, within } from '@testing-library/react'
import React from 'react'
import { BuyerBrief } from '@/components/app/BuyerBrief'
import { EMPTY_VIEW, type BriefView, type LeadBrief } from '@/lib/app/buyerMind'

const brief: LeadBrief = {
  buyer: '2 BHK buyer, ₹50-80 L, home loan, moving in 3-6 months',
  implied: ['Serious: asked for plans late at night'], unknown: ['which floor'],
  asked_for: 'floor plans', can_answer: 'no',
  flags: ['Possession is due December 2027, after the 3-6 months he wants'],
  alternatives: [{ slug: 'kohinoor-ravet-ready', name: 'Kohinoor Ravet Ready', why: 'completed' }],
  price_idea: '2 BHK ₹68 Lakh to ₹74 Lakh on puraniks.com, read 20 Oct', next_step: 'Call tomorrow morning', when: 'tomorrow',
  temperature: 'hot', draft: 'Namaste Rahul ji, our team is getting the floor plans. Avasetu team', why: 'He wants plans soon.',
  confidence: 'medium', problems: [], by: 'mind',
}
const thought: BriefView = { brief, at: new Date().toISOString(), outcome: 'done', lookups: ['project_facts'], profile: null }
const api = { brief: jest.fn(async () => EMPTY_VIEW), think: jest.fn(async () => thought) }

jest.mock('@/lib/app/buyerMind', () => ({
  ...jest.requireActual('@/lib/app/buyerMind'),
  buyerMindApi: { brief: (...a: unknown[]) => (api.brief as (...x: unknown[]) => unknown)(...a),
                  think: (...a: unknown[]) => (api.think as (...x: unknown[]) => unknown)(...a) },
}))
jest.mock('@/lib/app/client', () => ({ errorMessage: (e: Error) => e.message }))

describe('BuyerBrief', () => {
  it('thinks about a lead on request, then shows what to tell them and a draft to send from their own WhatsApp', async () => {
    render(<BuyerBrief leadId="rahul" phone="+919822000001" />)
    expect(await screen.findByText(/Not thought about yet/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Think about this lead' }))
    const panel = await screen.findByRole('region', { name: 'Buyer brief' })
    expect(await within(panel).findByText(brief.buyer!)).toBeInTheDocument()
    expect(api.think).toHaveBeenCalledWith('rahul')
    expect(within(screen.getByRole('note', { name: 'Tell them' })).getByText(brief.flags[0])).toBeInTheDocument()
    expect(within(panel).getByText(/We cannot answer this yet/)).toBeInTheDocument()
    expect(within(panel).getByRole('link', { name: 'Kohinoor Ravet Ready' })).toHaveAttribute('href', '/projects/kohinoor-ravet-ready')
    const box = within(panel).getByLabelText('Suggested reply (edit before sending)')
    fireEvent.change(box, { target: { value: 'Rahul ji, edited' } })
    const send = within(panel).getByRole('link', { name: 'Send from my WhatsApp' })
    expect(send.getAttribute('href')).toContain('919822000001')
    expect(decodeURIComponent(send.getAttribute('href')!)).toContain('Rahul ji, edited')
    expect(within(panel).getByRole('button', { name: 'Think again' })).toBeInTheDocument()
  })

  it('says when the checks left the reply out, and when the brief is the lead facts alone', async () => {
    api.brief.mockResolvedValueOnce({ ...thought, brief: { ...brief, draft: null, problems: ['draft dropped: price'] } })
    const { unmount } = render(<BuyerBrief leadId="rahul" phone="+919822000001" />)
    expect(await screen.findByText(/the checks left it out/)).toBeInTheDocument()
    expect(screen.getByText(/Left out by the checks: draft dropped: price/)).toBeInTheDocument()
    unmount()
    api.brief.mockResolvedValueOnce({ ...thought, brief: { ...brief, draft: null, by: 'rules', flags: [] } })
    render(<BuyerBrief leadId="rahul" phone="+919822000001" />)
    expect(await screen.findByText(/From the lead’s details only/)).toBeInTheDocument()
    expect(screen.queryByText(/the checks left it out/)).not.toBeInTheDocument()
  })

  it('shows the server’s reason when thinking again is too soon', async () => {
    api.brief.mockResolvedValueOnce(thought)
    api.think.mockRejectedValueOnce(new Error('Thought about this lead a moment ago; try again in 91 s'))
    render(<BuyerBrief leadId="rahul" phone="+919822000001" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Think again' }))
    expect(await screen.findByText(/try again in 91 s/)).toBeInTheDocument()
  })
})
