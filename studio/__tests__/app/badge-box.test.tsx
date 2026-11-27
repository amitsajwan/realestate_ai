// "Badge for your website" on a listing: only for a MahaRERA number in our register, with code that links the project page
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { BadgeBox } from '@/components/app/BadgeBox'

describe('BadgeBox', () => {
  afterEach(() => { delete (global as { fetch?: unknown }).fetch })

  it('shows the badge and its code once the register knows the number', async () => {
    ;(global as any).fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({ slug: 'godrej-ivara-pune' }) })
    render(<BadgeBox regno=" pr1260002502426 " name="Godrej Ivara" />)
    const box = await screen.findByTestId('badge-box')
    expect((global.fetch as jest.Mock).mock.calls[0][0]).toBe('/api/v1/public/register/by-regno/PR1260002502426')
    const code = (screen.getByLabelText('Badge code') as HTMLTextAreaElement).value
    expect(code).toContain('/projects/godrej-ivara-pune"')
    expect(code).toContain('/badge/PR1260002502426.svg')
    expect(box).toHaveTextContent('Copy the code')
    expect(screen.getByTestId('badge-qr').getAttribute('href')).toMatch(/\/qr\/godrej-ivara-pune\.svg$/)
  })

  it('shows nothing for a number we do not hold', async () => {
    ;(global as any).fetch = jest.fn().mockResolvedValue({ ok: false, json: async () => ({}) })
    const { container } = render(<BadgeBox regno="P52100099999" name="X" />)
    await waitFor(() => expect(global.fetch).toHaveBeenCalled())
    expect(container).toBeEmptyDOMElement()
  })
})
