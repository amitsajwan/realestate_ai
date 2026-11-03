'use client'
import React from 'react'
import { formatPrice } from '@/lib/app/format'
import { sourceLabel } from '@/lib/app/leads'
import { lostHint, resultsEmpty } from '@/lib/app/outcomes'
import { t } from '@shared/strings'
import type { TodayResults } from '@/lib/app/types'

/** "This month": deals won and their value, best channel and why deals were lost. Hidden until there is something to show. */
export function ResultsCard({ results }: { results?: TodayResults }) {
  if (resultsEmpty(results) || !results) return null
  const hint = lostHint(results)
  return (
    <section aria-label={t('thisMonth')} className="space-y-3 rounded-2xl border border-green-200 bg-green-50 p-4" data-testid="results-card">
      <h2 className="font-bold text-gray-900">{t('thisMonth')}</h2>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-3xl font-bold text-gray-900" data-testid="deals-won">{results.deals_won}</p>
          <p className="text-sm text-gray-700">{t('dealsWon')}</p>
        </div>
        <div>
          <p className="text-3xl font-bold text-gray-900" data-testid="deal-value">{results.deal_value_inr > 0 ? formatPrice(results.deal_value_inr) : '-'}</p>
          <p className="text-sm text-gray-700">{t('dealValue')}</p>
        </div>
      </div>
      {results.top_source && (
        <p className="text-sm font-semibold text-gray-800">
          {t('bestChannel')}: {sourceLabel(results.top_source)}
        </p>
      )}
      {hint && <p className="text-sm text-gray-700" data-testid="lost-hint">{hint}</p>}
    </section>
  )
}
