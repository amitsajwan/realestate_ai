# One project, one page, one address

Status: step 1 **BUILT** 2026-11-27 (not yet deployed); steps 2-3 **TARGET**. Owner 2026-11-27 ("lets get the 1 now, for full project; make sure we dont break SEO, sitemap etc").
Step 1 of the consolidation agreed the same day: one record per project that every page, card, list, sitemap entry and
structured data reads. Step 2 (one price per project) and step 3 (a daily whole-site check) follow.

## Why

The same kind of problem kept coming back, each found by eye and fixed on one page: Lodha Camelot shown at two prices on one
page, two Camelot pages, addresses made of the builder's paperwork name ("kharadi-new-project-tower-5-wagholi"). They have one
cause: MahaRERA registers each tower and phase on its own, we built a page per registration (11,536 pages), and the grouping that
joins them into projects was added later and is partial. Google judges the site as a whole: thin near-duplicate pages under names
nobody searches read as mass-made content and split one project's links and clicks over several pages.

## What already runs (keep it)

- **Groups** (`areastats/clusters.py`, run with the slugs by `pages.assign_all` and `seo.splits`): towers and phases of one
  project share a primary page. A group comes from, in order: a confirmed list (`agent_projects.registrations`, Studio's
  `owner_group`), the web proving two registrations are one project (`samegroup`, `web:` ids), the name rule (promoter + name
  without its tower/phase words + pincode). `cluster_skip` undoes a wrong merge.
- **Redirects**: a member's address and any `old_slugs` serve the primary's page, and the site answers 308 to the primary's
  address (`pages.project_page`, `app/projects/[slug]/page.tsx`). The sitemap lists primaries only.
- **Names** (`pages.shown_name`): search name (`seo.targets`, changes as titles are tuned), else the name sites printing the
  MahaRERA number use (`market_name`), else brand + name, else the group's or the registration's name.

## What is missing

1. **A confirmed group never grows.** Its list is fixed, and the name rule and the web proof both skip its members, so a tower
   registered later stays a page of its own: Camelot's group lists towers 1-4 and 11; tower 5 (PR1260002502039, also "Lodha
   Camelot", same promoter) has its own page and its own price. Measured 2026-11-27: 12 projects (24 indexed pages) where two
   primaries in one place have the same shown name and the same promoter.
2. **Addresses never follow the name.** An address is made once from the registered name. 295 records have a market or search
   name; 54 addresses were ever changed (by the place check). ~1,120 addresses carry a tower or wing, ~1,150 a phase or part
   (most are primaries that stand alone, and stay as they are until a group or a name says otherwise).
3. **A renamed page loses its history.** Search Console counts are matched to a record by its current address only
   (`areastats/searchconsole.refresh`, `seo/targets`), so a rename reads as a page that lost every impression, and the rank loop
   reacts to that.
4. **Two kinds of project page.** `/projects/<slug>` is either a register page or an agent catalog page (`agent_projects`); one
   catalog page is live, `lodha-camelot`. Left as it is in this step (a register page of a listed project redirects to it); folding
   it into the register model is later work.

## Decisions

- **The address name is stable**: the owner's name for the page, else `market_name`, else the group's name, else the registered
  name without tower/phase words. Never `search_name`, which the rank loop changes. An address is changed at most once by code;
  after that only by the owner.
- **Redirect plus canonical, never canonical alone**: the old address answers 308 to the new one, the new page's canonical is
  itself, the sitemap and every internal link name only the new one.
- **Paced**: at most `RENAMES_PER_DAY` (25) addresses a day, pages with the fewest search impressions first, so a mistake shows on
  pages that matter least and Google sees a steady trickle, not a site-wide move. The daily pace lives in one setting.
- **History follows the page**: Search Console counts and phrases for a record are the sum over its address and its `old_slugs`.
- **Nothing is removed**: merging joins pages and keeps every old address working (owner: never prune indexed pages).

## Steps

| # | Step | State |
|---|---|---|
| 1a | Same-name rule (`clusters.same_project`, `identity_key`): two groups (or a group and a single registration) in one place with the same promoter and the same stable name are one project; a confirmed group takes in a registration this way, never loses one; two confirmed groups are never joined; `cluster_skip` stays alone. Dry run on production 2026-11-27: 8 groups change, 13 registrations join (Lodha Camelot towers 5, 6, 9; Rohan Abhilasha D, F, 2-A; Green Hive Plus A2; Venkatesh Skydale 1; Ashtavinayak City 1-2; Shubh Tristar C; Aria; Aditya Vivaaz), no promoter crossed | BUILT |
| 1b | History follows renames: `searchconsole.page_paths` / `summed` (counts, the week's counts, position weighted by impressions) and `seo.targets` (phrases, conflicts) read every address a page has had | BUILT |
| 1c | Addresses from the stable name: `pages.address_name` / `address_slug` (also the place check's, so a rename is never undone); `pages.rename_addresses` in the register step after the groups, `settings.project_renames_per_day` (25; 0 stops), least-seen pages first, once per page by code (`address_from`, `address_at`), never onto an address another page has or had or a catalog page's. Banner picks, site visits and the chat find a page by an old address | BUILT |
| 1d | One redirect, never a chain: a tower's or an old address goes straight to the page an agent lists the project on, else to the project page (`app/projects/[slug]/page.tsx`) | BUILT |
| 2 | One price per project, one resolver every surface reads | TARGET |
| 3 | Daily whole-site check: two pages for one project, a price that differs between pages, a paperwork-name address with a known name, anything over the first screen, an agent called our partner | TARGET |

## What we watch

Search Console, weekly: impressions and clicks of renamed pages (old + new address together) against the four weeks before;
"Page with redirect" in the Pages report rising by the renames and nothing else; no new 404s. Stop the renames
(`RENAMES_PER_DAY=0`) if renamed pages lose more than the site as a whole over two weeks.
