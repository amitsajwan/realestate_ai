"""Words that code (not a model) puts on a card or in a caption, in every post language, and the spelling glossary for
place names in Marathi and Hindi.

`ui(key, lang)` gives a card's fixed words ("Swipe", "MYTH", "Call / WhatsApp"); `known(text, lang)` translates a fixed
English string the copywriter chose (a card CTA, a default kicker) or returns None; `fix_spelling(text, lang)` corrects the
misspellings models make of our place names and land units (रंजनगांव -> रांजणगाव, गुनथा -> गुंठा). Pure data and functions."""
import re
from typing import Dict, Optional

UI: Dict[str, Dict[str, str]] = {
    "swipe": {"en": "Swipe", "mr": "पुढे पाहा", "hi": "आगे देखें"},
    "save_this": {"en": "Save this", "mr": "सेव्ह करा", "hi": "सेव करें"},
    "myth": {"en": "MYTH", "mr": "गैरसमज", "hi": "मिथक"},
    "fact": {"en": "FACT", "mr": "सत्य", "hi": "सच"},
    "vs": {"en": "VS", "mr": "VS", "hi": "VS"},
    "vote_ab": {"en": "Vote A or B in the comments", "mr": "कमेंटमध्ये A किंवा B लिहा", "hi": "कमेंट में A या B लिखें"},
    "illustrative": {"en": "Illustrative photo", "mr": "प्रातिनिधिक फोटो", "hi": "प्रतीकात्मक फोटो"},
    "n_things": {"en": "{n} things, one per slide", "mr": "{n} मुद्दे, प्रत्येक स्लाइडवर एक", "hi": "{n} बातें, हर स्लाइड पर एक"},
    "call": {"en": "Call / WhatsApp", "mr": "कॉल / WhatsApp", "hi": "कॉल / WhatsApp"},
    "price": {"en": "Price", "mr": "किंमत", "hi": "कीमत"},
    "maharera": {"en": "MahaRERA", "mr": "MahaRERA", "hi": "MahaRERA"},
    "ask": {"en": "Ask for details", "mr": "माहितीसाठी संपर्क करा", "hi": "जानकारी के लिए संपर्क करें"},
}

# Fixed English strings the copywriter may put on a card (CARD_CTA, KICKER): their translations.
KNOWN: Dict[str, Dict[str, str]] = {
    "Save this": UI["save_this"],
    "Save this list": {"en": "Save this list", "mr": "ही यादी सेव्ह करा", "hi": "यह लिस्ट सेव करें"},
    "Share with a buyer": {"en": "Share with a buyer", "mr": "खरेदीदाराला पाठवा", "hi": "खरीदार को भेजें"},
    "Vote in the comments": {"en": "Vote in the comments", "mr": "कमेंटमध्ये मत द्या", "hi": "कमेंट में वोट करें"},
    "Swipe": UI["swipe"],
    "WORTH REMEMBERING": {"en": "WORTH REMEMBERING", "mr": "लक्षात ठेवा", "hi": "याद रखें"},
    "MYTH VS FACT": {"en": "MYTH VS FACT", "mr": "गैरसमज विरुद्ध सत्य", "hi": "मिथक बनाम सच"},
    "THIS OR THAT": {"en": "THIS OR THAT", "mr": "हे की ते", "hi": "यह या वह"},
    "SAVE THIS": {"en": "SAVE THIS", "mr": "सेव्ह करा", "hi": "सेव करें"},
    "SWIPE THROUGH": {"en": "SWIPE THROUGH", "mr": "पुढे पाहा", "hi": "आगे देखें"},
    "BUYER NOTE": {"en": "BUYER NOTE", "mr": "खरेदीदारांसाठी", "hi": "खरीदारों के लिए"},
    "QUICK TIP": {"en": "QUICK TIP", "mr": "छोटी टीप", "hi": "छोटी सलाह"},
}


def ui(key: str, lang: str = "en", **fmt) -> str:
    row = UI[key]
    text = row.get(lang) or row["en"]
    return text.format(**fmt) if fmt else text


_MONEY = {"mr": {"lakh": "लाख", "crore": "कोटी"}, "hi": {"lakh": "लाख", "crore": "करोड़"}}


def money(text: str, lang: str) -> str:
    """'₹32.3 lakh' -> '₹32.3 लाख' on a Marathi/Hindi card (the digits stay as they are)."""
    words = _MONEY.get(lang)
    if not words or not text:
        return text
    return re.sub(r"\b(lakh|crore)s?\b", lambda m: words[m.group(1).lower()], text, flags=re.I)


def known(text: str, lang: str) -> Optional[str]:
    """The fixed translation of a code-chosen English string, or None when `text` is not one."""
    row = KNOWN.get((text or "").strip())
    return row.get(lang) if row else None


# Place names as Marathi and Hindi write them. Every area in app/core/areas.py has an entry (a test checks it).
PLACES: Dict[str, Dict[str, str]] = {
    "Pune": {"mr": "पुणे", "hi": "पुणे"},
    "Kharadi": {"mr": "खराडी", "hi": "खराडी"},
    "Upper Kharadi": {"mr": "अप्पर खराडी", "hi": "अपर खराडी"},
    "Wagholi": {"mr": "वाघोली", "hi": "वाघोली"},
    "Lohegaon": {"mr": "लोहगाव", "hi": "लोहगांव"},
    "Keshav Nagar": {"mr": "केशवनगर", "hi": "केशव नगर"},
    "Hinjawadi": {"mr": "हिंजवडी", "hi": "हिंजवडी"},
    "Wakad": {"mr": "वाकड", "hi": "वाकड"},
    "Baner": {"mr": "बाणेर", "hi": "बाणेर"},
    "Ranjangaon": {"mr": "रांजणगाव", "hi": "रांजणगांव"},
    "Shikrapur": {"mr": "शिक्रापूर", "hi": "शिक्रापुर"},
    "Shirur": {"mr": "शिरूर", "hi": "शिरूर"},
}
# Words of the trade with one right spelling.
TERMS: Dict[str, Dict[str, str]] = {
    "guntha": {"mr": "गुंठा", "hi": "गुंठा"},
    "plot": {"mr": "प्लॉट", "hi": "प्लॉट"},
}

# Misspellings models write -> the right spelling. A wrong form is matched at the start of a word, so its suffixes stay
# (रंजनगांवमध्ये -> रांजणगावमध्ये).
MISSPELLED: Dict[str, Dict[str, str]] = {
    "mr": {
        "गुनथा": "गुंठा", "गुंथा": "गुंठा", "गुन्था": "गुंठा", "गुंटा": "गुंठा", "गुणठा": "गुंठा",
        "रंजनगांव": "रांजणगाव", "रंजनगाव": "रांजणगाव", "रांजनगांव": "रांजणगाव", "रांजनगाव": "रांजणगाव",
        "रांजणगांव": "रांजणगाव", "रंजणगाव": "रांजणगाव", "रंजणगांव": "रांजणगाव",
        "शिक्रापुर": "शिक्रापूर", "शिरुर": "शिरूर", "लोहगांव": "लोहगाव", "लोहेगाव": "लोहगाव", "लोहेगांव": "लोहगाव",
        "हिंजेवाडी": "हिंजवडी", "हिंजवाडी": "हिंजवडी", "हिंजेवडी": "हिंजवडी", "बानेर": "बाणेर", "खरडी": "खराडी",
        "वाघोलि": "वाघोली", "केशव नगर": "केशवनगर",
    },
    "hi": {
        "गुनथा": "गुंठा", "गुंथा": "गुंठा", "गुन्था": "गुंठा", "गुंटा": "गुंठा",
        "रंजनगांव": "रांजणगांव", "रंजनगाव": "रांजणगांव", "रांजनगांव": "रांजणगांव", "रांजनगाव": "रांजणगांव",
        "रांजणगाव": "रांजणगांव", "शिरुर": "शिरूर", "हिंजेवाडी": "हिंजवडी", "हिंजवाडी": "हिंजवडी", "बानेर": "बाणेर",
    },
}
_DEV = "ऀ-ॿ"


def _pattern(lang: str) -> Optional["re.Pattern[str]"]:
    table = MISSPELLED.get(lang)
    if not table:
        return None
    alts = "|".join(re.escape(w) for w in sorted(table, key=len, reverse=True))
    return re.compile(rf"(?<![{_DEV}\w])(?:{alts})")


_PATTERNS = {lang: _pattern(lang) for lang in MISSPELLED}


def fix_spelling(text: str, lang: str) -> str:
    pat = _PATTERNS.get(lang)
    if not pat or not text:
        return text
    return pat.sub(lambda m: MISSPELLED[lang][m.group(0)], text)


def glossary(lang: str) -> str:
    """'Ranjangaon = रांजणगाव, ...' for the translator prompt."""
    pairs = [f"{en} = {row[lang]}" for en, row in {**PLACES, **TERMS}.items() if lang in row]
    return ", ".join(pairs)
