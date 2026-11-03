import { redirect } from 'next/navigation'

/** Interest was split on 2026-10-17: numbers went to Results, comments to the Inbox. Old links and bookmarks land on Results. */
export default function InterestPage() {
  redirect('/studio/results')
}
