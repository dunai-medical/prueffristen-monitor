"""Misst die Erkennungsrate gegen das Fehlerprotokoll der synthetischen Daten.

Grenze: Fehler und Prüfregeln stammen vom selben Autor. 100 % hier belegen nur, dass jede Regel
wie beschrieben greift – nicht, dass jeder reale Datenfehler gefunden wird.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path

from .auswertung import werte_aus
from .einlesen import lese_csv

DATEN = Path(__file__).resolve().parent.parent / "daten"
STICHTAG = date(2026, 11, 9)


def validiere(befunde, protokoll, datei):
    erwartet = [(int(r["zeile"]), r["regel"]) for r in protokoll if r["datei"] == datei]
    treffer, falsch_positiv = set(), []
    for b in befunde:
        if not b.regel.startswith("DQ-"):
            continue
        passend = {(z, r) for (z, r) in erwartet if r == b.regel and z in b.zeilen}
        if passend:
            treffer |= passend
        else:
            falsch_positiv.append(b)
    verpasst = [e for e in erwartet if e not in treffer]
    return {"erwartet": erwartet, "treffer": treffer, "verpasst": verpasst, "falsch_positiv": falsch_positiv}


def main():
    protokoll = lese_csv(DATEN / "fehlerprotokoll.csv")
    gesamt = Counter()
    for datei, regelsatz in [("geraete_de.csv", "DE"), ("geraete_ch.csv", "CH")]:
        a = werte_aus(DATEN / datei, regelsatz, STICHTAG)
        v = validiere(a.befunde, protokoll, datei)
        print(f"\n{datei} ({regelsatz}): {len(a.geraete)} Geräte")
        je_regel = Counter(r for _, r in v["erwartet"])
        gefunden = Counter(r for _, r in v["treffer"])
        fp = Counter(b.regel for b in v["falsch_positiv"])
        for regel in sorted(set(je_regel) | set(fp)):
            print(f"  {regel}: {gefunden[regel]}/{je_regel[regel]} gefunden, {fp[regel]} falsch positiv")
        for z, r in v["verpasst"]:
            print(f"  VERPASST: Zeile {z} {r}")
        for b in v["falsch_positiv"]:
            print(f"  FALSCH POSITIV: Zeilen {b.zeilen} {b.regel} – {b.text}")
        gesamt.update(erwartet=len(v["erwartet"]), treffer=len(v["treffer"]), fp=len(v["falsch_positiv"]))
    tr, er, fp = gesamt["treffer"], gesamt["erwartet"], gesamt["fp"]
    print(f"\nGesamt: {tr}/{er} eingebaute Fehler gefunden (Trefferquote {tr / er:.0%}), {fp} falsch positive Befunde")


if __name__ == "__main__":
    main()
