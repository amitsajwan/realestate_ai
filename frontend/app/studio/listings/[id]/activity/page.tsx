'use client'
import { useParams } from 'next/navigation'
import React from 'react'
import { ListingActivityView } from '@/components/app/ListingActivityView'

export default function ListingActivityPage() {
  const { id } = useParams<{ id: string }>()
  return <ListingActivityView id={id} />
}
