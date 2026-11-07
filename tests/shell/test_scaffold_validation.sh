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
