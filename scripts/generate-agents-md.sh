#!/bin/bash
# Generate AGENTS.md from always-on Kiro steering files
# Usage: ./scripts/generate-agents-md.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STEERING_DIR="${REPO_ROOT}/.kiro/steering"
OUTPUT_FILE="${REPO_ROOT}/AGENTS.md"

# Always-on steering files (only universally applicable files)
# Note: Context-specific files (reiseplanung, app-development) use fileMatch patterns
SOURCES=(
  "commit-messages.md"
)

# Header
cat > "${OUTPUT_FILE}" << 'EOF'
# Gerrit on Tour — AI Context

Universelle Vorgaben für alle KI-Assistenten in diesem Repository.

**Generiert aus:** `.kiro/steering/commit-messages.md`
**Kontext-spezifische Vorgaben:** Organisiert in `.kiro/steering/` mit fileMatch-Patterns:
- **Reiseplanung:** `user-preferences.md`, `bike-planner.md`, `road-planner.md` (aktiv bei Dateien in `trips/**`)
- **App-Entwicklung:** `app-product.md`, `project-layout.md`, `mcp-development.md`, `trip-planner-app.md` (aktiv bei Dateien in `app/**`, `mcp/**`)

---

EOF

# Append each source file
for file in "${SOURCES[@]}"; do
  source_path="${STEERING_DIR}/${file}"

  if [[ ! -f "${source_path}" ]]; then
    echo "Warning: ${source_path} not found, skipping" >&2
    continue
  fi

  # Remove YAML front-matter if present (lines between --- markers)
  awk '
    BEGIN { in_frontmatter = 0; first_marker_seen = 0 }
    /^---$/ {
      if (first_marker_seen == 0) {
        in_frontmatter = 1
        first_marker_seen = 1
        next
      } else if (in_frontmatter == 1) {
        in_frontmatter = 0
        next
      }
    }
    !in_frontmatter { print }
  ' "${source_path}" >> "${OUTPUT_FILE}"

  echo -e "\n---\n" >> "${OUTPUT_FILE}"
done

echo "✓ Generated ${OUTPUT_FILE} from ${#SOURCES[@]} steering files"
