'use client'
import React from 'react'
import type { NewsroomCheck } from '@/lib/app/newsroom'

export function CheckResult({ check }: { check: NewsroomCheck }) {
  if (check.ok) {
    return <p data-testid="check-ok" className="rounded-lg bg-green-50 p-2 text-sm font-semibold text-green-800">Checks passed: facts, numbers and wording match the source.</p>
  }
  return (
    <div data-testid="check-problems" role="alert" className="rounded-lg bg-red-50 p-2 text-sm text-red-800">
      <p className="font-semibold">Needs a fix before it can go out:</p>
      <ul className="mt-1 list-disc space-y-0.5 pl-5">
        {check.problems.length === 0 ? <li>The automatic check did not pass.</li> : check.problems.map((p, i) => <li key={i}>{p}</li>)}
      </ul>
    </div>
  )
}
