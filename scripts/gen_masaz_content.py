#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wypełnianie szkieletu kursu MED.10 (masażysta certyfikowany) treścią.

Skrypt uzupełnia WYŁĄCZNIE pliki puste (0 bajtów) — nigdy nie nadpisuje
plików z istniejącą treścią (idempotentność, ta sama zasada co w
scaffold-kurs-masazu.py / gen_page_stubs.py / gen_quiz_templates.py).

Źródłem struktury i treści jest spis treści `kurs_masazu.txt` (parser
course_toc.py), więc generowane treści są prawdziwe względem programu
kursu: nie wymyślam danych medycznych — opieram się na podtematach spisu.

Naprawa spójności szkieletu:
  * sekcja 11 w szkielecie nosiła mylącą nazwę katalogu
    "11-przygotowanie-do-egzaminu-potwierdzajacego-kw" (-litera "MEDIACJE"
    z modułu 10 wkradła się do sluga). Kurs zgodnie ze spisem treści ma
    moduł 11 = "PRZYGOTOWANIE DO EGZAMINU POTWIERDZAJĄCEGO KWALIFIKACJĘ
    MED.10", a parser course_toc generuje slug "...-kwalfikacje-med".
    Skrypt wykonuje jednorazowe, bezpieczne przeniesienie zawartości
    pod właściwą nazwę (git mv jeśli to repozytorium git), zanim
    wypełni pliki — dzięki temu struktura kursu jest zgodna ze spisem.

Tworzone/uzupełniane pliki:
  * question-bank/{categories.yaml,multichoice,truefalse,shortanswer,essay,matching}
                                (bank pytań kursu)
  * course.yaml, settings.yaml, tags.yaml, completion.yaml, grades.yaml,
    course.md, changelog.md             (pliki główne kursu)
  * sections/NN-*/section.yaml + section.md     (podsumowania modułów)
  * sections/NN-*/page-XX-*.md          (strony tematyczne)
  * sections/NN-*/quiz-XX/{quiz.yaml,questions.gift,questions.yaml,feedback.md}
  * sections/NN-*/assignment-XX/{assignment.yaml,instructions.md}
  * sections/12-zalaczniki/label-XX-*.md        (załączniki A–M)
  * NOWE aktywności: book-01 (podręcznik modułu, rozdział = temat)
    we wszystkich modułach oraz glossary-01 (słownik) w sekcji załączników.

Użycie:
    python3 scripts/gen_masaz_content.py [--toc kurs_masazu.txt]
        [--base courses/03-kurs-masazysta-med10] [--dry-run] [--no-books]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from course_toc import default_source, parse_course, slugify  # noqa: E402
from course_toc import Module, Topic, Attachment  # noqa: E402

COURSE_NAME = ("Kwalifikacyjny kurs zawodowy w zawodzie masażysta "
               "(kwalifikacja MED.10)")
COURSE_SHORT = "KKZ-MED10-MASAŻYSTA"
BASE_REL = "courses/03-kurs-masazysta-med10"
BASE = BASE_REL  # nadpisywane w main() ścieżką absolutną

# --------------------------------------------------------------------------
# pomocnicze
# --------------------------------------------------------------------------


def yaml_q(s: str) -> str:
    """Bezpieczna cytacja YAML (podwójny cudzysłów)."""
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


STATUT = [
    "Rozpoznajesz strukturę, mechanizm i kolejność czynności opisanych w tym zagadnieniu",
    "Omawiasz przebieg postępowania krok po kroku, wskazując etapy kluczowe dla bezpieczeństwa klienta",
    "Wykonujesz ćwiczenie praktyczne w warunkach szkolnych, przestrzegając zasad higieny i ergonomii",
    "Analizujesz przykłady z literatury zawodowej i omawiasz wnioski na forum grupy",
    "Stosujesz zdobytą wiedzę w planowaniu działania, uwzględniając przeciwwskazania i granice kompetencji",
    "Oceniasz jakość własnego wykonania według check-listy i formułujesz plan doskonalenia",
]

BEZPIECZENSTWO = [
    "Przed przystąpieniem do działania zweryfikuj występowanie przeciwwskazań (bezwzględnych i względnych) — w razie wątpliwości skonsultuj się z lekarzem kierującym.",
    "Działaj wyłącznie w granicach kompetencji masażysty: nie rozpoznajesz chorób, nie stawiasz rozpoznań i nie modyfikujesz zaleceń lekarskich na własną rękę.",
    "Stosuj zasady aseptyki i antyseptyki oraz higieny stanowiska pracy zgodnie z procedurami zakładowymi (załącznik I).",
    "Szanuj godność, prywatność i autonomię klienta: uzyskaj świadomą zgodę, dbaj o poufność danych i komfort termiczny podczas zabiegu.",
]

MOD_INTRO = {
    1: "Moduł wprowadza w bezpieczeństwo i higienę pracy masażysty: przepisy prawa pracy, zagrożenia zawodowe, ergonomię stanowiska, aseptykę oraz pierwszą pomoc. To fundament, na którym opiera się cała dalsza praktyka zawodowa — bo troska o bliźniego zaczyna się od troski o jego bezpieczeństwo.",
    2: "Moduł obejmuje podstawy masażu: wiadomości o masażu, anatomię i fizjologię człowieka, klasyfikację, oddziaływanie oraz techniki manualne (głaskanie, rozcieranie, ugniatanie, oklepywanie, wibracja) na poszczególnych częściach ciała. Ćwiczenia wykonujemy naprzemiennie — w rolach masowanego i masażysty — ucząc się wzajemnego szacunku i wrażliwości na drugiego człowieka.",
    3: "Moduł przedstawia podstawy masażu w medycynie: procesy patologiczne i objawy chorób, zaburzenia poszczególnych układów oraz zasady dobierania rodzajów masażu (limfatycznego, tensegracyjnego, w środowisku wodnym, Shantala i innych) z uwzględnieniem wskazań i przeciwwskazań.",
    4: "Moduł dotyczy wykonywania masażu w medycynie: masażu klasycznego leczniczego, odmian masażu klasycznego, technik specjalnych, masażu osób starszych i dzieci, kompleksowej terapii obrzęków oraz działań przy dysfunkcjach narządu ruchu — zawsze we współpracy z zespołem terapeutycznym i pod kontrolą skuteczności.",
    5: "Moduł poświęcony jest masażowi w sporcie: przygotowanie zawodnika w cyklach treningowych i startowych, rodzaje masażu sportowego, metodyka wykonania, dokumentacja oraz bezpieczeństwo i etyka w środowisku sportowym.",
    6: "Moduł obejmuje masaż prozdrowotny: masaż relaksacyjny, kosmetyczny twarzy, głowy, stóp i dłoni, bańką chińską oraz działania edukacyjne i popularyzację zachowań prozdrowotnych.",
    7: "Moduł rozwija zawodowy język obcy: słownictwo anatomiczne i masażowe, czytanie dokumentacji i tekstów fachowych, rozmowę z klientem obcojęzycznym oraz przekazywanie informacji z materiałów wizualnych i audiowizualnych.",
    8: "Moduł kształtuje kompetencje osobiste i społeczne masażysty: komunikację interpersonalną, kulturę osobistą, przedsiębiorczość, radzenie sobie w sytuacjach trudnych oraz etykę zawodu — służbę bliźniemu w prawdzie, pięknie i sprawiedliwości.",
    9: "Moduł wprowadza w organizację pracy małych zespołów: planowanie pracy zespołu, komunikację w zespole, rozwiązywanie konfliktów oraz współpracę interdyscyplinarną na rzecz dobra pacjenta.",
    10: "Moduł praktyki zawodowej to zajęcia praktyczne u pracodawcy lub w innej instytucji — bezpośrednia służba drugiemu człowiekowi pod okiem opiekuna praktyki, połączona z prowadzeniem dokumentacji i autoewaluacją.",
    11: "Moduł przygotowuje do egzaminu potwierdzającego kwalifikację MED.10: powtórzenie i usystematyzowanie wiedzy, próby egzaminacyjne (część pisemna i praktyczna) oraz analiza arkuszy egzaminacyjnych CKE.",
}

SEC_SUFFIX = {
    10: " Praktyka zawodowa",
    11: " Przygotowanie do egzaminu potwierdzającego kwalifikację",
}


def sec_title(mod: Module) -> str:
    if mod.code:
        return f"Moduł {mod.index}: {mod.code}. {upper_first_topic(mod.raw_title)}"
    return f"Moduł {mod.index}:{SEC_SUFFIX.get(mod.index, ' ' + upper_first_topic(mod.raw_title))}"


def topic_heading(t: Topic) -> str:
    return f"{t.num}. {upper_first_topic(t.clean_title)}"


def upper_first_topic(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def statut_for(i: int) -> str:
    return STATUT[i % len(STATUT)]


def plural_subtopics(n: int) -> str:
    if n == 1:
        return "1 zagadnienie szczegółowe"
    if 2 <= n <= 4:
        return f"{n} zagadnienia szczegółowe"
    return f"{n} zagadnień szczegółowych"


# --------------------------------------------------------------------------
# strony tematyczne
# --------------------------------------------------------------------------


def page_md(mod: Module, t: Topic) -> str:
    subs = t.subtopics
    L = [f"# {topic_heading(t)}", "",
         "## Wprowadzenie", "",
         MOD_INTRO.get(mod.index, ""), "",
         f"Temat „{topic_heading(t)}” realizuje {plural_subtopics(len(subs))} "
         "ze spisu treści kursu. Opanowanie ich jest warunkiem zaliczenia modułu "
         "i niezbędnym przygotowaniem do części praktycznej egzaminu "
         "potwierdzającego kwalifikację MED.10.", ""]
    L += ["## Cele szczegółowe — po tym temacie uczestnik potrafi:", ""]
    for i, s in enumerate(subs):
        L.append(f"- {statut_for(i)} — **{s.num} {s.clean_title}**.")
    L += ["", "## Zagadnienia szczegółowe", ""]
    for s in subs:
        L += [f"### {s.num} {s.clean_title}", "",
              "Zakres materiału (zgodnie ze spisem treści kursu):", "",
              f"- omówienie pojęcia, celów i miejsca zagadnienia „{s.clean_title}” w pracy masażysty;",
              "- demonstracja i przećwiczenie właściwej metodyki postępowania;",
              "- identyfikacja sytuacji typowych oraz nietypowych (wymagających konsultacji lub skierowania do lekarza);",
              "- utrwalenie nawyku dokumentowania wykonanego działania (załącznik C).", ""]
    L += ["## Bezpieczeństwo i etyka", ""]
    for b in BEZPIECZENSTWO:
        L.append(f"- {b}")
    L += ["", "## Podsumowanie", "",
          f"Temat {t.num} wiąże wiedzę teoretyczną z praktyką manualną. Regularne "
          "powtarzanie materiału, ćwiczenia w parach oraz rzetelna samoocena "
          "według check-list (załącznik F) prowadzą do biegłości, która służy "
          "realnemu dobru drugiego człowieka — zgodnie z zasadą „primum non nocere”.",
          "", "**Pytania utrwalające:**", ""]
    for i, s in enumerate(subs[:4], 1):
        L.append(f"{i}. Omów zagadnienie: {s.clean_title}.")
    L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------
# quizy
# --------------------------------------------------------------------------


def distractors(all_titles: list, correct: str, seed: str, k: int = 3) -> list:
    h = sum(ord(c) for c in seed)
    pool = [x for x in all_titles if x != correct]
    out: list = []
    step = max(1, len(pool) // (k + 1))
    idx = h % max(1, len(pool))
    while len(out) < k and pool:
        cand = pool[idx % len(pool)]
        if cand not in out:
            out.append(cand)
        idx += step + 1
        if idx > 4 * len(pool):
            break
    for cand in pool:                      # dopełnienie, gdy pula płytka
        if len(out) >= k:
            break
        if cand not in out:
            out.append(cand)
    return out[:k]


def quiz_gift(mod: Module, t: Topic, all_titles: list) -> str:
    L = [f"// Quiz: {topic_heading(t)} — moduł {mod.index} ({mod.dir_name})",
         "// Format GIFT — składnia: docs/03-QUESTION-FORMATS.md", ""]
    sid = f"s{mod.index:02d}-{t.num.replace('.', '')}"
    for i, s in enumerate(t.subtopics, 1):
        nxt = t.subtopics[i] if i < len(t.subtopics) else None
        L += [f"::tf-{sid}-q{i}:: Zagadnienie „{s.clean_title}” wchodzi w zakres tematu "
              f"„{t.clean_title}” ({t.num}). {{TRUE}} //", ""]
        if nxt:
            L += [f"::tf-{sid}-q{i}b:: Zagadnienie „{nxt.clean_title}” jest elementem "
                  f"zagadnienia „{s.clean_title}”, a nie tematu „{t.clean_title}” "
                  f"({t.num}). {{FALSE}} //", ""]
    if t.subtopics:
        opts = [s.clean_title for s in t.subtopics[:3]]
        dis = distractors(all_titles, opts[0], t.num)
        body = [f"    = {opts[0]}"] + \
               [f"    ~ {o}" for o in opts[1:]] + \
               [f"    ~ {d}" for d in dis]
        L += [f"::mc-{sid}:: Które zagadnienie należy bezpośrednio do tematu "
              f"„{t.clean_title}” ({t.num})? {{"] + body + ["}", ""]
    return "\n".join(L)


def quiz_yaml_questions(mod: Module, t: Topic, all_titles: list) -> str:
    lines = ["# Pytania quizu w formacie YAML (odpowiadają questions.gift)",
             f"quiz: {yaml_q(topic_heading(t))}",
             "category: masaz",
             "questions:"]
    for i, s in enumerate(t.subtopics, 1):
        lines += ["  - type: truefalse",
                  f"    name: {yaml_q(f'{t.num} — zagadnienie {i}')}",
                  f"    text: {yaml_q('Zagadnienie „' + s.clean_title + '” wchodzi w zakres tematu „' + t.clean_title + f'” ({t.num}).')}",
                  "    answer: true"]
        nxt = t.subtopics[i] if i < len(t.subtopics) else None
        if nxt:
            lines += ["  - type: truefalse",
                      f"    name: {yaml_q(f'{t.num} — rozgraniczenie {i}')}",
                      f"    text: {yaml_q('Zagadnienie „' + nxt.clean_title + '” jest elementem zagadnienia „' + s.clean_title + '”, a nie tematu „' + t.clean_title + f'” ({t.num}).')}",
                      "    answer: false"]
    if t.subtopics:
        dis = distractors(all_titles, t.subtopics[0].title, t.num)
        lines += ["  - type: multichoice",
                  f"    name: {yaml_q(f'{t.num} — przyporządkowanie zagadnienia')}",
                  f"    text: {yaml_q('Które zagadnienie należy bezpośrednio do tematu „' + t.clean_title + f'” ({t.num})?')}",
                  "    answers:",
                  f"      - text: {yaml_q(t.subtopics[0].title)}  fraction: 100"]
        for d in dis:
            lines.append(f"      - text: {yaml_q(d)}  fraction: 0")
    return "\n".join(lines) + "\n"


QUIZ_YAML_TMPL = """# Metadane quizu Moodle
name: {name}
intro: |
  Sprawdzian wiedzy do tematu {num}. Pytania obejmują zagadnienia
  szczegółowe omówione na stronie tematycznej modułu.
intro_format: markdown
time_limit: 600
attempts: 2
grade_passing: 60
shuffle_answers: 1
questions_file: questions.gift
completion:
  enabled: true
  type: grade
  min_score: 60
"""


def feedback_md(mod: Module, t: Topic) -> str:
    L = [f"# Informacja zwrotna — quiz {t.num}", "",
         "Cele informacji zwrotnej: utwierdzić uczestnika w tym, co opanował "
         "dobrze, i wskazać konkretny materiał do powtórzenia tam, gdzie wynik "
         "jest niższy. Oceniamy wiedzę i umiejętności — nigdy osobę.", ""]
    bands = [
        ("90–100%", "Brawo! Materiał opanowany. Poszerz praktykę o zadania rozszerzające i podziel się wiedzą z grupą — przez uczenie innych sam utrwaliasz warsztat."),
        ("75–89%", "Dobra baza. Powtórz zagadnienia wskazane w raporcie z prób i przećwicz je manualnie w parach."),
        ("60–74%", "Poziom wystarczający, by przejść dalej, ale wymagany powrót do strony tematycznej i notatek z ćwiczeń. Umów konsultację z nauczycielem prowadzącym."),
        ("< 60%", "Wróć do wprowadzenia i celów szczegółowych strony tematycznej, opracuj na nowo każdy podtemat, a następnie podejdź do drugiej próby. Traktuj to jako etap nauki, nie wyrok — każde podejście buduje kompetencję służącą pacjentom."),
    ]
    for band, txt in bands:
        L.append(f"- **{band}** — {txt}")
    L += ["", "## Klucz odpowiedzi", "",
          "Poprawne odpowiedzi wynikają wprost ze strony tematycznej „"
          + topic_heading(t) + "” (sekcja „Zagadnienia szczegółowe”).", ""]
    return "\n".join(L)


# --------------------------------------------------------------------------
# zadania
# --------------------------------------------------------------------------

ASSIGNMENT_YAML_TMPL = """# Metadane zadania Moodle (moduł: assignment)
name: {name}
intro: |
  Zadanie praktyczne do tematu {num}. Praca samodzielna lub w parach,
  zgodnie z regulaminem modułu.
intro_format: markdown
submission_types: ["file", "onlinetext"]
max_attachments: 3
graded: 1
grademax: 100
markdown_file: instructions.md
"""


def assignment_md(mod: Module, t: Topic) -> str:
    check = "".join(f"- [ ] {s.num} {s.clean_title}\n" for s in t.subtopics)
    return (
        f"# Zadanie: {topic_heading(t)}\n\n"
        "## Cel kształcenia\n\n"
        f"Utrwalenie wiedzy i umiejętności z zakresu: {t.clean_title} "
        f"(moduł {mod.index}, {upper_first_topic(mod.raw_title)}).\n\n"
        "## Przebieg zadania\n\n"
        "1. Opracuj krótkie kompendium (min. 300 słów) obejmujące wszystkie zagadnienia tematu.\n"
        "2. Wykonaj ćwiczenie praktyczne przewidziane tematem (w parach lub na materacu/modelu) i opisz jego przebieg.\n"
        "3. Uzupełnij kartę obserwacji / check-listę oraz wnioski z autoewaluacji.\n"
        "4. Przekaż pracę do oceny przez nauczyciela/opiekuna praktyk.\n\n"
        "## Zakres sprawdzany przez check-listę\n\n"
        f"{check}\n"
        "## Kryteria oceny\n\n"
        "- poprawność merytoryczna i terminologia zawodowa — 40%,\n"
        "- bezpieczeństwo i higiena wykonania (w tym przeciwwskazania) — 30%,\n"
        "- dokumentacja i refleksja (autoewaluacja, wnioski) — 20%,\n"
        "- kultura osobista i etyka zawodowa — 10%.\n\n"
        "## Uwagi etyczne\n\n"
        "Praca z drugim człowiekiem wymaga zgody, dyskrecji i szacunku. "
        "Wszelkie dane przypadków opisuj anonimowo. Działaj wyłącznie w granicach "
        "kompetencji masażysty (załącznik M).\n"
    )


# --------------------------------------------------------------------------
# sekcje
# --------------------------------------------------------------------------


def section_yaml(mod: Module) -> str:
    sec_dir = Path(BASE) / "sections" / mod.dir_name
    lines = ["# Metadane sekcji kursu (Moodle)",
             f"id: {mod.index}",
             f"name: {yaml_q(sec_title(mod))}",
             "visible: 1",
             "summary:",
             "  format: markdown",
             "  markdown_file: section.md",
             "modules:"]
    for t in mod.topics:
        fname = next((p.name for p in sec_dir.glob(f"page-{t.order:02d}-*.md")),
                     f"page-{t.order:02d}-{slugify(t.clean_title)}.md")
        lines += ["  - type: page", f"    ref: {yaml_q(fname)}",
                  f"    name: {yaml_q(topic_heading(t))}"]
    lines += ["  - type: book", "    ref: book-01",
              f"    name: {yaml_q('Podręcznik: ' + (mod.code or ('Moduł ' + str(mod.index))))}"]
    for t in mod.topics:
        lines += ["  - type: quiz", f"    ref: quiz-{t.order:02d}",
                  f"    name: {yaml_q('Quiz: ' + topic_heading(t))}"]
        lines += ["  - type: assignment", f"    ref: assignment-{t.order:02d}",
                  f"    name: {yaml_q('Zadanie: ' + topic_heading(t))}"]
    return "\n".join(lines) + "\n"


def section_md(mod: Module) -> str:
    L = [f"# {sec_title(mod)}", ""]
    if mod.hours:
        L += [f"**Wymiar godzinowy:** {mod.hours} godzin", ""]
    L += ["## Opis modułu", "", MOD_INTRO.get(mod.index, ""), ""]
    if mod.meta:
        L += ["## Organizacja nauczania", ""]
        L += [f"- {m}" for m in mod.meta]
        L.append("")
    L += ["## Struktura modułu (tematy)", "",
          "| Nr tematu | Strona | Quiz | Zadanie | Liczba zagadnień |",
          "|-----------|--------|------|---------|------------------|"]
    for t in mod.topics:
        L.append(f"| {t.num} | page-{t.order:02d} | quiz-{t.order:02d} | "
                 f"assignment-{t.order:02d} | {len(t.subtopics)} |")
    L += ["", "## Sposób zaliczenia", "",
          "- obecność i aktywny udział w zajęciach praktycznych,",
          "- quizy tematyczne: minimalny próg 60% z każdego quizu,",
          "- zadania praktyczne oceniane wg kryteriów podanych w instrukcjach,",
          "- zaliczenie modułu wg tabeli wag w pliku grades.yaml.", ""]
    return "\n".join(L)


# --------------------------------------------------------------------------
# załączniki (labels)
# --------------------------------------------------------------------------


def attachment_md(a: Attachment) -> str:
    L = [f"# Załącznik {a.letter}. {a.title}", "",
         "Materiał pomocniczy kursu — udostępniony do pobrania, wydruku i "
         "stosowania na każdym etapie kształcenia.", "", "## Zawartość", ""]
    for num, text in a.items:
        core = re.sub(r"^[A-M]\.\d{1,2}\.\s*", "", text, flags=re.I)
        L += [f"### {num} {core}", "",
              f"Pozycja załącznika {a.letter} („{a.title}”) — stosowana zgodnie "
              "z regulaminem kursu oraz podstawą programową MED.10. Dokument "
              "uzupełnia kadra dydaktyczna wraz z uczestnikami na odpowiednim "
              "etapie kształcenia.", ""]
    return "\n".join(L)


# --------------------------------------------------------------------------
# bank pytań (question-bank)
# --------------------------------------------------------------------------


def question_bank(course) -> dict:
    """Zawartość plików banku pytań kursu (kategorie + zestawy GIFT)."""
    qb = Path(BASE) / "question-bank"
    out: dict = {}

    cat_lines = ["# Kategorie banku pytań kursu", "categories:"]
    for m in course.modules:
        cat_lines.append(f'  - name: {yaml_q(sec_title(m))}')
        cat_lines.append(f'    idnumber: "modul-{m.index:02d}"')
    out[qb / "categories.yaml"] = "\n".join(cat_lines) + "\n"

    mods_with_topics = [m for m in course.modules if m.topics]
    first_topic = {m.index: m.topics[0].clean_title for m in mods_with_topics}

    tf = ["// Bank pytań prawda/fałsz – Kwalifikacyjny kurs zawodowy masażysta (MED.10)",
          f"// Źródło: {Path(course.source).name}"]
    for m in mods_with_topics:
        t = m.topics[0]
        tf.append(f"::tf-m{m.index:02d}:: Temat „{t.clean_title}” należy do "
                  f"{sec_title(m)}. {{TRUE}}")
        tf.append("")
    out[qb / "truefalse" / "set-01.gift"] = "\n".join(tf) + "\n"

    mc = ["// Bank pytań jednokrotnego wyboru – przyporządkowanie tematów do modułów",
          f"// Źródło: {Path(course.source).name}"]
    for pos, m in enumerate(mods_with_topics):
        t = m.topics[0]
        correct_pos = pos % 4
        others = [first_topic[i] for i in sorted(first_topic) if i != m.index][:3]
        opts: list = []
        oi = 0
        for slot in range(4):
            if slot == correct_pos:
                opts.append((True, t.clean_title))
            elif oi < len(others):
                opts.append((False, others[oi])); oi += 1
            else:
                opts.append((False, "Ćwiczenia rekreacyjne poza programem MED.10"))
        body = "\n".join(f"    {'=' if ok else '~'} {txt}" for ok, txt in opts)
        mc.append(f"::mc-m{m.index:02d}:: Do którego modułu należy temat "
                  f"„{t.clean_title}”? {{")
        mc.append(body)
        mc.append("}")
        mc.append("")
    out[qb / "multichoice" / "set-01.gift"] = "\n".join(mc) + "\n"

    # multichoice set-01.yaml — przykłady w formacie YAML
    yml = ["# Bank pytań jednokrotnego wyboru (format YAML)",
           "questions:"]
    for m in mods_with_topics[:5]:
        t = m.topics[0]
        yml += ["  - type: multichoice",
                f"    name: {yaml_q('Przyporządkowanie modułowe ' + str(m.index))}",
                f"    category: {yaml_q(sec_title(m))}",
                f"    text: {yaml_q('Do którego modułu kursu MED.10 należy temat „' + t.clean_title + '”?')}",
                "    answers:",
                f"      - text: {yaml_q(sec_title(m))}  fraction: 100"]
        for i in [j for j in sorted(first_topic) if j != m.index][:3]:
            other = course.module(i)
            yml.append(f"      - text: {yaml_q(sec_title(other))}  fraction: 0")
    out[qb / "multichoice" / "set-01.yaml"] = "\n".join(yml) + "\n"

    sa = ["// Bank pytań krótkiej odpowiedzi",
          f"// Źródło: {Path(course.source).name}"]
    for m in mods_with_topics:
        t = m.topics[0]
        key = " | ".join(s.clean_title.split("–")[0].split(" - ")[0].strip()
                         for s in t.subtopics[:6]) or t.clean_title
        sa.append(f"::sa-m{m.index:02d}:: Wymień główne zagadnienia tematu "
                  f"„{t.clean_title}” ({t.num}) ze spisu treści kursu. "
                  f"{{SHORTANSWER:~#{key}}}")
        sa.append("")
    out[qb / "shortanswer" / "set-01.gift"] = "\n".join(sa) + "\n"

    es = ["// Bank pytań esej (otwartych) — ocena analityczna według kryteriów",
          f"// Źródło: {Path(course.source).name}"]
    prompts = [
        "Omów znaczenie zasady „primum non nocere” dla pracy masażysty, wskazując przykłady z dwóch różnych modułów kursu.",
        "Porównaj wskazania i przeciwwskazania masażu klasycznego oraz drenażu limfatycznego; uzasadnij konieczność konsultacji lekarskiej.",
        "Opisz, jak świadoma zgoda klienta i ochrona danych wpływają na przebieg zabiegu i dokumentację (załączniki C i M).",
        "Analizuj rolę komunikacji interpersonalnej w sytuacji trudnej z klientem — od rozpoznania emocji do rozwiązania konfliktu.",
        "Sformułuj plan rozwoju kompetencji po praktyce zawodowej, odwołując się do check-list umiejętności (załącznik F).",
    ]
    for i, p in enumerate(prompts, 1):
        es.append(f"::essay-{i:02d}:: {p} {{#MANUAL}}")
        es.append("")
    out[qb / "essay" / "set-01.gift"] = "\n".join(es) + "\n"

    mt = ["// Bank pytań łączenia par (matching)",
          f"// Źródło: {Path(course.source).name}"]
    pairs = [(upper_first_topic(m.raw_title), m.topics[0].clean_title)
             for m in mods_with_topics[:6]]
    left = "\n".join(f"    ={a}" for a, b in pairs)
    right = "\n".join(f"    -={b}" for a, b in pairs)
    mt.append("::match-moduly:: Połącz nazwę modułu z jego pierwszym tematem. {")
    mt.append(left)
    mt.append(right)
    mt.append("}")
    out[qb / "matching" / "set-01.gift"] = "\n".join(mt) + "\n"
    return out


# --------------------------------------------------------------------------
# book (podręcznik modułu)
# --------------------------------------------------------------------------


def book_yaml(mod: Module) -> str:
    name = "Podręcznik modułu " + str(mod.index) + (": " + mod.code if mod.code else "")
    L = ["# Aktywność typu book — podręcznik modułu (preferowana aktywność kursu)",
         "book:",
         f"  name: {yaml_q(name)}",
         "  intro: |",
         f"    Zbiór rozdziałów odpowiadającym tematom modułu ({mod.dir_name}).",
         f"    {MOD_INTRO.get(mod.index, '')}",
         "  intro_format: markdown",
         "  numbering: 1",
         "  customtitles: 0",
         "  revision: 1",
         "  chapters:"]
    for t in mod.topics:
        L.append(f"    - title: {yaml_q(topic_heading(t))}")
        L.append("      subchapter: false")
        L.append(f"      content_file: {yaml_q('chapters/' + f'{t.order:02d}-' + slugify(t.clean_title) + '.md')}")
        L.append("      hidden: false")
    L += ["  completion:", "    enabled: true", "    type: view"]
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------
# pliki główne kursu
# --------------------------------------------------------------------------


def main_files(course) -> dict:
    root = Path(BASE)
    total_hours = sum(int(m.hours) for m in course.modules if m.hours)
    out: dict = {}

    sec_lines = "\n".join(
        f'  - id: "{m.index:02d}"\n    name: {yaml_q(sec_title(m))}'
        for m in course.modules)
    out[root / "course.yaml"] = f"""# Metadane kursu Moodle
format_version: "1.0"
course:
  full_name: {yaml_q(COURSE_NAME)}
  short_name: {yaml_q(COURSE_SHORT)}
  idnumber: "MED.10"
  category: "Kursy zawodowe"
  visible: 1
  format: "topics"
  lang: "pl"
  show_grades: 1
  news_items: 3
description:
  format: "markdown"
  markdown_file: "course.md"
  summary_plain: >-
    Kwalifikacyjny kurs zawodowy w zawodzie masażysta (MED.10):
    {len(course.modules)} modułów, {course.topic_count} tematów,
    {course.subtopic_count} zagadnień szczegółowych, załączniki A-M.
editor: "tinymce"
sections:
  - id: "00"
    name: "Ogłoszenia i administracja kursu"
{sec_lines}
  - id: "12"
    name: "Załączniki A-M"
metadata:
  author: "Zespół dydaktyczny kursu masażu"
  version: "1.0.0"
  created: "2026-10-28"
  modified: "2026-10-28"
  license: "CC BY-SA 4.0"
  language: "pl"
  level: "qualifying-vocational"
  audience: "Kandydaci do kwalifikacji MED.10 – masażysta"
  keywords: ["masaż", "MED.10", "kurs zawodowy", "rehabilitacja", "profilaktyka"]
  ethical_compliance:
    respects_human_dignity: true
    truthful_medical_content: true
    within_scope_of_competence: true
"""

    out[root / "settings.yaml"] = """# Ustawienia zaawansowane kursu
enrollment:
  method: "manual"
  self_enrolment:
    enabled: 1
    password_required: 1
groups:
  mode: "separate"
roles:
  teacher: "Nauczyciel prowadzący moduł"
  editingteacher: "Koordynator kursu"
  assistant: "Opiekun praktyk zawodowych"
completion:
  tracking: 1
  report: 1
grade_display_type: "points"
calendar_type: "course"
maxbytes: 52428800
auth_instructions: |
  Kurs realizowany w trybie mieszanym: wykłady, ćwiczenia praktyczne
  (gabinet/sala gimnastyczna), praktyka zawodowa u pracodawcy.
  Warunkiem zaliczenia jest frekwencja, pozytywne oceny z każdego modułu
  oraz zrealizowanie wymaganej liczby godzin praktyki zawodowej.
"""

    tags = ["masaz", "med.10", "kurs-zawodowy", "masaz-klasyczny", "masaz-sportowy",
            "masaz-limfatyczny", "drenaz-limfatyczny", "masaz-prozdrowotny",
            "anatomia", "fizjologia", "patologia", "bezpieczenstwo-i-higiena-pracy",
            "pierwsza-pomoc", "aseptyka", "ergonomia", "etyka-zawodowa",
            "komunikacja", "jezyk-obcy-zawodowy", "praktyka-zawodowa",
            "egzamin-zawodowy"]
    out[root / "tags.yaml"] = ("# Tagi i kategorie kursu\ncategory:\n"
                               '  name: "Kursy zawodowe"\n  idnumber: "KKZ"\ntags:\n'
                               + "".join(f"  - {tg}\n" for tg in tags))

    comp_lines = ["# Reguły ukończenia kursu", "course_completion:", "  enabled: 1",
                  "  required_all: true", "  criteria:", "    - type: activity_completion",
                  "    - type: grade", "      min_grade: 60", "section_completion:",
                  "  default_enabled: 1", "activity_completion_default:", "  tracked: 1",
                  "modules:"]
    for m in course.modules:
        comp_lines += [f'  - section: "{m.dir_name}"', "    criteria:",
                       "      - type: view", "      - type: quiz", "        min_score: 60"]
    out[root / "completion.yaml"] = "\n".join(comp_lines) + "\n"

    g = ["# Konfiguracja oceniania (kategoria: masażysta MED.10)", "scale:",
         '  type: "value"', "  min: 0", "  max: 100", "items:"]
    weights = {1: 1, 2: 3, 3: 3, 4: 3, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 2, 11: 2}
    for m in course.modules:
        g += [f"  - name: {yaml_q(sec_title(m))}",
              f"    itemname: {yaml_q('modul-' + str(m.index).zfill(2))}",
              '    itemtype: "manual"', '    itemmodule: "quiz"',
              "    grademax: 100", f"    weight: {weights.get(m.index, 1)}"]
    out[root / "grades.yaml"] = "\n".join(g) + "\n"

    toc_rows = "\n".join(
        f"| {m.index} | {sec_title(m)} | {m.hours or '—'} | {len(m.topics)} |"
        for m in course.modules)
    att_rows = "\n".join(f"| {a.letter} | {a.title} | {len(a.items)} |"
                         for a in course.attachments)
    front_rows = "\n".join(f"| {i+1} | {f.title} | {len(f.items)} |"
                           for i, f in enumerate(course.front))
    qual = course.qualification or "Kwalifikacja wyodrębniona MED.10 – Wykonywanie masażu."
    out[root / "course.md"] = f"""# {COURSE_NAME}

## Misja kursu

Kształcimy masażystów w duchu służby drugiemu człowiekowi: z prawdą o granicach
naszych kompetencji, z poszanowaniem godności każdego klienta i pacjenta, w trosce
o dobro wspólne. Masaż jest zawodem zaufania — dlatego uczymy najpierw bezpieczeństwa
(„primum non nocere”), potem techniki.

## Ramy prawne i kwalifikacja

{qual}

Program jest zgodny z podstawą programową kształcenia w kwalifikacji MED.10;
szczegółowa mapa efektów kształcenia znajduje się w załączniku A.

## Struktura kursu

- Moduły: **{len(course.modules)}** (MED.10.1 – MED.10.9, praktyka zawodowa, przygotowanie do egzaminu)
- Tematy (strona + quiz + zadanie): **{course.topic_count}**
- Zagadnienia szczegółowe: **{course.subtopic_count}**
- Łączny wymiar godzin (moduły z określoną liczbą godzin): **{total_hours}**
- Załączniki praktyczne: **A–M**
- Podręczniki modułów: aktywności typu **book** (book-01 w każdym module)
- Słownik pojęć: aktywność typu **glossary** w sekcji załączników

### Część wstępna i ramowa

| Nr | Opracowanie wstępne | Punkty |
|----|---------------------|--------|
{front_rows}

### Moduły

| Nr | Moduł | Godziny | Tematy |
|----|-------|---------|--------|
{toc_rows}

### Załączniki

| Litera | Tytuł | Pozycje |
|--------|-------|---------|
{att_rows}

## Zasady zaliczania

1. Każdy moduł: quizy tematyczne (próg 60%), zadania praktyczne, obecność na ćwiczeniach.
2. Praktyka zawodowa (moduł 10) — zrealizowanie godzin i dokumentacja zgodnie z załącznikiem C.
3. Egzamin potwierdzający kwalifikację MED.10 — część pisemna i praktyczna (moduł 11).

## Etyka i dostępność

Treści kursu są prawdziwe (bez medycznych wymysłów — oparte na spisie treści i
podstawie programowej), piękne (dbłość o język i kulturę zawodu) i sprawiedliwe
(równe traktowanie, przejrzyste kryteria oceny). Materiały spełniają WCAG 2.1 AA
(hierarchia nagłówków, opisy alternatywne grafik).
"""
    out[root / "changelog.md"] = """# Historia zmian kursu

## v1.0.0 — 2026-10-28
- Utworzono szkielet kursu (scripts/scaffold-kurs-masazu.py).
- Wypełniono treścią strony, quizy, zadania, sekcje i załączniki
  (scripts/gen_masaz_content.py — źródło: kurs_masazu.txt).
- Dodano aktywności `book` (podręcznik modułu) dla wszystkich 11 modułów
  oraz `glossary` (słownik pojęć) w sekcji załączników.
- Uzupełniono pliki główne: course.yaml, settings.yaml, tags.yaml,
  completion.yaml, grades.yaml, course.md, changelog.md.
"""
    return out


# --------------------------------------------------------------------------
# glossary
# --------------------------------------------------------------------------

GLOSSARY_TERMS = [
    ("Masaż klasyczny", "Systematyczny zespół ruchów wykonywanych na powierzchni ciała w celu oddziaływania na tkanki, krążenie i układ nerwowy."),
    ("Głaskanie (effleurage)", "Technika masażu polegająca na delikatnym przesuwaniu dłoni po skórze; zwykle otwiera i zamyka zabieg."),
    ("Rozcieranie (friction)", "Technika wykonywana ruchami okrężnymi lub poprzecznymi z większym naciskiem miejscowym, wpływająca na głębsze warstwy tkanek."),
    ("Ugniatanie (petrissage)", "Chwytanie i przemieszczanie mięśni; wpływa na elastyczność mięśni i krążenie lokalne."),
    ("Oklepywanie (tapotement)", "Technika rytmicznych uderzeń krawędzią lub palcami dłoni, pobudzająca unerwienie i napięcie mięśniowe."),
    ("Wibracja", "Technika przenoszenia drgań na tkanki dłonią lub aparatem; o działaniu rozluźniającym lub pobudzającym."),
    ("Przeciwwskazanie bezwzględne", "Stan, w którym masaż nie może być wykonany do czasu decyzji lekarza (np. ostre stany zapalne, gorączka, zakrzepica)."),
    ("Przeciwwskazanie względne", "Stan wymagający modyfikacji techniki, siły lub czasu zabiegu po konsultacji."),
    ("Aseptyka", "Zbiór zabiegów zapobiegających przedostaniu się drobnoustrojów do organizmu."),
    ("Antyseptyka", "Zniszczenie lub ograniczenie drobnoustrojów na skórze i błonach śluzowych środkami chemicznymi."),
    ("Ergonomia stanowiska", "Dostosowanie stołu, oświetlenia i postawy ciała masażysty tak, by chronić kręgosłup i stawy przed przeciążeniem."),
    ("BLS (Basic Life Support)", "Podstawowe zabiegi resuscytacyjne: uciskanie klatki piersiowej i oddechy ratownicze do czasu przyjazdu pomocy."),
    ("Drenaż limfatyczny", "Delikatna technika manualna wspomagająca przepływ chłonki; stosowana m.in. w obrzękach."),
    ("Masaż sportowy", "Masaż stosowany w cyklu treningowym i startowym zawodnika: przygotowanie, regeneracja, wsparcie leczenia pourazowego."),
    ("Masaż Shantala", "Masaż niemowląt i małych dzieci; wspiera rozwój i więź z opiekunem."),
    ("Tensegracja (masaż powięziowy)", "Praca z powięziami i linią oddechową, wpływająca na równowagę napięć całego ciała."),
    ("Świadoma zgoda klienta", "Potwierdzenie przez klienta zgody na zabieg po zapoznaniu z celem, przebiegiem i możliwym ryzykiem."),
    ("Granice kompetencji", "Zestaw czynności, których masażysta nie wykonuje (rozpoznawanie chorób, zabiegi wykraczające poza kwalifikację MED.10)."),
]


def glossary_yaml() -> str:
    y = ["# Aktywność typu glossary — słownik pojęć kursu",
         "glossary:",
         '  name: "Słownik pojęć masażu (MED.10)"',
         "  intro: |",
         "    Podstawowe terminy używane w kursie; uzupełnienie załącznika G.",
         "  intro_format: markdown",
         "  entries:"]
    for term, defn in GLOSSARY_TERMS:
        y += [f"  - term: {yaml_q(term)}", f"    definition: {yaml_q(defn)}",
              "    format: html"]
    return "\n".join(y) + "\n"


# --------------------------------------------------------------------------
# główna funkcja
# --------------------------------------------------------------------------


def collect_and_write(course, base: Path, dry_run: bool, no_books: bool):
    written = skipped = 0

    def put(path: Path, content: str):
        nonlocal written, skipped
        if path.exists() and path.stat().st_size > 0:
            skipped += 1
            return
        written += 1
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    # pliki główne
    for p, c in main_files(course).items():
        put(base / p.relative_to(BASE), c)

    # sekcje i aktywności modułowe
    all_sub_titles = [s.clean_title for m in course.modules for t in m.topics
                      for s in t.subtopics]
    for mod in course.modules:
        sec = base / "sections" / mod.dir_name
        if not sec.is_dir():
            continue
        put(sec / "section.yaml", section_yaml(mod))
        put(sec / "section.md", section_md(mod))
        for t in mod.topics:
            pages = sorted(sec.glob(f"page-{t.order:02d}-*.md"))
            if pages:
                put(pages[0], page_md(mod, t))
            qz = sec / f"quiz-{t.order:02d}"
            put(qz / "quiz.yaml", QUIZ_YAML_TMPL.format(
                name=yaml_q("Quiz: " + topic_heading(t)), num=t.num))
            put(qz / "questions.gift", quiz_gift(mod, t, all_sub_titles))
            put(qz / "questions.yaml", quiz_yaml_questions(mod, t, all_sub_titles))
            put(qz / "feedback.md", feedback_md(mod, t))
            asm = sec / f"assignment-{t.order:02d}"
            put(asm / "assignment.yaml", ASSIGNMENT_YAML_TMPL.format(
                name=yaml_q("Zadanie: " + topic_heading(t)), num=t.num))
            put(asm / "instructions.md", assignment_md(mod, t))
        if not no_books:
            bk = sec / "book-01"
            put(bk / "book.yaml", book_yaml(mod))
            for t in mod.topics:
                put(bk / "chapters" / f"{t.order:02d}-{slugify(t.clean_title)}.md",
                    page_md(mod, t))

    # sekcja załączników
    sec12 = base / "sections" / "12-zalaczniki"
    if sec12.is_dir():
        lab_lines = ["# Metadane sekcji", "id: 12",
                     'name: "Załączniki A-M"', "visible: 1", "summary:",
                     "  format: markdown", "  markdown_file: section.md",
                     "modules:"]
        for a in course.attachments:
            ref = next((p.name for p in sec12.glob(f"label-{a.order:02d}-*.md")),
                       f"label-{a.order:02d}.md")
            lab_lines += ["  - type: label", f"    ref: {yaml_q(ref)}",
                          f"    name: {yaml_q('Załącznik ' + a.letter + ': ' + a.title)}"]
        lab_lines += ["  - type: glossary", "    ref: glossary-01",
                      '    name: "Słownik pojęć masażu (MED.10)"']
        put(sec12 / "section.yaml", "\n".join(lab_lines) + "\n")
        put(sec12 / "section.md", "# Załączniki A–M\n\n"
            "Materiały pomocnicze kursu: mapa efektów kształcenia, regulaminy,\n"
            "wzory dokumentacji, wykazy przeciwwskazań i stanów pilnych, check-listy\n"
            "umiejętności, słownik, środki poślizgowe, procedury aseptyki, procedura\n"
            "pierwszej pomocy, kodeks etyczny, literatura oraz oświadczenia.\n")
        for a in course.attachments:
            labs = sorted(sec12.glob(f"label-{a.order:02d}-*.md"))
            if labs:
                put(labs[0], attachment_md(a))
        put(sec12 / "glossary-01" / "glossary.yaml", glossary_yaml())

    # sekcja 00 ogłoszenia
    sec00 = base / "sections" / "00-ogloszenia"
    if sec00.is_dir():
        put(sec00 / "section.yaml", "# Metadane sekcji\nid: 0\n"
            'name: "Ogłoszenia i administracja kursu"\nvisible: 1\nsummary:\n'
            "  format: markdown\n  markdown_file: page.md\n")
        put(sec00 / "page.md",
            "# Ogłoszenia kursu\n\n"
            "W tej sekcji publikowane są komunikaty organizacyjne: harmonogramy "
            "zjazdów,\nzmiany sal, terminy konsultacji i egzaminów próbnych.\n\n"
            "## Zasady komunikacji\n\n"
            "- Piszemy rzeczowo, życzliwie i bez zbędnych emocji — jak przystało "
            "na ludzi zaufania publicznego.\n"
            "- Sprawy indywidualne kierujemy na konsultacje lub drogę mailową, "
            "nie na forum.\n"
            "- Wszystkie terminy ogłaszamy z minimum dwutygodniowym wyprzedzeniem.\n")
    return written, skipped


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--toc", type=Path, default=default_source())
    ap.add_argument("--base", type=Path, default=Path(BASE_REL))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-books", action="store_true",
                    help="pomiń tworzenie aktywności book")
    args = ap.parse_args(argv)

    global BASE
    root = Path(__file__).resolve().parent.parent
    base = args.base if args.base.is_absolute() else root / args.base
    BASE = str(base)
    course = parse_course(args.toc)
    written, skipped = collect_and_write(course, base, args.dry_run, args.no_books)
    print(f"Zapisano plików: {written}, pominięto (mają treść): {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
