import React from 'react'
import { act, render, screen } from '@testing-library/react'
import { useAsync } from '@/lib/app/useAsync'

/** A loader whose answers the test hands out by hand, in any order. */
function deferred() {
  const waiting: Record<string, (v: string) => void> = {}
  const load = (key: string) => new Promise<string>((resolve) => { waiting[key] = resolve })
  return { load, answer: (key: string, v: string) => waiting[key](v) }
}

function Shows({ who, load }: { who: string; load: (k: string) => Promise<string> }) {
  const { data } = useAsync(() => load(who), [who])
  return <p>{data ?? 'loading'}</p>
}

it('an earlier answer that arrives late does not replace the answer for what was asked last', async () => {
  const d = deferred()
  const { rerender } = render(<Shows who="mine" load={d.load} />)
  rerender(<Shows who="agent" load={d.load} />)   // the owner picked an agent before their own list came back
  await act(async () => { d.answer('agent', 'Rahul flat') })
  await act(async () => { d.answer('mine', 'My flat') })
  expect(screen.getByText('Rahul flat')).toBeInTheDocument()
  expect(screen.queryByText('My flat')).toBeNull()
})
