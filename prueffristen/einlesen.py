"""CSV einlesen und Datumsangaben streng prüfen (DQ-4, DQ-5). Nichts wird still umgedeutet."""
from __future__ import annotations

import csv
import re
from datetime import date
from typing import List, Optional, Tuple

RE_DE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})$")
RE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_SCHRAEG = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")


def lese_csv(pfad) -> List[dict]:
    """Semikolon-CSV, UTF-8 mit oder ohne BOM (utf-8-sig liest beides)."""
    with open(pfad, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def parse_datum(text) -> Tuple[Optional[date], Optional[Tuple[str, str]]]:
    """Gibt (Datum, None) oder (None, (Regel, Beschreibung)) zurück. Leeres Feld: (None, None)."""
    t = (text or "").strip()
    if not t:
        return None, None
    m = RE_DE.match(t)
    if m:
        tag, monat, jahr = map(int, m.groups())
        try:
            return date(jahr, monat, tag), None
        except ValueError:
            return None, ("DQ-4", f"unmögliches Datum „{t}“")
    if RE_ISO.match(t):
        return None, ("DQ-5", f"abweichendes Datumsformat „{t}“ (erwartet TT.MM.JJJJ)")
    if RE_SCHRAEG.match(t):
        return None, ("DQ-5", f"mehrdeutiges Datumsformat „{t}“ (Tag/Monat unklar)")
    return None, ("DQ-5", f"unbekanntes Datumsformat „{t}“")
