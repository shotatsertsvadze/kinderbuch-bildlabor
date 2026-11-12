"""Abschnitt Sicherung: Paket laden und prüfen. Zurückspielen geht nur per Kommandozeile."""

import io

import streamlit as st

from kinderbuch_bildlabor import backup, ui


def package() -> bytes:
    buffer = io.BytesIO()
    backup.write_backup(buffer)
    return buffer.getvalue()


def render() -> None:
    ui.section("Sicherung")
    st.caption(
        "Das Paket enthält Arbeitskopien, importierte Bücher und Exporte mit Prüfsummen. "
        "Zurückspielen: `python -m kinderbuch_bildlabor.backup restore PAKET.zip NEUER_ORDNER`; "
        "bestehende Daten werden nie überschrieben."
    )
    st.download_button(
        "Sicherungspaket herunterladen",
        data=package,
        file_name="bildlabor-sicherung.zip",
        mime="application/zip",
        key="backup-download",
    )
    upload = st.file_uploader(
        "Sicherungspaket prüfen", type=["zip"], key="backup-verify"
    )
    if upload is None:
        return
    try:
        problems = backup.verify_backup(io.BytesIO(upload.getvalue()))
    except backup.BackupError as error:
        st.error(str(error))
        return
    if problems:
        st.error("Paket ist nicht intakt:\n\n" + "\n".join(f"- {p}" for p in problems))
    else:
        st.success("Paket ist intakt. Es wurde nichts verändert.")
