# Messenger and Instagram DM assistant: setup (do this yourself; about 20 minutes)

What you get: when a buyer messages the Avasetu Page (the **Message** button) or the Instagram account, the same assistant as on WhatsApp
answers in their language from the facts we hold, asks what they are looking for, asks for their number (with the consent line), and the chat
becomes a **lead** in Studio with a badge. A buyer the comment assistant already messaged after a comment keeps the same lead.

What it costs: **nothing**. We only reply inside the 24 hours after the buyer's last message, which Meta allows for free.

When a person answers a chat from the Meta Business Suite inbox, the assistant **steps back in that chat for 12 hours**
(`MESSENGER_HUMAN_PAUSE_HOURS`), so you never talk over each other.

Never share your Facebook password with anyone, including an AI assistant. Nothing below needs it.

## A. Point Meta's webhooks at the server (10 min)
1. Open https://developers.facebook.com/apps and click the app **PuneProperties**.
2. **Messenger** (Use cases > Engage with customers on Messenger > Customize, or Messenger > Settings on older layouts) > **Webhooks**:
   - Callback URL: `https://34-180-39-243.sslip.io/api/v1/messenger/webhook`
   - Verify token: a long random string you make up. You also put it on the server as `MESSENGER_VERIFY_TOKEN` (step C), **before**
     you press Verify.
   - Fields: tick **messages**, **messaging_postbacks** and **message_echoes**.
3. Still in Messenger settings, under **Webhooks** > the Avasetu Page > **Add subscriptions**: the same three fields.
4. **Instagram** (Use cases > Instagram messaging, or Instagram > Webhooks): the same callback URL and verify token; tick **messages** and
   **messaging_postbacks**.

## B. Let the Instagram account's messages through (2 min)
On the phone, in the Instagram app of the Avasetu account: **Settings > Messages and calls (Message controls) > Connected tools >
Allow access to messages**: on.

## C. Server settings
| Setting | Value |
|---|---|
| `MESSENGER_ENABLED` | `true` |
| `MESSENGER_VERIFY_TOKEN` | the string from step A |
| `MESSENGER_APP_SECRET` | the app secret (leave unset to use `WHATSAPP_APP_SECRET`: it is the same app) |
| `MESSENGER_DRY_RUN` | keep `true` at first: replies are worked out and saved, nothing is sent |
| `MESSENGER_OWNER_AGENT_ID` | optional: who gets chats that name no agent (else the WhatsApp/interest owner) |

`META_PAGE_ID`, `META_PAGE_ACCESS_TOKEN` and `META_IG_BUSINESS_ID` are already set for posting. The Page token already has
`pages_messaging` and `instagram_manage_messages` (the comment assistant uses them for its private replies).

## D. Try it, then go live
1. From a personal Facebook account, message the Page; from a personal Instagram account, message @avasetu.
2. Studio > Admin shows **Messenger and Instagram DMs: practice mode**; the chats and the planned replies are saved
   (`GET /api/v1/messenger/conversations`), and the leads appear in Studio.
3. Happy with the replies? Set `MESSENGER_DRY_RUN=false` and restart. Admin then shows **On and sending replies**.

Turning it off: `MESSENGER_ENABLED=false` (the webhook still answers Meta, and does nothing).
