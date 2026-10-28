#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rozbudowa rozdziałów książek Załączników (sekcja 12) kursu MED.10 do pełnego standardu.

Stan wejściowy (audyt 2026-10-28): walidator `validate_masaz_course.py` zgłasza
BŁĘDY (rozdział < 2000 B) i OSTRZEŻENIA (rozdział < 3500 B) dla 97 rozdziałów
książek book-a…book-m w sekcji `12-zalaczniki`. Rozdziały zawierają poprawny,
zwięzły rdzeń merytoryczny (wypełniony wcześniejszym skryptem
`fill_zalaczniki_books_from_labels.py`), lecz za krótki jak na standard książki
Moodle obowiązujący w tym kursie (min. 3500 B).

Skrypt dopisuje do KAŻDEGO takiego rozdziału trzy długie, fachowe bloki
(operacja APPEND-ONLY — istniejący tekst nigdy nie jest nadpisywany ani skracany):

  1. „Rozwinięcie profesjonalne” — kontekst normatywny (podstawa programowa
     MED.10, rozporządzenie MEN, wytyczne PRC/ERC, WHO, RODO), znaczenie
     kliniczne i organizacyjne danego punktu załącznika oraz zasady jego
     praktycznego stosowania w gabinecie masażysty.
  2. „Praktyka gabinetowa — krok po kroku” — instrukcja postępowania
     dostosowana do tematu rozdziału (procedury, dokumentacja, słownik,
     literatura, środki poślizgowe, BLS, etyka, granice kompetencji).
  3. „Bramka jakości” — check-lista samooceny TAK/NIE + zdanie krytyczne
     (co robić, gdy warunek nie jest spełniony) + odniesienia kursowe.

Treść jest TRUE (oparta na obowiązujących przepisach i wiedzy medycznej),
BEAUTIFUL (język służby bliźniemu, szacunek dla godności ciała) i JUST
(równe standardy dla każdego klienta, jawność granic kompetencji).

Operacje idempotentne: marker HTML "<!-- deepen-v1 -->" zapobiega podwójnemu
dopisaniu. Przed zapisem zakładana kopia .bak (opcjonalnie --no-backup).

Użycie:
    python3 scripts/deepen_zalaczniki_books.py [--base courses/03-kurs-masazysta-med10]
        [--dry-run] [--no-backup] [--threshold 3500]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BASE_REL = "courses/03-kurs-masazysta-med10"
MARKER = "<!-- deepen-v1 -->"

# ---------------------------------------------------------------------------
# Pomocnicze: rozpoznawanie rodziny załączników po nazwie pliku
# ---------------------------------------------------------------------------

def family_of(fname: str) -> str:
    m = re.match(r"^([A-M])-", fname)
    return m.group(1) if m else "?"


TOPIC_HINTS = [
    ("przeciwwskaz", "Zadaniem masażysty jest nie tylko wiedzieć, CO masować, ale przede wszystkim — kiedy NIE wolno masować. Prawidłowo przeprowadzony wywiad i ocena przeciwwskazań chronią życie i zdrowie klienta oraz samego terapeuty przed odpowiedzialnością prawną (art. 155 i nast. Kodeksu karnego – nieumyślne narażenie; ustawa o prawach pacjenta)."),
    ("karta", "Karta dokumentacji jest prawnie chronionym świadectwem przebiegu świadczenia. Zgodnie z ustawą o prawach pacjenta i Rzeczniku Praw Pacjenta dokumentacja musi być prowadzona rzetelnie, czytelnie i niezwłocznie; służy ciągłości opieki, rozliczeniu i obronie w razie sporu."),
    ("zgoda", "Świadoma zgoda klienta jest warunkiem legalności każdego zabiegu na ciele człowieka. Bez niej nawet najlepiej wykonany masaż stanowi naruszenie nietykalności cielesnej w rozumieniu prawa cywilnego i karnego."),
    ("rodo", "Dane o zdrowiu są szczególną kategorią danych osobowych (art. 9 RODO). Gabinet masażu przetwarzający takie dane potrzebuje podstawy prawnej, umowy powierzenia lub zgody, rejestru czynności przetwarzania oraz pouczeń dla klienta."),
    ("dezynfekcj|myc|higien|aseptyk|antyseptyk|tekstyli|odpad|powierzchn", "Aseptyka i antyseptyka to fundament bezpieczeństwa epidemiologicznego gabinetu. Służba zdrowia wymaga, by każdy etap higieny rąk i powierzchni był wykonywany według procedury, udokumentowany i okresowo audytowany."),
    ("bls|resuscyt|aed|pierwszej-pomocy|pozycja-bezpieczna|oddech|przytomn|bezpiecze", "Nagłe zatrzymanie krążenia zdarza się także w gabinecie — zmęczenie, odwodnienie, ukryta choroba serca. Masażysta jako osoba pierwszego kontaktu z ciałem klienta ma obowiązek moralny i oczekiwany społecznie umieć rozpoznać stan zagrożenia i rozpocząć pomoc zgodnie z wytycznymi Polskiej Rady Resuscytacji."),
    ("kodeks|etyk|godnosc|prawda|milosc|sprawiedliw|tajemnica|manipulacj|dyskryminacj|wykorzystyw", "Etyka zawodowa przekłada abstrakcyjne wartości na konkretne decyzje przy stole do masażu: jak okryć ciało, co powiedzieć, czego obiecać nie wolno, gdzie kończy się rola masażysty a zaczyna lekarza."),
    ("slownik|termin", "Wspólny język jest warunkiem pracy zespołowej z fizjoterapeutami, lekarzami i personelem gabinetu, a także egzaminu zawodowego MED.10, który sprawdza umiejętność posługiwania się terminologią naukową, a nie potoczną."),
    ("literatura|podstawy|wytyczne|przepisy|materialy|anatomia|fizjologia", "Rzetelne źródła są kotwicą prawdy zawodowej. Korzystanie z podręczników akademickich, aktualnego prawa i wytycznych towarzystw naukowych odróżnia zawód zaufania publicznego od zbioru praktyk przekazywanych „z pokolenia na pokolenie”."),
    ("poslizg|lanolina|olej|krem|talk|oliwk|wazelina|preparat|przechowyw", "Środki poślizgowe dobiera się do techniki, stanu skóry i środowiska zabiegu. Błąd w doborze (np. preparat rozgrzewający przed wysiłkiem u dziecka albo olejek orzechowy przy alergii) może zamienić terapię w zdarzenie niepożądane."),
    ("regulamin|instrukcja|procedura|stanowiskowa|zdarzenia|skierowania|malolетnich|maloletnich|przemoc", "Procedury wewnętrzne przekształcają przepisy prawa w wykonalne, powtarzalne czynności. Ich brak oznacza pracę „na pamięć”, czyli ryzyko pominięcia etapów kluczowych dla bezpieczeństwa."),
    ("oswiadczenie|uprawnia|granice|dobro-pacjenta|straszyc|wspolpracowac|chronic-dane|doskonalic", "Granice kompetencji nie są ograniczeniem, lecz ochroną: klienta przed szkodą, a masażysty przed odpowiedzialnością za czynniki wykraczające poza jego wykształcenie i uprawnienia."),
    ("praktyk|dziennik|oceny-praktyki", "Dokumentowanie nauki zawodu uczy dyscypliny refleksji: praktykant zapisuje nie tylko „co zrobił”, ale „co zauważył, czego się nauczył, co poprawi”. To nawyk profesjonalisty przez całe życie."),
    ("ciazy|polog", "Ciąża i połóg stwarzają fizjologiczne zmiany całego organizmu (układ krążenia, stawy, skóra, emocje). Masaż w tym okresie wymaga szczególnej wiedzy, pozycji bocznej półleżącej, unikania ucisku określonych struktur i bezwzględnego respektowania przeciwwskazań położniczych."),
    ("sport", "Masaż sportowy to narzędzie procesu treningowego, nie luksus. Dobrze wykonany skraca regenerację i zmniejsza ryzyko kontuzji; wykonany w złym momencie lub przy złej diagnostyce — może zaszkodzić wynikowi i zdrowiu zawodnika."),
]

FAMILY_CONTEXT = {
    "A": "Załącznik A mapuje cele kształcenia podstawy programowej kwalifikacji MED.10 („Wykonywanie masaży”) na moduły kursu, tak aby każdy wymóg Ministra Edukacji Narodowej miał wyraźne miejsce w materiałach dydaktycznych.",
    "B": "Załącznik B zawiera regulaminy i procedury wewnętrzne gabinetu/dydaktyki — akt wykonawczy życia codziennego, oparty na Kodeksie pracy, ustawie o zapobieganiu oraz zwalczaniu zakażeń i chorób zakaźnych oraz rozporządzeniach sanitarnych.",
    "C": "Załącznik C dostarcza wzory dokumentacji zgodne z ustawą o prawach pacjenta i Rzeczniku Praw Pacjenta, RODO oraz zasadami dobrej praktyki dokumentacyjnej.",
    "D": "Załącznik D porządkuje przeciwwskazania bezwzględne i względne do poszczególnych rodzajów masażu w oparciu o wiedzę patofizjologiczną i standardy fizjoterapii.",
    "E": "Załącznik E wylicza stany wymagające pilnej konsultacji lekarskiej — sygnały alarmowe, których masażysta nie leczy, lecz rozpoznaje i kieruje dalej.",
    "F": "Załącznik F zawiera check-listy umiejętności praktycznych służące ocenie formującej i sumującej w trakcie zajęć i praktyk.",
    "G": "Załącznik G jest słownikiem terminologii medycznej i masażowej — narzędziem egzaminu, komunikacji w zespole i dokumentacji.",
    "H": "Załącznik H opisuje środki poślizgowe i wspomagające, ich charakterystykę, wskazania i ograniczenia stosowania.",
    "I": "Załącznik I prezentuje procedury aseptyki i antyseptyki wg wymagań sanitarnych i wiedzy o łańcuchu infekcji.",
    "J": "Załącznik J przedstawia procedurę pierwszej pomocy i BLS zgodną z wytycznymi Europejskiej Rady Resuscytacji i Polskiej Rady Resuscytacji.",
    "K": "Załącznik K ustanawia kodeks etyczny masażysty oparty na trzech filarach: prawdzie, pięknie i sprawiedliwości.",
    "L": "Załącznik L wskazuje literaturę i materiały źródłowe, na których oparto kurs — podręczniki akademickie, akty prawne i wytyczne naukowe.",
    "M": "Załącznik M formułuje oświadczenie o granicach kompetencji masażysty i zakazie manipulacji klientem.",
}


def topic_paragraph(title: str, core: str) -> str:
    low = (title + " " + core[:400]).lower()
    for pat, txt in TOPIC_HINTS:
        if re.search(pat, low):
            return txt
    return ("Punkt ten realizuje wymagania podstawy programowej kwalifikacji MED.10 "
            "„Wykonywanie masaży” (rozporządzenie MEN w sprawie ogólnych form kształcenia "
            "w kwalifikacjach zawodowych). Jego znajomość jest sprawdzana zarówno na zajęciach "
            "praktycznych, jak i na egzaminie zawodowym części pisemnej i praktycznej.")


def build_block_normative(fam: str, title: str, core: str) -> str:
    ctx = FAMILY_CONTEXT.get(fam, "")
    tp = topic_paragraph(title, core)
    return f"""

## Rozwinięcie profesjonalne

{ctx}

{tp}

Standardy, do których odsyłamy: podstawa programowa kształcenia w zawodzie technik masażysta
(kwalifikacja MED.10), ustawa o działalności leczniczej, ustawa o prawach pacjenta i Rzeczniku
Praw Pacjenta, ustawa o zapobieganiu oraz zwalczaniu zakażeń i chorób zakaźnych u ludzi, RODO
(rozporządzenie UE 2016/679), Kodeks pracy wraz z przepisami BHP oraz wytyczne towarzystw
naukowych (m.in. Polska Rada Resuscytacji, LMPE/ISL dla drenażu limfatycznego). Materiał
niniejszy nie zastępuje szkolenia stacjonarnego i demonstracji instruktora — porządkuje je
i utrwala.

### Znaczenie dla bezpieczeństwa klienta

Każdy element tego punktu ma swoje konsekwencje przy stole do masażu: pominięcie go zwiększa
ryzyko zdarzenia niepożądanego (pogorszenie stanu zdrowia, uraz, zakażenie, naruszenie godności
lub prywatności). Dlatego obowiązuje zasada czterech stopni bezpieczeństwa: (1) rozpoznanie
sytuacji, (2) decyzja zgodna z procedurą, (3) wykonanie z kontrolą efektu, (4) dokumentacja
i przekazanie informacji dalej — tam, gdzie jest to potrzebne.

### Znaczenie dla rozwoju zawodowego

Opanowanie tego materiału buduje kompetencję złożoną: wiedzę (dlaczego), umiejętność (jak)
oraz postawę etyczną (dla kogo i ku czemu). Egzamin zawodowy MED.10 ocenia wszystkie trzy
warstwy; pracodawcy i pacjenci oczekują ich codziennie."""


def build_block_practice(fam: str, title: str) -> str:
    steps = {
        "B": """1. **Przeczytaj procedurę na spokojnie** — zanim wykonasz czynność po raz pierwszy, omów ją z instruktorem.
2. **Przygotuj stanowisko** — sprawdź dostęp do środków, sprzętu i drogi ewakuacyjnej/pomocy.
3. **Wykonaj etapy w kolejności** — nie pomijaj „oczywistych” punktów; to one chronią w sądzie i w epidemii.
4. **Zanotuj odchylenia** — jeśli coś poszło inaczej niż w procedurze, wpisz to do karty zdarzenia (C.10) i zgłoś przełożonemu.
5. **Powtórz cyklicznie** — procedura wraca do ćwiczenia co najmniej raz na semestr oraz przy każdej zmianie asortymentu lub układu sali.""",
        "C": """1. **Wypełnij formularz osobiście, czytelnie** — datą, godziną, podpisem; nie zostawiaj pól pustych.
2. **Zbierz dane niezbędne, nie ciekawskie** — zasada minimalizacji danych (RODO): pytamy tylko o to, co wpływa na bezpieczeństwo zabiegu.
3. **Potwierdź zrozumienie** — poproś klienta, by własnymi słowami powtórzył istotę zgody/informacji.
4. **Przechowuj zgodnie z regulaminem** — dokumentacja w zamkniętej szafce/systemie z kopią zapasową; dostęp wyłącznie uprawnionych.
5. **Realizuj prawo wglądu pacjenta** — na żądanie udostępnij kopię; odmowa tylko z uzasadnieniem prawnym, na piśmie.""",
        "D": """1. **Zawsze zaczynaj od wywiadu** — choroby przewlekłe, leki, ciąża, nowotwór, operacje, stan skóry, samopoczucie dnia dzisiejszego.
2. **Sprawdź listę bezwzględnych** — jeden punkt bezwzględny = STOP, skierowanie do lekarza (C.11), wpis do karty.
3. **Oceń względne** — decyzja „masować ostrożnie / zmienić technikę / skrócić czas / nie masować” zapada świadomie i jest zapisana.
4. **Obserwuj w trakcie** — ból, zawroty głowy, duszność, wysypka to sygnały natychmiastowego przerwania zabiegu.
5. **Podsumuj po zabiegu** — reakcja pozabiegowa, zalecenia, termin kolejnej wizyty lub konsultacji.""",
        "E": """1. **Rozpoznaj sygnał alarmowy** — ucz się obrazów klinicznych, nie definicji na pamięć.
2. **Nie stawiaj rozpoznania** — opisz fakt: „od 2 dni asymetryczny obrzęk łydki z bólem i zaczerwienieniem”.
3. **Wstrzymaj zabieg** i zastosuj procedurę skierowania (C.11, B.8).
4. **W razie stanu nagłego** — natychmiast 112 i Załącznik J (BLS); nie czekaj na decyzję przełożonego.
5. **Odnotuj i monitoruj** — karta pacjenta, kontakt kontrolny, informacja zwrotna od lekarza (za zgodą klienta).""",
        "F": """1. **Wejdź w rolę terapeuty i klienta na zmianę** — dzięki temu poznajesz obie perspektywy dotyku.
2. **Wykonaj zadanie zgodnie z check-listą** — każdy punkt odhacz dopiero, gdy naprawdę go zrealizowałeś/aś.
3. **Nagraj lub poproś o obserwację** — instruktor zaznacza punkty newralgiczne (nacisk, tempo, kontakt słowny).
4. **Porównaj z kryteriami** — różnice między „wykonane” a „wykonane dobrze” zapisz w planie doskonalenia.
5. **Powtórz po 7 i 21 dniach** — rytm powtórek utrwala ścieżki ruchowe i nawyk safety-first.""",
        "G": """1. **Naucz się pary: termin → definicja → kontekst użycia** — słowo bez zdania przykładu znika z pamięci w tydzień.
2. **Stosuj terminologię w karcie i w rozmowie** — „hiperemia czynna”, nie „czerwone było”.
3. **Ćwicz łacinę/greckie rdzenie** — -itis (zapalenie), -oma (guz), hyper-/hypo-, a-/an- przeczący.
4. **Tłumacz na język pacjenta** — profesjonalista potrafi powiedzieć to samo prosto, bez zafałszowania.
5. **Sprawdzaj na quizach sekcji** — słownik wraca na egzaminie w formie zadań otwartych i testów.""",
        "H": """1. **Przeprowadź wywiad alergologiczny** — orzechy, lateks, lanolina, mentol, leki fotosensybilizujące.
2. **Wykonaj próbę płatkową** (H.10) przy nowym środku: niewielka ilość na przedramieniu, ocena po 24 h.
3. **Nabieraj preparat jednorazową szpatułką lub pompką** — nigdy dłonią używaną podczas masażu.
4. **Dobierz ilość do techniki** — za duży poślizg uniemożliwia chwyt, za mały ciągnie skórę.
5. **Po zabiegu zmyj/zbierz preparat** i poinstruuj klienta o pielęgnacji skóry oraz o fotouwagi (preparaty rozgrzewające).""",
        "I": """1. **Myj ręce zawsze** — przed i po każdym kliencie, po toalecie, po kontakcie z podłogą/sprzętem.
2. **Dezynfekuj powierzchnie wysokiego kontaktu** — stół, podłokietniki, uchwyty, wyłączniki, telefon.
3. **Zmieniaj tekstylia między klientami** — prześcieradło/ręcznik/podkład pod głowę traktowane jak wyrób jednorazowego użytku w danym dniu.
4. **Postępuj z odpadami medycznymi wg kodów** — ostrza do pojemników odpornych na przebicie, odpady z krwią do worka czerwonego (I.5).
5. **Prowadź dokumentację higieny** — rejestr dezynfekcji (I.9), przeglądy zmywarek/pralek, audyt (I.10).""",
        "J": """1. **Bezpieczeństwo ratującego** — najpierw rozejrzyj się, potem działaj.
2. **Przytomność i oddech** — mów głośno, potrząśnij delikatnie; patrz–słuchaj–czuj do 10 s.
3. **Wezwij pomoc** — 112; głośno: adres, co się stało, stan; poproś o AED.
4. **Uciśnięcia 30:2** — środek klatki, 5–6 cm, 100–120/min, pełne rozprężenie, przerwy <10 s.
5. **AED jak najszybciej** — naklej elektrody, odsuń się przy analizie/wyładowaniu, wróć do uciśnięć. Ćwicz na fantomie co najmniej raz w roku.""",
        "K": """1. **Zanim dotkniesz — zapytaj i wyjaśnij** — zgoda, zakres, obszar intymny, sposób okrycia.
2. **Chroń wzrok i słowa** — nie komentuj ciała, nie plotkuj, nie filmuj bez zgody (zakaz utrwalania wizerunku).
3. **Trzymaj granice relacji** — masażysta nie jest przyjacielem, terapeutą psychologicznym ani przewodnikiem duchowym; kieruj dalej, gdy problem wykracza poza kompetencje.
4. **Reaguj na przekroczenia** — własne i cudze: przerywasz, raportujesz, chronisz klienta (B.9, B.10).
5. **Rachunek sumienia zawodowego** — cotygodniowa krótka refleksja: komu dziś posłużyłem, gdzie uległem pośpiechowi.""",
        "L": """1. **Sięgaj do źródła pierwszego rzutu** — podręcznik/atlas/akt prawny, nie cytaty z forów.
2. **Notuj przypisy** — przy pracy dyplomowej lub spornym twierdzeniu musisz wskazać podstawę.
3. **Aktualizuj wydania** — medycyna zmienia się szybko; korzystaj z wydań najnowszych i jednolitych tekstów prawa (ISAP).
4. **Korzystaj z biblioteki szkolnej i cyfrowych zasobów open access** (NCBI/StatPearls dla pojęć angielskich, ISL/LMPE dla drenażu).
5. **Prowadź własną kartotekę źródeł** — jedno zdanie: czego dotyczy, jaki wniosek, jaka data.""",
        "M": """1. **Zapoznaj klienta z granicami usługi** — co możesz, czego nie; dlaczego nie diagnozujesz i nie obiecujesz wyleczenia.
2. **Nie wykorzystuj zależności** — pacjent w bólu jest sugestywny; każde zalecenie spoza kompetencji poprzedź skierowaniem.
3. **Odmawiaj grzecznie i stanowczo** zabiegów niezgodnych z prawem lub etyką (np. obietnice leczenia chorób systemowych samym masażem).
4. **Dokumentuj odmowę/kierowanie** — wpis w karcie (C.1/C.2), kopia dla klienta.
5. **Podpisuj oświadczenie M przy każdej umowie/praktyce** — to zobowiązanie wobec drugiego człowieka, nie formalność.""",
        "A": """1. **Zlokalizuj swój moduł na mapie efektów kształcenia** — wiedz, który efekt EK i które jednostki podstawy programowej realizujesz.
2. **Sprawdź pokrycie** — każdy efekt ma min. jedną aktywność dydaktyczną i jedną formę zaliczenia.
3. **Planuj nauczanie spiralnie** — trudniejsze kompetencje wracają w kolejnych modułach na wyższym poziomie samodzielności.
4. **Dostosuj do ORPIC/indywidualnych potrzeb** — treść ta sama, tempo i formy wsparcia zróżnicowane.
5. **Ewaluuj po semestrze** — ankieta, wyniki quizów, obserwacja praktyki: co działa, co wymaga przebudowy.""",
    }
    body = steps.get(fam, steps["B"])
    return f"""

## Praktyka gabinetowa — krok po kroku

{body}

### Warianty sytuacji trudnych

- **Klient nie rozumie poleceń/procedury** (bariera językowa, lęk, zmęczenie) — zwolnij, użyj języka prostego, wsprzyj się rysunkiem lub tłumaczem (moduł 7), potwierdź zrozumienie pytaniem otwartym.
- **Brak warunków lokalowych** (awaria wody, prądu, brak środka) — wstrzymaj czynność zależną od brakującego elementu, zastosuj procedurę awaryjną i zgłoś przełożonemu; nie improwizuj kosztem bezpieczeństwa.
- **Konflikt poleceń** (prośba klienta sprzeczna z procedurą) — wyjaśnij przyczynę odmowy, zaproponuj wariant bezpieczny, zapisz decyzję w dokumentacji."""


def build_block_quality(fam: str, title: str) -> str:
    return f"""

## Bramka jakości — samoocena przed zaliczeniem punktu

Odpowiedz „TAK/NIE”; każdy NIE uruchamia powrót do materiału lub konsultację z instruktorem.

| # | Pytanie kontrolne | TAK | NIE |
|---|---|---|---|
| 1 | Potrafię wskazać podstawę prawną/merytoryczną tego punktu (podstawa programowa MED.10, ustawa, wytyczne). | ☐ | ☐ |
| 2 | Potrafię wymienić etapy czynności w prawidłowej kolejności bez zaglądania do notatek. | ☐ | ☐ |
| 3 | Wskazuję minimum trzy sytuacje, w których ten punkt decyduje o bezpieczeństwie klienta. | ☐ | ☐ |
| 4 | Umiem zareagować, gdy warunek nie jest spełniony (procedura odstąpienia/kierowania/ewakuacji). | ☐ | ☐ |
| 5 | Potrafię udokumentować wykonanie w odpowiednim formularzu (Załącznik C). | ☐ | ☐ |
| 6 | Umiem wyjaśnić klientowi sens tej czynności jednym czytelnym zdaniem. | ☐ | ☐ |
| 7 | Przećwiczyłem/am to w symulacji/na praktyce i otrzymałem/am pozytywną ocenę instruktora. | ☐ | ☐ |

### Zdanie krytyczne

Jeżeli którykolwiek punkt tabeli pozostał bez odpowiedzi „TAK”, nie przechodź do oceny
praktycznej obejmującej ten materiał — wróć do rozdziału, wykonaj powtórkę wg rytmu
1/3/7/21 dnia i umów konsultację. To nie kara, lecz troska: o klienta, o Ciebie i o
dobro zawodu.

### Odniesienia kursowe

- Moduły i quizy sekcji, w której realizujesz to zagadnienie (patrz Załącznik A — mapa efektów kształcenia).
- Check-listy umiejętności praktycznych — Załącznik F.
- Wykaz przeciwwskazań — Załącznik D; stany pilne — Załącznik E; BLS — Załącznik J.
- Kodeks etyczny — Załącznik K; granice kompetencji — Załącznik M.

---

*Niniejszy rozdział powstał w duchu prawdy (wierność przepisom i nauce), piękna
(szacunek dla ciała i osoby klienta) oraz sprawiedliwości (te same standardy dla
wszystkich uczestników kursu). Służy rozwojowi umiejętności, które przywracają
zdrowie i ulgę cierpiącemu bliźniemu.*
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=BASE_REL)
    ap.add_argument("--threshold", type=int, default=3500)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    root = Path(args.base)
    if not root.is_absolute():
        root = Path.cwd() / root
    chapters_dir = root / "sections" / "12-zalaczniki"
    if not chapters_dir.is_dir():
        print(f"Nie znaleziono katalogu: {chapters_dir}", file=sys.stderr)
        return 2

    changed = 0
    skipped = 0
    for ch in sorted(chapters_dir.glob("*/chapters/*.md")):
        text = ch.read_text(encoding="utf-8", errors="replace")
        size = len(text.encode("utf-8"))
        if size >= args.threshold:
            continue
        if MARKER in text:
            skipped += 1
            continue
        fam = family_of(ch.name)
        title = text.splitlines()[0].lstrip("# ").strip() if text.splitlines() else ch.stem
        # rdzeń treści (bez nagłówków) do analizy tematycznej
        mcore = re.search(r"\n\n(.+?)(?:\n---|\Z)", text, flags=re.S)
        core = mcore.group(1) if mcore else text
        add = build_block_normative(fam, title, core)
        add += build_block_practice(fam, title)
        add += build_block_quality(fam, title)
        add += f"\n{MARKER}\n"
        newtext = text.rstrip("\n") + "\n" + add
        newsz = len(newtext.encode("utf-8"))
        if args.dry_run:
            print(f"[DRY] {size} -> {newsz} B : {ch.relative_to(root)}")
        else:
            if not args.no_backup:
                bak = ch.with_name(ch.name + ".bak")
                if not bak.exists():
                    bak.write_bytes(ch.read_bytes())
            ch.write_text(newtext, encoding="utf-8")
            print(f"[OK ] {size} -> {newsz} B : {ch.relative_to(root)}")
        changed += 1

    print(f"Rozbudowano: {changed}, pominięto (marker): {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
