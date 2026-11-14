"""Datenqualitätsprüfung nach REGELN.md Abschnitt 4 (DQ-1 bis DQ-9).

Liefert je Zeile ein bereinigtes Gerät (Datumsfelder als date oder None) und eine Liste von Befunden.
Felder mit fehlerhaftem Inhalt landen in g["_ungueltig"]; Fristen aus solchen Feldern werden
später nicht berechnet, sondern als Datenfehler ausgewiesen.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Tuple

from .einlesen import parse_datum
from .regeln import ANLAGE1_NUMMERN, ANLAGE2_NUMMERN, STK_HOECHSTFRIST_MONATE, plus_monate

FEHLER, VERDACHT = "Fehler", "Verdacht"

# § 14 Abs. 2 MPBetreibV (betriebliche Identifikationsnummer nur "soweit vorhanden" → nicht Pflicht)
PFLICHT_DE = {"bezeichnung": "Bezeichnung", "art_typ": "Art und Typ", "seriennr": "Loscode oder Seriennummer",
              "anschaffungsjahr": "Anschaffungsjahr", "hersteller": "Hersteller",
              "hersteller_anschrift": "Anschrift des Herstellers", "standort": "Standort",
              "zuordnung": "betriebliche Zuordnung"}
# GPI Kap. 8.1; letzte/nächste Massnahme gesondert (s. REGELN DQ-2, Präzisierung)
PFLICHT_CH = {"inventarnr": "Inventarnummer", "bezeichnung": "Bezeichnung", "hersteller": "Hersteller",
              "modell": "Modell", "udi_oder_seriennr": "UDI oder Seriennummer", "typ": "Typ (MP/IVD)",
              "risikoklasse": "Risikoklasse", "lieferant": "Lieferant", "zustaendig": "Zuständigkeit Instandhaltung",
              "standort": "Standort", "status": "Zustand/Status", "inbetriebnahme": "Datum der Inbetriebnahme",
              "schutzklasse": "Schutzklasse", "anwendungsteil": "Typ Anwendungsteil",
              "sw_version": "Softwareversion", "netzwerk": "Netzwerkverbindung"}
DATUM = {"DE": ["inbetriebnahme", "letzte_stk", "letzte_mtk"],
         "CH": ["inbetriebnahme", "letzte_instandhaltung", "naechste_instandhaltung"]}
VERGANGENHEIT = {"inbetriebnahme", "letzte_stk", "letzte_mtk", "letzte_instandhaltung"}
NACH_INBETRIEBNAHME = {"letzte_stk", "letzte_mtk", "letzte_instandhaltung"}
SERIE = {"DE": "seriennr", "CH": "udi_oder_seriennr"}
RECHTSFORMEN = {"gmbh", "ag", "kg", "sa", "se", "ohg", "ltd", "inc", "co"}
JA_NEIN = {"ja", "nein"}


@dataclass
class Befund:
    regel: str
    schwere: str
    zeilen: List[int]
    inventarnr: str
    feld: str
    text: str


def _leer(w) -> bool:
    return w is None or str(w).strip() == ""


def norm_hersteller(name: str) -> str:
    woerter = re.findall(r"[^\W_]+", (name or "").casefold())   # Unicode: auch é, è, à …
    return " ".join(w for w in woerter if w not in RECHTSFORMEN)


def pruefe(zeilen: List[dict], regelsatz: str, stichtag: date) -> Tuple[List[dict], List[Befund]]:
    if regelsatz not in DATUM:
        raise ValueError(f"Unbekannter Regelsatz: {regelsatz!r}")
    geraete, befunde = [], []
    for nr, roh in enumerate(zeilen, start=1):
        g = dict(roh)
        g["_zeile"], g["_ungueltig"] = nr, set()
        inv = (roh.get("inventarnr") or "").strip()

        def befund(regel, feld, text, schwere=FEHLER, ungueltig=True):
            befunde.append(Befund(regel, schwere, [nr], inv, feld, text))
            if ungueltig:
                g["_ungueltig"].add(feld)

        # DQ-1 / DQ-2: Pflichtangaben
        pflicht, regel_p = (PFLICHT_DE, "DQ-1") if regelsatz == "DE" else (PFLICHT_CH, "DQ-2")
        for feld, name in pflicht.items():
            if _leer(roh.get(feld)):
                befund(regel_p, feld, f"Pflichtangabe fehlt: {name}", ungueltig=False)

        # DQ-4 / DQ-5: Datumsformat und unmögliche Daten
        for feld in DATUM[regelsatz]:
            d, problem = parse_datum(roh.get(feld))
            g[feld] = d
            if problem:
                befund(problem[0], feld, problem[1])
        ibn = g["inbetriebnahme"]
        for feld in DATUM[regelsatz]:
            d = g[feld]
            if d is None:
                continue
            if feld in VERGANGENHEIT and d > stichtag:
                befund("DQ-4", feld, f"{feld} liegt in der Zukunft ({d:%d.%m.%Y})")
            elif feld in NACH_INBETRIEBNAHME and ibn and d < ibn:
                befund("DQ-4", feld, f"{feld} ({d:%d.%m.%Y}) liegt vor der Inbetriebnahme ({ibn:%d.%m.%Y})")

        if regelsatz == "DE":
            aj = (roh.get("anschaffungsjahr") or "").strip()
            if aj and not aj.isdigit():
                befund("DQ-4", "anschaffungsjahr", f"Anschaffungsjahr „{aj}“ ist keine Jahreszahl", ungueltig=False)
            elif aj and ibn and int(aj) > ibn.year:
                befund("DQ-4", "anschaffungsjahr", f"Anschaffungsjahr {aj} liegt nach der Inbetriebnahme ({ibn.year})",
                       ungueltig=False)
            # DQ-7: Anlage-Nummern müssen in der geltenden Fassung existieren
            a1, a2 = (roh.get("anlage1_nr") or "").strip(), (roh.get("anlage2_nr") or "").strip()
            if a1 and a1 not in ANLAGE1_NUMMERN:
                befund("DQ-7", "anlage1_nr", f"Anlage-1-Nummer „{a1}“ gibt es nicht")
            if a2 and a2 not in ANLAGE2_NUMMERN:
                befund("DQ-7", "anlage2_nr", f"Anlage-2-Nummer „{a2}“ gibt es nicht")
            # DQ-10: Ja/Nein-Felder nie still umdeuten
            for feld in ("aktiv", "eingriff_seit_letzter_mtk"):
                wert = (roh.get(feld) or "").strip()
                if wert and wert.casefold() not in JA_NEIN:
                    befund("DQ-10", feld, f"„{wert}“ ist kein zulässiger Wert für {feld} (ja/nein)")
            # DQ-6: STK-Intervall 1–24 Monate
            iv = (roh.get("stk_intervall_monate") or "").strip()
            if iv:
                if not iv.isdigit() or int(iv) < 1:
                    befund("DQ-6", "stk_intervall_monate",
                           f"STK-Intervall „{iv}“ ungültig (ganze Zahl 1–24) – Frist nicht berechenbar")
                elif int(iv) > STK_HOECHSTFRIST_MONATE:
                    if a1:
                        befund("DQ-6", "stk_intervall_monate", f"STK-Intervall {iv} Monate über der Höchstfrist; "
                               "gerechnet wird mit 24 Monaten (§ 12 Abs. 1 Satz 2)", ungueltig=False)
                    else:
                        befund("DQ-6", "stk_intervall_monate", f"Festgelegtes STK-Intervall {iv} Monate über 24 – "
                               "Frist nicht berechenbar, Festlegung durch Fachperson klären", ungueltig=False)
            # DQ-9: prüfpflichtig, aber kein Bezugsdatum vorhanden
            if _leer(roh.get("inbetriebnahme")):
                if (not _leer(roh.get("anlage1_nr")) or iv) and _leer(roh.get("letzte_stk")):
                    befund("DQ-9", "inbetriebnahme", "STK-pflichtig, aber weder Inbetriebnahme noch letzte STK",
                           ungueltig=False)
                if not _leer(roh.get("anlage2_nr")) and _leer(roh.get("letzte_mtk")):
                    befund("DQ-9", "inbetriebnahme", "MTK-pflichtig, aber weder Inbetriebnahme noch letzte MTK",
                           ungueltig=False)
        else:
            iv = (roh.get("intervall_monate") or "").strip()
            if iv and (not iv.isdigit() or int(iv) < 1):
                befund("DQ-6", "intervall_monate", f"Intervall „{iv}“ ungültig (ganze Zahl ab 1 Monat)")
            elif iv:
                # DQ-2 (Präzisierung): bei festgelegtem Intervall muss die nächste Massnahme eingetragen sein
                if _leer(roh.get("naechste_instandhaltung")):
                    befund("DQ-2", "naechste_instandhaltung", "Pflichtangabe fehlt: nächste präventive Massnahme",
                           ungueltig=False)
                # DQ-8: eingetragene nächste Massnahme = Bezug + Intervall?
                letzte_roh = roh.get("letzte_instandhaltung")
                if "letzte_instandhaltung" in g["_ungueltig"] or "naechste_instandhaltung" in g["_ungueltig"]:
                    bezug = None
                else:
                    bezug = g["letzte_instandhaltung"] if not _leer(letzte_roh) else ibn
                naechste = g["naechste_instandhaltung"]
                if bezug and naechste:
                    soll = plus_monate(bezug, int(iv))
                    if soll != naechste:
                        befund("DQ-8", "naechste_instandhaltung",
                               f"nächste Instandhaltung {naechste:%d.%m.%Y}, erwartet {soll:%d.%m.%Y} "
                               f"(Bezug {bezug:%d.%m.%Y} + {iv} Monate)", ungueltig=False)
        geraete.append(g)

    befunde.extend(_dubletten(zeilen, regelsatz))
    return geraete, befunde


def _gruppen(zeilen: List[dict], schluessel) -> Dict[str, List[int]]:
    g: Dict[str, List[int]] = {}
    for nr, z in enumerate(zeilen, start=1):
        k = schluessel(z)
        if k:
            g.setdefault(k, []).append(nr)
    return {k: v for k, v in g.items() if len(v) > 1}


def _invs(zeilen, nrn):
    return " / ".join((zeilen[n - 1].get("inventarnr") or f"Zeile {n}") for n in nrn)


def _dubletten(zeilen: List[dict], regelsatz: str) -> List[Befund]:
    """DQ-3, je Gruppe ein Befund (nicht je Paar):
    - gleiche Inventarnummer mehrfach vergeben → Fehler (GPI 8.1: eindeutige Inventarnummer)
    - gleiche Seriennummer und exakt gleicher Hersteller → Fehler
    - gleiche Seriennummer, Hersteller nur ähnlich geschrieben oder leer → Verdacht"""
    feld = SERIE[regelsatz]
    befunde = []
    for inv, nrn in _gruppen(zeilen, lambda z: (z.get("inventarnr") or "").strip().upper()).items():
        befunde.append(Befund("DQ-3", FEHLER, nrn, inv, "inventarnr",
                              f"Inventarnummer {inv} ist {len(nrn)}-mal vergeben"))
    for serie, nrn in _gruppen(zeilen, lambda z: (z.get(feld) or "").strip().upper()).items():
        exakt: Dict[str, List[int]] = {}
        for n in nrn:
            exakt.setdefault((zeilen[n - 1].get("hersteller") or "").strip(), []).append(n)
        for hersteller, gleiche in exakt.items():
            if hersteller and len(gleiche) > 1:
                befunde.append(Befund("DQ-3", FEHLER, gleiche, _invs(zeilen, gleiche), feld,
                                      f"Dublette: Hersteller „{hersteller}“, Seriennummer {serie} ({len(gleiche)} Einträge)"))
        aehnlich: Dict[str, List[str]] = {}
        for hersteller in exakt:
            aehnlich.setdefault(norm_hersteller(hersteller), []).append(hersteller)
        for norm, schreibweisen in aehnlich.items():
            if len(schreibweisen) > 1 or not norm:
                betroffen = sorted(n for h in schreibweisen for n in exakt[h])
                if len(betroffen) < 2:
                    continue
                namen = " / ".join(f"„{h}“" if h else "(leer)" for h in schreibweisen)
                befunde.append(Befund("DQ-3", VERDACHT, betroffen, _invs(zeilen, betroffen), feld,
                                      f"Verdacht auf Dublette: Seriennummer {serie}, Hersteller {namen}"))
    return befunde
