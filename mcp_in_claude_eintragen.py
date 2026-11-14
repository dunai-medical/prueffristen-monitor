"""Traegt den MCP-Server in die Konfiguration der Claude-Desktop-App ein (macOS).

- legt vorher eine Sicherungskopie mit Zeitstempel an (ueberschreibt keine fruehere Sicherung)
- aendert nur den Eintrag "prueffristen-monitor" unter "mcpServers"
- alle anderen Einstellungen der App bleiben unveraendert

Aufruf (Claude-App vorher beenden):  .venv/bin/python mcp_in_claude_eintragen.py
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

PROJEKT = Path(__file__).resolve().parent
KONFIG = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"

daten = json.loads(KONFIG.read_text(encoding="utf-8")) if KONFIG.exists() else {}
if KONFIG.exists():
    sicherung = KONFIG.with_name(f"claude_desktop_config.backup_{datetime.now():%Y%m%d_%H%M%S}.json")
    shutil.copy2(KONFIG, sicherung)
    print(f"Sicherungskopie: {sicherung}")

daten.setdefault("mcpServers", {})["prueffristen-monitor"] = {
    "command": str(PROJEKT / ".venv" / "bin" / "python"),
    "args": [str(PROJEKT / "mcp_server.py")],
}
KONFIG.write_text(json.dumps(daten, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Kontrolle: Datei wieder einlesen
json.loads(KONFIG.read_text(encoding="utf-8"))
print("Eingetragen:", json.dumps(daten["mcpServers"]["prueffristen-monitor"], indent=2))
print("Andere Einstellungen unveraendert:", ", ".join(k for k in daten if k != "mcpServers"))
