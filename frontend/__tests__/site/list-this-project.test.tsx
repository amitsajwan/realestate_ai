import React from 'react'
import { render, screen } from '@testing-library/react'
import ListThisProject from '@/components/site/ListThisProject'

const mockToken = jest.fn()
jest.mock('@shared/session', () => ({ getToken: () => mockToken() }))

describe('List this project', () => {
  it('is for a signed-in agent, and is a plain link into Studio', async () => {
    mockToken.mockReturnValue('tok')
    render(<ListThisProject regno="P52100000001" />)
    const a = await screen.findByTestId('list-this-project')
    expect(a).toHaveAttribute('href', '/studio/listings/new?project=P52100000001')
  })

  it('never shows to a buyer', () => {
    mockToken.mockReturnValue(null)
    render(<ListThisProject regno="P52100000001" />)
    expect(screen.queryByTestId('list-this-project')).not.toBeInTheDocument()
  })
})
