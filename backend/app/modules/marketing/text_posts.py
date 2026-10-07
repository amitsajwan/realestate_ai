"""Text-first posts for the Page: one idea, a question that invites comments, and (usually) a link that unfolds into a preview card.
Only stable, checkable statements: no prices, no predictions, transport is 'approved is not running'. Nothing here contains a phone number."""
from app.core import brand
from typing import Dict, List

SITE = brand.SITE
TAGS = "#Pune " + brand.HASHTAG + " #PuneRealEstate"

TEXT_POSTS: List[Dict] = [
    {
        "slug": "pick-your-area", "link": f"{SITE}/localities",
        "text": (
            "Which area would you pick for a 2 BHK? \U0001F914\n\n"
            "1️⃣ Kharadi: closest to the big office campuses\n"
            "2️⃣ Upper Kharadi: newer projects, a short hop from Kharadi\n"
            "3️⃣ Wagholi: often more space for the budget, longer commute\n\n"
            "Comment 1, 2 or 3 and your budget range. We will share what to check for your pick.\n\n"
            "\U0001F449 Area guides: {link}\n\n#Kharadi #UpperKharadi #Wagholi " + TAGS),
    },
    {
        "slug": "metro-myth", "link": f"{SITE}/insights/metro-kharadi-wagholi-approved-not-running",
        "text": (
            "\U0001F687 A metro line on the plan is not a metro you can ride. Here is why that matters before you pay more \U0001F447\n\n"
            "Myth: a metro line on the plan means I should pay more for a flat near it.\n"
            "Fact: approved is not the same as running. Lines take years to build, so judge a flat on how you would live in it if the metro arrives late.\n\n"
            "Did a planned metro ever change how you picked a home? Tell us in the comments.\n\n"
            "What is approved today, with official sources: {link}\n\n#PuneMetro " + TAGS),
    },
    {
        "slug": "ask-the-builder", "link": f"{SITE}/insights/site-visit-checklist-upper-kharadi-wagholi",
        "text": (
            "5 questions to ask a builder before you book \U0001F4DD\n\n"
            "1. What is the RERA number, and what possession date is on it?\n"
            "2. What is the carpet area in the agreement?\n"
            "3. What does the full cost sheet include: parking, maintenance deposit, GST, stamp duty, registration?\n"
            "4. Can I visit a finished project of yours?\n"
            "5. Where does the water come from, and what does the power backup cover?\n\n"
            "Save this for your next site visit. The full checklist: {link}\n\n" + TAGS),
    },
    {
        "slug": "ready-or-uc", "link": "",
        "text": (
            "Ready-to-move or under construction? \U0001F3E0\n\n"
            "\U0001F44D Ready-to-move: I want to see exactly what I buy\n"
            "\U0001F62E Under construction: I am happy to wait for a lower entry price\n\n"
            "React with one and tell us why in the comments. If you are looking in Kharadi, Upper Kharadi or Wagholi, comment INTERESTED and we will share what to check.\n\n" + TAGS),
    },
    {
        "slug": "carpet-in-30-seconds", "link": f"{SITE}/insights/kharadi-upper-kharadi-wagholi",
        "text": (
            "Carpet vs built-up, in 30 seconds \U0001F4D0\n\n"
            "Carpet: the floor you actually use, wall to wall.\n"
            "Built-up: carpet plus walls and balcony.\n"
            "Super built-up: built-up plus your share of common areas.\n\n"
            "Compare two flats by the price per sq ft of CARPET area, so you compare like with like.\n\n"
            "Did a builder ever quote you super built-up when you expected carpet? Tell us in the comments.\n\n"
            "More buying guides for east Pune: {link}\n\n" + TAGS),
    },
    {
        "slug": "agents-week", "link": f"{SITE}/request-invite",
        "text": (
            "Pune property agents: what eats most of your week? \U0001F91D\n\n"
            "1️⃣ Making posts and photos\n"
            "2️⃣ Answering the same questions again and again\n"
            "3️⃣ Finding out who is serious\n"
            "4️⃣ Following up\n\n"
            "Comment your number. We are building " + brand.NAME + " to take these off your plate. Claim your free trial (your first 3 properties free): {link}\n\n#PuneAgents " + TAGS),
    },
]
