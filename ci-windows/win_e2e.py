"""Windows-Abnahme im echten Browser. Aufruf: win_e2e.py PHASE URL PAKET DATEN AUSGABE [KANAL]"""
import csv, json, pathlib, sys
from playwright.sync_api import sync_playwright

PHASE, URL = sys.argv[1], sys.argv[2]
PKG, DATA, OUT = (pathlib.Path(a) for a in sys.argv[3:6])
CHANNEL = sys.argv[6] if len(sys.argv) > 6 else "msedge"
NAME = "Testperson Windows"
TEXT = "Test „Gewölbe“ ‘Abnahme’ – Straße × 2; ſ und ꝛ."
OUT.mkdir(parents=True, exist_ok=True)
failures = []

def report(ok, what, detail=""):
    print(("OK  " if ok else "FAIL") + f" {what}" + (f" | {detail}" if detail else ""), flush=True)
    if not ok: failures.append(what)
def settle(pg, ms=2000): pg.wait_for_timeout(ms)
def vis(loc): return loc.locator("visible=true").first
def main(pg): return pg.locator("[data-testid=stMain]").inner_text()
def tab(pg, n): vis(pg.get_by_role("tab", name=n)).click(); settle(pg)
def tick(pg, label):
    if not pg.get_by_role("checkbox", name=label).first.is_checked():
        vis(pg.get_by_text(label, exact=True)).click(); settle(pg)
def name(pg):
    box = vis(pg.get_by_role("textbox", name="Prüfende Person")); box.fill(NAME); box.press("Tab"); settle(pg)
def shot(pg, n): pg.mouse.move(5, 5); settle(pg, 300); pg.screenshot(path=str(OUT / f"{PHASE}-{n}.png"))

def flow(pg, browser):
    erg = PKG / "docs" / "ergebnis"
    t = main(pg); report("Abgeschlossenes Beispiel" in t, "Startseite mit Beispielkasten"); shot(pg, "01-start")
    for label, f in [("JSON herunterladen", "genovefa-scan-022.json"), ("CSV herunterladen", "genovefa-scan-022.csv"), ("Erläuterung herunterladen", "README.md")]:
        with pg.expect_download() as info: vis(pg.get_by_role("button", name=label)).click()
        d = info.value; tgt = OUT / ("download-" + d.suggested_filename); d.save_as(tgt)
        report(tgt.read_bytes() == (erg / f).read_bytes(), f"Download {f} byte-identisch")
    vis(pg.get_by_role("button", name="Leitbeispiel öffnen")).click(); settle(pg, 3000)
    report("SCHRITT 1 VON 5" in main(pg).upper() and "0 von 4 bestätigt" in main(pg), "Leitbeispiel im Quellstand")
    vis(pg.get_by_role("button", name="1 · Bild prüfen")).click(); settle(pg); name(pg)
    vis(pg.get_by_text("Rahmen korrigieren")).click(); settle(pg)
    w = pg.get_by_role("spinbutton", name="Breite"); w.fill("5000"); w.press("Tab"); settle(pg)
    report("außerhalb der Bildbreite" in main(pg), "Ungültige Breite: deutsche Meldung"); w = pg.get_by_role("spinbutton", name="Breite"); w.fill("924"); w.press("Tab"); settle(pg)
    x = pg.get_by_role("spinbutton", name="x (links)"); x.focus(); x.press("ArrowUp"); x.press("ArrowUp"); x.press("Tab"); settle(pg)
    vis(pg.get_by_role("button", name="Rahmen speichern (Entwurf)")).click(); settle(pg)
    tick(pg, "Der Rahmen erfasst den Bereich vollständig.")
    vis(pg.get_by_role("button", name="Rahmen als geprüft bestätigen")).click(); settle(pg)
    report("Bestätigt von " + NAME in main(pg), "Rahmen geändert, gespeichert, bestätigt")
    vis(pg.get_by_role("button", name="Weiter")).click(); settle(pg)
    vis(pg.get_by_text("Manuelle Klasse trifft zu: Abbildung")).click()
    vis(pg.get_by_label("Begründung: Welche Beobachtungen")).fill("TESTBEGRÜNDUNG Windows")
    vis(pg.get_by_role("button", name="Entscheidung mit Namen speichern")).click(); settle(pg)
    report("TESTBEGRÜNDUNG Windows" in main(pg), "Klassifikation gespeichert")
    vis(pg.get_by_role("button", name="Weiter")).click(); settle(pg)
    ta = vis(pg.get_by_label("Bildbeschreibung (sichtbarer Inhalt, ohne Deutung)")); ta.fill(TEXT); pg.keyboard.press("Tab"); settle(pg)
    vis(pg.get_by_role("button", name="Text speichern (Entwurf)")).click(); settle(pg)
    tick(pg, "Ich habe die Beschreibung am Bild geprüft."); vis(pg.get_by_role("button", name="Als geprüft bestätigen")).click(); settle(pg)
    tick(pg, "Ich habe die Suchbegriffe am Bild geprüft."); vis(pg.get_by_role("button", name="Als geprüft bestätigen")).click(); settle(pg)
    vis(pg.get_by_role("button", name="Weiter")).click(); settle(pg)
    vis(pg.get_by_text("Illustrator bleibt unbekannt; Feld bewusst leer")).click()
    vis(pg.get_by_label("Begründung: Welche Quellen")).fill("TEST Windows")
    vis(pg.get_by_role("button", name="Entscheidung mit Namen speichern")).click(); settle(pg)
    tick(pg, "Ich bestätige den gesamten gespeicherten Arbeitsstand; keine Ground-Truth-Freigabe.")
    vis(pg.get_by_role("button", name="Endbestätigung erteilen")).click(); settle(pg)
    report("Endbestätigung erteilt von " + NAME in main(pg), "Endbestätigung erteilt")
    vis(pg.get_by_role("button", name="Weiter")).click(); settle(pg)
    vis(pg.get_by_role("button", name="JSON und CSV exportieren")).click(); settle(pg)
    vis(pg.get_by_role("button", name="Export erneut laden und prüfen")).click(); settle(pg)
    t = main(pg); report("Export geprüft" in t and "6 von 6 Prüfpunkten erhalten" in t and "Prüfung fehlgeschlagen" not in t, "Rückladeprüfung 6/6"); shot(pg, "02-export")

def after_restart(pg, browser):
    pg.locator("[data-testid=stSidebar]").get_by_text("5 · Genovefa, Scan 22", exact=True).click(); settle(pg, 3000)
    report("ALLE 5 SCHRITTE ERLEDIGT" in main(pg).upper() and "4 von 4 bestätigt" in main(pg), "Nach Serverneustart: Scan 22 vollständig")
    tab(pg, "Prüfung"); report("Endbestätigung erteilt von " + NAME in main(pg), "Nach Neustart: Endbestätigung sichtbar")
    tab(pg, "Export"); report("Export aktuell" in main(pg), "Nach Neustart: Export aktuell")
    e = json.loads((DATA / "exports" / "genovefa-scan-022.json").read_text(encoding="utf-8")); r = e["record"]
    report(r["image_description"]["working_description_de"] == TEXT, "JSON: Sonderzeichen exakt")
    report(r["source"]["printed_page_number"] is None and r["image_description"]["illustrator"] is None, "JSON: null bleibt null")
    report(r["region_annotations"][0]["xywh"] == [231, 299, 924, 617], "JSON: Koordinaten", r["region_annotations"][0]["xywh"])
    report(r["final_approval"]["by"] == NAME, "JSON: Prüfername")
    raw = (DATA / "exports" / "genovefa-scan-022.csv").read_bytes()
    c = list(csv.DictReader((DATA / "exports" / "genovefa-scan-022.csv").open(encoding="utf-8-sig", newline="")))[0]
    report(raw.startswith(b"\xef\xbb\xbf") and c["beschreibung"] == TEXT and c["illustrator"] == "", "CSV: BOM, Sonderzeichen, null als leere Zelle")
    pg.locator("[data-testid=stSidebar]").get_by_text("1 · Die Heimath in Amerika, Scan 6", exact=True).click(); settle(pg, 3000)
    tab(pg, "Transkription"); report("‘Die Geimatly „ir Amerika." in main(pg), "Heimath: OCR-Ausgabe")
    for label in ["2 · Genovefa, Scan 14", "6 · Genovefa, Scan 85"]:
        pg.locator("[data-testid=stSidebar]").get_by_text(label, exact=True).click(); settle(pg, 3000)
        report("Traceback" not in main(pg), f"{label} öffnet ohne Fehler")
    shot(pg, "03-nach-neustart")

with sync_playwright() as p:
    browser = p.chromium.launch(channel=CHANNEL)
    print("Browser:", CHANNEL, browser.version, flush=True)
    pg = browser.new_page(viewport={"width": 1440, "height": 900}, accept_downloads=True)
    pg.goto(URL); pg.get_by_text("Fallstudie").first.wait_for(timeout=120000); settle(pg)
    {"flow": flow, "after_restart": after_restart}[PHASE](pg, browser)
    browser.close()
sys.exit(1 if failures else 0)
