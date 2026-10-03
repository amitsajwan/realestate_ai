import React from 'react'
import Link from 'next/link'
import { agentPath } from '@/lib/site/slug'
import type { PublicProject } from '@/lib/site/types'
import ProjectCard from './ProjectCard'

/** The agent's builder projects on his home page, with a link to compare them. Renders nothing without projects. */
export default function ProjectsSection({ agentSlug, projects, anchor = 'projects' }: { agentSlug: string; projects: PublicProject[]; anchor?: string }) {
  if (!projects.length) return null
  return (
    <section id={anchor} aria-labelledby="projects-title" className="scroll-mt-16">
      <span id={anchor === 'projects' ? undefined : 'projects'} className="block" aria-hidden />
      <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 id="projects-title" className="text-2xl font-bold">New projects</h2>
          <p className="text-slate-600">Each one checked on MahaRERA, with the date filed and how many homes are booked.</p>
        </div>
        {projects.length > 1 && (
          <Link href={agentPath(agentSlug, 'projects/compare')} className="inline-flex min-h-[44px] items-center font-semibold text-[var(--site-primary)]">
            Compare side by side &rarr;
          </Link>
        )}
      </div>
      <ul className="grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((p) => <li key={p.slug}><ProjectCard agentSlug={agentSlug} p={p} /></li>)}
      </ul>
    </section>
  )
}
