/**
 * Neighbourhood research (backend app/modules/neighbourhood, docs/plan/pune-intelligence.md): what is around a place and a
 * project, measured from data and refreshed by itself. Every block carries its sources and the day it was measured; a block
 * the backend has too little for is simply absent, so a page shows only what it has.
 * GET /api/v1/public/research/places/{place}    a place's research (place page, /schools, /commute, /rent)
 * GET /api/v1/public/research/projects/{slug}   "Around this project" on a project page
 * GET /api/v1/public/research/hubs              the work hubs with pages
 * GET /api/v1/public/research/hubs/{slug}       one work hub page (/work-hubs/<slug>)
 * These types are the contract with backend/app/modules/neighbourhood/views.py and each researcher's `present`: change both.
 */

export interface Source {
  name: string
  url?: string
  read_on: string // YYYY-MM-DD
}

/** Every block has these on top of its own fields. */
interface BlockBase {
  sources: Source[]
  updated: string // YYYY-MM-DD, when this block was measured
  page_ready?: boolean // enough here for a page of its own (/schools, /commute, /rent) to be indexed
}

/** Drive times from the place (or the project's pin) to a work hub, with typical traffic, in minutes. */
export interface CommuteRow {
  hub: string
  hub_slug?: string // when the hub has a page (/work-hubs/<slug>)
  km: number // road distance
  am: [number, number] // weekday 9 am, low-high minutes
  pm: [number, number] // weekday 6 pm, back
  pin_km?: number // on a project page with a pin: straight-line km from the project's own pin to this hub
}
export interface CommuteBlock extends BlockBase {
  rows: CommuteRow[]
  measured_from?: 'place' | 'pin' // drive times are measured from the place centre ("place"), never scaled to a pin
  place_name?: string
  from?: string // "the Kharadi centre"
}

export type Board = 'CBSE' | 'ICSE' | 'ISC' | 'State' | 'IB' | 'IGCSE'
export interface School {
  name: string
  board: Board
  affiliation?: string // the board's affiliation number
  level?: string // "Up to Class 10", "Up to Class 12"
  km: number // straight line from the place centre or the project's pin
  address?: string
  website?: string
}
export interface SchoolsBlock extends BlockBase {
  schools: School[]
  total_within_km: { km: number; count: number; by_board: Partial<Record<Board, number>> }
}

/** Asked rent from listings (never what was paid), by flat size, for one month. */
export interface RentRow {
  bhk: string // "1 BHK", "2 BHK", "3 BHK"
  low: number // rupees a month, 25th percentile
  median: number
  high: number // 75th percentile
  listings: number
  yield_pct?: number // a year's median rent over the median asking price for that size, when both are known
}
export interface RentBlock extends BlockBase {
  month: string // YYYY-MM
  rows: RentRow[]
  within_km?: number // on a project page: listings this close to the project
}

/** Who lives and works around here, from facts we hold (never religion, caste or community). */
export interface ProfileBlock extends BlockBase {
  home_mix: Array<{ label: string; share: number }> // share of homes being built by size, 0-1
  finished_by_year: Array<{ year: number; homes: number }> // homes MahaRERA shows finished each year
  nearby: Array<{
    kind: 'it_park' | 'office' | 'college' | 'hospital' | 'government' | 'defence' | 'industrial' | 'market' | 'transport'
    name: string
    km: number
  }>
  lines: string[] // plain sentences built from the numbers above, e.g. "Most homes being built here are 2 BHK."
  measured_from?: 'place' | 'pin' // nearby km from the place centre or the project's pin
}

export interface BeingBuiltBlock extends BlockBase {
  within_km: number
  projects: number
  homes: number
  due_from: number // year
  due_to: number
  biggest: Array<{ slug: string; name: string; homes: number; due: string }> // due "YYYY-MM"
  measured_from?: 'place' | 'pin' // "place": filed under the place plus pinned ones within_km of its centre; "pin": pinned ones within_km of the project
  note?: string // says which of the two, in words
}

export interface JobsBlock extends BlockBase {
  hubs: Array<{ hub: string; hub_slug?: string; km: number; companies: string[]; companies_count?: number }>
}

/** A tracker (/news/track/<slug>) that touches the place: roads, metro, rules being built or changing. */
export interface ChangeLine {
  slug: string
  name: string
  status: string
  date: string // YYYY-MM-DD of the status
  stage?: string
}

export interface ResearchBlocks {
  commute?: CommuteBlock
  schools?: SchoolsBlock
  rent?: RentBlock
  profile?: ProfileBlock
  being_built?: BeingBuiltBlock
  jobs?: JobsBlock
}

export interface PlaceResearch {
  place: string
  place_name?: string
  blocks: ResearchBlocks
  changes: ChangeLine[]
  pages: { schools: boolean; commute: boolean; rent: boolean } // which sub-pages are worth indexing
}

export interface ProjectResearch {
  slug: string
  place: string
  place_name?: string
  pinned: boolean // measured from the project's own Google pin, else from the place centre
  blocks: ResearchBlocks
  changes: ChangeLine[]
}

export interface HubCard {
  slug: string
  name: string
  place: string
  kind: 'it_park' | 'business_district' | 'airport' | 'station' | 'industrial'
  ready?: boolean // its page is worth indexing: 3+ companies from its own list, or drive times from 3+ places
  updated?: string // YYYY-MM-DD of its last research, "" before the first
}

export interface HubPage extends HubCard {
  summary: string
  companies: string[]
  companies_source?: Source
  commute_from: Array<{ place: string; name: string; am: [number, number]; pm: [number, number] }>
  homes_nearby: Array<{ slug: string; name: string; km: number; price_from?: number; possession?: string }>
  rent_nearby?: RentRow[]
  changes: ChangeLine[]
  sources: Source[]
  updated: string
  page_ready?: boolean // the same rule as HubCard.ready
}

/** GET /api/v1/public/research/pages: the place sub-pages worth indexing, for the sitemap. */
export interface ResearchPages {
  pages: Array<{ place: string; kind: 'schools' | 'commute' | 'rent'; updated: string }>
}
