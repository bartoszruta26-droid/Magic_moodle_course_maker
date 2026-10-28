#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Etap 2a – naprawa mapowania sekcja->temat w kursie 03.

Wersja DWULETNIA programu (plik courses/DWULETNI KURS NATUROPATY.txt) numeruje
moduły 1..18, podczas gdy kurs używa numeracji modułów z wersji ROZSZERZONEJ
(1..21 + Cyrulika=22 + Prawo i organizacja=23). Niniejszy skrypt:

1. Parsuje OBYDWA bloki spisu treści osobno (rozszerzony / dwuletni).
2. Mapuje każdy temat na sekcję kursu po TYTULE MODUŁU (nie po numerze).
3. Nadpisuje strony page-X-Y-*.md podpunktami właściwego tematu.
4. Regeneruje quizy GIFT per sekcja (ID tf-/mc- z prefiksem sekcji sNN).
5. Aktualizuje tabele "Nr tematu" w section.md.
"""
import os, re, glob, shutil, unicodedata

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

def norm_title(t):
    t = t.upper()
    t = t.replace("–", "-").replace("—", "-")
    t = re.sub(r"[^A-ZĄĆĘŁŃÓŚŹŻ0-9- ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

# ---------- Parsowanie dwóch wersji TOC ----------
re_mod = re.compile(r"^###\s*MODU(?:Ł|L)\s*(\d+)\s*:\s*(.+)$")
re_sem = re.compile(r"^##\s*(SEMESTR\s+[IVX]+.*)$", re.I)
re_top = re.compile(r"^(\d{1,2}\.\d{1,2})\.\s+(.+)$")
re_sub = re.compile(r"^-\s+(\d{1,2}\.\d{1,2}\.\d{1,2})\.\s+(.+)$")

lines = open(SRC, encoding="utf-8").read().splitlines()

# punkt startu drugiej wersji: nagłówek przed nową listą MODUŁ 1 (po linii ~1000)
starts = [i for i, ln in enumerate(lines) if re_mod.match(ln.strip()) and re_mod.match(ln.strip()).group(1) == "1"]
split_idx = starts[-1] if len(starts) >= 2 else len(lines)

def parse(block):
    """-> dict module_norm_title -> list of topics {num,title,subs,semester}"""
    mods = {}
    cur_mod = None
    cur_sem = None
    cur_topic = None
    for ln in block:
        ln = ln.rstrip()
        m = re_sem.match(ln)
        if m:
            cur_sem = m.group(1).strip()
            continue
        m = re_mod.match(ln)
        if m:
            cur_mod = norm_title(m.group(2))
            mods.setdefault(cur_mod, [])
            cur_topic = None
            continue
        m = re_sub.match(ln)
        if m and cur_topic is not None:
            num, title = m.group(1), m.group(2).strip()
            if num not in cur_topic["sub_seen"]:
                cur_topic["sub_seen"].add(num)
                cur_topic["subs"].append(title)
            continue
        m = re_top.match(ln)
        if m and cur_mod is not None:
            num, title = m.group(1), m.group(2).strip()
            if num in {t["num"] for t in mods[cur_mod]}:
                cur_topic = next(t for t in mods[cur_mod] if t["num"] == num)
                continue
            cur_topic = {"num": num, "title": title, "subs": [],
                         "sub_seen": set(), "semester": cur_sem or ""}
            mods[cur_mod].append(cur_topic)
    return mods

ext = parse(lines[:split_idx])     # wersja rozszerzona (moduły 1..21)
two = parse(lines[split_idx:])     # wersja dwuletnia (moduły 1..18)
print("Wersja rozszerzona – moduły:", len(ext), "| dwuletnia:", len(two))

# ---------- Sekcje kursu ----------
section_dirs = sorted(d for d in os.listdir(SECTIONS_DIR) if re.match(r"^\d\d-", d))
sec_map = {}   # dirname -> {module_title, ext_topics(list), two_topics(list)}
for d in section_dirs:
    no = int(d.split("-")[0])
    if no == 0 or no >= 24:
        continue
    name_md = open(os.path.join(SECTIONS_DIR, d, "section.md"), encoding="utf-8").read()
    m = re.search(r"^# Moduł \d+:\s*(.+)$", name_md, re.M)
    if not m:
        print("Brak tytułu modułu w", d)
        continue
    mt = norm_title(m.group(1))
    sec_map[d] = {"mt": mt,
                  "ext": ext.get(mt, []),
                  "two": two.get(mt, [])}

unmatched = [d for d, v in sec_map.items() if not v["ext"] and not v["two"]]
print("Sekcje bez dopasowania w TOC:", unmatched)

# ---------- Rozwiązywanie konfliktów nazw plików ----------
# strona właściwa = ta, której sekcja odpowiada modułowi wg numeracji rozszerzonej;
# dla Cyruliki (sekcja 22) numeracja dwuletnia 14.x jest właściwa.
def desired_files(d, v):
    """zwraca listę (topic_num_from_course, topic_dict, semester_str)"""
    no = int(d.split("-")[0])
    out = []
    if d == "22-cyrulika-medyczna-felczerstwo":
        for t in v["two"]:
            out.append((t["num"], t, t["semester"]))
    elif v["ext"]:
        for t in v["ext"]:
            out.append((t["num"], t, t["semester"]))
    else:
        for t in v["two"]:
            out.append((t["num"], t, t["semester"]))
    return out

conflicts_removed = 0
pages_written = 0
gift_tf = gift_mc = 0

def render_page(num, t, dirname, mod_no_for_name, sem):
    items = "\n".join(f"- **{i+1}. {sub}**" for i, sub in enumerate(t["subs"]))
    if not items:
        items = ("- Omówienie podstaw teoretycznych tematu\n"
                 "- Zastosowanie praktyczne w procesie zdrowienia pacjenta\n"
                 "- Bezpieczeństwo pacjenta i granice kompetencji naturopaty")
    fn = f"page-{mod_no_for_name}-{num.split('.')[1]}-{slugify(t['title'])}.md"
    content = f"""<!--
Plik: {fn}
Typ pliku: Strona edukacyjna (page)
Konwersja: Markdown → HTML
Sekcja: {dirname}
Kurs: Kwalifikacyjny Kurs Zawodowy – Naturopata
-->

# {num}. {t['title']}

## Wprowadzenie

Strona tematyczna ({sem if sem else 'program kursu'}).
Temat zgodnie z połączonym spisem treści kursu: *{t['title']}*
(Punkty {num}.1–{num}.{len(t['subs'])} połączonego spisu treści.)

## Zagadnienia do opanowania

Po ukończeniu tego tematu uczestnik potrafi omówić i zastosować w praktyce
naturopatycznej każde z poniższych zagadnień szczegółowych:

{items}

## Cele szczegółowe

- Rozpoznanie i nazwanie struktur, mechanizmów i procedur objętych powyższymi zagadnieniami.
- Zastosowanie wiedzy w planowaniu działań naturopatycznych z zachowaniem zasady *primum non nocere*.
- Identyfikacja przeciwwskazań i sytuacji wymagających skierowania pacjenta do lekarza.

## Materiały do pobrania

Materiały poglądowe (ilustracje, filmy, dokumenty PDF) zostaną dodane w katalogu
`media/` kursu w kolejnym etapie prac redakcyjnych.

## Podsumowanie

Temat {num} („{t['title']}”) obejmuje {len(t['subs'])} zagadnień szczegółowych.
Przed przejściem do kolejnego tematu należy rozwiązać quiz sprawdzający
oraz wykonać zadanie modułowe.

## Pytania do refleksji

1. Jak zagadnienie „{t['title']}” wpływa na codzienną praktykę naturopatyczną?
2. Jakie są przeciwwskazania i środki ostrożności związane z tym tematem?
"""
    return fn, content

def esc(s):
    s = s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("#", "\\#")
    s = s.replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|")
    return s

all_pool_titles = []
for v in sec_map.values():
    for t in v["ext"] + v["two"]:
        all_pool_titles.append(t)

for d, v in sorted(sec_map.items()):
    pdir = os.path.join(SECTIONS_DIR, d)
    no = d.split("-")[0]
    desired = desired_files(d, v)
    wanted_names = set()
    new_refs = []
    gift_lines = []
    n_tf = n_mc = 0

    for num, t, sem in desired:
        mod_part, top_part = num.split(".")
        # numer modułu w nazwie pliku = numer sekcji kursu (poza Cyruliką: tam 14.x wg źródła dwuletniego)
        file_mod = "14" if d.startswith("22-") else str(int(no))
        fn, content = render_page(num, t, d, file_mod, sem)
        wanted_names.add(fn)
        path = os.path.join(pdir, fn)
        old_path = path  # jeśli istniał stary plik o innej nazwie – usuniemy poniżej
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        pages_written += 1
        new_refs.append((fn, f"{num}. {t['title']}"))

        kid = num.replace(".", "")
        gift_lines.append(f"// === Temat {num}: {t['title']} ===")
        for i, sub in enumerate(t["subs"]):
            if i % 2 == 0:
                stmt = f"Zagadnienie „{sub}” wchodzi w zakres tematu „{t['title']}” ({num})."
                ans = "TRUE"
            else:
                prev = t["subs"][i-1]
                stmt = f"Zagadnienie „{sub}” jest elementem zagadnienia „{prev}”, a nie tematu „{t['title']}” ({num})."
                ans = "FALSE"
            gift_lines.append(f"::tf-s{no}-{kid}-q{i+1}:: {esc(stmt)} {{{ans}}} //")
            n_tf += 1
        if len(t["subs"]) >= 2:
            pool = [x for x in all_pool_titles if x["num"] != num]
            wrong_t = pool[(int(kid) * 7) % len(pool)]
            wrong = wrong_t["subs"][int(kid) % len(wrong_t["subs"])] if wrong_t["subs"] else "Zagadnienie kontrolne"
            opts = [t["subs"][0], t["subs"][1], wrong]
            if len(t["subs"]) > 2:
                opts.insert(2, t["subs"][2])
            mc = [f"::mc-s{no}-{kid}:: Które z poniższych zagadnień należy bezpośrednio do tematu „{t['title']}” ({num})? {{"]
            for j, o in enumerate(opts):
                mark = "= " if j == 0 else "~ "
                mc.append(f"    {mark}{esc(o)}")
            mc.append("}")
            gift_lines.extend(mc)
            n_mc += 1

    # usuń zbędne stare strony (np. duplikaty z błędnym numerem modułu)
    for fn in os.listdir(pdir):
        m = re.match(r"^page-.+\.md$", fn)
        if m and fn not in wanted_names:
            os.remove(os.path.join(pdir, fn))
            conflicts_removed += 1

    # nadpisz sekcje w section.yaml (tylko bloczek page-*)
    ypath = os.path.join(pdir, "section.yaml")
    ytxt = open(ypath, encoding="utf-8").read()
    blocks = [f'  - type: page\n    ref: "{fn}"\n    name: "{name}"' for fn, name in new_refs]
    new_pages_block = "\n".join(blocks)
    ytxt_new = re.sub(r"(?:  - type: page\n    ref: \"page-[^\"]+\.md\"\n    name: \"[^\"]+\"\n)+",
                      new_pages_block + "\n", ytxt)
    if ytxt_new != ytxt:
        open(ypath, "w", encoding="utf-8").write(ytxt_new)

    # quiz
    qdir = os.path.join(pdir, "quiz-01")
    if os.path.isdir(qdir):
        with open(os.path.join(qdir, "questions.gift"), "w", encoding="utf-8") as f:
            f.write("\n".join(gift_lines) + "\n")
        gift_tf += n_tf
        gift_mc += n_mc

    # tabela w section.md
    spath = os.path.join(pdir, "section.md")
    txt = open(spath, encoding="utf-8").read()
    rows = []
    for num, t, sem in desired:
        rows.append(f"| {num} | page | {t['title']} | {len(t['subs'])} |")
    table = ("| Nr tematu | Typ zasobu | Temat | Liczba zagadnień |\n"
             "|-----------|------------|-------|------------------|\n" + "\n".join(rows) + "\n")
    pat = re.compile(r"\| Nr tematu \|[^\n]*\n\|[-| ]+\|\n(?:\|.*\n)+")
    txt2, cnt = pat.subn(table, txt)
    if cnt:
        open(spath, "w", encoding="utf-8").write(txt2)

print(f"Stron zapisano: {pages_written} | usunięto zbędnych: {conflicts_removed}")
print(f"Pytania GIFT: TF={gift_tf} MC={gift_mc}")
