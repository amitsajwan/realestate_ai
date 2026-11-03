import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { BrandEditor } from '@/components/app/BrandEditor'
import type { BrandingDoc } from '@/lib/app/branding'

const doc = (b: BrandingDoc['branding_data'] = {}): BrandingDoc => ({ slug: 'priya', agent_name: 'Priya Deshmukh', branding_data: b })

function setup(initial = doc()) {
  const load = jest.fn().mockResolvedValue(initial)
  const save = jest.fn().mockImplementation(async (patch) => doc({ ...initial.branding_data, ...patch }))
  const upload = jest.fn().mockResolvedValue('/uploads/images/new.jpg')
  render(<BrandEditor agentId="a1" loadBranding={load} saveBranding={save} uploadImage={upload} />)
  return { load, save, upload }
}

describe('BrandEditor', () => {
  it('loads with the agent id, shows a live preview and switches preset', async () => {
    const { load } = setup(doc({ business_name: 'Kulkarni Homes', preset: 'emerald' }))
    await screen.findByTestId('brand-editor')
    expect(load).toHaveBeenCalledWith('a1')
    const preview = screen.getByTestId('brand-preview')
    expect(preview).toHaveAttribute('data-preset', 'emerald')
    expect(preview).toHaveTextContent('Kulkarni Homes')
    fireEvent.click(screen.getByTestId('preset-royal-purple'))
    expect(screen.getByTestId('brand-preview')).toHaveAttribute('data-preset', 'royal-purple')
    expect(screen.getByTestId('preset-royal-purple')).toHaveAttribute('aria-checked', 'true')
  })

  it('preview follows the typed business name and tagline', async () => {
    setup()
    await screen.findByTestId('brand-editor')
    fireEvent.change(screen.getByLabelText('Business name'), { target: { value: 'Joshi & Associates' } })
    fireEvent.change(screen.getByLabelText('Tagline'), { target: { value: 'Kothrud since 2011' } })
    expect(screen.getByTestId('brand-preview')).toHaveTextContent('Joshi & Associates')
    expect(screen.getByTestId('brand-preview')).toHaveTextContent('Kothrud since 2011')
  })

  it('uploads a banner through the injected uploader and previews it', async () => {
    const { upload } = setup()
    await screen.findByTestId('brand-editor')
    const file = new File(['x'], 'b.jpg', { type: 'image/jpeg' })
    fireEvent.change(screen.getByTestId('brand-banner'), { target: { files: [file] } })
    await waitFor(() => expect(upload).toHaveBeenCalledWith(file, 'a1'))
    await waitFor(() => expect(screen.getByAltText('Banner photo preview')).toBeInTheDocument())
    expect(screen.getByText(/1600 x 600/)).toBeInTheDocument()
  })

  it('refuses a custom colour that is too light and blocks saving', async () => {
    const { save } = setup()
    await screen.findByTestId('brand-editor')
    fireEvent.click(screen.getByLabelText(/use my own main colour/i))
    fireEvent.change(screen.getByLabelText('Colour code'), { target: { value: '#ffff00' } })
    expect(screen.getByRole('alert')).toHaveTextContent(/too light/i)
    expect(screen.getByRole('button', { name: /save my brand/i })).toBeDisabled()
    fireEvent.change(screen.getByLabelText('Colour code'), { target: { value: '#1a2b5c' } })
    expect(screen.queryByRole('alert')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: /save my brand/i }))
    await waitFor(() => expect(save).toHaveBeenCalled())
    expect(save.mock.calls[0][0].custom_primary).toBe('#1a2b5c')
  })

  it('saves the full brand patch with areas capped at six, and shows server errors', async () => {
    const { save } = setup()
    await screen.findByTestId('brand-editor')
    for (const a of ['Baner', 'Aundh', 'Kothrud', 'Wakad', 'Hinjewadi', 'Kharadi', 'Wagholi']) fireEvent.click(screen.getByRole('button', { name: a }))
    fireEvent.change(screen.getByLabelText(/MahaRERA agent registration number/i), { target: { value: 'a52100012345' } })
    fireEvent.change(screen.getByLabelText(/Years in property/i), { target: { value: '9' } })
    save.mockRejectedValueOnce(new Error('Please do not put phone numbers in tagline'))
    fireEvent.click(screen.getByRole('button', { name: /save my brand/i }))
    expect(await screen.findByText(/phone numbers/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /save my brand/i }))
    await screen.findByRole('status')
    const patch = save.mock.calls[1][0]
    expect(patch.areas).toEqual(['Baner', 'Aundh', 'Kothrud', 'Wakad', 'Hinjewadi', 'Kharadi'])
    expect(patch.rera_agent_no).toBe('A52100012345')
    expect(patch.years_experience).toBe(9)
    expect(save.mock.calls[1][1]).toBe('a1')
  })
})
