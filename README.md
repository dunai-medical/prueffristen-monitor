# Prüffristen-Monitor

Prüffristen und Datenqualität von Medizinprodukte-Beständen, nachvollziehbar bis zur Rechtsquelle:
**STK und MTK nach MPBetreibV (Deutschland)** und **Instandhaltung nach MepV/GPI (Schweiz)**,
mit PDF-Bericht und MCP-Server für Claude.

> **Demonstration mit synthetischen Daten. Kein Medizinprodukt, keine Rechtsberatung.**
> Das Werkzeug organisiert Prüftermine und Bestandsdaten. Es ersetzt weder die Festlegung durch die
> verantwortliche Fachperson noch die Prüfung durch Personen, die die Anforderungen nach § 5 MPBetreibV erfüllen.

## Warum

Ein Gerätebestand ist nur so gut wie seine Daten. Swissmedic hat 2024 bei Inspektionen in 23 Spitälern
festgestellt, dass Lebenszyklusprozesse wie Inventarisierung und Wartung unzureichend dokumentiert waren
([Jahresbericht Spitalinspektionen 2024](https://www.swissmedic.ch/swissmedic/de/home/medizinprodukte/uebersicht-medizinprodukte/jahresbericht-spitalinspektionen-2024.html)).
Dieses Projekt zeigt, wie man Fristen regelgenau berechnet **und** sichtbar macht, wo die Daten dafür nicht reichen.

## Was es kann

| Funktion | Grundlage |
|---|---|
| STK-Fristen: höchstens 24 Monate, bis Monatsende; kürzere Betreiberintervalle | § 12 Abs. 1 MPBetreibV |
| MTK-Fristen je Gerätetyp, ab Ablauf des Jahres; nach Eingriff sofort fällig | § 15 Abs. 5 und Anlage 2 MPBetreibV |
| CH: Fälligkeit nach Herstellerintervall; fehlendes Intervall wird gemeldet, nicht erfunden | Art. 71 MepV, GPI 7.1/7.2.1 |
| Pflichtangaben des Bestands prüfen | § 14 MPBetreibV (DE), GPI Kap. 8.1 (CH) |
| Dubletten (exakt/Verdacht), unmögliche und mehrdeutige Datumsangaben, unzulässige Intervalle | REGELN.md, DQ-1 bis DQ-9 |
| PDF-Bericht: Gesamturteil, Kennzahlen (u. a. Verzug), Handlungsliste, Datenqualität, Grenzen | angelehnt an GPI 3.6 (Tätigkeitsbericht) |
| MCP-Server: Claude fragt den Bestand ab; die Fristen berechnet der geprüfte Rechenkern, nicht das Sprachmodell | Model Context Protocol |

Jedes Ergebnis nennt seine **Regel-ID** (z. B. `DE-STK-2`), die in [REGELN.md](REGELN.md) mit Fundstelle,
Wortlaut und Rechenbeispiel steht.

## Ergebnisse

- **124 automatische Tests**, davon 28 Fristfälle, die vor dem Code von Hand aus dem Gesetzestext berechnet wurden ([TESTFAELLE.md](TESTFAELLE.md)).
- **Validierung** auf zwei synthetischen Beständen (305 Geräte DE, 204 Geräte CH) mit 53 protokollierten Fehlern:

  | Bestand | Fehler eingebaut | gefunden | falsch positiv |
  |---|---|---|---|
  | DE | 29 | 29 | 0 |
  | CH | 24 | 24 | 0 |

  Negativkontrolle (als Test hinterlegt): Wird eine Prüfregel abgeschaltet, meldet die Validierung die verpassten Fehler.
- **Unabhängige Gegenprüfung** durch einen separaten KI-Prüfagenten (Claude), der den Code nicht kannte:
  alle 569 Fristen der beiden Testbestände mit eigenem Code nachgerechnet – 0 Abweichungen; Paragrafen und
  Fristen gegen den Gesetzestext abgeglichen. Seine 8 Verbesserungsvorschläge (u. a. ein falsch zugeordneter
  Rechtsbegriff und ein Eingabefehler, der still als „nein“ gelesen wurde) sind umgesetzt und durch Tests abgesichert.
- **Praxistest mit Claude** über MCP: Frage „Welche Geräte auf der Intensivstation sind im Dezember fällig?“
  → korrektes Gerät; zusätzlich meldete Claude – wie im Server vorgegeben – vier Intensiv-Geräte, für die wegen
  Datenfehlern oder fehlender Festlegung keine Frist berechnet werden kann.

## Beispielberichte

[DE: Klinikum Musterstadt](beispiele/bericht_de_beispiel.pdf) · [CH: Spital Musterhausen](beispiele/bericht_ch_beispiel.pdf)
(fiktive Bestände, Stichtag 09.11.2026)

## Schnellstart

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt     # Intel-Mac: zusätzlich --only-binary=cryptography
python -m pytest -q                           # 124 passed
python -m prueffristen.validierung            # Erkennungsrate gegen das Fehlerprotokoll
python -m prueffristen.bericht daten/geraete_de.csv DE --stichtag 09.11.2026 --haus "Klinikum Musterstadt (fiktiv)"
```

Daten neu erzeugen (reproduzierbar, fester Startwert): `python daten/erzeuge_daten.py`

### MCP-Server in Claude Desktop (macOS)

Claude-App beenden, dann `python mcp_in_claude_eintragen.py` (legt vorher eine Sicherungskopie der
Konfiguration an), App neu starten. Werkzeuge: `liste_bestaende`, `uebersicht`, `fristen`, `geraet`,
`datenqualitaet`, `erstelle_pdf_bericht`. Zugriff nur auf die zwei hinterlegten Bestände; der Server läuft
lokal, die CSV-Dateien verlassen den Rechner nicht. Die Ergebnisse einer Abfrage – auch einzelne Datensätze wie
Inventarnummer, Gerät und Standort – gehen an das Sprachmodell. Deshalb: nur synthetische oder freigegebene Daten verwenden.

## Aufbau

```
REGELN.md              Regelwerk mit Fundstellen (zuerst lesen)
TESTFAELLE.md          von Hand berechnete Erwartungswerte
prueffristen/
  regeln.py            Rechenkern (Fristen, Status)
  einlesen.py          CSV (UTF-8 mit/ohne BOM), strenge Datumsprüfung
  datenqualitaet.py    DQ-1 bis DQ-9
  auswertung.py        Datei → Befunde + Fristen
  kennzahlen.py        Kennzahlen, Gesamturteil, Handlungsliste
  bericht.py           PDF-Bericht
  validierung.py       Erkennungsrate gegen Fehlerprotokoll
  werkzeuge.py         Abfragen für den MCP-Server
mcp_server.py          MCP-Server
daten/                 synthetische Bestände, Fehlerprotokoll, Generator (DATEN.md)
beispiele/             Beispielberichte (PDF)
tests/                 pytest
```

## Methodik und Grenzen

- **Quellen:** MPBetreibV vom 14.02.2025, zuletzt geändert durch V v. 31.10.2025 (Anlage 2 neu gefasst);
  MepV Art. 71; Swissmedic/IHS GPI Version 2.1 (gültig ab 30.01.2026). Regeln nur aus der verkündeten Fassung –
  der Verordnungsentwurf (BR-Drs. 251/24) weicht an zwei Stellen davon ab.
- **Annahmen** (in REGELN.md begründet): kürzere STK-Intervalle ebenfalls bis Monatsende (A1);
  CH-Fälligkeit = Datum + Kalendermonate (A2); CH-Bestand enthält nur elektrische Geräte (A3).
- **Offen gelassen:** STK-Pflicht für Produkte außerhalb von Anlage 1 (§ 12 Abs. 1 Satz 5) – die amtliche
  Begründung erläutert den Satz nicht; das Werkzeug weist solche Fälle als Festlegung des Betreibers aus.
- **Nicht abgedeckt:** Laien-AED (§ 12 Abs. 2), Therapiedosimeter (Anlage 2 Nr. 1.5), Versorgungsfälle nach
  § 3 Abs. 2–4 (z. B. § 15 Abs. 3), Prüfintervalle aus anderen Schweizer Erlassen (Messmittel, Strahlenschutz),
  Medizinproduktebuch, Einweisungen, Vigilanz.
- **Kennzahlen** zählen den Bestand, wie er geliefert wurde (Dubletten und defekte Geräte nicht herausgerechnet).
- **Fehlerhafte Daten** führen nie zu einer scheinbar gültigen Frist, sondern zum Status „Datenfehler“.
- **Validierung:** Fehler und Prüfregeln stammen vom selben Autor. 100 % belegen die korrekte Umsetzung der
  Regeln, nicht die Vollständigkeit bei realen Daten.

## Lizenz

Code: MIT (siehe `LICENSE`). Synthetische Daten: frei verwendbar unter CC0 1.0 – sie sind vollständig erfunden.

Autor: Aron Dunai-Kovács, B.Eng. Medizintechnik · [dunai-medical.github.io](https://dunai-medical.github.io/)
