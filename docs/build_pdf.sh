#!/usr/bin/env bash
# Render docs/research_{EN,PL}.html to PDF with headless Chrome.
# The HTML files are page fragments (the artifact host adds the document
# skeleton), so wrap each one in a minimal skeleton before printing.
set -euo pipefail
cd "$(dirname "$0")"
CHROME=${CHROME:-google-chrome}

for lang in EN PL; do
  src="research_${lang}.html"
  [ -f "$src" ] || continue
  tmp=".print_${lang}.html"
  {
    printf '<!doctype html>\n<html lang="%s"><head><meta charset="utf-8">\n' "$(echo "$lang" | tr 'A-Z' 'a-z')"
    printf '<meta name="viewport" content="width=device-width, initial-scale=1">\n</head><body>\n'
    cat "$src"
    printf '\n</body></html>\n'
  } > "$tmp"
  "$CHROME" --headless=new --disable-gpu --no-pdf-header-footer \
    --virtual-time-budget=8000 --run-all-compositor-stages-before-draw \
    --print-to-pdf="research_${lang}.pdf" "file://$PWD/$tmp" 2>/dev/null
  rm -f "$tmp"
  echo "wrote docs/research_${lang}.pdf"
done
