# Konzept: Pragmatisches Multi-Tool Context-Management

## 1. Ziel und Problemstellung

Das Projekt nutzt derzeit Kiro als primären KI-Assistenten mit differenzierter Steering-Datei-Struktur (`.kiro/steering/*.md`). Parallel etabliert sich AGENTS.md als tool-übergreifender Standard (Linux Foundation, von Kiro nativ unterstützt).

**Zielsetzung:** Aufbau einer wartbaren Struktur, die:

1. **Grundlegenden Kontext** über AGENTS.md tool-übergreifend verfügbar macht
2. **Kiro-spezifische Features** (conditional inclusion via `fileMatch`) beibehält, wo sie essentiell sind
3. **MCP-Server-Konfigurationen** mit minimalem Aufwand zwischen Tools teilbar macht
4. **Keine zusätzliche Komplexität** durch Generatoren einführt, solange Kiro das Primärtool bleibt

## 2. Bestandsaufnahme: Aktuelle Steering-Struktur

Das Projekt nutzt derzeit 10 Steering-Dateien mit zwei Einbindungs-Strategien:

| Datei                     | Inclusion-Typ | Pattern               | Zweck                            |
| ------------------------- | ------------- | --------------------- | -------------------------------- |
| `product.md`              | (always)      | –                     | Produktbeschreibung              |
| `project-layout.md`       | (always)      | –                     | Ordnerstruktur, Namenskonvention |
| `commit-messages.md`      | (always)      | –                     | Conventional Commits Rules       |
| `mcp-development.md`      | (always)      | –                     | MCP-Server Entwicklungs-Vorgaben |
| `trip-planner-app.md`     | (always)      | –                     | Web-App Coding-Guidelines        |
| `user-preferences.md`     | fileMatch     | `trips/**`            | Persönliche Reisepräferenzen     |
| `bike-planner.md`         | fileMatch     | `trips/bike/**`       | Cycling-spezifische Logik        |
| `bike-output-template.md` | fileMatch     | `trips/bike/**`       | Cycling Tour Output-Format       |
| `road-planner.md`         | fileMatch     | (implizit road-tours) | Roadtrip-spezifische Logik       |
| `road-output-template.md` | fileMatch     | (implizit road-tours) | Roadtrip Output-Format           |

**Kritische Erkenntnis:** Die `fileMatch`-Steuerung ist essentiell – sie verhindert Context-Bloat, indem tour-type-spezifische Anweisungen nur bei Bedarf geladen werden. Diese Differenzierung muss erhalten bleiben.

## 3. Einfache Lösung: Zwei-Schicht-Architektur

```
AGENTS.md (Repo-Root)           ← Standard-Layer: immer aktive Basis
    ↑ generiert aus
.kiro/steering/*.md (ohne Front-Matter)

.kiro/steering/*.md (mit fileMatch)  ← Spezialisierungs-Layer: Kiro-only
    - user-preferences.md
    - bike-planner.md
    - bike-output-template.md
    - road-planner.md
    - road-output-template.md

mcp.json (Repo + optional User)  ← MCP-Layer: manuell repliziert bei Bedarf
```

### 3.1 Standard-Layer: AGENTS.md

**Inhalt:** Alle immer aktiven Steering-Dateien werden zu einer `AGENTS.md` konkateniert:

- `product.md`
- `project-layout.md`
- `commit-messages.md`
- `mcp-development.md`
- `trip-planner-app.md`

**Vorteile:**

- Kiro liest AGENTS.md nativ → kein Generierungs-Overhead zur Laufzeit
- Andere Tools (Cursor, Gemini CLI, Codex CLI) erhalten denselben Basis-Kontext
- Einfach per Skript oder manuell wartbar

**Implementierung:**

```bash
#!/bin/bash
# scripts/generate-agents-md.sh
cat > AGENTS.md << 'EOF'
# Gerrit on Tour — AI Context

Dieses Dokument enthält project-weite Vorgaben für KI-Assistenten.
Generiert aus `.kiro/steering/*.md` (always-on Dateien).

---
EOF

cat .kiro/steering/product.md >> AGENTS.md
echo -e "\n---\n" >> AGENTS.md
cat .kiro/steering/project-layout.md >> AGENTS.md
echo -e "\n---\n" >> AGENTS.md
cat .kiro/steering/commit-messages.md >> AGENTS.md
echo -e "\n---\n" >> AGENTS.md
cat .kiro/steering/mcp-development.md >> AGENTS.md
echo -e "\n---\n" >> AGENTS.md
cat .kiro/steering/trip-planner-app.md >> AGENTS.md
```

Aufruf in pre-commit hook oder manuell bei Änderungen an den Quell-Steering-Dateien.

### 3.2 Spezialisierungs-Layer: Kiro Steering mit fileMatch

**Verbleiben unverändert in `.kiro/steering/`:**

- `user-preferences.md` (fileMatch: `trips/**`)
- `bike-planner.md` (fileMatch: `trips/bike/**`)
- `bike-output-template.md` (fileMatch: `trips/bike/**`)
- `road-planner.md` (fileMatch: analog)
- `road-output-template.md` (fileMatch: analog)

**Begründung:**
Kein anderes verbreitetes Tool bietet vergleichbare conditional-inclusion-Mechanismen. Diese Dateien bleiben Kiro-spezifisch, da ihre Funktionalität (tour-type-spezifische Kontextsteuerung) anderswo nicht abbildbar ist.

**Akzeptiertes Trade-off:**
Bei Wechsel zu einem anderen Primärtool müssen diese Dateien manuell portiert oder in dessen nächstbeste Alternative überführt werden (z.B. Cursor: mehrere `.cursor/rules/*.mdc` mit Glob-Patterns; Claude Code: verschachtelte `CLAUDE.md` in Unterordnern).

## 4. MCP-Server-Konfiguration

### 4.1 Problem: Tool-spezifische Config-Pfade

| Tool        | Projekt-Config            | User-Config                           | Root-Key    |
| ----------- | ------------------------- | ------------------------------------- | ----------- |
| Kiro        | `.kiro/settings/mcp.json` | `~/.kiro/settings/mcp.json`           | mcpServers  |
| Claude Code | `.mcp.json`               | `~/.claude.json`                      | mcpServers  |
| Cursor      | `.cursor/mcp.json`        | `~/.cursor/mcp.json`                  | mcpServers  |
| Windsurf    | –                         | `~/.codeium/windsurf/mcp_config.json` | mcpServers  |
| VS Code     | `.vscode/mcp.json`        | –                                     | servers (!) |

### 4.2 Pragmatische Lösung: Selektive Replikation

**Ansatz:** MCP-Server-Definitionen bleiben in `.kiro/settings/mcp.json` als Quelle. Bei tatsächlichem Bedarf für ein zweites Tool:

1. **Einfache Kopie:** `cp .kiro/settings/mcp.json .cursor/mcp.json`
2. **Kiro-spezifische Felder entfernen/anpassen:**
   - `autoApprove` → Cursor hat eigenes Approval-System
   - `disabledTools` → Cursor: `disabledTools` ebenfalls unterstützt, aber optional

**Kein automatischer Sync:**

- Begründung: MCP-Server-Definitionen ändern sich selten (neue Server werden inkrementell hinzugefügt, bestehende bleiben stabil)
- Bei Änderung: manuelles Update der kopierten Datei (1-2 Minuten Aufwand pro Tool)

**Sonderfall VS Code:**

```bash
# Einmalig bei Bedarf
jq '.mcpServers as $servers | {servers: $servers}' .kiro/settings/mcp.json > .vscode/mcp.json
```

### 4.3 Kiro-spezifische Features: Pragmatische Behandlung

Die aktuelle `mcp.json` nutzt Kiro-Erweiterungen:

- `autoApprove: ["tool_name", ...]` – automatische Genehmigung vertrauenswürdiger Tools
- `disabledTools: []` – Blacklist einzelner Tools

**Empfehlung:**

- In der Kiro-Version behalten (erhöht Developer Experience)
- Bei Kopie zu anderen Tools: Felder entfernen oder dokumentieren, dass sie ignoriert werden
- MCP-Protokoll selbst bleibt portabel, nur die UX-Features sind tool-spezifisch

## 5. Ordnerstruktur (finaler Stand)

```
trip-planer/
├── AGENTS.md                      ← Generiert aus always-on Steering (tool-übergreifend)
│
├── .kiro/
│   ├── settings/
│   │   └── mcp.json               ← Kanonische MCP-Definitionen (manuell repliziert bei Bedarf)
│   └── steering/
│       ├── product.md             ← Quelle für AGENTS.md (ohne Front-Matter)
│       ├── project-layout.md      ← Quelle für AGENTS.md (ohne Front-Matter)
│       ├── commit-messages.md     ← Quelle für AGENTS.md (ohne Front-Matter)
│       ├── mcp-development.md     ← Quelle für AGENTS.md (ohne Front-Matter)
│       ├── trip-planner-app.md    ← Quelle für AGENTS.md (ohne Front-Matter)
│       ├── user-preferences.md    ← fileMatch: trips/** (Kiro-spezifisch)
│       ├── bike-planner.md        ← fileMatch: trips/bike/** (Kiro-spezifisch)
│       ├── bike-output-template.md
│       ├── road-planner.md
│       └── road-output-template.md
│
├── .cursor/                       (optional, bei Bedarf)
│   └── mcp.json                   ← Kopie von .kiro/settings/mcp.json
│
└── scripts/
    └── generate-agents-md.sh      ← Konkateniert always-on Steering zu AGENTS.md
```

## 6. Migration: Schritt-für-Schritt

### Schritt 1: Front-Matter aus always-on Dateien entfernen

Derzeit haben alle Steering-Dateien explizit oder implizit `inclusion: always`. Kiro interpretiert Dateien ohne Front-Matter ebenfalls als "always", daher:

```bash
# Für jede always-on Datei (product.md, project-layout.md, etc.)
# YAML-Front-Matter entfernen falls vorhanden
```

**Begründung:** Vereinfachung – Front-Matter nur dort, wo es funktional notwendig ist (fileMatch-Dateien).

### Schritt 2: AGENTS.md generieren

```bash
chmod +x scripts/generate-agents-md.sh
./scripts/generate-agents-md.sh
git add AGENTS.md
git commit -m "feat: add AGENTS.md for cross-tool compatibility"
```

### Schritt 3: Kiro-Verhalten verifizieren

- Kiro liest weiterhin alle `.kiro/steering/*.md` (Priorität vor AGENTS.md)
- AGENTS.md wird als Fallback gelesen (bestätigt via Kiro-Doku)
- Keine funktionale Änderung für Kiro-Nutzer

### Schritt 4: Pre-Commit Hook (optional)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: generate-agents-md
        name: Update AGENTS.md from steering files
        entry: scripts/generate-agents-md.sh
        language: script
        files: ^\.kiro/steering/(product|project-layout|commit-messages|mcp-development|trip-planner-app)\.md$
```

**Effekt:** AGENTS.md wird automatisch bei Änderungen an den Quell-Dateien aktualisiert.

## 7. Nutzung mit anderen Tools

### Cursor

1. AGENTS.md wird automatisch gelesen (Standard-Support)
2. Für MCP: `cp .kiro/settings/mcp.json .cursor/mcp.json`
3. Tour-type-spezifische Logik: Erstelle `.cursor/rules/bike.mdc`, `.cursor/rules/road.mdc` mit Glob-Patterns

### Claude Code

1. AGENTS.md → CLAUDE.md symlinken oder kopieren: `ln -s AGENTS.md CLAUDE.md`
2. Für MCP: `cp .kiro/settings/mcp.json .mcp.json`
3. Tour-type-spezifische Logik: verschachtelte CLAUDE.md in `trips/bike/CLAUDE.md`, `trips/road/CLAUDE.md`

### Gemini CLI / Antigravity

1. AGENTS.md wird nativ gelesen (Standard-Support)
2. MCP-Support prüfen (Stand 2026: teilweise via MCP-Protokoll)

### GitHub Copilot

1. `cp AGENTS.md .github/copilot-instructions.md`
2. Kein MCP-Support (Stand 2026)

## 8. Vergleich zu komplexeren Lösungen

### Option A: Ruler (intellectronica/ruler)

**Pro:**

- Generiert Configs für ~30 Tools automatisch
- Open Source, etabliert

**Contra:**

- Zusätzliche Abhängigkeit (`ruler` CLI tool)
- Generiert `.kiro/steering/ruler_kiro_instructions.md` (eine Datei) → Verlust der fileMatch-Granularität
- Overhead für ein Projekt, das primär Kiro nutzt

**Entscheidung:** Nicht verwenden. Das manuelle Skript ist ausreichend und transparenter.

### Option B: Kompletter Eigenbau mit meta.yaml

**Pro:**

- Maximale Kontrolle über Mapping-Logik

**Contra:**

- Zusätzliche Abstraktionsebene (meta.yaml) zwischen Inhalt und Nutzung
- Generator-Skript muss YAML parsen, Front-Matter einfügen, Dateien verteilen
- Debugging bei Fehlern aufwendiger

**Entscheidung:** Nicht umsetzen. Der Nutzen rechtfertigt die Komplexität nicht, solange Kiro primäres Tool ist.

## 9. Wartung und Evolution

### Szenario 1: Neue always-on Steering-Datei hinzufügen

1. Erstelle `.kiro/steering/neue-datei.md` (ohne Front-Matter)
2. Ergänze in `scripts/generate-agents-md.sh`
3. Führe Skript aus → AGENTS.md aktualisiert

### Szenario 2: Neue fileMatch-Datei hinzufügen

1. Erstelle `.kiro/steering/neue-datei.md` mit Front-Matter:

```yaml
---
inclusion: fileMatch
fileMatchPattern: "trips/hike/**"
---
```

2. Keine Änderung an AGENTS.md notwendig (bleibt Kiro-spezifisch)

### Szenario 3: Zweites Tool produktiv nutzen

1. Bei Cursor: Kopiere `mcp.json`, erstelle `.cursor/rules/` analog zu Kiro-fileMatch-Logik
2. Bei Claude Code: Symlink `AGENTS.md → CLAUDE.md`, kopiere `mcp.json → .mcp.json`
3. fileMatch-Logik manuell portieren (einmaliger Aufwand)

### Szenario 4: Kiro aufgeben

Falls Kiro nicht mehr genutzt wird:

1. `.kiro/steering/*.md` mit fileMatch → in Zieltool-Format migrieren
2. AGENTS.md bleibt universeller Standard
3. `mcp.json` → in Zieltool-Pfad verschieben

## 10. Entscheidungsmatrix

| Anforderung                     | Einfache Lösung    | Ruler                 | Vollständige SSoT + Generator |
| ------------------------------- | ------------------ | --------------------- | ----------------------------- |
| AGENTS.md für andere Tools      | ✅ Ja              | ✅ Ja                 | ✅ Ja                         |
| Kiro fileMatch erhalten         | ✅ Ja              | ❌ Nein               | ⚠️ Komplex                    |
| MCP-Config teilbar              | ⚠️ Manuell         | ⚠️ Rudimentär         | ✅ Ja                         |
| Einfachheit (Wartung/Debugging) | ✅ Hoch            | ⚠️ Mittel             | ❌ Niedrig                    |
| Keine zusätzlichen Dependencies | ✅ Ja              | ❌ Nein               | ⚠️ Build-Tool nötig           |
| Sofort einsatzbereit            | ✅ Ja (1h Aufwand) | ⚠️ Setup erforderlich | ❌ Build-Infrastruktur nötig  |

**Empfehlung:** Einfache Lösung umsetzen. Sie deckt 90% des Nutzens mit 10% der Komplexität.

## 11. Zusammenfassung

**Kernprinzip:** Trennung zwischen universeller Basis (AGENTS.md) und tool-spezifischen Features (Kiro fileMatch).

**Aufwand:**

- Initial: ~1 Stunde (Skript schreiben, AGENTS.md generieren)
- Laufend: ~5 Minuten bei Änderungen (Skript ausführen)

**Nutzen:**

- Kiro-Nutzer: keine Änderung im Workflow, bessere Basis für potenzielle Tool-Wechsel
- Andere Tools: sofortige Verfügbarkeit des Projekt-Kontexts via AGENTS.md
- MCP: einmalige manuelle Kopie bei Bedarf (selten nötig)

**Nicht gelöst (bewusste Limitation):**

- Automatische Synchronisation von MCP-Configs (Trade-off: Einfachheit vs. Automatisierung)
- fileMatch-Äquivalent für andere Tools (kein anderes Tool bietet diese Granularität out-of-the-box)

**Erweiterungspfad:**
Falls zukünftig ein zweites Tool intensiv genutzt wird → dann gezielt dessen Config automatisieren (z.B. `cp`-Befehl in Pre-Commit Hook). Vorab nicht nötig.
