import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import RequestInviteForm from '@/components/marketing/RequestInviteForm'

const fillValid = () => {
  fireEvent.change(screen.getByLabelText('Your name'), { target: { value: 'Rahul Sharma' } })
  fireEvent.change(screen.getByLabelText('Mobile number'), { target: { value: '+91 98765 43210' } })
  fireEvent.click(screen.getByRole('checkbox', { name: /ok to contact me/i }))
}
const submit = () => fireEvent.click(screen.getByRole('button', { name: /send request/i }))

describe('RequestInviteForm', () => {
  beforeEach(() => {
    ;(global as any).fetch = jest.fn().mockResolvedValue({ ok: true, status: 200 })
  })

  it('has the honeypot named "website", empty, hidden from people and assistive tech', () => {
    const { container } = render(<RequestInviteForm />)
    const hp = container.querySelector('input[name="website"]') as HTMLInputElement
    expect(hp).not.toBeNull()
    expect(hp.value).toBe('')
    expect(hp.tabIndex).toBe(-1)
    expect(hp.closest('[aria-hidden="true"]')).not.toBeNull()
  })

  it('defaults the city to Pune', () => {
    render(<RequestInviteForm />)
    expect(screen.getByLabelText('City')).toHaveValue('Pune')
  })

  it('validates name, phone and consent without calling the API', async () => {
    render(<RequestInviteForm />)
    fireEvent.change(screen.getByLabelText('Mobile number'), { target: { value: '12345' } })
    submit()
    expect(await screen.findByText(/please enter your name/i)).toBeInTheDocument()
    expect(screen.getByText(/valid 10-digit indian mobile/i)).toBeInTheDocument()
    expect(screen.getByText(/tick the box/i)).toBeInTheDocument()
    expect(global.fetch).not.toHaveBeenCalled()
  })

  it('requires consent even when everything else is valid', async () => {
    render(<RequestInviteForm />)
    fillValid()
    fireEvent.click(screen.getByRole('checkbox', { name: /ok to contact me/i })) // untick
    submit()
    expect(await screen.findByText(/tick the box/i)).toBeInTheDocument()
    expect(global.fetch).not.toHaveBeenCalled()
  })

  it('posts the payload with an empty honeypot and the normalised +91 number, then shows success', async () => {
    render(<RequestInviteForm />)
    fillValid()
    fireEvent.change(screen.getByLabelText(/anything you would like/i), { target: { value: 'Baner and Wakad' } })
    submit()
    await waitFor(() => expect(screen.getByText(/thank you, rahul/i)).toBeInTheDocument())
    const [url, init] = (global.fetch as jest.Mock).mock.calls[0]
    expect(url).toBe('/api/v1/join/request-invite')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body)).toEqual({
      name: 'Rahul Sharma', phone: '+919876543210', city: 'Pune', message: 'Baner and Wakad', consent: true, website: '',
    })
    expect(screen.getByText(/\+91 98765 43210/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /back to the home page/i })).toHaveAttribute('href', '/')
  })

  it('omits an empty message', async () => {
    render(<RequestInviteForm />)
    fillValid()
    submit()
    await waitFor(() => expect(global.fetch).toHaveBeenCalled())
    expect(JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body)).not.toHaveProperty('message')
  })

  it('shows a friendly message on 429 and keeps what was typed', async () => {
    ;(global as any).fetch = jest.fn().mockResolvedValue({ ok: false, status: 429 })
    render(<RequestInviteForm />)
    fillValid()
    submit()
    expect(await screen.findByRole('alert')).toHaveTextContent(/too many requests/i)
    expect(screen.getByLabelText('Your name')).toHaveValue('Rahul Sharma')
    expect(screen.queryByText(/thank you/i)).toBeNull()
  })

  it('shows a retry message when the network fails or the server errors', async () => {
    ;(global as any).fetch = jest.fn().mockRejectedValue(new Error('offline'))
    render(<RequestInviteForm />)
    fillValid()
    submit()
    expect(await screen.findByText(/could not send your request/i)).toBeInTheDocument()
    ;(global as any).fetch = jest.fn().mockResolvedValue({ ok: false, status: 500 })
    submit()
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1))
    expect(await screen.findByText(/could not send your request/i)).toBeInTheDocument()
  })

  it('shows a check-your-details message on 422', async () => {
    ;(global as any).fetch = jest.fn().mockResolvedValue({ ok: false, status: 422 })
    render(<RequestInviteForm />)
    fillValid()
    submit()
    expect(await screen.findByText(/were not accepted/i)).toBeInTheDocument()
  })

  it('links to the privacy policy', () => {
    render(<RequestInviteForm />)
    expect(screen.getByRole('link', { name: /privacy/i })).toHaveAttribute('href', '/privacy')
  })
})
