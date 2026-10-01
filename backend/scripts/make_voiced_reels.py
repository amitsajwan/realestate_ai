"""Make voiced sample reels with the AI director (run on the server, where the LLM and voice keys are):
  docker compose exec -T -e PYTHONPATH=. backend python scripts/make_voiced_reels.py
Writes uploads/reels/voiced-*.mp4 and prints the scripts. Posts nothing."""
import asyncio
import json
import os
from pathlib import Path

from app.modules.ai_listing.llm import default_llm
from app.modules.reels import director
from app.modules.showcase.samples import get

PHOTOS = Path("app/modules/showcase/assets/photos")
UP = Path(os.environ.get("UPLOAD_DIRECTORY", "uploads")) / "reels"


def home_facts(slug):
    h = get(slug)
    return (f"Sample home (illustrative, not for sale): {h.bhk} BHK in {h.locality}, Pune",
            [f"{h.bhk} BHK in {h.locality}, Pune", f"Carpet area {h.carpet_sqft} sq ft", f"Floor {h.floor} of {h.total_floors}",
             f"{h.possession}", f"{h.furnishing}", "Amenities: " + ", ".join(h.amenities),
             "Kharadi is an established IT-office hub on Pune's east side, with EON IT Park and World Trade Center Pune",
             "This is a sample home shown for illustration, not available for sale"])


HOME_FALLBACK = {
    "en": {"beats": [{"screen": "*2BHK* in Kharadi?", "voice": "Looking for a two BHK in Kharadi? Here is what you actually get."},
                     {"screen": "*780* sq ft carpet", "voice": "Seven hundred and eighty square feet of carpet area."},
                     {"screen": "Floor *7* of 22", "voice": "Seventh floor, ready to move, semi-furnished."},
                     {"screen": "Parking · Gym · *Lift*", "voice": "With parking, a gym, lifts, security and power backup."}],
           "cta_screen": "Tap *interested* · link in bio", "cta_voice": "This is a sample home. Tap interested in our bio and we will find you a real one."},
    "hi": {"beats": [{"screen": "Kharadi mein *2BHK*?", "voice": "खराडी में टू बीएचके ढूंढ रहे हैं? देखिए असल में क्या मिलता है।"},
                     {"screen": "*780* sq ft carpet", "voice": "सात सौ अस्सी स्क्वेयर फीट का कार्पेट एरिया।"},
                     {"screen": "Floor *7* of 22", "voice": "सातवीं मंज़िल, रेडी टू मूव, सेमी फर्निश्ड।"},
                     {"screen": "Parking · Gym · *Lift*", "voice": "पार्किंग, जिम, लिफ्ट, सिक्योरिटी और पावर बैकअप के साथ।"}],
           "cta_screen": "Tap *interested* · link in bio", "cta_voice": "यह एक सैंपल घर है। बायो में इंटरेस्टेड दबाइए, हम आपके लिए असली घर ढूंढेंगे।"},
}

TIP_FACTS = ("Site visit tip: water and power questions before you book a flat in Pune",
             ["Ask where the water comes from: municipal supply, tanker or borewell", "Ask how much water storage the building has",
              "Ask what the power backup covers: lifts, common areas or your flat too", "Ask who pays for the backup and the water",
              "Visit at 9 am and again at 6:30 pm on a weekday"])
TIP_FALLBACK_HI = {"beats": [{"screen": "Flat book karne se *pehle*", "voice": "फ्लैट बुक करने से पहले ये तीन सवाल ज़रूर पूछिए।"},
                             {"screen": "Paani kahan se *aata* hai?", "voice": "पानी कहाँ से आता है, म्युनिसिपल, टैंकर या बोरवेल?"},
                             {"screen": "Storage *kitna* hai?", "voice": "बिल्डिंग में पानी का स्टोरेज कितना है?"},
                             {"screen": "Backup *kya* cover karta hai?", "voice": "पावर बैकअप सिर्फ़ लिफ्ट का है या आपके फ्लैट का भी?"}],
                   "cta_screen": "*Save* karein · follow karein", "cta_voice": "इसे सेव कीजिए, और ऐसे टिप्स के लिए फॉलो कीजिए।"}


async def main():
    llm = default_llm()
    UP.mkdir(parents=True, exist_ok=True)
    ext, in1, in2 = PHOTOS / "u4453DIQWtsQ.jpg", PHOTOS / "uQGxBeUDkeWk.jpg", PHOTOS / "u0tVimluL_ls.jpg"
    subject, facts = home_facts("kharadi-2bhk-ready")
    jobs = [
        ("voiced-kharadi-2bhk-hi", "hi", subject, facts, HOME_FALLBACK["hi"], [ext, in1, in2, in1, ext], "SAMPLE HOME", "KHARADI, PUNE"),
        ("voiced-kharadi-2bhk-en", "en", subject, facts, HOME_FALLBACK["en"], [ext, in1, in2, in1, ext], "SAMPLE HOME", "KHARADI, PUNE"),
        ("voiced-tip-water-power-hi", "hi", TIP_FACTS[0], TIP_FACTS[1], TIP_FALLBACK_HI, [in2, in1, ext, in2, in1], None, "SITE VISIT TIP"),
    ]
    for name, lang, subj, f, fb, photos, badge, kicker in jobs:
        script = await director.write_script(subj, f, lang, llm, fb)
        print(f"===== {name} ({script['made_by']})\n" + json.dumps(script, ensure_ascii=False, indent=1))
        out = director.build(script, photos, lang, UP / f"{name}.mp4", badge=badge, kicker=kicker)
        print("->", out)


asyncio.run(main())
