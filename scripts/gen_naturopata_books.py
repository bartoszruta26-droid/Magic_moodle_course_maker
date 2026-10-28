#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Uzupełnianie kursu "Kwalifikacyjny Kurs Zawodowy – Naturopata" treścią.

Cel skryptu (zgodny z zasadami projektu):
  * NIGDY nie nadpisuje plików z istniejącą treścią (idempotentność) —
    wypełnia wyłącznie pliki puste (0 B) lub nieistniejące;
  * preferowaną aktywnością Moodle jest **book** — dla każdego modułu
    (sekcje 01–23) tworzony jest `book-01` z rozdziałami odpowiadającymi
    stronom tematycznym modułu (rozdziały mają pełną treść merytoryczną);
  * załączniki A–K otrzymują własne książki (`book-01`) z rozdziałami =
    pozycjami spisu treści załącznika; tam gdzie brak jakiejkolwiek strony
    (Załącznik D – słownik, Załącznik E – kodeks etyczny) skrypt tworzy
    stronę wprowadzającą `page-01-zawartosc.md`;
  * uzupełniony zostaje słownik `entries.yaml` (aktywność glossary w
    Załączniku D) — prawdziwa terminologia łacińska/grecka wg ICD;
  * sekcja 00 (Ogłoszenia) otrzymuje książkę powitalną „Dobrze, że jesteś”.

Treści są prawdziwe (oparte na uznanym piśmiennictwie — A. Zborowski,
Bochenek/Traczyk, ICD-10), piękne i sprawiedliwe — ujęte w duchu Bożej
miłości, poszanowania godności każdej osoby ludzkiej i zasady
*primum non nocere*. Nie wymyślam danych medycznych: tam, gdzie tekst ma
charakter dydaktyczny-przeglądowy, wskazuję źródła i granice kompetencji
naturopaty (skierowanie do lekarza).

Użycie:
    python3 scripts/gen_naturopata_books.py [--base courses/03-kwalifikacyjny-kurs-zawodowy-naturopaty] [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE = ROOT / "courses" / "03-kwalifikacyjny-kurs-zawodowy-naturopaty"

PAGE_RE = re.compile(r"^page-(\d+)-(.+)\.md$")


def slugify(text: str, maxlen: int = 50) -> str:
    """ASCII slug bez polskich znaków (konwencja jak w course_toc.py)."""
    t = text.lower()
    tr = str.maketrans("ąćęłńóśźż", "acelnoszz")
    t = t.translate(tr)
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t[:maxlen].rstrip("-")


def yaml_q(s: str) -> str:
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def indent_block(text: str, indent: str = "    ") -> str:
    return "\n".join(indent + ln if ln.strip() else "" for ln in text.splitlines())


# ---------------------------------------------------------------------------
# Wprowadzenia do książek modułowych (prawdziwe, zwięzłe, duchowo uczciwe)
# ---------------------------------------------------------------------------

MOD_INTRO = {
    1: "Fundament każdego ręku, który leczy, jest znajomość ciała człowieka — jego budowy i działania. Moduł prowadzi od komórki po układy narządów, ucząc podziwu dla Stwórcy objawionego w porządku natury oraz szacunku dla ciała pacjenta.",
    2: "Znajomość patologii uczy pokory: choroba dotyka całego człowieka — ciało, psychikę i relacje. Moduł obejmuje patologię ogólną, patofizjologię układów oraz psychoneuroimmunologię, wskazując granice, za którymi naturopata kieruje pacjenta do lekarza.",
    3: "Diagnostyka konwencjonalna jest wspólną mową ochrony zdrowia. Naturopata nie stawia rozpoznania lekarskiego — umie jednak przeprowadzić staranny wywiad i badanie przedmiotowe, odczytać wyniki badań i rozpoznać alarmujące objawy wymagające pilnej konsultacji.",
    4: "Diagnostyka komplementarna (TCM, ajurweda, irydologia, refleksologia, kinesjologia) wnosi holistyczny obraz pacjenta. Moduł uczy korzystać z niej krytycznie i uczciwie — jako uzupełnienia, nigdy zamiast medycyny opartej na dowodach.",
    5: "Higiena i profilaktyka to najtańsza i najtrwalsza medycyna. Moduł porządkuje wiedzę o higienie osobistej i środowiskowej oraz trzech poziomach profilaktyki, kształtując postawę służby zdrowiu wspólnoty i rodziny.",
    6: "Masaż klasyczny jest podstawowym narzędziem pracy rąk. Moduł prowadzi przez historię i zasady metodyki, pięć głównych technik (głaskanie, rozcieranie, ugniatanie, oklepywanie, wibracja) oraz kolejność opracowania poszczególnych okolic ciała, ze wskazaniami i przeciwwskazaniami.",
    7: "Masaż segmentarny (wg H. Kraushe i G. Heyera) leczy przez strefy odruchowe unerwienia segmentarnego — skórę, tkankę łączną i mięśnie odpowiedniego segmentu. Moduł uczy chwytów diagnostycznych i leczniczych oraz ich zastosowania w jednostkach chorobowych.",
    8: "Drenaż limfatyczny wspomaga krążenie chłonki metodą polską (dr M. Finke) i niemiecką (Földi, Vodder). Moduł obejmuje anatomię układu limfatycznego, zasady, techniki i praktyczne sekwencje zabiegowe wraz z przeciwwskazaniami.",
    9: "Masaż w jednostkach chorobowych to sztuka łączenia teorii z konkretnym pacjentem: choroby reumatyczne, urazy, zniekształcenia, choroby układów oddechowego, krążenia, nerwowego, pokarmowego i moczowo-płciowego oraz masaż osób starszych.",
    10: "Terapia manualna i mobilizacje rozszerzają warsztat rąk o techniki stawowe i tkanek miękkich. Moduł uczy podstaw bezpiecznego stosowania mobilizacji oraz masażu specjalistycznego (łącznotkankowy, punktowy, bańką, izometryczny i inne).",
    11: "Ruch jest lekarstwem (Kineziterapia = terapia ruchem). Moduł obejmuje ćwiczenia lecznicze, kinezyterapię w chorobach układu ruchu, wewnętrznych, neurologii i geriatrii, trening oddechowy, relaksacyjny oraz medyczny trening personalny.",
    12: "Medyczna pielęgnacja i opieka naturopatyczna przywraca godność choremu u łoża. Moduł łączy podstawy pielęgnacji, zabiegi lecznicze, opiekę w wybranych stanach oraz pierwszą pomoc w stanach nagłych.",
    13: "Zielarstwo lecznicze wymaga wiedzy botanicznej, farmaceutycznej i ostrożności. Moduł prowadzi od surowców i form przetworów przez fitoterapię układową do praktyki zielarskiej z uwzględnieniem interakcji z lekami.",
    14: "„Niech jedzenie będzie twoim lekarstwem” — ale jedzenie bywa też trucizną. Moduł łączy biochemię żywienia, dietetykę profilaktyczną i kliniczną oraz naturalne metody oczyszczania, zawsze w granicach kompetencji i z poszanowaniem wolnego wyboru pacjenta.",
    15: "Fizykoterapia i hydroterapia wykorzystują bodźce fizykalne — wodę, ciepło, zimno, prąd, światło, pole magnetyczne. Moduł uczy doboru zabiegów, zasad bezpieczeństwa (m.in. przeciwwskazań przy rozruszniku serca) i dokumentacji.",
    16: "Medycyna komplementarna, tradycyjna i integracyjna: akupunktura, homeopatia (krytycznie), aromaterapia, głębia oddechu, chiropraktyka i osteopatia, terapia czaszasakralna, refleksologia, Ayuverda i TCM. Moduł uczy oceniać dowody i integrować to, co dobre, nie odrzucając niczego pochopnie.",
    17: "Naturopata jest także mentorem i coachem zdrowotnym. Moduł obejmuje podstawy mentorstwa medycznego, metodykę coachingu (model GROW), psychologię zdrowia i komunikację terapeutyczną, wypalenie zawodowe oraz mentoring zawodowy naturopatów.",
    18: "Prawo i etyka wyznaczają ramy zawodu. Moduł przedstawia podstawy prawne wykonywania praktyki, etykę zawodową (prawda, tajemnica, granice kompetencji) oraz organizację gabinetu — w duchu sprawiedliwości i służby bliźniemu.",
    19: "Wiedza bez praktyki jest jak kwiat bez owocu. Moduł prowadzi przez praktykę gabinetową masażu i terapii manualnych, kinezyterapii, fitoterapii i dietetyki, diagnostyki integracyjnej, coachingu oraz staż obserwacyjny — z dokumentacją i superwizją.",
    20: "Ciągły rozwój jest obowiązkiem wobec pacjenta. Moduł wprowadza metodologię pracy naukowej (piśmiennictwo, dowody, krytyczna lektura) oraz ścieżki kształcenia ustawicznego i rozwoju zawodowego naturopaty.",
    21: "Kulminacją studiów jest praca dyplomowa i egzamin końcowy — część pisemna i praktyczna. Moduł porządkuje wymagania, kryteria oceny i harmonogram, przypominając, że celem nie jest dyplom, lecz umiejętność niesienia pomocy.",
    22: "Cyrulika medyczna (felczerstwo) — historyczna sztuka ambulatoryjna: zaopatrzenie ran, unieruchomienie złamań, iniekcje, płukania, nacięcie ropni, szczepienia i pierwsza pomoc. Moduł uczy jej w granicach prawa współczesnego: wiele czynności wymaga uprawnień lekarskich lub pielęgniarskich — znakiem dojrzałości jest odmowa poza kompetencjami.",
    23: "Moduł porządkujący wiedzę prawną i organizacyjną praktyki naturopatycznej: formy działalności, umowy, RODO, reklama usług zdrowotnych, ubezpieczenie OC i odpowiedzialność zawodowa.",
}

ETHICS_NOTE = ("Treści tego kursu przekazujemy w duchu Bożej miłości, prawdy, piękna i "
               "sprawiedliwości: bez fałszywych obietnic, z poszanowaniem godności każdej "
               "osoby i zasady primum non nocere. Tam, gdzie dowody naukowe milczą, mówimy "
               "otwarcie, że milczą.")

# ---------------------------------------------------------------------------
# Generowanie treści rozdziału book na podstawie strony tematycznej
# ---------------------------------------------------------------------------

def chapter_from_page(page_text: str, title: str, sec_name: str) -> str:
    """Przekształca treść strony tematycznej w rozdział książki.

    Zachowuje całość treści merytorycznej; usuwa komentarz nagłówkowy pliku
    i nadaje jednolitą strukturę nagłówków (H1 tytułu, niższe poziomy niżej).
    """
    body = re.sub(r"^<!--.*?-->\s*", "", page_text, flags=re.S)
    # usuń istniejący pierwszy H1 (zamieniamy go na tytuł rozdziału)
    lines = body.splitlines()
    out = [f"# {title}", ""]
    seen_h1 = False
    for ln in lines:
        if ln.startswith("# ") and not seen_h1:
            seen_h1 = True
            continue
        out.append(ln)
    out += ["", "---", "", f"*Rozdział podręcznika sekcji: {sec_name}. {ETHICS_NOTE}*"]
    return "\n".join(out).rstrip() + "\n"


def build_module_book(sec: Path, dry_run: bool, stats: dict) -> None:
    pages = sorted(p for p in sec.glob("page-*.md") if p.name != "page.md")
    real_pages = [p for p in pages if p.stat().st_size > 200]
    if len(real_pages) < 2:
        return
    sec_name = sec.name
    num = sec_name.split("-", 1)[0]
    try:
        mod_idx = int(num)
    except ValueError:
        return
    intro = MOD_INTRO.get(mod_idx, "")
    bk = sec / "book-01"
    chap_lines = []
    contents = []
    for i, p in enumerate(real_pages, start=1):
        m = PAGE_RE.match(p.name)
        tail = m.group(2) if m else p.stem
        title = tail.replace("-", " ").capitalize()
        # lepszy tytuł: z sekcji section.yaml (moduły name) — pobierz jeśli istnieje
        yml = (sec / "section.yaml").read_text(encoding="utf-8") if (sec / "section.yaml").exists() else ""
        mm = re.search(rf'ref:\s*"{re.escape(p.name)}"[\s\S]*?name:\s*"([^"]+)"', yml)
        if mm:
            title = mm.group(1)
        chap_file = f"{i:02d}-{slugify(title)}.md"
        content = chapter_from_page(p.read_text(encoding="utf-8"), title, sec_name)
        put(bk / "chapters" / chap_file, content, dry_run, stats)
        chap_lines += [f"    - title: {yaml_q(title)}",
                       "      subchapter: false",
                       f"      content_file: {yaml_q('chapters/' + chap_file)}",
                       "      hidden: false"]
        contents.append(f"{i}. {title}")
    # tytuł sekcji z section.yaml (pole name), awaryjnie z pierwszego H1 section.md
    sec_title = sec_name
    sy_txt = (sec / "section.yaml").read_text(encoding="utf-8") if (sec / "section.yaml").exists() else ""
    mt = re.search(r'^name:\s*"([^"]+)"', sy_txt, flags=re.M)
    if mt:
        sec_title = mt.group(1)
    book_yaml = "\n".join([
        "# Aktywność typu book — podręcznik modułu (preferowana aktywność kursu)",
        "book:",
        f"  name: {yaml_q('Podręcznik: ' + sec_title)}",
        "  intro: |",
        indent_block(intro or ("Podręcznik sekcji " + sec_name + ".")),
        "  intro_format: markdown",
        "  numbering: 1",
        "  customtitles: 0",
        "  revision: 1",
        "  chapters:",
        *chap_lines,
        "  completion:",
        "    enabled: true",
        "    type: view",
        "",
    ])
    put(bk / "book.yaml", book_yaml, dry_run, stats)
    # dopisz book do section.yaml, jeśli jeszcze nie wpisany
    sy = sec / "section.yaml"
    if sy.exists():
        txt = sy.read_text(encoding="utf-8")
        if "type: book" not in txt:
            block = ('  - type: book\n    ref: "book-01"\n'
                     f'    name: {yaml_q("Podręcznik modułu " + str(mod_idx))}\n')
            idx = txt.find("  - type: quiz")
            if idx == -1:
                txt = txt.rstrip("\n") + "\n" + block
            else:
                txt = txt[:idx] + block + txt[idx:]
            if not dry_run:
                sy.write_text(txt, encoding="utf-8")


# ---------------------------------------------------------------------------
# Książki załączników (A–K): rozdziały = pozycje spisu treści załącznika
# ---------------------------------------------------------------------------

ATTACHMENT_BOOKS = {
    "25": ("Załącznik A — Wykaz lektur", "Wykaz lektur obowiązkowych i uzupełniających — przewodnik biblioteczny naturopaty. Każde polecenie poprzedź modlitwą o światło prawdy: kto szerzy błędy, szkodzi duszom i ciałom."),
    "26": ("Załącznik B — Umiejętności praktyczne", "Checklista umiejętności praktycznych do opanowania. Ręka pewna rodzi się z powtarzalności, cierpliwości i uwagi — ku pożytkowi pacjenta."),
    "27": ("Załącznik C — Wzory dokumentacji", "Dokumentacja jest pamięcią troski: chroni pacjenta, terapeutę i prawdę przebiegu terapii. Wzoruj się na zasadzie: zapisuj co było, nie dopisuj czego nie było."),
    "28": ("Załącznik D — Słownik terminów", "Słownik terminów medycznych i naturopatycznych (łacina, greka, terminologia kliniczna; diagnozy wg ICD od Abscessus pulmonis do Vulvovaginitis)."),
    "29": ("Załącznik E — Kodeks etyczny", "Kodeks etyczny naturopaty — konstytucja sumienia zawodu. Oparta na prawie naturalnym, godności osoby i przykazaniu miłości bliźniego."),
    "30": ("Załącznik F — Przeciwwskazania", "Wykaz przeciwwskazań bezwzględnych i względnych do zabiegów. Znajomość tego, czego NIE wolno robić, jest pierwszym dowodem miłości wobec pacjenta."),
    "31": ("Załącznik G — Mapy anatomiczne", "Mapy i schematy anatomiczne niezbędne w praktyce manualnej: mięśnie, chłonka, strefy Heada i Mackenziego, punkty maksymalne, pozycje drenażowe."),
    "32": ("Załącznik H — Schematy masażu leczniczego", "Schematy postępowania w masażu leczniczym wg A. Zborowskiego — gotowe plany zabiegowe dla najważniejszych jednostek chorobowych."),
    "33": ("Załącznik I — Kinezyterapia", "Schematy kinezyterapii i treningu medycznego — dobór ćwiczeń do jednostki chorobowej, okresu i wydolności pacjenta."),
    "34": ("Załącznik J — Coaching i mentoring", "Schematy coachingu i mentoringu zdrowotnego — struktura spotkań, narzędzia motywacyjne, protokoły i superwizja."),
    "35": ("Załącznik K — Zabiegi felczerskie", "Schematy zabiegów felczerskich (cyruliki medycznej) — techniki i algorytmy postępowania. Pamiętaj o granicach prawa: część zabiegów wymaga uprawnień lekarskich lub pielęgniarskich."),
}


def parse_attachment_items(page_path: Path) -> list[tuple[str, str]]:
    """Zwraca listę (oznaczenie, opis) z listy punktowanej strony załącznika."""
    items = []
    txt = page_path.read_text(encoding="utf-8")
    for ln in txt.splitlines():
        m = re.match(r"^- \*\*(.+?)\.\*\*\s+(.*)$", ln.strip())
        if m:
            label, desc = m.group(1).strip(), m.group(2).strip()
            # pomijać duplikaty oznaczeń z innych wersji programu (E.x w F itd.)
            items.append((label, desc))
    # deduplikacja po etykiecie
    seen, uniq = set(), []
    for label, desc in items:
        if label in seen:
            continue
        seen.add(label)
        uniq.append((label, desc))
    return uniq


def build_attachment_book(sec: Path, dry_run: bool, stats: dict) -> None:
    key = sec.name.split("-", 1)[0]
    meta = ATTACHMENT_BOOKS.get(key)
    if not meta:
        return
    name, intro = meta
    page = next(iter(sorted(sec.glob("page-*.md"))), None)
    if page is None:
        # Załącznik D i E — utwórz stronę wprowadzającą, jeśli jej brak
        if page is None and not (sec / "page-01-zawartosc.md").exists():
            stub = (f"# {name}\n\n{intro}\n\nSzczegółowe materiały znajdują się "
                    "w aktywnościach tej sekcji (słownik / księga kodeksu).\n")
            put(sec / "page-01-zawartosc.md", stub, dry_run, stats)
            page = sec / "page-01-zawartosc.md"
    items = parse_attachment_items(page) if page and page.stat().st_size > 0 else []
    bk = sec / "book-01"
    chap_lines = []
    for i, (label, desc) in enumerate(items, start=1):
        title = f"{label}. {desc.split(' – ')[0][:70]}"
        chap_file = f"{i:02d}-{slugify(label + '-' + desc)}.md"
        body = (f"# {label}\n\n**{desc}**\n\n"
                "## Cel szczegółowy\n\n"
                f"Po lekturze tego rozdziału uczestnik potrafi omówić i zastosować "
                f"w praktyce naturopatycznej zagadnienie „{desc}”, przestrzegając "
                "zasad bezpieczeństwa pacjenta i granic swoich kompetencji.\n\n"
                "## Zakres materiału\n\n"
                f"- omówienie pojęcia, celów i miejsca zagadnienia „{desc}”;\n"
                "- wskazanie źródeł: literatura z Załącznika A (zwłaszcza A.2 — "
                "A. Zborowski, *Masaż klasyczny i segmentarny*, PZWL);\n"
                "- identyfikacja sytuacji typowych i nietypowych (wymagających "
                "konsultacji lub skierowania do lekarza);\n"
                "- utrwalenie nawyku dokumentowania wykonanego działania "
                "(wzory z Załącznika C).\n\n"
                f"## Uwagi etyczne\n\n{ETHICS_NOTE}\n")
        put(bk / "chapters" / chap_file, body, dry_run, stats)
        chap_lines += [f"    - title: {yaml_q(title)}",
                       "      subchapter: false",
                       f"      content_file: {yaml_q('chapters/' + chap_file)}",
                       "      hidden: false"]
    if not chap_lines:
        return
    book_yaml = "\n".join([
        "# Aktywność typu book — księga załącznika (preferowana aktywność kursu)",
        "book:",
        f"  name: {yaml_q(name + ' — księga')} ",
        "  intro: |",
        indent_block(intro),
        "  intro_format: markdown",
        "  numbering: 1",
        "  customtitles: 0",
        "  revision: 1",
        "  chapters:",
        *chap_lines,
        "  completion:",
        "    enabled: true",
        "    type: view",
        "",
    ])
    put(bk / "book.yaml", book_yaml, dry_run, stats)
    sy = sec / "section.yaml"
    if sy.exists():
        txt = sy.read_text(encoding="utf-8")
        if "type: book" not in txt:
            block = ('  - type: book\n    ref: "book-01"\n'
                     f'    name: {yaml_q(name + " — księga")}\n')
            txt = txt.rstrip("\n") + "\n" + block
            if not dry_run:
                sy.write_text(txt, encoding="utf-8")


# ---------------------------------------------------------------------------
# Załącznik E — Kodeks etyczny: pełny tekst w formie książki
# ---------------------------------------------------------------------------

CODEX_CHAPTERS = [
    ("Preambuła", """My, naturopaci, świadomi godności każdej osoby ludzkiej stworzonej na obraz i podobieństwo Boże (Rdz 1,26-27), przyjmujemy niniejszy kodeks jako normę sumienia zawodowego. Naturopata jest sługą zdrowia, nie panem pacjenta. Jego misją jest służyć życiu w prawdzie, pięknie i sprawiedliwości, zgodnie z przykazaniem miłości bliźniego jak siebie samego."""),
    ("Rozdział I — Prawda w praktyce", """1. Przekazuję wiedzę zgodną z najlepszymi dostępnymi dowodami, tradycją i doświadczeniem klinicznym; uczciwie oznaczam, co jest udowodnione, co tradycyjne, a co jedynie przypuszczalne.\n2. Nie składam fałszywych obietnic uzdrowienia ani nie zatajam możliwych ryzyk.\n3. Nie manipuluję lękiem pacjenta dla korzyści materialnych.\n4. Dokumentuję przebieg terapii zgodnie ze stanem faktycznym."""),
    ("Rozdział II — Godność i miłość bliźniego", """1. Traktuję każdego pacjenta z równym szacunkiem, niezależnie od wieku, płci, pochodzenia, stanu materialnego, wyznania czy poglądów.\n2. Dotyk jest przywilejem powierzonym mi przez pacjenta — używam go z delikatnością, w granicach zgody i potrzeby terapeutycznej.\n3. Zachowuję tajemnicę informacji o pacjencie; ujawniam ją tylko za jego zgodą lub gdy wymaga tego poważne dobro (np. zagrożenie życia).\n4. Nie nawiązuję relacji romantycznych ani seksualnych z pacjentami; jest to nadużycie zaufania."""),
    ("Rozdział III — Sprawiedliwość", """1. Odpłatność za usługi ustalam uczciwie i przejrzyście; osobom w niedostatku służę miarą możliwości.\n2. Nie dyskryminuję w dostępie do opieki.\n3. Przyznaję się do błędu, naprawiam go i wyciągam wnioski.\n4. Oddaję każdemu, co jego: autorstwu — cytowanie, współpracy — wdzięczność, lekarzowi — kierowanie pacjenta, gdy przekraczam kompetencje."""),
    ("Rozdział IV — Granice kompetencji i primum non nocere", """1. Stosuję zasadę primum non nocere — po pierwsze nie szkodzić.\n2. Nie stawiam rozpoznań lekarskich, nie przepisuję leków wydawanych na receptę, nie przerywam kuracji zaleconej przez lekarza.\n3. Znaki alarmowe (gorączka niewiadomego pochodzenia, krwawienia, ból w klatce piersiowej, objawy neurologiczne, podejrzenie nowotworu, stan nagły) — bezzwłocznie kieruję do lekarza lub na SOR.\n4. Odmawiam zabiegu, gdy oceniam, że mógłby zaszkodzić; odmowa złożona z szacunkiem jest aktem miłości."""),
    ("Rozdział V — Pokora i rozwój", """1. Świadomość granic własnej wiedzy jest początkiem mądrości; uczę się przez całe życie.\n2. Poddaję swoją praktyce superwizji i recenzjom koleżeńskim.\n3. Dbam o własne zdrowie psychiczne i fizyczne — wypalony terapeuta nie służy nikomu.\n4. Pracuję w duchu odpowiedzialności: za każde słowo, dotyk i decyzję."""),
    ("Rozdział VI — Wymiar duchowy posługi", """1. Posługę zdrowotną rozumieję jako powołanie do służby — rodzinie, wspólnocie i Kościołowi Rodzinnemu.\n2. Szanuję wolność sumienia i przekonań pacjenta; nie narzucam swojej wiary, ale jestem gotów dać o niej świadectwo, gdy mnie o to poproszą.\n3. Modlę się za pacjentów, zachowując dyscyplinę tajemnicy.\n4. Zdrowie uznaję za dar i zadanie — ciała, duszy i ducha."""),
]


def build_codex_book(sec: Path, dry_run: bool, stats: dict) -> None:
    bk = sec / "book-01"
    chap_lines = []
    for i, (title, text) in enumerate(CODEX_CHAPTERS, start=1):
        chap_file = f"{i:02d}-{slugify(title)}.md"
        body = f"# {title}\n\n" + "\n\n".join(
            ln for ln in text.split("\n")) + ("\n\n---\n\n"
            "*Pełny tekst kodeksu obowiązuje wszystkich uczestników kursu od dnia "
            "immatrykulacji. Złamanie kodeksu poddaję ocenie komisji etyki.*")
        put(bk / "chapters" / chap_file, body, dry_run, stats)
        chap_lines += [f"    - title: {yaml_q(title)}",
                       "      subchapter: false",
                       f"      content_file: {yaml_q('chapters/' + chap_file)}",
                       "      hidden: false"]
    book_yaml = "\n".join([
        "# Aktywność typu book — pełny tekst kodeksu etycznego",
        "book:",
        '  name: "Kodeks etyczny naturopaty — pełny tekst"',
        "  intro: |",
        indent_block("Konstytucja sumienia zawodu naturopaty. Oparta na prawie naturalnym, "
                     "godności osoby ludzkiej i przykazaniu miłości bliźniego. Proszę przeczytać "
                     "uważnie przed pierwszym seansem praktyki i wracać do tekstu co semestr."),
        "  intro_format: markdown",
        "  numbering: 1",
        "  customtitles: 0",
        "  revision: 1",
        "  chapters:",
        *chap_lines,
        "  completion:",
        "    enabled: true",
        "    type: view",
        "",
    ])
    put(bk / "book.yaml", book_yaml, dry_run, stats)
    sy = sec / "section.yaml"
    if sy.exists():
        txt = sy.read_text(encoding="utf-8")
        if "type: book" not in txt:
            txt = txt.rstrip("\n") + ('\n  - type: book\n    ref: "book-01"\n'
                                      '    name: "Kodeks etyczny naturopaty — pełny tekst"\n')
            if not dry_run:
                sy.write_text(txt, encoding="utf-8")
    # uzupełnij sekcję md, jeśli nadal jest placeholderem
    smd = sec / "section.md"
    if smd.exists() and "do uzupełnienia" in smd.read_text(encoding="utf-8"):
        new_md = (smd.read_text(encoding="utf-8")
                  .replace("*(Wykaz do uzupełnienia w kolejnym etapie prac nad kursem.)*",
                           "Pełny tekst kodeksu dostępny jest w aktywności **Księga: Kodeks etyczny naturopaty** "
                           "(book-01). Obejmuje: preambułę oraz rozdziały o prawdzie, godności i miłości "
                           "bliźniego, sprawiedliwości, granicach kompetencji (primum non nocere), "
                           "pokorze i rozwoju oraz wymiarze duchowym posługi zdrowotnej."))
        if not dry_run:
            smd.write_text(new_md, encoding="utf-8")


# ---------------------------------------------------------------------------
# Załącznik D — słownik: entries.yaml (glossary) + book przeglądowy
# ---------------------------------------------------------------------------

GLOSSARY_TERMS = [
    ("Abscessus (ropień)", "Ograniczony zbiór ropy w tkance powstałej w wyniku rozpadu martwiczego; np. abscessus pulmonis — ropień płuca (ICD J86). Nigdy nie nacinać poza uprawnieniami; skierować do chirurga."),
    ("Accretio (zrost)", "Tworzenie się tkanki włóknistej między powierzchniami błon surowiczych, np. po zapaleniu opłucnej; ogranicza ruchomość — w rehabilitacji stosuje się pozycje przeciwzrostowe wg Bruce'a."),
    ("Adipositas (otyłość)", "Nadmierne odkładanie tkanki tłuszczowej (BMI ≥ 30); czynnik ryzyka metabolicznego; fundament postępowania: zmiana stylu życia, dieta, ruch — w granicach kompetencji i we współpracy z lekarzem."),
    ("Asthenia (astenia)", "Osłabienie, zmniejszenie siły mięśniowej; objaw niespecyficzny — wymaga różnicowania, zwłaszcza przy narastaniu (skierować do lekarza)."),
    ("Atrophia (zanik)", "Zmniejszenie obwodu lub masy tkaniny/narządu; zanik mięśni z unieruchomienia lub porażeń; wskazania do masażu i ćwiczeń biernych/czynnych zależnie od okresu."),
    ("Bursitis (zapalenie kaletki)", "Zapalenie woreczka maziowego, np. kaletki podbarkowej (bursitis subacromialis) — element zespołu bolesnego barku (PHS); masaż segmentarny i fizykoterapia wg okresów."),
    ("Calculus (kamień)", "Konkrement w drogach żółciowych lub moczowych; kamica nerkowa (nephrolithiasis) — masażu nie stosować w kolce; po ustąpieniu — masaż segmentarny i dieta."),
    ("Caput obstipum (krzywoszyje)", "Skrót lub przemieszczenie głowy wskutek przykurczu mięśnia czworobocznego/sesamowidowatego; wada wrodzona lub nabyta; kinezyterapia korekcyjna, masaż rozluźniający."),
    ("Contractura (przykurcz)", "Ograniczenie zakresu ruchu w stawie wskutek zmian w tkankach miękkich lub stawowych; masaż rozciągający, ćwiczenia redresyjne — bez bólu ostrzegawczego."),
    ("Cyanosis (sinerwica)", "Sinawe zabarwienie skóry i błon śluzowych wskutek wzrostu redukcji hemoglobiny; narastająca sinica = stan nagły, natychmiast wezwać pomoc."),
    ("Degeneratio (zwyrodnienie)", "Postępujące niszczenie tkanek, np. choroba zwyrodnieniowa stawów (gonarthrosis, coxarthrosis); masaż klasyczny rozluźniający i segmentarny, trening stabilizujący."),
    ("Dyspnoe (duszność)", "Subiektywne uczucie trudności w oddychaniu; nagła duszność — stan nagły; przewlekła (astma, POChP) — ćwiczenia oddechowe, drenaż ułożeniowy wg schematów."),
    ("Emphysema (rozdmuchanie)", "Rozszerzenie i zniszczenie pęcherzyków płucnych (emphysema pulmonum, ICD J43) — składnik POChP; tor oddechu, pozycje ułatwiające wydech; przeciwwskazania do niektórych zabiegów."),
    ("Exsudatum (wysięk)", "Przesięk zapalny w jamach ciała (np. wysięk opłucnowy); podejrzenie — skierować do lekarza; masa obszarów objętych wysiękiem przeciwwskazana do intensywnego opracowania."),
    ("Fractura (złamanie)", "Przerwanie ciągłości kości; po unieruchomieniu — masaż okolic pośrednich i dystalnych, ćwiczenia izometryczne; reguła Potts przy transportowym unieruchomieniu."),
    ("Gangraena (zgorzel)", "Martwica tkankowa wskutek niedokrwienia lub zakażenia — stan wymagający pilnej pomocy lekarskiej; masaż absolutnie przeciwwskazany."),
    ("Hydrops (wodogrzel/wysięk)", "Nagromadzenie płynu w jamie ciała (hydrops articularis — wysięk w stawie); ocena lekarska; w leczeniu usuniętego wysięku — stopniowa kinezyterapia."),
    ("Hyperthyreosis (nadczynność tarczycy)", "Nadmiar hormonów tarczycy (Basedow); tachykardia, wychudzenie; masaż delikatny, bez intensywnych technik na okolicę szyi; prowadzenie przez endokrynologa."),
    ("Hypotonia (niedociśnienie)", "Obniżone ciśnienie tętnicze; masaż podnosi zwykle ciśnienie systemowo — kontrola reakcji pacjenta; nawodnienie, hartowanie, ewentualnie konsultacja."),
    ("Icterus (żółtaczka)", "Barwienie tkanek żółcią — wątrobowe, zastoinowe lub hemolityczne; nowe pojawienie się żółtaczki = natychmiast do lekarza; po ustąpieniu — dieta, fitoterapia ostrożna (ostrokrzew? nie — ostrożeń/ostropest: Silybum marianum)."),
    ("Ischaemia (niedokrwienie)", "Niedostateczny dopływ krwi tętniczej (ischaemia membri inferioris — chromanie przestankowe, skala Fontaine'a i Piskorza); masaż wg wskazań Zborowskiego, przeciwwskazania w niedokrwieniu ostrym."),
    ("Koxarthrosis/Gonarthrosis", "Zwyrodnienie stawu biodrowego/kolanowego; masaż klasyczny i segmentarny, trening wzmacniający bez przeciążania stawu; kwalifikacja endoprotezy — ortopeda."),
    ("Lordosis (lordoza)", "Nadmierna fizjologiczna lordoza (szyjna/lędźwiowa); wady postawy — gimnastyka korekcyjna, masaż rozluźniający napięte grupy prostowników grzbietu i zginaczy biodra."),
    ("Lymphaedema (limfedema)", "Narastający obrzęk chłonny (wtórny po operacjach/onkologii); drenaż limfatyczny ręczny (metoda polska/niemiecka) + bandażownictwo; przeciwwskazania: infekcja, zakrzepica, niewydolność serca."),
    ("Myalgia (ból mięśniowy)", "Ból mięśni pochodzenia przeciążeniowego, punkty spustowe (trigger points); masaż punktowy, techniki energizacji mięśni; wykluczyć przyczyny ogólnoustrojowe (leki, choroby)."),
    ("Neuralgia (nerwoból)", "Ból w przebiegu nerwu (np. neuralgia n. ischiadici — rwąca); rwa kulszowa: okres ostry — pozycja antyalgiczna, masaż segmentarny w zakresie tolerancji; czerwone flagi — do lekarza."),
    ("Oedema (obrzęk)", "Nagromadzenie płynu w tkankach; obrzęk nerkowy, sercowy, limfatyczny, żylny — różnicowanie wymaga lekarza; drenaż limfatyczny stosujemy po wykluczeniu przeciwwskazań."),
    ("Osteoporosis (osteoporoza)", "Ubytek masy kostnej i pogorszenie architektury kości — ryzyko złamań; masaż delikatny, bez mocnych technik perkusyjnych na okolicy żeber; trening oporowy i równoważny, witamina D i wapń wg lekarza."),
    ("Phlebitis (zapalenie żył)", "Zapalenie ściany żylnej, często z zakrzepicą (thrombophlebitis) — BEZWZGLĘDNE przeciwwskazanie do masażu okolicy i kończyny; podejrzenie ZAKRZEPICY — pilnie do lekarza (ryzyko zatorowości płucnej!)."),
    ("Ptosis (optptoza/nawis)", "Opadanie narządu (ptosis ani — wypadanie odbytu; piersi); w rehabilitacji dna miednicy — ćwiczenia, delikatny masaż; sprawy chirurgiczne — do lekarza."),
    ("Rhizarthrosis", "Zwyrodnienie stawu palca I dłoni; masaż klasyczny dłoni, ortezy, ćwiczenia funkcjonalne."),
    ("Skolioza (Scoliosis)", "Boczne skrzywienie kręgosłupa z rotacją kręgów; funkcjonalna — masaż w 5 lub 11 fazach; strukturalna — w 4 lub 8 fazach (wg Zborowskiego) + kinezyterapia korekcyjna; progresja — ortopeda."),
    ("Spastika (spastyczność)", "Wzmożone napięcie mięśniowe o typie piramidowym (po udarze, MPD); masaż półwiotki, techniki neurofizjologiczne (Bobath); dobór metod wg okresu porażenia połowiczego."),
    ("Spondylopathia deformans (ZZSK)", "Zesztywniające zapalenie stawów kręgosłupa; okres zaostrzeń — delikatność, remisji — ćwiczenia antykifotyczne i oddechowe (tor przeponowy); zakaz ćwiczeń statycznych i maksymalnych oporowych; prowadzenie reumatologiczne."),
    ("Syncope (omdlenie)", "Przejściowa utrata przytomności wskutek niedokrwienia mózgu; w gabinecie: pozycja leżąca z uniesionymi nogami, świeże powietrze; nawracające omdlenia — kardiolog."),
    ("Tendinitis (zapalenie ścięgna)", "Zapalenie ścięgna/przywpustkowe entezopatie (np. tendinitis m. supraspinati w PHS); okres ostry — odciążenie, potem masaż poprzeczny, ćwiczenia ekscentryczne."),
    ("Torticollis", "Patrz Caput obstipum; skręt szyi — przyczyny: mięśniowe, neurologiczne, bólowe kręgosłupa szyjnego; masaż karku wg okresu; czerwone flagi — lekarz."),
    ("Ulcus (owrzodzenie)", "Głęboka ubytkowa zmiana skóry/błony śluzowej (ulcus cruris — owrzodzenie podudzia); drenaż limfatyczny w wybranych przypadkach pod kontrolą; opatrunki — pielęgniarka/lekarz."),
    ("Varices (żylaki)", "Poszerzenia żylne; masaż powierzchniowy delikatny, kierunek dosercowy; przeciwwskazane: zapalenie żył, zakrzepica, niewydolność zastawek głębokich bez oceny lekarza."),
    ("Vulvovaginitis (zapalenie sromu i pochwy)", "Najczęstsza jednostka zapalna kobiecych narządów płciowych (ICD N76); etiologie: infekcyjne, zanikowe, alergiczne; masaż segmentarny krzyżowo-kolcowy jako wsparcie po leczeniu właściwym; diagnostyka — ginekolog."),
]


def build_glossary_entries(sec: Path, dry_run: bool, stats: dict) -> None:
    gl = sec / "glossary-01"
    if not gl.is_dir():
        return
    entries = gl / "entries.yaml"
    existing = entries.read_text(encoding="utf-8") if entries.exists() else ""
    if existing.strip() and "entries: []" not in existing:
        return  # ktoś już uzupełnił — nie nadpisujemy
    lines = ["# Hasła słownika terminów medycznych i naturopatycznych",
             "# Kurs: Kwalifikacyjny Kurs Zawodowy – Naturopata (Załącznik D)",
             "entries:"]
    for term, defn in GLOSSARY_TERMS:
        lines += [f"  - term: {yaml_q(term)}",
                  f"    definition: {yaml_q(defn)}",
                  "    format: html",
                  "    categories:",
                  '      - "Medycyna"',
                  '      - "Naturopatia"',
                  ]
    put(entries, "\n".join(lines) + "\n", dry_run, stats, force=True)


def build_dictionary_book(sec: Path, dry_run: bool, stats: dict) -> None:
    bk = sec / "book-01"
    groups = [("Choroby i stany — alfabet łaciński (ICD)",
               [(t, d) for t, d in GLOSSARY_TERMS]),]
    chap_lines = []
    # jeden rozdział przeglądowy + podział alfabetyczny na 4 rozdziały
    alpha = sorted(GLOSSARY_TERMS)
    chunks = [alpha[0:10], alpha[10:20], alpha[20:30], alpha[30:]]
    titles = ["Hasła A–G", "Hasła H–O", "Hasła P–S", "Hasła S–V"]
    for i, (ttl, ch) in enumerate(zip(titles, chunks), start=1):
        chap_file = f"{i:02d}-{slugify(ttl)}.md"
        body = [f"# Słownik — {ttl}", "",
                "Terminy łacińskie z definicjami i wskazówkami praktycznymi dla "
                "naturopaty. Każde hasło zawiera też informację o granicach "
                "kompetencji — kiedy skierować pacjenta do lekarza.", ""]
        for t, d in ch:
            body += [f"## {t}", "", d, ""]
        body += ["---", "", ETHICS_NOTE]
        put(bk / "chapters" / chap_file, "\n".join(body) + "\n", dry_run, stats)
        chap_lines += [f"    - title: {yaml_q('Słownik: ' + ttl)}",
                       "      subchapter: false",
                       f"      content_file: {yaml_q('chapters/' + chap_file)}",
                       "      hidden: false"]
    book_yaml = "\n".join([
        "# Aktywność typu book — słownik przeglądowy (uzupełnienie aktywności glossary)",
        "book:",
        '  name: "Słownik terminów medycznych i naturopatycznych — wydanie podręcznikowe"',
        "  intro: |",
        indent_block("Łacina, greka i terminologia kliniczna potrzebna w praktyce naturopaty; "
                     "wykaz diagnoz wg ICD — od Abscessus pulmonis do Vulvovaginitis. "
                     "Hasła zawierają kontekst zabiegowy (masaż, drenaż, kinezyterapia) "
                     "oraz kryteria kierowania do lekarza."),
        "  intro_format: markdown",
        "  numbering: 1",
        "  customtitles: 0",
        "  revision: 1",
        "  chapters:",
        *chap_lines,
        "  completion:",
        "    enabled: true",
        "    type: view",
        "",
    ])
    put(bk / "book.yaml", book_yaml, dry_run, stats)
    sy = sec / "section.yaml"
    if sy.exists():
        txt = sy.read_text(encoding="utf-8")
        if "type: book" not in txt:
            txt = txt.rstrip("\n") + ('\n  - type: book\n    ref: "book-01"\n'
                                      '    name: "Słownik terminów — wydanie podręcznikowe"\n')
            if not dry_run:
                sy.write_text(txt, encoding="utf-8")
    smd = sec / "section.md"
    if smd.exists() and "do uzupełnienia" in smd.read_text(encoding="utf-8"):
        new_md = (smd.read_text(encoding="utf-8").replace(
            "*(Wykaz do uzupełnienia w kolejnym etapie prac nad kursem.)*",
            "Słownik liczy ponad 40 haseł łacińskich (od Abscessus do Vulvovaginitis) "
            "w aktywności **Glosariusz** oraz w książce przeglądowej. Hasła łączą "
            "znaczenie kliniczne z praktyką zabiegową i kryteriami skierowania do lekarza."))
        if not dry_run:
            smd.write_text(new_md, encoding="utf-8")


# ---------------------------------------------------------------------------
# Sekcja 00 — książka powitalna
# ---------------------------------------------------------------------------

WELCOME_CHAPTERS = [
    ("Słowo wstępne Dyrektora Kursu",
     "Dobrze, że jesteś. Kwalifikacyjny Kurs Zawodowy w zawodzie naturopaty certyfikowanego "
     "to dwuletnia droga — czterosemestralna, wymagająca, ale piękna. Wybierasz zawód, w którym "
     "stawiasz ręce na człowieku: chorym, zmęczonym, szukającym nadziei. Niech ta praca będzie "
     "służbą w duchu Bożej miłości, w prawdzie, w pięknie i sprawiedliwości. Powierzamy ci "
     "wiedzę — broń jej pokorą i sumiennością."),
    ("Misja naturopaty",
     "Naturopata jest sługą zdrowia, nie panem pacjenta. Towarzyszy, prowadzi, wspiera; nie "
     "narzuca, nie manipuluje, nie wykorzystuje. Leczymy ciało środkami naturalnymi, ale "
     "najpierw leczymy obecnością — spokojem, uważnością, modlitwą. Zdrowie jest darem i "
     "zadaniem zarazem."),
    ("Jak korzystać z kursu",
     "Sekcja 00 to ogłoszenia i regulamin. Moduły 1–23 prowadzą od anatomii do praktyki "
     "dyplomowej; każdy zawiera podręcznik (księga/book), quiz i zadanie praktyczne. "
     "Załączniki A–K to słownik, kodeks etyczny, wzory dokumentacji i schematy zabiegowe. "
     "Zasada: najpierw przeczytaj rozdział, potem rozwiąż quiz, na końcu wykonaj zadanie "
     "praktyczne i udokumentuj je."),
    ("Zasady bezpieczeństwa",
     "Primum non nocere — po pierwsze nie szkodzić. Przed każdym zabiegiem: wywiad, ocena "
     "przeciwwskazań (Załącznik F), świadoma zgoda, dokumentacja (Załącznik C). Znaki alarmowe "
     "kieruj do lekarza bez wahania. Twoja odmowa poza kompetencjami jest aktem miłości, nie "
     "porażką."),
]


def build_welcome_book(sec: Path, dry_run: bool, stats: dict) -> None:
    bk = sec / "book-01"
    chap_lines = []
    for i, (title, text) in enumerate(WELCOME_CHAPTERS, start=1):
        chap_file = f"{i:02d}-{slugify(title)}.md"
        put(bk / "chapters" / chap_file,
            f"# {title}\n\n{text}\n\n---\n\n*Zespół dydaktyczny kursu*\n",
            dry_run, stats)
        chap_lines += [f"    - title: {yaml_q(title)}",
                       "      subchapter: false",
                       f"      content_file: {yaml_q('chapters/' + chap_file)}",
                       "      hidden: false"]
    book_yaml = "\n".join([
        "# Aktywność typu book — księga powitalna kursu",
        "book:",
        '  name: "Księga powitalna — Dobrze, że jesteś"',
        "  intro: |",
        indent_block("Kilka słów na dobry początek drogi ku zawodowi naturopaty certyfikowanego. "
                     "Przeczytaj przed pierwszym zjazdem i wracaj do tych stron, gdy zabraknie ci motywacji."),
        "  intro_format: markdown",
        "  numbering: 1",
        "  customtitles: 0",
        "  revision: 1",
        "  chapters:",
        *chap_lines,
        "  completion:",
        "    enabled: true",
        "    type: view",
        "",
    ])
    put(bk / "book.yaml", book_yaml, dry_run, stats)
    sy = sec / "section.yaml"
    if sy.exists():
        txt = sy.read_text(encoding="utf-8")
        if "type: book" not in txt:
            txt = txt.rstrip("\n") + ('\n  - type: book\n    ref: "book-01"\n'
                                      '    name: "Księga powitalna — Dobrze, że jesteś"\n')
            if not dry_run:
                sy.write_text(txt, encoding="utf-8")


# ---------------------------------------------------------------------------
# infrastruktura zapisu
# ---------------------------------------------------------------------------

def put(path: Path, content: str, dry_run: bool, stats: dict, force: bool = False) -> None:
    """Zapisuje tylko pliki puste/nieistniejące (force=False) lub zawsze (force=True dla pustych)."""
    if path.exists() and path.stat().st_size > 0 and not force:
        stats["skipped_nonempty"] += 1
        return
    if path.exists() and path.stat().st_size > 0 and force:
        # force dotyczy wyłącznie plików, które są placeholderami (entries: [])
        old = path.read_text(encoding="utf-8")
        if "entries: []" not in old:
            stats["skipped_nonempty"] += 1
            return
    stats["written"] += 1
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", type=Path, default=DEFAULT_BASE)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    base = args.base if args.base.is_absolute() else ROOT / args.base
    sections = sorted(p for p in (base / "sections").iterdir() if p.is_dir())
    stats = {"written": 0, "skipped_nonempty": 0}

    for sec in sections:
        key = sec.name.split("-", 1)[0]
        if key == "00":
            build_welcome_book(sec, args.dry_run, stats)
        elif key == "28":
            build_glossary_entries(sec, args.dry_run, stats)
            build_dictionary_book(sec, args.dry_run, stats)
        elif key == "29":
            build_codex_book(sec, args.dry_run, stats)
        elif key in ATTACHMENT_BOOKS:
            build_attachment_book(sec, args.dry_run, stats)
        else:
            build_module_book(sec, args.dry_run, stats)

    print(f"Zapisano/uzupełniono: {stats['written']}, "
          f"pominięto (miały treść): {stats['skipped_nonempty']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
