# Konzept: Trennung von Reiseplanung-Kontext und App-Entwicklung-Kontext

## Problem

Das Repository dient zwei verschiedenen Zwecken:

1. **Persönliche Reiseplanung** — Du nutzt Kiro/die App, um konkrete Touren zu planen
2. **App-Entwicklung** — Du entwickelst die Plattform, die diese Planung ermöglicht

Aktuell sind beide Kontexte vermischt, was zu unnötigem Context-Bloat führt:
- Bei der Reiseplanung brauchst du keine Vue-Coding-Guidelines
- Bei der App-Entwicklung brauchst du nicht ständig die Bike-Planner-Regeln

## Lösung: Context-Scoping via fileMatch

Kiros `fileMatch`-Feature ermöglicht präzises Context-Scoping basierend auf den aktiven Dateien.

### Aktuelle Situation (teilweise schon korrekt)

| Datei                      | Aktuelles fileMatch | Zweck                  | Status    |
| -------------------------- | ------------------- | ---------------------- | --------- |
| `product.md`               | (always)            | Produktbeschreibung    | ⚠️ Hybrid |
| `project-layout.md`        | (always)            | Ordnerstruktur         | ⚠️ Hybrid |
| `commit-messages.md`       | (always)            | Git-Konventionen       | ✅ Neutral |
| `trip-planner-app.md`      | `app/**`            | App-Coding-Guidelines  | ✅ Korrekt |
| `mcp-development.md`       | `mcp/**`, `app/**`  | MCP/Backend Dev-Regeln | ✅ Korrekt |
| `user-preferences.md`      | `trips/**`          | Reisepräferenzen       | ✅ Korrekt |
| `bike-planner.md`          | `trips/bike/**`     | Cycling-Workflow       | ✅ Korrekt |
| `bike-output-template.md`  | `trips/bike/**`     | Cycling-Output-Format  | ✅ Korrekt |
| `road-planner.md`          | (implizit)          | Roadtrip-Workflow      | ⚠️ Pattern fehlt |
| `road-output-template.md`  | (implizit)          | Roadtrip-Output-Format | ⚠️ Pattern fehlt |

## Neue Struktur mit klarer Trennung

```
.kiro/steering/

# Universell (immer relevant, unabhängig vom Kontext)
├── commit-messages.md              (always) — Git gilt überall

# Reiseplanung-Kontext (nur bei Arbeit in trips/)
├── user-preferences.md             fileMatch: trips/**
├── bike-planner.md                 fileMatch: trips/bike/**
├── bike-output-template.md         fileMatch: trips/bike/**
├── road-planner.md                 fileMatch: trips/road/**
├── road-output-template.md         fileMatch: trips/road/**
├── hike-planner.md                 fileMatch: trips/hike/**  (zukünftig)
├── hike-output-template.md         fileMatch: trips/hike/**  (zukünftig)

# App-Entwicklung-Kontext (nur bei Arbeit in app/ oder mcp/)
├── app-product.md                  fileMatch: app/**,mcp/**,docs/**,scripts/**
├── app-architecture.md             fileMatch: app/**
├── app-development.md              fileMatch: app/**
├── mcp-development.md              fileMatch: mcp/**,app/backend/**
├── project-layout.md               fileMatch: app/**,mcp/**,docs/**,scripts/**
```

## Detaillierte Änderungen

### 1. product.md aufteilen

**Aktuell:** `product.md` enthält beide Aspekte (Reiseplanung + App-Beschreibung)

**Neu:**
- `user-preferences.md` erweitern um Produktbeschreibung aus Nutzersicht
- `app-product.md` erstellen mit Produktbeschreibung aus Entwicklersicht

```markdown
# user-preferences.md (fileMatch: trips/**)
---
inclusion: fileMatch
fileMatchPattern: "trips/**"
---

# Reiseplanung mit Gerrit on Tour

Home base: S Blankenfelde (TF) Bhf, Berlin
Reisegruppe: 2 Personen

## Tour-Typen
- Cycling: Brandenburg/Berlin Tagestouren
- Roadtrips: Mehrtägige Europa-Reisen
- Hiking: Brandenburg-Wanderungen (geplant)

## Präferenzen
[... bestehende user-preferences Inhalte ...]
```

```markdown
# app-product.md (fileMatch: app/**,mcp/**,docs/**,scripts/**)
---
inclusion: fileMatch
fileMatchPattern: ["app/**", "mcp/**", "docs/**", "scripts/**"]
---

# Gerrit on Tour — Platform Development

AI-powered tour planning platform.

## Architecture
- **Backend:** FastAPI + Gemini 2.5 Flash agent
- **Frontend:** Vue 3 + Vite + Tailwind
- **MCP Servers:** 13+ custom servers (routing, weather, POIs, transit)

## Deployment
- Kiro-native workflow (primary)
- Standalone web app (Vue SPA + FastAPI backend)
- Docker multi-stage build

## Output Format
Tours written to `trips/{type}/{tour-name}/`:
- `index.md` — Markdown tour description
- `gpx/` — GPX tracks
- `img/` — Route maps + elevation profiles
```

### 2. project-layout.md scopen

**Aktuell:** Immer geladen, aber primär für Entwickler relevant

**Neu:** fileMatch auf Development-Bereiche

```yaml
---
inclusion: fileMatch
fileMatchPattern: ["app/**", "mcp/**", "docs/**", "scripts/**", ".kiro/**"]
---
```

### 3. Fehlende fileMatch-Pattern ergänzen

**road-planner.md:**
```yaml
---
inclusion: fileMatch
fileMatchPattern: "trips/road/**"
---
```

**road-output-template.md:**
```yaml
---
inclusion: fileMatch
fileMatchPattern: "trips/road/**"
---
```

### 4. Neue App-Entwicklung-Datei: app-architecture.md

Extrahiere die Architektur-Beschreibung aus `trip-planner-app.md` in eine eigene Datei:

```yaml
---
inclusion: fileMatch
fileMatchPattern: "app/**"
---

# App Architecture

[Detaillierte Architektur-Beschreibung ohne Code-Style-Regeln]
```

## Ergebnis: Kontext-Scoping-Matrix

| Szenario                       | Aktive Dateien             | Geladene Steering-Dateien                                                      |
| ------------------------------ | -------------------------- | ------------------------------------------------------------------------------ |
| **Radtour planen**             | `trips/bike/spreewald/...` | `commit-messages.md`, `user-preferences.md`, `bike-planner.md`, `bike-output-template.md` |
| **Roadtrip planen**            | `trips/road/sardinien/...` | `commit-messages.md`, `user-preferences.md`, `road-planner.md`, `road-output-template.md` |
| **Frontend entwickeln**        | `app/frontend/src/App.vue` | `commit-messages.md`, `app-product.md`, `project-layout.md`, `app-architecture.md`, `app-development.md` |
| **MCP-Server entwickeln**      | `mcp/brouter/server.py`    | `commit-messages.md`, `app-product.md`, `project-layout.md`, `mcp-development.md` |
| **Dokumentation schreiben**    | `docs/SSoT-Konzept.md`     | `commit-messages.md`, `app-product.md`, `project-layout.md` |
| **Git-Commit (keine Datei)**   | (Repository-Root-Chat)     | `commit-messages.md` |

**Effekt:**
- Bei Reiseplanung: Keine Vue/FastAPI/MCP-Entwicklungs-Regeln im Kontext
- Bei App-Entwicklung: Keine tour-spezifischen Planner-Workflows im Kontext
- Nur commit-messages.md bleibt universal (Git-Konventionen gelten immer)

## Migrations-Plan

### Phase 1: Bestehende Patterns vervollständigen (5 Minuten)

```bash
# road-planner.md und road-output-template.md Front-Matter hinzufügen
```

### Phase 2: project-layout.md scopen (2 Minuten)

```yaml
# In .kiro/steering/project-layout.md
---
inclusion: fileMatch
fileMatchPattern: ["app/**", "mcp/**", "docs/**", "scripts/**", ".kiro/**"]
---
```

### Phase 3: product.md aufteilen (15 Minuten)

1. Erstelle `app-product.md` mit Entwickler-Perspektive
2. Erweitere `user-preferences.md` um Nutzer-Perspektive
3. Lösche `product.md` (Inhalte komplett migriert)

### Phase 4: AGENTS.md neu generieren (1 Minute)

Nach den Änderungen bleibt nur noch `commit-messages.md` als always-on → AGENTS.md wird sehr schlank:

```bash
./scripts/generate-agents-md.sh
```

**Neue AGENTS.md:**
```markdown
# Gerrit on Tour — AI Context

Universelle Vorgaben für alle KI-Assistenten in diesem Repository.

---

# Commit Messages

[... Conventional Commits Regeln ...]

---

**Note:** Kontext-spezifische Vorgaben (Reiseplanung vs. App-Entwicklung) 
sind in `.kiro/steering/` mit fileMatch-Patterns organisiert.
```

## Vorteile

1. **Präziser Kontext** — Die KI bekommt nur relevante Informationen
2. **Schnellere Verarbeitung** — Weniger Token pro Request
3. **Weniger Verwirrung** — Keine widersprüchlichen Anweisungen (z.B. "Schreibe Markdown-Touren" vs. "Schreibe TypeScript-Code")
4. **Bessere Wartbarkeit** — Klare Trennung der Concerns
5. **Zukunftssicher** — Bei weiteren Use-Cases (z.B. Marketing-Materialien) einfach neue fileMatch-Bereiche hinzufügen

## Anti-Pattern vermeiden

**Nicht tun:**
```yaml
# FALSCH: Zu breites Pattern
fileMatchPattern: "**/*.md"  # matched auch docs/, README.md, etc.
```

**Stattdessen:**
```yaml
# RICHTIG: Spezifisch und intentional
fileMatchPattern: "trips/**"  # nur Tour-Dokumente
```

## Zusammenfassung

**Kernprinzip:** Jede Steering-Datei hat ein klares fileMatch-Pattern, das ihren Anwendungsbereich definiert.

**Ausnahme:** Nur universelle Regeln (commit-messages.md) bleiben always-on.

**Aufwand:** 
- Initial: ~30 Minuten (Patterns hinzufügen, product.md aufteilen)
- Laufend: 0 Minuten (funktioniert automatisch basierend auf aktiven Dateien)

**Ergebnis:** 
Saubere Trennung zwischen "Ich plane eine Reise" und "Ich entwickle die Plattform" ohne manuelle Kontext-Auswahl.
