# REGELN.md – Regelwerk des Prüffristen-Monitors

Stand: 11.11.2026 · Autor: Aron Dunai-Kovács

> Demonstration. Keine Rechtsberatung. Ersetzt keine Festlegung durch die verantwortliche
> Fachperson und keine Prüfung durch Personen, die die Anforderungen nach § 5 MPBetreibV erfüllen. Kein Medizinprodukt:
> Das Werkzeug organisiert Prüftermine und Bestandsdaten, es dient weder Diagnose noch Therapie.

Jede Regel hat eine ID. Code und Tests verweisen auf diese IDs. Ändert sich eine Quelle,
wird zuerst diese Datei geändert, dann Tests, dann Code.

---

## 1. Quellen (nur amtliche bzw. behördliche Fassungen)

| Kürzel | Quelle | Fassung | Abgerufen |
|---|---|---|---|
| MPBetreibV | Medizinprodukte-Betreiberverordnung vom 14.02.2025 (BGBl. 2025 I Nr. 38), zuletzt geändert durch Art. 1 V v. 31.10.2025 (BGBl. 2025 I Nr. 263), gesetze-im-internet.de/mpbetreibv_2025 | gilt ab 20.02.2025 | 09.11.2026 |
| Anlage 1 / 2 | Anlagen der MPBetreibV; Anlage 2 neu gefasst durch V v. 31.10.2025 | wie oben | 09.11.2026 |
| BR-Drs. 251/24 | Entwurf mit Begründung (Bundesrat, 23.05.2024) – nur zur Auslegung, **nicht** als Regeltext | Entwurf | 09.11.2026 |
| MepV | Medizinprodukteverordnung (CH, SR 812.213), Art. 71 | Wortlaut nach droit-bilingue.ch (nicht amtliche Wiedergabe); Abs. 1 und 2 inhaltsgleich in der Swissmedic-Leitlinie GPI (Kap. 4.1.2, 4.2.2, 7.1) wiedergegeben | 09.11.2026 |
| GPI | Swissmedic/IHS: Schweizerische Gute Praxis für die Instandhaltung von Medizinprodukten, Version 2.1, gültig ab 30.01.2026 | 2.1 | 09.11.2026 |

**Lehre aus der Recherche:** Der Entwurf (BR-Drs. 251/24) weicht vom geltenden Text ab.
Im Entwurf hieß es bei der STK nur „alle zwei Jahre“, und § 14 hatte eine Nr. 5 (STK-Frist im
Bestandsverzeichnis). Beides steht so **nicht** in der geltenden Fassung. Regeln werden
deshalb nur aus der verkündeten Fassung abgeleitet.

---

## 2. Deutschland (Regelsatz `DE`)

### DE-STK-1 · Pflicht
- **Fundstelle:** § 12 Abs. 1 Satz 1 MPBetreibV i. V. m. Anlage 1
- **Inhalt:** Für Produkte nach Anlage 1 sind sicherheitstechnische Kontrollen (STK) durchzuführen.
- **Umsetzung:** Gerät hat Feld `anlage1_nr` (z. B. `1.1`, `1.5`, `2`). Ist es gesetzt → STK-pflichtig.

### DE-STK-2 · Höchstfrist 24 Monate, Monatsende
- **Fundstelle:** § 12 Abs. 1 Satz 2
- **Wortlaut (Kern):** „spätestens alle zwei Jahre mit Ablauf des Monats …, in dem die Inbetriebnahme
  des Produktes erfolgte oder die letzte sicherheitstechnische Kontrolle durchgeführt wurde.“
- **Umsetzung:** `faellig = letzter Tag des Monats(Bezugsdatum + 24 Monate)`.
  Bezugsdatum = letzte STK, sonst Inbetriebnahme.
- **Beispiele (Stichtag 09.11.2026):**
  | Bezugsdatum | fällig spätestens | Tage bis fällig |
  |---|---|---|
  | Inbetriebnahme 15.03.2025, keine STK | 31.03.2027 | 142 |
  | letzte STK 02.11.2024 | 30.11.2026 | 21 |
  | letzte STK 31.01.2024 | 31.01.2026 | −282 (überfällig) |

### DE-STK-3 · Kürzeres Intervall
- **Fundstelle:** § 12 Abs. 1 Satz 3; Begründung BR-Drs. 251/24 zu § 12 Abs. 1
- **Inhalt:** Ist früher mit Mängeln zu rechnen, muss der Betreiber rechtzeitig vor Ablauf der zwei Jahre prüfen.
- **Umsetzung:** Optionales Feld `stk_intervall_monate` (vom Betreiber festgelegt, z. B. nach
  Herstellerangabe, vgl. § 7 Abs. 2 Satz 2). Gültig: ganze Zahl 1–24.
  Anlage-1-Gerät mit Wert > 24 → es gilt die Höchstfrist 24 (Hinweis DQ-6). Wert < 1 oder keine Zahl → Datenfehler.
- **Annahme A1:** Auch beim kürzeren Intervall wird auf Monatsende gerechnet. Begründung: Die
  Prüfplakette nennt „Jahr und Monat der nächsten sicherheitstechnischen Kontrolle“ (§ 12 Abs. 3 Nr. 2).
- **Beispiel:** Intervall 12 Monate, letzte STK 10.05.2026 → fällig 31.05.2027.

### DE-STK-4 · Andere Produkte (offene Auslegung)
- **Fundstelle:** § 12 Abs. 1 Satz 5: „Für andere Produkte sowie mit Produkten nach Anlage 1
  verbundene Gegenstände gelten die Sätze 1 bis 3 entsprechend.“
- **Problem:** Die amtliche Begründung (BR-Drs. 251/24) erläutert diesen Satz nicht. Ob daraus
  eine STK-Pflicht für alle aktiven Geräte folgt, entscheidet das Werkzeug **nicht**.
- **Umsetzung:** Gerät ohne `anlage1_nr`, aber mit `stk_intervall_monate` → Frist wird nach DE-STK-2/3
  berechnet und als „Festlegung des Betreibers“ markiert. Ohne Intervall → Hinweis
  „STK-Bedarf durch Fachperson festlegen (§ 12 Abs. 1 Satz 5, Auslegung offen)“.
  Festgelegtes Intervall > 24 Monate → Datenfehler (Festlegung klären), keine angenommene Frist.
- **Einordnung:** Die Vorgängerfassung (§ 11 Abs. 1 MPBetreibV 2017) bezog die Pflicht auf Zubehör, das der Betreiber
  mit Anlage-1-Produkten verbunden verwendet. Das spricht eher für eine enge Auslegung. In der Praxis legen Betreiber
  für weitere aktive Geräte oft Wiederholungsprüfungen fest (vgl. DIN EN 62353); das ist eine Betreiberentscheidung.

### DE-STK-5 · Ausnahme Laien-AED – nicht abgedeckt
- **Fundstelle:** § 12 Abs. 2
- **Umsetzung:** Kategorie `aed_laien` → Ausgabe „nicht abgedeckt, Einzelfall prüfen“. Keine Frist.

### DE-MTK-1 · Pflicht und Fristen
- **Fundstelle:** § 15 Abs. 1 und 5 i. V. m. Anlage 2 (Fassung V v. 31.10.2025)
- **Fristentabelle (im Code alle Nummern außer 1.5, siehe DE-MTK-4):**
  | Anlage 2 Nr. | Produkt | Jahre |
  |---|---|---|
  | 1.1 | Ton- und Sprachaudiometer | 1 |
  | 1.2.1 | medizinische Elektrothermometer | 2 |
  | 1.2.2 | mit austauschbaren Temperaturfühlern | 2 |
  | 1.2.3 | Infrarot-Strahlungsthermometer | 1 |
  | 1.3 | nichtinvasive Blutdruckmessung | 2 |
  | 1.4 | Augentonometer | 2 |
  | 1.6 | Diagnostikdosimeter | 5 |
  | 1.7 | Tretkurbelergometer | 2 |

### DE-MTK-2 · Jahresende
- **Fundstelle:** § 15 Abs. 5 Satz 3: „Die Fristen beginnen mit Ablauf des Jahres, in dem das
  Produkt in Betrieb genommen oder die letzten messtechnischen Kontrollen durchgeführt wurden.“
- **Umsetzung:** `faellig = 31.12.(Jahr des Bezugsdatums + Frist)`.
- **Beispiele (Stichtag 09.11.2026):**
  | Gerät | Bezugsdatum | fällig spätestens |
  |---|---|---|
  | IR-Thermometer (1 J.) | 20.12.2025 | 31.12.2026 |
  | IR-Thermometer (1 J.) | 02.01.2025 | 31.12.2026 ← gleiches Ergebnis! |
  | NIBP (2 J.) | 15.03.2025 | 31.12.2027 |
  Das zweite Beispiel ist Absicht: Durch den Fristbeginn zum Jahresende liegen hier fast zwei Jahre zwischen Prüfung und Fälligkeit.

### DE-MTK-3 · Sofort fällig
- **Fundstelle:** § 15 Abs. 5 Satz 4
- **Inhalt:** Unverzüglich bei Anzeichen auf Überschreitung der Fehlergrenzen oder nach einem
  Eingriff, der die messtechnischen Eigenschaften beeinflusst haben könnte.
- **Umsetzung:** Feld `eingriff_seit_letzter_mtk = ja` → Status „sofort fällig“, unabhängig vom Datum.
  Zulässig sind nur „ja“/„nein“; jeder andere Wert ist ein Datenfehler (DQ-10), nie stilles „nein“.

### DE-MTK-4 · Sonderfälle – nicht abgedeckt
- Therapiedosimeter (Anlage 2 Nr. 1.5 mit Ausnahme nach Nr. 2 und Vergleichsmessungen nach Nr. 3.2).
  **Umsetzung:** Anlage-2-Nummern 1.5.1–1.5.3 → „nicht abgedeckt, Einzelfall prüfen“.
- Außerhalb des Umfangs: Versorgungsfälle nach § 3 Abs. 2–4 (z. B. Laien-Blutdruckmessgeräte nach § 15 Abs. 3).
  Das Werkzeug betrachtet Bestände von Gesundheitseinrichtungen; solche Fälle werden nicht erkannt.
- Hinweis: Luftimpuls-Tonometer (Nr. 1.4) werden laut Anlage 2 Nr. 3.1 per Vergleichsmessung geprüft;
  die Frist (2 Jahre) rechnet das Werkzeug, die Prüfmethode ist nicht Teil des Werkzeugs.

---

## 3. Schweiz (Regelsatz `CH`)

### CH-1 · Keine festen Fristen
- **Fundstelle:** Art. 71 Abs. 2 MepV; GPI Kap. 7.1
- **Inhalt:** Instandhaltung richtet sich nach den Anweisungen des Herstellers und nach dem Risiko
  des Produkts. Art. 71 MepV legt keine festen Fristen fest. Prüfintervalle aus anderen Erlassen
  (z. B. Messmittel nach Art. 71 Abs. 3 MepV, Strahlenschutz) sind nicht abgedeckt.
- **Umsetzung:** Frist nur aus Feld `intervall_monate` (Herstellerangabe oder Festlegung der Fachperson).

### CH-2 · Fehlende Herstellerangaben
- **Fundstelle:** GPI Kap. 7.2.1 und 7.2.3
- **Inhalt:** Fehlen Fristen des Herstellers (z. B. ältere Geräte), legt die Fachperson sie im QMS fest.
- **Umsetzung:** `intervall_monate` leer → Befund „Intervall fehlt – Festlegung durch Fachperson“.
  Das Werkzeug schlägt **kein** Intervall vor.

### CH-3 · Datumsrechnung
- **Annahme A2:** Kein Monatsende-Prinzip vorgeschrieben → `faellig = Bezugsdatum + n Monate`
  (Kalendermonate; gibt es den Tag nicht, gilt der letzte Tag des Monats).
- **Beispiele:** 15.03.2026 + 12 → 15.03.2027 · 31.01.2026 + 1 → 28.02.2026.

### CH-4 · Kennzahlen für den Tätigkeitsbericht
- **Fundstelle:** GPI Kap. 3.6
- **Umsetzung:** Bericht liefert Bestand mit Gerätestatus (inkl. nicht auffindbar), Altersstruktur,
  Zuständigkeit (intern/extern) sowie **Verzüge und deren Zeitspanne**. Nicht geliefert: Anzahl
  durchgeführter Massnahmen (der Datensatz enthält keine Historie).

---

## 4. Datenqualität (beide Regelsätze)

Pflichtfelder sind aus den Quellen abgeleitet, nicht frei gewählt.

| ID | Prüfung | Quelle |
|---|---|---|
| DQ-1 | DE-Pflichtangaben vorhanden: Bezeichnung, Art und Typ, Loscode oder Seriennummer, Anschaffungsjahr, Hersteller mit Anschrift, Standort und betriebliche Zuordnung | § 14 Abs. 2 MPBetreibV |
| DQ-2 | CH-Pflichtangaben vorhanden: Inventarnummer, Bezeichnung, Hersteller, Modell, UDI oder Seriennummer, Typ, Risikoklasse, Lieferant, Zuständigkeit, Standort, Status, Inbetriebnahme, letzte und nächste präventive Massnahme; bei elektrischen Geräten zusätzlich Schutzklasse, Anwendungsteil, Softwareversion, Netzwerk ja/nein | GPI Kap. 8.1 |
| DQ-3 | Inventarnummer mehrfach vergeben → **Fehler**; gleiche Seriennummer und gleicher Hersteller → **Fehler**; Hersteller nur ähnlich geschrieben oder leer → **Verdacht**. Ein Befund je Gruppe, nicht je Paar | GPI 8.1 (eindeutige Inventarnummer) |
| DQ-4 | Unmögliches Datum (z. B. 31.02.), Datum in der Zukunft, Prüfung vor Inbetriebnahme, Anschaffungsjahr nach Inbetriebnahme. Bewusst konservativ als Fehler gewertet (in der Praxis teils erklärbar, z. B. Eingangsprüfung, Kauf nach Miete) | Plausibilität |
| DQ-5 | Datumsformat nicht eindeutig (gemischt TT.MM.JJJJ / JJJJ-MM-TT) → melden, **nie still umdeuten** | Plausibilität |
| DQ-6 | STK-Intervall außerhalb 1–24 Monate oder keine ganze Zahl; CH-Intervall < 1 oder keine ganze Zahl | § 12 Abs. 1 Satz 2; Art. 71 MepV |
| DQ-7 | Anlage-1- oder Anlage-2-Nummer existiert in der geltenden Fassung nicht → Frist nicht berechenbar | Anlagen 1 und 2 MPBetreibV |
| DQ-8 | CH: eingetragene „nächste präventive Massnahme“ widerspricht letzter Massnahme + Intervall | GPI 7.3 (nächster Termin auf Basis der erfolgten Instandhaltung im Inventar hinterlegen) |
| DQ-9 | Prüfpflichtiges Gerät ohne Bezugsdatum (weder Inbetriebnahme noch letzte Prüfung) → Frist nicht berechenbar | § 12 Abs. 1 Satz 2, § 15 Abs. 5 Satz 3 |
| DQ-10 | Ja/Nein-Felder (`aktiv`, `eingriff_seit_letzter_mtk`) mit anderem Wert als „ja“/„nein“ → Datenfehler, nie still umdeuten | Plausibilität, § 15 Abs. 5 Satz 4 |

---

**Präzisierungen (09.11.2026):**
- DQ-2: „Datum der letzten präventiven Massnahme“ wird nur verlangt, wenn eine stattgefunden hat; die nächste
  Massnahme wird verlangt, sobald ein Intervall festgelegt ist. Ohne Intervall gilt CH-2 („Festlegung fehlt“), kein Datenfehler.
- Annahme A3: Der CH-Datensatz enthält nur elektrische Medizinprodukte; die elektrischen Zusatzfelder nach GPI 8.1 sind daher Pflicht.
- Ist ein Datum, aus dem eine Frist berechnet wird, fehlerhaft (DQ-4/DQ-5), wird **keine** Frist berechnet
  (Status „Datenfehler“). Es wird nie still auf ein anderes Datum ausgewichen.

## 5. Ausgabe je Gerät

`status` ∈ {„in Ordnung“, „bald fällig“ (≤ 90 Tage, einstellbar), „überfällig“, „sofort fällig“,
„Festlegung fehlt“, „nicht abgedeckt“}, dazu `faellig_am`, `tage_bis_faellig`, `regel_id`.
Stichtag ist immer ein Parameter, nie automatisch „heute“.

## 6. Offene Punkte

1. DE-STK-4 (Auslegung § 12 Abs. 1 Satz 5) – bleibt offen, ist im Werkzeug sichtbar markiert.
2. Art. 71 MepV ist nach einer nicht amtlichen Wiedergabe zitiert; maßgeblich ist die Fassung auf fedlex.admin.ch.
3. Abgleich mit dem Gesetzestext erfolgte über die Webfassungen (gesetze-im-internet.de, buzer.de), nicht über das Bundesgesetzblatt.
