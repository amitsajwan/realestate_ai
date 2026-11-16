import React from 'react'
import { fireEvent, render, screen, act } from '@testing-library/react'
import CheckEmbedBox from '@/components/site/CheckEmbedBox'
import { checkEmbed } from '@/lib/site/checkEmbed'

const parse = (html: string) => { const d = document.createElement('div'); d.innerHTML = html; return d }

test('the embed is a plain form that opens our check, with a followed link and no script or iframe', () => {
  const html = checkEmbed('https://avasetu.in/')
  const d = parse(html)
  const form = d.querySelector('form')!
  expect(form.getAttribute('action')).toBe('https://avasetu.in/check')
  expect(form.getAttribute('method')).toBe('get')
  expect(d.querySelector('input[name="q"]')).not.toBeNull()
  const link = d.querySelector('a')!
  expect(link.getAttribute('href')).toBe('https://avasetu.in/check')
  expect(link.getAttribute('rel')).toBeNull()   // a nofollow would waste the point
  expect(html).not.toMatch(/<script|<iframe/i)
})

test('/check shows the embed as it will look, with its code to copy', async () => {
  const writeText = jest.fn().mockResolvedValue(undefined)
  Object.assign(navigator, { clipboard: { writeText } })
  render(<CheckEmbedBox siteUrl="https://avasetu.in" />)
  expect(screen.getByRole('heading', { name: 'Put this check on your website' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Check' })).toBeInTheDocument()   // the preview
  expect((screen.getByLabelText('Code to paste') as HTMLTextAreaElement).value).toBe(checkEmbed('https://avasetu.in'))
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Copy the code' })) })
  expect(writeText).toHaveBeenCalledWith(checkEmbed('https://avasetu.in'))
  expect(screen.getByRole('button', { name: '✓ Code copied' })).toBeInTheDocument()
})
