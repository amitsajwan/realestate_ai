import { render, screen } from '@testing-library/react'
import React from 'react'
import { VoiceRecorder } from '@/components/app/VoiceRecorder'

describe('voice listing is a Premium feature (visible but disabled by default)', () => {
  it('shows a greyed-out mic with a Premium badge and never records', () => {
    const onChange = jest.fn()
    render(<VoiceRecorder onChange={onChange} />)
    const mic = screen.getByRole('button', { name: /Voice listing \(Premium\)/i })
    expect(mic).toBeDisabled()
    expect(screen.getByText('Premium')).toBeInTheDocument()
    expect(screen.getByText(/Coming with Premium/i)).toBeInTheDocument()
    expect(screen.queryByText(/Tap to speak/i)).toBeNull()
    expect(onChange).not.toHaveBeenCalled()
  })
})
