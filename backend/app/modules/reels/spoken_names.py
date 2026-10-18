"""How our voices say Pune's names: every place in app/core/pune_places.py (a test checks) and the names our reels keep saying,
in Devanagari as the place writes itself (Marathi spelling). Google's Indian voices say a name right when it comes in Devanagari,
in an English line too ("Buying a flat in अपर खराड़ी?"); written in Latin letters they guess ("Kharadi" came out "kardi").
Google's en-IN Chirp voice takes no custom pronunciations (every IPA request is refused, checked 2026-10-19), so this is the
one way that works for every language. creative.i18n.PLACES wins for Hindi and Marathi where it differs (Hindi खराड़ी)."""
from typing import Dict

SPOKEN: Dict[str, str] = {
    # ---- East
    "Kharadi": "खराडी", "Upper Kharadi": "अप्पर खराडी", "Viman Nagar": "विमान नगर", "Vadgaon Sheri": "वडगाव शेरी",
    "Kalyani Nagar": "कल्याणी नगर", "Wagholi": "वाघोली", "Lohegaon": "लोहगाव", "Dhanori": "धानोरी", "Mundhwa": "मुंढवा",
    "Manjari": "मांजरी", "Hadapsar": "हडपसर", "Magarpatta": "मगरपट्टा", "Mohammadwadi": "महंमदवाडी", "Undri": "उंड्री",
    "Phursungi": "फुरसुंगी", "Wanowrie": "वानवडी", "Kondhwa": "कोंढवा", "Lonikand": "लोणीकंद", "Loni Kalbhor": "लोणी काळभोर",
    "Theur": "थेऊर", "Yerwada": "येरवडा", "Vishrantwadi": "विश्रांतवाडी", "Uruli Kanchan": "उरुळी कांचन", "Keshav Nagar": "केशवनगर",
    # ---- Central and South
    "Pune": "पुणे", "Deccan": "डेक्कन", "Shivajinagar": "शिवाजीनगर", "Parvati": "पर्वती", "Bibwewadi": "बिबवेवाडी",
    "Khadki": "खडकी", "Katraj": "कात्रज", "Ambegaon": "आंबेगाव", "Dhankawadi": "धनकवडी", "Dhayari": "धायरी",
    "Nanded City": "नांदेड सिटी", "Sinhagad Road": "सिंहगड रोड", "Kirkatwadi": "किरकटवाडी", "Khadakwasla": "खडकवासला",
    "Shivane": "शिवणे", "Karve Nagar": "कर्वेनगर", "Warje": "वारजे", "Narhe": "नऱ्हे", "Vadgaon Budruk": "वडगाव बुद्रुक",
    # ---- West
    "Kothrud": "कोथरूड", "Bavdhan": "बावधन", "Sus": "सूस", "Baner": "बाणेर", "Balewadi": "बालेवाडी", "Mahalunge": "महाळुंगे",
    "Pashan": "पाषाण", "Aundh": "औंध", "Hinjawadi": "हिंजवडी", "Hinjewadi": "हिंजवडी", "Wakad": "वाकड", "Tathawade": "ताथवडे",
    "Punawale": "पुनावळे", "Pirangut": "पिरंगुट", "Paud": "पौड", "Mulshi": "मुळशी", "Lavasa": "लवासा", "Marunji": "मारुंजी",
    # ---- Pimpri-Chinchwad and north
    "Pimple Saudagar": "पिंपळे सौदागर", "Pimple Gurav": "पिंपळे गुरव", "Pimpri": "पिंपरी", "Chinchwad": "चिंचवड",
    "Akurdi": "आकुर्डी", "Nigdi": "निगडी", "Bhosari": "भोसरी", "Kasarwadi": "कासारवाडी", "Dapodi": "दापोडी",
    "Chikhali": "चिखली", "Moshi": "मोशी", "Charholi": "चऱ्होली", "Ravet": "रावेत", "Kiwale": "किवळे", "Dehu": "देहू",
    "Chakan": "चाकण", "Talegaon": "तळेगाव", "Thergaon": "थेरगाव", "Sangvi": "सांगवी", "Pimple Nilakh": "पिंपळे निलख",
    "Alandi": "आळंदी",
    # ---- Pune district
    "Shikrapur": "शिक्रापूर", "Ranjangaon": "रांजणगाव", "Malthan": "मलठण", "Lonavala": "लोणावळा", "Khandala": "खंडाळा",
    "Kamshet": "कामशेत", "Shirur": "शिरूर", "Saswad": "सासवड", "Jejuri": "जेजुरी", "Yavat": "यवत",
    "Narayangaon": "नारायणगाव", "Manchar": "मंचर", "Junnar": "जुन्नर", "Rajgurunagar": "राजगुरुनगर", "Khed": "खेड",
    "Bhor": "भोर", "Baramati": "बारामती", "Indapur": "इंदापूर", "Daund": "दौंड", "Maval": "मावळ", "Purandar": "पुरंदर",
    "Velhe": "वेल्हे",
    # ---- names our reels say that are not places of the register
    "Avasetu": "अवास सेतु",   # owner 2026-10-16: AvaS-Setu, not Av-setu
    "Lodha": "लोढा", "Ubale Nagar": "उबाळे नगर", "Tulja Bhavani": "तुळजा भवानी", "Tulaja Bhavani": "तुळजा भवानी",
    "Kesnand": "केसनंद", "Wagheshwar": "वाघेश्वर", "Vitthalwadi": "विठ्ठलवाडी", "Bakori Phata": "बकोरी फाटा",
    "Ramwadi": "रामवाडी", "Somnath Nagar": "सोमनाथ नगर", "Ahilyanagar": "अहिल्यानगर",
}

# words in a register place's name that an English voice says right as they are ("Airport Road", "Peth areas", "NDA Road")
PLAIN_WORDS = {"and", "Road", "City", "taluka", "areas", "Airport", "Camp", "Peth", "NDA", "NIBM"}
