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
