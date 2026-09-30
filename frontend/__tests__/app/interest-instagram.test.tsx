import { render, screen } from '@testing-library/react'
import React from 'react'
import InterestPage from '@/app/studio/interest/page'
import type { FacebookInterest } from '@/lib/app/types'

const row = (over: Partial<FacebookInterest>): FacebookInterest => ({
  id: 'c', post_id: 'p', listing_id: null, from_name: 'Priya', text: 'INTERESTED', intent: 'interested', language: 'en', status: 'replied',
  reply: 'Thanks!', needs_human: false, reason: '', created_time: null, permalink: 'https://example.test/x', ...over,
})
const getFacebookInterest = jest.fn()
jest.mock('@/lib/app/client', () => ({
  api: {
    getFacebookInterest: () => getFacebookInterest(),
    getChatConversations: async () => [],
    getFacebookStatus: async () => ({ ok: true, reconnect: false, checked_at: null }),
  },
  errorMessage: (e: Error) => e.message,
  isFixtureMode: () => false,
}))

describe('interest page channels', () => {
  it('labels Instagram comments and leaves Facebook and older rows unlabeled', async () => {
    getFacebookInterest.mockResolvedValue([
      row({ id: '1', from_name: 'Insta Person', channel: 'instagram' }),
      row({ id: '2', from_name: 'Fb Person', channel: 'facebook' }),
      row({ id: '3', from_name: 'Old Row' }),
    ])
    render(<InterestPage />)
    expect(await screen.findByText('Insta Person')).toBeInTheDocument()
    expect(screen.getAllByText('Instagram')).toHaveLength(1)
    expect(screen.getByText('Open on Instagram')).toBeInTheDocument()
    expect(screen.getAllByText('Open on Facebook')).toHaveLength(2)
  })
})
