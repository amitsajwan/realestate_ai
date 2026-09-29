import type { Metadata } from 'next'
import { JoinFlow } from '@/components/app/JoinFlow'

export const metadata: Metadata = { title: 'Join - PropertyAI' }

export default function JoinPage() {
  return <JoinFlow />
}
