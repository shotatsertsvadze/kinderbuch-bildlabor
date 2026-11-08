"""Wiederkehrende Anzeigebausteine der Oberfläche."""

from dataclasses import dataclass
from datetime import datetime
from functools import cached_property

import streamlit as st
from PIL import Image

from kinderbuch_bildlabor import review, store

# Ein Symbol je Bedeutung, damit gleiche Zustände überall gleich aussehen
OK = ":material/check:"
CONFIRMED = ":material/check_circle:"
ERROR = ":material/error:"
WARNING = ":material/warning:"
INFO = ":material/info:"
PENDING = ":material/pending:"
LOCK = ":material/lock:"
BLOCKED = ":material/block:"

# Gemeinsame Maße: Spaltenverhältnis Bild zu Bedienfeldern, Höhe von Textfeldern, größte Bildbreite
SPLIT = [2, 3]
TEXT_AREA_HEIGHT = 140
MAX_CROP_WIDTH = 730
MAX_CROP_HEIGHT = 420


def section(title: str) -> None:
    st.subheader(title)


def subsection(title: str) -> None:
    st.markdown(f"**{title}**")


def image_and_controls(pinned: str | None = None):
    """Bild links, Bedienung rechts; mit `pinned` bleibt der Scan beim Blättern neben der Bedienung."""
    left, right = st.columns(SPLIT, gap="large")
    return (left.container(key=f"pinned-scan-{pinned}") if pinned else left), right


def neutral_badge(text: str) -> None:
    st.badge(text, icon=BLOCKED, color="gray")


def crop_width(xywh: list[int]) -> int:
    """Anzeigebreite so, dass auch hohe Regionen nicht übermäßig viel Platz einnehmen."""
    w, h = xywh[2], xywh[3]
    return max(1, min(w, MAX_CROP_WIDTH, round(MAX_CROP_HEIGHT * w / h)))


@dataclass
class Current:
    """Das angezeigte Objekt: Quelldateien und gespeicherter Arbeitsstand dieses Laufs."""

    src: store.ObjectSource
    working: dict

    @property
    def record(self) -> dict:
        return self.working["record"]

    @property
    def id(self) -> str:
        return self.src.id

    @cached_property
    def size(self) -> tuple[int, int]:
        return self.record["source"]["image_width"], self.record["source"][
            "image_height"
        ]


@st.cache_resource
def page_image(path) -> Image.Image:
    """Ausgangsbilder sind unveränderlich; Arbeitsdaten werden dagegen bei jedem Lauf neu gelesen."""
    return Image.open(path).convert("RGB")


def local_time(iso: str) -> str:
    return datetime.fromisoformat(iso).astimezone().strftime("%d.%m.%Y, %H:%M Uhr")


def local_time_exact(iso: str) -> str:
    """Mit Sekunden: zwei Aktionen in derselben Minute sollen unterscheidbar bleiben."""
    return datetime.fromisoformat(iso).astimezone().strftime("%d.%m.%Y, %H:%M:%S Uhr")


def set_feedback(object_id: str, slot: str, kind: str, text_de: str) -> None:
    """Merkt sich das Ergebnis einer Aktion, damit es neben ihrem Knopf stehen bleibt."""
    st.session_state.feedback = {
        "object": object_id,
        "slot": slot,
        "kind": kind,
        "text": text_de,
        "at": store.now_utc(),
    }


def feedback(object_id: str, slot: str) -> None:
    """Zeigt das Ergebnis der letzten Aktion, aber nur am Knopf und Objekt, zu dem es gehört."""
    entry = st.session_state.get("feedback")
    if not entry or entry["object"] != object_id or entry["slot"] != slot:
        return
    text = f"{entry['text']} ({local_time_exact(entry['at'])})"
    if entry["kind"] == "draft":
        st.info(text, icon=":material/save:")
    elif entry["kind"] == "error":
        st.error(text, icon=ERROR)
    else:
        st.info(text, icon=INFO)


def object_label(record: dict) -> str:
    source = record["source"]
    return f"{record['bibliographic_metadata_from_colibri']['title']}, Scan {source['scan_number']}"


def status_badge(status: str) -> None:
    """Status als Text und Symbol, nicht nur als Farbe."""
    if status in review.DONE_STATUSES:
        st.badge(
            f"Bestätigt: {review.status_label(status)}",
            icon=CONFIRMED,
            color="green",
        )
    else:
        st.badge(
            f"Offen: {review.status_label(status)}",
            icon=PENDING,
            color="orange",
        )


def origin_note(text: str | None) -> None:
    if origin := review.origin_label(text):
        st.caption(f":material/smart_toy: Herkunft: {origin}")


def source_text(text: str) -> None:
    """Gibt Text unverändert aus: Zeilenumbrüche bleiben, Markdown-Zeichen wie * werden nicht ausgewertet."""
    st.text(text)


def edit_state(sync: str, consequence_de: str = "") -> None:
    """Zeigt, ob die Eingabe dem gespeicherten Stand entspricht."""
    if sync == EDITED:
        st.warning(
            f"Ungespeicherte Änderung. {consequence_de}".strip(), icon=":material/edit:"
        )
    elif sync == CLEAN:
        st.caption(":material/save: Entspricht dem gespeicherten Stand.")


def reviewer_input() -> None:
    st.text_input(
        "Prüfende Person",
        key="reviewer",
        placeholder="Vor- und Nachname",
        help="Der Name wird bei jeder Bestätigung und Entscheidung gespeichert.",
    )


def confirm_controls(
    key: str,
    meaning_de: str,
    statement_de: str,
    on_click,
    args=(),
    blocked_de: str | None = None,
    button_label: str = "Als geprüft bestätigen",
) -> None:
    """Bestätigung mit erklärter Bedeutung und sichtbarem Grund, falls gesperrt."""
    with st.container(border=True, key=f"{key}-box"):
        subsection("Prüfung mit Ihrem Namen bestätigen")
        st.caption(
            f"{meaning_de} Speichern ändert nur den Inhalt; erst die Bestätigung zählt als geprüft."
        )
        checked = st.checkbox(
            statement_de, key=f"{key}-check", disabled=blocked_de is not None
        )
        reviewer = st.session_state.get("reviewer", "").strip()
        reason = blocked_de or (
            "Bitte zuerst das Häkchen setzen."
            if not checked
            else "Tragen Sie oben im Prüfpfad unter „Prüfende Person“ Ihren Namen ein."
            if not reviewer
            else None
        )
        st.button(
            button_label,
            key=f"{key}-confirm",
            on_click=on_click,
            args=args,
            disabled=reason is not None,
            type="primary",
            icon=CONFIRMED,
        )
        if reason:
            st.caption(f"{LOCK} Noch nicht möglich: {reason}")


def confirmed_note(record: dict, area: str) -> None:
    entry = review.last_confirmation(record, area)
    if entry:
        st.success(
            f"Bestätigt von {entry['by']} am {local_time(entry['at'])}. "
            "Eine spätere Änderung setzt diese Bestätigung zurück.",
            icon=CONFIRMED,
        )


CLEAN, EDITED, CONFLICT = "clean", "edited", "conflict"


def base_key(keys: list[str]) -> str:
    return f"{keys[0]}--base"


def load_fields(keys: list[str], stored: list) -> None:
    """Setzt Eingabefelder und ihren Ausgangsstand auf den gespeicherten Wert."""
    for key, value in zip(keys, stored):
        st.session_state[key] = value
    st.session_state[base_key(keys)] = list(stored)


def sync_fields(keys: list[str], stored: list, normalize=lambda values: values) -> str:
    """Hält Eingabefelder am gespeicherten Stand, solange in dieser Sitzung nichts eingegeben wurde.

    Speichert ein anderes Fenster, übernehmen unveränderte Felder den neuen Stand. Wurde hier schon
    etwas eingegeben, ist das ein Konflikt: Die Eingabe bleibt sichtbar, darf aber nicht speichern.
    """
    state = st.session_state
    if any(key not in state for key in keys) or base_key(keys) not in state:
        load_fields(keys, stored)
        return CLEAN
    current = [state[key] for key in keys]
    if normalize(current) == normalize(stored):
        state[base_key(keys)] = list(stored)
        return CLEAN
    if normalize(state[base_key(keys)]) != normalize(stored):
        if normalize(current) == normalize(state[base_key(keys)]):
            load_fields(keys, stored)
            return CLEAN
        return CONFLICT
    return EDITED


def seen_values(keys: list[str]) -> list:
    """Gespeicherter Stand, von dem die Eingabe in dieser Sitzung ausging."""
    return st.session_state[base_key(keys)]


def conflict_note(keys: list[str], stored: list, shown_de: str) -> None:
    st.error(
        "Inzwischen wurde in einem anderen Fenster ein neuer Stand gespeichert. Ihre Eingabe hier "
        f"ist nicht gespeichert und kann den neuen Stand nicht überschreiben. Gespeichert ist jetzt: {shown_de}",
        icon=":material/sync_problem:",
    )
    st.button(
        "Gespeicherten Stand laden (eigene Eingabe verwerfen)",
        key=f"{keys[0]}-reload",
        on_click=load_fields,
        args=(keys, stored),
    )


def next_step(record: dict, export_current: bool, blockers: int = 0) -> str:
    open_areas = [a for a in review.review_areas(record) if not a["done"]]
    if open_areas:
        area = open_areas[0]
        if area["draft"]:
            return (
                f"Gespeicherten Entwurf am Bild prüfen und bestätigen: {area['label_de']} "
                f"(Reiter „{area['tab_de']}“)."
            )
        return f"{area['label_de']} prüfen (Reiter „{area['tab_de']}“)."
    if blockers:
        return (
            f"Offene fachliche Hinweise ({blockers}) im Reiter „Prüfung“ begründet entscheiden "
            "oder bewusst offen lassen; bis dahin ist keine Endbestätigung möglich."
        )
    approved = record.get("final_approval") and record.get("status") == (
        review.FINAL_APPROVED
    )
    if not approved:
        return "Endbestätigung im Reiter „Prüfung“ erteilen, danach exportieren."
    if not export_current:
        return "Export erstellen (Reiter „Export“)."
    return "Das Objekt ist endbestätigt und exportiert. Das ist keine Ground-Truth-Freigabe."
