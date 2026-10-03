import React from 'react'
import ProjectCard from '@/components/site/ProjectCard'
import { HOME } from '@/lib/marketing/strings'
import { AVASETU_SITE_VARS } from '@/lib/marketing/siteTheme'
import type { CatalogProject } from '@/lib/site/types'
import SectionHead from './SectionHead'
import { wrap } from './shared'

/** Builder projects on Avasetu's shared pages. Renders nothing when there are none. */
export default function HomeProjects({ items }: { items: CatalogProject[] }) {
  if (!items.length) return null
  return (
    <section id="projects" aria-labelledby="home-projects-title" className="scroll-mt-16 bg-slate-50 py-12 sm:py-16">
      <div className={wrap}>
        <SectionHead id="home-projects-title" title={HOME.projects.heading} lead={HOME.projects.lead} more={{ href: '/projects', label: HOME.projects.all }} />
        <ul style={AVASETU_SITE_VARS} className="mt-6 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((p) => <li key={p.slug}><ProjectCard p={p} href={`/projects/${p.slug}`} /></li>)}
        </ul>
      </div>
    </section>
  )
}
