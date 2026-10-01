"""The buyer's language on WhatsApp. The chat engine speaks English; its fixed sentences (greeting, the five questions, hand-offs) are swapped
here for Hindi, Marathi, Hinglish or romanised Marathi, and our own WhatsApp lines (data-use notice, STOP, media) exist in all five.
Answers from the vetted knowledge are translated by the knowledge module's checked translator (numbers and names must survive) or stay English."""
import re
from typing import Dict, List, Optional, Tuple

from app.core import brand

LANGS = ("en", "hi", "mr", "hinglish", "mr_latn")

# English sentence from chat.engine -> {lang: translation}
FIXED: List[Tuple[str, Dict[str, str]]] = [
    (f"Hi! I am the {brand.NAME} assistant. I can answer basic questions about buying or renting in Pune and pass your requirement to our team.", {
        "hi": f"नमस्ते! मैं {brand.NAME_DEVANAGARI} का सहायक हूँ। मैं पुणे में घर खरीदने या किराए पर लेने के बारे में आम सवालों के जवाब दे सकता हूँ और आपकी ज़रूरत हमारी टीम तक पहुँचा सकता हूँ।",
        "hinglish": f"Namaste! Main {brand.NAME} ka assistant hoon. Pune mein ghar kharidne ya rent par lene ke basic sawaalon ke jawab de sakta hoon aur aapki requirement hamari team tak pahuncha sakta hoon.",
        "mr": f"नमस्कार! मी {brand.NAME_DEVANAGARI} चा सहाय्यक आहे. पुण्यात घर घेणे किंवा भाड्याने घेणे याबद्दलच्या साध्या प्रश्नांची उत्तरे देऊ शकतो आणि तुमची गरज आमच्या टीमपर्यंत पोहोचवू शकतो.",
        "mr_latn": f"Namaskar! Mi {brand.NAME} cha sahayyak aahe. Punyat ghar ghene kiwa bhadyane ghene yabaddal sadhya prashnanchi uttare deu shakto ani tumchi garaj aamchya team paryant pohochvu shakto."}),
    ("Are you looking to buy or to rent?", {
        "hi": "क्या आप घर खरीदना चाहते हैं या किराए पर लेना?", "hinglish": "Aap ghar kharidna chahte hain ya rent par lena?",
        "mr": "तुम्हाला घर विकत घ्यायचे आहे की भाड्याने?", "mr_latn": "Tumhala ghar vikat ghyayche aahe ki bhadyane?"}),
    ("Which area are you most interested in?", {
        "hi": "आपको कौन सा इलाका सबसे ज़्यादा पसंद है?", "hinglish": "Aapko kaun sa area sabse zyada pasand hai?",
        "mr": "तुम्हाला कोणता भाग सर्वात जास्त आवडतो?", "mr_latn": "Tumhala konta bhag sarvat jast aavadto?"}),
    ("How many bedrooms do you need?", {
        "hi": "आपको कितने बेडरूम चाहिए?", "hinglish": "Aapko kitne bedroom chahiye?",
        "mr": "तुम्हाला किती बेडरूम हवे आहेत?", "mr_latn": "Tumhala kiti bedroom have aahet?"}),
    ("What budget do you have in mind?", {
        "hi": "आपका बजट कितना है?", "hinglish": "Aapka budget kitna hai?", "mr": "तुमचे बजेट किती आहे?", "mr_latn": "Tumche budget kiti aahe?"}),
    ("When are you planning to move?", {
        "hi": "आप कब तक शिफ्ट होना चाहते हैं?", "hinglish": "Aap kab tak shift hona chahte hain?",
        "mr": "तुम्ही कधी शिफ्ट होण्याचा विचार करत आहात?", "mr_latn": "Tumhi kadhi shift honyacha vichar karat aahat?"}),
    ("Is there anything else I can help you with?", {
        "hi": "क्या मैं आपकी और कोई मदद कर सकता हूँ?", "hinglish": "Kya main aapki aur koi madad kar sakta hoon?",
        "mr": "अजून काही मदत हवी आहे का?", "mr_latn": "Ajun kahi madat havi aahe ka?"}),
    ("I do not want to guess on that one. I will ask our team to confirm it for you.", {
        "hi": "इस बारे में मैं अंदाज़ा नहीं लगाना चाहता। मैं हमारी टीम से इसकी पुष्टि करवा दूँगा।",
        "hinglish": "Is baare mein main andaaza nahi lagana chahta. Hamari team se confirm karwa deta hoon.",
        "mr": "याबद्दल मी अंदाज लावू इच्छित नाही. आमच्या टीमकडून खात्री करून घेतो.",
        "mr_latn": "Yabaddal mi andaj lavu ichhit nahi. Aamchya team kadun khatri karun gheto."}),
    ("Of course, our team can take it from here.", {
        "hi": "ज़रूर, हमारी टीम आपसे बात करेगी।", "hinglish": "Zaroor, hamari team aapse baat karegi.",
        "mr": "नक्की, आमची टीम तुमच्याशी बोलेल.", "mr_latn": "Nakki, aamchi team tumchyashi bolel."}),
    ("I will pass this to our team so they can look into it. If you would like help finding a home, just tell me what you need.", {
        "hi": "मैं यह हमारी टीम तक पहुँचा दूँगा। अगर आपको घर ढूँढने में मदद चाहिए, तो बस बताइए।",
        "hinglish": "Main yeh hamari team tak pahuncha deta hoon. Ghar dhoondhne mein madad chahiye to bas bataiye.",
        "mr": "मी हे आमच्या टीमपर्यंत पोहोचवतो. घर शोधायला मदत हवी असल्यास सांगा.",
        "mr_latn": "Mi he aamchya team paryant pohochavto. Ghar shodhayla madat havi aslyas sanga."}),
]
GOT_IT = {"en": "Got it: ", "hi": "ठीक है: ", "hinglish": "Theek hai: ", "mr": "ठीक आहे: ", "mr_latn": "Theek aahe: "}
OPTIONS = {"en": "Reply with: ", "hi": "जवाब दें: ", "hinglish": "Reply karein: ", "mr": "उत्तर द्या: ", "mr_latn": "Uttar dya: "}

NOTICE = {
    "en": "Note: {agent} will contact you on this WhatsApp number about your enquiry. Reply STOP at any time and we will not message you again.",
    "hi": "सूचना: {agent} इसी WhatsApp नंबर पर आपकी पूछताछ के बारे में आपसे संपर्क करेंगे। संदेश बंद करवाने के लिए कभी भी STOP लिखें।",
    "hinglish": "Note: {agent} isi WhatsApp number par aapki enquiry ke baare mein aapse contact karenge. Messages band karne ke liye kabhi bhi STOP likhein.",
    "mr": "सूचना: {agent} तुमच्या चौकशीबद्दल याच WhatsApp नंबरवर तुमच्याशी संपर्क साधतील. मेसेज बंद करण्यासाठी कधीही STOP लिहा.",
    "mr_latn": "Note: {agent} tumchya chaukashibaddal yach WhatsApp number var tumchyashi samparka sadhtil. Message band karnyasathi kadhihi STOP liha.",
}
TEAM = {"en": f"The {brand.NAME} team", "hi": f"{brand.NAME_DEVANAGARI} की टीम", "hinglish": f"{brand.NAME} ki team", "mr": f"{brand.NAME_DEVANAGARI} ची टीम",
        "mr_latn": f"{brand.NAME} chi team"}
STOPPED = {
    "en": "Done. You will not get any more messages from us here. If you change your mind, reply START.",
    "hi": "ठीक है। अब आपको यहाँ हमारी ओर से कोई संदेश नहीं मिलेगा। फिर से बात करनी हो तो START लिखें।",
    "hinglish": "Theek hai. Ab aapko yahan hamari taraf se koi message nahi aayega. Dobara baat karni ho to START likhein.",
    "mr": "ठीक आहे. आता तुम्हाला इथे आमच्याकडून कोणताही मेसेज येणार नाही. पुन्हा बोलायचे असल्यास START लिहा.",
    "mr_latn": "Theek aahe. Aata tumhala ithe aamchyakadun kontahi message yenar nahi. Punha bolayche aslyas START liha.",
}
RESTARTED = {
    "en": "Welcome back! Tell me what you are looking for, or ask me anything about homes in Pune.",
    "hi": "फिर से स्वागत है! बताइए आप क्या ढूँढ रहे हैं, या पुणे में घरों के बारे में कुछ भी पूछिए।",
    "hinglish": "Welcome back! Bataiye aap kya dhoondh rahe hain, ya Pune mein gharon ke baare mein kuch bhi poochhiye.",
    "mr": "पुन्हा स्वागत आहे! तुम्ही काय शोधत आहात ते सांगा, किंवा पुण्यातील घरांबद्दल काहीही विचारा.",
    "mr_latn": "Punha swagat aahe! Tumhi kay shodhat aahat te sanga, kiwa Punyatil gharanbaddal kahihi vichara.",
}
MEDIA = {
    "en": "Thanks! I can only read text messages here. Please type your question, or tell me the area, BHK and budget you are looking for.",
    "hi": "धन्यवाद! मैं यहाँ सिर्फ़ लिखे हुए संदेश पढ़ सकता हूँ। कृपया अपना सवाल लिखें, या इलाका, BHK और बजट बताइए।",
    "hinglish": "Thanks! Main yahan sirf text messages padh sakta hoon. Apna sawaal type karein, ya area, BHK aur budget bataiye.",
    "mr": "धन्यवाद! मी इथे फक्त लिहिलेले मेसेज वाचू शकतो. कृपया तुमचा प्रश्न लिहा, किंवा भाग, BHK आणि बजेट सांगा.",
    "mr_latn": "Dhanyavad! Mi ithe fakt lihilele message vachu shakto. Krupaya tumcha prashna liha, kiwa bhag, BHK ani budget sanga.",
}
LOCATION = {
    "en": "Thanks for the location. Please also type the area name (for example Kharadi or Wagholi) so I can help.",
    "hi": "लोकेशन के लिए धन्यवाद। कृपया इलाके का नाम भी लिखें (जैसे Kharadi या Wagholi), ताकि मैं मदद कर सकूँ।",
    "hinglish": "Location ke liye thanks. Area ka naam bhi type karein (jaise Kharadi ya Wagholi), taaki main madad kar sakoon.",
    "mr": "लोकेशनसाठी धन्यवाद. कृपया भागाचे नावही लिहा (उदा. Kharadi किंवा Wagholi), म्हणजे मी मदत करू शकेन.",
    "mr_latn": "Location sathi dhanyavad. Krupaya bhagache naav pan liha (udaharanarth Kharadi kiwa Wagholi), mhanje mi madat karu shaken.",
}

ENGLISH_RUN = re.compile(r"[A-Za-z][A-Za-z,'’-]*(?:\s+[A-Za-z][A-Za-z,'’-]*){5,}")


def pick(table: Dict[str, str], lang: str, **kw) -> str:
    return table.get(lang, table["en"]).format(**kw)


def sticky(previous: Optional[str], detected: str, text: str) -> str:
    """Keep the conversation's language across short answers ('2 BHK', 'Kharadi'): switch only on a non-English message, or on a clearly
    English sentence of four words or more."""
    if detected != "en":
        return detected
    if previous and previous != "en" and len((text or "").split()) < 4:
        return previous
    return "en"


def localise_fixed(text: str, lang: str) -> Tuple[str, bool]:
    """Swap the engine's fixed English sentences. Returns (text, english_left) where english_left says a longer English passage (for example a
    vetted knowledge answer) is still in it."""
    if lang == "en" or lang not in LANGS:
        return text, False
    out, residual = text, text
    for en, tr in FIXED:
        if en in out and lang in tr:
            out = out.replace(en, tr[lang])
        residual = residual.replace(en, "")
    if out.startswith(GOT_IT["en"]):
        out = GOT_IT[lang] + out[len(GOT_IT["en"]):]
    residual = re.sub(r"Got it: [^.]*\.", "", residual)
    return out, bool(ENGLISH_RUN.search(residual))


def options_line(quick: List[str], lang: str) -> str:
    q = [x for x in quick if x][:5]
    return (OPTIONS.get(lang, OPTIONS["en"]) + " / ".join(q)) if q else ""
