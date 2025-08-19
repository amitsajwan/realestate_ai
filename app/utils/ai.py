from typing import Dict, Any, Optional


def _fallback_branding(name: str) -> Dict[str, Any]:
    return {
        "tagline": f"Your Property Partner, {name}",
        "about": f"{name} brings reliability and a modern approach to real estate success.",
        "colors": {
            "primary": "#232946",
            "secondary": "#eebbc3",
            "accent": "#b8c1ec"
        }
    }


def generate_branding(name: str, tags: Optional[str] = None) -> Dict[str, Any]:
    """Generate branding suggestions via Groq LLM if available.

    Returns keys: tagline, about, colors {primary, secondary, accent}
    """
    try:
        from core.config import settings
        if not getattr(settings, "GROQ_API_KEY", None):
            return _fallback_branding(name)

        try:
            from groq import Groq
        except Exception:
            return _fallback_branding(name)

        client = Groq(api_key=settings.GROQ_API_KEY)

        guidance = (
            "You are a senior brand strategist crafting crisp, modern branding for a real estate agent. "
            "Return STRICT JSON with keys: tagline, about, colors:{primary, secondary, accent}. "
            "Colors must be valid hex like #112233 optimized for mobile UI contrast."
        )

        user = (
            f"Agent/Brand name: {name}. "
            f"Focus tags: {tags or 'real estate, trust, local, responsive, modern'}. "
            "Tone: professional, warm, trustworthy. Limit tagline to <= 8 words. "
            "About: 1 short sentence (<= 18 words)."
        )

        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": guidance},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
            max_tokens=300,
        )

        content = completion.choices[0].message.content.strip()

        import json
        try:
            data = json.loads(content)
        except Exception:
            # Try to extract JSON substring
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                data = json.loads(content[start : end + 1])
            else:
                return _fallback_branding(name)

        tagline = data.get("tagline") or f"Trusted Realty • {name}"
        about = data.get("about") or f"{name} delivers seamless property experiences."
        colors = data.get("colors") or {}
        primary = colors.get("primary") or "#232946"
        secondary = colors.get("secondary") or "#eebbc3"
        accent = colors.get("accent") or "#b8c1ec"

        return {
            "tagline": tagline,
            "about": about,
            "colors": {
                "primary": primary,
                "secondary": secondary,
                "accent": accent,
            },
        }
    except Exception:
        return _fallback_branding(name)
