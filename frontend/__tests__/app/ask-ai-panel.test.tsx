import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import { AskAiPanel } from '@/components/app/AskAiPanel'
import { createApiClient } from '@/lib/app/api'
import type { AskAiAnswer, AskAiPrompt, Listing } from '@/lib/app/types'

const mockFetch = jest.fn()
jest.mock('@/lib/app/client', () => {
  const { createApiClient: make } = jest.requireActual('@/lib/app/api')
  return {
    api: make({ baseUrl: '', getToken: () => 'tok', fetchImpl: (...a: unknown[]) => mockFetch(...a) }),
    errorMessage: (e: Error) => e.message,
    isFixtureMode: () => false,
  }
})

const PROMPTS: AskAiPrompt[] = [
  { id: 'plan', title: 'Marketing plan', use: 'Who buys, 5 pictures, captions and a reel.', best: 'ChatGPT', best_note: 'thinking on',
    paste: 'the whole answer, with its headings', after: 'The pictures become your picture plan.', text: 'PLAN PROMPT' },
  { id: 'facts', title: 'Find project facts', use: 'One fact per line with its source.', best: 'Gemini', best_note: 'web search on',
    paste: 'the whole list of facts', after: 'Only numbers we can find can be kept.', text: 'FACTS PROMPT' },
  { id: 'faq', title: 'Buyer questions', use: 'Six questions before a site visit.', best: 'ChatGPT', best_note: '',
    paste: 'the whole list of questions and answers', after: 'Copy the answers you like.', text: 'FAQ PROMPT' },
]

const EMPTY: AskAiAnswer = { lines: [], headline: null, captions: [], pictures: [], reel: [], missing: [] }
const PLAN_ANSWER: AskAiAnswer = {
  ...EMPTY,
  pictures: [{ type: 'building render', shows: 'The tower from the road', where: "builder's website gallery",
    text: 'Kumar Pinnacle, Kharadi', why: 'stops the scroll', status: 'checked', missing: [] }],
  captions: [{ text: 'A 3 BHK in Kharadi for ₹85 lakh.', status: 'checked', missing: [] }],
}
const FACTS_ANSWER: AskAiAnswer = {
  ...EMPTY,
  lines: [{ text: '4 towers of 148 homes', source: 'builder site', status: 'words', missing: [], keep: '4 towers of 148 homes' }],
}

const listing: Listing = {
  id: 'L1', agent_id: 'a1', status: 'live', visibility: 'public', transaction: 'sale', property_type: 'apartment',
  title: '3 BHK flat in Kharadi', description: { en: 'East facing, 1,050 sq ft carpet' }, price_inr: 8500000,
  city: 'Pune', locality: 'Kharadi', amenities: [], media: [], picture_plan: null,
  created_at: '2026-10-01T00:00:00Z', updated_at: '2026-10-01T00:00:00Z',
}

function ok(body: unknown) {
  return { ok: true, status: 200, text: async () => JSON.stringify(body) }
}

let prompts = PROMPTS
let checked: AskAiAnswer = PLAN_ANSWER

beforeEach(() => {
  prompts = PROMPTS
  checked = PLAN_ANSWER
  mockFetch.mockReset()
  mockFetch.mockImplementation((url: string) => {
    if (String(url).includes('ask-ai/check')) return Promise.resolve(ok(checked))
    if (String(url).includes('ask-ai')) return Promise.resolve(ok({ prompts }))
    return Promise.resolve(ok(listing))
  })
})

const renderPanel = () => render(<AskAiPanel listing={listing} onSaved={() => undefined} />)

it('opens one step at a time, starting with the first', async () => {
  renderPanel()
  expect(await screen.findByText('Marketing plan')).toBeInTheDocument()
  expect(screen.getByText('Buyer questions')).toBeInTheDocument()
  expect(screen.getAllByRole('button', { name: /^Open in/ })).toHaveLength(1) // only the open step offers its AI
  expect(screen.queryByLabelText('The answer to Buyer questions')).toBeNull()
})

it('keeps each step’s own paste box and answer', async () => {
  renderPanel()
  fireEvent.change(await screen.findByLabelText('The answer to Marketing plan'), { target: { value: 'HEADLINE: A 3 BHK in Kharadi' } })
  fireEvent.click(screen.getByRole('button', { name: 'Check the answer' }))
  await screen.findByText('Pictures, in order')

  fireEvent.click(screen.getByRole('button', { name: /^Find project facts/ }))
  expect(screen.queryByLabelText('The answer to Marketing plan')).toBeNull()
  expect(screen.getByText('Only numbers we can find can be kept.')).toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: /^Marketing plan/ }))
  expect(screen.getByLabelText('The answer to Marketing plan')).toHaveValue('HEADLINE: A 3 BHK in Kharadi')
  expect(screen.getByText('Pictures, in order')).toBeInTheDocument()
})

it('saves the picture plan, then walks to the next step for the facts to keep', async () => {
  renderPanel()
  fireEvent.change(await screen.findByLabelText('The answer to Marketing plan'), { target: { value: 'PICTURES:' } })
  fireEvent.click(screen.getByRole('button', { name: 'Check the answer' }))
  fireEvent.click(await screen.findByRole('button', { name: 'Use this picture plan' }))
  await waitFor(() => expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/listings/L1'),
    expect.objectContaining({ method: 'PATCH' })))
  expect(await screen.findByText(/Picture plan saved/)).toBeInTheDocument()

  checked = FACTS_ANSWER
  fireEvent.click(await screen.findByRole('button', { name: 'Next step: Find project facts' }))
  fireEvent.change(await screen.findByLabelText('The answer to Find project facts'), { target: { value: '- 4 towers of 148 homes' } })
  fireEvent.click(screen.getByRole('button', { name: 'Check the answer' }))
  fireEvent.click(await screen.findByRole('checkbox', { name: 'Keep: 4 towers of 148 homes' }))
  fireEvent.click(await screen.findByRole('button', { name: 'Add 1 to highlights' }))
  expect(await screen.findByText(/Added 1 to the listing/)).toBeInTheDocument()
})

it('puts the research step first, and says why, when we hold few facts', async () => {
  prompts = [{ ...PROMPTS[1], hint: 'We hold few facts on this property, so do this step first.' }, PROMPTS[0], PROMPTS[2]]
  checked = FACTS_ANSWER
  renderPanel()
  expect(await screen.findByText('We hold few facts on this property, so do this step first.')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /^Open in Gemini/ })).toBeInTheDocument()
})

it('says so when the pasted answer holds nothing to read', async () => {
  checked = EMPTY
  renderPanel()
  fireEvent.change(await screen.findByLabelText('The answer to Marketing plan'), { target: { value: 'sure! here you go' } })
  fireEvent.click(screen.getByRole('button', { name: 'Check the answer' }))
  expect(await screen.findByText(/Nothing to read in this answer/)).toBeInTheDocument()
})
