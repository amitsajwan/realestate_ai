# Meta setup for the PUNE Property Page (do this yourself; ~30 minutes)

Why you and not me: these steps need your Facebook login, 2-step verification and your acceptance of Meta's terms. Do not share your
password with anyone, including an AI assistant. The app never needs it: it needs a **Page access token** that you create and put in
`backend/.env`. If a password was ever shared or pasted anywhere, change it now and turn on 2-step verification.

Publishing to your own brand Page and its linked Instagram works **without Meta App Review** while the Meta app is in Development mode and
you (the token owner) are an admin of both the Page and the app. Agents' own Pages need App Review and Business Verification later.

## A. Clean up the Page (5 min)
1. Replace the cover with `docs/brand/pune-property-cover.png` (1640x624; the text sits in the centre so it survives the phone crop) and the profile picture with `docs/brand/pune-property-profile.png` (shown as a circle).
   The current cover shows post thumbnails with view counts (8.3K, 6.1K...) and a fake Follow button on a Page with 0 followers. That looks
   fabricated and can hurt trust and reach. Use a plain banner instead.
2. Page > Edit: set the category (Real Estate), add a real contact number and email, and a website link (your future domain, or the agent
   site link for now). A bare Page is treated as low quality.

## B. Instagram Business account linked to the Page (5 min)
1. In the Instagram app: Settings > Account type and tools > switch to a **Professional (Business)** account.
2. On Facebook: Page > Settings > Linked accounts > Instagram > connect. (Publishing through the API needs this link.)

## C. Meta developer app (10 min)
1. https://developers.facebook.com > My Apps > Create App > use case **Other** > type **Business**. Name: "PropertyAI".
2. Add the product **Instagram** (choose "Instagram API with Facebook Login") and **Facebook Login for Business**. Meta's menus change, so if a name differs
   pick the option that says it publishes to a Page or an Instagram professional account. Keep the app in **Development** mode: you do NOT need to go Live
   to post to your own Page and Instagram.
3. App roles: your own Facebook profile must be an **Admin** of the app (it is if you created it).
4. Settings > Basic, enter (live pilot address; replace with your domain when you have one):

| Meta field | Value |
|---|---|
| App domains | `34-180-39-243.sslip.io` |
| Privacy Policy URL | `https://34-180-39-243.sslip.io/privacy` (page is being added) |
| Terms of Service URL | `https://34-180-39-243.sslip.io/terms` (page is being added) |
| User data deletion | Instructions URL `https://34-180-39-243.sslip.io/data-deletion` (page is being added; only required to go Live) |
| Site URL (Add platform > Website) | `https://34-180-39-243.sslip.io` |
| Category | Business and pages, or Real estate |
| App icon (1024x1024) | `docs/brand/pune-property-profile.png` |
| Contact email | a real address you read (Meta emails policy notices here) |

A future custom domain means changing these once. Meta is stricter with free hostnames like sslip.io for App Review later, so buy the domain before applying for review.

Permissions you will request in Graph API Explorer (Development mode, no review needed for your own accounts):
`pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`, plus `business_management` only if asked.

Instagram picture rules our cards already follow: JPEG only, plain-ASCII web addresses, carousel pictures are cropped to the first picture's shape
(all our cards are square), at most 100 API posts per 24 hours.

## D. Get the IDs and a long-lived Page token (10 min)
Use Graph API Explorer (developers.facebook.com/tools/explorer) with YOUR app selected:
1. Get User Token with permissions: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`, `business_management` (if asked).
2. Exchange for a long-lived user token, then request `GET /me/accounts`: the response lists your Page with its **id** and a **Page access token**
   (a Page token derived from a long-lived user token does not expire while you stay admin and do not change your password).
3. `GET /{page-id}?fields=instagram_business_account` gives the **Instagram Business ID**.
4. Check the token at developers.facebook.com/tools/debug/accesstoken (type Page, scopes present, expiry "never" or far future).

## E. Put the values on the SERVER (never in chat, never committed)
The pilot runs on the VM, so the token goes in the deploy folder's `.env` there (not in your local backend/.env, which is only for local testing):
```
gcloud compute ssh pune-property --zone asia-south1-a --project trader-502012
# then edit the .env next to docker-compose.yml (deploy/gcp/.env) and add:
META_PAGE_ID=...
META_PAGE_ACCESS_TOKEN=...
META_IG_BUSINESS_ID=...
SOCIAL_DRY_RUN=true            # keep true until the test post below works, then set false
PUBLIC_MEDIA_BASE_URL=https://34-180-39-243.sslip.io
# then: sudo docker compose up -d backend
```
The token gives full control of the Page. If it leaks: Facebook Settings > Business integrations > remove the app, or reset the app secret.

## F. Public HTTPS address for images (Instagram fetches the pictures itself)
The pilot server is already live at **https://34-180-39-243.sslip.io** and serves our pictures under `/uploads`. On the SERVER set:
```
PUBLIC_MEDIA_BASE_URL=https://34-180-39-243.sslip.io
```
(then restart the backend container). For the Meta app settings, the same address is your site URL and where the privacy-policy page will live
(`/privacy`). Once you own a domain, point it at the server and use it instead: Meta settings are easier to set once.
For testing on this PC only, a free tunnel also works: `cloudflared tunnel --url http://localhost:8000`.

## G. First real post (after the app shows the "Post to PUNE Property" section)
1. Keep `SOCIAL_DRY_RUN=true` and post once to see the "Test post" result. Nothing goes to Facebook.
2. Set `SOCIAL_DRY_RUN=false`, restart the backend, post a listing you own, tick your consent, tap Approve. Check the Page and Instagram.

## Rules we follow
- Every post needs a human tap (Approve). Nothing is auto-posted.
- Only listings whose agent agreed ("post with my name and phone on the PUNE Property Page") are posted.
- No invented numbers: no fake views, likes or followers anywhere.

---

## H. Rebuild the app from scratch: use cases and permissions (now and later)

Use this if the app's use cases disappear, the app is deleted, or you create a new one. Values you will need: App display name **PUNE Property** (or PuneProperties), contact email, the URLs from section C.

### H1. Use cases to add (Meta developer dashboard, app > Use cases > Add use case)
| # | Use case (name in the picker) | Permissions to add under Customize | Needed for | When |
|---|---|---|---|---|
| 1 | **Manage everything on your Page** | `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `pages_manage_metadata`, `pages_read_user_content`, `pages_manage_engagement` | Posting to the Page, reading and answering comments, the comment assistant, scheduling | **Now** |
| 2 | **Manage messaging & content on Instagram** (Instagram API with Facebook Login) | `instagram_basic`, `instagram_content_publish`, `instagram_manage_comments` | Posting to Instagram, later answering Instagram comments | Now (once the Instagram account is Professional and linked to the Page) |
| 3 | **Engage with customers on Messenger from Meta** | `pages_messaging` | Answering Messenger chats with the same engine as the website chat | Later (needs App Review for the public) |
| 4 | **Connect with customers through WhatsApp** | WhatsApp Business permissions | WhatsApp OTP, alerts, chat | Later (needs a business portfolio and business verification) |
| 5 | Facebook Login for Business (added automatically with #1) | none of ours | not used | Leave as is |

Do NOT add: Marketing API, app ads, Threads, Instant Games (not needed).

### H2. App settings to restore (App settings > Basic)
- Display name, category **Business and pages**, contact email `sajwansavita35@gmail.com`.
- App domains `34-180-39-243.sslip.io` (change when we have a real domain).
- Privacy Policy `https://34-180-39-243.sslip.io/privacy`, Terms `/terms`, Data deletion instructions URL `/data-deletion`.
- App icon `docs/brand/pune-property-profile.png`.

### H3. Roles (App roles > Roles)
While the app is in Development mode, only people with a role can use it. Add your own account as **Administrator** and any test account (a friend, an agent) as **Tester**. The Page owner's Facebook account must be an admin of the Page.

### H4. Generate the token and connect the server
1. Graph API Explorer: Meta App = the app, User or Page = "Get Token".
2. Add every permission from H1 rows 1 and 2, then **Generate Access Token** and approve everything for the PUNE Property Page (keep it selected).
3. `.\deploy\gcp\meta_connect.ps1` (token + App Secret). It prints the permissions it received and whether Instagram is linked.
4. Check: `python scripts/verify_engage_live.py` (on the server) must say ALL PASSED.

### H5. Keep it connected (what breaks the token)
Removing the app under Facebook Settings > Business integrations, changing the Facebook password, "log out of all sessions", removing the Page admin. The Interest tab shows a red banner when Facebook rejects the token; fix with H4.

### H6. Going Live later (public, not just testers)
1. Business verification of the business (needs the legal entity, documents).
2. App Review for advanced access: `pages_manage_engagement`/`pages_read_user_content` for comments by the public, `pages_messaging` (Messenger), `instagram_content_publish`/`instagram_manage_comments` for other people's accounts. Prepare a screencast per permission, the privacy policy and a test login.
3. Switch the app to Live. Until then it works for the Page and for people with a role.
4. Agents connecting their OWN Pages/Instagram needs the same App Review plus Business verification: plan it after the pilot.
