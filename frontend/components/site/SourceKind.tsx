import React from 'react'

interface Source { site: string; url?: string | null }

/**
 * Where a fact was read, said by kind: "the builder's site" (linked, it is the official word) and "2 property sites". Other
 * sites are never named (owner 2026-10-30: housiey.com and builder domains on an agent's page sent buyers elsewhere); the
 * record of which sites keeps the names. `official`: the first source is the builder's own site; without it, a source with a
 * link is.
 */
export default function SourceKind({ sources, official }: { sources: Source[]; official?: boolean }) {
  const builder = official ? sources[0] : sources.find((s) => s.url)
  const others = sources.filter((s) => s !== builder).length
  const sites = others === 1 ? 'a property site' : `${others} property sites`
  if (!builder) return <>{sites}</>
  const link = builder.url
    ? <a href={builder.url} target="_blank" rel="noopener nofollow" className="underline underline-offset-2">the builder&apos;s site</a>
    : <>the builder&apos;s site</>
  return <>{link}{others ? <> and {sites}</> : null}</>
}
