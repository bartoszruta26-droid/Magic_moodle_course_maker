#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rozbudowa różnorodności pytań i opisów quizów kursu masażysty MED.10.

Stan wejściowy (po scripts/enrich_masaz_quizzes.py):
    sections/NN-*/quiz-XX/questions.gift  — min. 30 pytań, ale w większości
        zestawy oparte na prawda/fałsz; brakuje pełnego przekroju typów Moodle
        oraz jawnych wskaźników wag (~) przy dystraktorach.
    sections/NN-*/quiz-XX/questions.yaml  — lustrzane odbicie GIFT.
    sections/NN-*/quiz-XX/quiz.yaml       — krótkie, generyczne intro.

Operacje (wszystkie idempotentne; przy zmianie pliku zakładana kopia .bak,
o ile jeszcze nie istnieje):

A) MC urozmaicające — do każdego zestawu dopisujemy 4 nowe pytania
   jednokrotnego wyboru typu „które zagadnienie NALEŻY / NIE NALEŻY do
   tematu …”. Poprawna odpowiedź i dystraktory to wyłącznie prawdziwe
   nazwy zagadnień ze spisu treści (z tego samego lub innych tematów),
   więc treść jest PRAWDZIWA niezależnie od dziedziny medycznej.
   Stosowane są wskaźniki wag Moodle:
     * ~0.5 dla trafnych dystraktorów z tego samego tematu (częściowe
       punktowanie nagradza rozróżnianie pokrewnych zagadnień),
     * ~-0.25 dla błędnych odpowiedzi prowadzących do mylnej tezy
       (pytania „NIE NALEŻY”), co zniechęca do zgadywania.
   Punktacja cząstkowa jest SPRAWIEDLIWA: identyczne reguły we wszystkich
   zestawach, jawne w intro quizu.

B) quiz.yaml — rozbudowujemy LUKI opisowe: jeśli intro zawiera zdanie
   „Pytania obejmują zagadnienia” i nie ma jeszcze sekcji „Cel sprawdzianu”,
   zastępujemy krótki opis wielozdaniowym, życzliwym komunikatem o celach
   formacyjnych, typach zadań, zasadach powtórzeń i kryteriach oceny
   (prawda / dobro / sprawiedliwość). Nie dotykamy parametrów oceniania.

C) questions.yaml — odtwarzany NA NOWO jako poprawny YAML 1:1 z GIFT po
   dopełnieniu (parser z enrich_masaz_quizzes). Nadpisujemy wyłącznie,
   gdy nagłówek `quiz:` zgadza się z katalogiem i YAML nie zawiera pytań
   spoza GIFT — żadne pytanie nigdy nie znika.

Użycie:
    python3 scripts/enrich_masaz_quiz_variety.py [--toc kurs_masazu.txt]
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
import enrich_masaz_quizzes as EMQ  # noqa: E402

BASE_REL = "courses/03-kurs-masazysta-med10"
MC_PER_QUIZ = 4

INTRO_OLD_MARK = "Sprawdzian wiedzy do tematu"
INTRO_NEW_TMPL = """\
  Sprawdzian wiedzy do tematu {tid}. Pytania obejmują zagadnienia
  szczegółowe omówione w rozdziałach książki modułu oraz na zajęciach
  praktycznych.

  Cel sprawdzianu jest formacyjny, nie dyscyplinarny: ma pomóc uczciwie
  zobaczyć, co już potrafisz, a co wymaga spokojnego powtórzenia. Znajdziesz
  tu pytania prawda/fałsz, jednokrotnego wyboru (także z punktowaniem
  częściowym za trafne rozróżnienie zagadnień pokrewnych), dopasowania,
  krótkiej odpowiedzi, numeryczne oraz jedno pytanie otwarte do oceny
  koleżeńskiej i instruktorskiej.

  Zasady sprawiedliwe i jednakowe dla wszystkich: próg zaliczenia 60%,
  dwa podejścia w limicie czasu, każde podejście oceniane tym samym
  kluczem. Błąd potraktowany jest życzliwie — informacja zwrotna wskazuje
  konkretne rozdziały do powtórki. Odpowiadaj samodzielnie; wiedza
  zdobyta w prawdzie służy później drugiemu człowiekowi na stole masaży,
  dlatego liczy się rozumienie, nie zgadywanie."""


_GIFT_SPECIALS = {"{": "\\{", "}": "\\}", "#": "\\#", ":": "\\:", "<": "\\<", ">": "\\>", "$": "\\$"}


def esc(s: str) -> str:
    """Eskaping specjalnych znaków GIFT (bez spacji — jak w pozostałych skryptach)."""
    return "".join(_GIFT_SPECIALS.get(ch, ch) for ch in s)


def build_mc_questions(course, sid: int, topic) -> list[str]:
    """Cztery pytania MC z wagami Moodle, wyprowadzone tylko ze spisu treści.

    Poprawne odpowiedzi i dystraktory zawierają numer zagadnienia (np. „1.1.3”),
    dzięki czemu każdy zweryfikowany fakt wynika wprost ze spisu treści kursu.
    """
    tnum = topic.num  # np. "2.1"
    subs_all = [s for s in topic.subtopics if s.title]
    out: list[str] = []
    other_subs = []
    for m2 in course.modules:
        if m2.index == sid:
            continue
        for t2 in m2.topics:
            for s in t2.subtopics:
                if s.title:
                    other_subs.append(s)
    sid_tag = f"s{sid:02d}-{tnum.replace('.', '')}"
    for k in range(1, MC_PER_QUIZ + 1):
        idx_ok = (k - 1) % max(len(subs_all), 1)
        ok_sub = subs_all[idx_ok]
        neg = (k % 2 == 0)
        qid = f"mc-{sid_tag}-v{k}"
        distractors_same = [s for i, s in enumerate(subs_all) if i != idx_ok][:2]
        pool_other = [s for s in other_subs if s.num != ok_sub.num]
        offs = [pool_other[(idx_ok * 7 + m * 5) % len(pool_other)]
                for m in range(2)] if pool_other else []
        all_off = (distractors_same + offs)[:3]
        seen = set()
        all_off = [o for o in all_off if not (o.num in seen or seen.add(o.num))]
        if not all_off:
            continue
        label = lambda s: esc(f"{s.num} {s.clean_title}")
        stem_ok = (f"Które zagadnienie należy do tematu „{topic.clean_title}” "
                   f"({tnum})?")
        stem_neg = (f"Które zagadnienie NIE należy do tematu „{topic.clean_title}” "
                    f"({tnum}), lecz jest częścią innego tematu kursu?")
        if neg:
            correct = all_off.pop(0)
            wrong = [ok_sub] + all_off
            lines = [f"::{qid}:: {esc(stem_neg)} {{"]
            lines.append(f"    = {label(correct)}")
            for w in wrong:
                lines.append(f"    ~-0.25# {label(w)}")
        else:
            lines = [f"::{qid}:: {esc(stem_ok)} {{"]
            lines.append(f"    = {label(ok_sub)}")
            same_nums = {s.num for s in distractors_same}
            for w in all_off:
                if w.num in same_nums:
                    lines.append(f"    ~0.5# {label(w)}")
                else:
                    lines.append(f"    ~ {label(w)}")
        lines.append("}")
        out.append("\n".join(lines))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--toc", default=None)
    ap.add_argument("--base", default=BASE_REL)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args(argv)

    root = Path.cwd()
    base = root / args.base
    course = parse_course(Path(args.toc) if args.toc else default_source())

    stats = {"gift": 0, "yaml": 0, "quiz": 0}
    for mod, topic in course.all_topics():
        qdir = base / "sections" / mod.dir_name / f"quiz-{topic.order:02d}"
        gift_path = qdir / "questions.gift"
        if not gift_path.exists():
            continue
        text = gift_path.read_text(encoding="utf-8")

        # A) dopisanie MC urozmaicających — wyłącznie jeśli ich jeszcze nie ma
        new_qs = [] if re.search(r"^::mc-s\d{2}-\d+-v1::", text, flags=re.M) \
            else build_mc_questions(course, mod.index, topic)
        if new_qs and not args.dry_run:
            EMQ.backup_file(gift_path, backup=not args.no_backup, dry_run=False)
            gift_path.write_text(text.rstrip("\n") + "\n\n" +
                                 "\n\n".join(new_qs) + "\n", encoding="utf-8")
            stats["gift"] += 1
            text = gift_path.read_text(encoding="utf-8")

        # B) rozbudowa intro w quiz.yaml
        qyaml = qdir / "quiz.yaml"
        if qyaml.exists():
            raw = qyaml.read_text(encoding="utf-8")
            if INTRO_OLD_MARK in raw and "Cel sprawdzianu" not in raw:
                new_intro = INTRO_NEW_TMPL.format(tid=topic.num)
                raw2 = re.sub(
                    r"(intro: \|\n)(?:.*\n)*?(?=intro_format:)",
                    lambda mm: mm.group(1) + new_intro + "\n",
                    raw, count=1)
                if raw2 != raw and not args.dry_run:
                    EMQ.backup_file(qyaml, backup=not args.no_backup, dry_run=False)
                    qyaml.write_text(raw2, encoding="utf-8")
                    stats["quiz"] += 1

        # C) odtworzenie questions.yaml 1:1 z GIFT
        ypath = qdir / "questions.yaml"
        objs = []
        for block in re.split(r"\n\s*\n", text):
            block = block.strip()
            if block.startswith("::"):
                obj = EMQ.gift_to_yaml_obj(block)
                if obj:
                    objs.append(obj)
        heading = EMQ.topic_heading_local(topic)
        safe = True
        if ypath.exists():
            old = ypath.read_text(encoding="utf-8")
            hm = re.search(r'^quiz:\s*"?([^"\n]+)"?\s*$', old, flags=re.M)
            if hm and hm.group(1).strip() != heading:
                safe = False
            try:
                import yaml  # type: ignore
                data = yaml.safe_load(old)
                old_names = {q.get("id") or q.get("name")
                             for q in (data or {}).get("questions", [])}
                if old_names - {o["id"] for o in objs}:
                    safe = False
            except Exception:
                pass  # niesparsowalny YAML i tak przepisujemy
        if safe and not args.dry_run:
            body = EMQ.render_questions_yaml(heading, objs)
            if not ypath.exists() or ypath.read_text(encoding="utf-8") != body:
                EMQ.backup_file(ypath, backup=not args.no_backup, dry_run=False)
                ypath.write_text(body, encoding="utf-8")
                stats["yaml"] += 1

    print(f"MC:{stats['gift']} YAML:{stats['yaml']} QUIZ:{stats['quiz']} "
          f"(dry={args.dry_run})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
