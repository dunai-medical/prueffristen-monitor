"""Werkzeuge des MCP-Servers (ohne MCP getestet): Filter korrekt, Zugriff begrenzt, Fehler verständlich."""
from datetime import date

import pytest

from prueffristen import werkzeuge as w
from prueffristen.auswertung import werte_aus

S = "09.11.2026"


def test_liste_bestaende():
    namen = {b["name"] for b in w.liste_bestaende()["bestaende"]}
    assert namen == {"klinikum_musterstadt", "spital_musterhausen"}


@pytest.mark.parametrize("bestand", ["../daten/geraete_de.csv", "/etc/passwd", "geraete_de.csv", "KLINIKUM_MUSTERSTADT"])
def test_nur_hinterlegte_bestaende(bestand):
    with pytest.raises(ValueError):
        w.uebersicht(bestand, S)


@pytest.mark.parametrize("stichtag", ["", "2026-11-09", "31.02.2026", "heute"])
def test_stichtag_streng(stichtag):
    with pytest.raises(ValueError):
        w.fristen("klinikum_musterstadt", stichtag)


def test_unbekannter_status():
    with pytest.raises(ValueError):
        w.fristen("klinikum_musterstadt", S, status=["kaputt"])


def test_intensivstation_im_dezember():
    """Beispielfrage: 'Welche Geräte auf der Intensivstation sind im Dezember fällig?'"""
    r = w.fristen("klinikum_musterstadt", S, bereich="intensiv", faellig_von="01.12.2026", faellig_bis="31.12.2026")
    # unabhängige Gegenrechnung direkt aus der Auswertung
    a = werte_aus(w.DATEN / "geraete_de.csv", "DE", date(2026, 11, 9))
    soll = [(g["_zeile"], e.art) for g, e in a.fristen
            if "Intensiv" in (g.get("zuordnung") or "") and e.faellig_am
            and date(2026, 12, 1) <= e.faellig_am <= date(2026, 12, 31)]
    assert r["anzahl"] == len(soll) > 0
    assert sorted((x["zeile"], x["pruefung"]) for x in r["eintraege"]) == sorted(soll)
    assert all(x["faellig_am"].endswith(".12.2026") and x["regel"] for x in r["eintraege"])


def test_status_und_pruefart_filter():
    r = w.fristen("klinikum_musterstadt", S, status=["sofort fällig"])
    assert r["anzahl"] == 2 and all(x["regel"] == "DE-MTK-3" and x["pruefung"] == "MTK" for x in r["eintraege"])
    r = w.fristen("spital_musterhausen", S, status=["Festlegung fehlt"], pruefung="instandhaltung")
    assert r["anzahl"] > 0 and all(x["regel"] == "CH-2" for x in r["eintraege"])


def test_geraet_mit_befund():
    r = w.geraet("klinikum_musterstadt", "de-00124", S)
    (g,) = r["geraete"]
    assert g["stammdaten"]["stk_intervall_monate"] == "36"
    assert [b["regel"] for b in g["befunde"]] == ["DQ-6"]
    assert g["fristen"][0]["pruefung"] == "STK" and any("DQ-6" in h for h in g["fristen"][0]["hinweise"])


def test_geraet_dublette_zeigt_befund():
    r = w.geraet("klinikum_musterstadt", "DE-00129", S)
    assert any(b["regel"] == "DQ-3" and len(b["zeilen"]) == 2 for b in r["geraete"][0]["befunde"])


def test_geraet_unbekannt():
    with pytest.raises(ValueError):
        w.geraet("klinikum_musterstadt", "DE-99999", S)


def test_uebersicht_und_datenqualitaet():
    u = w.uebersicht("spital_musterhausen", S)
    assert u["urteil"] == "Handlungsbedarf" and u["regelsatz"] == "CH" and "hinweis" in u
    d = w.datenqualitaet("spital_musterhausen", S, regel="DQ-8")
    assert d["anzahl"] == 3


def test_status_als_text_statt_liste():
    assert w.fristen("klinikum_musterstadt", S, status="sofort fällig")["anzahl"] == 2


def test_unbekannte_pruefart():
    with pytest.raises(ValueError):
        w.fristen("klinikum_musterstadt", S, pruefung="xyz")
