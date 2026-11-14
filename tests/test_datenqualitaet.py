"""Tests zu REGELN.md Abschnitt 4 (DQ-1 bis DQ-9), zum Einlesen und zur Validierung."""
from datetime import date
from pathlib import Path

import pytest

from prueffristen.auswertung import werte_aus
from prueffristen.datenqualitaet import FEHLER, VERDACHT, norm_hersteller, pruefe
from prueffristen.einlesen import lese_csv, parse_datum
from prueffristen.validierung import validiere

S = date(2026, 11, 9)
DATEN = Path(__file__).resolve().parent.parent / "daten"


def de_zeile(**ersatz):
    z = {"inventarnr": "DE-1", "bezeichnung": "Defibrillator", "art_typ": "DFB-1", "seriennr": "S1",
         "anschaffungsjahr": "2020", "hersteller": "Musterwerk Medizintechnik GmbH",
         "hersteller_anschrift": "Industriestraße 1", "standort": "Haus A", "zuordnung": "Intensiv",
         "kategorie": "defibrillator", "anlage1_nr": "1.1", "anlage2_nr": "", "aktiv": "ja",
         "inbetriebnahme": "01.06.2020", "letzte_stk": "01.06.2025", "stk_intervall_monate": "",
         "letzte_mtk": "", "eingriff_seit_letzter_mtk": "nein", "status": "betriebsbereit"}
    z.update(ersatz)
    return z


def regeln_von(zeilen, regelsatz="DE"):
    return sorted(b.regel for b in pruefe(zeilen, regelsatz, S)[1])


# ---------- Datumsangaben ----------
@pytest.mark.parametrize("text, datum, regel", [
    ("05.03.2025", date(2025, 3, 5), None),
    ("", None, None),
    ("31.02.2025", None, "DQ-4"),
    ("03/04/2025", None, "DQ-5"),
    ("2025-04-03", None, "DQ-5"),
    ("5.3.2025", None, "DQ-5"),
])
def test_parse_datum(text, datum, regel):
    d, problem = parse_datum(text)
    assert d == datum
    assert (problem[0] if problem else None) == regel


def test_csv_mit_und_ohne_bom_gleich(tmp_path):
    inhalt = "inventarnr;bezeichnung\nDE-1;Prüfgerät\n"
    (tmp_path / "mit.csv").write_text(inhalt, encoding="utf-8-sig")
    (tmp_path / "ohne.csv").write_text(inhalt, encoding="utf-8")
    assert lese_csv(tmp_path / "mit.csv") == lese_csv(tmp_path / "ohne.csv") == [
        {"inventarnr": "DE-1", "bezeichnung": "Prüfgerät"}]


# ---------- DE ----------
def test_saubere_zeile_ohne_befund():
    assert regeln_von([de_zeile()]) == []


@pytest.mark.parametrize("ersatz, regel", [
    (dict(seriennr=""), "DQ-1"),
    (dict(hersteller_anschrift=""), "DQ-1"),
    (dict(inventarnr=""), None),                         # § 14: nur "soweit vorhanden"
    (dict(letzte_stk="31.02.2025"), "DQ-4"),
    (dict(letzte_stk="01.12.2026"), "DQ-4"),             # Zukunft
    (dict(letzte_stk="01.01.2020"), "DQ-4"),             # vor Inbetriebnahme
    (dict(anschaffungsjahr="2021"), "DQ-4"),             # nach Inbetriebnahme 2020
    (dict(letzte_stk="03/04/2025"), "DQ-5"),
    (dict(stk_intervall_monate="36"), "DQ-6"),
    (dict(stk_intervall_monate="0"), "DQ-6"),
    (dict(inbetriebnahme="", letzte_stk=""), "DQ-9"),
])
def test_de_einzelfehler(ersatz, regel):
    assert regeln_von([de_zeile(**ersatz)]) == ([regel] if regel else [])


def test_dublette_exakt_und_verdacht():
    zeilen = [de_zeile(inventarnr="A"), de_zeile(inventarnr="B"),
              de_zeile(inventarnr="C", seriennr="S2"), de_zeile(inventarnr="D", seriennr="S2", hersteller="Musterwerk Medizintechnik"),
              de_zeile(inventarnr="E", seriennr="S3"), de_zeile(inventarnr="F", seriennr="S4")]
    d = [b for b in pruefe(zeilen, "DE", S)[1] if b.regel == "DQ-3"]
    assert [(b.schwere, b.zeilen) for b in d] == [(FEHLER, [1, 2]), (VERDACHT, [3, 4])]


def test_norm_hersteller():
    assert norm_hersteller("Demo Devices SA") == norm_hersteller("DEMO DEVICES SA") == "demo devices"


def test_keine_frist_aus_fehlerhaftem_datum(tmp_path):
    """Ungültige letzte STK darf nicht still durch die Inbetriebnahme ersetzt werden."""
    import csv
    p = tmp_path / "x.csv"
    z = de_zeile(letzte_stk="31.02.2025")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(z), delimiter=";"); w.writeheader(); w.writerow(z)
    (_, e), = werte_aus(p, "DE", S).fristen
    assert e.status == "Datenfehler" and e.faellig_am is None


# ---------- CH ----------
def ch_zeile(**ersatz):
    z = {"inventarnr": "CH-1", "bezeichnung": "EKG-Gerät", "hersteller": "Demo Devices SA", "modell": "EKG-1",
         "udi_oder_seriennr": "U1", "typ": "MP", "risikoklasse": "IIa", "lieferant": "MediHandel",
         "zustaendig": "Medizintechnik intern", "standort": "Haus A", "status": "betriebsbereit",
         "inbetriebnahme": "01.06.2020", "letzte_instandhaltung": "15.03.2026",
         "naechste_instandhaltung": "15.03.2027", "intervall_monate": "12", "schutzklasse": "I",
         "anwendungsteil": "CF", "sw_version": "1.0", "netzwerk": "ja"}
    z.update(ersatz)
    return z


@pytest.mark.parametrize("ersatz, regel", [
    ({}, None),
    (dict(risikoklasse=""), "DQ-2"),
    (dict(naechste_instandhaltung=""), "DQ-2"),
    (dict(naechste_instandhaltung="15.06.2027"), "DQ-8"),
    (dict(intervall_monate="", naechste_instandhaltung=""), None),     # Festlegung fehlt: kein Datenfehler
    (dict(letzte_instandhaltung="", naechste_instandhaltung="01.06.2021"), None),  # Bezug Inbetriebnahme
])
def test_ch_einzelfehler(ersatz, regel):
    assert regeln_von([ch_zeile(**ersatz)], "CH") == ([regel] if regel else [])


# ---------- Validierung gegen das Fehlerprotokoll ----------
@pytest.mark.parametrize("datei, regelsatz", [("geraete_de.csv", "DE"), ("geraete_ch.csv", "CH")])
def test_validierung_synthetische_daten(datei, regelsatz):
    """Regressionstest: alle eingebauten Fehler gefunden, keine falsch positiven Befunde.
    Grenze: Fehler und Regeln vom selben Autor – siehe validierung.py."""
    a = werte_aus(DATEN / datei, regelsatz, S)
    v = validiere(a.befunde, lese_csv(DATEN / "fehlerprotokoll.csv"), datei)
    assert v["verpasst"] == [] and v["falsch_positiv"] == []
    assert len(v["treffer"]) == len(v["erwartet"]) > 0


# ---------- Befunde der unabhängigen Gegenprüfung (11.11.2026) ----------
def schreibe_csv(pfad, zeilen):
    import csv
    with open(pfad, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(zeilen[0]), delimiter=";")
        w.writeheader()
        w.writerows(zeilen)
    return pfad


@pytest.mark.parametrize("wert", ["j", "yes", "x", "1"])
def test_DQ10_eingriff_nie_still_nein(tmp_path, wert):
    z = de_zeile(kategorie="nibp", anlage1_nr="", anlage2_nr="1.3", letzte_stk="", letzte_mtk="10.10.2025",
                 eingriff_seit_letzter_mtk=wert)
    a = werte_aus(schreibe_csv(tmp_path / "x.csv", [z]), "DE", S)
    assert [b.regel for b in a.befunde] == ["DQ-10"]
    mtk = [e for _, e in a.fristen if e.art == "MTK"][0]
    assert mtk.status == "Datenfehler"


@pytest.mark.parametrize("wert", ["ja", "JA", " Ja ", "nein", "NEIN", ""])
def test_DQ10_zulaessige_werte(wert):
    assert regeln_von([de_zeile(eingriff_seit_letzter_mtk=wert)]) == []


def test_DQ10_aktiv_ungueltig_ergibt_datenfehler(tmp_path):
    z = de_zeile(kategorie="ekg", anlage1_nr="", aktiv="x", letzte_stk="")
    a = werte_aus(schreibe_csv(tmp_path / "x.csv", [z]), "DE", S)
    (_, e), = a.fristen
    assert e.status == "Datenfehler" and e.regel_id == "DQ-10"


@pytest.mark.parametrize("ersatz", [dict(anlage1_nr="1.9"), dict(anlage2_nr="1.2"), dict(anlage2_nr="1.50")])
def test_DQ7_unbekannte_anlage_nummer(ersatz):
    assert regeln_von([de_zeile(**ersatz)]) == ["DQ-7"]


def test_DQ7_anlage1_falsch_keine_frist(tmp_path):
    a = werte_aus(schreibe_csv(tmp_path / "x.csv", [de_zeile(anlage1_nr="1.9")]), "DE", S)
    (_, e), = a.fristen
    assert e.status == "Datenfehler" and e.faellig_am is None


def test_DQ3_inventarnummer_doppelt():
    d = [b for b in pruefe([de_zeile(inventarnr="X", seriennr="S1"), de_zeile(inventarnr="x", seriennr="S2")], "DE", S)[1]]
    assert [(b.regel, b.schwere, b.zeilen, b.feld) for b in d] == [("DQ-3", FEHLER, [1, 2], "inventarnr")]


def test_DQ3_gruppe_ein_befund():
    zeilen = [de_zeile(inventarnr=i) for i in "ABC"]
    d = pruefe(zeilen, "DE", S)[1]
    assert [(b.schwere, b.zeilen) for b in d] == [(FEHLER, [1, 2, 3])]


def test_DQ3_leerer_hersteller_nur_verdacht():
    zeilen = [de_zeile(inventarnr="A", hersteller=""), de_zeile(inventarnr="B", hersteller="")]
    d = [b for b in pruefe(zeilen, "DE", S)[1] if b.regel == "DQ-3"]
    assert [(b.schwere, b.zeilen) for b in d] == [(VERDACHT, [1, 2])]


def test_norm_hersteller_akzente():
    assert norm_hersteller("Médical Suisse SA") == "médical suisse"


def test_negativkontrolle_validierung():
    """Wird die Seriennummer-Prüfung abgeschaltet, muss die Validierung genau die 4 Fälle als verpasst melden."""
    import prueffristen.datenqualitaet as dq
    gesichert = dict(dq.PFLICHT_DE)
    try:
        dq.PFLICHT_DE.pop("seriennr")
        a = werte_aus(DATEN / "geraete_de.csv", "DE", S)
        v = validiere(a.befunde, lese_csv(DATEN / "fehlerprotokoll.csv"), "geraete_de.csv")
        assert len(v["verpasst"]) == 4 and {r for _, r in v["verpasst"]} == {"DQ-1"}
    finally:
        dq.PFLICHT_DE.clear()
        dq.PFLICHT_DE.update(gesichert)
