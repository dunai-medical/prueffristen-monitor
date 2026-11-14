"""Kennzahlen und Gesamturteil (angelehnt an GPI Kap. 3.6, Tätigkeitsbericht)."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from statistics import median
from typing import Dict, List, Optional

from .auswertung import Auswertung
from .datenqualitaet import FEHLER, VERDACHT
from .regeln import (BALD_FAELLIG, DATENFEHLER, FESTLEGUNG_FEHLT, NICHT_ABGEDECKT, SOFORT_FAELLIG,
                     UEBERFAELLIG)

KEINE = "Keine Auffälligkeiten"
BEOBACHTEN = "Beobachten"
HANDLUNGSBEDARF = "Handlungsbedarf"


@dataclass
class Kennzahlen:
    geraete: int
    geraetestatus: Dict[str, int]
    altersstruktur: Dict[str, int]
    fristen: Dict[str, Dict[str, int]]          # Art -> Status -> Anzahl
    ueberfaellig: int
    verzug_median_tage: Optional[float]
    verzug_max_tage: Optional[int]
    sofort_faellig: int
    bald_faellig: int
    festlegung_fehlt: int
    nicht_abgedeckt: int
    frist_datenfehler: int
    dq_fehler: int
    dq_verdacht: int
    dq_je_regel: Dict[str, int]
    urteil: str = ""
    urteil_text: List[str] = field(default_factory=list)
    regelsatz: str = "DE"
    zustaendigkeit: Dict[str, int] = field(default_factory=dict)


def _alter(g, stichtag) -> str:
    ibn = g.get("inbetriebnahme")
    if not ibn:
        return "unbekannt"
    jahre = (stichtag - ibn).days / 365.25
    return "unter 5 Jahre" if jahre < 5 else "5 bis 10 Jahre" if jahre < 10 else "über 10 Jahre"


def berechne(a: Auswertung) -> Kennzahlen:
    fristen: Dict[str, Counter] = {}
    for _, e in a.fristen:
        fristen.setdefault(e.art, Counter())[e.status] += 1
    status = Counter(e.status for _, e in a.fristen)
    verzug = [-e.tage for _, e in a.fristen if e.status == UEBERFAELLIG]
    alter = Counter(_alter(g, a.stichtag) for g in a.geraete)
    reihenfolge = ["unter 5 Jahre", "5 bis 10 Jahre", "über 10 Jahre", "unbekannt"]
    k = Kennzahlen(
        geraete=len(a.geraete),
        geraetestatus=dict(Counter((g.get("status") or "ohne Angabe") for g in a.geraete).most_common()),
        altersstruktur={r: alter[r] for r in reihenfolge if alter[r]},
        fristen={art: dict(c) for art, c in fristen.items()},
        ueberfaellig=len(verzug),
        verzug_median_tage=median(verzug) if verzug else None,
        verzug_max_tage=max(verzug) if verzug else None,
        sofort_faellig=status[SOFORT_FAELLIG], bald_faellig=status[BALD_FAELLIG],
        festlegung_fehlt=status[FESTLEGUNG_FEHLT], nicht_abgedeckt=status[NICHT_ABGEDECKT],
        frist_datenfehler=status[DATENFEHLER],
        dq_fehler=sum(b.schwere == FEHLER for b in a.befunde),
        dq_verdacht=sum(b.schwere == VERDACHT for b in a.befunde),
        dq_je_regel=dict(sorted(Counter(b.regel for b in a.befunde).items())),
        regelsatz=a.regelsatz,
        zustaendigkeit=dict(Counter(g.get("zustaendig") or "ohne Angabe" for g in a.geraete).most_common())
        if a.regelsatz == "CH" else {},
    )
    k.urteil, k.urteil_text = urteil(k)
    return k


def handlungsliste(a: Auswertung) -> Dict[str, list]:
    """Alle Fristen außer 'in Ordnung', in drei Gruppen. Vollständigkeit ist per Test abgesichert."""
    def tage(ge):
        return ge[1].tage if ge[1].tage is not None else 0
    return {
        "dringend": sorted([ge for ge in a.fristen if ge[1].status in (SOFORT_FAELLIG, UEBERFAELLIG)],
                           key=lambda ge: (ge[1].status != SOFORT_FAELLIG, tage(ge))),
        "bald": sorted([ge for ge in a.fristen if ge[1].status == BALD_FAELLIG], key=tage),
        "ohne_frist": sorted([ge for ge in a.fristen if ge[1].status in (DATENFEHLER, FESTLEGUNG_FEHLT, NICHT_ABGEDECKT)],
                             key=lambda ge: ([DATENFEHLER, FESTLEGUNG_FEHLT, NICHT_ABGEDECKT].index(ge[1].status),
                                             ge[0]["_zeile"])),
    }


def _n(zahl, einzahl, mehrzahl):
    return f"{zahl} {einzahl if zahl == 1 else mehrzahl}"


def urteil(k: Kennzahlen):
    handeln, beobachten = [], []
    massnahme = ("Instandhaltung", "Instandhaltungen") if k.regelsatz == "CH" else ("Prüfung", "Prüfungen")
    if k.sofort_faellig:
        handeln.append(_n(k.sofort_faellig, "Prüfung", "Prüfungen") + " sofort fällig (Eingriff seit letzter MTK)")
    if k.ueberfaellig:
        handeln.append(_n(k.ueberfaellig, *massnahme) + f" überfällig (Verzug bis {k.verzug_max_tage} Tage)")
    if k.dq_fehler:
        handeln.append(_n(k.dq_fehler, "Datenqualitäts-Befund", "Datenqualitäts-Befunde") + " der Schwere „Fehler“")
    if k.frist_datenfehler:
        handeln.append(_n(k.frist_datenfehler, "Frist", "Fristen") + " wegen fehlerhafter Daten nicht berechenbar")
    if k.bald_faellig:
        beobachten.append(_n(k.bald_faellig, *massnahme) + " in den nächsten 90 Tagen fällig")
    if k.festlegung_fehlt:
        beobachten.append(_n(k.festlegung_fehlt, "Gerät", "Geräte") + " ohne festgelegtes Intervall (Festlegung durch Fachperson)")
    if k.dq_verdacht:
        beobachten.append(_n(k.dq_verdacht, "Verdachtsfall", "Verdachtsfälle") + " auf Dubletten prüfen")
    if k.nicht_abgedeckt:
        beobachten.append(_n(k.nicht_abgedeckt, "Sonderfall", "Sonderfälle") + " außerhalb des Werkzeugs (Einzelfall prüfen)")
    if handeln:
        return HANDLUNGSBEDARF, handeln + beobachten
    if beobachten:
        return BEOBACHTEN, beobachten
    return KEINE, ["Keine überfälligen Prüfungen, keine Datenfehler."]
