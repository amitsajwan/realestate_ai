"""The brain of every 1:1 chat away from the website (Messenger, Instagram, WhatsApp), 2026-10-18: who is writing and what they ask, read with
where they came from; then the answer from the knowledge that fits. An agent gets our service for agents; a question about a post, guide or
project gets that post's own facts and reply sheet (as a comment would); only someone looking for a home goes through the buyer conversation
(chat/agent.py). The service using it provides db, llm, and `trial_line` (how an agent starts the free trial on that channel)."""
import logging
import re
from typing import Optional

from app.core import keywords
from app.modules.engage.config import quiet_topic

from . import adapters, check_flow, lang as L

log = logging.getLogger(__name__)

WHO = ("buyer", "agent", "seller", "other")
NEEDS = ("question", "homes", "person", "greeting", "complaint", "spam", "other")
UNDERSTAND = f"""You read one message sent to {adapters.brand_name()} on Facebook Messenger, Instagram or WhatsApp. {adapters.brand_name()} posts about homes
in Pune, guides (government housing schemes such as the MHADA lottery, buying tips, area news) and offers a service to real estate agents.
Use WHERE THEY CAME FROM and the CONVERSATION to understand short or unclear messages ("is it in Nashik?" after a MHADA post asks about MHADA).

Return ONE JSON object: {{"who": one of {list(WHO)}, "need": one of {list(NEEDS)}, "about": "what they ask about, in a few English words"}}
who: agent = a real estate agent, broker or builder's sales person, or anyone asking how to list properties, join, get leads or the free trial;
     seller = wants to sell or rent out their own property; buyer = looking for a home to buy or rent, or asking as a home seeker; other = anything else
     (someone asking about a scheme or a post is "other" unless they say they want a home).
need: question = asks for information (a scheme, the post, a project, a home, an area, prices, the process); homes = wants homes or options, or
     gives what they want (area, BHK, budget); person = wants a call or a person; greeting = hello, thanks; complaint = unhappy, rude or says
     fraud; spam = ads, links, nonsense; other = anything else."""
TRIAL_LINE = {
    "en": "Free trial for agents, 1 month free: {url}",
    "hi": "एजेंट्स के लिए फ्री ट्रायल, 1 महीना फ्री: {url}",
    "hinglish": "Agents ke liye free trial, 1 mahina free: {url}",
    "mr": "एजंटसाठी फ्री ट्रायल, 1 महिना फ्री: {url}",
    "mr_latn": "Agents sathi free trial, 1 mahina free: {url}",
}
SHARED_ASK = ("(They shared this post with us without writing anything.) What is this post about? Say it in one or two sentences, "
              "then ask what they would like to know.")
LOAN = re.compile(r"\b(home\s*loan|loan|emi)\b|लोन|कर्ज|ऋण", re.I)
LOAN_TEXT = {
    "en": "We do not give loans. Your bank decides the loan amount from your income and documents; for a home you like, the agent can tell you which banks work with that project.",
    "hi": "हम लोन नहीं देते। लोन कितना मिलेगा, यह आपका बैंक आपकी आय और दस्तावेज़ देखकर तय करता है; जो घर आपको पसंद आए, उसके लिए एजेंट बता सकते हैं कि कौन से बैंक उस प्रोजेक्ट के साथ काम करते हैं।",
    "hinglish": "Hum loan nahi dete. Loan kitna milega, yeh aapka bank aapki income aur documents dekh kar tay karta hai; jo ghar pasand aaye, uske liye agent bata sakte hain ki kaun se bank us project ke saath kaam karte hain.",
    "mr": "आम्ही कर्ज देत नाही. किती कर्ज मिळेल हे तुमची बँक तुमचे उत्पन्न आणि कागदपत्रे पाहून ठरवते; आवडलेल्या घरासाठी कोणत्या बँका त्या प्रोजेक्टसोबत काम करतात हे एजंट सांगू शकतात.",
    "mr_latn": "Aamhi loan det nahi. Kiti loan milel he tumchi bank tumche income ani documents baghun tharavte; avadlelya gharasathi konatya bank tya project sobat kaam kartat he agent sangu shaktat.",
}
NOT_IN_POST = {
    "en": "Our post does not cover that. I have asked our team, and they will reply here.",
    "hi": "यह जानकारी हमारी पोस्ट में नहीं है। मैंने हमारी टीम से पूछा है, वे यहीं जवाब देंगे।",
    "hinglish": "Yeh jaankari hamari post mein nahi hai. Maine hamari team se poocha hai, woh yahin reply karenge.",
    "mr": "ही माहिती आमच्या पोस्टमध्ये नाही. मी आमच्या टीमला विचारले आहे, ते इथेच उत्तर देतील.",
    "mr_latn": "Hi mahiti aamchya post madhe nahi. Mi aamchya team la vicharle aahe, te ithech uttar detil.",
}
QUIET = {   # a topic the bot must not answer (MHADA, owner 2026-10-20): never a figure or a date, only who to ask; the team is told
    "en": "We are not MHADA and we never take any payment. For your application or payment, please check only with MHADA's official website or office. Our team will read your message.",
    "hi": "हम MHADA नहीं हैं और कोई भी पैसा नहीं लेते। अपने आवेदन या पेमेंट के लिए सिर्फ MHADA की ऑफिशियल वेबसाइट या ऑफिस से ही पूछें। हमारी टीम आपका मैसेज पढ़ेगी।",
    "hinglish": "Hum MHADA nahi hain aur koi bhi paisa nahi lete. Apne application ya payment ke liye sirf MHADA ki official website ya office se hi poochhein. Hamari team aapka message padhegi.",
    "mr": "आम्ही MHADA नाही आणि कोणतेही पैसे घेत नाही. तुमच्या अर्ज किंवा पेमेंटसाठी फक्त MHADA ची अधिकृत वेबसाइट किंवा ऑफिसकडेच चौकशी करा. आमची टीम तुमचा मेसेज वाचेल.",
    "mr_latn": "Aamhi MHADA nahi ani konatehi paise ghet nahi. Tumchya arj kinva payment sathi fakt MHADA chi adhikrut website kinva office kadech chaukashi kara. Aamchi team tumcha message vachel.",
}
GONE = {
    "en": "“{title}” is no longer listed. Here is what I can find for you instead.",
    "hi": "“{title}” अब लिस्टेड नहीं है। इसकी जगह मैं आपके लिए और घर ढूँढ सकता हूँ।",
    "hinglish": "“{title}” ab listed nahi hai. Iski jagah main aapke liye aur ghar dhoondh sakta hoon.",
    "mr": "“{title}” आता लिस्टेड नाही. त्याऐवजी मी तुमच्यासाठी दुसरी घरे शोधू शकतो.",
    "mr_latn": "“{title}” aata listed nahi. Tyaaivaji mi tumchyasathi dusri ghare shodhu shakto.",
}
SELLER = {
    "en": "Thanks! Selling or renting out is handled by our agents. Please share your area, the home's size and your mobile number, and an agent will call you.",
    "hi": "धन्यवाद! बेचने या किराये पर देने का काम हमारे एजेंट करते हैं। अपना एरिया, घर का साइज़ और मोबाइल नंबर भेजें, एजेंट आपको कॉल करेंगे।",
    "hinglish": "Thanks! Bechne ya rent pe dene ka kaam hamare agents karte hain. Apna area, ghar ka size aur mobile number bhejein, agent aapko call karenge.",
    "mr": "धन्यवाद! विक्री किंवा भाड्याने देण्याचे काम आमचे एजंट करतात. तुमचा एरिया, घराचा साइज आणि मोबाईल नंबर पाठवा, एजंट तुम्हाला कॉल करतील.",
    "mr_latn": "Dhanyavad! Vikri kiva bhadyane denyache kaam aamche agent kartat. Tumcha area, gharacha size ani mobile number pathva, agent tumhala call kartil.",
}

# A message that is a post's code alone, or with "interested / info / price list" (the text Facebook's wa.me link fills in, what our captions
# and comment replies tell people to send), gets that post's price lines and page at once, taken from the post's facts, never written by the
# model (2026-10-20: the bare code got no answer and "price list please" was told to go and comment INFO)
CODE_FILLER = re.compile(r"\b(?:hi+|hello|hey|namaste|namaskar|i|am|im|interested|intrested|in|info|details?|prices?|list|sheet|floor|plans?|"
                         r"please|pls|plz|send|me|the|and|of|for|code|want|share)\b|[^\w\s]", re.I)
CARD_FACT = re.compile(r"₹|\bBHK\b|payment plan|possession|MahaRERA|price", re.I)
CARD_NOT_PRICE = re.compile(r"\bloan\b|\bemi\b|a month|per month|/month|% for \d+ years", re.I)   # an EMI post is not a price list
CARD_CAUTION = re.compile(r"before you book|confirm|today's price", re.I)   # a line without a figure is kept only as the price caution
CARD_MAX_FACTS = 12
WHICH_PROJECT = {   # a word two live projects share
    "en": "Which project do you mean: {names}? Reply with its name.",
    "hi": "आप कौन सा प्रोजेक्ट पूछ रहे हैं: {names}? उसका नाम लिखें।",
    "hinglish": "Aap kaunsa project pooch rahe hain: {names}? Uska naam likhein.",
    "mr": "तुम्ही कोणता प्रोजेक्ट विचारत आहात: {names}? त्याचे नाव लिहा.",
    "mr_latn": "Tumhi konta project vicharat aahat: {names}? Tyache nav liha.",
}
CARD_PAGE = {
    "en": "Full details and pictures: {page}",
    "hi": "पूरी जानकारी और फोटो: {page}",
    "hinglish": "Poori jaankari aur photos: {page}",
    "mr": "संपूर्ण माहिती आणि फोटो: {page}",
    "mr_latn": "Sampurna mahiti ani photos: {page}",
}
CARD_PLANS = {   # no page of ours carries a project's floor plans yet: a person sends them, and the team is told (needs_human)
    "en": "Floor plans: our team will send them here shortly.",
    "hi": "फ्लोर प्लान: हमारी टीम जल्द ही यहीं भेजेगी।",
    "hinglish": "Floor plans: hamari team jald hi yahin bhejegi.",
    "mr": "फ्लोअर प्लॅन: आमची टीम लवकरच इथेच पाठवेल.",
    "mr_latn": "Floor plans: aamchi team lavkarach ithech pathvel.",
}
CARD_END = {
    "en": "Ask me anything about it here, or reply VISIT to book a site visit.",
    "hi": "इसके बारे में कुछ भी यहीं पूछें, या साइट विज़िट के लिए VISIT लिखें।",
    "hinglish": "Iske baare mein kuch bhi yahin poochhein, ya site visit ke liye VISIT likhein.",
    "mr": "याबद्दल काहीही इथेच विचारा, किंवा साइट व्हिजिटसाठी VISIT लिहा.",
    "mr_latn": "Yabaddal kahihi ithech vichara, kiva site visit sathi VISIT liha.",
}


def card_facts(facts) -> list:
    """The lines of a post a buyer asking for its price list wants: prices, configurations, payment plan, possession, MahaRERA."""
    out = []
    for f in facts or []:
        f = (f or "").strip()
        if f and len(f) <= 200 and CARD_FACT.search(f) and not CARD_NOT_PRICE.search(f) and (re.search(r"\d", f) or CARD_CAUTION.search(f)) \
                and f not in out:
            out.append(f)
    return out[:CARD_MAX_FACTS] if any("₹" in f for f in out) else []


def _once(text: str) -> str:
    """'…aapka budget kya hai? Aapka budget kya hai?' -> said once."""
    seen, lines = set(), []
    for line in text.split("\n"):   # lines stay lines (home cards are one per line)
        kept = []
        for part in re.split(r"(?<=[.!?।])\s+", line):
            sig = " ".join(re.sub(r"\W+", " ", part.lower()).split()[-4:])
            if sig and sig in seen and part.rstrip().endswith("?"):
                continue
            if sig:
                seen.add(sig)
            kept.append(part)
        if kept or not line:
            lines.append(" ".join(kept))
    return "\n".join(lines)


class ChatBrain:
    trial_line = None   # {lang: text with {url}}; None: the link line (TRIAL_LINE)

    async def _answer(self, conv: dict, text: str, lang: str) -> str:
        """Who is writing and what they ask, read with where they came from; then the answer from the knowledge that fits:
        an agent gets our service for agents, a question about a post, guide or project gets that post's own answer sheet (as a comment
        would), and only someone looking for a home goes through the buyer conversation."""
        data = conv["data"]
        checked = await check_flow.turn(self.db, conv, text, lang)   # "check my project's status" (docs/plan/project-check.md)
        if checked is not None:
            return checked
        code = (conv.get("context") or {}).get("code")
        named = None
        if not (code and re.search(rf"\b{re.escape(code)}\b", text, re.I)) and not adapters.codes_in(text):
            # a project's word ('IVARA', what Instagram captions and replies ask for): as if they had sent its newest post's code
            found = await keywords.listings_named_in(self.db, text)
            if len(found) > 1:
                return L.pick(WHICH_PROJECT, lang, names=" / ".join(keywords.full_word(keywords.project_name(d)) for d in found))
            ctx = await adapters.listing_word_context(self.db, found[0]) if found else None
            if ctx:
                conv["context"], named, code = ctx, found[0], ctx["code"]
                if ctx.get("agent_id") and conv.get("routed_by") in (None, "owner"):
                    conv["agent_id"], conv["routed_by"] = ctx["agent_id"], "project_word"
        if code and (named or re.search(rf"\b{re.escape(code)}\b", text, re.I)):
            rest = keywords.without_word(text, named) if named else re.sub(rf"\b{re.escape(code)}\b", " ", text, flags=re.I)
            # the website's WhatsApp button fills in "Hi, I am interested in <title> (ref <code>)" (WhatsAppButton.waText)
            prefilled = re.search(rf"\binterested in\b.*\(ref\s+{re.escape(code)}\)", text, re.I | re.S)
            if prefilled:
                rest = text[:prefilled.start()] + text[prefilled.end():]
            if not CODE_FILLER.sub(" ", rest).strip() and code not in (conv.get("cards") or []):
                card = await self._post_card(conv, lang)
                if card:
                    return card
            # read without the code (a bare code once looked like spam and got no reply); a post without prices (a guide) is told in
            # a sentence or two with its page, instead of the buyer questions ("which area?") an "I am interested" alone would get
            if not named:   # a question naming the project keeps the name ("is camelot near the metro?")
                text = rest.strip(" -:,") if CODE_FILLER.sub(" ", rest).strip() else SHARED_ASK
            elif not CODE_FILLER.sub(" ", rest).strip():
                text = SHARED_ASK
        u = await self._understand(conv, text)
        who, need = (u or {}).get("who"), (u or {}).get("need")
        if who in ("agent", "seller") and not conv.get("role"):
            conv["role"] = who
        elif who == "buyer" and conv.get("role") == "seller":
            conv["role"] = None
        if conv.get("role") == "agent":
            return await self._agent_answer(conv, text)
        if conv.get("role") == "seller" and need not in ("homes",):
            data["needs_human"] = True
            return L.pick(SELLER, adapters.detect_language(text))
        if need == "spam":
            return ""
        ctx = conv.get("context") or {}
        if quiet_topic(text, ctx.get("slug"), ctx.get("came_from"), (u or {}).get("about")):
            data["needs_human"] = True
            data.setdefault("questions", []).append(text[:200])
            return L.pick(QUIET, adapters.detect_language(text))
        if LOAN.search(text) and need in ("question", "other", None):
            return L.pick(LOAN_TEXT, adapters.detect_language(text))
        ctx = conv.get("context") or {}
        if need in ("question", "other", None) and ctx.get("kind") != "listing":
            groundings = await self._topic_groundings(conv, text)
            for g in groundings:  # the post they came from first, then our other posts on it: the first that answers
                said = await adapters.facts_reply(text, g, lang, self.llm, self._history(conv))
                if said:
                    return self._grounded_text(conv, g, said, True)
            if groundings:  # none answered: the rules' answer when it is sure, else plainly that we will find out
                r = await adapters.grounded_answer(text, groundings[0], self.llm)
                said = r.text if r.confident else L.pick(NOT_IN_POST, adapters.detect_language(text))
                return self._grounded_text(conv, groundings[0], said, r.confident, text)
        return await self._buyer_answer(conv, text, lang)

    @staticmethod
    def _history(conv: dict) -> str:
        return "\n".join(f"{'Person' if x['role'] == 'user' else 'Us'}: {x['text'][:300]}" for x in (conv.get("messages") or [])[-8:])

    async def _understand(self, conv: dict, text: str) -> Optional[dict]:
        if self.llm is None or not hasattr(self.llm, "json"):
            return None
        ctx = conv.get("context") or {}
        history = "\n".join(f"{'Person' if x['role'] == 'user' else 'Us'}: {x['text'][:300]}" for x in (conv.get("messages") or [])[-8:])
        try:
            u = await self.llm.json(UNDERSTAND, f"WHERE THEY CAME FROM: {ctx.get('came_from') or 'they wrote to us directly'}\n"
                                                f"WHAT WE KNOW: {conv.get('role') or 'nothing yet'}\nCONVERSATION:\n{history or '(first message)'}\n\n"
                                                f"MESSAGE:\n{text[:600]}")
        except Exception as e:
            log.info("dm: understand failed: %s", self._clean(type(e).__name__))
            return None
        if not isinstance(u, dict) or u.get("who") not in WHO or u.get("need") not in NEEDS:
            return None
        conv["last_understood"] = {k: u.get(k) for k in ("who", "need", "about")}
        return u

    async def _topic_groundings(self, conv: dict, text: str) -> list:
        """What a question may be answered from, best first: the post or link they came from, a project they name, our guide post on it."""
        ctx = conv.get("context") or {}
        out, seen = [], set()
        if ctx.get("kind") in ("calendar", "post", "project"):
            g = await adapters.grounding_for(self.db, ctx, None)
            if g is not None:
                out.append(g)
                seen.update(x for x in (ctx.get("ref"), ctx.get("slug")) if x)
        earlier = " ".join(x["text"] for x in (conv.get("messages") or [])[-4:] if x["role"] == "user")
        for found in (await adapters.project_for(self.db, text), await adapters.guide_for(self.db, text, earlier, exclude=seen)):
            if found and found["ref"] not in seen and found.get("slug") not in seen:
                g = await adapters.grounding_for(self.db, found, None)
                if g is not None:
                    seen.update(x for x in (found["ref"], found.get("slug")) if x)
                    out.append(g)
                    if not ctx.get("kind"):
                        conv["context"] = ctx = {**found, "came_from": ctx.get("came_from") or found["came_from"]}
        return out

    async def _post_card(self, conv: dict, lang: str) -> Optional[str]:
        """The price lines of the post behind the code, its page, and who sends the floor plans; None for a post without prices (a guide),
        which the normal answer handles. Once per code per chat."""
        ctx = conv.get("context") or {}
        g = await adapters.grounding_for(self.db, ctx, None)
        lines = card_facts(g.facts) if g is not None else []
        title = (ctx.get("title") or "").strip()
        for other in await adapters.listing_posts_groundings(self.db, ctx):   # a reel's caption has one price; its listing post has them all
            more = card_facts(other.facts)
            if sum("₹" in x for x in more) > sum("₹" in x for x in lines) or \
                    (more and getattr(other, "subject", "").endswith("-listing") and sum("₹" in x for x in more) == sum("₹" in x for x in lines)):
                g, lines, title = other, more, ""   # the listing post's own headline leads, not the reel's hook
        if not lines:
            return None
        out = [title] if title and not lines[0].startswith(title[:24]) else []
        out += [lines[0]] + [ln if ln.startswith("•") else f"• {ln}" for ln in lines[1:]]
        page = g.links.get("page") if isinstance(g.links, dict) else ""
        if page:
            out.append(L.pick(CARD_PAGE, lang, page=page))
            conv["page_sent"] = True
        out.append(L.pick(CARD_PLANS, lang))
        data = conv["data"]
        data["needs_human"] = True   # the team is told to send the floor plans (WhatsApp service: whatsapp_needs_you)
        data.setdefault("questions", []).append(f"Send the floor plans of {title or 'this project'}"[:200])
        out.append(L.pick(CARD_END, lang))
        conv.setdefault("cards", []).append(ctx["code"])
        return "\n".join(out)

    def _grounded_text(self, conv: dict, g, reply: str, confident: bool, question: str = "") -> str:
        """An answer from a post's, project's or guide's facts, in the person's language; one we could not answer tells the team."""
        data = conv["data"]
        if not confident:
            data["needs_human"] = True
            data.setdefault("questions", []).append(question[:200])
        page = g.links.get("page") if isinstance(g.links, dict) else ""
        if page and page not in reply and not conv.get("page_sent"):
            conv["page_sent"] = True   # the page link once per chat
            return f"{reply}\n{page}"
        return reply

    async def _agent_answer(self, conv: dict, text: str) -> str:
        g = adapters.agents_grounding()
        lang = adapters.detect_language(text)
        out = await adapters.facts_reply(text, g, lang, self.llm, self._history(conv))
        confident = bool(out)
        if not out:
            r = await adapters.grounded_answer(text, g, self.llm)
            out, confident = r.text, r.confident
        if not conv.get("trial_sent") and adapters.trial_url():
            conv["trial_sent"] = True
            out = f"{out}\n\n{L.pick(self.trial_line or TRIAL_LINE, lang, url=adapters.trial_url())}"
        if not confident:
            conv["data"]["needs_human"] = True
        return out

    async def _buyer_answer(self, conv: dict, text: str, lang: str) -> str:
        data = conv["data"]
        data["localise"], data["lang"] = True, lang   # the model writes in their language, not English to be translated
        ctx = conv.get("context") or {}
        gone = ""
        if ctx.get("listing_id") and not ctx.get("listing_read"):
            ctx["listing_read"] = True
            state = await adapters.listing_state(self.db, ctx["listing_id"])
            if state.get("tx") and not data.get("tx"):
                data["tx"] = state["tx"]
            if state.get("locality") and not data.get("locality"):
                data["locality"], data["locality_src"] = state["locality"], "listing"
            if state.get("bhk") and not data.get("bhk"):
                data["bhk"], data["bhk_src"] = float(state["bhk"]), "listing"
            if not state.get("live"):
                gone = L.pick(GONE, lang, title=ctx.get("title") or "")
                await adapters.prefill_from_title(data, ctx.get("title") or "")
        grounding = await adapters.grounding_for(self.db, conv.get("context"), data.get("locality"))
        if grounding is not None and getattr(grounding, "locality", None) and not data.get("locality") and ctx.get("kind") == "project":
            data["locality"], data["locality_src"] = grounding.locality, "project"
        t = await adapters.chat_turn(data, text, self.llm, grounding, finder=await adapters.homes_finder(self.db, conv.get("agent_id")),
                                    history=conv.get("messages") or [])
        # the homes sit between what we found and what we ask next, as on the website; the links are never translated
        parts = [await self._say(t.reply, lang), adapters.card_lines(t.cards), await self._say(t.follow_up, lang) if t.follow_up else ""]
        reply = _once("\n".join(p for p in [gone] + parts if p))
        opts = L.options_line([q for q in t.quick if q and "whatsapp" not in q.lower()], lang)
        return f"{reply}\n{opts}" if opts else reply

    async def _say(self, body: str, lang: str) -> str:
        reply, english_left = L.localise_fixed(body, lang)
        if english_left and self.llm is not None:
            translated = await adapters.translate(body, lang, self.llm)
            if translated != body:
                reply = translated
        return reply
