import type { Metadata } from 'next'
import { JoinFlow } from '@/components/app/JoinFlow'
import { BRAND_NAME } from '@/lib/brand'

export const metadata: Metadata = { title: `Join - ${BRAND_NAME}` }

export default function JoinPage() {
  return <JoinFlow />
}
