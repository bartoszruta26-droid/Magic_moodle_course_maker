#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enrich_naturopata_books.py — profesjonalne rozbudowy rozdziałów kursu
„Kwalifikacyjny Kurs Zawodowy – Naturopata”.

Co robi
-------
Dla każdego rozdziału książki (`sections/*/book-*/chapters/*.md`), który ma
poniżej PRO threshold bajtów i NIE zawiera jeszcze markerów, dopisuje sekcję
merytoryczną „Rozszerzenie zawodowe” złożoną z:

1. bloku ogólnego (prawda / piękno / sprawiedliwość + granice kompetencji),
2. bloku specyficznego dla typu rozdziału rozpoznawanego po przedrostku:
   - A.x — wykaz lektur: jak czytać ze zrozumieniem, notatka studyjna,
     krytyczna ocena źródeł;
   - B.x — umiejętności praktyczne: fazy nauki techniki (pokaz–naśladowanie–
     ćwiczenie–samokontrola), kryteria opanowania, samoocena;
   - C.x — dokumentacja: RODO, retencja, czytelność, korekty, podpis;
   - F.x/E.x — przeciwwskazania: czerwone flagi, wywiad przesiewowy, tryb
     skierowania do lekarza;
   - G.x — mapy anatomiczne: jak pracować z atlasem, rysunek własny;
   - H.x — schematy masażu: kolejność technik, czas, siła, reakcje
     pourazowe/po-zabiegowe, modyfikacje;
   - I.x — kinezyterapia: dobór ćwiczeń, progresja obciążeń, monitorowanie;
   - J.x — coaching/mentoring: struktura sesji, etyka rozmowy;
   - K.x — zabiegi felczerskie: aseptyka, granice działania, stany nagłe;
   - słownik (hasła) — praca z terminem, etymologia, zdania kontekstowe;
   - spisy treści / rozdziały kodeksu / pozostałe — wskazówki metodyczne.

Zasady:
* NIGDY nie nadpisuje istniejącej treści — tylko dopisuje (append-once);
* idempotentność przez markery („Rozwinięcie treści”, „Rozszerzenie zawodowe”);
* treści są prawdziwe (oparte na uznanej literaturze: Zborowski, Bochenek/
  Traczyk, ICD-10, RODO, ustawa o prawach pacjenta), piękne (język służby
  dobru pacjenta) i sprawiedliwe (jasne granice kompetencji, kierowanie do
  lekarza, ochrona danych).

Użycie
------
    python3 scripts/enrich_naturopata_books.py [--base courses/03-kwalifikacyjny-kurs-zawodowy-naturopaty] [--dry-run] [--min-size 4500]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE = ROOT / "courses" / "03-kwalifikacyjny-kurs-zawodowy-naturopaty"

MARKER_OLD = "## Rozwinięcie treści"
MARKER_NEW = "## Rozszerzenie zawodowe"

GENERIC_BLOCK = """
### Czytać ze zrozumieniem — metoda pracy z rozdziałem

1. **Pierwsze czytanie (orientacja).** Przelicz tytuły i punkty, zaznacz w
   notesie trzy rzeczy, które wydają się najważniejsze, i dwa pytania, które
   rodzi temat. Nie zagłębiaj się jeszcze w szczegóły.
2. **Drugie czytanie (porządkowanie).** Spisz definicje, liczby i kolejności
   (np. sekwencje chwytów) we własnych słowach — to najskuteczniejszy test
   rozumienia. Własne sformułowanie, nawet niedoskonałe, jest dowodem wiedzy;
   mechaniczne powtarzenie tekstu źródłowego — nie.
3. **Trzecie czytanie (zastosowanie).** Odpowiedz na pytanie: „co zmienię w
   planowaniu zabiegu lub rozmowie z pacjentem dzięki tej wiedzy?”. Jeśli
   odpowiedzi brak, rozdział przeczytaj raz jeszcze — wiedza medyczna istnieje
   po to, by służyć człowiekowi.
4. **Powtórka.** Wróć do notatek po 24 godzinach i po tygodniu; utrwalony w
   ten sposób materiał pozostaje na lata.

### Prawda, piękno i sprawiedliwość w nauce tego tematu

- *Prawda* — opieram się wyłącznie na źródłach sprawdzonych (Załącznik A) i
  mówię „nie wiem” tam, gdzie piśmiennictwo milczy. Nie obiecuję efektów,
  których nie sposób udowodnić.
- *Piękno* — piękna jest metoda uporządkowana: wywiad przed dotykiem, łagodność
  przed siłą, cierpliwość przed pośpiechem. Piękno zawodu objawia się w
  drobiazgowej dbałości o drugiego człowieka.
- *Sprawiedliwość* — każdy pacjent, niezależnie od ceny wizyty, poglądów czy
  stanu portfela, ma prawo do tej samej jakości wiedzy i bezpieczeństwa.
  Sprawiedliwością wobec pacjenta jest też uczciwe wyznaczenie granicy moich
  kompetencji i terminowe skierowanie do lekarza, gdy jej przekraczam.
"""


def block_lektury(title: str) -> str:
    return f"""
### Jak korzystać z wykazu lektur («{title}»)

1. **Kolejność.** Zacznij od podręcznika wskazanego jako obowiązkowy, dopiero
   potem sięgaj po pozycje uzupełniające. Przeciążenie źródłami na początku
   zaciemnia, a nie porządkuje wiedzę.
2. **Notatka studyjna** (pół strony na książkę): teza autora, trzy kluczowe
   rozdziały, jedna rzecz, z której zrezygnuję w praktyce, i jedna, którą
   wprowadzę. Taka notatka pozwala po latach odtworzyć, co naprawdę wyniosłem.
3. **Krytyczna ocena źródła.** Sprawdzaj: rok wydania i aktualność wytycznych,
   afiliację autora, wydawnictwo recenzowane, przypisy prowadzące do badań
   pierwotnych. Książka bez przypisów może inspirować, ale nie może być
   podstawą decyzji dotyczących zdrowia.
4. **Spójność z prawem i etyką.** Lektura nie rozszerza uprawnień zawodowych —
   jeśli autor opisuje czynności zastrzeżone dla lekarzy, traktuję je jako
   wiedzę orientacyjną, niezbędną do współpracy i skierowań, nie jako zaproszenie
   do ich wykonywania.
5. **Uczciwość cytowania.** W pracach kursowych i dokumentacji podaję pełny
   opis bibliograficzny. Plagiat narusza sprawiedliwość wobec autora i prawdę
   wobec pacjenta.
"""


def block_umiejetnosci(title: str) -> str:
    return f"""
### Fazy opanowania umiejętności («{title}»)

1. **Pokaz.** Obserwuję wykonanie prawidłowe — najpierw całą sekwencję, potem
   pojedyncze elementy; zwracam uwagę na ułożenie rąk, kierunek ruchu, rytm.
2. **Naśladowanie w zwolnionym tempie.** Ćwiczę na fantomie lub na sobie
   (kolba, ręcznik, własne przedramię), bez presji czasu i siły.
3. **Ćwiczenie właściwe** — minimum kilkadziesiąt powtórzeń na każdej stronie
   ciała partnera ćwicznego; proszę o informację zwrotną: «co czujesz, gdzie
  ucieka napięcie?».
4. **Samokontrola i kryteria zaliczenia:** prawidłowa pozycja wyjściowa terapeuty
   (stopy, grzbiet, barki luźne), stały kontakt skóry, ruch zgodny z kierunkiem
   odpływu chłonki/dosercowym (zależnie od techniki), brak bólu stawów u
   wykonującego, powtarzalność sekwencji.
5. **Utrwalenie:** ćwiczę krótko, ale codziennie (10–15 minut bije dwugodzinną
   sesję raz w tygodniu); co drugi tydzień nagrywam siebie na telefon i
   porównuję z pokazem wzorcowym.

### Higiena pracy własnego ciała

Zespół bólu nadgarstków i karku to najczęstsza przyczyna wypadnięcia z zawodu.
Stosuj zasadę: siła pochodzi z ciężaru ciała i nóg, nie z kciuka ani barku;
kozetka na wysokości bioder; przerwy między zabiegami; rozciąganie przedramion
po serii. Dbając o swoje ręce, sprawiedliwie dbasz o przyszłych pacjentów.
"""


def block_dokumentacja(title: str) -> str:
    return f"""
### Zasady prowadzenia dokumentacji («{title}»)

1. **Podstawa prawna.** Dokumentację medyczną prowadzę zgodnie z ustawą
   o prawach pacjenta i Rzeczniku Praw Pacjenta (art. 23–30) oraz RODO; dane
   zdrowotne to szczególna kategoria danych — przechowuję je szyfrowane,
   z ograniczonym dostępem, a papier w zamkniętej szafie.
2. **Retencja.** Co do zasady 20 lat od końca roku, w którym dokonano wpisu
   (może się skrócić lub wydłużyć na podstawie przepisów szczegółowych);
   nie niszczę dokumentacji wcześniej.
3. **Bieżącość.** Wpisu dokonam zaraz po wizycie/zabiegu — zapis z pamięci po
   dniu jest mniej wiarygodny i mniej sprawiedliwy wobec pacjenta.
4. **Poprawki.** Błędu nie zamazuję ani nie wycieram; przekreślam jednym
   linią tak, by tekst pozostał czytelny, dodaję datę, parafkę i poprawkę
   obok. Wersja elektroniczna: ślad zmian (audit trail).
5. **Język.** Rzeczowo, bez ocen i emocji; opisuję fakty («pacjent zgłasza
   ból 4/10 przy zgięciu»), nie domniemania («pacjent symuluje»).
6. **Świadoma zgoda** na zabieg odnotowuję zawsze — zakresem, ryzykiem i
   możliwym dyskomfortem; cofnięcie zgody szanuję natychmiast i zapisuję.
7. **Anonimizacja do celów dydaktycznych.** Opisy przypadków na forum kursu
   bez imienia, wieku dokładnego, miejsca i cech identyfikujących.
"""


def block_przeciwwskazania(title: str) -> str:
    return f"""
### Stosowanie wykazu w praktyce («{title}»)

1. **Wywiad przesiewowy przed każdym zabiegiem** (2–3 minuty): gorączka lub
   infekcja w ciągu ostatnich 7 dni; choroby nowotworowe i leczenie onkologiczne;
   leki (przeciwzakrzepowe!); ciąża; żylaki i obrzęki jednostronne; choroby
   skóry w okolicy zabiegowej; ostatnie zabiegi operacyjne; ciśnienie tętnicze
   dzisiaj. Wynik zapisuję w karcie zabiegowej (Załącznik C.2).
2. **Przeciwwskazanie bezwzględne** — rezygnuję z zabiegu w całości i
   dokumentuję przyczynę; **względne** — modyfikuję (pozycja, siła, obszar,
   czas) i wpisuję zakres modyfikacji; wątpliwość — kieruję do lekarza.
3. **Czerwone flagi wymagające pilnej konsultacji lekarskiej** (spójnie z
   Załącznikiem E, rozdz. IV): nagły najsilniejszy w życiu ból głowy; ból w
   klatce piersiowej; jednostronny obrzęk łydki (podejrzenie zakrzepicy);
   gorączka niewiadomego pochodzenia; smoliste stolce lub krwiomocz; nowe,
   zmieniające się znamię skórne; objawy neurologiczne ogniskowe; podejrzenie
   przemocy wobec dziecka lub osoby zależnej.
4. **Zasada «lepiej zapytać raz za dużo».** Pacjent nie ponosi winy za to, że
   nie wiedział, iż jego lek rozrzedzający krew wyklucza intensywny masaż —
   moim obowiązkiem jest zapytać. To akt sprawiedliwości i miłości bliźniego.
5. **Po zabiegu** notuję reakcje (zmęczenie, bolesność, senność) i planuję
   kolejną wizytę; niepokojące objawy — kontakt z lekarzem, nie «czekamy».
"""


def block_mapy(title: str) -> str:
    return f"""
### Praca z mapą i atlasem anatomicznym («{title}»)

1. **Trzy poziomy spojrzenia:** całość (kontur regionu), warstwa (skóra →
   powięź → mięsień → naczynia/nerwy → kość), relacja (co leży przy czym i
   dlaczego to ma znaczenie kliniczne).
2. **Rysunek własny.** Przepisanie mapy odręcznym szkicem utrwala lepiej niż
   wielokrotne patrzenie; podpisuj łaciną, zaznaczaj kierunki przebiegu
   (np. węzły chłonne pachowy → dół podobojczykowy).
3. **Palpacja według mapy.** Każdy punkt na mapie potwierdzam na żywym ciele
   partnera ćwicznego: «gdzie to czuję pod palcami? jak to się rusza przy
   oddechu/ruchu?». Anatomia podręczna bez palpacji pozostaje teorią.
4. **Bezpieczeństwo wynikające z anatomii:** znajomość przebiegu tętnicy
   udowej, dołu jarzmowego i rowków nerwu promieniowego chroni przed uciskiem
   struktur wrażliwych; na mapie zaznaczam «strefy ostrożności» kolorem
   czerwonym i nigdy nie masuję «na ślepo».
"""


def block_schematy_masazu(title: str) -> str:
    return f"""
### Realizacja schematu w gabinecie («{title}»)

1. **Sekwencja klasyczna:** głaskanie (rozgrzanie, kontakt) → rozcieranie
   (głębsze warstwy, tkanka łączna) → ugniatanie (mięsień) → oklepywanie
   (mechaniczne pobudzenie) → głaskanie końcowe (wyciszenie). Odchylenie od
   kolejności stosuję świadomie i uzasadniam w karcie zabiegowej.
2. **Parametry zapisuję przed zabiegiem:** czas całkowity, czas na okolicę,
   siła (skala 1–3: powierzchowna / średnia / głęboka), częstotliwość ruchów,
   środek poślizgowy, pozycja pacjenta z podparciami.
3. **Kontrola w trakcie:** co kilka minut pytam o odczucia; objawy alarmowe
   (ból ostry, zawrót głowy, drętwienie) = przerwanie techniki, ocena, w razie
   potrzeby — przerwanie zabiegu i postępowanie wg procedury.
4. **Reakcje po zabiegu:** typowe — rozluźnienie, ciepło, senność; nietypowe —
   wzrost bólu po 24 h, obrzęk, siniak większy niż oczekiwany; notuję i
   dostosowuję następną serię (mniejsza siła, krótszy czas, inna okolica).
5. **Modyfikacje:** ciąża (pozycja boczna, bez intensywnego odcinka lędźwiowego),
   podeszły wiek (delikatniejsza skóra, mniej oklepywania), osteoporoza (zakres
   bez ucisku punkowego), cukrzyca (kontrola stopy, bez głębokiego masażu miejsc
   o upośledzonym czuciu).
"""


def block_kinezyterapia(title: str) -> str:
    return f"""
### Prowadzenie programu («{title}»)

1. **Ocena wyjściowa:** zakres ruchów (goniometr lub kątomierz aplikacyjny),
   siła (skala Lovetta 0–5 lub dynamometria), ból (NRS 0–10), funkcja
   (np. test wstania z krzesła, pokonanie 6 minut marszu) — zapisuję liczby,
   nie wrażenia.
2. **Dobór ćwiczeń:** od stabilizacji i toru oddechowego do wzmacniania i
   funkcji; każde ćwiczenie ma cel, dawkę (serie × powtórzenia × obciążenie),
   pozycję wyjściową i kryterium zaprzestania.
3. **Progresja:** najpierw zwiększam liczbę powtórzeń, potem obciążenie, na
   końcu tempo i trudność zadania; zasada «nie więcej niż 10% na tydzień»
   chroni ścięgna i więzadła.
4. **Monitorowanie:** tętno i odczuwany wysiłek (skala Borga 6–20) przed/po;
   u kardiopacjentów tylko w zakresie ustalonym z lekarzem prowadzącym.
5. **Zasada bezpieczeństwa:** ból stawowy (stawowy) > 3/10 utrzymujący się
   dłużej niż 24 h po ćwiczeniach = regresja obciążenia i konsultacja.
   Ćwiczenia oddechowe i relaksacyjne wykonuję zawsze na początku jednostki.
"""


def block_coaching(title: str) -> str:
    return f"""
### Etos rozmowy wspierającej («{title}»)

1. **Struktura sesji:** kontakt i cel (5 min) → mapa sytuacji (10 min) →
   opcje i konsekwencje (15 min) → zobowiązanie SMART i wsparcie (10 min) →
   podsumowanie (5 min). Notuję ustalenia razem z pacjentem, nie «o nim».
2. **Słuchanie aktywne:** parafrazy, pytania otwarte, milczenie tolerowane.
   Nie doradzam przed zbadaniem gotowości do zmiany (model transteoretyczny
   Prochaski: prekontemplacja → utrzymanie).
3. **Granice:** coaching zdrowotny nie jest psychoterapią. Objawy depresji,
   lęku napadowego, zaburzeń odżywiania czy myśli samobójczych — natychmiast
   kieruję do lekarza/psychoterapeuty; bezpieczeństwo pacjenta jest przed
   jakąkolwiek metodą.
4. **Superwizja:** co najmniej raz na kwartał przedstawiam przypadek (anonimowo)
   mentorowi; pokora wobec własnych ograniczeń jest warunkiem uczciwości
   zawodu.
"""


def block_felczerstwo(title: str) -> str:
    return f"""
### Warunki wykonania zabiegu («{title}»)

1. **Asepsja i antysepsa:** mycie rąk, rękawiczki jednorazowe, jałowy zestaw
   zamknięty, dezynfekcja skóry (od miejsca wkłucia na zewnątrz), odpady do
   pojemników na ostrza i odpadów medycznych.
2. **Tożsamość i przygotowanie pacjenta:** sprawdzenie danych, alergii, leków
   (zwłaszcza przeciwzakrzepowych), stanowiska, oświetlenia; zgoda pisemna
   (Załącznik C.8).
3. **Opis przebiegu:** czas, użyte środki i dawki, liczba szwów, wygląd rany,
   ewentualne powikłania, zalecenia kontrolne — wszystko w karcie zabiegów
   (Załącznik C.12).
4. **Kontrole:** rana — ocena po 24–48 h i wg schematu zdjęć szwów; szczepienia
   — obserwacja 15–30 min po podaniu, dokumentacja serii i dawki (C.13).
5. **Stan nagły:** utrata przytomności, duszność, krwawienie tętnicze, wstrząs
   — natychmiastowe wezwanie pomocy (112/999) i postępowanie wg algorytmu BLS;
   każda zwłoka jest zagrożeniem życia, żadna «porada z internetu» nie zastąpi
   zespołu ratownictwa.
"""


def block_slownik(title: str) -> str:
    return f"""
### Jak uczyć się hasła («{title}»)

1. **Etymologia:** rozłóż termin na cząstki (np. *hepat-ō-megalia*: gr.
   *hēpar* wątroba + *megas* wielki) — nazwa niesie definicję.
2. **Zdanie kontekstowe:** wpisz termin do własnego zdania klinicznego
   («W marskości wątroby obserwuje się hepatomegalię w fazie...»); termin bez zdania
   ginie w miesiąc.
3. **Łacina/grecka w dokumentacji:** odmiana i rodzaj gramatyczny mają znaczenie
   przy redagowaniu kart; błędna forma bywa myląca dla kolejnego czytelnika.
4. **Mapowanie na ICD-10:** przyporządkuj hasło do grupy jednostek chorobowych —
   ułatwia to komunikację z lekarzem przy skierowaniu i czytanie opisów badań.
"""


def block_spis_tresci(title: str) -> str:
    return f"""
### Jak korzystać ze spisu treści

Traktuj spis jako «mapę drogową» załącznika: przed lekturą wybranego tematu
przejrzyj cały spis i zaznacz trzy pozycje, których potrzebujesz dziś (przed
zjazdem, zabiegiem, pracą). Po lekturze wróć do spisu i oceń w skali 1–3,
czy umiesz streścić każdą pozycję jednym zdaniem — brak pewności oznacza
temat do powtórki. Taki przegląd zajmuje 5 minut, a porządkuje wiedzę na
cały semestr.
"""


def detect_block(rel: str, title: str) -> tuple[str, str]:
    """Zwraca (nazwa_bloku, treść) na podstawie ścieżki i tytułu."""
    t = title.lower()
    fname = Path(rel).name.lower()
    # prefiks kodu pozycji w nazwie pliku: a-, b-, c-, f-, g-, h-, i-, j-, e-, k-
    code = ""
    m = re.match(r"\d+-([a-k])-", fname)
    if m:
        code = m.group(1)
    sec = rel.split("/")[0]
    if "slownik" in sec or fname.startswith("hasla"):
        return "slownik", block_slownik(title)
    if code == "a":
        return "lektury", block_lektury(title)
    if code == "b":
        return "umiejetnosci", block_umiejetnosci(title)
    if code == "c":
        return "dokumentacja", block_dokumentacja(title)
    if code in ("f", "e"):
        return "przeciwwskazania", block_przeciwwskazania(title)
    if code == "g":
        return "mapy", block_mapy(title)
    if code == "h":
        return "schematy-masazu", block_schematy_masazu(title)
    if code == "i":
        return "kinezyterapia", block_kinezyterapia(title)
    if code == "j":
        return "coaching", block_coaching(title)
    if code == "k":
        return "felczerstwo", block_felczerstwo(title)
    if "zawarto" in t or "spis" in t:
        return "spis-tresci", block_spis_tresci(title)
    if "kodeks" in sec or "rozdzial" in fname or "preambula" in fname:
        return "etyka", GENERIC_BLOCK
    return "ogolny", GENERIC_BLOCK


def main() -> int:
    ap = argparse.ArgumentParser(description="Rozbudowa rozdziałów kursu Naturopata")
    ap.add_argument("--base", type=Path, default=DEFAULT_BASE)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-size", type=int, default=4500,
                    help="rozdziały poniżej tej wielkości (bajtów) otrzymują rozwinięcie")
    args = ap.parse_args()
    sections = args.base / "sections"
    if not sections.is_dir():
        print(f"BLAD: brak katalogu {sections}", file=sys.stderr)
        return 2

    stats = {"written": 0, "skipped": 0}
    per_type: dict[str, int] = {}
    for ch in sorted(sections.glob("*/book-*/chapters/*.md")):
        size = ch.stat().st_size
        text = ch.read_text(encoding="utf-8")
        if MARKER_NEW in text or MARKER_OLD in text or size >= args.min_size:
            stats["skipped"] += 1
            continue
        rel = str(ch.relative_to(sections))
        m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        title = (m.group(1).strip() if m else ch.stem)
        # tytułem właściwym bywa linia pogrubiona po "# Kod"
        mb = re.search(r"\*\*(.+?)\*\*", text)
        if m and len(m.group(1)) < 12 and mb:
            title = mb.group(1).strip()
        name, block = detect_block(rel, title)
        new = text.rstrip() + "\n\n---\n\n" + MARKER_NEW + "\n" + block.strip() + "\n"
        stats["written"] += 1
        per_type[name] = per_type.get(name, 0) + 1
        if not args.dry_run:
            ch.write_text(new, encoding="utf-8")
        print(f"  {'[DRY-RUN] ' if args.dry_run else ''}ROZBUDOWA [{name}]: {rel} ({size} B -> ~{len(new.encode())} B)")

    print("\nPODSUMOWANIE" + (" [DRY-RUN]" if args.dry_run else "") + ":")
    print(f"  rozdziały rozwinięte: {stats['written']}")
    print(f"  pominięte (pełne/marker): {stats['skipped']}")
    for k, v in sorted(per_type.items()):
        print(f"    {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
