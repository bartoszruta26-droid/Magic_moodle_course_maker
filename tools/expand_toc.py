#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Etap 2 rozbudowy kursu 03-kwalifikacyjny-kurs-zawodowy-naturopaty:
1. Parsuje połączony spis treści z courses/DWULETNI KURS NATUROPATY.txt
   (tematy X.Y + podpunkty X.Y.Z, obie wersje programu, bez duplikatów).
2. Nadpisuje strony page-X-Y-*.md pełną listą podpunktów jako "Zagadnienia".
3. Generuje rozbudowane quizy GIFT (truefalse per podpunkt + multichoice per temat).
4. Aktualizuje tabele tematów w section.md (kolumna "Liczba zagadnień").
"""
import os, re, unicodedata

BASE = "/workspace/courses"
SRC = os.path.join(BASE, "DWULETNI KURS NATUROPATY.txt")
COURSE = os.path.join(BASE, "03-kwalifikacyjny-kurs-zawodowy-naturopaty")
SECTIONS_DIR = os.path.join(COURSE, "sections")

def slugify(text):
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60]

# ---------- 1. Parsowanie źródła ----------
with open(SRC, encoding="utf-8") as f:
    lines = f.read().splitlines()

re_mod = re.compile(r"^###\s*MODU(?:Ł|L)\s*(\d+)\s*:\s*(.+)$")
re_sem = re.compile(r"^##\s*(SEMESTR\s+[IVX]+.*)$", re.I)
re_top = re.compile(r"^(\d{1,2}\.\d{1,2})\.\s+(.+)$")
re_sub = re.compile(r"^-\s+(\d{1,2}\.\d{1,2}\.\d{1,2})\.\s+(.+)$")

topics = {}
cur_module_title = None
cur_semester = None
cur_topic = None

for ln in lines:
    ln = ln.rstrip()
    m = re_sem.match(ln)
    if m:
        cur_semester = m.group(1).strip()
        continue
    m = re_mod.match(ln)
    if m:
        cur_module_title = m.group(2).strip()
        continue
    m = re_sub.match(ln)
    if m and cur_topic is not None:
        num, title = m.group(1), m.group(2).strip()
        if num not in topics[cur_topic]["sub_seen"]:
            topics[cur_topic]["sub_seen"].add(num)
            topics[cur_topic]["subs"].append(title)
        continue
    m = re_top.match(ln)
    if m:
        num, title = m.group(1), m.group(2).strip()
        if num in topics:
            cur_topic = num  # ten sam temat w drugiej wersji programu
            continue
        topics[num] = {
            "num": num, "title": title, "subs": [], "sub_seen": set(),
            "mod_no": int(num.split(".")[0]),
            "mod_title": cur_module_title or "",
            "semester": cur_semester or "",
        }
        cur_topic = num
        continue

def sort_key(k):
    a, b = k.split(".")
    return (int(a), int(b))
topic_keys = sorted(topics.keys(), key=sort_key)
print("TEMATY:", len(topic_keys), "PODPUNKTY:", sum(len(t["subs"]) for t in topics.values()))

# ---------- 2. Mapowanie sekcji kursu na numery tematów ----------
section_dirs = sorted(d for d in os.listdir(SECTIONS_DIR) if re.match(r"^\d\d-", d))
sec_topics = {}
for d in section_dirs:
    pdir = os.path.join(SECTIONS_DIR, d)
    for fn in os.listdir(pdir):
        m = re.match(r"^page-(\d{1,2})-(\d{1,2})-.*\.md$", fn)
        if m:
            key = f"{m.group(1)}.{m.group(2)}"
            sec_topics.setdefault(d, []).append(key)
    if d in sec_topics:
        sec_topics[d].sort(key=sort_key)

covered = {t for ts in sec_topics.values() for t in ts}
missing = [k for k in topic_keys if k not in covered]
extra = sorted([t for t in covered if t not in topics], key=sort_key)
print("BRAKUJE stron dla:", missing)
print("Strony bez źródła w TOC:", extra)

# ---------- 3. Nadpisywanie stron ----------
def render_page(t, dirname):
    num, title = t["num"], t["title"]
    sem = t["semester"] if t["semester"] else "kurs zbiorczy"
    items = "\n".join(f"- **{i+1}. {sub}**" for i, sub in enumerate(t["subs"]))
    if not items:
        items = ("- Omówienie podstaw teoretycznych tematu\n"
                 "- Zastosowanie praktyczne w procesie zdrowienia pacjenta\n"
                 "- Bezpieczeństwo pacjenta i granice kompetencji naturopaty")
    return f"""<!--
Plik: page-{num.replace('.', '-')}-{slugify(title)}.md
Typ pliku: Strona edukacyjna (page)
Konwersja: Markdown → HTML
Sekcja: {dirname}
Kurs: Kwalifikacyjny Kurs Zawodowy – Naturopata
-->

# {num}. {title}

## Wprowadzenie

Strona tematyczna modułu **{t['mod_no']} – {t['mod_title']}** ({sem}).
Temat zgodnie z połączonym spisem treści kursu: *{title}*

## Zagadnienia do opanowania

Po ukończeniu tego tematu uczestnik potrafi omówić i zastosować w praktyce
naturopatycznej każde z poniższych zagadnień szczegółowych (podpunkty {num}
połączonego spisu treści programu kursu):

{items}

## Cele szczegółowe

- Rozpoznanie i nazwanie struktur, mechanizmów i procedur objętych powyższymi zagadnieniami.
- Zastosowanie wiedzy w planowaniu działań naturopatycznych z zachowaniem zasady *primum non nocere*.
- Identyfikacja przeciwwskazań i sytuacji wymagających skierowania pacjenta do lekarza.

## Materiały do pobrania

Materiały poglądowe (ilustracje, filmy, dokumenty PDF) zostaną dodane w katalogu
`media/` kursu w kolejnym etapie prac redakcyjnych.

## Podsumowanie

Temat {num} („{title}”) obejmuje {len(t['subs'])} zagadnień szczegółowych.
Przed przejściem do kolejnego tematu należy rozwiązać quiz sprawdzający
oraz wykonać zadanie modułowe.

## Pytania do refleksji

1. Jak zagadnienie „{title}” wpływa na codzienną praktykę naturopatyczną?
2. Jakie są przeciwwskazania i środki ostrożności związane z tym tematem?
"""

written_pages = 0
for d, keys in sec_topics.items():
    pdir = os.path.join(SECTIONS_DIR, d)
    for fn in sorted(os.listdir(pdir)):
        m = re.match(r"^page-(\d{1,2})-(\d{1,2})-.*\.md$", fn)
        if not m:
            continue
        key = f"{m.group(1)}.{m.group(2)}"
        if key in topics:
            with open(os.path.join(pdir, fn), "w", encoding="utf-8") as f:
                f.write(render_page(topics[key], d))
            written_pages += 1
print("Zapisano stron:", written_pages)

# ---------- 4. Quizy GIFT ----------
def esc(s):
    s = s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("#", "\\#")
    s = s.replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|")
    return s

total_tf = total_mc = 0
for d, keys in sec_topics.items():
    qdir = os.path.join(SECTIONS_DIR, d, "quiz-01")
    if not os.path.isdir(qdir):
        continue
    keys = [k for k in keys if k in topics]
    if not keys:
        continue
    out = []
    n_tf = n_mc = 0
    for key in keys:
        t = topics[key]
        mod_no = t["mod_no"]
        kid = key.replace(".", "")
        out.append(f"// === Temat {key}: {t['title']} ===")
        for i, sub in enumerate(t["subs"]):
            if i % 2 == 0:
                stmt = (f"Zagadnienie „{sub}” wchodzi w zakres tematu "
                        f"„{t['title']}” ({key}) modułu {mod_no}.")
                ans = "TRUE"
            else:
                prev = t["subs"][i-1]
                stmt = (f"Zagadnienie „{sub}” jest elementem tematu „{prev}”, "
                        f"a nie tematu „{t['title']}” ({key}).")
                ans = "FALSE"
            out.append(f"::tf-m{mod_no:02d}-{kid}-q{i+1}:: {esc(stmt)} {{{ans}}} //")
            n_tf += 1
        if len(t["subs"]) >= 2:
            wrong_idx = (int(kid) * 13) % len(topic_keys)
            wrong_key = topic_keys[wrong_idx]
            pool = topics[wrong_key]["subs"]
            wrong = pool[(int(kid)) % len(pool)] if pool else "Zagadnienie kontrolne spoza tematu"
            opts = [t["subs"][0], t["subs"][1], wrong,
                    t["subs"][2] if len(t["subs"]) > 2 else topics[topic_keys[(wrong_idx+3) % len(topic_keys)]]["subs"][0]]
            correct_idx = 0
            mc_lines = [f"::mc-m{mod_no:02d}-{kid}:: Które z poniższych zagadnień należy bezpośrednio do tematu „{t['title']}” ({key})? {{"]
            for j, o in enumerate(opts):
                mark = "= " if j == correct_idx else "~ "
                mc_lines.append(f"    {mark}{esc(o)}")
            mc_lines.append("}")
            out.extend(mc_lines)
            n_mc += 1
    with open(os.path.join(qdir, "questions.gift"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    total_tf += n_tf
    total_mc += n_mc
print("Pytania TF:", total_tf, "| MC:", total_mc)

# ---------- 5. Tabele w section.md ----------
updated_tables = 0
for d, keys in sec_topics.items():
    spath = os.path.join(SECTIONS_DIR, d, "section.md")
    if not os.path.isfile(spath):
        continue
    with open(spath, encoding="utf-8") as f:
        content = f.read()
    rows = []
    for key in keys:
        t = topics.get(key)
        title = t["title"] if t else "(poza numerowanym spisem treści)"
        n = len(t["subs"]) if t else "-"
        rows.append(f"| {key} | page | {title} | {n} |")
    new_table = ("| Nr tematu | Typ zasobu | Temat | Liczba zagadnień |\n"
                 "|-----------|------------|-------|------------------|\n"
                 + "\n".join(rows) + "\n")
    pat = re.compile(r"\| Nr tematu \|[^\n]*\n\|[-| ]+\|\n(?:\|.*\n)+")
    new_content, cnt = pat.subn(new_table, content)
    if cnt:
        with open(spath, "w", encoding="utf-8") as f:
            f.write(new_content)
        updated_tables += cnt
print("Zaktualizowano tabel:", updated_tables)
