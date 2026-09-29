import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import { JoinFlow } from '@/components/app/JoinFlow'
import { ReviewForm } from '@/components/app/ReviewForm'

const requestOtp = jest.fn()
const verifyOtp = jest.fn()
jest.mock('@/lib/app/client', () => ({
  api: {
    requestOtp: (...a: unknown[]) => requestOtp(...a),
    verifyOtp: (...a: unknown[]) => verifyOtp(...a),
    createSite: jest.fn(),
  },
  errorMessage: (e: Error) => e.message,
  isFixtureMode: () => false,
}))

describe('JoinFlow', () => {
  beforeEach(() => {
    requestOtp.mockReset()
    verifyOtp.mockReset()
    window.localStorage.clear()
  })

  it('rejects a bad number, then normalises and shows the dev OTP hint', async () => {
    requestOtp.mockResolvedValue({ sent: true, dev_code: '654321' })
    render(<JoinFlow />)
    const input = screen.getByLabelText(/mobile number/i)
    fireEvent.change(input, { target: { value: '12345' } })
    fireEvent.click(screen.getByRole('button', { name: /send otp/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/valid 10-digit/i)
    expect(requestOtp).not.toHaveBeenCalled()

    fireEvent.change(input, { target: { value: '98765 43210' } })
    fireEvent.click(screen.getByRole('button', { name: /send otp/i }))
    await waitFor(() => expect(requestOtp).toHaveBeenCalledWith('+919876543210'))
    expect(await screen.findByText('654321')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /resend otp in 30s/i })).toBeDisabled()
  })

  it('autofill verifies and stores the session', async () => {
    requestOtp.mockResolvedValue({ sent: true, dev_code: '654321' })
    verifyOtp.mockResolvedValue({ access_token: 'tok', is_new_user: true, has_site: false, site_url: null })
    render(<JoinFlow />)
    fireEvent.change(screen.getByLabelText(/mobile number/i), { target: { value: '9876543210' } })
    fireEvent.click(screen.getByRole('button', { name: /send otp/i }))
    fireEvent.click(await screen.findByRole('button', { name: /fill it/i }))
    await waitFor(() => expect(verifyOtp).toHaveBeenCalledWith('+919876543210', '654321'))
    expect(await screen.findByLabelText(/your name/i)).toBeInTheDocument()
    expect(window.localStorage.getItem('app_token')).toBe('tok')
  })
})

describe('ReviewForm', () => {
  it('shows lakh/crore while editing rupees, and flags low confidence and missing fields', () => {
    const onChange = jest.fn()
    render(<ReviewForm value={{ title: 'x', price_inr: 8_500_000 }} onChange={onChange} confidence={{ title: 0.4 }} missing={['locality']} />)
    expect(screen.getByText(/₹85 L/)).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText(/price/i), { target: { value: '1.2 cr' } })
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ price_inr: 12_000_000 }))
    expect(screen.getByText('Please check')).toBeInTheDocument()
    expect(screen.getByText('Required to publish')).toBeInTheDocument()
  })
})
