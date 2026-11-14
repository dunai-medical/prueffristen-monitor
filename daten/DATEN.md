# DATEN.md – synthetische Gerätebestände

**Alle Daten sind erfunden.** Häuser, Hersteller, Anschriften, Modelle und Seriennummern
existieren nicht. Risikoklassen und Intervalle sind plausible Beispielwerte, keine Klassifizierungsauskunft.
Keine Patientendaten, keine Firmendaten.

| Datei | Inhalt | Zeilen |
|---|---|---|
| geraete_de.csv | fiktives „Klinikum Musterstadt“, Spalten nach § 14 MPBetreibV plus Prüfdaten | 305 |
| geraete_ch.csv | fiktives „Spital Musterhausen“, Spalten nach GPI Kap. 8.1 | 204 |
| fehlerprotokoll.csv | jeder absichtlich eingebaute Fehler: Datei, Zeile, Inventarnr., Regel-ID | 53 |

Format: CSV, Trennzeichen `;`, UTF-8 mit BOM (damit Excel am Mac Umlaute richtig zeigt), Datumsangaben TT.MM.JJJJ.
Dateien in Excel nur ansehen, **nicht speichern** (Excel ändert sonst Kodierung und Datumsformate). Stichtag der Erzeugung: 09.11.2026.

## Erzeugung
`python3 erzeuge_daten.py` (nur Standardbibliothek). Fester Startwert `SEED = 20261109`:
Jeder Lauf erzeugt bitgleiche Dateien (geprüft per Prüfsumme).

## Eingebaute Fehler (Grundwahrheit für die Validierung)
| Regel | DE | CH | Art |
|---|---|---|---|
| DQ-1 | 10 | – | fehlende Pflichtangabe nach § 14 (Seriennr., Herstelleranschrift, Standort) |
| DQ-2 | – | 11 | fehlende Pflichtangabe nach GPI 8.1 (UDI/Seriennr., Risikoklasse, Lieferant, Schutzklasse, Inventarnr.) |
| DQ-3 | 5 | 4 | Dubletten: je 3/2 exakt, je 2 Schreibvarianten („Verdacht“) |
| DQ-4 | 8 | 5 | unmögliches Datum, Zukunft, Prüfung vor Inbetriebnahme, Anschaffung nach Inbetriebnahme |
| DQ-5 | 2 | 1 | mehrdeutiges Format (03/04/…) |
| DQ-6 | 2 | – | STK-Intervall 36 Monate |
| DQ-8 | – | 3 | nächste Instandhaltung passt nicht zu letzter + Intervall |
| DQ-9 | 2 | – | Anlage-1-Gerät ohne Inbetriebnahme und ohne STK |

Regeln für die Auswertung:
- Jede fehlerhafte Zeile hat **genau einen** eingebauten Fehler (geprüft).
- Bei Dubletten ist die **Kopie** protokolliert. Ein Fund, der das Paar Original/Kopie nennt, zählt als ein Treffer.
- Bei 8 % der CH-Geräte fehlt das Herstellerintervall absichtlich. Das ist **kein Datenfehler**,
  sondern der legitime Zustand „Festlegung fehlt“ (CH-2). Ebenso Geräte mit Eingriff seit letzter MTK (DE-MTK-3) und Laien-AED (DE-STK-5).
- Im DE-Bestand hat ein Großteil der Geräte außerhalb von Anlage 1 eine vom Betreiber festgelegte STK (24 Monate),
  bewusst breit gewählt, um Regel DE-STK-4 zu testen. Für batteriebetriebene Kleingeräte (z. B. Thermometer)
  wäre das in der Praxis unüblich.
- Normale Fälligkeiten (überfällig/bald fällig) sind kein Datenfehler und stehen nicht im Protokoll.
