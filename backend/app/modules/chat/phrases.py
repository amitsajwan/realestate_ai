"""The website assistant's fixed sentences in the buyer's language: en, hinglish (Hindi in Roman letters), hi, mr (Devanagari), mr_latn.

Only the sentences the engine controls live here (greetings, the questions, the number ask, no-match, thanks). Answers from the vetted
knowledge stay as the knowledge module returns them. The English sentences the WhatsApp module translates on its own (lang.FIXED) are kept
word for word, so a WhatsApp buyer (who gets English from the engine) is still translated there.

`say(key, lang, **kw)` never mixes: a key missing in a language falls back to the whole English sentence, never half of one.
"""
from typing import Dict

from app.core import brand

LANGS = ("en", "hinglish", "hi", "mr", "mr_latn")

P: Dict[str, Dict[str, str]] = {
    # ---- greetings (kept short) -----------------------------------------------------------------------------------
    "greet": {
        "en": f"Hi! I am the {brand.NAME} assistant. I can answer basic questions about buying or renting in Pune and pass your requirement to our team.",
        "hinglish": f"Namaste! Main {brand.NAME} ka assistant hoon. Pune mein ghar kharidne ya rent par lene ke basic sawaalon ke jawab de sakta hoon aur aapki requirement hamari team tak pahuncha sakta hoon.",
        "hi": f"नमस्ते! मैं {brand.NAME_DEVANAGARI} का सहायक हूँ। मैं पुणे में घर खरीदने या किराए पर लेने के बारे में आम सवालों के जवाब दे सकता हूँ और आपकी ज़रूरत हमारी टीम तक पहुँचा सकता हूँ।",
        "mr": f"नमस्कार! मी {brand.NAME_DEVANAGARI} चा सहाय्यक आहे. पुण्यात घर घेणे किंवा भाड्याने घेणे याबद्दलच्या साध्या प्रश्नांची उत्तरे देऊ शकतो आणि तुमची गरज आमच्या टीमपर्यंत पोहोचवू शकतो.",
        "mr_latn": f"Namaskar! Mi {brand.NAME} cha sahayyak aahe. Punyat ghar ghene kiwa bhadyane ghene yabaddal sadhya prashnanchi uttare deu shakto ani tumchi garaj aamchya team paryant pohochvu shakto.",
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
    "greet_area": {
        "en": "Looking at homes in {area}? I can answer questions about the area or show homes there.",
        "hinglish": "{area} mein ghar dekh rahe hain? Main area ke sawaalon ke jawab de sakta hoon ya wahan ke ghar dikha sakta hoon.",
        "hi": "{area} में घर देख रहे हैं? मैं इलाके के सवालों के जवाब दे सकता हूँ या वहाँ के घर दिखा सकता हूँ।",
        "mr": "{area} मध्ये घर पाहत आहात? मी या भागाबद्दलच्या प्रश्नांची उत्तरे देऊ शकतो किंवा तिथली घरे दाखवू शकतो.",
        "mr_latn": "{area} madhye ghar pahat aahat? Mi ya bhagabaddal prashnanchi uttare deu shakto kiwa tithli ghare dakhavu shakto.",
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


# quick replies the engine understands in every language (the parser reads the English and these)
QUICK = {
    "not_now": {"en": "Not now", "hinglish": "Abhi nahi", "hi": "अभी नहीं", "mr": "आता नको", "mr_latn": "Aata nako"},
    "about_it": {"en": "Tell me about it", "hinglish": "Iske baare mein batao", "hi": "इसके बारे में बताइए", "mr": "याबद्दल सांगा", "mr_latn": "Yabaddal sanga"},
    "similar": {"en": "Similar homes", "hinglish": "Aise aur ghar", "hi": "ऐसे और घर", "mr": "असेच घर", "mr_latn": "Asech ghar"},
    "show_homes": {"en": "Show homes", "hinglish": "Ghar dikhao", "hi": "घर दिखाइए", "mr": "घरे दाखवा", "mr_latn": "Ghare dakhva"},
}
WHATSAPP = "Continue on WhatsApp"


def say(key: str, lang: str = "en", **kw) -> str:
    table = P[key]
    return table.get(lang if lang in LANGS else "en", table["en"]).format(**kw)


def quick(key: str, lang: str = "en") -> str:
    return QUICK[key].get(lang, QUICK[key]["en"])
