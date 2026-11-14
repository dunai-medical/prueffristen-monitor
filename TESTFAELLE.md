# TESTFAELLE.md – von Hand berechnet, vor dem Code

Stichtag, wenn nicht anders angegeben: **09.11.2026**. Vorlauf „bald fällig“: **90 Tage**.
Regel: tage = fällig_am − Stichtag. tage < 0 → überfällig · 0 ≤ tage ≤ 90 → bald fällig · tage > 90 → in Ordnung.
Erwartete Werte stammen aus REGELN.md und wurden unabhängig vom späteren Code berechnet.
Fälle mit (A) wurden zusätzlich als Übungsaufgabe ohne Vorlage gerechnet und mit der Tabelle verglichen.

## DE – Sicherheitstechnische Kontrolle (STK)
| Nr | Regel | Eingabe | fällig am | Tage | Status |
|---|---|---|---|---|---|
| T01 | DE-STK-2 | Inbetriebnahme 15.03.2025, keine STK | 31.03.2027 | 142 | in Ordnung |
| T02 | DE-STK-2 | letzte STK 02.11.2024 | 30.11.2026 | 21 | bald fällig |
| T03 | DE-STK-2 | letzte STK 31.01.2024 | 31.01.2026 | −282 | überfällig |
| T04 (A) | DE-STK-2 | letzte STK 17.08.2025 | 31.08.2027 | 295 | in Ordnung |
| T05 (A) | DE-STK-2 | Inbetriebnahme 29.02.2024, keine STK | 28.02.2026 | −254 | überfällig |
| T06 (A) | DE-STK-2 | Beatmungsgerät, letzte STK 14.12.2024 | 31.12.2026 | 52 | bald fällig |
| T07 | Grenze | wie T02, Stichtag 30.11.2026 | 30.11.2026 | 0 | bald fällig |
| T08 | Grenze | wie T02, Stichtag 01.12.2026 | 30.11.2026 | −1 | überfällig |
| T09 | Vorlauf | wie T01, Stichtag 31.12.2026 | 31.03.2027 | 90 | bald fällig |
| T10 | Vorlauf | wie T01, Stichtag 30.12.2026 | 31.03.2027 | 91 | in Ordnung |
| T11 | DE-STK-3 | Intervall 12 Monate, letzte STK 10.05.2026 | 31.05.2027 | 203 | in Ordnung |
| T12 | DQ-6 | Intervall 30 Monate, letzte STK 02.11.2024 | 30.11.2026 (24 Mon.) | 21 | bald fällig + Hinweis DQ-6 |
| T13 | DE-STK-4 | kein Anlage-1-Gerät, kein Intervall | – | – | Festlegung fehlt |
| T14 | DE-STK-4 | kein Anlage-1-Gerät, Intervall 12, letzte STK 10.05.2026 | 31.05.2027 | 203 | in Ordnung + Hinweis Betreiberfestlegung |
| T15 | DE-STK-5 | Laien-AED | – | – | nicht abgedeckt |
| T16 | Daten | Anlage-1-Gerät ohne Inbetriebnahme und ohne STK | – | – | Datenfehler |

## DE – Messtechnische Kontrolle (MTK)
| Nr | Regel | Eingabe | fällig am | Tage | Status |
|---|---|---|---|---|---|
| T17 | DE-MTK-2 | IR-Thermometer (1.2.3), MTK 20.12.2025 | 31.12.2026 | 52 | bald fällig |
| T18 | DE-MTK-2 | IR-Thermometer, MTK 02.01.2025 | 31.12.2026 | 52 | bald fällig |
| T19 (A) | DE-MTK-2 | IR-Thermometer, MTK 05.03.2025 | 31.12.2026 | 52 | bald fällig |
| T20 | DE-MTK-2 | NIBP (1.3), MTK 15.03.2025 | 31.12.2027 | 417 | in Ordnung |
| T21 (A) | DE-MTK-2 | Audiometer (1.1), MTK 30.06.2026 | 31.12.2027 | 417 | in Ordnung |
| T22 | DE-MTK-2 | Diagnostikdosimeter (1.6), MTK 01.07.2022 | 31.12.2027 | 417 | in Ordnung |
| T23 (A) | DE-MTK-3 | NIBP, MTK 10.10.2025, Eingriff seit letzter MTK | – | – | sofort fällig |
| T24 | DE-MTK-4 | Therapiedosimeter (1.5.1) | – | – | nicht abgedeckt |

## CH – Instandhaltung nach Herstellerintervall
| Nr | Regel | Eingabe | fällig am | Tage | Status |
|---|---|---|---|---|---|
| T25 | CH-3 | 12 Monate, letzte Instandhaltung 15.03.2026 | 15.03.2027 | 126 | in Ordnung |
| T26 | CH-3 | 1 Monat, letzte 31.01.2026 | 28.02.2026 | −254 | überfällig |
| T27 | CH-3 | 12 Monate, letzte 29.02.2024 (Schaltjahr) | 28.02.2025 | −619 | überfällig |
| T28 | CH-2 | kein Intervall | – | – | Festlegung fehlt |
