"""Verbindet Einlesen, Datenqualität und Fristberechnung für eine ganze Datei."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Tuple

from .datenqualitaet import Befund, pruefe
from .einlesen import lese_csv
from .regeln import DATENFEHLER, VORLAUF_TAGE, Ergebnis, bewerte

# Felder, aus denen die jeweilige Frist berechnet wird
FELDER_JE_ART = {"STK": {"letzte_stk", "inbetriebnahme", "stk_intervall_monate", "anlage1_nr"},
                 "MTK": {"letzte_mtk", "inbetriebnahme", "anlage2_nr", "eingriff_seit_letzter_mtk"},
                 "Instandhaltung": {"letzte_instandhaltung", "inbetriebnahme", "intervall_monate"}}


@dataclass
class Auswertung:
    regelsatz: str
    stichtag: date
    geraete: List[dict]
    befunde: List[Befund]
    fristen: List[Tuple[dict, Ergebnis]]


def werte_aus(pfad, regelsatz: str, stichtag: date, vorlauf_tage: int = VORLAUF_TAGE) -> Auswertung:
    geraete, befunde = pruefe(lese_csv(pfad), regelsatz, stichtag)
    fristen = []
    for g in geraete:
        ergebnisse = bewerte(g, stichtag, regelsatz, vorlauf_tage)
        if (regelsatz == "DE" and "aktiv" in g["_ungueltig"] and not (g.get("anlage1_nr") or "").strip()
                and not any(e.art == "STK" for e in ergebnisse)):
            ergebnisse.append(Ergebnis("STK", DATENFEHLER, "DQ-10",
                                       hinweise=["Angabe „aktiv“ ungültig – STK-Bedarf nicht bestimmbar"]))
        for e in ergebnisse:
            betroffen = g["_ungueltig"] & FELDER_JE_ART[e.art]
            if betroffen and e.faellig_am is not None:
                # Nie aus einem fehlerhaften Datum eine scheinbar gültige Frist ableiten
                e = Ergebnis(e.art, DATENFEHLER, "DQ-4/5", hinweise=[
                    f"Frist nicht berechenbar: fehlerhafte Angabe in {', '.join(sorted(betroffen))}"])
            fristen.append((g, e))
    return Auswertung(regelsatz, stichtag, geraete, befunde, fristen)
