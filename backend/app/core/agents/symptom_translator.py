"""Translates medical terminology to patient-friendly Hinglish lay terms."""

def translate_to_lay_terms(chief_complaint: str) -> dict:
    """Convert medical chief complaint to patient-friendly descriptions.

    Returns dict with:
    - patient_description: What the patient would say
    - family_description: What the family would say
    - simple_terms: Basic lay description
    """
    cc = chief_complaint.lower()

    # Common symptom translations
    translations = {
        # GI symptoms
        "bloody diarrhea": {
            "patient": "potty mein khoon aa raha hai, bahut baar jaana padta hai",
            "family": "inko din mein 10-12 baar loose motion ho raha hai, khoon bhi aata hai",
            "simple": "khoon wali loose motion"
        },
        "painless bloody diarrhea": {
            "patient": "potty mein khoon aata hai, dard nahi hota par bahut baar jaana padta hai",
            "family": "khoon wali loose motion ho rahi hai, dard toh nahi batate",
            "simple": "bina dard ke khoon wali potty"
        },
        "hematemesis": {
            "patient": "ulti mein khoon aa raha hai",
            "family": "khoon ki ulti hui hai, bahut dar lag raha hai",
            "simple": "khoon ki ulti"
        },
        "melena": {
            "patient": "potty ekdum kaali ho gayi hai, tar jaisi",
            "family": "inki potty kaali hai, doctor ne kaha khoon hai",
            "simple": "kaali potty"
        },
        "dysphagia": {
            "patient": "khana nigalne mein dikkat ho rahi hai, gale mein atak jaata hai",
            "family": "khana nahi kha pa rahe, gale mein fas jaata hai",
            "simple": "nigalne mein dikkat"
        },

        # Cardiac symptoms
        "chest pain": {
            "patient": "chhati mein dard ho raha hai",
            "family": "seene mein dard ki shikayat kar rahe hain",
            "simple": "seene mein dard"
        },
        "palpitations": {
            "patient": "dil bahut tez tez dhadak raha hai, kabhi kabhi chhoot bhi jaata hai",
            "family": "dil ki dhakdhak ki shikayat hai, ghabrahat hoti hai",
            "simple": "dil ki tez dhakdhak"
        },
        "dyspnea": {
            "patient": "saans phool rahi hai, saans lene mein dikkat hai",
            "family": "saans nahi aa rahi inko theek se",
            "simple": "saans ki takleef"
        },
        "orthopnea": {
            "patient": "lete hue saans nahi aa paati, baith kar sona padta hai",
            "family": "raat ko baith kar sote hain, lete hue saans phoolti hai",
            "simple": "lete hue saans phoolna"
        },
        "syncope": {
            "patient": "chakkar aakar behosh ho gaya tha",
            "family": "achanak behosh ho gaye the, gir gaye the",
            "simple": "behoshi"
        },

        # Respiratory symptoms
        "cough with expectoration": {
            "patient": "khansi ho rahi hai, balgam bhi aata hai",
            "family": "bahut khansi hai, kaf bhi nikalta hai",
            "simple": "balgam wali khansi"
        },
        "hemoptysis": {
            "patient": "khansi mein khoon aa raha hai",
            "family": "khoon ki khansi ho rahi hai",
            "simple": "khoon wali khansi"
        },
        "wheezing": {
            "patient": "saans lete waqt seeti ki awaaz aati hai",
            "family": "saans mein awaaz aa rahi hai",
            "simple": "saans mein seeti"
        },

        # Neuro symptoms
        "headache": {
            "patient": "sar mein bahut dard hai",
            "family": "sar dard ki shikayat kar rahe hain",
            "simple": "sar dard"
        },
        "seizures": {
            "patient": "mirgi ka daura pada tha, haath pair akad gaye the",
            "family": "jhatke aaye the, behosh ho gaye the",
            "simple": "daura/mirgi"
        },
        "weakness": {
            "patient": "kamzori bahut hai, chalne mein dikkat hai",
            "family": "bahut kamzor ho gaye hain",
            "simple": "kamzori"
        },
        "hemiparesis": {
            "patient": "ek taraf ka haath pair nahi chal raha",
            "family": "right/left side kamzor hai",
            "simple": "aadhe badan ki kamzori"
        },

        # General symptoms
        "fever": {
            "patient": "bukhar hai, thand lag rahi hai",
            "family": "bukhar hai 3 din se",
            "simple": "bukhar"
        },
        "weight loss": {
            "patient": "wazan bahut kam ho gaya hai",
            "family": "bahut duble ho gaye hain",
            "simple": "wazan ghatna"
        },
        "loss of appetite": {
            "patient": "bhookh nahi lagti, kuch khane ka mann nahi karta",
            "family": "khana bilkul nahi khate",
            "simple": "bhookh na lagna"
        },
        "fatigue": {
            "patient": "thakawat bahut rehti hai, kaam karne ka mann nahi karta",
            "family": "hamesha thake thake rehte hain",
            "simple": "thakaan"
        },
        "jaundice": {
            "patient": "aankhen peeli ho gayi hain, peshaab bhi peela hai",
            "family": "peeliya ho gaya hai, aankhen peeli hain",
            "simple": "peeliya"
        },
        "edema": {
            "patient": "pair suj gaye hain, joote tight ho gaye",
            "family": "haath pair mein sujan hai",
            "simple": "sujan"
        },
        "ascites": {
            "patient": "pet phool gaya hai, paani bhar gaya hai",
            "family": "pet mein paani bhar gaya hai",
            "simple": "pet mein paani"
        }
    }

    # Check for exact matches first
    for medical_term, lay_terms in translations.items():
        if medical_term in cc:
            return lay_terms

    # Check for partial matches
    for medical_term, lay_terms in translations.items():
        for word in medical_term.split():
            if word in cc and len(word) > 4:  # Avoid short words like "of", "with"
                return lay_terms

    # Default fallback - extract key symptoms
    if "pain" in cc or "ache" in cc:
        if "chest" in cc:
            return translations["chest pain"]
        elif "head" in cc:
            return translations["headache"]
        else:
            return {
                "patient": "bahut dard ho raha hai",
                "family": "dard ki shikayat kar rahe hain",
                "simple": "dard"
            }

    if "bleeding" in cc or "blood" in cc:
        return {
            "patient": "khoon aa raha hai",
            "family": "khoon aane ki problem hai",
            "simple": "khoon aana"
        }

    if "vomit" in cc:
        return {
            "patient": "ulti ho rahi hai",
            "family": "baar baar ulti kar rahe hain",
            "simple": "ulti"
        }

    if "breath" in cc or "dyspn" in cc or "short" in cc:
        return translations["dyspnea"]

    if "swelling" in cc or "swell" in cc:
        return translations["edema"]

    # Generic fallback
    return {
        "patient": "tabiyat kharab hai, theek nahi lag raha",
        "family": "tabiyat bigad gayi hai",
        "simple": "bimaar"
    }


def get_patient_friendly_description(chief_complaint: str, distress_level: str = "moderate") -> str:
    """Get patient's description based on distress level."""
    lay_terms = translate_to_lay_terms(chief_complaint)

    if distress_level == "critical":
        return f"{lay_terms['simple']}... bahut... zyada..."
    elif distress_level == "high":
        return f"{lay_terms['patient']}, bahut takleef hai"
    else:
        return lay_terms['patient']


def get_family_friendly_description(chief_complaint: str, duration: str = "kuch din") -> str:
    """Get family member's description of the problem."""
    lay_terms = translate_to_lay_terms(chief_complaint)
    return f"{lay_terms['family']}, {duration} se pareshan hain"