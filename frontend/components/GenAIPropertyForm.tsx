'use client'

import React from 'react'
import SmartPropertyForm from './SmartPropertyForm'

interface GenAIPropertyFormProps {
  onSuccess?: () => void
}

export default function GenAIPropertyForm({ onSuccess }: GenAIPropertyFormProps) {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <SmartPropertyForm onSuccess={onSuccess} />
    </div>
  )
}