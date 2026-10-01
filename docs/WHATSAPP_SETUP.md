# WhatsApp setup for Avasetu (do this yourself; about 30 minutes)

What you get: a buyer taps **Chat on WhatsApp** on the website (or messages the number), the Avasetu assistant answers in their
language from the facts we hold (never inventing prices or details), the buyer's requirement becomes a **lead** in Studio, and the agent
sees a **badge** on the Studio home.

What it costs today: **nothing**. We only reply to buyers who message us first, inside the 24 hours after their last message. Those replies
are free. We send no paid "template" messages, so **no payment card is needed**.

Never share your Facebook password with anyone, including an AI assistant. Nothing below needs it. The only secrets are a token and the app
secret, and you paste those into a hidden prompt on your own PC (the script never prints them).

We start on **Meta's free test number** (it can message up to 5 numbers that you add). Later: the agent's own WhatsApp Business App number
(coexistence) or a real Avasetu number (sections F and G).

---

## A. Add WhatsApp to the existing Meta app (5 min)
1. Open https://developers.facebook.com/apps and click your app **PuneProperties** (App ID `1072258319113727`).
2. In the left menu click **Use cases** (or **Add product** on older layouts) > **Add use case**.
3. Choose **Connect with customers through WhatsApp** > **Next** / **Add**.
4. If Meta asks for a **business portfolio**, pick the one that owns the Avasetu Page. If it asks to create a WhatsApp Business
   Account, accept the suggested one. Meta creates a **test number** for you automatically.

## B. Find the test number and its Phone number ID (2 min)
1. Left menu > **WhatsApp** > **API Setup** (in some layouts: Use cases > WhatsApp > Customize > API Setup).
2. Under **Step 1: Select phone numbers**, the **From** box shows the test number (it starts with +1 555...).
3. Directly below it you see **Phone number ID** (a long number such as `106540352242922`) and **WhatsApp Business Account ID**.
   Copy both into a note. They are not secret.

## C. Add up to 5 phones that may chat with the test number (5 min)
The test number only talks to numbers you list here.
1. Same page, the **To** box > **Manage phone number list** > **Add phone number**.
2. Type your own mobile with +91 (and later the agent's). Meta sends a code by WhatsApp or SMS to that phone.
3. Type the code to confirm. Repeat for up to 5 numbers.

## D. Create a permanent token (System User) (8 min)
The temporary token on the API Setup page expires in 24 hours. For the pilot we use a token that does not expire.
1. Open https://business.facebook.com/settings (Business Settings) and choose the Avasetu business portfolio.
2. **Users** > **System users** > **Add**. Name: `pune-property-whatsapp`, role **Admin** > **Create system user**.
3. With that system user selected: **Assign assets** > **Apps** > tick **PuneProperties** > **Full control** > **Save changes**.
4. Still on the system user: **Assign assets** > **WhatsApp accounts** > tick your WhatsApp Business Account > **Full control** > **Save**.
5. Click **Generate new token** > app **PuneProperties** > expiry **Never** > tick these permissions:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
   - (`business_management` if Meta lists it)
6. **Generate token**. Keep the page open: you paste the token into the script in the next step. Do not paste it into chat or email.
7. Also have the **App Secret** ready: developers.facebook.com > PuneProperties > **App settings** > **Basic** > App secret > **Show**.

## E. Connect the server and the webhook (10 min)
1. On your PC, in PowerShell, from the repo folder, run (use your Phone number ID and WhatsApp Business Account ID from step B):
   ```powershell
   .\deploy\gcp\whatsapp_connect.ps1 -PhoneNumberId 106540352242922 -WabaId 123456789012345
   ```
   Optional: `-OwnerAgentId <your agent id>` (who receives chats that name no agent; if you leave it out the interest/engage owner is used)
   and `-PublicNumber 15550783881` (the number shown on the website button; needs a frontend rebuild, see the note below).
2. Paste the **token** and the **App Secret** when asked (typing is hidden). The script checks them with Meta and shows the number, its name
   and the token's permissions. It writes everything to the server and restarts the backend.
3. At the end it prints **only** two lines you need:
   - Callback URL: `https://34-180-39-243.sslip.io/api/v1/whatsapp/webhook`
   - Verify token: `pp-...` (a random value it just made)
4. Back on developers.facebook.com > **WhatsApp** > **Configuration** > **Webhook** > **Edit**: paste the Callback URL and the Verify
   token > **Verify and save**. (If it fails, check the backend is running and that the token was pasted exactly.)
5. On the same page, **Webhook fields** > **Manage** > find **messages** > **Subscribe**.
6. Test: from a phone you added in step C, send **Hi** to the test number.
   - The reply appears in Studio > **Interest** > **WhatsApp chats** marked "Test mode, not sent" (the server starts in test mode).
   - The lead appears in Studio > **Leads** (source WhatsApp) and a green badge appears on the Studio home.
7. When the replies look right, switch real replies on:
   ```powershell
   .\deploy\gcp\whatsapp_connect.ps1 -PhoneNumberId 106540352242922 -Live
   ```
   (It asks for the token and secret again and prints a new verify token; you do **not** need to re-verify the webhook in Meta.)
   Send **Hi** again: now the answer arrives on your phone.
   Running the script again without `-Live` puts it back in test mode.

Note for the website button: the "Chat on WhatsApp" button shows only when `NEXT_PUBLIC_WHATSAPP_NUMBER` is set when the frontend is
built. The developer adds that build setting once (see docs/handoff/WA1-whatsapp.md); then `-PublicNumber` plus a redeploy shows it.
With the test number, only the 5 phones from step C get answers, so keep the button off until you use a real number.

What buyers experience
- Answers in English, Hindi, Marathi or Hinglish, matching how they write. Questions about a home are answered only from that home's facts;
  sample homes are always called samples; anything we do not know is passed to the agent instead of guessed.
- Once, briefly: "Note: <agent> will contact you on this WhatsApp number about your enquiry. Reply STOP at any time..."
- **STOP** (or UNSUBSCRIBE) stops all messages; **START** turns them back on.
- Photos, voice notes and locations get a friendly "please type" reply.

---

## F. Later: the agent's own WhatsApp Business App number (coexistence)
Coexistence lets an agent keep using the **WhatsApp Business app** on his phone while the same number also works with our assistant.
Messages he sends from his phone are reported to us too.

What Meta requires today (check again when you start; Meta changes this):
- The agent's number must be on the **WhatsApp Business app** (not plain WhatsApp), version **2.24.17 or newer**.
- Onboarding runs through Meta's **Embedded Signup** flow, which Meta offers to **Tech Providers / Solution Partners**. Our app has to be
  set up as a Tech Provider for this (or we use a partner). This is a one-time step for Avasetu, not for each agent.
- Limits on a shared number: about 20 messages per second; group chats, disappearing messages, view-once and live location are turned off
  for that number; chat history sync must finish within 24 hours.

What the agent does on his phone (5 min, with you beside him):
1. Update the WhatsApp Business app.
2. Open the signup link we send him and log in with his own Facebook account (never share passwords).
3. Choose **Connect your existing WhatsApp Business app**; WhatsApp on his phone shows a request (a QR code or a code from Facebook).
4. Tap **Connect** > **Connect to the Business Platform**, choose whether to share chat history, and enter the code.
5. Keep the WhatsApp Business app open until it says it is connected.

What we do afterwards: add his Phone number ID to `WHATSAPP_NUMBER_AGENTS` on the server (a small JSON map, e.g.
`{"<phone number id>": "<agent id>"}`), so every chat to his number goes to his Studio. His number is never shown on the public site unless
his branding has `show_whatsapp` turned on.

## G. Later: a real Avasetu number
1. Get a number that is **not** on WhatsApp now (or delete the WhatsApp account on it first). A landline that can receive a voice call works.
2. WhatsApp Manager (business.facebook.com > WhatsApp accounts > your account > **Phone numbers** > **Add phone number**).
3. Display name **Avasetu**: Meta reviews it (usually 1-2 days). It must match your brand on the website and Page.
4. Verify the number by SMS or voice call. Copy its new Phone number ID.
5. Run the connect script again with the new `-PhoneNumberId` (and `-PublicNumber` so the website button shows it).
6. **Business verification** (Business Settings > Security Center) raises Meta's limits and is needed for the green tick later; it asks for
   business documents, not passwords.

---

## Cost table (Meta per-message pricing, in force since 1 July 2025)

| Message | When | Cost | We use it? |
|---|---|---|---|
| Our reply to a buyer who messaged us (text, image...) | within 24 hours of the buyer's last message | **Free** | Yes, this is everything we send |
| Utility template (e.g. "new lead" alert to an agent) | inside an open 24-hour window | Free | No |
| Utility template | outside the window | Paid (per message) | No (later, needs a payment card) |
| Marketing template | any time | Paid (per message) | No |
| Authentication template | outside the window | Paid | No |

Because we only answer buyers who start the chat, there is nothing to pay and no card is needed. Agent alerts are in-app (the Studio badge)
for now. When you want WhatsApp alerts to agents, add a payment method in WhatsApp Manager and a "new lead" utility template; the code has a
marked place for it.
