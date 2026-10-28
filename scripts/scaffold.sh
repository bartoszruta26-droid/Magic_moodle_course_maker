#!/usr/bin/env bash
# Konwencja kursu w repozytorium:
#   * nazwa katalogu:  courses/<NN>-<slug-tytulu>[-<kod-kwalifikacji>]
#       NN  = kolejny wolny numer dwucyfrowy (01, 02, 03, ...)
#       slug= malymi literami, bez polskich znakow, mylniki, max ~55 zn.
#       kod = opcjonalny identyfikator kwalifikacji (np. med10 dla MED.10)
#     Przyklady: 01-prawda-i-natura, 02-wiara-i-rozum,
#                03-kurs-masazysta-med10
#   * sekcje:          sections/<NN>-<slug-tematu>/  (od 00-ogloszenia)
#   * strony:          page-<NN>-<slug-tematu>.md   (NN = numer tematu w module)
#   * quizy/zadania:   quiz-<NN>/..., assignment-<NN>/...
#   * zalaczniki:      label-<NN>-<slug>.md lub podkatalogi (tryb subdirs)
set -euo pipefail
TOC="${1:?uzycie: $0 <spis-tresci.txt> [nazwa-kursu]}"; shift
NAME="${1:-}"

# 1. kolejny wolny numer NN w courses/
NUM=$(ls -1 courses/ 2>/dev/null | grep -oE '^([0-9]{2})-' | sed 's/-//' | sort -n | tail -1)
NUM=$(( ${NUM:-0} + 1 ))
NN=$(printf '%02d' "$NUM")

# 2. slug nazwy kursu (python course_toc.slugify - ta sama funkcja co w generatorach)
if [ -n "$NAME" ]; then
  SLUG=$(python3 -c "import sys; sys.path.insert(0,'scripts'); from course_toc import slugify; print(slugify(sys.argv[1], 45))" "$NAME")
else
  SLUG=$(python3 -c "import sys,re; sys.path.insert(0,'scripts'); from course_toc import parse_course, slugify; c=parse_course(sys.argv[1]); print(slugify(re.sub(r'(?i)(kwalifikacyjny|kurs|zawodowy|certyfikowanego)', '', c.name), 45))" "$TOC")
fi
BASE="courses/${NN}-${SLUG}"

# 3. szkic pustych plikow + stuby stron + szablony quizow
python3 scripts/scaffold_course.py --toc "$TOC" --base "$BASE"
python3 scripts/gen_page_stubs.py  --toc "$TOC" --base "$BASE"
python3 scripts/gen_quiz_templates.py --toc "$TOC" --base "$BASE"

# 4. kontrola struktury wzgledem spisu tresci
python3 scripts/scaffold_course.py --toc "$TOC" --base "$BASE" --check || true
echo "Kurs szkicowy gotowy: $BASE"
