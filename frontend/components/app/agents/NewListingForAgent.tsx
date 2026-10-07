'use client'
import React from 'react'
import { conciergeApi } from '@/lib/app/concierge'
import { useAsync } from '@/lib/app/useAsync'
import { ErrorBox, Spinner } from '../ui'
import { NewListingFlow } from '../NewListingFlow'

/** The normal new-listing flow, but every call goes to this agent. Loads his name first. */
export function NewListingForAgent({ id }: { id: string }) {
  const { data, error, reload } = useAsync(() => conciergeApi.get(id), [id])
  if (error && !data) return <ErrorBox message={error} onRetry={reload} />
  if (!data) return <Spinner />
  return <NewListingFlow onBehalfOf={{ id: data.id, name: data.name }} />
}
