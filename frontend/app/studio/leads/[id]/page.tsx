'use client'
import { useParams } from 'next/navigation'
import React from 'react'
import { LeadDetailView } from '@/components/app/LeadDetailView'

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>()
  return <LeadDetailView id={id} />
}
