#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/data/mimic-iv-demo-2.2"
if [[ -d "$DEST/hosp" ]]; then
  echo "Data already present at $DEST"
  exit 0
fi
mkdir -p "$ROOT/data"
TMP="$ROOT/data/mimic-iv-demo-2.2.zip"
echo "Downloading MIMIC-IV Clinical Database Demo v2.2…"
curl -L -o "$TMP" "https://physionet.org/content/mimic-iv-demo/get-zip/2.2/"
unzip -q "$TMP" -d "$ROOT/data"
# PhysioNet zip extracts as mimic-iv-clinical-database-demo-2.2
EXTRACTED="$ROOT/data/mimic-iv-clinical-database-demo-2.2"
if [[ -d "$EXTRACTED" ]]; then
  mv "$EXTRACTED" "$DEST"
fi
rm -f "$TMP"
echo "Ready: $DEST"
