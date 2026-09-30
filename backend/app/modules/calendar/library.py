"""Evergreen library: 40 stable posts for Pune home buyers (Kharadi, Upper Kharadi, Wagholi, east Pune).

Rules every entry follows (enforced by tests and `calendar_admin.py --dry-check`):
  * no prices, predictions, statistics, builder names, phone numbers or personal names;
  * transport follows "approved is not running";
  * legal statements are limited to those verified against official text (see `review`);
  * the body ends with a question or a save/share prompt;
  * the Facebook caption may link to our site; the Instagram caption never has a URL (it says "link in our bio").
"""
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

SITE = (os.environ.get("PUBLIC_SITE_URL") or "https://34-180-39-243.sslip.io").rstrip("/")

PILLARS = ("myth", "explainer", "checklist", "local", "poll", "agent")

# Source notes reused in `review`.
S_RERA = "RERA Act 2016 text (Sec 2(k), 3, 4(2)(l)(D), 13, 14(3), 19(10)) as reproduced on ibclaw.in, taxguru.in and iPleaders; indiacode.nic.in PDF blocked (403), so re-check wording on indiacode.nic.in"
S_MAHARERA = "maharera.maharashtra.gov.in (fetched: registered projects, project progress, make a complaint, guidance for home buyers)"
S_IGR = "igrmaharashtra.gov.in (fetched: e-ASR, e-Registration 2.0, e-Appointment, e-Search, e-Payment GRAS)"
S_REGACT = "Registration Act 1908 Sec 23: four months to present a document (legalserviceindia.com, bcasonline.org)"
S_STAMP = "Stamp duty on the higher of agreement value and ready reckoner value: cleartax.in, godrejcapital.com, propnewz.com (secondary; official rate tool is e-ASR on igrmaharashtra.gov.in). No rate quoted on purpose"
S_OC = "OC vs CC: maharera.maharashtra.gov.in/possession-stage, PMC/PCMC guidance summarised on nobrokerage.com and marathon.in (secondary)"
S_RBI = "RBI Directions on Pre-payment Charges on Loans, 2025 (businesstoday.in, angelone.in; RBI PDF not machine-readable): no prepayment charge on floating-rate loans to individuals for non-business use, sanctioned or renewed on or after 1 January 2026. Re-check on rbi.org.in before each use"
S_METRO = "Site pages /insights/metro-kharadi-wagholi-approved-not-running (Union Cabinet approvals of Corridor 2B and Line 4; cites Maha-Metro)"
GENERAL = "General, non-legal advice from practice (no figure or rule stated); no source needed"


@dataclass(frozen=True)
class Entry:
    slug: str
    pillar: str
    kicker: str
    title: str
    points: Tuple[str, ...]
    body: str                      # shared caption text, no URLs, ends with a question or a save/share prompt
    tags: Tuple[str, ...]          # hashtags; Instagram uses all, Facebook the first four
    review: str                    # which facts need sources, and what was verified
    link: Optional[str] = None     # site path for the Facebook caption, e.g. /insights/<slug>, /localities, /request-invite
    cta_ig: Optional[str] = None   # overrides the generic "link in our bio" line
    card_from: Optional[str] = None  # reuse a pre-rendered brand card (Devanagari cannot be shaped by Pillow)

    @property
    def fb_caption(self) -> str:
        out = self.body
        if self.link:
            out += f"\n\n\U0001F517 {SITE}{self.link}"
        return out + "\n\n" + " ".join(self.tags[:4])

    @property
    def ig_caption(self) -> str:
        out = self.body
        if self.link:
            out += "\n\n" + (self.cta_ig or _IG_CTA.get(self.link.split("/")[1], "More in the link in our bio."))
        return out + "\n\n" + " ".join(self.tags)


_IG_CTA = {"insights": "The full guide is at the link in our bio.", "localities": "Area guides: link in our bio.",
           "request-invite": "Request your invite: link in our bio."}

B = "#PunePropertyHub"


def _e(slug, pillar, kicker, title, points, body, tags, review, **kw) -> Entry:
    return Entry(slug, pillar, kicker, title, tuple(points), body.strip(), tuple(tags), review, **kw)


ENTRIES: List[Entry] = [
    # ---------------------------------------------------------------- myth vs fact
    _e("myth-rera-means-safe", "myth", "MYTH VS FACT", "\"It has a RERA number, so I can relax\"",
       ["Myth: registration means nothing more to check", "Fact: it gives you information and rights", "Open the project page and read it yourself",
        "Compare its dates and details with what you were told"],
       "\U0001F914 Myth vs fact\n\nMyth: \"It has a RERA number, so I can relax.\"\n\n"
       "Fact: registration puts the project's details on a public page and gives you rights as a buyer. It does not read the page for you.\n\n"
       "Open the project's page on the MahaRERA website. Match the possession date and the details there with what you were told.\n\n"
       "\U0001F4AC Have you ever opened a RERA page before booking? Tell us in the comments.",
       (B, "#RERA", "#MahaRERA", "#PuneRealEstate", "#HomeBuyingTips"),
       f"Claim: registration gives public project details and buyer rights. Verified: {S_MAHARERA}. No 'guarantee' wording used."),
    _e("myth-token-booking", "myth", "MYTH VS FACT", "\"The booking amount is just a small token\"",
       ["Myth: pay whatever they ask, it is only a token", "Fact: RERA caps advances at 10% of the cost", "Above that, a registered agreement for sale must come first",
        "Ask to see the agreement before paying more"],
       "\U0001F4B8 Myth vs fact\n\nMyth: \"The booking amount is just a token, pay now and sort the rest later.\"\n\n"
       "Fact: under RERA (Section 13) a promoter cannot take more than 10% of the cost as an advance or application fee without first signing a written agreement for sale and registering it.\n\n"
       "So if a large amount is asked before any agreement: pause and ask for the draft agreement first.\n\n"
       "\U0001F4E4 Share this with a friend who is about to book.",
       (B, "#RERA", "#HomeBuyingTips", "#FirstHomeBuyer", "#PuneRealEstate"),
       f"Verified RERA Sec 13(1): no more than ten per cent as advance/application fee without a written agreement for sale registered. Source: {S_RERA}."),
    _e("myth-stamp-on-price", "myth", "MYTH VS FACT", "\"Stamp duty is on the price I pay\"",
       ["Myth: duty is charged only on the agreed price", "Fact: Maharashtra charges on the higher of agreement value and ready reckoner value",
        "Check the official e-ASR tool for the rate that applies", "Ask for duty and registration in the cost sheet"],
       "\U0001F9FE Myth vs fact\n\nMyth: \"Stamp duty is charged on the price I agreed.\"\n\n"
       "Fact: in Maharashtra it is calculated on the higher of two values: the agreement value and the government's ready reckoner value for the property.\n\n"
       "We do not quote a rate here because rates and concessions change. The state's registration department has an online tool (e-ASR) for the current position.\n\n"
       "\U0001F4AC Saving this for your budget sheet? Tell us what else confuses you.",
       (B, "#StampDuty", "#Maharashtra", "#HomeBuyingTips", "#PuneHomes"),
       f"Claim: duty on the higher of agreement and ready reckoner value. {S_STAMP}. Tool name e-ASR verified on {S_IGR}. No rate stated."),
    _e("myth-cc-means-move-in", "myth", "MYTH VS FACT", "\"The project has a commencement certificate, so I can move in\"",
       ["Commencement certificate (CC): permission to start building", "Occupancy certificate (OC): the building is ready to occupy", "Possession is about the OC",
        "Ask which one you are being shown"],
       "\U0001F3D7️ Myth vs fact\n\nMyth: \"The project has a commencement certificate, so I can move in.\"\n\n"
       "Fact: a commencement certificate (CC) is permission to start construction. The occupancy certificate (OC), issued by the local authority, is what says the building can be occupied.\n\n"
       "When someone says \"approvals are in place\", ask which approval, and ask to see it.\n\n"
       "\U0001F4BE Save this for your next builder meeting.",
       (B, "#OccupancyCertificate", "#HomeBuyingTips", "#PuneRealEstate", "#Kharadi"),
       f"Claim: CC = permission to begin building; OC = fit to occupy, issued by local authority. {S_OC}. No authority name given because it differs by area."),
    _e("myth-uc-always-cheaper", "myth", "MYTH VS FACT", "\"Under construction is always the smarter buy\"",
       ["It can cost less to enter, but you wait", "You may pay rent and EMI together meanwhile", "You depend on the stated possession date",
        "Ready-to-move: you see exactly what you get"],
       "⚖️ Myth vs fact\n\nMyth: \"Under construction is always the smarter buy.\"\n\n"
       "Fact: it can cost less to enter, but you wait, you may pay rent and EMI together meanwhile, and you rely on the builder keeping the date. "
       "Ready-to-move means no waiting, and you see exactly what you buy.\n\n"
       "Neither is wrong. Pick the risk you prefer, and check the possession date on the RERA page either way.\n\n"
       "\U0001F4AC Which would you choose, and why?",
       (B, "#ReadyToMove", "#UnderConstruction", "#Wagholi", "#UpperKharadi"),
       f"Balanced framing, no price comparison or statistic. Matches site page /insights/kharadi-upper-kharadi-wagholi. {GENERAL}.",
       link="/insights/kharadi-upper-kharadi-wagholi"),
    _e("myth-near-metro", "myth", "MYTH VS FACT", "\"There is a metro line planned, so this flat is near the metro\"",
       ["Approved is not the same as running", "Approved lines take years to build", "Do not pay extra for a station that does not exist yet",
        "Check status on the official Maha-Metro website"],
       "\U0001F687 Myth vs fact\n\nMyth: \"A metro line is planned, so this flat is near the metro.\"\n\n"
       "Fact: two lines for this side of Pune (Ramwadi to Wagholi, and Kharadi to Khadakwasla) have been approved. Approved is not running, and approved lines take years to build.\n\n"
       "Do not pay extra today for a station that does not exist yet. Check the current status on the Maha-Metro website.\n\n"
       "\U0001F4E4 Share with someone who is comparing flats by \"metro distance\".",
       (B, "#PuneMetro", "#Kharadi", "#Wagholi", "#HomeBuyingTips"),
       f"Transport policy: approved is not running. {S_METRO}. No dates, no opening forecast.",
       link="/insights/metro-kharadi-wagholi-approved-not-running"),
    _e("myth-rent-is-waste", "myth", "MYTH VS FACT", "\"Rent is money thrown away\"",
       ["Rent buys flexibility: move when work moves", "Buying adds EMI, maintenance, tax and repairs", "Buying also means staying put for years",
        "The real question: how long will you stay?"],
       "\U0001F3E0 Rent vs buy, without the slogans\n\nMyth: \"Rent is money thrown away.\"\n\n"
       "Fact: rent buys you flexibility. Buying gives you a home of your own, and also adds an EMI, maintenance, taxes and repairs, and ties you to one place for years.\n\n"
       "A simple first question: how long do you realistically expect to stay in this area? Start from your answer.\n\n"
       "\U0001F4AC Renting or buying right now? Tell us what tipped it for you.",
       (B, "#RentVsBuy", "#FirstHomeBuyer", "#PuneHomes", "#Kharadi"),
       f"Framing only, no numbers or market view. {GENERAL}."),

    # ---------------------------------------------------------------- explainers
    _e("carpet-under-rera", "explainer", "CARPET AREA, AS RERA DEFINES IT", "What counts as carpet area, and what does not",
       ["Counts: the net usable floor area inside the flat", "Counts: the area of internal partition walls", "Does not count: external walls and service shafts",
        "Does not count: exclusive balcony, verandah or open terrace"],
       "\U0001F4D0 Carpet area under RERA\n\nRERA defines carpet area as the net usable floor area of the apartment.\n\n"
       "✅ Included: the area covered by the internal partition walls\n"
       "❌ Not included: external walls, service shafts, your exclusive balcony or verandah, your exclusive open terrace\n\n"
       "So when a brochure shows a bigger number, ask which area it is. Compare flats on carpet area.\n\n"
       "\U0001F4BE Save this before your next site visit.",
       (B, "#CarpetArea", "#RERA", "#PuneRealEstate", "#HomeBuyingTips"),
       f"Verified RERA Sec 2(k) wording. Source: {S_RERA}."),
    _e("cost-sheet-decoded", "explainer", "HOW TO READ", "Reading a cost sheet: the lines that are not the price",
       ["Base price: on which area is it calculated?", "Parking and club or amenity charges", "Maintenance and other deposits",
        "Taxes and government charges", "Ask for the total, in writing"],
       "\U0001F9FE How to read a cost sheet\n\nThe headline price is one line. Ask the cost sheet to show all of these:\n\n"
       "1️⃣ Base price, and the area it is calculated on\n2️⃣ Parking and amenity charges\n3️⃣ Maintenance and other deposits\n"
       "4️⃣ Taxes and government charges\n5️⃣ The total, in writing\n\n"
       "Put two cost sheets side by side and compare the totals, not the headlines.\n\n"
       "\U0001F4AC What surprised you most on a cost sheet?",
       (B, "#CostSheet", "#HomeBuyingTips", "#PuneHomes", "#UpperKharadi"),
       f"Structure of charges only; no amounts, no claim about what is legally allowed. {GENERAL}."),
    _e("read-your-agreement", "explainer", "BEFORE YOU SIGN", "Five things to find in your agreement for sale",
       ["The area you are buying, stated as carpet area", "The payment schedule and what each payment is linked to", "The possession date and what happens if it slips",
        "What is included: parking, fittings, amenities", "Have a lawyer read it before you sign"],
       "✍️ Before you sign the agreement for sale\n\nFind these five things in the draft:\n\n"
       "1️⃣ The area you are buying, stated as carpet area\n2️⃣ The payment schedule and what each payment is linked to\n"
       "3️⃣ The possession date and what happens if it slips\n4️⃣ What is included: parking, fittings, amenities\n"
       "5️⃣ Whether a lawyer of your choice has read it\n\n"
       "Ask for the draft days before signing day, not on the day.\n\n"
       "\U0001F4E4 Share this with a friend who is about to sign.",
       (B, "#AgreementForSale", "#HomeBuyingTips", "#RERA", "#PuneRealEstate"),
       f"Practical checklist; RERA Sec 13 (agreement particulars incl. payment schedule and possession date) per {S_RERA}. Not legal advice."),
    _e("read-a-rera-page", "explainer", "HOW TO READ", "How to read a project's MahaRERA page",
       ["Find the registration number from the ad or brochure", "Search it on the MahaRERA website", "Note the stated completion date",
        "Check the project progress updates", "Same details as your agreement?"],
       "\U0001F4CB How to read a project's MahaRERA page\n\n"
       "1️⃣ Take the registration number from the ad or brochure\n2️⃣ Search it on the MahaRERA website\n"
       "3️⃣ Note the stated completion date\n4️⃣ Look at the project progress updates\n"
       "5️⃣ Compare all of it with your agreement and what you were told\n\n"
       "No registration number in the ad? Ask for it before you pay anything.\n\n"
       "\U0001F4BE Save this steps list.",
       (B, "#MahaRERA", "#RERA", "#HomeBuyingTips", "#Kharadi"),
       f"Verified site features: registered project search, project progress, complaints. Source: {S_MAHARERA}."),
    _e("loan-eligibility-basics", "explainer", "HOME LOAN BASICS", "What a lender looks at before approving a home loan",
       ["Your income and how stable it is", "Your existing EMIs and loans", "Your credit history", "The property's papers and approvals",
        "Get the eligibility checked before you pay a booking amount"],
       "\U0001F3E6 Home loan basics\n\nBefore approving a loan, a lender usually looks at:\n\n"
       "▪ Your income and how stable it is\n▪ Your existing EMIs and loans\n▪ Your credit history\n▪ The property's papers and approvals\n\n"
       "Practical tip: ask the lender about eligibility before you pay a booking amount, not after.\n\n"
       "\U0001F4AC What would you like explained next: EMI, eligibility or documents?",
       (B, "#HomeLoan", "#FirstHomeBuyer", "#HomeBuyingTips", "#PuneHomes"),
       f"General lending practice, no rates, limits or ratios quoted. {GENERAL}."),
    _e("registration-steps", "explainer", "REGISTRATION DAY", "Registering your agreement: the steps in order",
       ["Agreement for sale is drafted and read", "Stamp duty is paid through the official system", "Book an appointment at the sub-registrar's office",
        "Present the document within four months of signing", "Collect your registered copy and keep it safe"],
       "\U0001F4DD Registering your agreement, in order\n\n"
       "1️⃣ The agreement is drafted and read\n2️⃣ Stamp duty is paid through the official system\n"
       "3️⃣ Book an appointment at the sub-registrar's office (the state offers online e-Registration and e-Appointment)\n"
       "4️⃣ Present the document within four months of signing it\n5️⃣ Collect your registered copy and keep it safe\n\n"
       "\U0001F4AC Done this before? Tell us what you wish you had known.",
       (B, "#PropertyRegistration", "#StampDuty", "#HomeBuyingTips", "#PuneRealEstate"),
       f"Four-month presentation period: {S_REGACT}. Online services named: {S_IGR}. Order of steps is general; fees not quoted."),
    _e("possession-and-oc", "explainer", "POSSESSION", "Before you take possession: OC, then the keys",
       ["Ask to see the occupancy certificate (OC)", "RERA: take physical possession within two months of the OC", "Inspect the flat against the agreement",
        "Note every defect in writing", "Do not sign a \"fully satisfied\" paper in a hurry"],
       "\U0001F511 Before you take possession\n\n"
       "✅ Ask to see the occupancy certificate (OC)\n✅ Under RERA (Section 19(10)) the buyer is expected to take physical possession within two months of the OC being issued\n"
       "✅ Inspect the flat against the agreement\n✅ Write down every defect\n\n"
       "Do not sign a \"fully satisfied\" paper in a rush if something is not right.\n\n"
       "\U0001F4E4 Share with someone whose flat is nearly ready.",
       (B, "#Possession", "#OccupancyCertificate", "#RERA", "#PuneRealEstate"),
       f"Verified RERA Sec 19(10): take physical possession within two months of the occupancy certificate. {S_RERA}. OC meaning: {S_OC}."),
    _e("defect-liability-5yrs", "explainer", "YOUR RIGHTS", "After possession: the five-year defect window",
       ["Report structural or workmanship defects in writing", "Within five years of possession", "RERA: the promoter must fix them within 30 days, free of charge",
        "Keep dated photos and emails"],
       "\U0001F6E0️ After possession: the five-year window\n\n"
       "Under RERA (Section 14(3)), if a structural defect or a defect in workmanship or services is brought to the promoter's notice within five years of handing over possession, the promoter must rectify it within thirty days at no extra charge.\n\n"
       "Report in writing, keep dated photos, keep the emails.\n\n"
       "\U0001F4BE Save this for after you move in.",
       (B, "#RERA", "#HomeOwner", "#HomeBuyingTips", "#PuneHomes"),
       f"Verified RERA Sec 14(3): five years from possession, rectify within thirty days without charge. {S_RERA}."),
    _e("rera-70-percent-account", "explainer", "WHERE YOUR MONEY GOES", "The separate account behind a RERA project",
       ["70% of what buyers pay goes into a separate bank account", "It is for construction and land cost only", "Withdrawals follow the project's progress",
        "Certified by an architect, an engineer and a CA"],
       "\U0001F3E6 The separate account behind a RERA project\n\n"
       "Under RERA (Section 4(2)(l)(D)), 70% of the money a promoter collects from buyers for a project must be kept in a separate bank account and used only for that project's construction and land cost.\n\n"
       "Money can be taken out in proportion to progress, as certified by an architect, an engineer and a chartered accountant.\n\n"
       "\U0001F4AC Did you know this before? Tell us.",
       (B, "#RERA", "#HomeBuyingTips", "#PuneRealEstate", "#FirstHomeBuyer"),
       f"Verified RERA Sec 4(2)(l)(D): 70% in a separate scheduled-bank account, withdrawal in proportion to completion, certified by architect, engineer and CA. {S_RERA}."),
    _e("payment-plan-milestones", "explainer", "PAYMENT PLANS", "Pay against progress, not against pressure",
       ["Read the payment schedule in the agreement", "Each instalment should be linked to a stage", "Match each stage with what you see on site",
        "Keep receipts for every payment", "Questions? Ask before the next instalment"],
       "\U0001F4B3 Pay against progress\n\nBefore every instalment:\n\n"
       "1️⃣ Read the payment schedule in the agreement\n2️⃣ Check which stage each instalment is linked to\n"
       "3️⃣ Match the stage to what you can see on site\n4️⃣ Keep a receipt for every payment\n\n"
       "A demand that does not match the schedule is worth a question before you pay.\n\n"
       "\U0001F4E4 Share with a friend who is paying instalments.",
       (B, "#PaymentPlan", "#HomeBuyingTips", "#UnderConstruction", "#PuneRealEstate"),
       f"Practical checklist; agreement must state payment manner and dates (RERA Sec 13(2), {S_RERA}). No percentages quoted."),

    # ---------------------------------------------------------------- checklists
    _e("water-and-power-questions", "checklist", "ASK BEFORE YOU BOOK", "Six water and power questions for any flat",
       ["Where does the water come from: municipal, tanker or borewell?", "How much storage does the building have?", "What does the power backup cover?",
        "Who pays for it: you, or the society?", "Is there a water meter or a flat charge?", "Ask current residents, not just the seller"],
       "\U0001F4A7⚡ Water and power: six questions\n\n"
       "1️⃣ Where does the water come from: municipal, tanker or borewell?\n2️⃣ How much storage does the building have?\n"
       "3️⃣ What does the power backup cover: lifts, common areas, your flat?\n4️⃣ Who pays for it?\n5️⃣ Is water metered or a flat charge?\n"
       "6️⃣ What do current residents say?\n\n"
       "\U0001F4BE Save this for your next site visit.",
       (B, "#UpperKharadi", "#Wagholi", "#SiteVisit", "#HomeBuyingTips"),
       f"Questions only, no claim about any locality's supply. Mirrors site page /insights/site-visit-checklist-upper-kharadi-wagholi. {GENERAL}.",
       link="/insights/site-visit-checklist-upper-kharadi-wagholi"),
    _e("commute-test-3-runs", "checklist", "COMMUTE TEST", "Do the commute test three times",
       ["Weekday, about 9 am: to your office", "Weekday, about 6:30 pm: back home", "Once in rain or on a busy day", "Use the route you would really take",
        "Count the time door to door"],
       "\U0001F697 The commute test, done properly\n\n"
       "1️⃣ A weekday at about 9 am: to your office\n2️⃣ A weekday at about 6:30 pm: back home\n3️⃣ Once more on a busy day or in the rain\n\n"
       "Use the route you would really take, and count the time door to door, including parking at both ends.\n\n"
       "A Sunday drive tells you nothing about a Monday.\n\n"
       "\U0001F4AC How long is your commute today, and what would you accept?",
       (B, "#Kharadi", "#Wagholi", "#CommuteTest", "#PuneRealEstate"),
       f"No travel times stated (policy: never quote times). Matches site guide /insights/kharadi-upper-kharadi-wagholi. {GENERAL}.",
       link="/insights/kharadi-upper-kharadi-wagholi"),
    _e("society-and-maintenance", "checklist", "LIVING THERE", "Questions about the society and maintenance",
       ["What does the monthly maintenance cover?", "Is there a deposit or corpus fund, and why?", "Who manages the building after handover?",
        "Are lifts, security and cleaning included?", "Meet two current residents"],
       "\U0001F3E2 The society and maintenance: what to ask\n\n"
       "▪ What does the monthly maintenance cover?\n▪ Is there a deposit or corpus fund, and what is it for?\n▪ Who manages the building after handover?\n"
       "▪ Are lifts, security and cleaning included?\n▪ Can you meet two current residents?\n\n"
       "Get the answers in writing. Maintenance is a cost you pay every month for years.\n\n"
       "\U0001F4BE Save this list.",
       (B, "#SocietyLiving", "#HomeBuyingTips", "#PuneHomes", "#UpperKharadi"),
       f"Questions only; no amounts or legal claim about society formation. {GENERAL}."),
    _e("questions-for-agent", "checklist", "BEFORE YOU HIRE AN AGENT", "Eight questions to ask your property agent",
       ["Can I see the RERA number of this project?", "Is this flat available, and since when?", "What is the full cost, in writing?",
        "What is included in the price?", "What do current residents say?", "Is there anything you would not recommend?",
        "Which documents can I see today?", "May I take time to decide?"],
       "\U0001F91D Eight questions for your property agent\n\n"
       "1️⃣ Can I see the RERA number of this project?\n2️⃣ Is this flat available, and since when?\n3️⃣ What is the full cost, in writing?\n"
       "4️⃣ What is included in the price?\n5️⃣ What do current residents say?\n6️⃣ Is there anything you would not recommend?\n"
       "7️⃣ Which documents can I see today?\n8️⃣ May I take time to decide?\n\n"
       "A good agent is comfortable with these. \U0001F4E4 Share with someone starting their search.",
       (B, "#PropertyAgent", "#HomeBuyingTips", "#PuneRealEstate", "#FirstHomeBuyer"),
       f"Questions only. {GENERAL}."),
    _e("red-flags-in-ads", "checklist", "RED FLAGS", "Six red flags in a property ad",
       ["No RERA registration number", "\"Only a few left, book today\" pressure", "A price with no area basis", "Photos that are only renders",
        "\"Metro coming soon\" as the main selling point", "No address you can visit"],
       "\U0001F6A9 Six red flags in a property ad\n\n"
       "1️⃣ No RERA registration number\n2️⃣ \"Only a few left, book today\" pressure\n3️⃣ A price with no area it is based on\n"
       "4️⃣ Only computer renders, no site photos\n5️⃣ \"Metro coming soon\" as the main selling point. Approved is not running.\n6️⃣ No address you can visit\n\n"
       "One flag is a question. Three flags is a reason to walk away.\n\n"
       "\U0001F4AC Which one have you seen most?",
       (B, "#RedFlags", "#PropertyAds", "#HomeBuyingTips", "#PuneRealEstate"),
       f"Opinion checklist; RERA-number point per {S_RERA} (advertisements of registered projects carry the number: re-verify Sec 11(2) wording before adding legal language). Metro line per {S_METRO}."),
    _e("resale-vs-new", "checklist", "RESALE OR NEW?", "Resale or new: what to check in each",
       ["New: RERA page, agreement, possession date", "Resale: the seller's ownership papers", "Resale: society dues cleared in writing",
        "Resale: the age and upkeep of the building", "Either: loan eligibility and full cost"],
       "\U0001F504 Resale or new: what to check in each\n\n"
       "\U0001F195 New: the RERA page, the agreement, the possession date\n\n"
       "\U0001F3E0 Resale: the seller's ownership papers, society dues cleared in writing, the age and upkeep of the building\n\n"
       "Either way: loan eligibility and the full cost, in writing.\n\n"
       "\U0001F4AC Resale or new, which are you leaning towards?",
       (B, "#ResaleFlat", "#NewHome", "#HomeBuyingTips", "#PuneHomes"),
       f"Checklist only. Have a lawyer verify title (advice, not a legal claim). {GENERAL}."),
    _e("documents-before-booking", "checklist", "DOCUMENTS", "Documents to see before you pay a booking amount",
       ["The project's RERA registration number", "The approvals and sanctioned plan", "Draft agreement for sale", "The full cost sheet",
        "A lawyer's view on the title"],
       "\U0001F4C2 Documents to see before you pay a booking amount\n\n"
       "✅ The project's RERA registration number\n✅ The approvals and the sanctioned plan\n✅ The draft agreement for sale\n✅ The full cost sheet\n✅ A lawyer's view on the title\n\n"
       "If something is \"not ready yet\", ask when it will be, and decide after you have seen it.\n\n"
       "\U0001F4BE Save this checklist.",
       (B, "#HomeBuyingTips", "#RERA", "#PuneRealEstate", "#FirstHomeBuyer"),
       f"General checklist; RERA Sec 13 context per {S_RERA}."),
    _e("rainy-day-visit", "checklist", "MONSOON VISIT", "Visit the flat once when it rains",
       ["Is the road outside easy to use?", "Does water collect near the entrance or parking?", "Any seepage on walls, ceilings or window corners?",
        "How does the building handle rainwater?", "Ask residents about last monsoon"],
       "\U0001F327️ Visit the flat once when it rains\n\n"
       "▪ Is the road outside easy to use?\n▪ Does water collect near the entrance or parking?\n▪ Any damp on walls, ceilings or window corners?\n"
       "▪ How does the building handle rainwater?\n▪ What do residents say about last monsoon?\n\n"
       "A sunny-day visit hides what a rainy day shows.\n\n"
       "\U0001F4E4 Share with someone viewing flats this season.",
       (B, "#Monsoon", "#SiteVisit", "#UpperKharadi", "#Wagholi"),
       f"Checklist only, no claim about any area's drainage. Complements /insights/site-visit-checklist-upper-kharadi-wagholi. {GENERAL}.",
       link="/insights/site-visit-checklist-upper-kharadi-wagholi"),
    _e("possession-day-snag-list", "checklist", "POSSESSION DAY", "Possession-day snag list",
       ["Switches, sockets and lights", "Taps, drains and water pressure", "Doors, windows and locks", "Walls, tiles and paint for cracks or damp",
        "Meter, lift and parking match the agreement"],
       "✅ Possession-day snag list\n\nBring a torch, a phone charger and a copy of the agreement.\n\n"
       "▪ Switches, sockets and lights\n▪ Taps, drains and water pressure\n▪ Doors, windows and locks\n▪ Walls, tiles and paint: cracks or damp\n"
       "▪ Meter, lift and parking match the agreement\n\n"
       "Photograph every issue and send the list in writing the same day.\n\n"
       "\U0001F4BE Save this for the big day.",
       (B, "#Possession", "#HomeOwner", "#HomeBuyingTips", "#PuneHomes"),
       f"Practical checklist. Written notice supports the defect window (RERA Sec 14(3), {S_RERA})."),
    _e("monthly-outgoings", "checklist", "AFTER YOU MOVE IN", "What a home costs every month, beyond the EMI",
       ["EMI, if you have a loan", "Society maintenance", "Parking, if charged separately", "Property tax and insurance", "Electricity, water and repairs"],
       "\U0001F4C5 What a home costs every month, beyond the EMI\n\n"
       "▪ EMI, if you have a loan\n▪ Society maintenance\n▪ Parking, if charged separately\n▪ Property tax and insurance\n▪ Electricity, water and repairs\n\n"
       "Write your own numbers next to each line before you book. A home should fit your month, not only your budget for the purchase.\n\n"
       "\U0001F4AC What did you forget to budget for?",
       (B, "#HomeBudget", "#FirstHomeBuyer", "#HomeBuyingTips", "#PuneHomes"),
       f"Categories only, no amounts. {GENERAL}."),

    # ---------------------------------------------------------------- local life and polls
    _e("poll-near-office-vs-space", "poll", "WHICH WOULD YOU PICK?", "Near the office, or more space further out?",
       ["1. A smaller flat close to work", "2. A bigger flat, a longer commute", "Comment 1 or 2, and tell us why"],
       "\U0001F5F3️ Which would you pick?\n\n1️⃣ A smaller flat close to work\n2️⃣ A bigger flat, with a longer commute\n\n"
       "Kharadi, Upper Kharadi and Wagholi each lean a different way, and there is no wrong answer. It depends on how you spend your week.\n\n"
       "\U0001F4AC Comment 1 or 2, and tell us why.",
       (B, "#Kharadi", "#Wagholi", "#UpperKharadi", "#PuneHomes"),
       f"Poll. No price or distance claim; area character per site page /localities. {GENERAL}.",
       link="/localities"),
    _e("poll-ready-vs-uc", "poll", "WHICH WOULD YOU PICK?", "Ready to move, or under construction?",
       ["1. Ready to move: see exactly what you get", "2. Under construction: wait, but enter earlier", "Comment 1 or 2"],
       "\U0001F5F3️ Which would you pick?\n\n1️⃣ Ready to move: you see exactly what you get\n2️⃣ Under construction: you wait, and you enter earlier\n\n"
       "Think about how long you can wait, and how much you trust a date.\n\n"
       "\U0001F4AC Comment 1 or 2. Why?",
       (B, "#ReadyToMove", "#UnderConstruction", "#PuneRealEstate", "#Wagholi"),
       f"Poll, no claims. {GENERAL}."),
    _e("poll-top-priority", "poll", "YOUR TOP PRIORITY", "Pick ONE thing you would not compromise on",
       ["1. Short commute", "2. Space inside the flat", "3. Schools and hospitals close by", "4. A quiet, green surrounding", "Comment the number"],
       "\U0001F5F3️ If you could keep only one, which?\n\n1️⃣ A short commute\n2️⃣ Space inside the flat\n3️⃣ Schools and hospitals close by\n4️⃣ A quiet, green surrounding\n\n"
       "Your answer tells you what to look for first.\n\n\U0001F4AC Comment the number.",
       (B, "#HomeBuyingTips", "#PuneHomes", "#Kharadi", "#Wagholi"),
       f"Poll, no claims. {GENERAL}."),
    _e("poll-wfh-room", "poll", "WHICH WOULD YOU PICK?", "A work-from-home room, or a bigger living room?",
       ["1. A separate room to work in", "2. A bigger living room for everyone", "3. Neither: I want a balcony", "Comment the number"],
       "\U0001F5F3️ Which would you pick?\n\n1️⃣ A separate room to work in\n2️⃣ A bigger living room for everyone\n3️⃣ Neither, give me a balcony\n\n"
       "Work habits changed what people want from a flat.\n\n\U0001F4AC Comment 1, 2 or 3.",
       (B, "#WorkFromHome", "#HomeBuyingTips", "#PuneHomes", "#UpperKharadi"),
       f"Poll, no claims. {GENERAL}."),
    _e("poll-metro-pay-more", "poll", "YOUR VIEW", "Would you pay extra for a flat near a planned metro station?",
       ["1. Yes, for the convenience later", "2. No, approved is not running", "3. Only once it is running", "Comment the number"],
       "\U0001F687 A question for buyers\n\nTwo metro lines for this side of Pune are approved. Approved is not running, and they take years to build.\n\n"
       "Would you pay extra for a flat near a planned station?\n\n1️⃣ Yes, for the convenience later\n2️⃣ No, approved is not running\n3️⃣ Only once it is running\n\n"
       "\U0001F4AC Comment the number.",
       (B, "#PuneMetro", "#Kharadi", "#Wagholi", "#HomeBuyingTips"),
       f"Transport policy: approved is not running. {S_METRO}. Poll option 1 is a viewpoint offered for discussion, not a claim."),
    _e("local-10-minute-test", "local", "NEIGHBOURHOOD TEST", "The 10-minute test: what should be close to home?",
       ["A pharmacy and a clinic", "Daily groceries and vegetables", "A school you would consider", "Somewhere to walk", "Write your own list first"],
       "\U0001F6B6 The 10-minute test\n\nBefore you fall for a flat, write down what you need within a short trip from home:\n\n"
       "▪ A pharmacy and a clinic\n▪ Daily groceries and vegetables\n▪ A school you would consider\n▪ Somewhere to walk\n\n"
       "Then go and check each one on foot or by the route you would really use.\n\n"
       "\U0001F4AC What is on your list that is not on ours?",
       (B, "#NeighbourhoodGuide", "#Kharadi", "#Wagholi", "#PuneHomes"),
       f"No named places, no distances. Area context from site page /localities. {GENERAL}.",
       link="/localities"),
    _e("local-sunday-vs-monday", "local", "LOCAL LIFE", "Visit on a Sunday, then again on a Monday",
       ["Sunday: how quiet is it, really?", "Monday morning: how busy are the roads?", "Weekday evening: noise, traffic, parking", "Talk to a shopkeeper nearby",
        "Decide after both visits"],
       "\U0001F4C6 Visit on a Sunday, then again on a Monday\n\nA Sunday shows you the quiet version of a neighbourhood. A Monday morning shows you the daily one.\n\n"
       "▪ Sunday: how quiet is it, really?\n▪ Monday morning: how busy are the roads?\n▪ Weekday evening: noise, traffic, parking\n▪ Talk to a shopkeeper nearby\n\n"
       "Decide after both.\n\n\U0001F4E4 Share with someone viewing flats this weekend.",
       (B, "#SiteVisit", "#Kharadi", "#UpperKharadi", "#Wagholi"),
       f"No local facts. {GENERAL}."),
    _e("local-evening-walk", "local", "LOCAL LIFE", "Take an evening walk around the building before you book",
       ["Are the footpaths usable?", "Is it lit and does it feel safe?", "Can you find tea, groceries and a chemist?", "Would you be comfortable walking it after dark?",
        "Go at the hour you will actually be home"],
       "\U0001F306 An evening walk before you book\n\nGo around the building at the hour you will actually be home.\n\n"
       "▪ Are the footpaths usable?\n▪ Is it well lit?\n▪ Can you find tea, groceries and a chemist?\n▪ Would you be comfortable there after dark?\n\n"
       "Thirty minutes tells you more than a brochure.\n\n\U0001F4AC What do you look for on an evening walk?",
       (B, "#NeighbourhoodGuide", "#PuneHomes", "#UpperKharadi", "#Kharadi"),
       f"No local facts. {GENERAL}."),

    # ---------------------------------------------------------------- agent pitch
    _e("agent-consistent-posting", "agent", "FOR PUNE AGENTS", "Posting regularly is hard when you are busy showing flats",
       ["Post a property from your phone", "Ready-made posts for Facebook, Instagram and WhatsApp", "Your own website is ready", "Free, invite-only pilot"],
       "\U0001F91D Property agent in Pune?\n\nPosting regularly is hard when you are busy showing flats.\n\n"
       "✅ Post a property from your phone\n✅ Get ready-made posts for Facebook, Instagram and WhatsApp\n✅ Your own website is ready\n\n"
       "The pilot is free and invite-only. \U0001F4E4 Know an agent who would like this? Share this post.",
       (B, "#RealEstateAgent", "#PuneAgents", "#PuneRealEstate"),
       "Claims mirror the published brand posts (agents, agents-problem). No pricing or result claims. Pilot is free and invite-only per existing brand copy.",
       link="/request-invite"),
    _e("agent-buyer-summary", "agent", "FOR PUNE AGENTS", "Which enquiry is serious? A summary for each buyer",
       ["Comments like INTERESTED are answered for you", "Each buyer summarised: budget, BHK, timing", "How warm they are, at a glance", "Free, invite-only pilot"],
       "\U0001F4CA Which enquiry is serious?\n\nWhen enquiries arrive as comments and messages, it is hard to tell who is ready.\n\n"
       "✅ Comments like INTERESTED are answered for you\n✅ Each buyer summarised: budget, BHK and timing\n✅ How warm they are, at a glance\n\n"
       "Free, invite-only pilot. \U0001F4AC Agents: what is your biggest enquiry headache?",
       (B, "#RealEstateAgent", "#PuneAgents", "#PuneRealEstate"),
       "Claims mirror published brand post agents-problem. No result claims.",
       link="/request-invite"),
    _e("agent-hindi", "agent", "पुणे के एजेंट्स के लिए", "एक प्रॉपर्टी दीजिए, पूरा मार्केटिंग कैंपेन पाइए",
       ["मोबाइल से प्रॉपर्टी डालें, वेबसाइट अपने-आप तैयार", "फेसबुक, इंस्टाग्राम और व्हाट्सऐप के लिए तैयार पोस्ट", "कमेंट में INTERESTED लिखने वालों को जवाब",
        "हर खरीदार का सार: बजट, BHK, समय, कितना गंभीर"],
       "\U0001F91D पुणे के प्रॉपर्टी एजेंट, एक सवाल: पूछताछ करने वाले कितने खरीदार कमेंट में खो जाते हैं?\n\n"
       "✅ मोबाइल से प्रॉपर्टी डालें, आपकी अपनी वेबसाइट अपने-आप तैयार\n✅ फेसबुक, इंस्टाग्राम और व्हाट्सऐप के लिए तैयार पोस्ट\n"
       "✅ हर खरीदार का सार: बजट, BHK और समय\n\n"
       "पायलट मुफ़्त है और सिर्फ़ इन्विटेशन से। किसी एजेंट दोस्त को यह पोस्ट शेयर करें।",
       (B, "#PuneAgents", "#RealEstateAgent", "#PuneRealEstate"),
       "Hindi text adapted from the already-published brand post agents-hindi; have a Hindi reader approve before seeding. Card is the pre-rendered Chrome card (Pillow cannot shape Devanagari).",
       link="/request-invite", cta_ig="इन्विटेशन के लिए बायो में दिया लिंक (link in our bio) देखें।", card_from="agents-hindi"),
    _e("agent-marathi", "agent", "पुण्यातील एजंट्ससाठी", "एक प्रॉपर्टी द्या, पूर्ण मार्केटिंग कॅम्पेन मिळवा",
       ["मोबाईलवरून प्रॉपर्टी टाका, वेबसाइट आपोआप तयार", "फेसबुक, इंस्टाग्राम आणि व्हॉट्सअ‍ॅपसाठी तयार पोस्ट", "कमेंटमध्ये INTERESTED लिहिणाऱ्यांना उत्तर",
        "प्रत्येक खरेदीदाराचा सारांश: बजेट, BHK, वेळ, किती गंभीर"],
       "\U0001F91D पुण्यातील प्रॉपर्टी एजंट, एक प्रश्न: चौकशी करणाऱ्या खरेदीदारांपैकी किती जण कमेंटमध्ये हरवून जातात?\n\n"
       "✅ मोबाईलवरून प्रॉपर्टी टाका, तुमची स्वतःची वेबसाइट आपोआप तयार\n✅ फेसबुक, इंस्टाग्राम आणि व्हॉट्सअ‍ॅपसाठी तयार पोस्ट\n"
       "✅ प्रत्येक खरेदीदाराचा सारांश: बजेट, BHK आणि वेळ\n\n"
       "पायलट मोफत आहे आणि फक्त आमंत्रणाने. एखाद्या एजंट मित्राला हे पोस्ट शेअर करा.",
       (B, "#PuneAgents", "#RealEstateAgent", "#PuneRealEstate"),
       "Marathi text adapted from the already-published brand post agents-marathi; have a Marathi reader approve before seeding. Card is the pre-rendered Chrome card.",
       link="/request-invite", cta_ig="आमंत्रणासाठी बायोमधील लिंक (link in our bio) पाहा.", card_from="agents-marathi"),
]

BY_SLUG: Dict[str, Entry] = {e.slug: e for e in ENTRIES}
