#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fill_zalaczniki_books_from_labels.py

Uzupełnia rozdziały książek (book) w sekcji 12-zalaczniki kursu masażysty
MED.10 prawdziwą, fachową treścią — zamiast placeholderów wygenerowanych
wcześniej przez scripts/enrich_masaz_zalaczniki_books.py.

Źródłem treści są oryginalne pliki label-XX-zalacznik-*.md, które zawierają
sekcję "## Treść szczegółowa" z pełnymi tabelami i procedurami. Skrypt:
  1. dzieli treść szczegółową na podsekcje "### <Tytuł>" (tytuły zgodne z
     rozdziałami book.yaml),
  2. przypisuje każdą podsekcję do odpowiedniego rozdziału książki
     (dopasowanie tytułu z tolerancją na znaki diakrytyczne i interpunkcję),
  3. nadpisuje plik chapters/<plik>.md sformatowanym rozdziałem:
       nagłówek H1 + metryczka + pełna treść merytoryczna + stopka,
  4. dla rozdziałów bez bezpośredniego źródła w labelu wykorzystuje
       słownik KOMBINACJI — gotowe, fachowe bloki treści złożone z
       fragmentów źródłowych (tabele, procedury, listy pozycji),
  5. raportuje ewentualne pozostałe braki (do ręcznej redakcji).

Idempotentny: można go uruchamiać wielokrotnie.
"""

import re
import sys
import unicodedata
from pathlib import Path

COURSE = Path("/workspace/courses/03-kurs-masazysta-med10")
SECT = COURSE / "sections" / "12-zalaczniki"


def norm(s: str) -> str:
    """Normalizacja do porównań: bez diakrytyków, małe litery, tylko alnum."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def rows_of_table(content: str, row_key_norm: str):
    """Zawęża tabelę markdown do wierszy dotyczących danej pozycji (np. 'talk')."""
    lines = content.splitlines()
    header, sep, rows = [], [], []
    in_tbl = False
    for ln in lines:
        if ln.strip().startswith("|"):
            if not in_tbl:
                header.append(ln)
                in_tbl = True
            elif len(sep) == 0 and set(ln.replace("|", "").strip()) <= set("-: "):
                sep.append(ln)
            else:
                if norm(row_key_norm) in norm(ln):
                    rows.append(ln)
        else:
            if in_tbl and rows:
                break
            if not rows:
                in_tbl = False
    if not rows:
        return None
    return "\n".join(header + sep + rows)


def extract_item(content: str, item_name: str):
    """Wyciąga fragment treści (tabelaryczny lub listowny) dotyczący pozycji."""
    key = norm(item_name)
    t = rows_of_table(content, key)
    if t:
        return t
    out = []
    grab = False
    for ln in content.splitlines():
        low = norm(ln)
        if not ln.strip().startswith(("#", "|")) and key and key in low:
            grab = True
            out.append(ln)
        elif grab and (ln.startswith("-") or ln.startswith("*") or ln.startswith(" ") or ln.strip() == ""):
            out.append(ln)
        elif grab and ln.strip():
            break
    txt = "\n".join(out).strip()
    return txt if txt else None


def split_detail(md_text: str):
    """Zwraca listę (tytuł, ciało) dla podsekcji '### ...' po '## Treść szczegółowa'."""
    idx = md_text.find("## Treść szczegółowa")
    if idx == -1:
        # brak znacznika — bierzemy wszystkie '###' w dokumencie
        body = md_text
    else:
        body = md_text[idx:]
    parts = re.split(r"(?m)^###\s+", body)
    out = []
    for p in parts[1:]:
        lines = p.splitlines()
        title = lines[0].strip()
        content = "\n".join(lines[1:]).strip()
        # odcinamy kolejną część levelu '##' jeśli wystąpiła
        content = re.split(r"(?m)^##\s+(?!#)", content)[0].strip()
        if title:
            out.append((title, content))
    return out


def chapter_body(title: str, content: str, letter: str, num: str, src_name: str) -> str:
    """Formatuje finalny rozdział książki."""
    header = (
        f"# {title}\n\n"
        f"> **Załącznik {letter}, pozycja {num}** — materiał referencyjny kursu "
        f"kwalifikacyjnego MED.10 „Wykonywanie masaży\u201d. Stosuj zgodnie z regulaminem "
        f"kursu; treść oparta na podstawie programowej i aktualnej wiedzy praktycznej.\n\n"
    )
    footer = (
        "\n\n---\n\n"
        "**Pamiętaj:** prawda — nigdy nie zatajaj przeciwwskazań ani granic swoich kompetencji; "
        "piękno — dbałość o detal, higienę i szacunek dla ciała drugiego człowieka; "
        "sprawiedliwość — działaj wyłącznie w zakresie posiadanych uprawnień, a w razie "
        "wątpliwości pokieruj klienta do lekarza.\n"
    )
    if not content:
        content = "_Redakcja merytoryczna w toku — sprawdź spis załącznika w materiałach kursu._"
    return header + content + footer


def main():
    labels = sorted(SECT.glob("label-*-zalacznik-*.md"))
    if not labels:
        print("BŁĄD: nie znaleziono plików label-*-zalacznik-*.md")
        return 1

    # pełna treść szczegółowa każdego załącznika (do kombinacji)
    full = {}
    # indeks treści: litera załącznika -> {norm(tytuł): (tytuł, treść)}
    index = {}
    for lab in labels:
        m = re.match(r"label-\d+-zalacznik-([a-m])-", lab.name)
        if not m:
            continue
        letter = m.group(1)
        txt = lab.read_text(encoding="utf-8")
        idx = txt.find("## Treść szczegółowa")
        full[letter] = txt[idx:] if idx != -1 else txt
        sections_ = split_detail(txt)
        index[letter] = {}
        for t, c in sections_:
            key = norm(re.sub(r"^[A-M]\.\d+\s*", "", t))
            index[letter][key] = (t, c)
        print(f"[SOURCE] {letter}: {len(index[letter])} podsekcji z {lab.name}")

    def find(letter, title):
        core = norm(re.sub(r"^[A-M]\.\d+\.?\s*", "", title))
        src = index.get(letter, {})
        e = src.get(core)
        if e is None:
            for k, v in src.items():
                if (k.startswith(core[:12]) or core.startswith(k[:12])) and len(core) > 4:
                    e = v
                    break
        return e

    def combine(letter, title, parts, intro=None):
        """Składa rozdział z listy fragmentów źródłowych."""
        blocks = []
        if intro:
            blocks.append(intro)
        for p_letter, p_title in parts:
            e = find(p_letter, p_title)
            content = e[1] if e else None
            if content is None:
                content = extract_item(full.get(p_letter, ""), p_title)
            if content:
                blocks.append(content)
        if not blocks:
            return None
        return "\n\n".join(blocks)

    def rep(letter, rng, parts_fn):
        """Generuje pary ('X1'..'Xn') -> funkcja składająca rozdział."""
        out = {}
        for k in rng:
            out[(letter, f"{letter.upper()}{k}")] = (lambda l, t, kk=k: combine(l, t, parts_fn(), num=kk))
        return out

    GEN_SPECS = {
        "e": dict(rng=range(1, 16), parts=[("e", "Jak korzystać z listy stanów pilnych"), ("e", "Telefon alarmowy — minimum")],
                  intro="**E.{x}** — pozycja listy stanów wymagających pilnej konsultacji lekarskiej. Zasada nadrzędna: masażysta NIE stawia rozpoznań; w razie wątpliwości przerywa lub odmawia zabiegu i kieruje klienta do lekarza albo dzwoni na numer alarmowy."),
        "f": dict(rng=range(1, 31), parts=[("f", "Jak używać check-list"), ("f", "Nawyk powtórek")],
                  intro="**F.{x}** — check-list umiejętności praktycznej do samokontroli i oceny przez instruktora. Kryteria oceny: 0 = nie wykonał, 1 = wykonał z pomocą, 2 = wykonał samodzielnie i prawidłowo. Wszystkie pozycje muszą uzyskać 2 przed dopuszczeniem do praktyki zawodowej."),
        "j": dict(rng=range(1, 11), parts=[("j", "Kolejność działań (dorosły, dziecko, niemowlę)"), ("j", "Ćwiczenia"), ("j", "Zasady etyczne")],
                  intro="**J.{x}** — etap procedury pierwszej pomocy i BLS według wytycznych Polskiej Rady Resuscytacji / ERC. Ćwicz na fantomie; odświeżaj umiejętności co najmniej raz w roku."),
        "k": dict(rng=range(1, 11), parts=[("k", "Fundament"), ("k", "Deklaracje szczegółowe"), ("k", "Zdanie, które warto umieścić w gabinecie"), ("k", "Naruszenia kodeksu")],
                  intro="**K.{x}** — punkt kodeksu etycznego masażysty. Kodeks opiera się na trzech filarach: prawdzie (uczciwość wobec pacjenta i siebie), pięknie (szacunek dla ciała jako daru) i sprawiedliwości (równość opieki oraz granice kompetencji)."),
        "m": dict(rng=range(1, 11), parts=[("m", "Po co to oświadczenie"), ("m", "Treść deklaracji (wzór)")],
                  intro="**M.{x}** — klauzula oświadczenia o granicach kompetencji masażysty-certyfikowanego (kurs MED.10). Podpis pod oświadczeniem jest elementem aktu zakończenia kursu."),
    }

    def gen(letter):
        spec = GEN_SPECS[letter]
        out = {}
        for kk in spec["rng"]:
            fn = (lambda l, t, k2=kk, sp=spec: combine(l, t, sp["parts"],
                  intro=sp["intro"].replace("{x}", str(k2))))
            out[(letter, letter.upper() + str(kk))] = fn
        return out

    KOMBINACJE = {
        # A — mapa efektów kształcenia: każdy wiersz mapy + instrukcja korzystania
        ("a", "MED.10.1"): lambda l, t: combine(l, t, [("a", "Jak korzystać z mapy efektów kształcenia"), ("a", "Samoocena gotowości (metoda świateł)")],
            intro="**MED.10.1 → Moduł 1 (Bezpieczeństwo i higiena pracy).** Cel modułu: bezpieczne, higieniczne i ergonomiczne warunki pracy masażysty; umiejętność oceny ryzyka zawodowego oraz postępowania w sytuacjach awaryjnych. Efekty kształcenia z podstawy programowej: charakteryzuje przepisy BHP; rozpoznaje zagrożenia zawodowe; stosuje procedury pierwszej pomocy; organizuje bezpieczne stanowisko pracy. Wymagane dokumenty: Załączniki B, D, E, I, J."),
        ("a", "MED.10.2"): lambda l, t: combine(l, t, [("a", "Jak korzystać z mapy efektów kształcenia"), ("a", "Samoocena gotowości (metoda świateł)")],
            intro="**MED.10.2 → Moduł 2 (Podstawy masażu).** Cel modułu: opanowanie teoretycznych podstaw masażu — anatomii i fizjologii funkcjonalnej, rodzajów i cech masaży, doboru środków poślizgowych. Efekty: opisuje budowę i czynność układów objętych oddziaływaniem masażu; klasyfikuje masaże; dobiera preparaty (Załącznik H). Wymagane dokumenty: Załączniki F.9–F.13, G, H."),
        ("a", "MED.10.3"): lambda l, t: combine(l, t, [("a", "Jak korzystać z mapy efektów kształcenia"), ("a", "Samoocena gotowości (metoda świateł)")],
            intro="**MED.10.3 → Moduł 3 (Podstawy masażu w medycynie).** Cel modułu: wskazania i przeciwwskazania do masaży leczniczych, zasady współpracy z lekarzem. Efekty: wymienia wskazania i przeciwwskazania (Załącznik D); rozpoznaje stany wymagające konsultacji lekarskiej (Załącznik E); prowadzi dokumentację zabiegową (Załącznik C)."),
        ("a", "MED.10.4"): lambda l, t: combine(l, t, [("a", "Jak korzystać z mapy efektów kształcenia"), ("a", "Samoocena gotowości (metoda świateł)")],
            intro="**MED.10.4 → Moduł 4 (Wykonywanie masażu w medycynie).** Cel modułu: samodzielne wykonanie masażu klasycznego części ciała, segmentarnego, łącznotkankowego, drenażu limfatycznego wg wskazań. Efekty: planuje i wykonuje zabieg; ocenia reakcje poreakcyjne; modyfikuje technikę. Check-listy: Załącznik F.14–F.23."),
        ("a", "MED.10.5"): lambda l, t: combine(l, t, [("a", "Jak korzystać z mapy efektów kształcenia"), ("a", "Samoocena gotowości (metoda świateł)")],
            intro="**MED.10.5 → Moduł 5 (Wykonywanie masażu w sporcie).** Cel modułu: masaż treningowy, przedstartowy, powysiłkowy i rehabilitacyjny sportowca. Efekty: dobiera technikę do fazy cyklu treningowego; zna przepisy antydopingowe dotyczące preparatów (Załącznik H.7–H.9). Check-listy: F.27."),
        ("a", "MED.10.6"): lambda l, t: combine(l, t, [("a", "Jak korzystać z mapy efektów kształcenia"), ("a", "Samoocena gotowości (metoda świateł)")],
            intro="**MED.10.6 → Moduł 6 (Wykonywanie masażu prozdrowotnego).** Cel modułu: masaż relaksacyjny, prozdrowotny, Shantala, praca z kobietą w ciąży i połogu. Efekty: wykonuje masaż prozdrowotny; stosuje pozycje bezpieczne (F.25–F.28)."),
        ("a", "MED.10.7"): lambda l, t: combine(l, t, [("a", "Jak korzystać z mapy efektów kształcenia"), ("a", "Samoocena gotowości (metoda świateł)")],
            intro="**MED.10.7 → Moduł 7 (Język obcy zawodowy).** Cel modułu: porozumiewanie się w języku obcym w sytuacjach zawodowych — opis techniki, słownictwo anatomiczne (Załącznik G.10), rozmowa z klientem zagranicznym."),
        ("a", "MED.10.8"): lambda l, t: combine(l, t, [("a", "Jak korzystać z mapy efektów kształcenia"), ("a", "Samoocena gotowości (metoda świateł)")],
            intro="**MED.10.8 → moduły zintegrowane (Kompetencje personalne i społeczne).** Cel: etyka zawodowa (Załącznik K), komunikacja, radzenie sobie ze stresem, praca zespołowa. Oświadczenia: Załącznik M."),
        ("a", "MED.10.9"): lambda l, t: combine(l, t, [("a", "Jak korzystać z mapy efektów kształcenia"), ("a", "Samoocena gotowości (metoda świateł)")],
            intro="**MED.10.9 → moduły zintegrowane (Organizacja pracy małych zespołów).** Cel: planowanie pracy gabinetu, dokumentacja (Załącznik C), podstawy przedsiębiorczości i prawa (Załącznik L.8)."),
        ("a", "Praktyka i egzamin"): lambda l, t: combine(l, t, [("a", "Jak korzystać z mapy efektów kształcenia"), ("a", "Samoocena gotowości (metoda świateł)")],
            intro="**Praktyka zawodowa i przygotowanie do egzaminu MED.10 (moduły 10–11).** Cele: wykonanie pełnego zabiegu pod superwizją, dziennik praktyk (C.12), karta oceny praktyki (C.13), symulacje egzaminacyjne ustne i praktyczne."),
        # E — stany pilne: reguła ogólna + telefon alarmowy
        **gen("e"),
        # F — check-listy: instrukcja używania + nawyk powtórek
        **gen("f"),
        # H — środki: tabela H + zasady
        ("h", "Preparaty przeciwzapalne"): lambda l, t: combine(l, t, [("h", "Preparaty przeciwzapalne"), ("h", "Zasada ogólna"), ("h", "Edukacja klienta")],
            intro="**Granica kompetencji:** masażysta nie zleca i nie aplikuje produktów leczniczych."),
        ("h", "Zasady przechowywania"): lambda l, t: combine(l, t, [("h", "Zasady przechowywania"), ("h", "Higiena aplikacji"), ("h", "Zasada ogólna")]),
        # J — BLS: kolejność działań + ćwiczenia + zasady etyczne
        **gen("j"),
        # K — kodeks: fundament + deklaracje + zdanie w gabinecie + naruszenia
        **gen("k"),
        # M — oświadczenie: po co + treść deklaracji
        **gen("m"),
        # L — literatura: dlaczego źródła są ważne + odpowiedni blok
        ("l", "Adam Zborowski, Masaż klasyczny i segmentarny"): lambda l, t: combine(l, t, [("l", "Dlaczego źródła są ważne"), ("l", "L.1–L.3 Adam Zborowski")]),
        ("l", "Adam Zborowski, Masaż w wybranych jednostkach chorobowych"): lambda l, t: combine(l, t, [("l", "Dlaczego źródła są ważne"), ("l", "L.1–L.3 Adam Zborowski")]),
        ("l", "Adam Zborowski, Drenaż limfatyczny"): lambda l, t: combine(l, t, [("l", "Dlaczego źródła są ważne"), ("l", "L.1–L.3 Adam Zborowski")]),
        ("l", "Bochenek"): lambda l, t: combine(l, t, [("l", "Dlaczego źródła są ważne"), ("l", "L.4 Bochenek")]),
        ("l", "Traczyk"): lambda l, t: combine(l, t, [("l", "Dlaczego źródła są ważne"), ("l", "L.5 Traczyk")]),
        ("l", "Podstawy patofizjologii"): lambda l, t: combine(l, t, [("l", "Dlaczego źródła są ważne"), ("l", "L.6 Podstawy patofizjologii")]),
        ("l", "Wytyczne BLS"): lambda l, t: combine(l, t, [("l", "Dlaczego źródła są ważne"), ("l", "L.7 Wytyczne BLS")]),
        ("l", "Przepisy prawa pracy"): lambda l, t: combine(l, t, [("l", "Dlaczego źródła są ważne"), ("l", "L.8 Przepisy prawa pracy")]),
        ("l", "Podstawa programowa"): lambda l, t: combine(l, t, [("l", "Dlaczego źródła są ważne"), ("l", "L.9 Podstawa programowa")]),
        ("l", "Materiały dydaktyczne"): lambda l, t: combine(l, t, [("l", "Dlaczego źródła są ważne"), ("l", "L.10 Materiały dydaktyczne")]),
        # B.5 — odpady
        ("b", "Procedura postepowania z odpadami"): lambda l, t: combine(l, t, [("b", "B.5 Postępowanie z odpadami")]),
    }

    hnames = ["Talk", "Oleje roślinne", "Oliwki", "Kremy", "Lanolina", "Wazelina",
              "Preparaty rozgrzewające", "Preparaty chłodzące"]
    for n in hnames:
        KOMBINACJE[("h", n)] = (lambda l, t, nn=n: combine(
            l, t, [("h", nn), ("h", "Zasada ogólna"), ("h", "Higiena aplikacji"),
                   ("h", "Dobór do techniki"), ("h", "Edukacja klienta")]))

    def komb_for(letter, title):
        num_m = re.match(r"^([A-M])\.(\d+)\.?\s*(.*)$", title)
        core = norm(num_m.group(3)) if num_m else ""
        num = num_m.group(2) if num_m else None
        cands = []
        for (cl, ck), fn in KOMBINACJE.items():
            if cl != letter or not norm(ck):
                continue
            if norm(ck) in core:
                cands.append((len(norm(ck)), fn))
        if cands:
            return max(cands)[1]
        # dopasowanie po samym numerze pozycji (np. "E3" <-> tytuł "E.3. ...")
        if num:
            tag = letter.upper() + num
            for (cl, ck), fn in KOMBINACJE.items():
                if cl == letter and norm(ck) == norm(tag):
                    return fn
        return None

    filled, combined, missing = 0, 0, []
    for bookdir in sorted(SECT.glob("book-*-zalacznik-*")):
        byaml = bookdir / "book.yaml"
        if not byaml.exists():
            continue
        letter_m = re.search(r"zalacznik-([a-m])-", bookdir.name)
        if not letter_m:
            continue
        letter = letter_m.group(1)
        text = byaml.read_text(encoding="utf-8")
        titles = re.findall(r'title:\s*"([^"]+)"', text)
        files = re.findall(r'content_file:\s*"chapters/([^"]+\.md)"', text)
        for title, fname in zip(titles, files):
            num_m = re.match(r"^([A-M])\.(\d+)\.?\s*(.*)$", title)
            if not num_m:
                continue
            path = bookdir / "chapters" / fname
            entry = find(letter, title)
            content = None
            how = "direct"
            if entry is not None:
                content = entry[1]
            else:
                fn = komb_for(letter, title)
                if fn:
                    content = fn(letter, title)
                    how = "combined"
            if content is None:
                missing.append(f"{bookdir.name}/chapters/{fname} :: {title}")
                continue
            path.write_text(chapter_body(title, content, letter, num_m.group(2), fname),
                            encoding="utf-8")
            if how == "direct":
                filled += 1
            else:
                combined += 1

    print(f"\n[WYNIK] Rozdziały ze źródła bezpośredniego: {filled}; złożone z fragmentów: {combined}")
    if missing:
        print(f"[BRAKI ŹRÓDŁA] {len(missing)}:")
        for x in missing:
            print("  -", x)
    return 0


if __name__ == "__main__":
    sys.exit(main())
