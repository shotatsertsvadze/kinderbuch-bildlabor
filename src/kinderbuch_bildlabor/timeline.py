"""Verlauf eines Objekts in Zeitfolge, nur aus dem Prüfprotokoll abgeleitet. Nur Lesen."""


def kind(entry: dict) -> str:
    area, action = entry["area"], entry["action"]
    if area == "final_review":
        return "Endbestätigung" if "erteilt" in action else "Endbestätigung aufgehoben"
    if area.startswith("second_review/"):
        return "Zweitprüfung"
    if "zurückgezogen" in action:
        return "Zurückgezogen"
    return "Bestätigung" if "by" in entry else "Änderung"


def events(record: dict) -> list[dict]:
    """Protokolleinträge aufsteigend nach Zeit; zurückgezogene Regionen mit ihrem damaligen Text."""
    withdrawn = {
        w["region"]["id"]: w.get("transcription", {}).get("text")
        for w in record.get("withdrawn_regions", [])
    }
    result = []
    for entry in record.get("review_log", []):
        text = entry["action"]
        old = withdrawn.get(entry["area"]) if "zurückgezogen" in text else None
        if old:
            text += f" Gelöschter Text: „{old}“"
        result.append(
            {
                "at": entry["at"],
                "kind": kind(entry),
                "person": entry.get("by", "–"),
                "area": entry["area"],
                "text": text,
            }
        )
    return sorted(result, key=lambda e: e["at"])
