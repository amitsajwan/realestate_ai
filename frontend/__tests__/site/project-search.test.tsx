import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'

const mockRegister = jest.fn(async (_q: string) => [] as unknown[])
const mockPlace = jest.fn(async (_q: string) => null as unknown)
jest.mock('@/lib/site/register', () => {
  const actual = jest.requireActual('@/lib/site/register')
  return { ...actual, searchRegister: (q: string) => mockRegister(q), searchPlace: (q: string) => mockPlace(q) }
})

const mockPush = jest.fn()
jest.mock('next/navigation', () => ({ useRouter: () => ({ push: mockPush }) }))

import ProjectSearch from '@/components/site/ProjectSearch'

const KHARADI_2BHK = { path: '/projects/area/kharadi/2-bhk', label: '2 BHK flats in Kharadi', place: 'Kharadi' }
const IVARA = { slug: 'godrej-ivara-pune', name: 'Godrej Ivara', marketed_name: 'Godrej Ivara', regno: 'P52100050000', completion_now: '2029-12-31' }

beforeEach(() => {
  mockRegister.mockReset().mockResolvedValue([])
  mockPlace.mockReset().mockResolvedValue(null)
  mockPush.mockReset()
})

describe('the project search box', () => {
  it('shows the area page a search names above the projects, and Search opens it', async () => {
    mockPlace.mockResolvedValue(KHARADI_2BHK)
    render(<ProjectSearch hero />)
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: '2 bhk kharadi' } })
    const row = await screen.findByTestId('search-place')
    expect(row).toHaveAttribute('href', '/projects/area/kharadi/2-bhk')
    expect(row).toHaveTextContent('2 BHK flats in Kharadi')
    fireEvent.submit(screen.getByRole('search'))
    expect(mockPush).toHaveBeenCalledWith('/projects/area/kharadi/2-bhk')
  })

  it('opens the one project a search finds', async () => {
    mockRegister.mockResolvedValue([IVARA])
    render(<ProjectSearch hero />)
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'ivara' } })
    await screen.findByRole('link', { name: /Godrej Ivara/ })
    fireEvent.submit(screen.getByRole('search'))
    expect(mockPush).toHaveBeenCalledWith('/projects/godrej-ivara-pune')
  })

  it('lets several results go on to the full results page, as the form does without JavaScript', async () => {
    mockRegister.mockResolvedValue([IVARA, { ...IVARA, slug: 'bhide-nivara', name: 'Bhide Nivara', marketed_name: 'Bhide Nivara', regno: 'P1' }])
    render(<ProjectSearch hero />)
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'ivara' } })
    await waitFor(() => expect(screen.getAllByRole('link')).toHaveLength(2))
    const ev = new Event('submit', { bubbles: true, cancelable: true })
    screen.getByRole('search').dispatchEvent(ev)
    expect(ev.defaultPrevented).toBe(false)
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('shows the area row from the server render of /projects?q=', () => {
    render(<ProjectSearch initialQ="kharadi" initialPlace={{ path: '/projects/area/kharadi', label: 'New projects in Kharadi', place: 'Kharadi' }} />)
    expect(screen.getByTestId('search-place')).toHaveAttribute('href', '/projects/area/kharadi')
    expect(mockPlace).not.toHaveBeenCalled()
  })
})
