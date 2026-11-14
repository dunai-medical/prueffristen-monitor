"""MCP-Server: Werkzeuge vorhanden, Ergebnisse über das Protokoll abrufbar, Zugriff begrenzt."""
import asyncio
import json

import pytest

pytest.importorskip("mcp")
import mcp_server  # noqa: E402


def rufe(name, **args):
    ergebnis = asyncio.run(mcp_server.mcp.call_tool(name, args))
    return json.loads(ergebnis.content[0].text)


def test_werkzeuge_vorhanden():
    namen = {t.name for t in asyncio.run(mcp_server.mcp.list_tools())}
    assert namen == {"liste_bestaende", "uebersicht", "fristen", "geraet", "datenqualitaet", "erstelle_pdf_bericht"}


def test_fristen_ueber_server():
    r = rufe("fristen", bestand="klinikum_musterstadt", stichtag="09.11.2026", status=["sofort fällig"])
    assert r["anzahl"] == 2


@pytest.mark.parametrize("bestand", ["../daten/geraete_de.csv", "/etc/hosts"])
def test_kein_zugriff_auf_andere_dateien(bestand):
    with pytest.raises(Exception):
        rufe("uebersicht", bestand=bestand, stichtag="09.11.2026")
