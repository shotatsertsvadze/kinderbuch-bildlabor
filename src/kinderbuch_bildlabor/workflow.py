"""Prüfpfad: nummerierte Schritte mit Stand und ein einheitliches „Weiter“ nach dem Speichern."""

import re
from collections.abc import Callable
from typing import Literal

import streamlit as st

from kinderbuch_bildlabor import review, store, ui


def approved(record: dict) -> bool:
    return (
        bool(record.get("final_approval")) and record["status"] == review.FINAL_APPROVED
    )


def next_tab(
    record: dict, export_current: bool = False, blockers: int = 0
) -> str | None:
    """Reiter des nächsten offenen Schritts; None, wenn alles erledigt ist."""
    pending = next(
        (a["tab_de"] for a in review.review_areas(record) if not a["done"]), None
    )
    if pending:
        return pending
    if blockers or not approved(record):
        return "Prüfung"
    return None if export_current else "Export"


def steps(record: dict, export_current: bool) -> list[tuple[str, bool]]:
    """Schritte des Objekts mit Erledigt-Stand, in Arbeitsreihenfolge."""
    areas = review.review_areas(record)
    done = {
        tab: all(a["done"] for a in areas if a["tab_de"] == tab)
        for tab in dict.fromkeys(a["tab_de"] for a in areas)
    }
    # Ein aktueller Export eines ungeprüften Entwurfs ist noch kein erledigter Schritt
    return [
        *done.items(),
        ("Prüfung", approved(record)),
        ("Export", export_current and approved(record)),
    ]


def area_counts(areas: list[dict]) -> tuple[int, int, int]:
    """Bestätigt, als Entwurf gespeichert, noch unberührt offen."""
    confirmed = sum(a["done"] for a in areas)
    drafts = sum(a["draft"] for a in areas)
    return confirmed, drafts, len(areas) - confirmed - drafts


def segmented_bar(confirmed: int, drafts: int, untouched: int) -> str:
    """Schmuckleiste zum Fortschrittsbalken: der Text darüber nennt dieselben Zahlen."""
    segments = "".join(
        f'<span class="bl-seg bl-seg-{name}" style="flex-grow:{count}"></span>'
        for name, count in (("ok", confirmed), ("draft", drafts), ("open", untouched))
        if count
    )
    return f'<div class="bl-segbar" aria-hidden="true">{segments}</div>'


def object_state(
    record: dict,
) -> tuple[str, str, str, Literal["green", "orange", "gray"]]:
    """Symbol, Zustandszeile, Kurzwort und Badge-Farbe eines Objekts für Seitenleiste und Karten."""
    if approved(record):
        return ":material/verified:", "endbestätigt", "endbestätigt", "green"
    areas = review.review_areas(record)
    confirmed, drafts, _ = area_counts(areas)
    if not confirmed and not drafts:
        return ":material/radio_button_unchecked:", "offen", "offen", "gray"
    line = f"{confirmed} von {len(areas)} bestätigt"
    return ":material/clock_loader_40:", line, "in Arbeit", "orange"


def current_step(all_steps: list[tuple[str, bool]], pending: str | None) -> str:
    if pending is None:
        return f"alle {len(all_steps)} Schritte erledigt"
    number = [tab for tab, _ in all_steps].index(pending) + 1
    return f"Schritt {number} von {len(all_steps)} · {ui.STEPS[pending][0]}"


def step_tabs(all_steps: list[tuple[str, bool]]) -> list[str]:
    return [tab for tab, _ in all_steps]


def view_name(tab: str, tabs: list[str]) -> str:
    return f"{tabs.index(tab) + 1} · {ui.STEPS[tab][0]}" if tab in tabs else tab


def area_state(area: dict) -> str:
    if area["done"]:
        return "bestätigt"
    if area["draft"]:
        return "Entwurf gespeichert, Bestätigung offen"
    return f"offen ({review.status_label(area['status'])})"


def step_hint(tab: str, done: bool, areas: list[dict]) -> str:
    in_tab = [a for a in areas if a["tab_de"] == tab]
    count = (
        f" {sum(a['done'] for a in in_tab)} von {len(in_tab)} Prüfbereichen bestätigt."
        if in_tab
        else ""
    )
    return ui.STEPS[tab][1] + count + (" Erledigt." if done else "")


def final_line(record: dict, blockers: int) -> str:
    if approved(record):
        return "**Endbestätigung:** erteilt (keine Ground-Truth-Freigabe)."
    if blockers:
        count = (
            "1 offener fachlicher Hinweis"
            if blockers == 1
            else f"{blockers} offene fachliche Hinweise"
        )
        return (
            f"**Endbestätigung:** noch nicht erteilt; {count} im {ui.place('Prüfung')}."
        )
    return "**Endbestätigung:** noch nicht erteilt."


def open_tab(key: str, tab: str) -> None:
    st.session_state[key] = tab


def viewed_marker(tab: str) -> str:
    """Hebt den gerade gezeigten Reiter hervor und meldet ihn Screenreadern als aktuelle Seite."""
    # Streamlit ersetzt in Klassennamen alles außer [A-Za-z0-9_-] durch „-“ (ü in „Übersicht“)
    cls = re.sub(r"[^A-Za-z0-9_-]", "-", f"st-key-guide-{tab.lower()}")
    return (
        f"<style>.st-key-guide-steps .{cls} button {{ color: var(--bl-ink) !important; font-weight: 620;"
        " box-shadow: inset 0 -3px 0 var(--bl-primary) !important; }</style>"
        "<script>(() => {"
        "const bar = document.querySelector('.st-key-guide-steps'); if (!bar) return;"
        "bar.querySelectorAll('button')"
        f".forEach((b) => b.closest('.{cls}') ? b.setAttribute('aria-current', 'page')"
        " : b.removeAttribute('aria-current'));"
        f"bar.querySelector('.{cls} button')"
        "?.scrollIntoView({inline: 'nearest', block: 'nearest'});"
        "const more = () => bar.classList.toggle('bl-more',"
        " bar.scrollWidth - bar.clientWidth - bar.scrollLeft > 4);"
        "more(); if (!bar.dataset.blWatch) { bar.dataset.blWatch = '1';"
        " bar.addEventListener('scroll', more); addEventListener('resize', more); }"
        "})();</script>"
    )


def navigation(
    names: list[str],
    all_steps: list[tuple[str, bool]],
    areas: list[dict],
    pending: str | None,
    tabs_key: str,
) -> None:
    """Eine Navigationsleiste: Übersicht, nummerierte Prüfschritte, danach Nachschlageansichten."""
    step_tabs = [tab for tab, _ in all_steps]
    viewed = st.session_state.get(tabs_key)
    viewed = viewed if viewed in names else names[0]
    with st.container(horizontal=True, gap=None, key="guide-steps"):
        st.button(
            names[0],
            key=f"guide-{names[0].lower()}",
            type="tertiary",
            on_click=open_tab,
            args=(tabs_key, names[0]),
        )
        for number, (tab, done) in enumerate(all_steps, start=1):
            st.button(
                f"{number} · {ui.STEPS[tab][0]}",
                key=f"guide-{tab.lower()}",
                help=step_hint(tab, done, areas),
                # Primär = nächster offener Schritt (Kobalt), nicht der gerade gezeigte Reiter
                type="primary" if tab == pending else "secondary",
                icon=":material/check_circle:"
                if done
                else ":material/arrow_forward:"
                if tab == pending
                else None,
                on_click=open_tab,
                args=(tabs_key, tab),
            )
        for tab in names[1:]:
            if tab not in step_tabs:
                st.button(
                    tab,
                    key=f"guide-{tab.lower()}",
                    type="tertiary",
                    on_click=open_tab,
                    args=(tabs_key, tab),
                )
    st.html(viewed_marker(viewed), unsafe_allow_javascript=True)


def render(
    record: dict,
    tabs_key: str,
    names: list[str],
    export_current: bool,
    blockers: int,
    footer: Callable[[], None] | None = None,
) -> None:
    pending = next_tab(record, export_current, blockers)
    all_steps = steps(record, export_current)
    areas = review.review_areas(record)
    confirmed, drafts, untouched = area_counts(areas)
    navigation(names, all_steps, areas, pending, tabs_key)
    viewed = st.session_state.get(tabs_key)
    with st.container(key="review-guide", border=True):
        text, progress = st.columns([3, 2], gap="medium")
        with text:
            with st.container(key="guide-eyebrow"):
                st.caption(f"PRÜFPFAD · {current_step(all_steps, pending).upper()}")
            if pending and viewed in names and viewed != pending:
                st.caption(
                    f"Sie sehen: {view_name(viewed, step_tabs(all_steps))}. "
                    f"Nächster offener Schritt: {view_name(pending, step_tabs(all_steps))}."
                )
            if not store.DEMO:
                label = "Nächste Handlung"
            else:
                label = "Offen im Prüfablauf" if pending else "Stand"
            st.markdown(
                f"**{label}:** {ui.next_step(record, export_current, blockers)}"
            )
            with st.container(key="guide-final"):
                st.markdown(final_line(record, blockers))
        with progress:
            st.progress(
                confirmed / len(areas),
                text=f"Prüfbereiche: {confirmed} von {len(areas)} bestätigt · "
                f"{drafts} als Entwurf gespeichert · {untouched} offen",
            )
            st.html(segmented_bar(confirmed, drafts, untouched))
            with st.expander(f"Prüfbereiche dieses Objekts ({len(areas)})"):
                st.markdown(
                    "\n".join(f"- {a['label_de']}: {area_state(a)}" for a in areas)
                )
                st.caption(
                    "Ein gespeicherter Entwurf ist noch keine Prüfung. Erst die Bestätigung mit "
                    "Häkchen und Name zählt als bestätigter Bereich."
                )
                st.caption(
                    "Die nummerierten Schritte führen durch die Prüfung; ein Schritt gilt erst als "
                    "erledigt, wenn alle seine Prüfbereiche bestätigt sind. Übersicht und "
                    "Bibliotheksdaten sind Nachschlageansichten."
                )
    if footer:
        # Tastenkürzel gelten seitenweit; ihre Hilfe steht ruhig in der Seitenleiste
        with st.sidebar, st.container(key="guide-keys"):
            footer()


def continue_button(object_id: str, record: dict, key: str) -> None:
    """Primäre „Weiter“-Schaltfläche zum nächsten offenen Schritt, direkt nach dem Speichern."""
    target = next_tab(record)
    if target is None:
        return
    st.button(
        f"Weiter: {ui.STEPS[target][0]}",
        key=key,
        type="primary",
        icon=":material/arrow_forward:",
        help=ui.STEPS[target][1],
        on_click=open_tab,
        args=(f"{object_id}-tabs", target),
    )
