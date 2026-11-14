"""Werkzeuge für den MCP-Server – ohne MCP-Abhängigkeit, damit sie direkt testbar sind.

Zugriff nur auf die zwei fest hinterlegten Bestände (kein freier Dateipfad → kein Path Traversal).
Alle Ergebnisse sind JSON-fähige dicts mit Regel-IDs und Hinweisen.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import List, Optional

from .auswertung import werte_aus
from .einlesen import parse_datum
from .kennzahlen import berechne
from .regeln import (BALD_FAELLIG, DATENFEHLER, FESTLEGUNG_FEHLT, IN_ORDNUNG, NICHT_ABGEDECKT, SOFORT_FAELLIG,
                     UEBERFAELLIG)

BASIS = Path(__file__).resolve().parent.parent
DATEN = BASIS / "daten"
AUSGABE = BASIS / "ausgabe"
BESTAENDE = {
    "klinikum_musterstadt": {"datei": "geraete_de.csv", "regelsatz": "DE", "haus": "Klinikum Musterstadt (fiktiv)"},
    "spital_musterhausen": {"datei": "geraete_ch.csv", "regelsatz": "CH", "haus": "Spital Musterhausen (fiktiv)"},
}
ALLE_STATUS = [UEBERFAELLIG, SOFORT_FAELLIG, BALD_FAELLIG, IN_ORDNUNG, FESTLEGUNG_FEHLT, NICHT_ABGEDECKT, DATENFEHLER]
HINWEIS = ("Demonstration mit synthetischen Daten; kein Medizinprodukt, keine Rechtsberatung. "
           "Festlegungen und Freigaben trifft die verantwortliche Fachperson.")


def _bestand(name: str) -> dict:
    if name not in BESTAENDE:
        raise ValueError(f"Unbekannter Bestand '{name}'. Verfügbar: {sorted(BESTAENDE)}")
    return BESTAENDE[name]


def _datum(text: Optional[str], feld: str) -> Optional[date]:
    if text is None or str(text).strip() == "":
        return None
    d, problem = parse_datum(text)
    if problem:
        raise ValueError(f"{feld}: {problem[1]} – bitte im Format TT.MM.JJJJ angeben")
    return d


def _fmt(d) -> Optional[str]:
    return d.strftime("%d.%m.%Y") if isinstance(d, date) else d


def _auswertung(bestand: str, stichtag: str):
    b = _bestand(bestand)
    tag = _datum(stichtag, "stichtag")
    if tag is None:
        raise ValueError("stichtag fehlt (TT.MM.JJJJ)")
    return werte_aus(DATEN / b["datei"], b["regelsatz"], tag)


def _eintrag(g: dict, e) -> dict:
    return {"inventarnr": g.get("inventarnr") or None, "zeile": g["_zeile"], "bezeichnung": g.get("bezeichnung"),
            "standort": g.get("standort") or None, "zuordnung": g.get("zuordnung"),
            "geraetestatus": g.get("status"), "pruefung": e.art, "status": e.status,
            "faellig_am": _fmt(e.faellig_am), "tage_bis_faellig": e.tage, "regel": e.regel_id, "hinweise": e.hinweise}


def liste_bestaende() -> dict:
    return {"bestaende": [{"name": n, "haus": b["haus"], "regelsatz": b["regelsatz"], "datei": b["datei"]}
                          for n, b in BESTAENDE.items()], "hinweis": HINWEIS}


def uebersicht(bestand: str, stichtag: str) -> dict:
    a = _auswertung(bestand, stichtag)
    k = asdict(berechne(a))
    return {"bestand": bestand, "haus": _bestand(bestand)["haus"], "regelsatz": a.regelsatz,
            "stichtag": _fmt(a.stichtag), **k, "hinweis": HINWEIS}


def fristen(bestand: str, stichtag: str, status: Optional[List[str]] = None, pruefung: Optional[str] = None,
            bereich: Optional[str] = None, faellig_von: Optional[str] = None, faellig_bis: Optional[str] = None) -> dict:
    if isinstance(status, str):
        status = [status]
    if pruefung and pruefung.casefold() not in {"stk", "mtk", "instandhaltung"}:
        raise ValueError(f"Unbekannte Prüfart '{pruefung}'. Erlaubt: STK, MTK, Instandhaltung")
    for s in status or []:
        if s not in ALLE_STATUS:
            raise ValueError(f"Unbekannter Status '{s}'. Erlaubt: {ALLE_STATUS}")
    von, bis = _datum(faellig_von, "faellig_von"), _datum(faellig_bis, "faellig_bis")
    a = _auswertung(bestand, stichtag)
    treffer = []
    for g, e in a.fristen:
        if status and e.status not in status:
            continue
        if pruefung and e.art.casefold() != pruefung.casefold():
            continue
        if bereich:
            text = f"{g.get('standort') or ''} {g.get('zuordnung') or ''}".casefold()
            if bereich.casefold() not in text:
                continue
        if von or bis:
            if e.faellig_am is None or (von and e.faellig_am < von) or (bis and e.faellig_am > bis):
                continue
        treffer.append((g, e))
    treffer.sort(key=lambda ge: (ge[1].faellig_am is None, ge[1].faellig_am or date.max, ge[0]["_zeile"]))
    return {"bestand": bestand, "stichtag": _fmt(a.stichtag), "anzahl": len(treffer),
            "eintraege": [_eintrag(g, e) for g, e in treffer], "hinweis": HINWEIS}


def geraet(bestand: str, inventarnr: str, stichtag: str) -> dict:
    a = _auswertung(bestand, stichtag)
    gesucht = inventarnr.strip().upper()
    funde = []
    for g in a.geraete:
        if (g.get("inventarnr") or "").strip().upper() != gesucht:
            continue
        stamm = {k: _fmt(v) for k, v in g.items() if not k.startswith("_")}
        funde.append({"zeile": g["_zeile"], "stammdaten": stamm,
                      "fristen": [_eintrag(g2, e) for g2, e in a.fristen if g2 is g],
                      "befunde": [asdict(b) for b in a.befunde if g["_zeile"] in b.zeilen]})
    if not funde:
        raise ValueError(f"Inventarnummer '{inventarnr}' nicht im Bestand '{bestand}'")
    return {"bestand": bestand, "stichtag": _fmt(a.stichtag), "anzahl_treffer": len(funde), "geraete": funde,
            "hinweis": HINWEIS}


def datenqualitaet(bestand: str, stichtag: str, regel: Optional[str] = None) -> dict:
    a = _auswertung(bestand, stichtag)
    bef = [asdict(b) for b in a.befunde if not regel or b.regel == regel]
    return {"bestand": bestand, "stichtag": _fmt(a.stichtag), "anzahl": len(bef), "befunde": bef, "hinweis": HINWEIS}


def bericht_pdf(bestand: str, stichtag: str) -> dict:
    from .bericht import baue_bericht      # reportlab erst bei Bedarf laden
    a = _auswertung(bestand, stichtag)
    b = _bestand(bestand)
    ziel = AUSGABE / f"bericht_{a.regelsatz.lower()}_{a.stichtag:%Y%m%d}.pdf"
    k = berechne(a)
    baue_bericht(a, k, ziel, b["haus"], b["datei"], synthetisch=True)
    return {"pfad": str(ziel), "urteil": k.urteil}
