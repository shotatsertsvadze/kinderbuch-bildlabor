"""Wiederkehrende Anzeigebausteine der Oberfläche."""

from datetime import datetime

import streamlit as st

from kinderbuch_bildlabor import review


def local_time(iso: str) -> str:
    return datetime.fromisoformat(iso).astimezone().strftime("%d.%m.%Y, %H:%M Uhr")


def status_badge(status: str) -> None:
    """Status als Text und Symbol, nicht nur als Farbe."""
    if status in review.DONE_STATUSES:
        st.badge(f"Erledigt: {review.status_label(status)}", icon=":material/check_circle:", color="green")
    else:
        st.badge(f"Offen: {review.status_label(status)}", icon=":material/pending:", color="orange")


def source_text(text: str) -> None:
    """Gibt Text unverändert aus: Zeilenumbrüche bleiben, Markdown-Zeichen wie * werden nicht ausgewertet."""
    st.text(text)


def unsaved_note(is_unsaved: bool, consequence_de: str = "") -> None:
    if is_unsaved:
        st.warning(f"Ungespeicherte Eingabe. {consequence_de}".strip(), icon=":material/edit:")


def confirm_controls(key: str, meaning_de: str, statement_de: str, on_click, args=(),
                     blocked_de: str | None = None) -> None:
    """Bestätigung mit erklärter Bedeutung und sichtbarem Grund, falls gesperrt."""
    st.caption(f"Bedeutung der Bestätigung: {meaning_de}")
    checked = st.checkbox(statement_de, key=f"{key}-check", disabled=blocked_de is not None)
    reviewer = st.session_state.get("reviewer", "").strip()
    reason = blocked_de or (
        "Bitte zuerst das Häkchen setzen." if not checked else
        "Bitte links unter „Prüfende Person“ einen Namen eintragen." if not reviewer else None)
    st.button("Bestätigen und speichern", key=f"{key}-confirm", on_click=on_click, args=args,
              disabled=reason is not None, type="primary")
    if reason:
        st.caption(f"Gesperrt: {reason}")


def confirmed_note(record: dict, area: str) -> None:
    entry = review.last_confirmation(record, area)
    if entry:
        st.caption(f"Bestätigt von {entry['by']} am {local_time(entry['at'])}.")


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
    st.error("Inzwischen wurde in einem anderen Fenster ein neuer Stand gespeichert. Ihre Eingabe hier "
             f"ist nicht gespeichert und kann den neuen Stand nicht überschreiben. Gespeichert ist jetzt: {shown_de}",
             icon=":material/sync_problem:")
    st.button("Gespeicherten Stand laden (eigene Eingabe verwerfen)", key=f"{keys[0]}-reload",
              on_click=load_fields, args=(keys, stored))
