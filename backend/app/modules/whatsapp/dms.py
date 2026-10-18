"""Messenger and Instagram DM assistant: the WhatsApp assistant's brain on the Page's own inboxes. One incoming message in, at most one reply
out (free, inside the 24-hour window the buyer opened).

Collections
  dm_messages       _id = Meta message id (inbound, the idempotency key) or out-<uuid> (outbound, saved before sending; message_id
                    is Meta's id once sent)
  dm_conversations  _id = "<platform>:<sender id>" (platform = messenger | instagram): agent, engine state, last 20 messages, opt-out, lead id,
                    human_until (a person replied from the Page inbox: the assistant stays quiet until then)

Rules
  - Routing: the lead this sender already has (the comment assistant's private reply, or an earlier DM) > an interest code in the text > the
    owner agent.
  - Answers come from the website chat engine and grounded knowledge, in the buyer's language; the engine asks for the number with its consent line.
  - A lead from the first message (no number yet); the number and requirement are added as the buyer gives them.
  - A person replying from the Page inbox (an echo without our BOT_TAG) pauses the assistant in that chat for MESSENGER_HUMAN_PAUSE_HOURS.
  - STOP / START as on WhatsApp. Replies only inside 24 hours of the buyer's last message. Dry run records the reply and sends nothing.
"""
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Callable, Optional

from . import adapters, lang as L
from .dm_config import DmConfig
from .dm_graph import BOT_TAG, DmGraphError
from .service import MAX_KEPT, MAX_REPLIES_PER_HOUR, MAX_TEXT, START_RX, STOP_RX, WINDOW

log = logging.getLogger(__name__)

PLATFORMS = ("messenger", "instagram")
OURS_WINDOW = timedelta(minutes=10)   # an echo of a reply we sent this recently, with the same text, is ours even without the tag

NOTICE = {
    "en": "Note: {agent} may also reply to you here. Reply STOP at any time and we will not message you again.",
    "hi": "सूचना: {agent} भी आपको यहाँ जवाब दे सकते हैं। संदेश बंद करवाने के लिए कभी भी STOP लिखें।",
    "hinglish": "Note: {agent} bhi aapko yahan reply kar sakte hain. Messages band karne ke liye kabhi bhi STOP likhein.",
    "mr": "सूचना: {agent} सुद्धा तुम्हाला इथे उत्तर देऊ शकतात. मेसेज बंद करण्यासाठी कधीही STOP लिहा.",
    "mr_latn": "Note: {agent} suddha tumhala ithe uttar deu shaktat. Message band karnyasathi kadhihi STOP liha.",
}


WHO = ("buyer", "agent", "seller", "other")
NEEDS = ("question", "homes", "person", "greeting", "complaint", "spam", "other")
UNDERSTAND = f"""You read one message sent to {adapters.brand_name()} on Facebook Messenger or Instagram. {adapters.brand_name()} posts about homes
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


def _ts(ms) -> Optional[datetime]:
    try:
        return datetime.utcfromtimestamp(int(ms) / 1000)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def platform_of(obj: str) -> Optional[str]:
    return {"page": "messenger", "instagram": "instagram"}.get(obj or "")


def refs_of(ev: dict) -> dict:
    """Where the person came from, as Meta tells it: the ref of the link or ad they opened (m.me / ig.me ?ref=, click-to-message ads), the
    post, reel or story they shared or replied to (ids and links). Empty when the chat simply started."""
    msg, pb = ev.get("message") or {}, ev.get("postback") or {}
    referral = ev.get("referral") or msg.get("referral") or pb.get("referral") or {}
    out = {"ref": str(referral.get("ref") or "")[:64], "ad_id": str(referral.get("ad_id") or "")[:64], "media_ids": [], "urls": [],
           "reply_to_story": False}
    reply_to = msg.get("reply_to") or {}
    story = reply_to.get("story") or {}
    if story:
        out["reply_to_story"] = True
        out["media_ids"].append(str(story.get("id") or ""))
        out["urls"].append(str(story.get("url") or ""))
    for att in msg.get("attachments") or []:
        pay = att.get("payload") or {}
        for k in ("reel_video_id", "id", "media_id", "ig_post_media_id"):
            if pay.get(k):
                out["media_ids"].append(str(pay[k]))
        if pay.get("url"):
            out["urls"].append(str(pay["url"])[:500])
        if pay.get("title"):
            out["shared_title"] = str(pay["title"])[:200]
    out["media_ids"] = [x for x in out["media_ids"] if x][:5]
    out["urls"] = [x for x in out["urls"] if x][:5]
    return {k: v for k, v in out.items() if v}


def parse(ev: dict) -> dict:
    """One `messaging` event -> {kind: message | echo | other, mid, sender, recipient, text, media, ts, tag, refs}."""
    msg = ev.get("message") or {}
    pb = ev.get("postback") or {}
    sender = str((ev.get("sender") or {}).get("id") or "")
    recipient = str((ev.get("recipient") or {}).get("id") or "")
    refs = refs_of(ev)
    if msg:
        kind = "echo" if msg.get("is_echo") else "message"
        text = str(msg.get("text") or "")
        media = bool(msg.get("attachments")) and not text
        return {"kind": kind, "mid": str(msg.get("mid") or ""), "sender": sender, "recipient": recipient, "text": text[:1000],
                "media": media, "ts": _ts(ev.get("timestamp")), "tag": msg.get("metadata"), "refs": refs}
    if pb:  # a tapped button (ice breaker, persistent menu): its title is what the buyer "said"
        return {"kind": "message", "mid": str(pb.get("mid") or ""), "sender": sender, "recipient": recipient,
                "text": str(pb.get("title") or pb.get("payload") or "")[:1000], "media": False, "ts": _ts(ev.get("timestamp")), "tag": None,
                "refs": refs}
    if ev.get("referral"):  # opened the chat from a link or an ad without writing yet: remembered for their first message
        return {"kind": "referral", "mid": "", "sender": sender, "recipient": recipient, "text": "", "media": False, "ts": _ts(ev.get("timestamp")),
                "tag": None, "refs": refs}
    return {"kind": "other", "mid": "", "sender": sender, "recipient": recipient, "text": "", "media": False, "ts": None, "tag": None}


class DmService:
    def __init__(self, db, cfg: DmConfig, graph=None, llm=None, now: Callable[[], datetime] = datetime.utcnow):
        self.db, self.cfg, self.graph, self.llm, self.now = db, cfg, graph, llm, now
        self.messages = db.get_collection("dm_messages")
        self.convs = db.get_collection("dm_conversations")

    def _clean(self, text) -> str:
        from app.platform.meta_graph.publisher import sanitize
        return sanitize(text, self.cfg.secrets)

    def _ours(self, account_id: str) -> bool:
        return bool(account_id) and account_id in (self.cfg.page_id, self.cfg.ig_id)

    # ---- webhook intake (in the request: fast, no network) ------------------------------------------------------------
    async def claim(self, platform: str, m: dict) -> bool:
        """Store an inbound buyer message once. False for a retry Meta sent again, our own account, or a message with no id."""
        if m["kind"] != "message" or not m["mid"] or not m["sender"] or self._ours(m["sender"]):
            return False
        if await self.messages.find_one({"_id": m["mid"]}):
            return False
        try:
            await self.messages.insert_one({"_id": m["mid"], "direction": "in", "platform": platform, "sender": m["sender"],
                                            "text": m["text"], "ts": m["ts"] or self.now(), "received_at": self.now(), "status": "received"})
        except Exception:  # a duplicate key from a concurrent retry
            return False
        return True

    async def echo(self, platform: str, m: dict) -> bool:
        """A message the Page sent. Ours (tagged, or the reply we just sent) is ignored; anything else is a person answering from the Page
        inbox, so the assistant steps back in that chat. Returns True when it paused the chat."""
        buyer = m["recipient"]
        if not buyer or m["tag"] == BOT_TAG:
            return False
        now = self.now()
        if m["mid"] and await self.messages.find_one({"message_id": m["mid"], "direction": "out"}):
            return False
        # Instagram may not echo the tag, and the echo can arrive before the send call returns: our reply is saved before it is sent
        sent = await self.messages.find_one({"direction": "out", "recipient": buyer, "text": m["text"]})
        if sent and now - sent["ts"] < OURS_WINDOW:
            return False
        cid = f"{platform}:{buyer}"
        conv = await self.convs.find_one({"_id": cid})
        until = now + timedelta(hours=self.cfg.human_pause_hours)
        if conv:
            msgs = (conv.get("messages") or []) + [{"role": "agent", "text": m["text"] or "[attachment]", "ts": now}]
            await self.convs.update_one({"_id": cid}, {"$set": {"human_until": until, "messages": msgs[-MAX_KEPT:], "updated_at": now}})
        else:
            await self.convs.insert_one(self._new_conv(cid, platform, buyer, now) | {"human_until": until})
        return True

    async def remember_referral(self, platform: str, m: dict) -> None:
        """They opened the chat from a link or an ad and have not written yet: what they opened is kept for their first message."""
        if not m.get("sender") or self._ours(m["sender"]) or not m.get("refs"):
            return
        cid, now = f"{platform}:{m['sender']}", self.now()
        if await self.convs.find_one({"_id": cid}):
            await self.convs.update_one({"_id": cid}, {"$set": {"pending_refs": m["refs"], "origin_checked": False}})
        else:
            await self.convs.insert_one(self._new_conv(cid, platform, m["sender"], now) | {"pending_refs": m["refs"]})

    @staticmethod
    def _new_conv(cid: str, platform: str, sender: str, now: datetime) -> dict:
        from app.modules.chat import engine
        return {"_id": cid, "platform": platform, "sender": sender, "agent_id": None, "routed_by": None, "data": engine.new_data(),
                "messages": [], "created_at": now, "opted_out": False, "notice_sent_at": None, "lead_id": None, "context": None,
                "language": None, "needs_human_notified": False, "replies": [], "human_until": None}

    # ---- routing --------------------------------------------------------------------------------------------------------
    async def _route(self, conv: dict, text: str, now: datetime, refs: Optional[dict] = None) -> None:
        if refs or not conv.get("origin_checked"):
            # once per chat, and again whenever Meta says what they opened or shared: the post, reel, link or comment behind the chat
            conv["origin_checked"] = True
            origin = await adapters.dm_origin(self.db, conv["platform"], conv["sender"], refs)
            if origin:
                conv["context"] = origin
                if origin.get("listing_id") and conv.get("routed_by") in (None, "owner"):
                    listing_agent = await adapters.listing_agent(self.db, origin["listing_id"])
                    if listing_agent:
                        conv["agent_id"], conv["routed_by"] = listing_agent, "origin"
        if not conv.get("agent_id"):
            known = await adapters.find_dm_lead(self.db, conv["platform"], conv["sender"])
            if known:
                conv["agent_id"], conv["routed_by"], conv["lead_id"] = known.get("agent_id"), "lead", known["_id"]
        link = await adapters.find_interest_link(self.db, text) if text else None
        if link:
            conv["context"] = adapters.link_context(link, "wrote the code of")
            if conv.get("routed_by") in (None, "owner"):
                conv["agent_id"], conv["routed_by"] = adapters.interest_target_agent(link, self.cfg.owner_agent_id), "interest_code"
            await adapters.record_interest_event(self.db, link["code"], f"{conv['platform']}:{conv['sender']}", now)
        if not conv.get("agent_id"):
            conv["agent_id"], conv["routed_by"] = self.cfg.owner_agent_id or None, "owner"

    # ---- one message (background task) -------------------------------------------------------------------------------
    async def handle(self, platform: str, m: dict) -> dict:
        try:
            return await self._handle(platform, m)
        except Exception as e:
            log.error("dm: could not handle message: %s", self._clean(f"{type(e).__name__}: {e}"))
            if m.get("mid"):
                await self.messages.update_one({"_id": m["mid"]}, {"$set": {"status": "error", "error": self._clean(str(e))}})
            return {"status": "error"}

    async def _handle(self, platform: str, m: dict) -> dict:
        now = self.now()
        text = (m["text"] or "").strip()[:MAX_TEXT]
        cid = f"{platform}:{m['sender']}"
        conv = await self.convs.find_one({"_id": cid}) or self._new_conv(cid, platform, m["sender"], now)
        sent_at = m["ts"] or now
        last_in = conv.get("last_inbound_at")
        conv["last_inbound_at"] = max(sent_at, last_in) if last_in else sent_at
        refs, conv["pending_refs"] = m.get("refs") or conv.get("pending_refs"), None
        await self._route(conv, text, now, refs)
        lang = L.sticky(conv.get("language"), adapters.detect_language(text) if text else "en", text)
        conv["language"] = lang

        if text and STOP_RX.match(text):
            conv["opted_out"], conv["opted_out_at"] = True, now
            await adapters.mark_dm_opt_out(self.db, conv.get("lead_id"), True, now)
            return await self._finish(conv, m["mid"], L.pick(L.STOPPED, lang), "stopped", now, text)
        if conv.get("opted_out"):
            if text and START_RX.match(text):
                conv["opted_out"], conv["opted_out_at"] = False, None
                await adapters.mark_dm_opt_out(self.db, conv.get("lead_id"), False, now)
                return await self._finish(conv, m["mid"], L.pick(L.RESTARTED, lang), "restarted", now, text)
            return await self._finish(conv, m["mid"], None, "opted_out", now, text)

        human = conv.get("human_until") and conv["human_until"] > now
        reply = None
        if not human:
            shared = (m.get("refs") or {}).get("shared_title") or ""
            if (m["media"] or not text) and conv.get("context") and conv["context"].get("kind"):
                # they shared our post without a word: what it is about, then what they would like to know
                reply = await self._answer(conv, shared or SHARED_ASK, lang)
            else:
                reply = L.pick(L.MEDIA, lang) if (m["media"] or not text) else await self._answer(conv, text, lang)
        elif text:
            await self._answer(conv, text, lang)  # still learn the requirement and number for the lead; the person answers
        agent_id = conv.get("agent_id")
        if agent_id and conv.get("role") == "agent":
            if not conv.get("agent_notified"):
                conv["agent_notified"] = True
                label = adapters.DM_LABEL[conv["platform"]]
                await adapters.notify(self.db, agent_id, "dm_agent", f"An agent wrote on {label}: \"{(text or '')[:140]}\"",
                                      {"conversation_id": conv["_id"]}, now)
        elif agent_id:
            await self._lead(conv, agent_id, text or "[attachment]", now)
        else:
            log.warning("dm: no agent for this chat (set MESSENGER_OWNER_AGENT_ID); replying without saving a lead")
        if reply and agent_id and not conv.get("notice_sent_at"):
            reply = f"{reply}\n\n{L.pick(NOTICE, lang, agent=await adapters.agent_name(self.db, agent_id) or L.pick(L.TEAM, lang))}"
            conv["notice_sent_at"] = now
        return await self._finish(conv, m["mid"], reply, "answered" if reply else "human", now, text)

    async def _answer(self, conv: dict, text: str, lang: str) -> str:
        """Who is writing and what they ask, read with where they came from; then the answer from the knowledge that fits:
        an agent gets our service for agents, a question about a post, guide or project gets that post's own answer sheet (as a comment
        would), and only someone looking for a home goes through the buyer conversation."""
        data = conv["data"]
        u = await self._understand(conv, text)
        who, need = (u or {}).get("who"), (u or {}).get("need")
        if who in ("agent", "seller") and not conv.get("role"):
            conv["role"] = who
        elif who == "buyer" and conv.get("role") == "seller":
            conv["role"] = None
        if conv.get("role") == "agent":
            return await self._agent_answer(conv, text)
        if (conv.get("context") or {}).get("code"):
            text = re.sub(rf"\b{re.escape(conv['context']['code'])}\b", "", text, flags=re.I).strip(" -:,") or "Tell me about this"
        if conv.get("role") == "seller" and need not in ("homes",):
            data["needs_human"] = True
            return L.pick(SELLER, adapters.detect_language(text))
        if need == "spam":
            return ""
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
            out = f"{out}\n\n{L.pick(TRIAL_LINE, lang, url=adapters.trial_url())}"
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

    async def _lead(self, conv: dict, agent_id: str, text: str, now: datetime) -> None:
        label = adapters.DM_LABEL[conv["platform"]]
        try:
            contact_id, created = await adapters.upsert_dm_lead(self.db, agent_id=agent_id, platform=conv["platform"], sender=conv["sender"],
                                                                data=conv["data"], message=f"{label}: {text}", now=now, interest=conv.get("context"))
        except Exception as e:  # a lead problem must never stop the reply
            log.warning("dm: lead not stored: %s", self._clean(type(e).__name__))
            return
        conv["lead_id"] = contact_id
        ref = {"lead_id": contact_id, "conversation_id": conv["_id"]}
        who = conv["data"].get("name") or "A buyer"
        if created:
            await adapters.notify(self.db, agent_id, "new_dm_lead", f"{who} messaged on {label}. {adapters.summary(conv['data'])}", ref, now)
        if conv["data"].get("needs_human") and not conv.get("needs_human_notified"):
            conv["needs_human_notified"] = True
            asked = (conv["data"].get("questions") or [""])[-1]
            await adapters.notify(self.db, agent_id, "dm_needs_you", f"{who} asked something on {label} we could not answer: \"{asked[:120]}\"",
                                  ref, now)

    # ---- sending ----------------------------------------------------------------------------------------------------------
    def in_window(self, conv: dict, now: datetime) -> bool:
        last = conv.get("last_inbound_at")
        return bool(last) and now - last < WINDOW

    async def _send(self, conv: dict, reply: str, now: datetime) -> dict:
        rec = {"direction": "out", "platform": conv["platform"], "recipient": conv["sender"], "agent_id": conv.get("agent_id"), "text": reply,
               "ts": now, "error": None, "dry_run": self.cfg.dry_run}
        recent = [r for r in conv.get("replies", []) if r > now - timedelta(hours=1)]
        if not self.in_window(conv, now):
            rec.update(status="refused", error="outside the 24-hour messaging window")
        elif len(recent) >= MAX_REPLIES_PER_HOUR:
            rec.update(status="refused", error="hourly reply cap for this buyer")
        elif self.cfg.dry_run:
            rec["status"] = "dry_run"
        elif self.graph is None or not self.cfg.can_send:
            rec.update(status="failed", error="Messenger is not connected (no Page token)")
        else:
            rec.update(_id=f"out-{uuid.uuid4().hex}", status="sending", message_id=None)
            await self.messages.insert_one(dict(rec))  # saved first, so its echo is known as ours however fast it comes back
            try:
                rec["message_id"] = await self.graph.send_text(conv["sender"], reply) or None
                rec["status"] = "sent"
            except DmGraphError as e:
                rec.update(status="failed", error=self._clean(e))
                log.warning("dm: send failed: %s", rec["error"])
            await self.messages.update_one({"_id": rec["_id"]}, {"$set": {k: rec[k] for k in ("status", "message_id", "error")}})
        if rec["status"] in ("sent", "dry_run"):
            conv["replies"] = recent + [now]
        if "_id" not in rec:
            rec["_id"] = f"out-{uuid.uuid4().hex}"
            await self.messages.insert_one(rec)
        return rec

    async def _finish(self, conv: dict, mid: str, reply: Optional[str], outcome: str, now: datetime, text: str) -> dict:
        conv["messages"] = conv.get("messages", []) + [{"role": "user", "text": text or "[attachment]", "ts": now}]
        status = None
        if reply:
            rec = await self._send(conv, reply, now)
            status = rec["status"]
            conv["messages"].append({"role": "bot", "text": reply, "ts": now, "status": status})
        conv["messages"] = conv["messages"][-MAX_KEPT:]
        conv["updated_at"] = now
        conv["needs_human"] = bool(conv["data"].get("needs_human"))
        if await self.convs.find_one({"_id": conv["_id"]}):
            await self.convs.update_one({"_id": conv["_id"]}, {"$set": {k: v for k, v in conv.items() if k != "_id"}})
        else:
            await self.convs.insert_one(conv)
        if mid:
            await self.messages.update_one({"_id": mid}, {"$set": {"status": outcome, "agent_id": conv.get("agent_id"), "processed_at": now}})
        return {"status": outcome, "reply": reply, "send_status": status, "agent_id": conv.get("agent_id"), "lead_id": conv.get("lead_id")}

    # ---- Studio -------------------------------------------------------------------------------------------------------------
    async def conversations(self, agent_id: str, limit: int = 30) -> list:
        docs = await self.convs.find({"agent_id": agent_id}).sort("updated_at", -1).limit(min(max(limit, 1), 100)).to_list(100)
        now = self.now()
        return [{
            "id": uuid.uuid5(uuid.NAMESPACE_URL, d["_id"]).hex[:12], "channel": d["platform"], "name": d["data"].get("name") or None,
            "lead_id": d.get("lead_id"), "summary": adapters.summary(d["data"]), "needs_human": bool(d.get("needs_human")),
            "opted_out": bool(d.get("opted_out")), "updated_at": d.get("updated_at"), "language": d.get("language") or "en",
            "interest_title": (d.get("context") or {}).get("title") or None, "window_open": self.in_window(d, now),
            "person_replying": bool(d.get("human_until") and d["human_until"] > now),
            "messages": [{"role": x["role"], "text": x["text"][:600], "ts": x["ts"], "status": x.get("status")} for x in (d.get("messages") or [])[-6:]],
        } for d in docs]
