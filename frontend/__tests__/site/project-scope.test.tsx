// A project page may stand for several MahaRERA registrations (towers, phases). Its own record is one of them, so the record's
// counts and dates are one part's. On 2026-11-12, 85 of 88 such pages said one wing's homes as the whole project's in their FAQ
// and structured data (Venkatesh Vanaya: 168 of 745). These tests keep that from coming back, whoever writes the next section.
import fs from 'fs'
import path from 'path'
import { render } from '@testing-library/react'
import React from 'react'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import { registerDescription, registerProjectJsonLd, registerTitle } from '@/lib/site/projectSeo'
import { projectFaq } from '@/lib/site/register'
import type { RegisterProject } from '@/lib/site/register'

jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: () => <section id="enquire" /> }))

// the record fields that are one registration's: a page reads them only through lib/site/register's accessors
const ONE_REGISTRATION = ['units_total', 'units_booked', 'completion_now', 'completion_at_registration', 'completion_passed',
  'booked_readings', 'area_compare', 'completion_moves', 'details', 'stage', 'sold_out', 'extension_only']
const ROOT = path.join(__dirname, '..', '..')

function sources(dir: string): string[] {
  return fs.readdirSync(path.join(ROOT, dir), { withFileTypes: true }).flatMap((e) => {
    const rel = path.join(dir, e.name)
    if (e.isDirectory()) return e.name === 'node_modules' || e.name.startsWith('.') ? [] : sources(rel)
    return /\.(ts|tsx)$/.test(e.name) ? [rel] : []
  })
}

describe('the one rule: a project page never reads one registration\'s figures as the project\'s', () => {
  it('no file that handles a project page reads those fields directly (lib/site/register\'s accessors do)', () => {
    const files = ['app', 'components', 'lib'].flatMap(sources)
      .filter((f) => f !== path.join('lib', 'site', 'register.ts'))
      .filter((f) => /\bRegisterProject\b/.test(fs.readFileSync(path.join(ROOT, f), 'utf8')))
    expect(files.length).toBeGreaterThan(3)
    const read = new RegExp(`\\b(?:p|project|page)\\.(${ONE_REGISTRATION.join('|')})\\b`)
    const offenders = files.flatMap((f) => fs.readFileSync(path.join(ROOT, f), 'utf8').split('\n')
      .map((line, i) => (read.test(line) ? `${f}:${i + 1}: ${line.trim()}` : null)).filter(Boolean))
    // use homesOf, possessionOf, possessionLabel, completionPassedOf, soldOutOf, stageOf or areaCompareOf for the project, and
    // mainRegistration(p) for a figure that is one registration's (then say which one on the page)
    expect(offenders).toEqual([])
  })
})

// Venkatesh Vanaya as the backend sends it: the main registration (wings I & J) holds 168 homes, 7 of them booked; the project
// has 745 homes over 7 registrations, 40 booked across the 6 that report them
const MAIN = 'PR1261012601206'
const tower = (regno: string, completion_now: string, units_total: number, units_booked: number) =>
  ({ regno, name: `VENKATESH VANAYA ${regno}`, completion_now, completion_at_registration: completion_now, units_total, units_booked, registered_on: null, maharera_url: null })
const VANAYA: RegisterProject = {
  slug: 'venkatesh-vanaya-wing-i-j-phase-2-kharadi', name: 'VENKATESH VANAYA-WING- I & J-PHASE -2', marketed_name: 'Venkatesh Vanaya',
  regno: MAIN, promoter: 'SVBPL HOMES PVT LTD', pincode: '411014', area: { key: 'kharadi', slug: 'kharadi', name: 'Kharadi' },
  completion_now: '2031-04-30', completion_at_registration: '2031-04-30', units_total: 168, units_booked: 7, details_read_at: '2026-10-26',
  listed_or_updated: '2026-10-16', maharera_url: null, paragraph: '', indexable: true, same_area: [], source: 'MahaRERA public records',
  stage: 'new', sold_out: false, completion_passed: false,
  details: { towers: 2, max_floors: 25, units_total: 168, units_residential: 168, units_other: 0, booked_pct: 4, registered_on: '2026-01-10', completion_moved_months: 0 },
  booked_readings: [{ on: '2026-07-03', booked: 2 }, { on: '2026-10-26', booked: 7 }],
  area_compare: { place: 'Kharadi', booked: { pct: 4, area_pct: 40, projects: 20 }, moved: null },
  towers: [tower(MAIN, '2031-04-30', 168, 7), tower('PR1261012601751', '2030-08-31', 78, 3), tower('PR1261012601264', '2030-12-31', 144, 10),
    tower('PR1261012601304', '2031-01-31', 249, 20), tower('PR1261012601229', '2031-10-31', 90, 0), tower('PC1261012601213', '2032-04-30', 16, 0),
    tower('PR1261012601239', '2033-01-31', 0, 0)],
  project: { registrations: 7, regnos: [MAIN, 'PR1261012601751', 'PR1261012601264', 'PR1261012601304', 'PR1261012601229', 'PC1261012601213',
    'PR1261012601239'], units_total: 745, units_counted: 6, units_booked: 40, booked_of: 745, booked_counted: 6,
    completion_first: '2030-08-31', completion_last: '2033-01-31', completion_passed: false },
} as RegisterProject

/** Every place in `text` where the main registration's own count is said, with what is said around it. */
function mainCounts(text: string): string[] {
  const out: string[] = []
  const re = /\b168\b/g
  let m: RegExpExecArray | null
  while ((m = re.exec(text))) out.push(text.slice(Math.max(0, m.index - 90), m.index + 90))
  return out
}

describe('a page for a project in several registrations', () => {
  const html = (() => {
    const { container } = render(<RegisterProjectPage p={VANAYA} siteUrl="https://avasetu.in" facts={null} />)
    return container.textContent ?? ''
  })()
  const seo = [registerTitle(VANAYA), registerDescription(VANAYA), JSON.stringify(registerProjectJsonLd({ p: VANAYA, siteUrl: 'https://avasetu.in', faq: projectFaq(VANAYA) }))]

  it('says one registration\'s count only beside that registration\'s name', () => {
    for (const around of mainCounts([html, ...seo].join('\n'))) {
      expect(around).toMatch(new RegExp(`${MAIN}|this registration`))
    }
  })

  it('says the whole project\'s homes, bookings and possession span', () => {
    expect(html).toContain('40 of 745')
    expect(html).toMatch(/31 Aug 2030 to 31 Jan 2033/)
    expect(seo[1]).toContain('40 of 745 homes booked')
    expect(seo[1]).toContain('Possession from Aug 2030')
    expect(seo[0]).toContain('possession from Aug 2030')
    expect(seo[2]).toContain('"numberOfAccommodationUnits":745')
  })

  it('leaves out what is one registration\'s alone: the stage, the area comparison', () => {
    const { queryByTestId } = render(<RegisterProjectPage p={VANAYA} siteUrl="https://avasetu.in" facts={null} />)
    expect(queryByTestId('stage')).toBeNull()
    expect(queryByTestId('area-compare')).toBeNull()
  })

  it('a project registered once still says its record\'s own figures', () => {
    const one = { ...VANAYA, project: null, towers: [] } as RegisterProject
    expect(registerDescription(one)).toContain('7 of 168 homes booked')
    expect(registerTitle(one)).toContain('possession Apr 2031')
  })
})
