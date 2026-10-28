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
    title: str
    subtopics: list[Subtopic] = field(default_factory=list)

    @property
    def order(self) -> int:
        return int(self.num.split(".")[1])


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
