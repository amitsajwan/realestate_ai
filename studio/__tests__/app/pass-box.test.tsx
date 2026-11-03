import { fireEvent, render, screen, within } from '@testing-library/react'
import React from 'react'
import { PassBox, PassedNote } from '@/components/app/PassBox'
import type { Handover, PassResult } from '@/lib/app/inbox'

const card = {
  lines: [{ label: 'Name', value: 'Saket Patil' }, { label: 'Project', value: 'Mansha Phase-II, Wagholi (MahaRERA P52100028315)' },
    { label: 'Home', value: '2 BHK' }],
  missing: ['budget', 'when they want to buy'],
  text: 'New buyer for you from Avasetu',
}
const handover: Handover = { card, project: { slug: 'mansha-phase-ii-wagholi', name: 'Mansha Phase-II', area: 'Wagholi', regno: 'P52100028315' }, rule: null, areas: ['Wagholi'] }
const passed: PassResult = { passed_to: 'House Deal', lead_id: 'l1', card, whatsapp_status: 'sent', whatsapp_error: null,
  rule_added: { kind: 'area', label: 'Wagholi' }, whatsapp_url: 'https://wa.me/919921900001?text=x' }
const passLead = jest.fn(async () => passed)

jest.mock('@/lib/app/inbox', () => ({
  ...jest.requireActual('@/lib/app/inbox'),
  inboxApi: {
    agents: async () => [{ agent_id: 'HD', name: 'House Deal', has_whatsapp: true, slug: 'house-deal' }],
    handover: async () => handover,
    passLead: (...a: unknown[]) => (passLead as (...x: unknown[]) => Promise<PassResult>)(...a),
    pass: jest.fn(),
  },
}))
jest.mock('@/lib/app/client', () => ({ errorMessage: (e: Error) => e.message }))

describe('PassBox', () => {
  it('shows the card the agent gets, then passes with the area rule', async () => {
    render(<PassBox leadId="l1" />)
    fireEvent.click(screen.getByRole('button', { name: 'Pass to an agent' }))
    expect(await screen.findByText('Mansha Phase-II, Wagholi (MahaRERA P52100028315)')).toBeInTheDocument()
    expect(screen.getByText(/they should ask: budget, when they want to buy/)).toBeInTheDocument()
    fireEvent.change(await screen.findByLabelText('Pass this buyer to'), { target: { value: 'HD' } })
    expect(screen.getByRole('option', { name: 'House Deal (/agent/house-deal)' })).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText('Pass every Wagholi lead to this agent by itself'))
    fireEvent.click(screen.getByRole('button', { name: 'Pass' }))
    const note = await screen.findByRole('region', { name: 'Passed' })
    expect(passLead).toHaveBeenCalledWith('l1', 'HD', 'area')
    expect(within(note).getByText(/full details went to House Deal on WhatsApp/)).toBeInTheDocument()
    expect(within(note).getByText(/leads about Wagholi go to House Deal by themselves/)).toBeInTheDocument()
  })
})

describe('PassedNote', () => {
  it('asks the owner to send from their phone when the template did not go', () => {
    render(<PassedNote r={{ ...passed, whatsapp_status: 'failed', whatsapp_error: 'template not approved', rule_added: null }} />)
    expect(screen.getByText(/did not go out \(template not approved\)/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Send the details to House Deal on WhatsApp' })).toHaveAttribute('href', passed.whatsapp_url)
  })
})
