# Avasetu brand guide

## Name and meaning

**Avasetu** (Devanagari: **आवासेतु**) joins *āvās* (home) and *setu* (bridge). We are the bridge between a person and the right home,
and between buyers and trusted local agents. The name replaces "PUNE Property", which tied us to one city. Pune is still our
first city, so copy about places stays: "homes in Pune", "Kharadi, Upper Kharadi, Wagholi".

Write it as **Avasetu**: capital A, then lower case. Never "AvaSetu", "AVASETU" in running text, "Ava Setu" or "Awasetu".
All capitals is fine only in small kicker labels (for example "NEWS · AVASETU").

## Tagline

| Language | Tagline |
|---|---|
| English | **Your bridge to the right home** |
| Hindi | **सही घर तक आपका सेतु** |
| Marathi | **योग्य घरापर्यंत तुमचा सेतू** |

The sign-off on posts is **Avasetu team**. Our hashtag is **#Avasetu**. Keep the topic and area hashtags next to it
(#PuneRealEstate, #Kharadi, #Wagholi and so on).

## Colours

| Role | Hex | Use |
|---|---|---|
| Navy | `#102340` | backgrounds, headings, the roof and bridge in the gold mark |
| Gold | `#F0B13B` | the mark's disc, buttons, highlights, one emphasised phrase |
| White | `#FFFFFF` | text on navy |
| Cream | `#FBF6EA` | light page backgrounds |

Keep gold for one thing per screen or card: the mark, the main button or one highlighted phrase. Text on gold is navy.

## Fonts

- Wordmark and big headings on brand images: **Baloo 2** (ExtraBold), as in the share image and cover.
- Taglines, Hindi and Marathi: **Hind** (SemiBold). It renders Devanagari well.
- Generated cards and the website use **Poppins**, which is already bundled in `backend/app/modules/marketing/fonts`.

## Logo

Files are in this folder; the web copies are in `frontend/public/brand/` and the card renderer copies are in
`backend/app/modules/marketing/assets/`.

| File | What it is | Use it for |
|---|---|---|
| `mark.svg` / `avasetu-mark.png` | gold disc with a navy roof over a bridge arch | headers, card footers, profile pictures |
| `mark-navy.svg` / `avasetu-mark-navy.png` | navy rounded square with a gold mark | app icons, favicon, light backgrounds where the disc looks weak |
| `lockup.png` | mark, wordmark and tagline on navy | slides, documents, the top of an email |
| `profile.png` (1080) | gold mark on navy | Facebook and Instagram profile picture |
| `cover.png` (1640x624) | mark, wordmark, tagline in three languages | Facebook cover |
| `og.png` (1200x630) | the link preview | website share image (`frontend/public/brand/og.jpg`) |
| `icon-32/192/512.png` | navy tile icons | favicon, home-screen icon, manifest |

Do:
- Leave clear space around the mark of at least a quarter of its width.
- Put the gold mark on navy or on white. Put the navy tile on light or busy backgrounds.
- Show the mark at 32 px or larger on screens and 64 px or larger on images.

Don't:
- Stretch, rotate, recolour, outline or add shadows to the mark.
- Put the gold mark on a gold or a busy photo background without a navy scrim.
- Rebuild the wordmark in another font, or put the old "PP" badge next to the new mark.
- Use the brand to look like a builder, bank or government body.

## Voice

Plain, honest, warm. Never hype.

- Say what is true and checkable: price, carpet area, possession, RERA number, the source and date of news.
- Short sentences and everyday words. Hindi and Marathi should sound the way people in Pune actually speak.
- No superlatives ("best", "dream home", "guaranteed"), no price predictions, no pressure ("hurry", "last few units").
- Samples are always labelled "Sample listing". Agents are "listed by <name> on Avasetu", never "verified by Avasetu".
- End posts with a real question or one clear next step.

## Where the brand lives in code

- Backend: `backend/app/core/brand.py` (`NAME`, `TAGLINE`, `TAGLINE_HI`, `TAGLINE_MR`, `TEAM`, `HASHTAG`, `SITE`).
- Frontend: `frontend/lib/brand.ts` (same values; `NEXT_PUBLIC_BUSINESS_NAME` overrides the shown name, default `Avasetu`).
- Public site address: `PUBLIC_SITE_URL` (backend) and `NEXT_PUBLIC_SITE_URL` (frontend, from `SITE_HOST` in `deploy/gcp/.env`).
  On the VM the backend now follows `SITE_HOST` too unless `PUBLIC_SITE_URL` is set in `.env`. Switching to a real domain is
  changing `SITE_HOST` (and `PUBLIC_SITE_URL` if you set it) and redeploying.
- Facebook and Instagram links: `NEXT_PUBLIC_FACEBOOK_URL`, `NEXT_PUBLIC_INSTAGRAM_URL` (the defaults are the current profile URLs).

## Owner's checklist (things only you can change)

On the VM first:
- [ ] In `deploy/gcp/.env`, remove `NEXT_PUBLIC_BUSINESS_NAME=PUNE Property` if it is there (or set it to `Avasetu`), then redeploy.
      The frontend bakes this in at build time. Deploy the backend and frontend together: the agent consent text changed on both.

Facebook Page:
- [ ] Rename the Page to **Avasetu** (Page settings > Page info > Name). Meta may review it for a day or two.
- [ ] Change the username to `@avasetu` (or `@avasetu.in` if it is taken).
- [ ] Profile picture: `profile.png`. Cover photo: `cover.png`.
- [ ] Intro/bio: "Your bridge to the right home. Homes, guides and trusted local agents in Pune."
- [ ] Website link: the site address (later the new domain).
- [ ] Then set `NEXT_PUBLIC_FACEBOOK_URL` in `deploy/gcp/.env` to the new Page URL and redeploy.

Instagram:
- [ ] Change the username from `kharadi_prop` to `avasetu` (or `avasetu.in`), and the name to **Avasetu**.
- [ ] Bio: "Your bridge to the right home · सही घर तक आपका सेतु · Homes, guides and trusted local agents in Pune".
- [ ] Profile picture: `profile.png`. Website link: `<site>/go`.
- [ ] Then set `NEXT_PUBLIC_INSTAGRAM_URL` to the new profile URL and redeploy.

Meta developer app:
- [ ] App display name **Avasetu** and app icon `icon-512.png` (developers.facebook.com > App settings > Basic).
- [ ] If WhatsApp is set up later, request the display name **Avasetu** (see `docs/WHATSAPP_SETUP.md`).

Later:
- [ ] Google Business Profile as **Avasetu** (once there is an address or service area you are happy to show).
- [ ] Buy the domains: **avasetu.com**, **avasetu.in**, and **awasetu.com** (common misspelling, redirect it). Then point
      `SITE_HOST` at the main one and redeploy; footers, captions and links follow automatically.
- [ ] Email from the domain (for example hello@avasetu.in) and set `NEXT_PUBLIC_CONTACT_EMAIL`.

## Rebrand record

`rebrand-check.jpg` in this folder shows the generated cards (marketing, calendar, creative, showcase, news, reel end card) and the
landing, /go, agent page and /news screens at 390x844 after the switch. Posts already published under "PUNE Property" were not changed.
