"""Kennzahlen, Gesamturteil und PDF-Erzeugung."""
from datetime import date
from pathlib import Path

import pytest

from prueffristen.auswertung import werte_aus
from prueffristen.kennzahlen import BEOBACHTEN, HANDLUNGSBEDARF, KEINE, Kennzahlen, berechne, urteil

S = date(2026, 11, 9)
DATEN = Path(__file__).resolve().parent.parent / "daten"


def leer(**ersatz):
    k = Kennzahlen(geraete=1, geraetestatus={}, altersstruktur={}, fristen={}, ueberfaellig=0,
                   verzug_median_tage=None, verzug_max_tage=None, sofort_faellig=0, bald_faellig=0,
                   festlegung_fehlt=0, nicht_abgedeckt=0, frist_datenfehler=0, dq_fehler=0, dq_verdacht=0, dq_je_regel={})
    for f, w in ersatz.items():
        setattr(k, f, w)
    return k


@pytest.mark.parametrize("ersatz, erwartet", [
    ({}, KEINE),
    (dict(bald_faellig=3), BEOBACHTEN),
    (dict(dq_verdacht=1), BEOBACHTEN),
    (dict(festlegung_fehlt=1), BEOBACHTEN),
    (dict(ueberfaellig=1, verzug_max_tage=5), HANDLUNGSBEDARF),
    (dict(sofort_faellig=1), HANDLUNGSBEDARF),
    (dict(dq_fehler=1), HANDLUNGSBEDARF),
])
def test_urteil(ersatz, erwartet):
    assert urteil(leer(**ersatz))[0] == erwartet


def test_urteil_einzahl():
    assert urteil(leer(ueberfaellig=1, verzug_max_tage=5))[1][0].startswith("1 Prüfung überfällig")


@pytest.mark.parametrize("datei, regelsatz", [("geraete_de.csv", "DE"), ("geraete_ch.csv", "CH")])
def test_kennzahlen_stimmig(datei, regelsatz):
    a = werte_aus(DATEN / datei, regelsatz, S)
    k = berechne(a)
    assert k.geraete == len(a.geraete)
    assert sum(sum(c.values()) for c in k.fristen.values()) == len(a.fristen)
    assert sum(k.altersstruktur.values()) == k.geraete
    assert k.dq_fehler + k.dq_verdacht == len(a.befunde)
    if k.ueberfaellig:
        assert 0 < k.verzug_median_tage <= k.verzug_max_tage


def test_pdf_wird_erzeugt(tmp_path):
    pytest.importorskip("reportlab")
    from prueffristen.bericht import baue_bericht
    a = werte_aus(DATEN / "geraete_de.csv", "DE", S)
    ziel = baue_bericht(a, berechne(a), tmp_path / "b.pdf", "Test", "geraete_de.csv")
    inhalt = ziel.read_bytes()
    assert inhalt.startswith(b"%PDF") and len(inhalt) > 5000


@pytest.mark.parametrize("datei, regelsatz", [("geraete_de.csv", "DE"), ("geraete_ch.csv", "CH")])
def test_handlungsliste_vollstaendig(datei, regelsatz):
    """Jede Frist, die nicht 'in Ordnung' ist, steht genau einmal in der Handlungsliste."""
    from prueffristen.kennzahlen import handlungsliste
    a = werte_aus(DATEN / datei, regelsatz, S)
    liste = handlungsliste(a)
    eintraege = [id(e) for gruppe in liste.values() for _, e in gruppe]
    offen = [id(e) for _, e in a.fristen if e.status != "in Ordnung"]
    assert sorted(eintraege) == sorted(offen) and len(set(eintraege)) == len(eintraege)
    assert any(e.status == "Datenfehler" for _, e in liste["ohne_frist"])


def test_ch_urteil_spricht_von_instandhaltung():
    k = berechne(werte_aus(DATEN / "geraete_ch.csv", "CH", S))
    assert any("Instandhaltungen überfällig" in t for t in k.urteil_text)
    assert not any("Prüfung" in t for t in k.urteil_text)
    assert sum(k.zustaendigkeit.values()) == k.geraete


@pytest.mark.parametrize("stichtag", ["9.11.2026", "2026-11-09", "31.02.2026"])
def test_bericht_cli_stichtag_streng(stichtag):
    pytest.importorskip("reportlab")
    from prueffristen.bericht import main
    with pytest.raises(SystemExit):
        main([str(DATEN / "geraete_de.csv"), "DE", "--stichtag", stichtag, "--ziel", "/dev/null"])
