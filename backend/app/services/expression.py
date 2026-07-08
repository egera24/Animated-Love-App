from __future__ import annotations

import unicodedata

VALID_EXPRESSIONS = {
    "celebrate",
    "comfort",
    "melancholy",
    "happy",
    "curious",
    "neutral",
    "talking",
}

_MOOD_TO_EXPRESSION = {
    "celebrate": "celebrate",
    "happy": "happy",
    "comfort": "comfort",
    "cozy": "comfort",
    "melancholy": "melancholy",
    "sleepy": "melancholy",
    "curious": "curious",
    "alert": "curious",
    "idle": "neutral",
}

# Keyword hints used to nudge the expression from a chat message intent.
# Stored accent-folded (see _fold) and matched against folded input, so both
# "szomorú" and "szomoru" trigger. Kept small; Hungarian + English stems.
_INTENT_KEYWORDS = {
    "comfort": ("szomor", "hiany", "sir", "nehez", "faj", "gyasz", "magany", "sad", "miss", "cry", "lonely"),
    "celebrate": ("unnep", "szulinap", "gratula", "siker", "party", "birthday", "yay", "hurra"),
    "curious": ("miert", "hogyan", "mesel", "mi az", "why", "how", "what", "?"),
}


def _fold(text: str) -> str:
    """Lowercase and strip diacritics for accent-insensitive matching."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def mood_to_expression(mood: str | None) -> str:
    if not mood:
        return "neutral"
    return _MOOD_TO_EXPRESSION.get(mood, "neutral")


def expression_from_chat(mood: str | None, *, user_text: str | None = None) -> str:
    """Resolve the expression for a chat reply.

    The calendar/weather mood is the baseline; a strong emotional cue in the
    user's latest message can override it (e.g. she writes something sad -> comfort).
    """
    base = mood_to_expression(mood)
    if not user_text:
        return base

    folded = _fold(user_text)
    # comfort takes precedence over everything when clearly present
    for expr in ("comfort", "celebrate", "curious"):
        keywords = _INTENT_KEYWORDS.get(expr, ())
        if any(k in folded for k in keywords):
            return expr
    return base
