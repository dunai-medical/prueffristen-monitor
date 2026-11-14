"""Rechenkern: setzt REGELN.md um. Jede Ausgabe nennt die Regel-ID.

Eingabe: ein Gerät als dict mit bereits geprüften Werten (datetime.date oder leer).
Das Einlesen und die Datenqualitätsprüfung (DQ-1 bis DQ-9) erledigt ein eigenes Modul.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

VORLAUF_TAGE = 90
STK_HOECHSTFRIST_MONATE = 24  # § 12 Abs. 1 Satz 2 MPBetreibV

# Anlage 2 MPBetreibV (Fassung V v. 31.10.2025): Nachprüffristen in Jahren
MTK_FRISTEN_JAHRE = {"1.1": 1, "1.2.1": 2, "1.2.2": 2, "1.2.3": 1, "1.3": 2, "1.4": 2, "1.6": 5, "1.7": 2}
MTK_NICHT_ABGEDECKT = {"1.5.1", "1.5.2", "1.5.3"}  # Therapiedosimeter: Sonderregeln Anlage 2 Nr. 1.5, 2, 3.2
# Gültige Nummern der geltenden Fassung (für DQ-7)
ANLAGE1_NUMMERN = {"1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "2", "3"}
ANLAGE2_NUMMERN = set(MTK_FRISTEN_JAHRE) | MTK_NICHT_ABGEDECKT
STK_NICHT_ABGEDECKT = {"aed_laien"}      # § 12 Abs. 2

IN_ORDNUNG = "in Ordnung"
BALD_FAELLIG = "bald fällig"
UEBERFAELLIG = "überfällig"
SOFORT_FAELLIG = "sofort fällig"
FESTLEGUNG_FEHLT = "Festlegung fehlt"
NICHT_ABGEDECKT = "nicht abgedeckt"
DATENFEHLER = "Datenfehler"


@dataclass
class Ergebnis:
    art: str                      # "STK", "MTK" oder "Instandhaltung"
    status: str
    regel_id: str
    faellig_am: Optional[date] = None
    tage: Optional[int] = None    # fällig_am − Stichtag
    hinweise: List[str] = field(default_factory=list)


# ---------- Datumsrechnung ----------
def _monat_plus(d: date, monate: int):
    m = d.month - 1 + monate
    return d.year + m // 12, m % 12 + 1


def plus_monate(d: date, monate: int) -> date:
    """Kalendermonate addieren; fehlt der Tag im Zielmonat, gilt dessen letzter Tag (CH-3, Annahme A2)."""
    j, m = _monat_plus(d, monate)
    return date(j, m, min(d.day, calendar.monthrange(j, m)[1]))


def stk_faellig(bezug: date, monate: int = STK_HOECHSTFRIST_MONATE) -> date:
    """DE-STK-2/3: mit Ablauf des Monats (Annahme A1 auch für kürzere Intervalle)."""
    j, m = _monat_plus(bezug, monate)
    return date(j, m, calendar.monthrange(j, m)[1])


def mtk_faellig(bezug: date, jahre: int) -> date:
    """DE-MTK-2: Frist beginnt mit Ablauf des Jahres → endet am 31.12."""
    return date(bezug.year + jahre, 12, 31)


def einstufen(faellig: date, stichtag: date, vorlauf_tage: int = VORLAUF_TAGE):
    """Fälligkeitstag selbst zählt noch als 'bald fällig' ('spätestens')."""
    tage = (faellig - stichtag).days
    if tage < 0:
        return tage, UEBERFAELLIG
    if tage <= vorlauf_tage:
        return tage, BALD_FAELLIG
    return tage, IN_ORDNUNG


# ---------- Hilfen ----------
def _leer(wert) -> bool:
    return wert is None or (isinstance(wert, str) and wert.strip() == "")


UNGUELTIG = -1


def _ganzzahl(wert) -> Optional[int]:
    """None = keine Angabe; UNGUELTIG (-1) = Angabe vorhanden, aber keine ganze Zahl."""
    if _leer(wert):
        return None
    try:
        return int(str(wert).strip())
    except ValueError:
        return UNGUELTIG


def _erstes(*werte):
    """Erster nicht leerer Wert (Leerzeichen zählen als leer)."""
    for w in werte:
        if not _leer(w):
            return w
    return None


def _wahr(wert) -> bool:
    """Nur True oder „ja“ zählt als ja; andere Werte meldet die Datenqualitätsprüfung (DQ-10)."""
    return wert is True or (isinstance(wert, str) and wert.strip().casefold() == "ja")


def _mit_frist(art, regel, faellig, stichtag, vorlauf, hinweise):
    tage, status = einstufen(faellig, stichtag, vorlauf)
    return Ergebnis(art, status, regel, faellig, tage, hinweise)


# ---------- Deutschland ----------
def _stk(g: dict, stichtag: date, vorlauf: int) -> Optional[Ergebnis]:
    if g.get("kategorie") in STK_NICHT_ABGEDECKT:
        return Ergebnis("STK", NICHT_ABGEDECKT, "DE-STK-5",
                        hinweise=["Laien-AED: Ausnahme nach § 12 Abs. 2 – Einzelfall prüfen"])
    anlage1 = not _leer(g.get("anlage1_nr"))
    intervall = _ganzzahl(g.get("stk_intervall_monate"))
    hinweise: List[str] = []

    if anlage1:
        regel = "DE-STK-2"
    elif intervall is not None:
        regel = "DE-STK-4"
        hinweise.append("Kein Anlage-1-Produkt: Frist aus Festlegung des Betreibers (§ 12 Abs. 1 Satz 5, Auslegung offen)")
    elif _wahr(g.get("aktiv")):
        return Ergebnis("STK", FESTLEGUNG_FEHLT, "DE-STK-4",
                        hinweise=["STK-Bedarf durch Fachperson festlegen (§ 12 Abs. 1 Satz 5, Auslegung offen)"])
    else:
        return None

    monate = STK_HOECHSTFRIST_MONATE
    if intervall is not None:
        if intervall < 1:
            return Ergebnis("STK", DATENFEHLER, "DQ-6",
                            hinweise=hinweise + ["DQ-6: STK-Intervall ungültig (erlaubt 1–24 Monate)"])
        if intervall > STK_HOECHSTFRIST_MONATE:
            if not anlage1:
                return Ergebnis("STK", DATENFEHLER, "DQ-6", hinweise=hinweise + [
                    f"DQ-6: Festgelegtes STK-Intervall {intervall} Monate über 24 – Festlegung durch Fachperson klären"])
            hinweise.append(f"DQ-6: STK-Intervall {intervall} Monate über der Höchstfrist – "
                            "gerechnet mit 24 Monaten (§ 12 Abs. 1 Satz 2)")
        else:
            monate = intervall
            if anlage1 and intervall < STK_HOECHSTFRIST_MONATE:
                regel = "DE-STK-3"

    bezug = _erstes(g.get("letzte_stk"), g.get("inbetriebnahme"))
    if _leer(bezug):
        return Ergebnis("STK", DATENFEHLER, "DQ-9", hinweise=hinweise + ["DQ-9: weder letzte STK noch Inbetriebnahme"])
    return _mit_frist("STK", regel, stk_faellig(bezug, monate), stichtag, vorlauf, hinweise)


def _mtk(g: dict, stichtag: date, vorlauf: int) -> Optional[Ergebnis]:
    nr = g.get("anlage2_nr")
    if _leer(nr):
        return None
    nr = str(nr).strip()
    if nr in MTK_NICHT_ABGEDECKT:
        return Ergebnis("MTK", NICHT_ABGEDECKT, "DE-MTK-4",
                        hinweise=["Therapiedosimeter: Sonderregeln Anlage 2 – Einzelfall prüfen"])
    if nr not in MTK_FRISTEN_JAHRE:
        return Ergebnis("MTK", DATENFEHLER, "DE-MTK-1", hinweise=[f"Unbekannte Anlage-2-Nummer: {nr}"])
    if _wahr(g.get("eingriff_seit_letzter_mtk")):
        return Ergebnis("MTK", SOFORT_FAELLIG, "DE-MTK-3",
                        hinweise=["Eingriff seit letzter MTK: unverzüglich prüfen (§ 15 Abs. 5 Satz 4 Nr. 2)"])
    bezug = _erstes(g.get("letzte_mtk"), g.get("inbetriebnahme"))
    if _leer(bezug):
        return Ergebnis("MTK", DATENFEHLER, "DQ-9", hinweise=["DQ-9: weder letzte MTK noch Inbetriebnahme"])
    return _mit_frist("MTK", "DE-MTK-2", mtk_faellig(bezug, MTK_FRISTEN_JAHRE[nr]), stichtag, vorlauf, [])


# ---------- Schweiz ----------
def _ch(g: dict, stichtag: date, vorlauf: int) -> Ergebnis:
    monate = _ganzzahl(g.get("intervall_monate"))
    if monate is None:
        return Ergebnis("Instandhaltung", FESTLEGUNG_FEHLT, "CH-2",
                        hinweise=["Herstellerintervall fehlt – Festlegung durch Fachperson (GPI 7.2.1)"])
    if monate < 1:
        return Ergebnis("Instandhaltung", DATENFEHLER, "CH-1", hinweise=["Intervall ungültig (ganze Zahl ab 1 Monat)"])
    bezug = _erstes(g.get("letzte_instandhaltung"), g.get("inbetriebnahme"))
    if _leer(bezug):
        return Ergebnis("Instandhaltung", DATENFEHLER, "DQ-9",
                        hinweise=["DQ-9: weder letzte Instandhaltung noch Inbetriebnahme"])
    return _mit_frist("Instandhaltung", "CH-3", plus_monate(bezug, monate), stichtag, vorlauf, [])


def bewerte(g: dict, stichtag: date, regelsatz: str = "DE", vorlauf_tage: int = VORLAUF_TAGE) -> List[Ergebnis]:
    """Alle Fristen eines Geräts. Stichtag ist Pflicht – nie automatisch 'heute'."""
    if regelsatz == "DE":
        return [e for e in (_stk(g, stichtag, vorlauf_tage), _mtk(g, stichtag, vorlauf_tage)) if e is not None]
    if regelsatz == "CH":
        return [_ch(g, stichtag, vorlauf_tage)]
    raise ValueError(f"Unbekannter Regelsatz: {regelsatz!r} (erlaubt: 'DE', 'CH')")
