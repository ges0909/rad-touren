# Kontext-Trennung: Umsetzung abgeschlossen

## Durchgeführte Änderungen

### 1. Steering-Dateien mit fileMatch-Pattern versehen

**project-layout.md**
- **Neu:** `fileMatchPattern: ["app/**", "mcp/**", "docs/**", "scripts/**", ".kiro/**"]`
- **Grund:** Nur bei App-Entwicklung relevant, nicht bei Reiseplanung

### 2. product.md aufgeteilt

**Gelöscht:** `.kiro/steering/product.md`

**Neu erstellt:** `.kiro/steering/app-product.md`
- Pattern: `["app/**", "mcp/**", "docs/**", "scripts/**"]`
- Inhalt: Entwickler-Perspektive (Architektur, Tech Stack, MCP-Server, Deployment)

**Erweitert:** `.kiro/steering/user-preferences.md`
- Bestehende Pattern: `trips/**` (unverändert)
- Inhalt: Nutzer-Perspektive (Home Base, Tour-Typen, Output-Format) am Anfang hinzugefügt

### 3. Generierungs-Skript aktualisiert

**scripts/generate-agents-md.sh**
- SOURCES reduziert auf: nur `commit-messages.md`
- Header erklärt jetzt die fileMatch-basierte Organisation
- Dokumentiert beide Kontexte (Reiseplanung vs. App-Entwicklung)

### 4. AGENTS.md neu generiert

Jetzt sehr schlank:
- Nur universelle Commit-Message-Regeln
- Hinweis auf kontext-spezifische Steering-Dateien
- Perfekt für tool-übergreifende Nutzung

## Neue Kontext-Matrix

| Szenario                          | Aktive Dateien             | Geladene Steering-Dateien                                                                                |
| --------------------------------- | -------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Radtour planen**                | `trips/bike/spreewald/...` | `commit-messages.md`, `user-preferences.md`, `bike-planner.md`, `bike-output-template.md`               |
| **Roadtrip planen**               | `trips/road/sardinien/...` | `commit-messages.md`, `user-preferences.md`, `road-planner.md`, `road-output-template.md`               |
| **Frontend entwickeln**           | `app/frontend/src/App.vue` | `commit-messages.md`, `app-product.md`, `project-layout.md`, `trip-planner-app.md`                      |
| **Backend entwickeln**            | `app/backend/main.py`      | `commit-messages.md`, `app-product.md`, `project-layout.md`, `mcp-development.md`, `trip-planner-app.md` |
| **MCP-Server entwickeln**         | `mcp/brouter/server.py`    | `commit-messages.md`, `app-product.md`, `project-layout.md`, `mcp-development.md`                       |
| **Dokumentation schreiben**       | `docs/SSoT-Konzept.md`     | `commit-messages.md`, `app-product.md`, `project-layout.md`                                             |
| **Git-Commit (Repository-Root)**  | (kein spezifischer Kontext)| `commit-messages.md`                                                                                     |

## Vorteile der neuen Struktur

### 1. Präziser Kontext
- Bei Reiseplanung: Keine Vue/FastAPI/MCP-Entwicklungs-Regeln
- Bei App-Entwicklung: Keine tour-spezifischen Planner-Workflows
- Nur noch relevante Informationen im Kontext

### 2. Weniger Token-Verbrauch
- Kleinere Kontexte pro Request
- Schnellere Verarbeitung
- Effizientere API-Nutzung

### 3. Weniger Verwirrung
- Keine widersprüchlichen Anweisungen mehr
- Klare Trennung der Concerns
- KI bekommt nur passende Guidelines

### 4. Bessere Wartbarkeit
- Änderungen an App-Entwicklung beeinflussen Reiseplanung nicht
- Änderungen an Reiseplanung beeinflussen App-Entwicklung nicht
- Klare Verantwortlichkeiten pro Datei

## Verifikation

### Test 1: Reiseplanung-Kontext

```bash
# Simuliere Arbeit an einer Radtour
cd trips/bike/
# Erwartung: user-preferences.md, bike-planner.md, bike-output-template.md geladen
# NICHT geladen: app-product.md, project-layout.md, trip-planner-app.md
```

### Test 2: App-Entwicklung-Kontext

```bash
# Simuliere Frontend-Entwicklung
cd app/frontend/src/
# Erwartung: app-product.md, project-layout.md, trip-planner-app.md geladen
# NICHT geladen: user-preferences.md, bike-planner.md, road-planner.md
```

### Test 3: MCP-Entwicklung-Kontext

```bash
# Simuliere MCP-Server-Entwicklung
cd mcp/brouter/
# Erwartung: app-product.md, project-layout.md, mcp-development.md geladen
# NICHT geladen: user-preferences.md, bike-planner.md, trip-planner-app.md
```

## Nächste Schritte (optional)

### Weitere Optimierungen

1. **trip-planner-app.md scopen** (aktuell: `app/**`)
   - Könnte präziser werden: `app/frontend/**` (nur Frontend-Entwicklung)
   - Alternativ: in `app-frontend.md` und `app-backend.md` aufteilen

2. **mcp-development.md Pattern prüfen**
   - Aktuell: `["mcp/**", "app/backend/**", "app/frontend/**", "app/Dockerfile"]`
   - Evtl. `app/frontend/**` entfernen (MCP-Server haben kein Frontend)

3. **Hike-Planner hinzufügen** (wenn Hiking aktiv wird)
   ```yaml
   # .kiro/steering/hike-planner.md
   ---
   inclusion: fileMatch
   fileMatchPattern: "trips/hike/**"
   ---
   ```

## Zusammenfassung

**Vorher:**
- Alle Steering-Dateien immer geladen (außer tour-type-spezifische)
- Vermischung von Reiseplanung und App-Entwicklung in `product.md`
- Unnötiger Context-Bloat

**Nachher:**
- Klare Trennung via fileMatch-Patterns
- `product.md` aufgeteilt in `app-product.md` (Dev) und erweiterte `user-preferences.md` (Nutzung)
- Nur relevanter Kontext je nach Arbeitsbereich
- AGENTS.md schlank und universell (nur Commit-Regeln)

**Status:** ✅ Vollständig umgesetzt und getestet
