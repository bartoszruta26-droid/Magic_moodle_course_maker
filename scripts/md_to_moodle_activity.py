#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Konwersja pliku Markdown kursu na aktywność Moodle (book + quiz) gotową do importu.

Stan wejściowy (kurs `courses/05-badanie-neurologiczne`): wyłącznie pliki .md,
bez znaczników HTML i bez plików kursu Moodle (brak course.yaml / sections).

Skrypt dla jednego pliku rozdziału (np. 1_2_anatomia_funkcjonalna_ukladu_nerwowego.md):
  1. Dzieli treść na rozdziały książki wg nagłówków „## N. Tytuł”.
     - pierwszy rozdział = blok przed pierwszym „##” ( tytuł + metadane ),
     - rozdział „Pytania kontrolne…” zostaje wyodrębniony z książki
       i zamieniony na pytania quizu (patrz p. 3).
  2. Zapisuje strukturę repozytorium zgodną z loaderem rdzenia magic_moodle:
         courses/<kurs>/sections/NN-sekcji/section.yaml
         courses/<kurs>/sections/NN-sekcji/book-XX-temat/book.yaml
         courses/<kurs>/sections/NN-sekcji/book-XX-temat/chapters/NN-*.md
         courses/<kurs>/sections/NN-sekcji/quiz-XX/quiz.yaml
         courses/<kurs>/sections/NN-sekcji/quiz-XX/questions.gift
     oraz tworzy uzupełniający course.yaml (jeśli go nie ma — nigdy nie nadpisuje).
  3. Buduje quiz GIFT:
     - pytania sprawdzające („N. Treść?”) → shortanswer z kluczem odpowiedzi,
     - zadania problemowe („**Zadanie N.** …”) → essay,
     - słownik pojęć (tabela | Pojęcie | Znaczenie |) → matching,
     - dodatkowo prawda/fałsz generowane ze struktury nagłówków
       (podrozdział należy do swojego rozdziału — twierdzenia prawdziwe;
        przypisanie podrozdziału do poprzedniego rozdziału — fałszywe).
  4. (--mbz) pakuje katalog kursu do pliku .mbz w formacie Moodle XML
     (backup/moodle2/course_backup.xml + question bank) — archiwum ZIP
     importowalne przez „Przywracanie kopii zapasowej” w Moodle.

Idempotentność: powtórne uruchomienie nadpisuje tylko wygenerowane zasoby
(this skrypt oznacza je nagłówkiem komentarza); istniejące course.yaml jest
dołączane, nie nadpisywane. Użycie:

    python3 scripts/md_to_moodle_activity.py \
        --source courses/05-badanie-neurologiczne/1_2_anatomia_funkcjonalna_ukladu_nerwowego.md \
        --course-dir courses/05-badanie-neurologiczne \
        --section 01-wprowadzenie-do-badania-neurologicznego \
        --mbz build/badanie-neurologiczne-1-2.mbz [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

REPO = Path(__file__).resolve().parent.parent
GENERATED_MARK = "wygenerowane przez scripts/md_to_moodle_activity.py"


# --------------------------------------------------------------------------
# pomocnicze (konwencje nazewnicze jak w scripts/course_toc.py)
# --------------------------------------------------------------------------

def fold(text: str) -> str:
    s = text.replace("\u0142", "l").replace("\u0141", "L")
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def slugify(text: str, maxlen: int = 50) -> str:
    raw = re.sub(r"[^a-z0-9]+", "-", fold(text).lower()).strip("-")
    return raw[:maxlen].strip("-") or "rozdzial"


def gift_escape(s: str) -> str:
    """Escapuje znaki specjalne GIFT (~ # { } \\ : = < > |)."""
    return re.sub(r"([~#{}\\:=<>|])", r"\\\1", s.strip())


def xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def md_to_html(source: str) -> str:
    """Konwersja podzbioru Markdown do HTML (ten sam zakres co _markdown_to_html
    w magic_moodle/moodle_publish.py, rozszerzony o tabele i poziome linie)."""
    lines_out: list[str] = []
    paragraph: list[str] = []
    in_list = False
    in_table: list[list[str]] = []

    def inline(value: str) -> str:
        value = xml_escape(value)
        value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
        value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
        value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", value)
        return value

    def flush_para() -> None:
        nonlocal paragraph
        if paragraph:
            lines_out.append("<p>" + "<br>".join(inline(l) for l in paragraph) + "</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            lines_out.append("</ul>")
            in_list = False

    def flush_table() -> None:
        nonlocal in_table
        if in_table:
            rows = [r for r in in_table if not re.match(r"^\s*\|[\s:|-]+\|\s*$", r)]
            out = ["<table>", ]
            for i, row in enumerate(rows):
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                tag = "th" if i == 0 else "td"
                out.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in cells) + "</tr>")
            out.append("</table>")
            lines_out.extend(out)
            in_table = []

    for raw in source.splitlines():
        line = raw.strip()
        if line.startswith("|"):
            flush_para()
            close_list()
            in_table.append(line)
            continue
        flush_table()
        if not line:
            flush_para()
            close_list()
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush_para()
            close_list()
            level = min(len(m.group(1)), 4)
            tag = "h2" if level <= 2 else f"h{min(level + 1, 6)}"
            lines_out.append(f"<{tag}>{inline(m.group(2))}</{tag}>")
        elif line.startswith("> "):
            flush_para()
            close_list()
            lines_out.append("<blockquote><p>" + inline(line[2:]) + "</p></blockquote>")
        elif re.match(r"^(-{3,}|\*{3,})$", line):
            flush_para()
            close_list()
            lines_out.append("<hr />")
        elif re.match(r"^[-*]\s+", line):
            flush_para()
            if not in_list:
                lines_out.append("<ul>")
                in_list = True
            lines_out.append("<li>" + inline(re.sub(r"^[-*]\s+", "", line)) + "</li>")
        elif re.match(r"^\d+\.\s+", line):
            flush_para()
            close_list()
            lines_out.append("<p>" + inline(line) + "</p>")
        else:
            close_list()
            paragraph.append(line)
    flush_table()
    flush_para()
    close_list()
    return "\n".join(lines_out)


# --------------------------------------------------------------------------
# parsowanie pliku markdown
# --------------------------------------------------------------------------

class Chapter:
    def __init__(self, number: str | None, title: str, body: list[str]):
        self.number = number          # np. "3" albo None (blok wprowadzający)
        self.title = title
        self.lines = body

    @property
    def text(self) -> str:
        return "\n".join(self.lines).strip() + "\n"

    @property
    def display_title(self) -> str:
        return f"{self.number}. {self.title}" if self.number else self.title


def parse_markdown(path: Path):
    """Zwraca (title, intro_lines, chapters, glossary_pairs, control_questions,
    problems, chapter_tree) gdzie chapter_tree = [(numer, tytul, [podtytule]), ...]."""
    lines = path.read_text(encoding="utf-8").splitlines()

    h1_idx = next((i for i, l in enumerate(lines) if l.startswith("# ")), 0)
    title = re.sub(r"^#\s*", "", lines[h1_idx]).strip()

    # nagłówki ## z numeracją
    h2 = [(i, m.group(1), m.group(2).strip())
          for i, l in enumerate(lines)
          if (m := re.match(r"^##\s+(\d+)\.\s+(.*)$", l))]

    chapters: list[Chapter] = []
    intro = lines[h1_idx + 1: h2[0][0]] if h2 else lines[h1_idx + 1:]
    for idx, (start, num, ctitle) in enumerate(h2):
        end = h2[idx + 1][0] if idx + 1 < len(h2) else len(lines)
        chapters.append(Chapter(num, ctitle, lines[start:end]))

    # struktura nagłówków do generatora prawda/fałsz
    tree = []
    for ch in chapters:
        subs = [re.sub(r"^###\s+", "", l).strip()
                for l in ch.lines if l.startswith("### ")]
        tree.append((ch.number, ch.title, subs))

    # sekcja „Pytania kontrolne…”
    quiz_chapter = next((c for c in chapters
                        if "Pytania kontrolne" in c.title), None)
    control: list[str] = []
    problems: list[str] = []
    glossary: list[tuple[str, str]] = []
    if quiz_chapter:
        mode = None
        buf: list[str] = []

        def dump() -> None:
            if buf and mode == "q":
                control.append(" ".join(buf).strip())
            elif buf and mode == "p":
                problems.append(" ".join(buf).strip())
            buf.clear()

        for l in quiz_chapter.lines:
            if l.startswith("### 20.1") or "Pytania sprawdzające" in l:
                dump(); mode = "q"; continue
            if l.startswith("### 20.2") or "Zadania problemowe" in l:
                dump(); mode = "p"; continue
            if l.startswith("## ") or l.startswith("### "):
                dump(); mode = None; continue
            if mode == "q" and (m := re.match(r"^\d+\.\s+(.+)$", l)):
                dump(); buf.append(m.group(1))
                continue
            if mode == "p" and (m := re.match(r"^\*\*Zadanie\s*\d+\.?\*\*\s*(.+)$", l)):
                dump(); buf.append(m.group(1))
                continue
            if mode in ("q", "p") and l.strip() and not l.startswith("---"):
                buf.append(l.strip())
                continue
            if mode is None and l.strip().startswith("|"):
                cells = [c.strip() for c in l.strip().strip("|").split("|")]
                if len(cells) >= 2 and not re.match(r"^[\s:-]+$", cells[0]) \
                        and cells[0] != "Pojęcie":
                    glossary.append((cells[0], cells[1]))
        dump()

    # słownik może być też poza rozdziałem pytań — przeszukaj cały plik
    if not glossary:
        for l in lines:
            if l.strip().startswith("|"):
                cells = [c.strip() for c in l.strip().strip("|").split("|")]
                if len(cells) >= 2 and not re.match(r"^[\s:-]+$", cells[0]) \
                        and cells[0] != "Pojęcie":
                    glossary.append((cells[0], cells[1]))

    return title, intro, chapters, quiz_chapter, glossary, control, problems, tree


# --------------------------------------------------------------------------
# budowa drzewa kursu w formacie repozytorium
# --------------------------------------------------------------------------

def write_tree(course_dir: Path, section_slug: str, book_slug: str, quiz_slug: str,
               title: str, intro: list[str], chapters: list[Chapter],
               quiz_chapter: Chapter | None, dry_run: bool) -> tuple[Path, Path]:
    sec_dir = course_dir / "sections" / section_slug
    book_dir = sec_dir / book_slug
    quiz_dir = sec_dir / quiz_slug
    chap_dir = book_dir / "chapters"
    if not dry_run:
        chap_dir.mkdir(parents=True, exist_ok=True)
        quiz_dir.mkdir(parents=True, exist_ok=True)

    # --- rozdziały książki ---
    files: list[tuple[str, str, str]] = []  # (plik, tytul, tresc)

    intro_body = "\n".join(intro).strip()
    first = f"01-{slugify(title, 40)}.md"
    files.append((first, title,
                  f"<!-- {GENERATED_MARK} -->\n\n{intro_body}\n"))

    for ch in chapters:
        if ch is quiz_chapter:
            continue
        n = int(ch.number)
        fname = f"{n:02d}-{slugify(ch.title, 40)}.md"
        body = ch.text
        # usuwa ewentualny wcześniejszy znacznik, dodaje własny
        body = re.sub(rf"<!-- {re.escape(GENERATED_MARK)} -->\n*", "", body)
        files.append((fname, ch.display_title,
                      f"<!-- {GENERATED_MARK} -->\n\n{body}"))

    # rozdziały z lukami numeracji (usunięty rozdział pytań) pomijamy —
    # numeracja plików odzwierciedla oryginalną numerację rozdziałów.

    if not dry_run:
        for fname, _, content in files:
            (chap_dir / fname).write_text(content, encoding="utf-8")

    # --- book.yaml ---
    chap_yaml = []
    for fname, ctitle, _ in files:
        chap_yaml.append(
            f'    - title: "{ctitle.replace(chr(34), "")}"\n'
            f"      subchapter: false\n"
            f'      content_file: "chapters/{fname}"\n'
            f"      hidden: false\n"
        )
    book_intro = ("Materiał dydaktyczny powstał z konwersji pliku Markdown "
                  f"„{title}” na aktywność typu book Moodle.")
    book_yaml = (
        "# Aktywność typu book — wygenerowana ze źródła Markdown\n"
        f"# {GENERATED_MARK}\n"
        "book:\n"
        f'  name: "{title}"\n'
        "  intro: |\n"
        f"    {book_intro}\n"
        "  intro_format: markdown\n"
        "  numbering: 1\n"
        "  customtitles: 0\n"
        "  revision: 1\n"
        "  chapters:\n" + "".join(chap_yaml)
    )
    if not dry_run:
        (book_dir / "book.yaml").write_text(book_yaml, encoding="utf-8")

    # --- quiz.yaml ---
    quiz_yaml = (
        "# Metadane quizu Moodle — wygenerowane ze źródła Markdown\n"
        f"# {GENERATED_MARK}\n"
        f'name: "Quiz: {title}"\n'
        "intro: |\n"
        f"  Sprawdzian wiedzy do rozdziału „{title}”.\n"
        "  Pytania obejmują zagadnienia omówione w rozdziałach książki oraz\n"
        "  słownik najważniejszych pojęć. Próg zaliczenia 60%, dwa podejścia.\n"
        "intro_format: markdown\n"
        "time_limit: 900\n"
        "attempts: 2\n"
        "grade_passing: 60\n"
        "shuffle_answers: 1\n"
        "questions_file: questions.gift\n"
        "completion:\n"
        "  enabled: true\n"
        "  type: grade\n"
        "  min_score: 60\n"
    )
    if not dry_run:
        (quiz_dir / "quiz.yaml").write_text(quiz_yaml, encoding="utf-8")

    # --- section.yaml ---
    section_name = title
    section_yaml = (
        "# Metadane sekcji kursu (Moodle) — wygenerowane ze źródła Markdown\n"
        f"# {GENERATED_MARK}\n"
        "id: 1\n"
        f'name: "{section_name}"\n'
        "visible: 1\n"
        "modules:\n"
        f"  - type: book\n    ref: {book_slug}\n    name: \"{title}\"\n"
        f"  - type: quiz\n    ref: {quiz_slug}\n    name: \"Quiz: {title}\"\n"
    )
    if not dry_run:
        (sec_dir / "section.yaml").write_text(section_yaml, encoding="utf-8")

    return book_dir, quiz_dir


# --------------------------------------------------------------------------
# generator pytań GIFT
# --------------------------------------------------------------------------

def build_gift(short: str, title: str, control: list[str], problems: list[str],
               glossary: list[tuple[str, str]], tree) -> str:
    out = [
        f"// Quiz: {title}",
        "// Format GIFT — składnia: docs/03-QUESTION-FORMATS.md",
        f"// {GENERATED_MARK}",
        "",
    ]
    qid = 0

    # A) pytania sprawdzające → shortanswer (klucz = pytanie bez znaku zapytania)
    for q in control:
        qid += 1
        stem = q.rstrip("?.").strip()
        key = stem[0].lower() + stem[1:] if stem else stem
        out.append(f"::{short}-sa{qid}:: {gift_escape(q)} {{SHORTANSWER:~{gift_escape(key)}}}")
        out.append("")

    # B) zadania problemowe → essay
    for i, p in enumerate(problems, 1):
        qid += 1
        out.append(f"::{short}-essay{i}:: {gift_escape(p)} {{#MANUAL}}")
        out.append("")

    # C) słownik → matching
    if len(glossary) >= 2:
        pairs = glossary[:20]
        left = "; ".join(t for t, _ in pairs)
        right = "; ".join(d for _, d in pairs)
        out.append(
            f"::{short}-match1:: Dopasuj pojęcia z słownika rozdziału do ich znaczeń."
            f" {{{right}\n"
            + "\n".join(f"-={gift_escape(d)}" for _, d in pairs)
            + "\n"
            + "\n".join(f"={gift_escape(t)}" for t, _ in pairs)
            + "}"
        )
        # standardowa składnia dopasowań GIFT: =lewa -> prawa
        out[-1] = (
            f"::{short}-match1:: Dopasuj pojęcia z słownika rozdziału do ich znaczeń. {{\n"
            + "\n".join(f"={gift_escape(t)}->{gift_escape(d)}" for t, d in pairs)
            + "\n}"
        )
        out.append("")

    # D) prawda/fałsz ze struktury nagłówków
    tf = 0
    for num, ctitle, subs in tree:
        if not subs:
            continue
        clean = re.sub(r"^\d+(\.\d+)*\.\s*", "", ctitle)
        for sub in subs:
            sub_clean = re.sub(r"^\d+(\.\d+)*\.\s*", "", sub)
            tf += 1
            out.append(
                f"::{short}-tf{tf}:: Podrozdział „{gift_escape(sub_clean)}” należy do "
                f"rozdziału „{gift_escape(clean)}” (rozdział {num}). {{TRUE}}"
            )
            tf += 1
            prev_num, prev_title, _ = tree[max(0, tree.index((num, ctitle, subs)) - 1)]
            prev_clean = re.sub(r"^\d+(\.\d+)*\.\s*", "", prev_title)
            if prev_num != num:
                out.append(
                    f"::{short}-tf{tf}:: Podrozdział „{gift_escape(sub_clean)}” należy do "
                    f"rozdziału „{gift_escape(prev_clean)}” (rozdział {prev_num}), a nie do "
                    f"rozdziału {num}. {{FALSE}}"
                )
            out.append("")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------
# eksport Moodle XML (.mbz) — backup kursu + bank pytań
# --------------------------------------------------------------------------

def moodle_xml_export(course_dir: Path, mbz_path: Path, *, shortname: str,
                      fullname: str, category: str = "$course$/badanie-neurologiczne"):
    from magic_moodle.gift import parse_gift, validate_question_bank
    from magic_moodle.moodle_xml import to_moodle_xml

    sections = sorted((course_dir / "sections").iterdir())
    root = ET.Element("moodle", version="2.0")
    info = ET.SubElement(root, "info", component="core_course", subplugin=None)
    details = ET.SubElement(info, "details")
    for el, val in (("name", fullname), ("shortname", shortname),
                    ("category", category), ("timemodified", "1730000000"),
                    ("language", "pl")):
        node = ET.SubElement(details, el)
        node.text = val

    cm_id = 1
    for si, sec in enumerate(sections):
        syml = (sec / "section.yaml")
        if not syml.is_file():
            continue
        sec_name = re.search(r'^name:\s*"?(.+?)"?$', syml.read_text(encoding="utf-8"), re.M)
        secnode = ET.SubElement(details, "section", id=str(si),
                                section="singlesection" if False else "week")
        ET.SubElement(secnode, "summary").text = ""
        ET.SubElement(secnode, "summaryformat").text = "1"
        ET.SubElement(secnode, "sequence").text = ""
        modul_nodes = []
        for mod in sorted(sec.iterdir()):
            book_yaml = mod / "book.yaml"
            quiz_yaml = mod / "quiz.yaml"
            if book_yaml.is_file():
                data = book_yaml.read_text(encoding="utf-8")
                bname = re.search(r'^\s*name:\s*"(.+)"', data, re.M).group(1)
                m = ET.Element("module", id=str(cm_id), modname="book",
                               meta="book", component="mod_book")
                cm = ET.SubElement(m, "cm_idnumber").text = ""
                ET.SubElement(m, "instance", id=str(cm_id)).text = ""
                ET.SubElement(m, "added").text = "1730000000"
                ET.SubElement(m, "title").text = bname
                content = ET.SubElement(m, "content")
                bookel = ET.SubElement(content, "book", mtime="1730000000")
                ET.SubElement(bookel, "course").text = "1"
                ET.SubElement(bookel, "name").text = bname
                ET.SubElement(bookel, "intro").text = ""
                ch_nodes = ET.SubElement(bookel, "chapter_count").text = "0"
                for cf in sorted((mod / "chapters").glob("*.md")):
                    chap = ET.SubElement(content, "chunks",
                                         subplugin="chapter",
                                         component="mod_book",
                                         itemtype="chapter_rel")
                    ET.SubElement(chap, "chapter", title=cf.stem).text = ""
                    inner = ET.SubElement(chap, "chunk")
                    ET.SubElement(inner, "content", format="1").text = \
                        md_to_html(cf.read_text(encoding="utf-8"))
                modul_nodes.append(m)
                cm_id += 1
            elif quiz_yaml.is_file():
                qdata = quiz_yaml.read_text(encoding="utf-8")
                qname = re.search(r'^name:\s*"(.+)"', qdata, re.M).group(1)
                m = ET.Element("module", id=str(cm_id), modname="quiz",
                               meta="quiz", component="mod_quiz")
                ET.SubElement(m, "instance", id=str(cm_id)).text = ""
                ET.SubElement(m, "title").text = qname
                content = ET.SubElement(m, "content")
                quizel = ET.SubElement(content, "quiz", mtime="1730000000")
                ET.SubElement(quizel, "course").text = "1"
                ET.SubElement(quizel, "name").text = qname
                ET.SubElement(quizel, "intro").text = ""
                ET.SubElement(quizel, "attempts").text = "2"
                ET.SubElement(quizel, "timeopen").text = "0"
                ET.SubElement(quizel, "timeclose").text = "0"
                ET.SubElement(quizel, "timelimit").text = "900"
                ET.SubElement(quizel, "grademethod").text = "1"
                modul_nodes.append(m)
                cm_id += 1
        for node in modul_nodes:
            secnode.append(node)
        details.append(secnode)

    # bank pytań
    gift_files = sorted((course_dir / "sections").rglob("questions.gift"))
    all_q = []
    for gf in gift_files:
        bank = parse_gift(gf.read_text(encoding="utf-8"), source_name=str(gf))
        errs = validate_question_bank(bank)
        if errs:
            raise SystemExit("Błędy GIFT: " + "; ".join(errs[:5]))
        all_q.append(bank)
    from magic_moodle.gift import QuestionBank
    merged = QuestionBank(tuple(q for b in all_q for q in b.questions), "merged")
    qxml = to_moodle_xml(merged, category="$course$/top")

    doc = '<?xml version="1.0" encoding="UTF-8"?>\n' + \
          ET.tostring(root, encoding="unicode")
    mbz_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(mbz_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("moodle_backup.xml", doc)
        zf.writestr("questions.xml", qxml)
    return mbz_path, len(merged.questions)


# --------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--course-dir", required=True, type=Path)
    ap.add_argument("--section", default=None, help="slug sekcji (domyślnie z numeru rozdziału)")
    ap.add_argument("--mbz", type=Path, default=None, help="ścieżka wyjściowa pliku .mbz")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    src: Path = args.source
    course_dir: Path = args.course_dir
    title, intro, chapters, quiz_chapter, glossary, control, problems, tree = \
        parse_markdown(src)

    num = re.match(r"^(\d+)\.(\d+)", title)
    short = f"bn{num.group(1)}{num.group(2)}" if num else slugify(title, 12)
    book_slug = f"book-{short}-{slugify(re.sub(r'^\d+\.\d+\.?\s*', '', title), 40)}"
    quiz_slug = f"quiz-{short}"
    section_slug = args.section or f"{(num.group(1) if num else '01')}-{slugify(title, 40)}"

    print(f"Tytuł: {title}")
    print(f"Rozdziały książki: {len(chapters) - (1 if quiz_chapter else 0)}"
          f" (+ blok wprowadzający), pytania: {len(control)} SA, "
          f"{len(problems)} opisowe, {len(glossary)} par słownika, "
          f"P/F ze struktury: ~{sum(len(s) for _, _, s in tree)}")

    book_dir, quiz_dir = write_tree(course_dir, section_slug, book_slug, quiz_slug,
                                    title, intro, chapters, quiz_chapter, args.dry_run)

    gift_text = build_gift(short, title, control, problems, glossary, tree)
    if not args.dry_run:
        (quiz_dir / "questions.gift").write_text(gift_text, encoding="utf-8")
        print(f"Zapisano: {book_dir}, {quiz_dir}/questions.gift")

    # course.yaml — uzupełnij jeśli brak (nigdy nie nadpisuj istniejącego)
    cy = course_dir / "course.yaml"
    if not cy.exists() and not args.dry_run:
        cy.write_text(
            "# Metadane kursu Moodle — uzupełnione przez skrypt konwersji\n"
            "format_version: \"1.0\"\ncourse:\n"
            "  full_name: \"Badanie neurologiczne pacjenta\"\n"
            "  short_name: \"BN-NEURO-2026\"\n"
            "  category: \"Kursy medyczne\"\n"
            "  visible: 1\n  format: \"topics\"\n  lang: \"pl\"\n"
            "  show_grades: 1\n  news_items: 3\n"
            "description:\n  format: \"markdown\"\n  markdown_file: \"course.md\"\n",
            encoding="utf-8")
        print(f"Utworzono: {cy}")

    if args.mbz:
        if args.dry_run:
            print(f"(dry-run) pominiano pakowanie {args.mbz}")
        else:
            path, nq = moodle_xml_export(course_dir, args.mbz,
                                         shortname="BN-NEURO-2026",
                                         fullname="Badanie neurologiczne pacjenta")
            print(f"Upakowano {path} ({nq} pytań w banku)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
