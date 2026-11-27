/** SEO → Answers: this week's buyer questions with the page's own answer, a draft to copy and where to find a thread. */
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import AnswersTab from '@/app/studio/seo/AnswersTab'
import { insightsFixture } from '@/lib/app/fixtures-owner'
import type { Answers } from '@/lib/app/insights'

const mockAnswers = jest.fn()
jest.mock('@/lib/app/insights', () => ({ getAnswers: (...a: unknown[]) => mockAnswers(...a) }))

beforeEach(() => mockAnswers.mockReset())

it('shows each question with its draft, the page and the Reddit and Quora searches', async () => {
  const d = insightsFixture('answers') as Answers
  mockAnswers.mockResolvedValue(d)
  render(<AnswersTab />)
  expect(await screen.findByText('When is Godrej Ivara possession?')).toBeInTheDocument()
  expect(screen.getByText('Answers to post, week 47')).toBeInTheDocument()
  expect((screen.getByLabelText(/Draft answer/) as HTMLTextAreaElement).value).toContain('/projects/godrej-ivara-pune?src=answer')
  expect(screen.getByText('Find on r/pune').closest('a')).toHaveAttribute('href', d.items[0].find.reddit)
  expect(screen.getByText('Find on Quora').closest('a')).toHaveAttribute('href', d.items[0].find.quora)
})

it('says where the questions come from when there are none yet', async () => {
  mockAnswers.mockResolvedValue({ week: 47, items: [] })
  render(<AnswersTab />)
  expect(await screen.findByText(/No questions with an answer yet/)).toBeInTheDocument()
})
