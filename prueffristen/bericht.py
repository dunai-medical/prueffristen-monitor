"""PDF-Bericht: Gesamturteil, Kennzahlen, Handlungsliste, Datenqualität, Methodik und Grenzen.

Aufruf:  python -m prueffristen.bericht daten/geraete_de.csv DE --stichtag 09.11.2026 --haus "Klinikum Musterstadt (fiktiv)"
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import __version__
from .auswertung import Auswertung, werte_aus
from .einlesen import parse_datum
from .kennzahlen import BEOBACHTEN, HANDLUNGSBEDARF, Kennzahlen, berechne, handlungsliste
from .regeln import BALD_FAELLIG, FESTLEGUNG_FEHLT, NICHT_ABGEDECKT, SOFORT_FAELLIG, UEBERFAELLIG

ST = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=ST["Heading1"], fontSize=16, spaceAfter=4)
H2 = ParagraphStyle("h2", parent=ST["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=4)
TXT = ParagraphStyle("t", parent=ST["BodyText"], fontSize=9, leading=12)
KLEIN = ParagraphStyle("k", parent=TXT, fontSize=7.5, leading=9.5)
FARBE = {HANDLUNGSBEDARF: colors.HexColor("#b3261e"), BEOBACHTEN: colors.HexColor("#9a6700")}

QUELLEN = {
    "DE": ["MPBetreibV vom 14.02.2025, zuletzt geändert durch V v. 31.10.2025 (§§ 12, 14, 15, Anlagen 1 und 2)"],
    "CH": ["MepV (SR 812.213) Art. 71",
           "Swissmedic/IHS: Schweizerische Gute Praxis für die Instandhaltung von Medizinprodukten (GPI), Version 2.1, gültig ab 30.01.2026"],
}


def _p(text, stil=KLEIN):
    return Paragraph(str(text), stil)


def _tabelle(kopf, zeilen, breiten, kopf_farbe="#e8e8e8"):
    daten = [[_p(f"<b>{k}</b>") for k in kopf]] + [[_p(z) for z in zeile] for zeile in zeilen]
    t = Table(daten, colWidths=[b * mm for b in breiten], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(kopf_farbe)),
                           ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def _datum(d):
    return f"{d:%d.%m.%Y}" if d else "–"


def baue_bericht(a: Auswertung, k: Kennzahlen, ziel: Path, haus: str, quelle: str, synthetisch: bool = False) -> Path:
    ziel.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(ziel), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=15 * mm, bottomMargin=15 * mm, title="Prüffristen- und Datenqualitätsbericht")
    s = [Paragraph("Prüffristen- und Datenqualitätsbericht", H1),
         _p(f"{haus} · Regelsatz {a.regelsatz} · Stichtag {_datum(a.stichtag)} · Datei {quelle} · "
            f"erstellt {datetime.now():%d.%m.%Y %H:%M} · Prüffristen-Monitor {__version__}", TXT),
         Spacer(1, 3 * mm),
         _p("<i>" + ("Demonstration mit synthetischen Daten. " if synthetisch else "Demonstrationswerkzeug. ")
            + "Kein Medizinprodukt, keine Rechtsberatung. Ersetzt weder die Festlegung durch die verantwortliche "
            + ("Fachperson noch die Prüfung durch Personen, die die Anforderungen nach § 5 MPBetreibV erfüllen."
               if a.regelsatz == "DE" else
               "Fachperson noch die Instandhaltung durch qualifizierte Instandhalter (Art. 71 MepV, GPI).")
            + "</i>", KLEIN)]

    # 1. Gesamturteil
    s.append(Paragraph("1. Gesamturteil", H2))
    farbe = FARBE.get(k.urteil, colors.HexColor("#1e6b34"))
    s.append(Paragraph(f'<font color="{farbe.hexval()}"><b>{k.urteil}</b></font>',
                       ParagraphStyle("u", parent=TXT, fontSize=13, leading=16)))
    for zeile in k.urteil_text:
        s.append(_p(f"• {zeile}", TXT))

    # 2. Kennzahlen
    s.append(Paragraph("2. Kennzahlen", H2))
    verzug = (f"Median {k.verzug_median_tage:.0f} Tage, Maximum {k.verzug_max_tage} Tage"
              if k.ueberfaellig else "–")
    s.append(_tabelle(["Kennzahl", "Wert"], [
        ["Geräte im Bestand", k.geraete],
        ["Gerätestatus", ", ".join(f"{n}: {v}" for n, v in k.geraetestatus.items())],
        ["Altersstruktur (Inbetriebnahme)", ", ".join(f"{n}: {v}" for n, v in k.altersstruktur.items())],
        ["Überfällige Prüfungen", k.ueberfaellig], ["Verzug der überfälligen Prüfungen", verzug],
        ["Sofort fällig", k.sofort_faellig], ["Bald fällig (90 Tage)", k.bald_faellig],
        ["Intervall nicht festgelegt", k.festlegung_fehlt], ["Nicht abgedeckte Sonderfälle", k.nicht_abgedeckt],
        ["Datenqualität", f"{k.dq_fehler} Befunde „Fehler“, {k.dq_verdacht} Verdachtsfälle "
                          f"({', '.join(f'{r}: {n}' for r, n in k.dq_je_regel.items()) or 'keine'})"],
    ] + ([["Zuständigkeit Instandhaltung", ", ".join(f"{n}: {v}" for n, v in k.zustaendigkeit.items())]]
         if k.zustaendigkeit else []), [60, 120]))
    s.append(Spacer(1, 3 * mm))
    stati = [UEBERFAELLIG, SOFORT_FAELLIG, BALD_FAELLIG, "in Ordnung", FESTLEGUNG_FEHLT, NICHT_ABGEDECKT, "Datenfehler"]
    s.append(_tabelle(["Prüfart"] + stati,
                      [[art] + [c.get(st, 0) for st in stati] for art, c in sorted(k.fristen.items())],
                      [26] + [22] * 7))

    # 3. Handlungsliste
    s.append(Paragraph("3. Handlungsliste", H2))
    liste = handlungsliste(a)
    dringend, bald = liste["dringend"], liste["bald"]
    s.append(_p("Tage = fällig am minus Stichtag; negativ bedeutet Verzug in Tagen.", KLEIN))
    s.append(Spacer(1, 2 * mm))
    kopf = ["Inventar-Nr.", "Gerät", "Standort", "Gerätestatus", "Prüfart", "fällig am", "Tage", "Regel"]
    breiten = [20, 45, 25, 21, 22, 18, 12, 17]   # ausgemessen: längster Inhalt passt ohne Wortumbruch

    def zeilen(liste):
        return [[g.get("inventarnr") or f"Zeile {g['_zeile']}", g.get("bezeichnung", ""), g.get("standort", ""),
                 g.get("status", ""), e.art, _datum(e.faellig_am) if e.faellig_am else e.status,
                 e.tage if e.tage is not None else "–", e.regel_id] for g, e in liste]
    s.append(_p(f"<b>Sofort fällig und überfällig ({len(dringend)})</b> – sortiert nach Dringlichkeit", TXT))
    s.append(_tabelle(kopf, zeilen(dringend), breiten, "#f6d5d3") if dringend else _p("keine", TXT))
    s.append(Spacer(1, 3 * mm))
    s.append(_p(f"<b>Bald fällig, nächste 90 Tage ({len(bald)})</b>", TXT))
    s.append(_tabelle(kopf, zeilen(bald), breiten, "#fbeccb") if bald else _p("keine", TXT))

    offen = liste["ohne_frist"]
    if offen:
        s.append(Spacer(1, 3 * mm))
        s.append(_p(f"<b>Ohne berechenbare Frist: Datenfehler, Festlegung fehlt, Sonderfall ({len(offen)})</b>", TXT))
        s.append(_tabelle(["Inventar-Nr.", "Gerät", "Prüfart", "Status", "Hinweis"],
                          [[g.get("inventarnr") or f"Zeile {g['_zeile']}", g.get("bezeichnung", ""), e.art, e.status,
                            "; ".join(e.hinweise)] for g, e in offen], [20, 45, 22, 24, 69]))

    # 4. Datenqualität
    s.append(Paragraph("4. Datenqualität", H2))
    if a.befunde:
        bef = sorted(a.befunde, key=lambda b: (b.regel, b.zeilen[0]))
        s.append(_tabelle(["Regel", "Schwere", "Zeile(n)", "Inventar-Nr.", "Befund"],
                          [[b.regel, b.schwere, ", ".join(map(str, b.zeilen)), b.inventarnr, b.text] for b in bef],
                          [14, 18, 18, 32, 98]))
    else:
        s.append(_p("Keine Befunde.", TXT))

    # 5. Methodik und Grenzen
    s.append(Paragraph("5. Methodik und Grenzen", H2))
    for q in QUELLEN[a.regelsatz]:
        s.append(_p(f"• Quelle: {q}", TXT))
    texte = {
        "DE": ["STK: spätestens 24 Monate, gerechnet bis Monatsende (§ 12 Abs. 1 Satz 2); kürzere Intervalle des "
               "Betreibers ebenfalls bis Monatsende (Annahme A1, Prüfplakette nennt Jahr und Monat).",
               "MTK: Frist nach Anlage 2, beginnend mit Ablauf des Jahres der letzten Kontrolle (§ 15 Abs. 5); "
               "nach einem Eingriff sofort fällig.",
               "Offen: STK-Pflicht anderer Produkte (§ 12 Abs. 1 Satz 5) wird nicht entschieden, sondern als "
               "Festlegung des Betreibers ausgewiesen.",
               "Nicht abgedeckt: Laien-AED (§ 12 Abs. 2), Therapiedosimeter (Anlage 2 Nr. 1.5)."],
        "CH": ["Art. 71 MepV legt keine festen Fristen fest: Intervalle nach Herstellerangabe bzw. Festlegung der "
               "Fachperson (Art. 71 Abs. 2 MepV, GPI 7.1/7.2.1); das Werkzeug schlägt kein Intervall vor. Prüfintervalle "
               "aus anderen Erlassen (z. B. Messmittel nach Art. 71 Abs. 3 MepV, Strahlenschutz) sind nicht abgedeckt.",
               "Fälligkeit = letzte Instandhaltung + Intervall in Kalendermonaten (Annahme A2).",
               "Pflichtfelder des Inventars nach GPI 8.1; Kennzahlen angelehnt an den Tätigkeitsbericht (GPI 3.6)."],
    }
    for t in texte[a.regelsatz] + [
            "Fehlerhafte Daten: Aus einem fehlerhaften Datum wird keine Frist berechnet (Status „Datenfehler“).",
            "Fälligkeitstag zählt als „bald fällig“; Vorlauf 90 Tage.",
            "Kennzahlen zählen den Bestand, wie er geliefert wurde: Dubletten und Geräte mit Status defekt, nicht "
            "auffindbar oder außer Betrieb werden nicht herausgerechnet. Datenqualität deshalb zuerst bereinigen.",
            "Validierung des Werkzeugs (Testdaten des Projekts): 53 protokollierte Fehler, alle gefunden, keine falsch "
            "positiven Befunde. Fehler und Regeln stammen vom selben Autor; das belegt die Umsetzung der Regeln, nicht "
            "die Vollständigkeit bei realen Daten."]:
        s.append(_p(f"• {t}", TXT))

    def fusszeile(canvas, doc_):
        canvas.setFont("Helvetica", 7)
        canvas.drawString(15 * mm, 8 * mm, f"Prüffristen-Monitor {__version__} · Demonstration, kein Medizinprodukt")
        canvas.drawRightString(195 * mm, 8 * mm, f"Seite {doc_.page}")
    doc.build(s, onFirstPage=fusszeile, onLaterPages=fusszeile)
    return ziel


def main(argv=None):
    ap = argparse.ArgumentParser(description="PDF-Bericht zu Prüffristen und Datenqualität")
    ap.add_argument("csv")
    ap.add_argument("regelsatz", choices=["DE", "CH"])
    ap.add_argument("--stichtag", required=True, help="TT.MM.JJJJ")
    ap.add_argument("--haus", default="Gerätebestand")
    ap.add_argument("--ziel", default=None)
    ap.add_argument("--synthetisch", action="store_true", help="Hinweis 'synthetische Daten' in den Bericht")
    arg = ap.parse_args(argv)
    stichtag, problem = parse_datum(arg.stichtag)
    if problem or stichtag is None:
        ap.error(f"--stichtag: {problem[1] if problem else 'fehlt (TT.MM.JJJJ)'}")
    a = werte_aus(arg.csv, arg.regelsatz, stichtag)
    k = berechne(a)
    ziel = Path(arg.ziel or f"ausgabe/bericht_{arg.regelsatz.lower()}_{stichtag:%Y%m%d}.pdf")
    baue_bericht(a, k, ziel, arg.haus, Path(arg.csv).name, arg.synthetisch)
    print(f"{k.urteil}: {ziel}")


if __name__ == "__main__":
    main()
