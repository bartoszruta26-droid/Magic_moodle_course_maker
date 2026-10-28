#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wspolny parser spisu tresci kursu (format markdown-like jak kurs_masazu.txt).

Udostepnia:
  * Course / Module / Topic / Subtopic / Attachment - struktury danych,
  * parse_course(path) - cala analiza pliku zrodlowego,
  * slugify/fold/upper_first - normalizacja nazw,
  * TOP_FILES / MEDIA_SUBDIRS / QKINDS / ACTIVITY_KINDS - stale konwencji repozytorium.

Format zrodlowy (kurs_masazu.txt):
    # SPIS TRESCI KURSU                -> poczatek czesci wlasciwej kursu
    ## MODUL N                         -> naglowek modulu
    ## MED.10.1. PEWIEN TYTUL          -> tytul modulu (bezposrednio po "## MODUL N")
    ### 30 godzin                     -> meta modulu (godziny / "realizowane ...")
    ### N.M. Tytatu tematu            -> temat (strona + quiz + zadanie)
    N.M.K. Podtemat                    -> podtemat (lista punktow wewnatrz tematu)
    ## Zalacznik X. Tytul              -> zalacznik (A..M)
    X.Y. Punkt zalacznika              -> pozycja zalacznika
    ## CZESC WSTEPNA I RAMOWA          -> czesc przed "# SPIS TRESCI KURSU"
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

MAX_SLUG = 55                 # dlugosc slugu jak w istniejacych sekcjach kursow
FRONT_MATTER_END = re.compile(r"^---\s*$")

# --- konwencja nazewnicza repozytorium (kursy courses/01-*, courses/02-*) ---
TOP_FILES = ["course.yaml", "course.md", "settings.yaml", "tags.yaml",
             "completion.yaml", "grades.yaml", "changelog.md", "course.jpg"]
MEDIA_SUBDIRS = ["images", "videos", "audio", "documents"]
QKINDS = ["multichoice", "truefalse", "shortanswer", "essay", "matching"]
ACTIVITY_KINDS = ["page", "quiz", "assignment"]


def fold(text: str) -> str:
    """Usuwa diakrytyki (slownie i przez NFKD) bez zmian wielkosci liter."""
    s = text.replace("\u0142", "l").replace("\u0141", "L")
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


_ABBREV = {
    "kwalifikacje": "kw", "kwalifikacyjnego": "kw",
    "kwalifikacji": "kw", "kwalifikacjie": "kw",
}


def _wordwise(tokens: list[str], maxlen: int) -> str:
    """Skleja slowa dopoki mieszcza sie w maxlen; ostatnie przycina co do limitu."""
    out = ""
    for tok in tokens:
        cand = tok if not out else out + "-" + tok
        if len(cand) <= maxlen:
            out = cand
            continue
        room = maxlen - len(out) - 1
        if room >= 2:
            out += "-" + tok[:room].strip("-")
        break
    return out.strip("-")


def slugify(text: str, maxlen: int = MAX_SLUG) -> str:
    """Malymi literami, bez diakrytykow, slowa rozdzielone mylnikiem.

    Ciecie odbywa sie NA GRANICY WYRAZOW. Gdy kolejne slowo nie miesci sie w
    limicie, jest zastepowane skrotem slownikowym (_ABBREV), a jesli to nie
    pomaga - inicjalami (stad nazwa sekcji 'przygotowanie-do-egzaminu-
    potwierdzajacego-kw' w katalogu kursu MED.10).
    """
    raw = re.sub(r"[^a-z0-9]+", "-", fold(text).lower()).strip("-")
    if len(raw) <= maxlen:
        return raw
    tokens = [t for t in raw.split("-") if t]
    keep: list[str] = []
    for tok in tokens:
        if len("-".join(keep + [tok])) <= maxlen:
            keep.append(tok)
        else:
            break
    rest = tokens[len(keep):]
    if not rest:
        return _wordwise(tokens, maxlen)
    # skrot od KONCA naglowka: slowo slownikowe ("kw") lub pierwsze 4 znaki
    words = [t for t in rest if not t.isdigit()]
    short = None
    for tok in reversed(words):             # najpierw doslownie ostatnie slowo
        if tok in _ABBREV:
            short = _ABBREV[tok]
            break
    if short is None:
        short = (words[-1][:4] if words else "x")
    stem = "-".join(keep)
    while stem and len(stem) + 1 + len(short) > maxlen:
        stem = "-".join(stem.split("-")[:-1])
    return f"{stem}-{short}" if stem else short[:maxlen]


def upper_first(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


@dataclass
class Subtopic:
    num: str                 # np. "1.2.3"
    title: str


@dataclass
class Topic:
    num: str                 # np. "1.2"
    title: str               # pelna linia spisu, np. "1.2. Przepisy prawa pracy..."
    stem: str = ""           # "02-przepisy-prawa-pracy" (slug BEZ numeru tematu)
    subtopics: list[Subtopic] = field(default_factory=list)

    @property
    def order(self) -> int:
        return int(self.num.split(".")[1])

    @property
    def clean_title(self) -> str:
        """Tytul bez numeru porzadkowego 'N.M.' - podstawa sluga strony."""
        return re.sub(r"^\d{1,2}\.\d{1,2}\.?\s*", "", self.title).strip()


@dataclass
class Module:
    index: int               # 1..11
    code: str                # np. "MED.10.1" albo "" (moduly 10-11)
    raw_title: str           # oryginalny tytul z pliku (duzymi literami)
    meta: list[str] = field(default_factory=list)      # "30 godzin", ...
    topics: list[Topic] = field(default_factory=list)
    dir_name: str = ""       # np. "01-med-10-1-bezpieczenstwo-i-higiena-pracy"

    @property
    def title(self) -> str:
        """Tytul 'human readable': MED.10.1. Bezpieczenstwo i higiena pracy."""
        t = self.raw_title.lower()
        return upper_first(t)

    @property
    def hours(self) -> str | None:
        for m in self.meta:
            hm = re.search(r"(\d+)\s*godz", fold(m), re.I)
            if hm:
                return hm.group(1)
        return None


@dataclass
class Attachment:
    letter: str              # "A".."M"
    title: str               # tytul bez litery
    items: list[tuple[str, str]] = field(default_factory=list)   # (num, tytul)

    @property
    def order(self) -> int:
        return ord(self.letter.upper()) - ord("A") + 1


@dataclass
class FrontSection:
    title: str                                  # "Przedmowa: kurs jako sluza bliźniemu ..."
    items: list[tuple[str, str]] = field(default_factory=list)   # (num, tytul)


@dataclass
class Course:
    source: Path
    name: str = ""                              # tytul glowny ("# ...")
    qualification: str = ""                     # "## Kwalifikacja wyodrebniona ..."
    front: list[FrontSection] = field(default_factory=list)
    modules: list[Module] = field(default_factory=list)
    attachments: list[Attachment] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)     # PODSUMOWANIE STRUKTURY KURSU
    unknown_headings: list[str] = field(default_factory=list)

    # --- pomocnicze ---
    def module(self, index: int) -> Module | None:
        return next((m for m in self.modules if m.index == index), None)

    @property
    def topic_count(self) -> int:
        return sum(len(m.topics) for m in self.modules)

    @property
    def subtopic_count(self) -> int:
        return sum(len(t.subtopics) for m in self.modules for t in m.topics)

    def all_topics(self):
        for mod in sorted(self.modules, key=lambda m: m.index):
            for topic in sorted(mod.topics, key=lambda t: t.order):
                yield mod, topic


_RE_MODUL = re.compile(r"^MODUL\s+(\d+)\b", re.I)   # fold() zamienia L->l, wiec "MODUŁ" -> "MODUL"
_RE_TOPIC = re.compile(r"^(\d{1,2})\.(\d{1,2})\.\s+(.+?)\s*$")
_RE_SUB = re.compile(r"^(\d{1,2}\.\d{1,2}\.\d{1,2})\.\s+(.+?)\s*$")
_RE_ATT_TITLE = re.compile(r"^Zala?cznik\s+([A-M])\.\s*(.*)$", re.I)
_RE_ATT_ITEM = re.compile(r"^([A-M])\.(\d{1,2})\.\s+(.+?)\s*$")
_RE_FRONT_SEC = re.compile(r"^(\d{1,2})\.\s+(.+?)\s*$")
_RE_FRONT_ITEM = re.compile(r"^(\d{1,2}\.\d{1,2})\.\s+(.+?)\s*$")


def _strip_prefixes(line: str) -> tuple[int, str]:
    """Zwraca (poziom '#', tresc) dla linii naglowkowej lub metalinii."""
    m = re.match(r"^(#{1,6})\s*(.*)$", line)
    if m:
        return len(m.group(1)), m.group(2).strip()
    return 0, line.strip()


def parse_course(path: str | Path) -> Course:
    path = Path(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    course = Course(source=path)

    state = "preamble"          # preamble -> front -> toc -> attachments -> summary/end
    cur_mod: Module | None = None
    cur_topic: Topic | None = None
    cur_att: Attachment | None = None
    cur_front: FrontSection | None = None
    pending_mod_index: int | None = None

    for raw in lines:
        level, text = _strip_prefixes(raw)
        if not text or set(text) <= {"-", "*", "_"}:
            continue
        flat = fold(text)
        head = flat.upper()

        # ---- naglowek H2/H3 "CZESC WSTEPNA I RAMOWA" (w pliku bywa H2!) ----
        if level in (2, 3) and state not in ("toc", "attachments", "summary", "end"):
            if "CZESC WSTEPNA" in head:
                state = "front"
                cur_front = None
                continue

        # ---- przejscia miedzy czesciami dokumentu (naglowki H1) ----
        if level == 1:
            cur_mod = cur_topic = cur_att = cur_front = None
            pending_mod_index = None
            if "SPIS TRESCI" in head and "SZCZEGOLOWY" not in head:
                state = "toc"
            elif head.startswith("ZALACZNIKI"):
                state = "attachments"
            elif "PODSUMOWANIE STRUKTURY" in head:
                state = "summary"
            elif "ZAKO" in head and "CZENIE" in head:
                state = "end"
            elif "CZESC WSTEPNA" in head:
                state = "front"
            else:
                course.name = course.name or text   # pierwsza H1 = tytul kursu
            continue

        # ---- czesc wstepna i ramowa ----
        if state == "front":
            if level in (2, 3):
                ms = _RE_FRONT_SEC.match(flat)
                if ms:                      # "1. Przedmowa: ..." -> sekcja
                    cur_front = FrontSection(title=ms.group(2))
                    course.front.append(cur_front)
                elif "kwalifikacj" in flat.lower() and not course.qualification:
                    course.qualification = text   # "## Kwalifikacja wyodrebniona ..."
                else:
                    cur_front = FrontSection(title=text)
                    course.front.append(cur_front)
                continue
            mi = _RE_FRONT_ITEM.match(flat)
            if mi and cur_front is not None:
                cur_front.items.append((mi.group(1), text))
            continue

        # ---- zalaczniki ----
        if state == "attachments":
            ma = _RE_ATT_TITLE.match(flat)
            if ma:
                # tytul bez prefiksu "Zalacznik X." - tak jest w katalogu kursu
                title = re.sub(r"^Za\u0142\u0105cznik\s+[A-M]\.\s*", "", text, flags=re.I)
                cur_att = Attachment(letter=ma.group(1).upper(), title=title)
                course.attachments.append(cur_att)
                continue
            mi = _RE_ATT_ITEM.match(flat)
            if mi and cur_att is not None and mi.group(1).upper() == cur_att.letter:
                cur_att.items.append((f"{mi.group(1).upper()}.{mi.group(2)}", text))
            continue

        # ---- podsumowanie / zakonczenie ----
        if state in ("summary", "end"):
            if not text.startswith("|") and level >= 3:
                course.summary.append(text)
            continue

        # ---- spis tresci wlasciwa (moduly) ----
        if state != "toc":
            if "KWALIFIKACYJNY KURS" in head:
                course.name = text
            elif level == 2 and "Kwalifikacja wyodr" in text:
                course.qualification = text
            continue

        mm = _RE_MODUL.match(flat)
        if mm and level == 2:
            pending_mod_index = int(mm.group(1))
            cur_mod, cur_topic = None, None
            continue

        if pending_mod_index is not None and level == 2:
            code_m = re.match(r"^\s*((?:MED|KKW|K)\.\d+(?:\.\d+)?)\.?\s+(.*)$", text)
            code = code_m.group(1) if code_m else ""
            raw_title = code_m.group(2) if code_m else text
            cur_mod = Module(index=pending_mod_index, code=code, raw_title=raw_title)
            slug_src = f"{code} {raw_title}" if code else raw_title
            cur_mod.dir_name = f"{cur_mod.index:02d}-{slugify(slug_src)}"
            course.modules.append(cur_mod)
            pending_mod_index = None
            continue

        if cur_mod is None:
            continue

        # meta modulu: "### 30 godzin" / "### realizowane w sposob zintegrowany"
        if level == 3 and not _RE_TOPIC.match(flat):
            cur_mod.meta.append(text)
            continue

        mt = _RE_TOPIC.match(flat)
        if mt and int(mt.group(1)) == cur_mod.index:
            cur_topic = Topic(num=f"{mt.group(1)}.{mt.group(2)}", title=text)
            cur_topic.stem = f"{cur_topic.order:02d}-{slugify(cur_topic.clean_title)}"
            cur_mod.topics.append(cur_topic)
            continue

        msub = _RE_SUB.match(flat)
        if msub and cur_topic is not None and msub.group(1).startswith(cur_topic.num + "."):
            cur_topic.subtopics.append(Subtopic(num=msub.group(1), title=text))
            continue

    # porzadkowanie
    course.modules.sort(key=lambda m: m.index)
    for mod in course.modules:
        mod.topics.sort(key=lambda t: t.order)
        for topic in mod.topics:
            topic.subtopics.sort(key=lambda s: [int(x) for x in s.num.split(".")])
    course.attachments.sort(key=lambda a: a.order)
    return course


class Plan:
    """Zbior operacji 'dotknij plik' z pelna idempotentnoscia (nic nie nadpisuje)."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.created: list[Path] = []
        self.existed: list[Path] = []

    def touch(self, path: Path):
        if path.exists():
            self.existed.append(path)
            return
        self.created.append(path)
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

    def report(self, label: str = "Plan"):
        print(f"{label}: nowe = {len(self.created)}, "
              f"istniejace = {len(self.existed)}, "
              f"razem = {len(self.created) + len(self.existed)}")


def course_file_plan(course: Course, base: Path, *,
                     attachments_mode: str = "labels",
                     front: bool = False,
                     first_module_section: int = 1) -> list[Path]:
    """Lista sciezek plikow szkicu kursu (bez tworzenia czegokolwiek)."""
    paths: list[Path] = []
    add = paths.append
    for f in TOP_FILES:
        add(base / f)
    for sub in MEDIA_SUBDIRS:
        add(base / "media" / sub / ".gitkeep")
    qb = base / "question-bank"
    add(qb / "categories.yaml")
    for kind in QKINDS:
        add(qb / kind / "set-01.gift")
    add(qb / "multichoice" / "set-01.yaml")
    add(base / "sections" / "00-ogloszenia" / "section.yaml")
    add(base / "sections" / "00-ogloszenia" / "page.md")

    if front:
        for i, fs in enumerate(course.front, start=0):
            sec = base / "sections" / f"{i:02d}-{slugify(fs.title)}"
            add(sec / "section.yaml"); add(sec / "section.md")
            for j, (_num, title) in enumerate(fs.items, start=1):
                add(sec / f"page-{j:02d}-{slugify(title)}.md")

    mods = sorted(course.modules, key=lambda m: m.index)
    for k, mod in enumerate(mods, start=first_module_section):
        sec = base / "sections" / mod.dir_name
        add(sec / "section.yaml"); add(sec / "section.md")
        for topic in mod.topics:
            stem = topic.stem or f"{topic.order:02d}-{slugify(topic.clean_title)}"
            add(sec / f"page-{stem}.md")
            qz = sec / f"quiz-{topic.order:02d}"
            for f in ("quiz.yaml", "questions.gift", "questions.yaml", "feedback.md"):
                add(qz / f)
            ap = sec / f"assignment-{topic.order:02d}"
            add(ap / "assignment.yaml"); add(ap / "instructions.md")

    if attachments_mode != "none":
        att_first = first_module_section + len(mods)
        if attachments_mode == "subdirs":
            for att in course.attachments:
                sec = base / "sections" / f"{att.order + att_first - 1:02d}-zalacznik-{slugify(att.title)}"
                add(sec / "section.yaml"); add(sec / "section.md")
                for j, (num, title) in enumerate(att.items, start=1):
                    add(sec / f"page-{j:02d}-{slugify(title)}.md")
        else:
            sec = base / "sections" / f"{att_first:02d}-zalaczniki"
            add(sec / "section.yaml"); add(sec / "section.md")
            for att in course.attachments:
                add(sec / f"label-{att.order:02d}-{slugify(att.title)}.md")
    return paths


def build_course_files(course: Course, base: Path, plan: Plan | None = None, **kw) -> Plan:
    """Materializuje szkic kursu (wylacznie puste pliki) wg planu ze spisu tresci."""
    plan = plan or Plan(dry_run=kw.pop("dry_run", False))
    for p in course_file_plan(course, base, **kw):
        plan.touch(p)
    return plan


# ------------------------------------------------------------------ slugi stron
_PAGE_RE = re.compile(r"^page-(\d{1,3})-(.+?)\.md$")


def topic_slug_variants(topic: Topic) -> list[str]:
    """Wszystkie akceptowalne koncowki sluga strony tematu (od najbardziej
    oczekiwanej do najluZniejszej) - tolerancja na historyjne skroty slow."""
    base_words = [w for w in slugify(topic.clean_title).split("-") if w]
    out = []
    # 1) pelny slug bez numeru tematu
    out.append("-".join(base_words))
    # 2) ten sam, ale 'kwalifikacy(jn|nego...) -> kw' itp. (historia repo)
    abb = [(_ABBREV.get(w, w)) for w in base_words]
    if abb != base_words:
        out.append("-".join(abb))
    # 3) wariant z przymusowa inicjala ostatniego mego slowa (maxdl truncation)
    return out


def match_page_topic(pages: list[str], topic: Topic) -> str | None:
    """Znajdz istniejaca strone page-NN-*.md pasujaca do tematu (po numerze NN)."""
    want_num = f"{topic.order:02d}"
    for name in pages:
        m = _PAGE_RE.match(name)
        if not m:
            continue
        if m.group(1) == want_num or int(m.group(1)) == topic.order:
            return name
    return None


def normalize_pages(course: Course, base: Path, *, dry_run: bool = False) -> dict:
    """Przechowuje/poukladaj puste strony page-NN-*.md wg spisu tresci.

    * pusty plik z tym samym numerem, ale innym slugiem   -> zmiana nazwy,
    * wiele pustych duplikatow tego samego numeru         -> usuniecie nadwyzki,
    * brak jakiejkolwiek strony dla tematu                -> utworzenie pustej,
    * plik NIEPUSTy (ma tresc)                            -> nietknięty (skipped).
    """
    stats = {"renamed": 0, "removed_dupes": 0, "created": 0,
             "kept": 0, "skipped_nonempty": 0}
    for mod in sorted(course.modules, key=lambda m: m.index):
        sec = base / "sections" / mod.dir_name
        if not sec.is_dir():
            continue
        pages = sorted(p.name for p in sec.glob("page-*.md"))
        for topic in mod.topics:
            want = sec / f"page-{topic.stem}.md"
            same_num = [sec / n for n in pages
                        if _PAGE_RE.match(n) and int(_PAGE_RE.match(n).group(1)) == topic.order]
            empties = [p for p in same_num if p.stat().st_size == 0]
            nonempty = [p for p in same_num if p.stat().st_size > 0]
            if want.exists():
                if want.stat().st_size > 0:
                    stats["kept"] += 1
                for dup in empties:
                    if dup != want:
                        if not dry_run:
                            dup.unlink()
                        stats["removed_dupes"] += 1
                continue
            if nonempty:
                stats["skipped_nonempty"] += 1     # nie niszczymy realnej tresci
                continue
            if len(empties) == 1:
                if not dry_run:
                    empties[0].rename(want)
                stats["renamed"] += 1
            else:
                for e in empties:
                    if not dry_run:
                        e.unlink()
                    stats["removed_dupes"] += 1
                if not dry_run:
                    want.parent.mkdir(parents=True, exist_ok=True)
                    want.touch()
                stats["created"] += 1
    return stats


def check_structure(course: Course, base: Path) -> list[str]:
    """Walidacja: co sie rozni miedzy spisem tresci a stanem na dysku."""
    problems = []
    for mod in sorted(course.modules, key=lambda m: m.index):
        sec = base / "sections" / mod.dir_name
        if not sec.is_dir():
            problems.append(f"brak sekcji {mod.dir_name}")
            continue
        pages = sorted(p.name for p in sec.glob("page-*.md"))
        for topic in mod.topics:
            want = f"page-{topic.stem}.md"
            if want not in pages:
                hit = match_page_topic(pages, topic)
                if hit:
                    problems.append(f"{mod.dir_name}: strona '{hit}' powinna miec nazwe '{want}'")
                else:
                    problems.append(f"{mod.dir_name}: brak strony '{want}'")
            for d, files in ((f"quiz-{topic.order:02d}", ("quiz.yaml", "questions.gift",
                                                          "questions.yaml", "feedback.md")),
                             (f"assignment-{topic.order:02d}", ("assignment.yaml",
                                                                "instructions.md"))):
                for f in files:
                    if not (sec / d / f).exists():
                        problems.append(f"{mod.dir_name}: brak {d}/{f}")
        nums = {int(_PAGE_RE.match(n).group(1)) for n in pages if _PAGE_RE.match(n)}
        orders = {t.order for t in mod.topics}
        for extra in sorted(nums - orders):
            problems.append(f"{mod.dir_name}: dodatkowa strona page-{extra:02d}-* (brak tematu w spisie)")
    return problems


def default_source() -> Path:
    """Domyślny plik zrodlowy kursu masażu."""
    root = Path(__file__).resolve().parent.parent
    return root / "kurs_masazu.txt"


if __name__ == "__main__":
    c = parse_course(default_source())
    print(f"Plik: {c.source}")
    print(f"Tytul: {c.name}")
    print(f"Czesc wstepna: {len(c.front)} sekcji")
    print(f"Moduly: {len(c.modules)}, tematy: {c.topic_count}, podtematy: {c.subtopic_count}")
    for mod in c.modules:
        first_sub = len(mod.topics[0].subtopics) if mod.topics else 0
        print(f"  {mod.dir_name:<50} {len(mod.topics):>3} tem., {first_sub:>2} podt.(1szy), godz.={mod.hours}")
    print(f"Zalaczniki: {len(c.attachments)}")
    for att in c.attachments:
        print(f"  {att.letter}. {att.title[:50]:<50} {len(att.items):>2} poz.")
