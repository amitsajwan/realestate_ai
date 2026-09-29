"""Text normalisation: Devanagari numerals/words and Hindi/Marathi keywords -> ASCII forms."""
import re
import unicodedata

_DIGITS = {ord(c): str(i) for i, c in enumerate("०१२३४५६७८९")}

_HI_NUM = (
    "एक दो तीन चार पांच छह सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस बीस "
    "इक्कीस बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस तीस इकतीस बत्तीस तैंतीस चौंतीस पैंतीस "
    "छत्तीस सैंतीस अड़तीस उनतालीस चालीस इकतालीस बयालीस तैंतालीस चौवालीस पैंतालीस छियालीस सैंतालीस "
    "अड़तालीस उनचास पचास इक्यावन बावन तिरपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ साठ इकसठ बासठ "
    "तिरसठ चौंसठ पैंसठ छियासठ सड़सठ अड़सठ उनहत्तर सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर पचहत्तर छिहत्तर "
    "सतहत्तर अठहत्तर उनासी अस्सी इक्यासी बयासी तिरासी चौरासी पचासी छियासी सत्तासी अट्ठासी नवासी नब्बे "
    "इक्यानवे बानवे तिरानवे चौरानवे पंचानवे छियानवे सत्तानवे अट्ठानवे निन्यानवे सौ"
).split()
NUM_WORDS: dict[str, int] = {w: i + 1 for i, w in enumerate(_HI_NUM)}
NUM_WORDS.update({"पाँच": 5, "छः": 6})
NUM_WORDS.update({  # Marathi variants
    "दोन": 2, "पाच": 5, "सहा": 6, "नऊ": 9, "दहा": 10, "पंधरा": 15, "वीस": 20, "पंचवीस": 25, "पस्तीस": 35,
    "चाळीस": 40, "पंचेचाळीस": 45, "पन्नास": 50, "पंचावन्न": 55, "पासष्ट": 65, "ऐंशी": 80, "पंच्याऐंशी": 85,
    "नव्वद": 90, "पंचाण्णव": 95, "पंचाहत्तर": 75,
})

# a Devanagari number word is only converted when the next token is one of these (avoids "एक बड़ा ...")
_UNIT_TOKENS = {"lakh", "cr", "bhk", "thousand", "floor", "sqft"}

_REPL = [
    ("स्क्वेअर फूट", " sqft "), ("स्क्वेयर फीट", " sqft "), ("स्क्वेअर फुट", " sqft "), ("स्क्वेयर फुट", " sqft "),
    ("स्क्वायर फीट", " sqft "), ("वर्ग फूट", " sqft "), ("वर्ग फुट", " sqft "), ("चौरस फूट", " sqft "),
    ("चौरस फुट", " sqft "), ("स्क्वेअरफूट", " sqft "), ("स्क्वेअर फिट", " sqft "),
    ("स्क्वेयर यार्ड", " sqyd "), ("वर्ग गज", " sqyd "),
    ("बीएचके", " bhk "), ("बी.एच.के", " bhk "), ("बी एच के", " bhk "),
    ("रेडी टू मूव", " ready to move "), ("रेडी पझेशन", " ready possession "), ("रेडी पजेशन", " ready possession "),
    ("तयार", " ready "), ("तैयार", " ready "), ("अंडर कंस्ट्रक्शन", " under construction "),
    ("बांधकाम सुरू", " under construction "), ("पझेशन", " possession "), ("पजेशन", " possession "),
    ("कारपेट", " carpet "), ("सुपर बिल्ट अप", " super built up "), ("सुपर बिल्टअप", " super built up "),
    ("सेमी फर्निश्ड", " semi furnished "), ("सेमी फर्निश", " semi furnished "), ("अनफर्निश्ड", " unfurnished "),
    ("फर्निश्ड", " furnished "),
    ("भाड्याने", " rent "), ("भाड्यानं", " rent "), ("किराये", " rent "), ("किराए", " rent "), ("किराया", " rent "),
    ("भाड़े", " rent "), ("भाडे", " rent "), ("भाडं", " rent "), ("भाडेतत्वावर", " rent "),
    ("विक्रीसाठी", " sale "), ("विक्री", " sale "), ("बिक्री", " sale "), ("विकाऊ", " sale "), ("बेचना", " sale "),
    ("प्रति महिना", " per month "), ("प्रति माह", " per month "), ("प्रतिमाह", " per month "),
    ("दर महिना", " per month "), ("महिना", " month "), ("महीना", " month "),
    ("लाखों", " lakh "), ("लाखाचे", " lakh "), ("लाख", " lakh "),
    ("करोड़", " cr "), ("करोड", " cr "), ("कोटी", " cr "), ("हजार", " thousand "), ("हज़ार", " thousand "),
    ("मंजिल", " floor "), ("मजल्यावर", " floor "), ("मजला", " floor "), ("माळा", " floor "),
    ("फ्लॅट", " flat "), ("फ्लैट", " flat "), ("प्लॉट", " plot "), ("बंगला", " bungalow "), ("बंगलो", " bungalow "),
    ("दुकान", " shop "), ("ऑफिस", " office "), ("पार्किंग", " parking "), ("लिफ्ट", " lift "), ("जिम", " gym "),
    ("स्विमिंग पूल", " swimming pool "), ("गार्डन", " garden "), ("सिक्युरिटी", " security "),
    ("क्लबहाऊस", " clubhouse "), ("क्लब हाउस", " clubhouse "), ("पॉवर बॅकअप", " power backup "),
    ("पावर बैकअप", " power backup "), ("टॉप", " top "), ("रेरा", " rera "),
]
_REPL.sort(key=lambda p: -len(p[0]))
_ORD_SUFFIX = re.compile(r"(\d+)\s*(?:वी|वा|रा|री|ऱ्या|था|थी|ला|ली|ले|वें|वे)\s*(?=floor)")
_SPACES = re.compile(r"[ \t]+")


def normalise(text: str) -> str:
    """Lowercase, translate Devanagari numerals/keywords to ASCII forms; keeps Devanagari place names."""
    t = unicodedata.normalize("NFC", text or "").translate(_DIGITS).lower()
    for src, dst in _REPL:
        if src in t:
            t = t.replace(src, dst)
    t = _numberwords(t)
    t = _ORD_SUFFIX.sub(lambda m: m.group(1) + "th ", t)
    return _SPACES.sub(" ", t).strip()


def _numberwords(t: str) -> str:
    toks = t.split(" ")
    for i, tok in enumerate(toks):
        core = tok.strip(",.;:()")
        if core in NUM_WORDS:
            nxt = next((x.strip(",.;:()") for x in toks[i + 1:] if x.strip()), "")
            if nxt in _UNIT_TOKENS:
                toks[i] = tok.replace(core, str(NUM_WORDS[core]))
    return " ".join(toks)
