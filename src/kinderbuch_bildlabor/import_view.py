import json
import subprocess

import streamlit as st
from PIL import UnidentifiedImageError

from kinderbuch_bildlabor import imports


def render() -> None:
    st.title("Eigenes Buch importieren")
    st.caption(
        "Lokal gespeicherte Seiten bleiben offline nutzbar. Unbekannte Herkunft/Rechte bleiben unbekannt. Erst der Importknopf veröffentlicht das Buch."
    )
    mode = st.radio("Quelle", ["JPEG/PNG", "PDF", "IIIF-Manifest"], key="import-mode")
    if mode != st.session_state.get("import-current-mode"):
        for key in (
            "import-preview",
            "import-iiif",
            "import-title",
            "import-source",
            "import-rights",
            "import-selection",
        ):
            st.session_state.pop(key, None)
        st.session_state["import-current-mode"] = mode
    if mode == "IIIF-Manifest":
        url = st.text_input("Öffentliche Manifest-URL")
        if st.button("Manifest ausdrücklich aus dem Netz laden", disabled=not url):
            try:
                preview = imports.preview_iiif(url)
                st.session_state["import-iiif"] = preview
                st.session_state["import-preview"] = preview["pages"]
                for field in ("title", "source", "rights"):
                    st.session_state[f"import-{field}"] = preview[field]
                st.session_state.pop("import-selection", None)
            except (ValueError, OSError) as error:
                st.error(str(error))
    else:
        if mode == "PDF" and not imports.pdf_available():
            st.info(
                "PDF benötigt Poppler: pdfinfo und pdftoppm im PATH. JPEG/PNG und IIIF bleiben verfügbar."
            )
            return
        files = st.file_uploader(
            "Seiten in gewünschter Reihenfolge auswählen",
            type=["jpg", "jpeg", "png"] if mode == "JPEG/PNG" else ["pdf"],
            accept_multiple_files=True,
        )
        if st.button("Lokale Vorschau erstellen", disabled=not files):
            try:
                if mode == "PDF":
                    if len(files) != 1:
                        raise ValueError("Bitte genau ein PDF auswählen.")
                    pages = imports.preview_pdf(files[0].name, files[0].getvalue())
                else:
                    pages = imports.preview_import(
                        [(file.name, file.getvalue()) for file in files]
                    )
                st.session_state["import-preview"] = pages
                st.session_state.pop("import-selection", None)
            except (
                ValueError,
                OSError,
                UnidentifiedImageError,
                subprocess.SubprocessError,
            ) as error:
                st.error(f"Vorschau fehlgeschlagen: {error}")
    pages = st.session_state.get("import-preview", [])
    if not pages:
        return
    selected = st.multiselect(
        "Seiten auswählen (Reihenfolge der Auswahl = Importreihenfolge)",
        list(range(len(pages))),
        default=list(range(len(pages))),
        format_func=lambda index: f"{index + 1} · {pages[index]['name']}",
        key="import-selection",
    )
    for index in selected:
        with st.expander(f"{index + 1} · {pages[index]['name']}"):
            if "image" in pages[index]:
                st.image(pages[index]["image"], width=300)
            else:
                st.text(pages[index]["url"])
                st.caption(
                    "Bild wird erst beim ausdrücklich bestätigten Import heruntergeladen."
                )
    title = st.text_input("Buchtitel", key="import-title")
    source = st.text_input("Quelle (unbekannt = leer)", key="import-source")
    rights = st.text_input("Rechte (unbekannt = leer)", key="import-rights")
    if st.button(
        "Ausgewählte Seiten ausdrücklich importieren",
        disabled=not selected or not title.strip(),
        key="import-commit",
    ):
        try:
            metadata = {
                "title": title.strip(),
                "source": source.strip() or None,
                "rights": rights.strip() or None,
            }
            if mode == "IIIF-Manifest":
                preview = st.session_state["import-iiif"]
                chosen = imports.download_iiif(preview, selected)
                metadata["iiif_manifest"] = json.loads(preview["manifest"])
            else:
                chosen = [pages[index] for index in selected]
            sources = imports.commit_import(chosen, metadata)
            st.success(
                f"{len(sources)} Seiten importiert oder bereits vorhanden. In der Seitenleiste öffnen; vorhandene Arbeitsstände bleiben unverändert."
            )
            st.button(
                "Sammlung öffnen",
                on_click=lambda: st.session_state.update(view="sammlung"),
            )
        except (ValueError, OSError) as error:
            st.error(f"Import fehlgeschlagen: {error}")
