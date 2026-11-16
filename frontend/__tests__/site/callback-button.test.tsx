// "Call me back": the number and a tick, nothing else; the lead says it asked for a call back (backend handover.ask_of)
import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import CallbackButton from '@/components/site/CallbackButton'

describe('CallbackButton', () => {
  beforeEach(() => {
    ;(global as any).fetch = jest.fn().mockResolvedValue({ ok: true })
  })

  it('opens to one number field, and sends nothing without a valid number and the buyer\'s own tick', async () => {
    render(<CallbackButton topic="KOLTE PATIL SPRINGSHIRE (MahaRERA P1)" />)
    fireEvent.click(screen.getByRole('button', { name: /call me back/i }))
    expect(screen.getByRole('checkbox')).not.toBeChecked()
    fireEvent.change(screen.getByLabelText('Your mobile number'), { target: { value: '12345' } })
    fireEvent.click(screen.getByRole('button', { name: 'Call me' }))
    expect(await screen.findByText(/valid 10-digit/i)).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Your mobile number'), { target: { value: '98765 11111' } })
    fireEvent.click(screen.getByRole('button', { name: 'Call me' }))
    expect(await screen.findByText(/tick the box/i)).toBeInTheDocument()
    expect(global.fetch).not.toHaveBeenCalled()
  })

  it('sends a call-back enquiry with no name to the house account, about the project', async () => {
    render(<CallbackButton topic="KOLTE PATIL SPRINGSHIRE (MahaRERA P1)" />)
    fireEvent.click(screen.getByRole('button', { name: /call me back/i }))
    fireEvent.change(screen.getByLabelText('Your mobile number'), { target: { value: '+91 98765 11111' } })
    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(screen.getByRole('button', { name: 'Call me' }))
    await waitFor(() => expect(screen.getByTestId('callback-done')).toHaveTextContent('The Avasetu team will call you soon'))
    const [url, init] = (global.fetch as jest.Mock).mock.calls[0]
    expect(url).toMatch(/\/api\/v1\/t\/inquiry$/)
    const body = JSON.parse(init.body)
    expect(body).toMatchObject({ agent_slug: 'avasetu', name: '', callback: true, consent: true,
      message: 'Call back: KOLTE PATIL SPRINGSHIRE (MahaRERA P1)' })
  })
})
