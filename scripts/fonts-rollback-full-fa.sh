#!/usr/bin/env bash
# Switch YAUB back to full Font Awesome (no file restore required for CSS/fonts).
# Usage: ./scripts/fonts-rollback-full-fa.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CFG="$ROOT/config.toml"

if grep -qE '^[[:space:]]*useFontAwesomeSubset[[:space:]]*=' "$CFG"; then
  perl -i -pe 's/^(\s*useFontAwesomeSubset\s*=\s*)\S+/${1}false/' "$CFG"
else
  perl -i -pe 's/^(\s*accentColor\s*=.*)$/$1\n  useFontAwesomeSubset = false/' "$CFG"
fi

echo "Set useFontAwesomeSubset = false in config.toml"
echo "Full FA: css/fontawesome-all.min.css + webfonts/fa-*.woff2"
echo "Backup copy: themes/yaub/static/_font-backups/2026-10-21/"
echo "Restart hugo server to pick up the change."
