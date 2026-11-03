'use client'
import { useParams } from 'next/navigation'
import React from 'react'
import { AgentDetailScreen } from '@/components/app/agents/AgentDetailScreen'

export default function AgentDetailPage() {
  const { id } = useParams<{ id: string }>()
  return <AgentDetailScreen id={id} />
}
