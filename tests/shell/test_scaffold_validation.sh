#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/bin" "$TMP/courses/01-existing"
: > "$TMP/toc.txt"

cat > "$TMP/bin/python3" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "-c" ]]; then
  printf '%s\n' "test-course"
  exit 0
fi

for arg in "$@"; do
  if [[ "$arg" == "--check" ]]; then
    exit 23
  fi
done

exit 0
MOCK
chmod +x "$TMP/bin/python3"

set +e
OUTPUT="$(
  cd "$TMP" &&
    PATH="$TMP/bin:$PATH" bash "$ROOT/scripts/scaffold.sh" "$TMP/toc.txt" "Test Course" 2>&1
)"
STATUS=$?
set -e

if [[ "$STATUS" -ne 23 ]]; then
  printf 'Oczekiwano kodu 23 z końcowej walidacji, otrzymano %s\n' "$STATUS" >&2
  printf '%s\n' "$OUTPUT" >&2
  exit 1
fi

if [[ "$OUTPUT" == *"Kurs szkicowy gotowy:"* ]]; then
  printf 'Skrypt zgłosił sukces mimo błędu walidacji.\n' >&2
  exit 1
fi

printf '%s\n' "OK: błąd końcowej walidacji jest propagowany."

 
# Test rzeczywistego TOC: generator i walidator muszą używać tej samej nazwy
# strony, bez podwójnego numeru N.M. w slug.
REAL_TMP="$(mktemp -d)"
trap 'rm -rf "$TMP" "$REAL_TMP"' EXIT
REAL_BASE="$REAL_TMP/course"
mkdir -p "$REAL_BASE"
python3 "$ROOT/scripts/scaffold_course.py" --toc "$ROOT/kurs_masazu.txt" --base "$REAL_BASE"
python3 "$ROOT/scripts/gen_page_stubs.py" --toc "$ROOT/kurs_masazu.txt" --base "$REAL_BASE"
python3 "$ROOT/scripts/gen_quiz_templates.py" --toc "$ROOT/kurs_masazu.txt" --base "$REAL_BASE"
python3 "$ROOT/scripts/scaffold_course.py" --toc "$ROOT/kurs_masazu.txt" --base "$REAL_BASE" --check
python3 - "$REAL_BASE" <<'PY'
from pathlib import Path
import re
import sys

base = Path(sys.argv[1])
for section in (base / "sections").iterdir():
    if not section.is_dir():
        continue
    pages = list(section.glob("page-*.md"))
    for page in pages:
        match = re.match(r"page-(\\d{2})-(.+)\\.md$", page.name)
        if match is None:
            continue
        slug = match.group(2)
        assert not re.match(r"^\\d{1,2}-\\d{1,2}-", slug), page
    section_file = section / "section.md"
    if pages and section_file.exists():
        text = section_file.read_text(encoding="utf-8")
        for page in pages:
            assert f"](.\\/{page.name})" in text, (section, page.name)
print("OK: rzeczywisty TOC generuje zgodne nazwy stron i odnośniki.")
PY
