'use client'
import { useParams } from 'next/navigation'
import React from 'react'
import { NewListingForAgent } from '@/components/app/agents/NewListingForAgent'

export default function NewListingForAgentPage() {
  const { id } = useParams<{ id: string }>()
  return <NewListingForAgent id={id} />
}
