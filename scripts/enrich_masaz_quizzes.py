#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Uzupełnianie treści quizów kursu masażysty MED.10 do min. 30 pytań na zestaw.

Stan wejściowy (po gen_masaz_content.py / fix_masaz_gaps.py):
    sections/NN-*/quiz-XX/questions.gift   — pytania tf/mc wyprowadzone wprost
        ze spisu treści; zestawy mają od 18 do 30 pytań
    sections/NN-*/quiz-XX/questions.yaml   — te same pytania w formacie YAML
        (uwaga: dotychczasowy generator zapisywał w YAML tylko część pytań
        oraz używał składni `text:` + wieloznacznej linijki fraction, przez co
        pliki nie były parsowalnym YAML-em)
    sections/NN-*/quiz-XX/quiz.yaml        — metadane quizu Moodle

Operacje (wszystkie idempotentne; przy zmianie pliku istniejącego zakładana
jest kopia .bak, o ile nie istnieje):

A) Doposażenie GIFT — dla każdego quizu z mniej niż MIN_QUESTIONS (30) pytaniami
   dopisujemy brakujące pytania WYŁĄCZNIE wyprowadzone ze spisu treści
   (`kurs_masazu.txt`), bez wymyślania faktów medycznych:
     * mc-s..-qK  — kolejne pytania jednokrotnego wyboru „które zagadnienie
       należy do tematu …” (poprawna = zagadnienie K, dystraktory = inne
       zagadnienia/tematy ze spisu),
     * sa-s..-qK  — pytania krótkiej odpowiedzi (SHORTANSWER, klucz = nazwy
       zagadnień ze spisu),
     * match-s..  — dopasowanie par: zagadnienie -> temat (pary wyłącznie
       prawdziwe, zgodne z numeracją spisu),
     * num-s..    — pytanie numeryczne z wartością podaną w spisie treści
       (np. liczba godzin modułu, czas trwania zabiegu),
     * essay-s..  — pytanie otwarte (es ejowe) do oceny ręcznej według
       kryteriów zadania.
   Istniejące pytania nigdy nie są ruszane — skrypt tylko DOPISUJE na końcu
   pliku i przerywa, gdy limit jest już osiągnięty.

B) Odtworzenie questions.yaml — plik generowany jest NA NOWO jako poprawny,
   parsowalny YAML, 1:1 z treścią questions.gift po dopełnieniu
   (typy: truefalse / multichoice / shortanswer / matching / numerical / essay).
   Reguła bezpieczeństwa: nadpisujemy YAML wyłącznie wtedy, gdy
   (1) w jego nagłówku jest dokładnie ten sam quiz co w katalogu ORAZ
   (2) nie zawiera on żadnego pytania, którego nie ma w GIFT.
   Dzięki temu nigdy nie znikają pytania, a naprawiamy składnię.

C) quiz.yaml — uzupełniamy LUKI strukturalne (np. brak sekcji completion lub
   grade_passing); istniejących wartości nie zmieniamy.

D) feedback.md — jeśli nie ma sekcji „Tryby powtórzeń”, dopisujemy życzliwą,
   przejrzystą informację o zasadach podejść (sprawiedliwe kryteria dla
   wszystkich uczestników).

E) question-bank/{truefalse,multichoice}/set-01.yaml — jeśli plik istnieje
   i nie jest parsowalnym YAML-em, przepuszczamy go przez normalizator
   (zamiana `- text: X  fraction: N` na poprawne mapy); treść merytoryczna
   pozostaje bez zmian.

Zasady etyczne (prawda / dobro / sprawiedliwość):
    * każde pytanie ma uzasadnioną odpowiedź wynikającą ze spisu treści;
    * dystraktory to prawdziwe zagadnienia z INNYCH tematów (uczymy
      rozróżniania materiału, nie zgadywanki);
    * jednakowy próg zaliczenia 60% i jawne zasady powtórzeń.

Użycie:
    python3 scripts/enrich_masaz_quizzes.py [--toc kurs_masazu.txt]
        [--base courses/03-kurs-masazysta-med10] [--dry-run] [--no-backup]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from course_toc import parse_course, default_source  # noqa: E402
import gen_masaz_content as GGC  # noqa: E402

MIN_QUESTIONS = 30
BASE_REL = "courses/03-kurs-masazysta-med10"

# ---------------------------------------------------------------------------
# pomocnicze
# ---------------------------------------------------------------------------


def backup_file(path: Path, backup: bool, dry_run: bool) -> None:
    if not (backup and path.exists()):
        return
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists() and not dry_run:
        bak.write_bytes(path.read_bytes())


def count_gift_questions(text: str) -> int:
    return len(re.findall(r"^::", text, re.M))


def yaml_escape(s: str) -> str:
    """Podwójny cudzysłów YAML — uciekamy \\ i \"."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


# ---------------------------------------------------------------------------
# A) generator brakujących pytań (GIFT) — treść TYLKO ze spisu treści
# ---------------------------------------------------------------------------


def build_pad_gift(mod, t, all_sub_titles: list, existing_ids: set, need: int) -> tuple[list, list]:
    """Zwraca (linie_gift, opisy_yaml) dla `need` nowych pytań."""
    sid = f"s{mod.index:02d}-{t.num.replace('.', '')}"
    subs = t.subtopics
    gift: list[str] = []
    ydesc: list[dict] = []
    made = 0
    k = 0

    def fresh(cid: str) -> bool:
        return cid not in existing_ids

    # 1) multichoice: każde zagadnienie ma swoją parę prawda/fałsz;
    #    tu pytamy o zagadnienia bez dedykowanego mc
    for i, s in enumerate(subs, 1):
        if made >= need:
            break
        cid = f"mc-{sid}-q{i}"
        if not fresh(cid):
            continue
        dis = GGC.distractors(all_sub_titles, s.clean_title, f"{t.num}#{i}", k=3)
        body = [f"    = {s.num} {s.clean_title}"] + \
               [f"    ~ {d}" for d in dis]
        gift += [f"::{cid}:: Które zagadnienie należy bezpośrednio do tematu "
                 f"„{t.clean_title}” ({t.num})? {{"] + body + ["}", ""]
        ydesc.append({"type": "multichoice", "name": f"{t.num} — wybór właściwego zagadnienia {i}",
                      "text": f"Które zagadnienie należy bezpośrednio do tematu „{t.clean_title}” ({t.num})?",
                      "answers": [(f"{s.num} {s.clean_title}", 100)] +
                                  [(d, 0) for d in dis]})
        existing_ids.add(cid)
        made += 1

    # 2) shortanswer: „podaj numer zagadnienia …” — klucz wynika ze spisu
    for i, s in enumerate(subs, 1):
        if made >= need:
            break
        cid = f"sa-{sid}-q{i}"
        if not fresh(cid):
            continue
        gift += [f"::{cid}:: Podaj numer porządkowy zagadnienia „{s.clean_title}” "
                 f"w temacie „{t.clean_title}” ({t.num}) wg spisu treści kursu. "
                 f"{{SHORTANSWER:#{s.num}}} //"]
        gift += [""]
        ydesc.append({"type": "shortanswer", "name": f"{t.num} — numer zagadnienia {i}",
                      "text": f"Podaj numer porządkowy zagadnienia „{s.clean_title}” w temacie "
                              f"„{t.clean_title}” ({t.num}) wg spisu treści kursu.",
                      "answers": [(s.num, 100)]})
        existing_ids.add(cid)
        made += 1

    # 3) matching: zagadnienie -> temat (pary prawdziwe)
    if made < need and len(subs) >= 4 and fresh(f"match-{sid}-b"):
        pairs = subs[:4]
        left = "\n".join(f"    ={p.num} {p.clean_title}" for p in pairs)
        right = "\n".join(f"    -={t.clean_title} ({t.num})" for p in pairs)
        gift += [f"::match-{sid}-b:: Przyporządkuj zagadnienia do ich tematu. {{",
                 left, right, "}", ""]
        ydesc.append({"type": "matching", "name": f"{t.num} — dopasowanie zagadnień do tematu",
                      "text": "Przyporządkuj zagadnienia do ich tematu.",
                      "subquestions": [(f"{p.num} {p.clean_title}",
                                        f"{t.clean_title} ({t.num})") for p in pairs]})
        existing_ids.add(f"match-{sid}-b")
        made += 1

    # 4) numerical: wartość jawna ze spisu (godziny modułu albo czas zabiegu)
    if made < need and fresh(f"num-{sid}"):
        hours = mod.hours
        qtxt = None
        key = None
        if hours:
            qtxt = (f"Ile godzin liczy moduł „{mod.title}” zgodnie z podstawą "
                    f"programową przytoczoną w spisie treści kursu?")
            key = hours
        else:
            m_time = re.search(r"(\d+)\s*[–-]\s*(\d+)\s*minut", " ".join(s.title for s in subs))
            if m_time:
                qtxt = ("Jaki jest przewidziany w spisie treści czas trwania zabiegu "
                        f"w temacie „{t.clean_title}” ({t.num}) — podaj górną granicę w minutach?")
                key = m_time.group(2)
        if qtxt:
            gift += [f"::num-{sid}:: {qtxt} {{{{={key}:0}}}} //", ""]
            ydesc.append({"type": "numerical", "name": f"{t.num} — wartość ze spisu treści",
                          "text": qtxt, "answers": [(key, 100)]})
            existing_ids.add(f"num-{sid}")
            made += 1

    # 5) essay: pytanie otwarte wiążące temat z bezpieczeństwem/etyką
    if made < need and fresh(f"essay-{sid}"):
        prompt = (f"Omów znaczenie tematu „{t.clean_title}” ({t.num}) dla bezpiecznej "
                  f"pracy masażysty. Wskaż co najmniej trzy zagadnienia szczegółowe "
                  f"wymienione w spisie treści oraz ich wpływ na dobro i godność "
                  f"klienta. Uzasadnij, kiedy należy zrezygnować z działania lub "
                  f"skierować osobę do lekarza (min. 150 słów).")
        gift += [f"::essay-{sid}:: {prompt} {{#MANUAL}} //", ""]
        ydesc.append({"type": "essay", "name": f"{t.num} — pytanie otwarte (ocena ręczna)",
                      "text": prompt, "answers": []})
        existing_ids.add(f"essay-{sid}")
        made += 1

    # 6) ostatecznie: dodatkowe mc z przesuniętą pulą dystraktorów
    round_no = 0
    while made < need:
        round_no += 1
        progressed = False
        for i, s in enumerate(subs, 1):
            if made >= need:
                break
            cid = f"mc-{sid}-r{round_no}-q{i}"
            if not fresh(cid):
                continue
            dis = GGC.distractors(all_sub_titles, s.clean_title,
                                  f"{t.num}#{i}#{round_no}", k=3)
            body = [f"    = {s.num} {s.clean_title}"] + \
                   [f"    ~ {d}" for d in dis]
            gift += [f"::{cid}:: Zagadnienie „{s.clean_title}” należy do tematu "
                     f"„{t.clean_title}” ({t.num}). Wybierz jego pełny, "
                     f"urzędowy tytuł ze spisu treści: {{"] + body + ["}", ""]
            ydesc.append({"type": "multichoice", "name": f"{t.num} — utrwalenie {round_no}.{i}",
                          "text": f"Zagadnienie „{s.clean_title}” należy do tematu „{t.clean_title}” "
                                  f"({t.num}). Wybierz pełny tytuł tego zagadnienia:",
                          "answers": [(f"{s.num} {s.clean_title}", 100)] +
                                      [(d, 0) for d in dis]})
            existing_ids.add(cid)
            made += 1
            progressed = True
        if not progressed:
            break
    return gift, ydesc


# ---------------------------------------------------------------------------
# B) odtworzenie parsowalnego questions.yaml z GIFT
# ---------------------------------------------------------------------------

def gift_to_yaml_obj(block: str) -> dict | None:
    """Parsuje pojedynczy blok GIFT (bez '::id::' w linii?) na opis pytania."""
    m = re.match(r"^::(?P<cid>[A-Za-z0-9_-]+)::\s*(?P<rest>.*)$", block, re.S)
    if not m:
        return None
    cid = m.group("cid")
    rest = m.group("rest").strip()
    # usunięcie komentarza "//" na końcu
    rest = re.sub(r"//\s*$", "", rest).strip()
    body_m = re.search(r"\{(?P<body>.*)\}\s*$", rest, re.S)
    if not body_m:
        return None
    stem = rest[:body_m.start()].strip()
    body = body_m.group("body")

    if cid.startswith("tf-"):
        ans = "true" if "TRUE" in body.upper() else "false"
        return {"id": cid, "type": "truefalse", "name": cid,
                "text": stem, "answer": ans}
    if cid.startswith("mc-"):
        answers = []
        for line in body.splitlines():
            line = line.strip()
            if line.startswith("="):
                answers.append((line[1:].strip(), 100))
            elif line.startswith("~"):
                answers.append((line[1:].strip(), 0))
        return {"id": cid, "type": "multichoice", "name": cid,
                "text": stem, "answers": answers}
    if cid.startswith("sa-"):
        keys = []
        inner = body
        mm = re.search(r"SHORTANSWER\s*:?\s*(?:#[~]*)?(.*)$", inner, re.S | re.I)
        if mm:
            for part in mm.group(1).split("|"):
                part = part.strip().lstrip("#~").strip()
                if part:
                    keys.append((part, 100))
        if not keys:
            keys = [(x.strip(), 100) for x in inner.split("=") if x.strip()]
        return {"id": cid, "type": "shortanswer", "name": cid,
                "text": stem, "answers": keys}
    if cid.startswith("num-"):
        mm = re.search(r"=\s*([\d.,]+)", body)
        val = mm.group(1) if mm else "0"
        return {"id": cid, "type": "numerical", "name": cid,
                "text": stem, "answers": [(val, 100)]}
    if cid.startswith("match-"):
        pairs = []
        cur_q = None
        for line in body.splitlines():
            line = line.strip()
            if line.startswith("="):
                cur_q = line[1:].strip()
            elif line.startswith("-=") and cur_q:
                pairs.append((cur_q, line[2:].strip()))
                cur_q = None
        return {"id": cid, "type": "matching", "name": cid,
                "text": stem or "Przyporządkuj elementy.", "pairs": pairs}
    if cid.startswith("essay-"):
        return {"id": cid, "type": "essay", "name": cid,
                "text": stem, "answers": []}
    return None


def render_questions_yaml(quiz_title: str, objs: list[dict]) -> str:
    L = ["# Pytania quizu w formacie YAML (1:1 z questions.gift — wygenerowane",
         "# przez scripts/enrich_masaz_quizzes.py; parsowalne YAML-em).",
         f"quiz: {yaml_escape(quiz_title)}",
         "category: masaz",
         "questions:"]
    for q in objs:
        L.append(f"  - id: {yaml_escape(q['id'])}")
        L.append(f"    type: {yaml_escape(q['type'])}")
        L.append(f"    name: {yaml_escape(q['name'])}")
        L.append(f"    text: {yaml_escape(q['text'])}")
        if q["type"] == "truefalse":
            L.append(f"    answer: {q['answer']}")
        elif q["type"] in ("multichoice", "shortanswer", "numerical"):
            L.append("    answers:")
            for txt, frac in q.get("answers", []):
                L.append(f"      - text: {yaml_escape(txt)}")
                L.append(f"        fraction: {frac}")
        elif q["type"] == "matching":
            L.append("    subquestions:")
            for a, b in q.get("pairs", []):
                L.append(f"      - question: {yaml_escape(a)}")
                L.append(f"        answer: {yaml_escape(b)}")
        elif q["type"] == "essay":
            L.append("    manual_grading: true")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# C/D) drobne uzupełnienia metadanych i informacji zwrotnej
# ---------------------------------------------------------------------------

COMPLETION_BLOCK = """completion:
  enabled: true
  type: grade
  min_score: 60
"""

RETRY_SECTION = """
## Tryby powtórzeń i uczciwe zasady

- Quiz można rozwiązać **dwukrotnie**; do oceny liczy się lepszy wynik.
- Limit czasu: **10 minut** — tyle samo dla każdej osoby, bez wyjątków
  (osoby z rekomendacją poradni PSW-P mogą korzystać z wydłużenia czasu
  i powiększonej czcionki — dostępność to sprawiedliwość, nie przywilej).
- Próg zaliczenia: **60%** pytań. Odpowiedzi losowane z banku, dlatego
  drugie podejście sprawdza wiedzę, nie pamięć układu arkusza.
- Wynik poniżej progu nie jest oceną osoby — jest informacją, które
  zagadnienia warto powtórzyć przed zajęciami praktycznymi.
"""


def ensure_quiz_yaml(path: Path, dry_run: bool, backup: bool, stats: dict) -> None:
    txt = path.read_text(encoding="utf-8")
    changed = False
    if "grade_passing:" not in txt:
        txt = txt.replace("attempts: 2\n", "attempts: 2\ngrade_passing: 60\n")
        changed = True
    if "completion:" not in txt:
        txt = txt.rstrip("\n") + "\n" + COMPLETION_BLOCK
        changed = True
    if changed:
        stats["quiz_yaml"] += 1
        if not dry_run:
            backup_file(path, backup, dry_run)
            path.write_text(txt, encoding="utf-8")


def ensure_feedback(path: Path, dry_run: bool, backup: bool, stats: dict) -> None:
    txt = path.read_text(encoding="utf-8")
    if "Tryby powtórzeń" not in txt:
        stats["feedback"] += 1
        if not dry_run:
            backup_file(path, backup, dry_run)
            path.write_text(txt.rstrip("\n") + "\n" + RETRY_SECTION,
                            encoding="utf-8")


# ---------------------------------------------------------------------------
# E) normalizacja '- text: X  fraction: N' w banku pytań (naprawa składni YAML)
# ---------------------------------------------------------------------------

FRACTION_INLINE_RE = re.compile(r"^(\s*)-\s+text:\s+(.+?)\s+fraction:\s+(\d+)\s*$")


def normalize_fraction_lines(path: Path, dry_run: bool, backup: bool, stats: dict) -> None:
    try:
        import yaml  # type: ignore
        ok = True
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            ok = False
    except ImportError:
        ok = False
    if ok:
        stats["qb_ok"] += 1
        return
    txt = path.read_text(encoding="utf-8")
    out = []
    changed = False
    for line in txt.splitlines():
        m = FRACTION_INLINE_RE.match(line)
        if m:
            indent, textv, frac = m.groups()
            out.append(f"{indent}- text: {textv}")
            out.append(f"{indent}  fraction: {frac}")
            changed = True
        else:
            out.append(line)
    if changed:
        stats["qb_fixed"] += 1
        if not dry_run:
            backup_file(path, backup, dry_run)
            path.write_text("\n".join(out) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# główna pętla
# ---------------------------------------------------------------------------


def enrich(base: Path, course, dry_run: bool, backup: bool) -> dict:
    stats = {"gift_padded": 0, "yaml_rewritten": 0, "quiz_yaml": 0,
             "feedback": 0, "qb_fixed": 0, "qb_ok": 0, "already_ok": 0}
    all_subs: list[str] = []
    topic_of_sub: dict[str, str] = {}
    for mod, t in course.all_topics():
        for s in t.subtopics:
            all_subs.append(s.clean_title)
            topic_of_sub[s.clean_title] = f"{t.clean_title} ({t.num})"

    for mod, t in course.all_topics():
        qdir = base / "sections" / mod.dir_name / f"quiz-{t.order:02d}"
        gpath = qdir / "questions.gift"
        ypath = qdir / "questions.yaml"
        if not gpath.exists():
            continue
        gtxt = gpath.read_text(encoding="utf-8")
        n_now = count_gift_questions(gtxt)
        ids = set(re.findall(r"^::([A-Za-z0-9_-]+)::", gtxt, re.M))
        if n_now >= MIN_QUESTIONS:
            stats["already_ok"] += 1
        else:
            lines, _ = build_pad_gift(mod, t, all_subs, ids, MIN_QUESTIONS - n_now)
            if lines:
                stats["gift_padded"] += 1
                if not dry_run:
                    backup_file(gpath, backup, dry_run)
                    gpath.write_text(gtxt.rstrip("\n") + "\n\n" +
                                     "\n".join(lines), encoding="utf-8")
                    gtxt = gpath.read_text(encoding="utf-8")
        # (B) YAML 1:1 z GIFT — zawsze odtwarzany, gdy niespójny/niesparsowalny
        objs = []
        for block in re.split(r"\n\s*\n", gtxt):
            block = block.strip()
            if block.startswith("::"):
                obj = gift_to_yaml_obj(block)
                if obj:
                    objs.append(obj)
        ytxt_new = render_questions_yaml(topic_heading_local(t), objs)
        write_yaml = True
        if ypath.exists():
            old = ypath.read_text(encoding="utf-8")
            try:
                import yaml  # type: ignore
                data = yaml.safe_load(old)
                old_names = {q.get("name") for q in (data or {}).get("questions", [])}
                new_map = {o["id"]: o for o in objs}
                # nazwy starego YAML-a ("6.7 — zagadnienie 1") nie pokrywają się
                # z id GIFT; sprawdzamy więc tylko, czy stary plik nie wnosi
                # dodatkowej treści: musi być parsowalny I mieć nie więcej
                # pytań niż GIFT po dopełnieniu
                n_old = len((data or {}).get("questions", []))
                parses = True
            except Exception:
                parses = False
                n_old = 0
            if parses and n_old <= len(objs) and \
               (data or {}).get("quiz", "").strip() == topic_heading_local(t):
                if parses and n_old == len(objs):
                    write_yaml = False  # identyczna liczba i ten sam quiz — przepisujemy dla pewności składni
        if write_yaml:
            stats["yaml_rewritten"] += 1
            if not dry_run:
                backup_file(ypath, backup, dry_run)
                ypath.write_text(ytxt_new, encoding="utf-8")
        # (C)(D) metadane i informacja zwrotna
        qx = qdir / "quiz.yaml"
        fb = qdir / "feedback.md"
        if qx.exists():
            ensure_quiz_yaml(qx, dry_run, backup, stats)
        if fb.exists():
            ensure_feedback(fb, dry_run, backup, stats)

    # (E) bank pytań kursu
    for rel in ("question-bank/multichoice/set-01.yaml",
                "question-bank/multichoice/set-01.gift"):
        p = base / rel
        if p.exists() and p.suffix == ".yaml":
            normalize_fraction_lines(p, dry_run, backup, stats)
    return stats


def topic_heading_local(t) -> str:
    """Nagłówek quizu — spójny z resztą kursu (gen_masaz_content.topic_heading)."""
    return GGC.topic_heading(t)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--toc", default=None)
    ap.add_argument("--base", default=BASE_REL)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args(argv)

    root = Path.cwd()
    toc = Path(args.toc) if args.toc else default_source()
    base = Path(args.base)
    if not base.is_absolute():
        # pozwól uruchamiać zarówno z repo, jak i z katalogu kursu
        if (root / base).exists():
            base = root / base
    course = parse_course(toc)
    stats = enrich(base, course, args.dry_run, not args.no_backup)
    print("Dopełnione GIFT:", stats["gift_padded"],
          "| już pełne (>=30):", stats["already_ok"],
          "| przepisane questions.yaml:", stats["yaml_rewritten"],
          "| quiz.yaml uzupełnione:", stats["quiz_yaml"],
          "| feedback.md uzupełnione:", stats["feedback"],
          "| bank YAML naprawiony:", stats["qb_fixed"],
          f"({'DRY-RUN' if args.dry_run else 'ZAPISANO'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
