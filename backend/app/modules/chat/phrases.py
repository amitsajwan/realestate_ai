"""The website assistant's fixed sentences in the buyer's language: en, hinglish (Hindi in Roman letters), hi, mr (Devanagari), mr_latn.

Only the sentences the engine controls live here (greetings, the questions, the number ask, no-match, thanks). Answers from the vetted
knowledge stay as the knowledge module returns them. The English sentences the WhatsApp module translates on its own (lang.FIXED) are kept
word for word, so a WhatsApp buyer (who gets English from the engine) is still translated there.

`say(key, lang, **kw)` never mixes: a key missing in a language falls back to the whole English sentence, never half of one.
"""
import re
from typing import Dict, Optional

from app.core import brand

LANGS = ("en", "hinglish", "hi", "mr", "mr_latn")

P: Dict[str, Dict[str, str]] = {
    # ---- greetings (kept short) -----------------------------------------------------------------------------------
    "greet": {
        "en": f"Hi! I am the {brand.NAME} assistant. I help you find new projects and homes in Pune, each checked against MahaRERA. Tell me the area, a project name or your budget.",
        "hinglish": f"Namaste! Main {brand.NAME} ka assistant hoon. Main Pune mein naye projects aur ghar dhoondhne mein madad karta hoon, har project MahaRERA se check kiya hua. Mujhe area, project ka naam ya apna budget bataiye.",
        "hi": f"नमस्ते! मैं {brand.NAME_DEVANAGARI} का सहायक हूँ। मैं पुणे में नए प्रोजेक्ट और घर ढूँढने में मदद करता हूँ, हर प्रोजेक्ट महारेरा से जाँचा हुआ। मुझे इलाका, प्रोजेक्ट का नाम या अपना बजट बताइए।",
        "mr": f"नमस्कार! मी {brand.NAME_DEVANAGARI} चा सहाय्यक आहे. मी पुण्यात नवीन प्रोजेक्ट आणि घरे शोधायला मदत करतो, प्रत्येक प्रोजेक्ट महारेरावर तपासलेला. मला भाग, प्रोजेक्टचे नाव किंवा तुमचे बजेट सांगा.",
        "mr_latn": f"Namaskar! Mi {brand.NAME} cha sahayyak aahe. Mi Punyat navin project ani ghare shodhayla madat karto, pratyek project MahaRERA var tapaslela. Mala bhag, projectche naav kiwa tumche budget sanga.",
    },
    "greet_listing": {
        "en": "Asking about the {home}? I can tell you about it or find similar homes.",
        "hinglish": "{home} ke baare mein jaanna hai? Main iske baare mein bata sakta hoon ya isi tarah ke ghar dhoondh sakta hoon.",
        "hi": "{home} के बारे में जानना है? मैं इसके बारे में बता सकता हूँ या इसी तरह के घर ढूँढ सकता हूँ।",
        "mr": "{home} बद्दल विचारायचे आहे? मी याबद्दल सांगू शकतो किंवा असेच घर शोधू शकतो.",
        "mr_latn": "{home} baddal vicharayche aahe? Mi yabaddal sangu shakto kiwa asech ghar shodhu shakto.",
    },
    "greet_sample": {
        "en": "Asking about the sample {home}? It is an illustration, not for sale. I can tell you about it or find real homes like it.",
        "hinglish": "Sample {home} ke baare mein jaanna hai? Yeh sirf ek udaharan hai, bikri ke liye nahi. Main iske baare mein bata sakta hoon ya aise asli ghar dhoondh sakta hoon.",
        "hi": "सैंपल {home} के बारे में जानना है? यह सिर्फ़ एक उदाहरण है, बिक्री के लिए नहीं। मैं इसके बारे में बता सकता हूँ या ऐसे असली घर ढूँढ सकता हूँ।",
        "mr": "सॅम्पल {home} बद्दल विचारायचे आहे? हे फक्त उदाहरण आहे, विक्रीसाठी नाही. मी याबद्दल सांगू शकतो किंवा असेच खरे घर शोधू शकतो.",
        "mr_latn": "Sample {home} baddal vicharayche aahe? He fakt udaharan aahe, vikrisathi nahi. Mi yabaddal sangu shakto kiwa asech khare ghar shodhu shakto.",
    },
    # ---- one greeting per kind of page (2026-10-29: the page decides the first question; the area is never asked where the page names it)
    "greet_area": {   # a locality page, or a guide about a place
        "en": "Reading about {area}? I can answer questions about the area or show new projects there.",
        "hinglish": "{area} ke baare mein padh rahe hain? Main area ke sawaalon ke jawab de sakta hoon ya wahan ke naye projects dikha sakta hoon.",
        "hi": "{area} के बारे में पढ़ रहे हैं? मैं इलाके के सवालों के जवाब दे सकता हूँ या वहाँ के नए प्रोजेक्ट दिखा सकता हूँ।",
        "mr": "{area} बद्दल वाचत आहात? मी या भागाबद्दलच्या प्रश्नांची उत्तरे देऊ शकतो किंवा तिथले नवीन प्रोजेक्ट दाखवू शकतो.",
        "mr_latn": "{area} baddal vachat aahat? Mi ya bhagabaddal prashnanchi uttare deu shakto kiwa tithle navin project dakhavu shakto.",
    },
    "greet_list": {   # an area's project page or one of its lists (top, new launches, ready to move, a BHK): {what} is from LIST_WHAT
        "en": "Looking at {what} in {area}?",
        "hinglish": "{area} mein {what} dekh rahe hain?",
        "hi": "{area} में {what} देख रहे हैं?",
        "mr": "{area} मधील {what} पाहत आहात?",
        "mr_latn": "{area} madhil {what} pahat aahat?",
    },
    "greet_project": {   # what the project page itself offers (lib/site/strings.ts PROJECT_CTA): the price sheet and floor plans, a visit
        "en": "Asking about {project}? I can get you its price sheet and floor plans, or set up a site visit.",
        "hinglish": "{project} ke baare mein jaanna hai? Main aapko iski price sheet aur floor plans dilwa sakta hoon, ya site visit fix karwa sakta hoon.",
        "hi": "{project} के बारे में जानना है? मैं आपको इसकी प्राइस शीट और फ्लोर प्लान दिलवा सकता हूँ, या साइट विज़िट तय करवा सकता हूँ।",
        "mr": "{project} बद्दल विचारायचे आहे? मी तुम्हाला याची प्राइस शीट आणि फ्लोर प्लॅन मिळवून देऊ शकतो, किंवा साइट व्हिजिट ठरवू शकतो.",
        "mr_latn": "{project} baddal vicharayche aahe? Mi tumhala yachi price sheet ani floor plan milvun deu shakto, kiwa site visit tharavu shakto.",
    },
    # ---- what they read earlier in this visit (2026-10-29, chat/visit.py): only names from our records, never from a URL alone
    "also_one": {   # after greet_project, on a project page, when they read one other project
        "en": "You also looked at {a}. Want its price sheet too?",
        "hinglish": "Aapne {a} bhi dekha tha. Uski price sheet bhi chahiye?",
        "hi": "आपने {a} भी देखा था। उसकी प्राइस शीट भी चाहिए?",
        "mr": "तुम्ही {a} सुद्धा पाहिला होता. त्याची प्राइस शीटही हवी आहे का?",
        "mr_latn": "Tumhi {a} suddha pahila hota. Tyachi price sheet pan havi aahe ka?",
    },
    "also_two": {
        "en": "You also looked at {a} and {b}. Want price sheets for those too?",
        "hinglish": "Aapne {a} aur {b} bhi dekhe the. Unki price sheets bhi chahiye?",
        "hi": "आपने {a} और {b} भी देखे थे। उनकी प्राइस शीट भी चाहिए?",
        "mr": "तुम्ही {a} आणि {b} सुद्धा पाहिले होते. त्यांच्या प्राइस शीटही हव्या आहेत का?",
        "mr_latn": "Tumhi {a} ani {b} suddha pahile hote. Tyanchya price sheet pan havya aahet ka?",
    },
    "seen_one": {   # a general page (home, news, /enquire) after reading one project
        "en": "You were looking at {a}. Want its price sheet and floor plans?",
        "hinglish": "Aap {a} dekh rahe the. Uski price sheet aur floor plans chahiye?",
        "hi": "आप {a} देख रहे थे। उसकी प्राइस शीट और फ्लोर प्लान चाहिए?",
        "mr": "तुम्ही {a} पाहत होता. त्याची प्राइस शीट आणि फ्लोर प्लॅन हवे आहेत का?",
        "mr_latn": "Tumhi {a} pahat hota. Tyachi price sheet ani floor plan have aahet ka?",
    },
    "seen_two": {
        "en": "You were looking at {a} and {b}. Want their price sheets and floor plans, or help comparing them?",
        "hinglish": "Aap {a} aur {b} dekh rahe the. Unki price sheets aur floor plans chahiye, ya dono ko compare karne mein madad?",
        "hi": "आप {a} और {b} देख रहे थे। उनकी प्राइस शीट और फ्लोर प्लान चाहिए, या दोनों की तुलना में मदद?",
        "mr": "तुम्ही {a} आणि {b} पाहत होता. त्यांच्या प्राइस शीट आणि फ्लोर प्लॅन हवे आहेत, की दोघांची तुलना करायला मदत?",
        "mr_latn": "Tumhi {a} ani {b} pahat hota. Tyanchya price sheet ani floor plan have aahet, ki doghanchi tulna karayla madat?",
    },
    "seen_plan": {   # chat/plan.py: a finished home plan; {want} is its size and budget
        "en": "Your home plan: {want}. Want today's prices for these picks from our team?",
        "hinglish": "Aapka home plan: {want}. In projects ke aaj ke prices hamari team se chahiye?",
        "hi": "आपका होम प्लान: {want}। इन प्रोजेक्ट की आज की कीमत हमारी टीम से चाहिए?",
        "mr": "तुमचा होम प्लॅन: {want}. या प्रोजेक्टच्या आजच्या किमती आमच्या टीमकडून हव्या आहेत का?",
        "mr_latn": "Tumcha home plan: {want}. Ya projectchya aajchya kimati aamchya team kadun havya aahet ka?",
    },
    "try_plan": {   # the one line that offers the plan; the link sits beside it
        "en": "Not sure which one fits your family? Our home plan takes six quick answers and gives you a short list, with the facts behind each pick.",
        "hinglish": "Samajh nahi aa raha kaunsa aapke parivaar ke liye sahi hai? Hamara home plan chhe aasan sawaalon se chhoti list deta hai, har project ke facts ke saath.",
        "hi": "समझ नहीं आ रहा कौन-सा आपके परिवार के लिए सही है? हमारा होम प्लान छह आसान सवालों से छोटी सूची देता है, हर प्रोजेक्ट के तथ्यों के साथ।",
        "mr": "तुमच्या कुटुंबासाठी कोणता योग्य आहे हे कळत नाही? आमचा होम प्लॅन सहा सोप्या प्रश्नांतून छोटी यादी देतो, प्रत्येक प्रोजेक्टच्या तथ्यांसह.",
        "mr_latn": "Tumchya kutumbasathi konta yogya aahe he kalat nahi? Aamcha home plan saha sopya prashnantun chhoti yadi deto, pratyek projectchya tathyansah.",
    },
    # ---- the note beside the chat button (chat/nudge.py)
    "nudge_compare": {
        "en": "Comparing {a} and {b}? I can get you both price sheets, side by side.",
        "hinglish": "{a} aur {b} compare kar rahe hain? Main dono ki price sheets saath mein dilwa sakta hoon.",
        "hi": "{a} और {b} की तुलना कर रहे हैं? मैं दोनों की प्राइस शीट साथ में दिलवा सकता हूँ।",
        "mr": "{a} आणि {b} ची तुलना करत आहात? मी दोघांच्या प्राइस शीट एकत्र मिळवून देऊ शकतो.",
        "mr_latn": "{a} ani {b} chi tulna karat aahat? Mi doghanchya price sheet ekatra milvun deu shakto.",
    },
    "nudge_hot": {
        "en": "Looking around {area}? I can show you the projects buyers are looking at most there right now.",
        "hinglish": "{area} dekh rahe hain? Main wahan ke woh projects dikha sakta hoon jo buyers abhi sabse zyada dekh rahe hain.",
        "hi": "{area} देख रहे हैं? मैं वहाँ के वे प्रोजेक्ट दिखा सकता हूँ जो खरीदार अभी सबसे ज़्यादा देख रहे हैं।",
        "mr": "{area} पाहत आहात? खरेदीदार सध्या तिथले सर्वात जास्त पाहत असलेले प्रोजेक्ट मी दाखवू शकतो.",
        "mr_latn": "{area} pahat aahat? Kharedidar sadhya tithle sarvat jast pahat aslele project mi dakhavu shakto.",
    },
    "lang_ok": {   # they chose a language in the middle of a chat
        "en": "Sure, let us continue in English.",
        "hinglish": "Zaroor, ab Hindi mein baat karte hain.",
        "hi": "ज़रूर, अब हिंदी में बात करते हैं।",
        "mr": "नक्की, आता मराठीत बोलूया.",
        "mr_latn": "Nakki, aata Marathit boluya.",
    },
    "cards_hot": {   # chat/projects.py: the area's hot projects, none of them priced for this buyer
        "en": "These are the projects buyers are looking at most in {area} right now. Our team can tell you today's prices.",
        "hinglish": "{area} mein abhi buyers sabse zyada yeh projects dekh rahe hain. Hamari team aapko aaj ke prices bata sakti hai.",
        "hi": "{area} में खरीदार अभी सबसे ज़्यादा ये प्रोजेक्ट देख रहे हैं। हमारी टीम आपको आज की कीमत बता सकती है।",
        "mr": "{area} मध्ये खरेदीदार सध्या सर्वात जास्त हे प्रोजेक्ट पाहत आहेत. आमची टीम तुम्हाला आजच्या किमती सांगू शकते.",
        "mr_latn": "{area} madhye kharedidar sadhya sarvat jast he project pahat aahet. Aamchi team tumhala aajchya kimati sangu shakte.",
    },
    "handoff_web_plan": {
        "en": "Share your mobile number and the {team} team will WhatsApp you today's prices for your plan.",
        "hinglish": "Apna mobile number share karein, {team} team aapke plan ke aaj ke prices WhatsApp karegi.",
        "hi": "अपना मोबाइल नंबर दें, {team} टीम आपके प्लान की आज की कीमत WhatsApp करेगी।",
        "mr": "तुमचा मोबाइल नंबर द्या, {team} टीम तुमच्या प्लॅनच्या आजच्या किमती WhatsApp करेल.",
        "mr_latn": "Tumcha mobile number dya, {team} team tumchya plan chya aajchya kimati WhatsApp karel.",
    },
    "seen_area": {   # a general page after reading an area's pages or lists: {what} is from LIST_WHAT
        "en": "Still looking at {what} in {area}?",
        "hinglish": "Abhi bhi {area} mein {what} dekh rahe hain?",
        "hi": "अभी भी {area} में {what} देख रहे हैं?",
        "mr": "अजूनही {area} मधील {what} पाहत आहात?",
        "mr_latn": "Ajunhi {area} madhil {what} pahat aahat?",
    },
    "greet_builder": {
        "en": "Looking at projects by {builder}? Tell me which project, or which area you want.",
        "hinglish": "{builder} ke projects dekh rahe hain? Bataiye kaun sa project, ya kaun sa area chahiye.",
        "hi": "{builder} के प्रोजेक्ट देख रहे हैं? बताइए कौन सा प्रोजेक्ट, या कौन सा इलाका चाहिए।",
        "mr": "{builder} चे प्रोजेक्ट पाहत आहात? कोणता प्रोजेक्ट, किंवा कोणता भाग हवा ते सांगा.",
        "mr_latn": "{builder} che project pahat aahat? Konta project, kiwa konta bhag hava te sanga.",
    },
    "greet_agent": {   # only on the pages for agents (/agents, /trial, /request-invite, /for-agents)
        "en": f"Hi! I am the {brand.NAME} assistant for agents. Ask me how we bring you buyer leads, what it costs, or how to start your free trial.",
        "hinglish": f"Namaste! Main agents ke liye {brand.NAME} ka assistant hoon. Mujhse poochhiye hum aapko buyer leads kaise dete hain, kitna lagta hai, ya free trial kaise shuru karein.",
        "hi": f"नमस्ते! मैं एजेंटों के लिए {brand.NAME_DEVANAGARI} का सहायक हूँ। मुझसे पूछिए कि हम आपको खरीदारों की लीड कैसे देते हैं, इसका खर्च कितना है, या फ्री ट्रायल कैसे शुरू करें।",
        "mr": f"नमस्कार! मी एजंटसाठी {brand.NAME_DEVANAGARI} चा सहाय्यक आहे. आम्ही तुम्हाला खरेदीदारांच्या लीड कशा देतो, खर्च किती आहे, किंवा फ्री ट्रायल कसा सुरू करायचा ते मला विचारा.",
        "mr_latn": f"Namaskar! Mi agent sathi {brand.NAME} cha sahayyak aahe. Aamhi tumhala buyer leads kasha deto, kharch kiti aahe, kiwa free trial kasa suru karaycha te mala vichara.",
    },
    "for_agents": {   # someone says they are an agent on a page for buyers: one line, then the chat stays a buyer chat
        "en": "For agents, see /agents.",
        "hinglish": "Agents ke liye /agents dekhiye.",
        "hi": "एजेंटों के लिए /agents देखें।",
        "mr": "एजंटसाठी /agents पहा.",
        "mr_latn": "Agent sathi /agents paha.",
    },
    "ask_size": {   # the project page's first question (ask_bhk stays word for word for WhatsApp)
        "en": "Which size (BHK) are you looking for?",
        "hinglish": "Aap kaun sa size (BHK) dekh rahe hain?",
        "hi": "आप कौन सा साइज़ (BHK) देख रहे हैं?",
        "mr": "तुम्ही कोणता साइज (BHK) पाहत आहात?",
        "mr_latn": "Tumhi konta size (BHK) pahat aahat?",
    },
    # ---- the questions (English kept identical to whatsapp.lang.FIXED) ---------------------------------------------
    "ask_tx": {"en": "Are you looking to buy or to rent?", "hinglish": "Aap ghar kharidna chahte hain ya rent par lena?",
               "hi": "क्या आप घर खरीदना चाहते हैं या किराए पर लेना?", "mr": "तुम्हाला घर विकत घ्यायचे आहे की भाड्याने?",
               "mr_latn": "Tumhala ghar vikat ghyayche aahe ki bhadyane?"},
    "ask_locality": {"en": "Which area are you most interested in?", "hinglish": "Aapko kaun sa area sabse zyada pasand hai?",
                     "hi": "आपको कौन सा इलाका सबसे ज़्यादा पसंद है?", "mr": "तुम्हाला कोणता भाग सर्वात जास्त आवडतो?",
                     "mr_latn": "Tumhala konta bhag sarvat jast aavadto?"},
    "ask_bhk": {"en": "How many bedrooms do you need?", "hinglish": "Aapko kitne bedroom chahiye?", "hi": "आपको कितने बेडरूम चाहिए?",
                "mr": "तुम्हाला किती बेडरूम हवे आहेत?", "mr_latn": "Tumhala kiti bedroom have aahet?"},
    "ask_budget": {"en": "What budget do you have in mind?", "hinglish": "Aapka budget kitna hai?", "hi": "आपका बजट कितना है?",
                   "mr": "तुमचे बजेट किती आहे?", "mr_latn": "Tumche budget kiti aahe?"},
    "ask_timeline": {"en": "When are you planning to move?", "hinglish": "Aap kab tak shift hona chahte hain?",
                     "hi": "आप कब तक शिफ्ट होना चाहते हैं?", "mr": "तुम्ही कधी शिफ्ट होण्याचा विचार करत आहात?",
                     "mr_latn": "Tumhi kadhi shift honyacha vichar karat aahat?"},
    "ask_name": {"en": "May I know your name?", "hinglish": "Aapka naam jaan sakta hoon?", "hi": "क्या मैं आपका नाम जान सकता हूँ?",
                 "mr": "तुमचे नाव कळेल का?", "mr_latn": "Tumche naav kalel ka?"},
    # ---- the number: asked at most twice, consent shown once, next to the ask -------------------------------------
    # ---- the hand-off (owner, 2026-10-20: short chats; when the bot is not sure, its last word is 'passed to the team') ----------------
    "handoff": {   # we have their number (WhatsApp, DMs, or shared on the site)
        "en": "I have passed this to the {team} team. They will get back to you soon.",
        "hinglish": "Maine yeh {team} team ko bhej diya hai. Woh jaldi aapse sampark karenge.",
        "hi": "मैंने यह {team} टीम को भेज दिया है। वे जल्द आपसे संपर्क करेंगे।",
        "mr": "मी हे {team} टीमकडे पाठवले आहे. ते लवकरच तुमच्याशी संपर्क करतील.",
        "mr_latn": "Mi he {team} team kade pathavle aahe. Te lavkarach tumchyashi samparka kartil.",
    },
    "handoff_web": {   # the website, no number yet: the team cannot answer in this chat, so the number is the way back
        "en": "I have passed this to the {team} team. Share your mobile number and they will call or WhatsApp you.",
        "hinglish": "Maine yeh {team} team ko bhej diya hai. Apna mobile number share karein, woh aapko call ya WhatsApp karenge.",
        "hi": "मैंने यह {team} टीम को भेज दिया है। अपना मोबाइल नंबर दें, वे आपको कॉल या WhatsApp करेंगे।",
        "mr": "मी हे {team} टीमकडे पाठवले आहे. तुमचा मोबाइल नंबर द्या, ते तुम्हाला कॉल किंवा WhatsApp करतील.",
        "mr_latn": "Mi he {team} team kade pathavle aahe. Tumcha mobile number dya, te tumhala call kinva WhatsApp kartil.",
    },
    # the hand-off on the website when the buyer asked for one thing: the line says what the team sends, so floor plans, the price sheet
    # and a visit do not all end in the same sentence (2026-10-25)
    "handoff_web_plans": {
        "en": "Share your mobile number and the {team} team will WhatsApp you the floor plans.",
        "hinglish": "Apna mobile number share karein, {team} team aapko floor plans WhatsApp karegi.",
        "hi": "अपना मोबाइल नंबर दें, {team} टीम आपको फ्लोर प्लान WhatsApp करेगी।",
        "mr": "तुमचा मोबाइल नंबर द्या, {team} टीम तुम्हाला फ्लोर प्लॅन WhatsApp करेल.",
        "mr_latn": "Tumcha mobile number dya, {team} team tumhala floor plan WhatsApp karel.",
    },
    "handoff_web_prices": {
        "en": "Share your mobile number and the {team} team will WhatsApp you today's price sheet.",
        "hinglish": "Apna mobile number share karein, {team} team aapko aaj ki price sheet WhatsApp karegi.",
        "hi": "अपना मोबाइल नंबर दें, {team} टीम आपको आज की प्राइस शीट WhatsApp करेगी।",
        "mr": "तुमचा मोबाइल नंबर द्या, {team} टीम तुम्हाला आजची प्राइस शीट WhatsApp करेल.",
        "mr_latn": "Tumcha mobile number dya, {team} team tumhala aajchi price sheet WhatsApp karel.",
    },
    "handoff_web_sheet": {   # both at once, as the project page's form offers them
        "en": "Share your mobile number and the {team} team will WhatsApp you today's price sheet and floor plans.",
        "hinglish": "Apna mobile number share karein, {team} team aapko aaj ki price sheet aur floor plans WhatsApp karegi.",
        "hi": "अपना मोबाइल नंबर दें, {team} टीम आपको आज की प्राइस शीट और फ्लोर प्लान WhatsApp करेगी।",
        "mr": "तुमचा मोबाइल नंबर द्या, {team} टीम तुम्हाला आजची प्राइस शीट आणि फ्लोर प्लॅन WhatsApp करेल.",
        "mr_latn": "Tumcha mobile number dya, {team} team tumhala aajchi price sheet ani floor plan WhatsApp karel.",
    },
    "handoff_web_compare": {   # 'Compare them' after the projects they read: both price sheets, side by side
        "en": "Share your mobile number and the {team} team will WhatsApp you both price sheets and floor plans to compare.",
        "hinglish": "Apna mobile number share karein, {team} team aapko dono ki price sheets aur floor plans compare karne ke liye WhatsApp karegi.",
        "hi": "अपना मोबाइल नंबर दें, {team} टीम आपको तुलना के लिए दोनों की प्राइस शीट और फ्लोर प्लान WhatsApp करेगी।",
        "mr": "तुमचा मोबाइल नंबर द्या, {team} टीम तुम्हाला तुलनेसाठी दोघांच्या प्राइस शीट आणि फ्लोर प्लॅन WhatsApp करेल.",
        "mr_latn": "Tumcha mobile number dya, {team} team tumhala tulnesathi doghanchya price sheet ani floor plan WhatsApp karel.",
    },
    "handoff_web_visit": {
        "en": "Share your mobile number and the {team} team will call you to fix your site visit.",
        "hinglish": "Apna mobile number share karein, {team} team aapko call karke site visit fix karegi.",
        "hi": "अपना मोबाइल नंबर दें, {team} टीम आपको कॉल करके साइट विज़िट तय करेगी।",
        "mr": "तुमचा मोबाइल नंबर द्या, {team} टीम तुम्हाला कॉल करून साइट व्हिजिट ठरवेल.",
        "mr_latn": "Tumcha mobile number dya, {team} team tumhala call karun site visit tharavel.",
    },
    "handed_no_number": {   # a website chat handed to the team, with no number to reach them on
        "en": "The {team} team can only reach you on your mobile number. Share it here whenever you are ready.",
        "hinglish": "{team} team aapse sirf aapke mobile number par hi sampark kar sakti hai. Jab theek lage, yahan share karein.",
        "hi": "{team} टीम आपसे सिर्फ़ आपके मोबाइल नंबर पर ही संपर्क कर सकती है। जब ठीक लगे, यहाँ दें।",
        "mr": "{team} टीम तुमच्याशी फक्त तुमच्या मोबाइल नंबरवरच संपर्क करू शकते. जेव्हा योग्य वाटेल तेव्हा इथे द्या.",
        "mr_latn": "{team} team tumchyashi fakt tumchya mobile number varach samparka karu shakte. Jevha yogya vatel tevha ithe dya.",
    },
    "handed_ack": {
        "en": "The {team} team has your message and will get back to you.",
        "hinglish": "{team} team ko aapka message mil gaya hai, woh aapse sampark karenge.",
        "hi": "{team} टीम को आपका संदेश मिल गया है, वे आपसे संपर्क करेंगे।",
        "mr": "{team} टीमला तुमचा संदेश मिळाला आहे, ते तुमच्याशी संपर्क करतील.",
        "mr_latn": "{team} team la tumcha sandesh milala aahe, te tumchyashi samparka kartil.",
    },
    "ask_phone": {
        "en": "If you like, share your mobile number and our team will send you options and answer anything I cannot.",
        "hinglish": "Aap chahein to apna mobile number share karein, hamari team aapko options bhejegi aur baaki sawaalon ke jawab degi.",
        "hi": "आप चाहें तो अपना मोबाइल नंबर दें, हमारी टीम आपको विकल्प भेजेगी और बाकी सवालों के जवाब देगी।",
        "mr": "हवे असल्यास तुमचा मोबाइल नंबर द्या, आमची टीम तुम्हाला पर्याय पाठवेल आणि इतर प्रश्नांची उत्तरे देईल.",
        "mr_latn": "Have aslyas tumcha mobile number dya, aamchi team tumhala paryay pathvel ani itar prashnanchi uttare deil.",
    },
    "ask_phone_again": {
        "en": "Would you like our team to follow up? Just share your mobile number.",
        "hinglish": "Kya hamari team aapse baat kare? Bas apna mobile number share karein.",
        "hi": "क्या हमारी टीम आपसे बात करे? बस अपना मोबाइल नंबर दें।",
        "mr": "आमच्या टीमने तुमच्याशी बोलावे का? फक्त तुमचा मोबाइल नंबर द्या.",
        "mr_latn": "Aamchya team ne tumchyashi bolave ka? Fakt tumcha mobile number dya.",
    },
    "consent": {
        "en": f"By sharing your number you agree that {brand.NAME} may contact you about this enquiry.",
        "hinglish": f"Number share karke aap maante hain ki {brand.NAME} is enquiry ke baare mein aapse contact kar sakta hai.",
        "hi": f"नंबर देकर आप सहमति देते हैं कि {brand.NAME_DEVANAGARI} इस पूछताछ के बारे में आपसे संपर्क कर सकता है।",
        "mr": f"नंबर देऊन तुम्ही मान्य करता की {brand.NAME_DEVANAGARI} या चौकशीबद्दल तुमच्याशी संपर्क साधू शकते.",
        "mr_latn": f"Number deun tumhi manya karta ki {brand.NAME} ya chaukashibaddal tumchyashi samparka sadhu shakte.",
    },
    "confirm_phone": {
        "en": "Can our team contact you on the number ending {last4}? Reply YES to confirm.",
        "hinglish": "Kya hamari team aapse {last4} par khatam hone wale number par contact kare? Confirm karne ke liye YES likhein.",
        "hi": "क्या हमारी टीम {last4} पर खत्म होने वाले नंबर पर आपसे संपर्क करे? पुष्टि के लिए YES लिखें।",
        "mr": "आमच्या टीमने {last4} ने संपणाऱ्या नंबरवर संपर्क करावा का? खात्रीसाठी YES लिहा.",
        "mr_latn": "Aamchya team ne {last4} ne sampnarya number var samparka karava ka? Khatri sathi YES liha.",
    },
    "not_now_ok": {"en": "No problem.", "hinglish": "Koi baat nahi.", "hi": "कोई बात नहीं।", "mr": "काही हरकत नाही.", "mr_latn": "Kahi harkat nahi."},
    "thanks_lead": {
        "en": "Thank you{name}! Our team will contact you soon. You can keep asking me questions in the meantime.",
        "hinglish": "Shukriya{name}! Hamari team jald hi aapse contact karegi. Tab tak aap mujhse sawaal poochh sakte hain.",
        "hi": "धन्यवाद{name}! हमारी टीम जल्द ही आपसे संपर्क करेगी। तब तक आप मुझसे सवाल पूछ सकते हैं।",
        "mr": "धन्यवाद{name}! आमची टीम लवकरच तुमच्याशी संपर्क करेल. तोपर्यंत तुम्ही मला प्रश्न विचारू शकता.",
        "mr_latn": "Dhanyavad{name}! Aamchi team lavkarach tumchyashi samparka karel. Toparyant tumhi mala prashna vicharu shakta.",
    },
    "thanks_name": {"en": "Thanks, {name}.", "hinglish": "Shukriya, {name}.", "hi": "धन्यवाद, {name}।", "mr": "धन्यवाद, {name}.", "mr_latn": "Dhanyavad, {name}."},
    # ---- homes ----------------------------------------------------------------------------------------------------
    "cards": {
        "en": "Here are {n} homes that fit what you told me.",
        "hinglish": "Aapki requirement se milte {n} ghar yeh rahe.",
        "hi": "आपकी ज़रूरत से मिलते {n} घर ये रहे।",
        "mr": "तुमच्या गरजेशी जुळणारी {n} घरे ही आहेत.",
        "mr_latn": "Tumchya garjeshi julnari {n} ghare hi aahet.",
    },
    "cards_one": {
        "en": "Here is a home that fits what you told me.",
        "hinglish": "Aapki requirement se milta ek ghar yeh raha.",
        "hi": "आपकी ज़रूरत से मिलता एक घर यह रहा।",
        "mr": "तुमच्या गरजेशी जुळणारे एक घर हे आहे.",
        "mr_latn": "Tumchya garjeshi julnare ek ghar he aahe.",
    },
    "cards_samples": {
        "en": "These sample homes show how matches look. They are illustrations, not for sale.",
        "hinglish": "Yeh sample ghar dikhate hain ki matches kaise dikhte hain. Yeh sirf udaharan hain, bikri ke liye nahi.",
        "hi": "ये सैंपल घर दिखाते हैं कि मिलान कैसे दिखते हैं। ये सिर्फ़ उदाहरण हैं, बिक्री के लिए नहीं।",
        "mr": "ही सॅम्पल घरे जुळणी कशी दिसते ते दाखवतात. ती फक्त उदाहरणे आहेत, विक्रीसाठी नाहीत.",
        "mr_latn": "Hi sample ghare julni kashi diste te dakhavtat. Ti fakt udaharane aahet, vikrisathi nahit.",
    },
    "sample_note": {
        "en": "Homes marked Sample are illustrations, not for sale.",
        "hinglish": "Sample wale ghar sirf udaharan hain, bikri ke liye nahi.",
        "hi": "सैंपल वाले घर सिर्फ़ उदाहरण हैं, बिक्री के लिए नहीं।",
        "mr": "सॅम्पल असलेली घरे फक्त उदाहरणे आहेत, विक्रीसाठी नाहीत.",
        "mr_latn": "Sample asleli ghare fakt udaharane aahet, vikrisathi nahit.",
    },
    "cards_projects": {   # chat/projects.py: no listing fits, so our project pages in the area (the register has no prices)
        "en": "No listed home fits this yet, but these projects in {area} are on our site. The agent can tell you their current prices.",
        "hinglish": "Abhi koi listed ghar match nahi hua, par {area} ke yeh projects hamari site par hain. Agent aapko inke aaj ke daam bata sakte hain.",
        "hi": "अभी कोई लिस्टेड घर मेल नहीं खाता, पर {area} के ये प्रोजेक्ट हमारी साइट पर हैं। एजेंट आपको इनकी आज की कीमत बता सकते हैं।",
        "mr": "सध्या कोणतेही लिस्टेड घर जुळत नाही, पण {area} मधले हे प्रोजेक्ट आमच्या साइटवर आहेत. एजंट तुम्हाला त्यांच्या आजच्या किमती सांगू शकतात.",
        "mr_latn": "Sadhya kontehi listed ghar julat nahi, pan {area} madhle he project aamchya site var aahet. Agent tumhala tyanchya aajchya kimati sangu shaktat.",
    },
    "no_match": {
        "en": "I could not find a listed home that matches this right now, but our team can look for you.",
        "hinglish": "Abhi is requirement se milta koi listed ghar nahi mila, par hamari team aapke liye dhoondh sakti hai.",
        "hi": "अभी इस ज़रूरत से मिलता कोई लिस्टेड घर नहीं मिला। हमारी टीम आपके लिए विकल्प ढूँढ सकती है।",
        "mr": "सध्या या गरजेशी जुळणारे कोणतेही लिस्टेड घर सापडले नाही. आमची टीम तुमच्यासाठी पर्याय शोधू शकते.",
        "mr_latn": "Sadhya ya garjeshi julnare kontehi listed ghar sapadle nahi. Aamchi team tumchyasathi paryay shodhu shakte.",
    },
    # on a listing page the home being viewed is left out of the search, so "no match" would read as "this home does not fit"
    "no_other_match": {
        "en": "I could not find another listed home like this right now, but our team can look for you.",
        "hinglish": "Abhi is jaisa koi aur listed ghar nahi mila, par hamari team aapke liye dhoondh sakti hai.",
        "hi": "अभी इस जैसा कोई और लिस्टेड घर नहीं मिला। हमारी टीम आपके लिए विकल्प ढूँढ सकती है।",
        "mr": "सध्या असे दुसरे कोणतेही लिस्टेड घर सापडले नाही. आमची टीम तुमच्यासाठी पर्याय शोधू शकते.",
        "mr_latn": "Sadhya ase dusre kontehi listed ghar sapadle nahi. Aamchi team tumchyasathi paryay shodhu shakte.",
    },
    # ---- the rest (English kept identical to whatsapp.lang.FIXED) -------------------------------------------------
    "anything_else": {"en": "Is there anything else I can help you with?", "hinglish": "Kya main aapki aur koi madad kar sakta hoon?",
                      "hi": "क्या मैं आपकी और कोई मदद कर सकता हूँ?", "mr": "अजून काही मदत हवी आहे का?", "mr_latn": "Ajun kahi madat havi aahe ka?"},
    "objection": {
        "en": "Understood, that is more than you want to spend. Tell me your budget and I will show homes that fit it.",
        "hinglish": "Samajh gaya, yeh aapke budget se zyada hai. Apna budget bataiye, main usi range ke ghar dikhata hoon.",
        "hi": "समझ गया, यह आपके बजट से ज़्यादा है। अपना बजट बताइए, मैं उसी रेंज के घर दिखाता हूँ।",
        "mr": "समजले, हे तुमच्या बजेटपेक्षा जास्त आहे. तुमचे बजेट सांगा, मी त्या रेंजमधील घरे दाखवतो.",
        "mr_latn": "Samajle, he tumchya budget peksha jast aahe. Tumche budget sanga, mi tya range madhil ghare dakhavto.",
    },
    "visit_ok": {
        "en": "Happy to set up a visit. The agent will confirm a day and time with you.",
        "hinglish": "Visit zaroor arrange karenge. Agent aapke saath din aur time confirm karenge.",
        "hi": "विज़िट ज़रूर तय करेंगे। एजेंट आपके साथ दिन और समय पक्का करेंगे।",
        "mr": "भेट नक्की ठरवू. एजंट तुमच्याशी दिवस आणि वेळ निश्चित करतील.",
        "mr_latn": "Bhet nakki tharavu. Agent tumchyashi diwas ani vel nishchit kartil.",
    },
    "dont_guess": {
        "en": "I do not want to guess on that one. I will ask our team to confirm it for you.",
        "hinglish": "Is baare mein main andaaza nahi lagana chahta. Hamari team se confirm karwa deta hoon.",
        "hi": "इस बारे में मैं अंदाज़ा नहीं लगाना चाहता। मैं हमारी टीम से इसकी पुष्टि करवा दूँगा।",
        "mr": "याबद्दल मी अंदाज लावू इच्छित नाही. आमच्या टीमकडून खात्री करून घेतो.",
        "mr_latn": "Yabaddal mi andaj lavu ichhit nahi. Aamchya team kadun khatri karun gheto."},
    "team_takes": {"en": "Of course, our team can take it from here.", "hinglish": "Zaroor, hamari team aapse baat karegi.",
                   "hi": "ज़रूर, हमारी टीम आपसे बात करेगी।", "mr": "नक्की, आमची टीम तुमच्याशी बोलेल.", "mr_latn": "Nakki, aamchi team tumchyashi bolel."},
    "abuse": {
        "en": "I will pass this to our team so they can look into it. If you would like help finding a home, just tell me what you need.",
        "hinglish": "Main yeh hamari team tak pahuncha deta hoon. Ghar dhoondhne mein madad chahiye to bas bataiye.",
        "hi": "मैं यह हमारी टीम तक पहुँचा दूँगा। अगर आपको घर ढूँढने में मदद चाहिए, तो बस बताइए।",
        "mr": "मी हे आमच्या टीमपर्यंत पोहोचवतो. घर शोधायला मदत हवी असल्यास सांगा.",
        "mr_latn": "Mi he aamchya team paryant pohochavto. Ghar shodhayla madat havi aslyas sanga."},
    "got_it": {"en": "Got it: ", "hinglish": "Theek hai: ", "hi": "ठीक है: ", "mr": "ठीक आहे: ", "mr_latn": "Theek aahe: "},
    # 'not sure, how much will I get?' in answer to the budget question: the prices of what we have, then the homes
    "price_from": {
        "en": "{What} on our list start at {low}.",
        "hinglish": "Hamari list mein {what} {low} se shuru hote hain.",
        "hi": "हमारी सूची में {what} {low} से शुरू होते हैं।",
        "mr": "आमच्या यादीत {what} {low} पासून सुरू होतात.",
        "mr_latn": "Aamchya yadit {what} {low} pasun suru hotat.",
    },
    "price_range": {
        "en": "{What} on our list cost {low} to {high}.",
        "hinglish": "Hamari list mein {what} {low} se {high} tak ke hain.",
        "hi": "हमारी सूची में {what} {low} से {high} तक के हैं।",
        "mr": "आमच्या यादीत {what} {low} ते {high} पर्यंत आहेत.",
        "mr_latn": "Aamchya yadit {what} {low} te {high} paryant aahet.",
    },
    "homes_word": {"en": "homes", "hinglish": "ghar", "hi": "घर", "mr": "घरे", "mr_latn": "ghare"},
    "in_area": {"en": "{what} in {area}", "hinglish": "{area} mein {what}", "hi": "{area} में {what}", "mr": "{area} मधील {what}",
                "mr_latn": "{area} madhil {what}"},
}

# the words inside 'Got it: buy, Kharadi, 2 BHK, under 80L.' (so an acknowledgement is one language, not English in a Hinglish frame)
ACK = {
    "buy": {"en": "buy", "hinglish": "kharidna", "hi": "खरीदना", "mr": "विकत घेणे", "mr_latn": "vikat ghene"},
    "rent": {"en": "rent", "hinglish": "rent par", "hi": "किराए पर", "mr": "भाड्याने", "mr_latn": "bhadyane"},
    "under": {"en": "under {x}", "hinglish": "{x} tak", "hi": "{x} तक", "mr": "{x} पर्यंत", "mr_latn": "{x} paryant"},
    "above": {"en": "above {x}", "hinglish": "{x} se upar", "hi": "{x} से ऊपर", "mr": "{x} पेक्षा जास्त", "mr_latn": "{x} peksha jast"},
    "now": {"en": "moving soon", "hinglish": "jaldi shift", "hi": "जल्दी शिफ्ट", "mr": "लवकर शिफ्ट", "mr_latn": "lavkar shift"},
    "1_3_months": {"en": "moving in 1-3 months", "hinglish": "1-3 mahine mein shift", "hi": "1-3 महीने में शिफ्ट", "mr": "1-3 महिन्यांत शिफ्ट",
                   "mr_latn": "1-3 mahinyat shift"},
    "3_6_months": {"en": "moving in 3-6 months", "hinglish": "3-6 mahine mein shift", "hi": "3-6 महीने में शिफ्ट", "mr": "3-6 महिन्यांत शिफ्ट",
                   "mr_latn": "3-6 mahinyat shift"},
    "exploring": {"en": "just exploring", "hinglish": "abhi sirf dekh rahe hain", "hi": "अभी सिर्फ़ देख रहे हैं", "mr": "सध्या फक्त पाहत आहात",
                  "mr_latn": "sadhya fakt pahat aahat"},
}


def ack_word(key: str, lang: str = "en", **kw) -> str:
    table = ACK[key]
    return table.get(lang, table["en"]).format(**kw)


# what an area list is about, inside greet_list ("Looking at the top projects in Kharadi?"); with a BHK, "bhk" ("2 BHK homes")
LIST_WHAT = {
    "all": {"en": "new projects", "hinglish": "naye projects", "hi": "नए प्रोजेक्ट", "mr": "नवीन प्रोजेक्ट", "mr_latn": "navin project"},
    "top": {"en": "the top projects", "hinglish": "top projects", "hi": "टॉप प्रोजेक्ट", "mr": "टॉप प्रोजेक्ट", "mr_latn": "top project"},
    "new-launches": {"en": "new launch projects", "hinglish": "new launch projects", "hi": "नए लॉन्च प्रोजेक्ट", "mr": "नवीन लाँच प्रोजेक्ट",
                     "mr_latn": "navin launch project"},
    "ready-to-move": {"en": "ready to move projects", "hinglish": "ready to move projects", "hi": "रेडी टू मूव प्रोजेक्ट",
                      "mr": "रेडी टू मूव्ह प्रोजेक्ट", "mr_latn": "ready to move project"},
    "bhk": {"en": "{bhk} homes", "hinglish": "{bhk} ghar", "hi": "{bhk} घर", "mr": "{bhk} घरे", "mr_latn": "{bhk} ghare"},
}


def list_what(kind: str, lang: str = "en", **kw) -> str:
    table = LIST_WHAT.get(kind) or LIST_WHAT["all"]
    return table.get(lang, table["en"]).format(**kw)


# quick replies the engine understands in every language (the parser reads the English and these)
QUICK = {
    "not_now": {"en": "Not now", "hinglish": "Abhi nahi", "hi": "अभी नहीं", "mr": "आता नको", "mr_latn": "Aata nako"},
    "about_it": {"en": "Tell me about it", "hinglish": "Iske baare mein batao", "hi": "इसके बारे में बताइए", "mr": "याबद्दल सांगा", "mr_latn": "Yabaddal sanga"},
    "similar": {"en": "Similar homes", "hinglish": "Aise aur ghar", "hi": "ऐसे और घर", "mr": "असेच घर", "mr_latn": "Asech ghar"},
    "find_home": {"en": "Find a home", "hinglish": "Ghar dhoondhna hai", "hi": "घर ढूँढना है", "mr": "घर शोधायचे आहे", "mr_latn": "Ghar shodhayche aahe"},
    "im_agent": {"en": "I'm an agent", "hinglish": "Main agent hoon", "hi": "मैं एजेंट हूँ", "mr": "मी एजंट आहे", "mr_latn": "Mi agent aahe"},
    "show_homes": {"en": "Show homes", "hinglish": "Ghar dikhao", "hi": "घर दिखाइए", "mr": "घरे दाखवा", "mr_latn": "Ghare dakhva"},
    # a project page's two asks, as its enquiry form names them (lib/site/strings.ts PROJECT_CTA pricesChoice, visitChoice)
    "sheet": {"en": "Price sheet & floor plans", "hinglish": "Price sheet & floor plans", "hi": "प्राइस शीट और फ्लोर प्लान",
              "mr": "प्राइस शीट आणि फ्लोर प्लॅन", "mr_latn": "Price sheet ani floor plan"},
    "visit": {"en": "Site visit", "hinglish": "Site visit", "hi": "साइट विज़िट", "mr": "साइट व्हिजिट", "mr_latn": "Site visit"},
    # after the projects they read earlier in this visit: compare the two (chat/agent.py _history_ask)
    "compare": {"en": "Compare them", "hinglish": "Compare karo", "hi": "तुलना कीजिए", "mr": "तुलना करा", "mr_latn": "Tulna kara"},
    # chat/plan.py: today's prices for the plan they made; the link to the plan's questions
    "plan_prices": {"en": "Today's prices for my plan", "hinglish": "Mere plan ke aaj ke prices", "hi": "मेरे प्लान की आज की कीमत",
                    "mr": "माझ्या प्लॅनच्या आजच्या किमती", "mr_latn": "Majhya plan chya aajchya kimati"},
    "try_plan": {"en": "Try the home plan", "hinglish": "Home plan try karein", "hi": "होम प्लान आज़माएँ", "mr": "होम प्लॅन वापरून पहा",
                 "mr_latn": "Home plan vaprun paha"},
    # an agent page's asks: English only, since each is a keyword of its answer in knowledge/site.py
    "agent_trial": {"en": "Free trial"},
    "agent_price": {"en": "Pricing"},
    "agent_start": {"en": "How do I start?"},
}


def is_quick(text: str, key: str) -> bool:
    """The visitor tapped (or typed) this quick reply, in any language."""
    t = " ".join((text or "").split()).strip(" .!?").lower()
    return any(t == v.lower().strip(" .!?") for v in QUICK[key].values())
# a quick reply naming one project they read earlier in this visit: "{project} price sheet"
QUICK_FOR = {
    "sheet_for": {"en": "{project} price sheet", "hinglish": "{project} price sheet", "hi": "{project} प्राइस शीट",
                  "mr": "{project} प्राइस शीट", "mr_latn": "{project} price sheet"},
    # the note beside the chat button (chat/nudge.py): the name here is the area's
    "hot_in": {"en": "Hot projects in {project}", "hinglish": "{project} ke hot projects", "hi": "{project} के हॉट प्रोजेक्ट",
               "mr": "{project} मधील हॉट प्रोजेक्ट", "mr_latn": "{project} madhil hot project"},
}


def quick_for(key: str, lang: str, project: str) -> str:
    return QUICK_FOR[key].get(lang, QUICK_FOR[key]["en"]).format(project=project)


def is_quick_for(text: str, key: str, project: str) -> bool:
    """The visitor tapped (or typed) this project's quick reply, in any language."""
    t = " ".join((text or "").split()).strip(" .!?").lower()
    return any(t == v.format(project=project).lower().strip(" .!?") for v in QUICK_FOR[key].values())


# "Hindi", "मराठीत बोला", "marathi madhe": a buyer choosing a language. The website chat's header offers them; our WhatsApp follow-up
# invites the same ("Hindi ya Marathi mein baat karna ho to bataiye")
_SAY = r"(?:\s+(?:me|mein|main|mai|madhe|madhye|please|pls|bolo|bola|bolu|baat|karo|karein|kijiye|में|मध्ये|बोलिए|बोला|बोलो|बात|करें|कीजिए))*"
LANG_ASK = (("hi", re.compile(rf"^\W*(?:hindi|हिंदी|हिन्दी){_SAY}\W*$", re.I)), ("mr", re.compile(rf"^\W*(?:marathi|marathit|मराठी|मराठीत){_SAY}\W*$", re.I)),
            ("en", re.compile(rf"^\W*(?:english|इंग्लिश|इंग्रजी){_SAY}\W*$", re.I)))
ROMAN = {"hi": "hinglish", "mr": "mr_latn"}


def asked_language(text: str) -> Optional[str]:
    """The language they chose, in the script they chose it in; None when the message does not choose one."""
    t = (text or "").strip()
    lang = next((k for k, rx in LANG_ASK if rx.match(t)), None)
    return ROMAN.get(lang, lang) if t.isascii() else lang


WHATSAPP = "Continue on WhatsApp"


def say(key: str, lang: str = "en", **kw) -> str:
    table = P[key]
    return table.get(lang if lang in LANGS else "en", table["en"]).format(**kw)


def quick(key: str, lang: str = "en") -> str:
    return QUICK[key].get(lang, QUICK[key]["en"])
