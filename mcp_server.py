"""MCP-Server: gibt Claude Werkzeuge für den Prüffristen-Monitor.

Claude rechnet keine Fristen selbst, sondern ruft den geprüften Rechenkern auf.
Start (zum Testen): .venv/bin/python mcp_server.py
In Claude Desktop wird er über claude_desktop_config.json gestartet (mcp_in_claude_eintragen.py).

Demonstration, kein Medizinprodukt, keine Rechtsberatung.
"""
from __future__ import annotations

from typing import List, Optional

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from prueffristen import werkzeuge as w

mcp = MCPServer(
    "prueffristen-monitor",
    instructions=(
        "Werkzeuge für Prüffristen (STK/MTK nach MPBetreibV, Instandhaltung nach MepV/GPI) und Datenqualität "
        "von Medizinprodukte-Beständen. Demonstration mit synthetischen Daten, kein Medizinprodukt, keine "
        "Rechtsberatung. Berechne Fristen nie selbst, sondern nutze die Werkzeuge. Gib bei jeder Aussage die "
        "Regel-ID und die Hinweise mit aus. Status 'Datenfehler', 'Festlegung fehlt' und 'nicht abgedeckt' "
        "immer ausdrücklich nennen, nie weglassen. Der Stichtag ist Pflicht (TT.MM.JJJJ): nimm das Datum, das "
        "der Mensch nennt, sonst das heutige Datum und sage, welches du genommen hast. Für 'Station' oder "
        "'Abteilung' den Parameter bereich nutzen (sucht in Standort und Zuordnung). Festlegungen und "
        "Freigaben trifft die verantwortliche Fachperson."
    ),
)
NUR_LESEN = ToolAnnotations(readOnlyHint=True)


@mcp.tool(annotations=NUR_LESEN)
def liste_bestaende() -> dict:
    """Listet die verfügbaren (fiktiven) Gerätebestände mit Regelsatz DE oder CH."""
    return w.liste_bestaende()


@mcp.tool(annotations=NUR_LESEN)
def uebersicht(bestand: str, stichtag: str) -> dict:
    """Gesamturteil und Kennzahlen eines Bestands (Bestand, Altersstruktur, Verzug, Datenqualität).
    bestand: Name aus liste_bestaende. stichtag: TT.MM.JJJJ."""
    return w.uebersicht(bestand, stichtag)


@mcp.tool(annotations=NUR_LESEN)
def fristen(bestand: str, stichtag: str, status: Optional[List[str]] = None, pruefung: Optional[str] = None,
            bereich: Optional[str] = None, faellig_von: Optional[str] = None,
            faellig_bis: Optional[str] = None) -> dict:
    """Prüffristen filtern. status: Liste aus 'überfällig', 'sofort fällig', 'bald fällig', 'in Ordnung',
    'Festlegung fehlt', 'nicht abgedeckt', 'Datenfehler'. pruefung: 'STK', 'MTK' oder 'Instandhaltung'.
    bereich: Teil von Standort oder Zuordnung (z. B. 'Intensiv'). faellig_von/faellig_bis: TT.MM.JJJJ."""
    return w.fristen(bestand, stichtag, status, pruefung, bereich, faellig_von, faellig_bis)


@mcp.tool(annotations=NUR_LESEN)
def geraet(bestand: str, inventarnr: str, stichtag: str) -> dict:
    """Stammdaten, Fristen und Datenqualitäts-Befunde eines Geräts (bei Dubletten alle Treffer)."""
    return w.geraet(bestand, inventarnr, stichtag)


@mcp.tool(annotations=NUR_LESEN)
def datenqualitaet(bestand: str, stichtag: str, regel: Optional[str] = None) -> dict:
    """Befunde der Datenqualitätsprüfung (DQ-1 bis DQ-9), optional gefiltert nach Regel-ID."""
    return w.datenqualitaet(bestand, stichtag, regel)


@mcp.tool()
def erstelle_pdf_bericht(bestand: str, stichtag: str) -> dict:
    """Erstellt den PDF-Bericht im Ordner ausgabe/ und gibt Pfad und Gesamturteil zurück."""
    return w.bericht_pdf(bestand, stichtag)


if __name__ == "__main__":
    mcp.run()
