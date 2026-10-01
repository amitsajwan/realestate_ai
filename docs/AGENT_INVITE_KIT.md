# Pilot invite kit (Pune agents)

Use this to invite, onboard and check in with the first 3 to 10 agents. Everything here reflects what works **today**. Keep promises inside this list.

## 1. Who to invite
- Active Pune agents who post listings on WhatsApp or Facebook already, ideally in Kharadi, Upper Kharadi or Wagholi (our guides and locality pages are there).
- Someone who will actually try it for two weeks and tell us what is wrong. Ten listings each is the target.
- MahaRERA-registered agents are preferred: ask for the registration number and note it. We do not verify it for them.

## 2. What you can promise (true today)
- A free website for their listings in minutes, on their phone, in the PUNE Property look.
- Ready-made posts (image cards + captions) for Facebook, Instagram and WhatsApp, in English, Hindi and Marathi.
- Posting to the PUNE Property Facebook Page (with their approval each time), signed "PUNE Property team", no phone number shown.
- "Comment INTERESTED" on those posts is answered automatically; questions we cannot answer wait in their **Interest** tab.
- A website chat that answers basic questions and, with the buyer's consent, hands over a lead with a summary (budget, BHK, timing).
- A **weekly summary** they can share on WhatsApp.
- Free during the pilot; we will tell them before that changes.

## 3. What NOT to promise yet
- Instagram publishing (waiting on account linking), voice listings (Premium, hidden), a phone-call button on their site (hidden by design), guaranteed leads or any price/appreciation forecast, or that AI replies replace them.

## 4. Invite message (WhatsApp)

**English**
> Hi {name}, I am building PUNE Property, a free tool for Pune agents. You add a property from your phone and get a website page, ready-made posts for Facebook/Instagram/WhatsApp, and replies to buyers' comments. I would like you to try it for two weeks. Sign in at https://34-180-39-243.sslip.io/join with your mobile number and your personal code: {code}. Please do not share the code. Tell me what is confusing or missing.

**हिंदी**
> नमस्ते {name} जी, मैं पुणे के एजेंट्स के लिए PUNE Property नाम का एक मुफ़्त टूल बना रहा हूँ। मोबाइल से प्रॉपर्टी डालिए, आपको वेबसाइट पेज, फेसबुक/इंस्टाग्राम/व्हाट्सऐप के लिए तैयार पोस्ट और खरीदारों के कमेंट का जवाब मिलेगा। कृपया दो हफ़्ते आज़माइए। https://34-180-39-243.sslip.io/join पर अपने मोबाइल नंबर और अपने पर्सनल कोड {code} से साइन इन करें। कोड किसी से साझा न करें। जो समझ न आए या कम लगे, मुझे बताइए।

**मराठी**
> नमस्कार {name}, मी पुण्यातील एजंट्ससाठी PUNE Property नावाचे मोफत टूल बनवत आहे. मोबाईलवरून प्रॉपर्टी टाका, तुम्हाला वेबसाइट पेज, फेसबुक/इंस्टाग्राम/व्हॉट्सअ‍ॅपसाठी तयार पोस्ट आणि खरेदीदारांच्या कमेंटला उत्तर मिळेल. कृपया दोन आठवडे वापरून पहा. https://34-180-39-243.sslip.io/join वर तुमचा मोबाईल नंबर आणि पर्सनल कोड {code} ने साइन इन करा. कोड कोणालाही देऊ नका. काही समजले नाही किंवा कमी वाटले तर मला सांगा.

## 5. Creating the invite (on the server)
```
gcloud compute ssh pune-property --zone asia-south1-a --project trader-502012
cd app/deploy/gcp
sudo docker compose exec -T -e PYTHONPATH=. backend python scripts/invite.py issue 98XXXXXXXX --label "Rahul, Baner"
```
It prints the 6-digit code and a message. Re-issuing for the same number replaces the code and clears any lockout. People who asked on the website: `scripts/invite_requests.py list`, then `mark-invited <number>`.

## 6. Quick start to send after they sign in (5 steps)
1. **Sign in** with your mobile number and code, then enter your name and city. Add your photo and Instagram/Facebook link if you like (optional).
2. **Add a listing:** tap "+ Add listing", type it the way you would say it ("2 BHK Kharadi 85 lakh ready"), add 2 to 3 photos, check the price, tap Confirm and post.
3. **Get your posts:** open the listing's Marketing screen, choose a language, share the cards to WhatsApp or Instagram, or approve "Post to PUNE Property Page".
4. **Watch the Interest tab:** people who comment INTERESTED or chat on your site show up here. Questions we cannot answer are marked "needs you".
5. **Check Home each morning** and share your week from the "This week" card.

## 7. First-week check-in (10 minutes, on a call or WhatsApp voice note)
Ask, and write down the answers:
1. Did you post a listing? How long did it take? What confused you?
2. Did you share the cards? Where (WhatsApp Status, groups, Instagram, Facebook)?
3. Did anyone enquire? Through what (form, comment, chat, WhatsApp)? Was the summary useful?
4. What would make you post your **next** property here rather than only on WhatsApp?
5. What would you pay for, and roughly how much per month, if this saved you an hour a day?

**Key measure:** does the agent add a second property within 7 days of the first, without being asked?

## 8. Tracking sheet (one row per agent)
Agent | Area | Invited on | First listing on | Listings after 14 days | Photos on listings | Enquiries | Site visits | Second listing within 7 days (Y/N) | Main complaint | Would pay (₹/month)

## 9. When something breaks
- Sign-in problem: re-issue the code (section 5). Five wrong codes lock a number for 30 minutes.
- A wrong or unsafe reply on the Page: delete it on Facebook, then tell the developer the comment text.
- Site down: `https://34-180-39-243.sslip.io/api/v1/health` should say healthy; otherwise see `docs/PILOT_RUNBOOK.md`.

## 9. White-glove onboarding (the owner sets him up; no Facebook or Instagram connection)
For the first agents we do the typing. We do not connect his Facebook or Instagram (that needs Meta review). His listings are posted on the **PUNE Property Page and Instagram** with his name on them, and buyers' interest lands in **his** Interest inbox.

**Collect from the agent (one WhatsApp thread, ask for it in one message):**
1. **Logo** (square image, PNG or JPG) and a **banner** (wide image; his office or a skyline is fine).
2. **Brand colour** (a colour he likes, or his logo's colour) and **business name** (if he trades under one).
3. **Tagline** (one line) and a short **bio** (2 to 3 sentences: years, areas, what he is known for).
4. **RERA agent registration number** (shown as "RERA agent reg: ..." on his posts and page). We do not verify it for him.
5. **Areas** he works in and **languages** he speaks.
6. A clear **photo of himself**.
7. **Per listing:** locality and project name, BHK, carpet area, price, possession, floor, furnishing, amenities, 3 to 6 real photos, and anything buyers always ask (parking, maintenance, nearby schools, metro).
8. **Consent**, in his own words (a WhatsApp reply is enough). Ask him to confirm this exact wording and record it in the Agents screen only after he has said yes:
   > I agree that PUNE Property may feature me and my listings on the PUNE Property Facebook Page, Instagram and website, with my name and RERA number, and that buyers' interest comes to my inbox.

**Owner steps (Studio, Agents tab; visible only to owner accounts):**
1. **Add agent:** name, mobile, a label. The sheet shows his 6-digit code and a ready WhatsApp message. Copy it and send it. The code is shown once (it is stored scrambled); "Make a new code" replaces it.
2. **Brand:** upload logo and photo, and fill the rest of the brand fields.
3. **Add listing for him:** the usual listing flow, saved under his name. Checks are the same as for him (Pune only, price sanity, required fields). Publish it.
4. **Preview his page:** open it and read it as a buyer would.
5. **Consent:** switch it on once he has agreed. Posting his listings is blocked until then.
6. **Post to PUNE Property:** the screen shows the exact Facebook and Instagram captions first. Each carries "Listed by <his business or name>" and "RERA agent reg: <no>" when known, never a phone number. Facebook has his interest link; Instagram says "link in our bio" and the listing appears on our link-in-bio page. You approve on his behalf; the post goes out as the PUNE Property team.

The checklist ring on each agent counts: logo, banner, RERA number, areas, photo, first listing, three listings, consent. Everything you change for him is written to an audit log (who, when, which fields; no values, codes or phone numbers).

**Tell him plainly:** his listings appear on our pages with his name; buyers reach him through the interest link and his Interest tab; we do not post from his own Facebook or Instagram yet.
