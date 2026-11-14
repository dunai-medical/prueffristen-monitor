"""Erzeugt zwei synthetische Gerätebestände mit protokollierten Fehlern.

- geraete_de.csv  : fiktives "Klinikum Musterstadt" (Felder nach § 14 MPBetreibV)
- geraete_ch.csv  : fiktives "Spital Musterhausen"  (Felder nach GPI Kap. 8.1)
- fehlerprotokoll.csv : jeder absichtlich eingebaute Fehler (Datensatz, Zeile, Regel-ID)

Alle Namen, Hersteller, Modelle und Seriennummern sind erfunden.
Risikoklassen und Intervalle sind plausible Beispielwerte, keine Klassifizierungsauskunft.
Reproduzierbar: gleicher SEED -> identische Dateien. Nur Standardbibliothek.
"""
import calendar
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20261109
STICHTAG = date(2026, 11, 9)
ORDNER = Path(__file__).parent
N_DE, N_CH = 300, 200

# key, Bezeichnung, Typkürzel, Anlage 1, Anlage 2, Gewicht, Risikoklasse, CH-Intervall (Monate), Schutzklasse, Anwendungsteil, Netzwerk
KATEGORIEN = [
    ("defibrillator", "Defibrillator", "DFB", "1.1", "", 10, "IIb", 12, "I", "CF", "nein"),
    ("infusionspumpe", "Infusionspumpe", "INF", "1.4", "", 40, "IIb", 24, "I", "CF", "ja"),
    ("spritzenpumpe", "Spritzenpumpe", "SPR", "1.4", "", 35, "IIb", 24, "I", "CF", "ja"),
    ("beatmung", "Beatmungsgerät", "BEA", "1.5", "", 15, "IIb", 12, "I", "BF", "ja"),
    ("anaesthesie", "Anästhesiegerät", "ANA", "1.5", "", 8, "IIb", 6, "I", "BF", "ja"),
    ("hf_chirurgie", "HF-Chirurgiegerät", "HFC", "1.3", "", 8, "IIb", 12, "I", "CF", "nein"),
    ("inkubator", "Säuglingsinkubator", "INK", "2", "", 6, "IIb", 12, "I", "BF", "nein"),
    ("dialyse", "Dialysegerät", "DIA", "1.4", "", 6, "IIb", 6, "I", "CF", "ja"),
    ("ekg", "EKG-Gerät", "EKG", "", "", 20, "IIa", 24, "I", "CF", "ja"),
    ("pulsoximeter", "Pulsoximeter", "POX", "", "", 25, "IIa", 24, "II", "BF", "nein"),
    ("absaugpumpe", "Absaugpumpe", "ABS", "", "", 15, "IIa", 24, "I", "B", "nein"),
    ("ultraschall", "Ultraschallgerät", "USG", "", "", 8, "IIa", 12, "I", "BF", "ja"),
    ("nibp", "Blutdruckmessgerät (nichtinvasiv)", "NBP", "", "1.3", 30, "IIa", 24, "II", "BF", "nein"),
    ("ir_thermometer", "Infrarot-Strahlungsthermometer", "IRT", "", "1.2.3", 25, "IIa", 12, "II", "B", "nein"),
    ("elektrothermometer", "Medizinisches Elektrothermometer", "ETH", "", "1.2.1", 10, "IIa", 24, "II", "B", "nein"),
    ("audiometer", "Ton- und Sprachaudiometer", "AUD", "", "1.1", 2, "IIa", 12, "I", "B", "nein"),
    ("tonometer", "Augentonometer", "TON", "", "1.4", 2, "IIa", 12, "I", "B", "nein"),
    ("ergometer", "Tretkurbelergometer", "ERG", "", "1.7", 2, "IIa", 12, "I", "B", "nein"),
    ("aed_laien", "AED (Laienanwendung, Foyer)", "AED", "1.1", "", 2, "IIb", 12, "II", "BF", "nein"),
]
FELDER_KAT = ["key", "bez", "kurz", "a1", "a2", "gewicht", "klasse", "ch_int", "schutz", "anw", "netz"]
KAT = [dict(zip(FELDER_KAT, k)) for k in KATEGORIEN]
MTK_JAHRE = {"1.1": 1, "1.2.1": 2, "1.2.2": 2, "1.2.3": 1, "1.3": 2, "1.4": 2, "1.6": 5, "1.7": 2}

HERSTELLER_DE = [
    ("Musterwerk Medizintechnik GmbH", "Industriestraße 1, 12345 Musterstadt, DE"),
    ("Beispiel Medical AG", "Werkweg 5, 54321 Beispielhausen, DE"),
    ("Fiktiva Health GmbH", "Am Prüfstand 3, 11111 Fiktivstadt, DE"),
    ("Probe Elektromedizin KG", "Testallee 7, 22222 Probeburg, DE"),
]
HERSTELLER_CH = [h for h, _ in HERSTELLER_DE] + ["Demo Devices SA", "Exempla Medtech AG"]
LIEFERANTEN_CH = ["MediHandel Muster AG", "Spitalbedarf Beispiel GmbH", "Direktbezug Hersteller"]
ZUSTAENDIG_CH = ["Medizintechnik intern", "Hersteller-Service", "Fremdfirma Muster Service AG"]
ORTE = [("Haus A, Ebene 2", "Intensivstation"), ("Haus A, Ebene 1", "Notaufnahme"),
        ("Haus B, Ebene 3", "Kardiologie"), ("Haus B, Ebene 0", "OP-Bereich"),
        ("Haus C, Ebene 1", "Neonatologie"), ("Haus C, Ebene 2", "Innere Medizin"),
        ("Haus D, Ebene 1", "HNO-Ambulanz"), ("Haus D, Ebene 0", "Foyer")]


def fmt(d):
    return d.strftime("%d.%m.%Y") if d else ""


def plus_monate_genau(d, n):
    m = d.month - 1 + n
    j, m = d.year + m // 12, m % 12 + 1
    return date(j, m, min(d.day, calendar.monthrange(j, m)[1]))


def zurueck(rng, tage_von, tage_bis):
    return STICHTAG - timedelta(days=rng.randint(tage_von, tage_bis))


def kategorie(rng, ohne=()):
    pool = [k for k in KAT if k["key"] not in ohne]
    return rng.choices(pool, weights=[k["gewicht"] for k in pool])[0]


def status(rng, land="DE"):
    r = rng.random()
    ausser = "außer Betrieb" if land == "DE" else "ausser Betrieb"  # CH-Rechtschreibung ohne ß
    return "betriebsbereit" if r < 0.94 else "defekt" if r < 0.97 else "nicht auffindbar" if r < 0.99 else ausser


def de_geraet(rng, nr, key=None):
    k = next(x for x in KAT if x["key"] == key) if key else kategorie(rng, ohne=("aed_laien",))
    ibn = zurueck(rng, 150, 12 * 365)
    hersteller, anschrift = rng.choice(HERSTELLER_DE)
    standort, zuordnung = rng.choice(ORTE)
    g = {"inventarnr": f"DE-{nr:05d}", "bezeichnung": k["bez"], "art_typ": f"{k['kurz']}-{rng.randint(100, 999)}",
         "seriennr": f"{k['kurz']}{rng.randint(10**6, 10**7 - 1)}",
         "anschaffungsjahr": str(ibn.year - (1 if rng.random() < 0.2 else 0)),
         "hersteller": hersteller, "hersteller_anschrift": anschrift, "standort": standort, "zuordnung": zuordnung,
         "kategorie": k["key"], "anlage1_nr": k["a1"], "anlage2_nr": k["a2"], "aktiv": "ja",
         "inbetriebnahme": fmt(ibn), "letzte_stk": "", "stk_intervall_monate": "", "letzte_mtk": "",
         "eingriff_seit_letzter_mtk": "nein", "status": status(rng, "DE"), "_ibn": ibn, "_fehler": []}
    # STK: Anlage 1 immer; andere aktive Geräte zu 90 % mit Betreiberfestlegung 24 Monate
    if k["a1"] or rng.random() < 0.9:
        monate = 12 if (k["a1"] and rng.random() < 0.15) else 24
        if not k["a1"] or monate == 12:
            g["stk_intervall_monate"] = str(monate)
        grenze = int(monate * 30.4)
        d = zurueck(rng, 20, grenze - 30) if rng.random() < 0.88 else zurueck(rng, grenze + 10, grenze + 200)
        if d >= ibn:
            g["letzte_stk"] = fmt(d)
    # MTK für Anlage-2-Geräte
    if k["a2"]:
        j = MTK_JAHRE[k["a2"]]
        d = zurueck(rng, 20, j * 365 - 30) if rng.random() < 0.88 else zurueck(rng, j * 365 + 400, j * 365 + 700)
        if d >= ibn:
            g["letzte_mtk"] = fmt(d)
        if rng.random() < 0.03:
            g["eingriff_seit_letzter_mtk"] = "ja"
    return g


def ch_geraet(rng, nr):
    k = kategorie(rng, ohne=("aed_laien",))
    ibn = zurueck(rng, 150, 12 * 365)
    standort, _ = rng.choice(ORTE)
    hersteller = rng.choice(HERSTELLER_CH)
    g = {"inventarnr": f"CH-{nr:05d}", "bezeichnung": k["bez"], "hersteller": hersteller,
         "modell": f"{k['kurz']}-{rng.randint(100, 999)}", "udi_oder_seriennr": f"{k['kurz']}{rng.randint(10**6, 10**7 - 1)}",
         "typ": "MP", "risikoklasse": k["klasse"], "lieferant": rng.choice(LIEFERANTEN_CH),
         "zustaendig": rng.choice(ZUSTAENDIG_CH), "standort": standort, "status": status(rng, "CH"),
         "inbetriebnahme": fmt(ibn), "letzte_instandhaltung": "", "naechste_instandhaltung": "",
         "intervall_monate": "", "schutzklasse": k["schutz"], "anwendungsteil": k["anw"],
         "sw_version": f"{rng.randint(1, 9)}.{rng.randint(0, 20)}", "netzwerk": k["netz"],
         "_ibn": ibn, "_fehler": []}
    if rng.random() < 0.92:  # 8 %: Herstellerangabe fehlt (legitimer Zustand, kein Datenfehler)
        n = k["ch_int"]
        g["intervall_monate"] = str(n)
        tage = int(n * 30.4)
        d = zurueck(rng, 15, tage - 15) if rng.random() < 0.88 else zurueck(rng, tage + 10, tage + 200)
        bezug = d if d >= ibn else ibn
        if d >= ibn:
            g["letzte_instandhaltung"] = fmt(d)
        g["naechste_instandhaltung"] = fmt(plus_monate_genau(bezug, n))
    return g


def pruefe_sauber(geraete, datumsfelder):
    """Basisdaten müssen fehlerfrei sein, bevor Fehler eingebaut werden."""
    for g in geraete:
        for f in datumsfelder:
            if g[f]:
                d = date(*reversed([int(x) for x in g[f].split(".")]))
                assert d <= STICHTAG or f == "naechste_instandhaltung", (g["inventarnr"], f)
                assert f == "inbetriebnahme" or f == "naechste_instandhaltung" or d >= g["_ibn"], (g["inventarnr"], f)


def markiere(g, regel, beschreibung):
    g["_fehler"].append((regel, beschreibung))


def baue_fehler_de(rng, geraete):
    anlage1 = [g for g in geraete if g["anlage1_nr"] and g["kategorie"] != "aed_laien"]
    for g in rng.sample(anlage1, 2):
        g["inbetriebnahme"] = ""; g["letzte_stk"] = ""; markiere(g, "DQ-9", "kein Bezugsdatum für STK")
    frei = [g for g in geraete if not g["_fehler"]]
    pflicht = rng.sample(frei, 10)                                      # DQ-1: zufällige Geräte
    rest = [g for g in frei if g not in pflicht and g["letzte_stk"]]
    it = iter(pflicht + rng.sample(rest, 12))                            # Datumsfehler: Geräte mit STK-Datum
    for _ in range(4):
        g = next(it); g["seriennr"] = ""; markiere(g, "DQ-1", "Seriennummer fehlt")
    for _ in range(3):
        g = next(it); g["hersteller_anschrift"] = ""; markiere(g, "DQ-1", "Herstelleranschrift fehlt")
    for _ in range(3):
        g = next(it); g["standort"] = ""; markiere(g, "DQ-1", "Standort fehlt")
    it2 = it
    for _ in range(2):
        g = next(it2); g["letzte_stk"] = "31.02.2025"; markiere(g, "DQ-4", "unmögliches Datum (31.02.)")
    for _ in range(2):
        g = next(it2); g["letzte_stk"] = fmt(STICHTAG + timedelta(days=rng.randint(30, 300))); markiere(g, "DQ-4", "Prüfdatum in der Zukunft")
    for _ in range(2):
        g = next(it2); g["letzte_stk"] = fmt(g["_ibn"] - timedelta(days=rng.randint(30, 200))); markiere(g, "DQ-4", "Prüfung vor Inbetriebnahme")
    for _ in range(2):
        g = next(it2); g["anschaffungsjahr"] = str(g["_ibn"].year + 1); markiere(g, "DQ-4", "Anschaffungsjahr nach Inbetriebnahme")
    for _ in range(2):
        g = next(it2); g["letzte_stk"] = "03/04/2025"; markiere(g, "DQ-5", "mehrdeutiges Datumsformat")
    for _ in range(2):
        g = next(it2); g["stk_intervall_monate"] = "36"; markiere(g, "DQ-6", "STK-Intervall über 24 Monate")
    neue = []
    unberuehrt = [g for g in geraete if not g["_fehler"]]
    for i, g in enumerate(rng.sample(unberuehrt, 5)):
        kopie = {k: (list() if k == "_fehler" else v) for k, v in g.items()}
        kopie["inventarnr"] = f"DE-{90001 + i:05d}"
        if i < 3:
            markiere(kopie, "DQ-3", f"exakte Dublette von {g['inventarnr']}")
        else:
            kopie["hersteller"] = g["hersteller"].rsplit(" ", 1)[0]
            markiere(kopie, "DQ-3", f"Schreibvariante (Verdacht) von {g['inventarnr']}")
        neue.append(kopie)
    return geraete + neue


def baue_fehler_ch(rng, geraete):
    opfer = rng.sample(geraete, 22)
    it = iter(opfer)
    for feld, n in [("udi_oder_seriennr", 3), ("risikoklasse", 2), ("lieferant", 2), ("schutzklasse", 2), ("inventarnr", 2)]:
        for _ in range(n):
            g = next(it); g[feld] = ""; markiere(g, "DQ-2", f"Pflichtfeld {feld} fehlt")
    mit_ih = [g for g in it if g["letzte_instandhaltung"]]
    it2 = iter(mit_ih)
    for _ in range(2):
        g = next(it2); g["letzte_instandhaltung"] = "31.02.2026"; markiere(g, "DQ-4", "unmögliches Datum (31.02.)")
    g = next(it2); d = STICHTAG + timedelta(days=45); g["letzte_instandhaltung"] = fmt(d)
    g["naechste_instandhaltung"] = fmt(plus_monate_genau(d, int(g["intervall_monate"]))); markiere(g, "DQ-4", "Datum in der Zukunft")
    for _ in range(2):
        g = next(it2); d = g["_ibn"] - timedelta(days=90); g["letzte_instandhaltung"] = fmt(d)
        g["naechste_instandhaltung"] = fmt(plus_monate_genau(d, int(g["intervall_monate"]))); markiere(g, "DQ-4", "Instandhaltung vor Inbetriebnahme")
    g = next(it2); g["letzte_instandhaltung"] = "03/04/2026"; markiere(g, "DQ-5", "mehrdeutiges Datumsformat")
    for _ in range(3):
        g = next(it2)
        d = date(*reversed([int(x) for x in g["naechste_instandhaltung"].split(".")]))
        g["naechste_instandhaltung"] = fmt(d + timedelta(days=rng.choice([-120, 95, 200])))
        markiere(g, "DQ-8", "nächste Instandhaltung widerspricht Intervall")
    neue = []
    unberuehrt = [g for g in geraete if not g["_fehler"]]
    for i, g in enumerate(rng.sample(unberuehrt, 4)):
        kopie = {k: (list() if k == "_fehler" else v) for k, v in g.items()}
        kopie["inventarnr"] = f"CH-{90001 + i:05d}"
        if i < 2:
            markiere(kopie, "DQ-3", f"exakte Dublette von {g['inventarnr']}")
        else:
            kopie["hersteller"] = g["hersteller"].upper()
            markiere(kopie, "DQ-3", f"Schreibvariante (Verdacht) von {g['inventarnr']}")
        neue.append(kopie)
    return geraete + neue


def schreibe(pfad, geraete):
    spalten = [k for k in geraete[0] if not k.startswith("_")]
    with open(pfad, "w", newline="", encoding="utf-8-sig") as f:  # BOM: Excel (Mac) erkennt UTF-8
        w = csv.DictWriter(f, fieldnames=spalten, delimiter=";")
        w.writeheader()
        for g in geraete:
            w.writerow({k: g[k] for k in spalten})


def main():
    rng = random.Random(SEED)
    de = [de_geraet(rng, i + 1) for i in range(N_DE - 2)]
    de += [de_geraet(rng, N_DE - 1 + i, key="aed_laien") for i in range(2)]  # Fall T15 sicher enthalten
    pruefe_sauber(de, ["inbetriebnahme", "letzte_stk", "letzte_mtk"])
    ch = [ch_geraet(rng, i + 1) for i in range(N_CH)]
    pruefe_sauber(ch, ["inbetriebnahme", "letzte_instandhaltung", "naechste_instandhaltung"])
    de = baue_fehler_de(rng, de)
    ch = baue_fehler_ch(rng, ch)
    rng.shuffle(de)
    rng.shuffle(ch)
    protokoll = []
    for name, liste in [("geraete_de.csv", de), ("geraete_ch.csv", ch)]:
        schreibe(ORDNER / name, liste)
        for zeile, g in enumerate(liste, start=1):
            for regel, text in g["_fehler"]:
                protokoll.append({"datei": name, "zeile": zeile, "inventarnr": g["inventarnr"], "regel": regel, "fehler": text})
    with open(ORDNER / "fehlerprotokoll.csv", "w", newline="", encoding="utf-8-sig") as f:  # BOM: Excel (Mac) erkennt UTF-8
        w = csv.DictWriter(f, fieldnames=["datei", "zeile", "inventarnr", "regel", "fehler"], delimiter=";")
        w.writeheader()
        w.writerows(protokoll)
    print(f"DE: {len(de)} Geräte, CH: {len(ch)} Geräte, eingebaute Fehler: {len(protokoll)}")


if __name__ == "__main__":
    main()
