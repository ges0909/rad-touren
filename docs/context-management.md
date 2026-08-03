# Konzept: Zwei-Schicht Context-Management

## 1. Ziel

Das Projekt nutzt Kiro mit kontextabhängiger Steering-Struktur (`.kiro/steering/*.md`). AGENTS.md ist der etablierte tool-übergreifende Standard (Linux Foundation, nativ unterstützt von 20+ Tools).

**Zielsetzung:**

1. **AGENTS.md** als universelle Basis für alle Tools (manuell gepflegt, ~150 Zeilen)
2. **Kiro Steering** mit `fileMatch` für kontext-spezifische Regeln (Kiro-exklusiv)
3. **MCP-Configs** bei Bedarf manuell replizieren (selten nötig)
4. **Keine Generatoren** – direkte, transparente Wartung

## 2. Aktuelle Struktur (Status Quo)

**8 Steering-Dateien mit `fileMatch`-Patterns:**

| Datei                     | Pattern                                     | Zweck                              |
| ------------------------- | ------------------------------------------- | ---------------------------------- |
| `app-product.md`          | `app/**`, `mcp/**`, `docs/**`, `scripts/**` | Platform-Architektur, Tech Stack   |
| `mcp-development.md`      | `mcp/**`, `app/backend/**`                  | MCP-Entwicklungs-Guidelines        |
| `trip-planner-app.md`     | `app/**`                                    | Web-App Coding-Vorgaben            |
| `user-preferences.md`     | `trips/**`                                  | Persönliche Reisepräferenzen       |
| `bike-planner.md`         | `trips/bike/**`                             | Cycling-Workflow + BRouter-Rules   |
| `bike-output-template.md` | `trips/bike/**`                             | Cycling-Output-Format              |
| `road-planner.md`         | `trips/road/**`                             | Roadtrip-Workflow + ORS/OSRM-Rules |
| `road-output-template.md` | `trips/road/**`                             | Roadtrip-Output-Format             |

**AGENTS.md (Repo-Root):**

- Universelle Regeln (Commit-Konventionen, Repository-Überblick, Context-Verweis)
- Manuell gepflegt, ~150 Zeilen

**Kritische Erkenntnis:** `fileMatch` ist essentiell – verhindert Context-Bloat durch selektives Laden.

## 3. Architektur: Zwei-Schicht-System

```
AGENTS.md (Repo-Root)
├─ Universelle Regeln (tool-übergreifend, manuell gepflegt)
├─ Commit-Konventionen
├─ Repository-Überblick
└─ Verweis auf Context-spezifische Steering-Dateien

.kiro/steering/*.md (fileMatch-gesteuert)
├─ Reiseplanung-Context (trips/**)
│  ├─ user-preferences.md
│  ├─ bike-planner.md + bike-output-template.md (trips/bike/**)
│  └─ road-planner.md + road-output-template.md (trips/road/**)
└─ App-Entwicklung-Context (app/**, mcp/**)
   ├─ app-product.md
   ├─ mcp-development.md
   └─ trip-planner-app.md

.kiro/settings/mcp.json (kanonische MCP-Definitionen)
└─ Bei Bedarf nach .cursor/mcp.json, .mcp.json kopieren
```

### 3.1 Layer 1: AGENTS.md

**Was:**

- Tool-übergreifender Standard (Linux Foundation)
- Nativ gelesen von Kiro, Cursor, Gemini CLI, Claude Code, Aider, Goose, etc.

**Inhalt:**

- Commit-Message-Konventionen
- Repository-Überblick (erklärt Zwei-Context-Struktur)
- Verweis auf `.kiro/steering/` mit fileMatch-Patterns
- Auto-Commit-Behavior

**Nicht enthalten:**

- Context-spezifische Vorgaben → leben in `.kiro/steering/*.md`

**Wartung:**

- Direkt editieren, manuell gepflegt
- ~150 Zeilen, Englisch
- Git-versioniert

### 3.2 Layer 2: Kiro Steering mit fileMatch

**Reiseplanung-Context:**

- `user-preferences.md` (trips/\*\*)
- `bike-planner.md` + `bike-output-template.md` (trips/bike/\*\*)
- `road-planner.md` + `road-output-template.md` (trips/road/\*\*)

**App-Entwicklung-Context:**

- `app-product.md` (app/**, mcp/**, docs/**, scripts/**)
- `mcp-development.md` (mcp/**, app/backend/**)
- `trip-planner-app.md` (app/\*\*)

**Warum fileMatch beibehalten:**

- Präzise Context-Steuerung – nur relevante Regeln werden geladen
- Verhindert Context-Bloat (wichtig bei 8 spezialisierten Dateien)
- Kiro-Feature ohne direkte Entsprechung in anderen Tools

**Trade-off:**

- Portabilität: fileMatch-Logik ist Kiro-spezifisch
- Bei Tool-Wechsel: manuelle Migration in Zieltool-Format
- Akzeptiert, da Kiro primäres Tool bleibt

## 4. MCP-Konfiguration: Pragmatischer Ansatz

### 4.1 Tool-spezifische Pfade

| Tool        | Projekt-Config            | User-Config                           |
| ----------- | ------------------------- | ------------------------------------- |
| Kiro        | `.kiro/settings/mcp.json` | `~/.kiro/settings/mcp.json`           |
| Claude Code | `.mcp.json`               | `~/.claude.json`                      |
| Cursor      | `.cursor/mcp.json`        | `~/.cursor/mcp.json`                  |
| Windsurf    | –                         | `~/.codeium/windsurf/mcp_config.json` |

### 4.2 Strategie: Selektive Replikation

**Ansatz:**

- `.kiro/settings/mcp.json` als kanonische Quelle
- Bei Bedarf manuell kopieren: `cp .kiro/settings/mcp.json .cursor/mcp.json`
- Kiro-spezifische Felder dokumentieren (`autoApprove`, `disabledTools`)

**Warum kein automatischer Sync:**

- MCP-Server ändern sich selten (inkrementelle Ergänzungen)
- Manuelles Update: 1-2 Minuten Aufwand bei Bedarf
- Vermeidet Komplexität (Build-Tools, Pre-Commit-Hooks)

**Trade-off:** Einfachheit vor Automatisierung

## 5. Implementierung & Wartung

### Ordnerstruktur

```
trip-planer/
├── AGENTS.md                      # Universelle Regeln (manuell gepflegt)
│
├── .kiro/
│   ├── settings/
│   │   └── mcp.json               # Kanonische MCP-Definitionen
│   └── steering/
│       ├── app-product.md         # fileMatch: app/**, mcp/**, docs/**, scripts/**
│       ├── mcp-development.md     # fileMatch: mcp/**, app/backend/**
│       ├── trip-planner-app.md    # fileMatch: app/**
│       ├── user-preferences.md    # fileMatch: trips/**
│       ├── bike-planner.md        # fileMatch: trips/bike/**
│       ├── bike-output-template.md
│       ├── road-planner.md        # fileMatch: trips/road/**
│       └── road-output-template.md
│
└── .cursor/                       # Optional, bei Bedarf
    └── mcp.json                   # Kopie von .kiro/settings/mcp.json
```

### Wartungs-Szenarien

**Szenario 1: AGENTS.md ändern**

- Direkt editieren, commit
- Änderung sofort für alle Tools verfügbar

**Szenario 2: Steering-Datei ändern**

- Editieren in `.kiro/steering/`
- fileMatch-Pattern anpassen falls nötig
- Nur für Kiro relevant

**Szenario 3: Neuer MCP-Server**

- Hinzufügen zu `.kiro/settings/mcp.json`
- Falls zweites Tool genutzt wird: Config manuell kopieren

**Szenario 4: Zweites Tool aktiv nutzen**

- `cp .kiro/settings/mcp.json .cursor/mcp.json`
- fileMatch-Logik manuell in Tool-Format portieren (einmalig)

## 6. Tool-Portabilität

### Cursor

- AGENTS.md: automatisch gelesen ✓
- MCP: `cp .kiro/settings/mcp.json .cursor/mcp.json`
- fileMatch-Äquivalent: `.cursor/rules/*.mdc` mit Glob-Patterns

### Claude Code

- AGENTS.md: als CLAUDE.md symlinken/kopieren
- MCP: `cp .kiro/settings/mcp.json .mcp.json`
- fileMatch-Äquivalent: verschachtelte CLAUDE.md in Unterverzeichnissen

### Andere Tools

- Gemini CLI, Aider, Goose: AGENTS.md nativ unterstützt
- GitHub Copilot: `cp AGENTS.md .github/copilot-instructions.md`

**Trade-off:** fileMatch-Logik muss manuell portiert werden (einmaliger Aufwand bei Tool-Wechsel)

## 7. Bewertung alternativer Ansätze

| Kriterium                  | Zwei-Schicht (gewählt) | Ruler               | Vollständige SSoT |
| -------------------------- | ---------------------- | ------------------- | ----------------- |
| AGENTS.md für andere Tools | ✅ Ja                  | ✅ Ja               | ✅ Ja             |
| Kiro fileMatch erhalten    | ✅ Ja                  | ❌ Nein             | ⚠️ Komplex        |
| MCP-Config teilbar         | ⚠️ Manuell             | ⚠️ Rudimentär       | ✅ Ja             |
| Wartungsaufwand            | ✅ Minimal             | ⚠️ Mittel           | ❌ Hoch           |
| Keine zusätzlichen Deps    | ✅ Ja                  | ❌ Nein (ruler CLI) | ❌ Build-Tool     |
| Transparenz/Debugging      | ✅ Hoch                | ⚠️ Mittel           | ❌ Niedrig        |

**Entscheidung:** Zwei-Schicht-Architektur – deckt 90% des Nutzens mit 10% der Komplexität.

**Ruler abgelehnt:** Verlust der fileMatch-Granularität, zusätzliche Dependency.
**Vollständige SSoT abgelehnt:** Zu komplex für aktuellen Bedarf (Kiro als primäres Tool).

## 8. Zusammenfassung

**Architektur:**

- **AGENTS.md:** Universelle Basis (Commits, Repository-Überblick) – tool-übergreifend, manuell gepflegt
- **.kiro/steering/\*.md:** Context-spezifisch mit fileMatch (Reiseplanung vs. App-Entwicklung) – Kiro-exklusiv
- **.kiro/settings/mcp.json:** Kanonische MCP-Definitionen – bei Bedarf manuell kopieren

**Vorteile:**

- Kiro-Workflow unverändert, volle fileMatch-Unterstützung
- Andere Tools erhalten universellen Kontext via AGENTS.md
- Transparent, wartbar, keine Build-Tools

**Akzeptierte Limitationen:**

- MCP-Configs nicht automatisch synchronisiert (selten nötig)
- fileMatch-Logik nicht direkt portabel (Tool-spezifisch)

**Aufwand:**

- Initial: 0h (AGENTS.md existiert bereits)
- Laufend: direkte Editierung, keine Generator-Skripte

**Evolution:**

- Bei intensiver Nutzung eines zweiten Tools: gezielt dessen Config automatisieren
- fileMatch-Migration einmalig bei Tool-Wechsel (akzeptierter Trade-off)
