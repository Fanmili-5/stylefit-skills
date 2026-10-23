"""A small, explicit profile contract; no inferred authorship score."""
import json
from pathlib import Path

DOMAINS = ("code", "research", "email")
LANGUAGES = ("zh", "en")


def validate(profile):
    if not isinstance(profile, dict):
        raise ValueError("Profile must be an object")
    if set(profile) - {"schema_version", "basis", "preferences", "sources", "notes"}:
        raise ValueError("Unknown profile fields")
    if profile.get("schema_version") != 1 or isinstance(profile.get("schema_version"), bool):
        raise ValueError("Unsupported profile version")
    if profile.get("basis") not in {"samples", "preferences", "mixed", "generic"}:
        raise ValueError("Profile basis is required")
    preferences = profile.get("preferences")
    if not isinstance(preferences, dict) or set(preferences) - set(DOMAINS):
        raise ValueError("Invalid preference domains")
    for domain, languages in preferences.items():
        if not isinstance(languages, dict) or set(languages) - set(LANGUAGES):
            raise ValueError("Invalid preference languages")
        for entries in languages.values():
            if not isinstance(entries, list) or len(entries) > 12:
                raise ValueError("Preferences must be a list of at most 12 items")
            if any(not isinstance(item, str) or not item.strip() for item in entries):
                raise ValueError("Preference items must be nonempty strings")
    if "sources" in profile and (not isinstance(profile["sources"], list) or
                               any(not isinstance(s, dict) for s in profile["sources"])):
        raise ValueError("Invalid sources")
    if "notes" in profile and (not isinstance(profile["notes"], list) or
                             any(not isinstance(s, str) for s in profile["notes"])):
        raise ValueError("Invalid notes")
    return profile


def load(path):
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))


def select(profile, domain, language):
    validate(profile)
    return {"basis": profile["basis"],
            "preferences": profile["preferences"].get(domain, {}).get(language, []),
            "missing_preferences": "Use plain task-appropriate defaults; do not invent personal habits."}
