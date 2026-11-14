"""Tests zu REGELN.md. Erwartungswerte von Hand berechnet (siehe TESTFAELLE.md).
Der Code darf an diese Werte angepasst werden, nie umgekehrt."""
from datetime import date

import pytest

from prueffristen.regeln import bewerte

S = date(2026, 11, 9)


def eins(geraet, art, stichtag=S, regelsatz="DE"):
    treffer = [e for e in bewerte(geraet, stichtag, regelsatz) if e.art == art]
    assert len(treffer) == 1, f"genau ein {art}-Ergebnis erwartet, erhalten: {treffer}"
    return treffer[0]


def stk_geraet(**felder):
    g = {"anlage1_nr": "1.5", "kategorie": "beatmung"}
    g.update(felder)
    return g


# ---------- DE-STK ----------
@pytest.mark.parametrize("nr, felder, faellig, tage, status", [
    ("T01", dict(inbetriebnahme=date(2025, 3, 15)), date(2027, 3, 31), 142, "in Ordnung"),
    ("T02", dict(letzte_stk=date(2024, 11, 2)), date(2026, 11, 30), 21, "bald fällig"),
    ("T03", dict(letzte_stk=date(2024, 1, 31)), date(2026, 1, 31), -282, "überfällig"),
    ("T04", dict(letzte_stk=date(2025, 8, 17)), date(2027, 8, 31), 295, "in Ordnung"),
    ("T05", dict(inbetriebnahme=date(2024, 2, 29)), date(2026, 2, 28), -254, "überfällig"),
    ("T06", dict(letzte_stk=date(2024, 12, 14)), date(2026, 12, 31), 52, "bald fällig"),
    ("T11", dict(letzte_stk=date(2026, 5, 10), stk_intervall_monate=12), date(2027, 5, 31), 203, "in Ordnung"),
])
def test_stk_fristen(nr, felder, faellig, tage, status):
    e = eins(stk_geraet(**felder), "STK")
    assert (e.faellig_am, e.tage, e.status) == (faellig, tage, status), nr


@pytest.mark.parametrize("nr, stichtag, felder, tage, status", [
    ("T07", date(2026, 11, 30), dict(letzte_stk=date(2024, 11, 2)), 0, "bald fällig"),
    ("T08", date(2026, 12, 1), dict(letzte_stk=date(2024, 11, 2)), -1, "überfällig"),
    ("T09", date(2026, 12, 31), dict(inbetriebnahme=date(2025, 3, 15)), 90, "bald fällig"),
    ("T10", date(2026, 12, 30), dict(inbetriebnahme=date(2025, 3, 15)), 91, "in Ordnung"),
])
def test_grenzen(nr, stichtag, felder, tage, status):
    e = eins(stk_geraet(**felder), "STK", stichtag=stichtag)
    assert (e.tage, e.status) == (tage, status), nr


def test_T12_intervall_ueber_24_wird_gekappt():
    e = eins(stk_geraet(letzte_stk=date(2024, 11, 2), stk_intervall_monate=30), "STK")
    assert e.faellig_am == date(2026, 11, 30) and e.status == "bald fällig"
    assert any("DQ-6" in h for h in e.hinweise)


def test_T13_anderes_geraet_ohne_intervall():
    e = eins({"kategorie": "ekg", "aktiv": True, "inbetriebnahme": date(2025, 1, 1)}, "STK")
    assert e.status == "Festlegung fehlt" and e.regel_id == "DE-STK-4"


def test_T14_anderes_geraet_mit_intervall():
    e = eins({"kategorie": "ekg", "aktiv": True, "letzte_stk": date(2026, 5, 10),
              "stk_intervall_monate": 12}, "STK")
    assert (e.faellig_am, e.status) == (date(2027, 5, 31), "in Ordnung")
    assert any("Betreiber" in h for h in e.hinweise)


def test_T15_laien_aed():
    e = eins({"kategorie": "aed_laien", "anlage1_nr": "1.1", "inbetriebnahme": date(2025, 1, 1)}, "STK")
    assert e.status == "nicht abgedeckt"


def test_T16_bezugsdatum_fehlt():
    e = eins(stk_geraet(), "STK")
    assert e.status == "Datenfehler"


# ---------- DE-MTK ----------
@pytest.mark.parametrize("nr, anlage2, mtk, faellig, tage, status", [
    ("T17", "1.2.3", date(2025, 12, 20), date(2026, 12, 31), 52, "bald fällig"),
    ("T18", "1.2.3", date(2025, 1, 2), date(2026, 12, 31), 52, "bald fällig"),
    ("T19", "1.2.3", date(2025, 3, 5), date(2026, 12, 31), 52, "bald fällig"),
    ("T20", "1.3", date(2025, 3, 15), date(2027, 12, 31), 417, "in Ordnung"),
    ("T21", "1.1", date(2026, 6, 30), date(2027, 12, 31), 417, "in Ordnung"),
    ("T22", "1.6", date(2022, 7, 1), date(2027, 12, 31), 417, "in Ordnung"),
])
def test_mtk_fristen(nr, anlage2, mtk, faellig, tage, status):
    e = eins({"anlage2_nr": anlage2, "letzte_mtk": mtk}, "MTK")
    assert (e.faellig_am, e.tage, e.status) == (faellig, tage, status), nr


def test_T23_eingriff_macht_sofort_faellig():
    e = eins({"anlage2_nr": "1.3", "letzte_mtk": date(2025, 10, 10),
              "eingriff_seit_letzter_mtk": True}, "MTK")
    assert e.status == "sofort fällig" and e.regel_id == "DE-MTK-3"


def test_T24_therapiedosimeter():
    e = eins({"anlage2_nr": "1.5.1", "letzte_mtk": date(2025, 1, 1)}, "MTK")
    assert e.status == "nicht abgedeckt"


# ---------- CH ----------
@pytest.mark.parametrize("nr, monate, letzte, faellig, tage, status", [
    ("T25", 12, date(2026, 3, 15), date(2027, 3, 15), 126, "in Ordnung"),
    ("T26", 1, date(2026, 1, 31), date(2026, 2, 28), -254, "überfällig"),
    ("T27", 12, date(2024, 2, 29), date(2025, 2, 28), -619, "überfällig"),
])
def test_ch_fristen(nr, monate, letzte, faellig, tage, status):
    e = eins({"intervall_monate": monate, "letzte_instandhaltung": letzte},
             "Instandhaltung", regelsatz="CH")
    assert (e.faellig_am, e.tage, e.status) == (faellig, tage, status), nr


def test_T28_ch_ohne_intervall():
    e = eins({"letzte_instandhaltung": date(2026, 1, 1)}, "Instandhaltung", regelsatz="CH")
    assert e.status == "Festlegung fehlt" and e.regel_id == "CH-2"


# ---------- Befunde der unabhängigen Gegenprüfung (11.11.2026) ----------
def test_T29_intervall_null_ist_datenfehler():
    e = eins(stk_geraet(letzte_stk=date(2026, 1, 1), stk_intervall_monate=0), "STK")
    assert e.status == "Datenfehler" and e.faellig_am is None


def test_T30_betreiberintervall_ueber_24_ist_datenfehler():
    e = eins({"kategorie": "ekg", "aktiv": True, "letzte_stk": date(2026, 1, 1), "stk_intervall_monate": 30}, "STK")
    assert e.status == "Datenfehler" and e.faellig_am is None


def test_T31_leerzeichen_zaehlt_als_leer():
    e = eins(stk_geraet(letzte_stk=" ", inbetriebnahme=date(2025, 3, 15)), "STK")
    assert e.faellig_am == date(2027, 3, 31)


@pytest.mark.parametrize("nr", ["1.50", "1.2", "9"])
def test_T32_unbekannte_anlage2_nummer(nr):
    e = eins({"anlage2_nr": nr, "letzte_mtk": date(2025, 1, 1)}, "MTK")
    assert e.status == "Datenfehler"


def test_T33_intervall_keine_zahl():
    e = eins(stk_geraet(letzte_stk=date(2026, 1, 1), stk_intervall_monate="zwölf"), "STK")
    assert e.status == "Datenfehler"
