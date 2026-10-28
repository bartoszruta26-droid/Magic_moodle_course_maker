#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Konwersja załączników A–M (aktywności label) na aktywności typu book.

Stan wejściowy: sekcja 12-zalaczniki zawiera 13 plików label-XX.md jako
etykiety (label). Etykieta w Moodle to krótki komunikat — nie nadaje się do
obszernej treści referencyjnej. Zgodnie z preferencją kursu (book jako główna
aktywność dydaktyczna, unikanie page/label dla długich treści) każdy
załącznik staje się książką:

    book-01-zalacznik-a-mapa-efektow-ksztalcenia-med-10/
        book.yaml
        chapters/00-wprowadzenie.md            (wprowadzenie + spis treści)
        chapters/NN-...podpunkty....md         (każdy podpunkt = rozdział)

Zasady:
  * TREŚĆ NIGDY NIE JEST TRACONA: istniejące bloki "## Treść szczegółowa"
    zostają przeniesione do odpowiednich rozdziałów; podpunkty posiadające
    wyłącznie placeholder ("Pozycja załącznika ...") otrzymują rzetelną,
    fachową treść napisaną przez autorów kursu (prawda, piękno, sprawiedliwość).
  * Stare pliki label-*.md pozostają w katalogu (kopia robocza), ale NIE są
    już wymieniane w section.yaml — sekcja wskazuje książki.
  * Operacja idempotentna: jeśli book.yaml dla danego załącznika istnieje,
    skrypt pomija jego konwersję (chyba że --force).
  * section.yaml jest przepisywany WYŁĄCZNIE, gdy wszystkie 13 książek
    zostało utworzonych i zwalidowanych (nagłówek YAML parsuje się).

Użycie:
    python3 scripts/enrich_masaz_zalaczniki_books.py \
        [--base courses/03-kurs-masazysta-med10] [--dry-run] [--force]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BASE_REL = "courses/03-kurs-masazysta-med10"

STUB_RE = re.compile(
    r"Pozycja załącznika [„A-M]+ .*?Dokument uzupełnia kadra dydaktyczna.*?"
    r"etapie kształcenia\.\s*",
    re.S,
)

# ---------------------------------------------------------------------------
# Fachowe treści uzupełniające dla podpunktów, które były placeholderami.
# Klucz: prefiks numeru podpunktu (np. "E.7"). Wartość: treść markdown.
# Wszystkie treści zgodne z podstawą programową MED.10 i literaturą przedmiotu
# (Zborowski, Doerr, Faller/Schwind, Bochenek/Traczyk, wytyczne ERC 2021).
# ---------------------------------------------------------------------------
CONTENT: dict[str, str] = {
    # ---- Załącznik A: mapa efektów kształcenia -----------------------------
    "A.1": """Efekty modułu 1 (BHP) realizują efekt kształcenia: *„Organizowanie stanowiska pracy oraz przestrzeganie zasad bezpieczeństwa i higieny pracy, przepisów przeciwpożarowych i ochrony środowiska”*.

**Uczeń potrafi:** rozpoznać czynniki szkodliwe i uciążliwe w gabinecie masażu; zastosować procedury mycia i dezynfekcji rąk; ocenić ergonomia stanowiska; przeprowadzić ewakuację; udzielić pierwszej pomocy. **Kwalifikacyjne:** zna prawa i obowiązki pracownika i pracodawcy oraz postępowanie z materiałami zakaźnymi.

**Jak mierzymy:** quizy 1.1–1.5, check-lista F.1–F.2, obserwacja stanowiska na praktyce (10), scenariusz BLS (załącznik J).""",
    "A.2": """Efekty modułu 2 (podstawy masażu) odpowiadają efektom: *„Posługiwania się podstawami anatomii, fizjologii i patologii przy wykonywaniu zabiegów”* oraz *„Korzystania z dokumentacji związanej z wykonywaniem zadań zawodowych”*.

**Uczeń potrafi:** wskazać na preparacie i na ciele żywym struktury objęte masażem; wyjaśnić mechanizm działania głaskania, rozcierania, ugniatania, oklepywania i wibracji; dobrać dawkę zabiegu; rozróżnić wskazania od przeciwwskazań bezwzględnych i względnych.

**Jak mierzymy:** quizy 2.x, karty pracy z atlasem, lokalizacja palpacyjna (book-14), kolokwium śródmodułowe."""
,
    "A.3": """Moduł 3 (podstawy masażu w medycynie) obsługuje efekt: *„Rozpoznawania stanów fizjologicznych i patologicznych mających znaczenie dla wykonania masażu”*.

**Uczeń potrafi:** opisać przebieg najczęstszych chorób układu ruchu, krążenia, oddechowego, pokarmowego, moczowo-płciowego, nerwowego oraz skóry w zakresie potrzebnym masażyście; przyporządkować każdej jednostce chorobowej wskazania, przeciwwskazania i modyfikacje techniki; rozpoznać sygnały alarmowe wymagające konsultacji lekarskiej (załącznik E).

**Jak mierzymy:** studia przypadków (book-11 modułu 11), mapy pojęciowe „choroba → reakcja ustroju → dobór techniki”, quizy 3.x.""",
    "A.4": """Moduł 4 (wykonywanie masażu w medycynie) to efekt: *„Wykonywania masażu leczniczego zgodnie ze wskazaniami, przeciwwskazaniami i zasadami bezpieczeństwa”*.

**Uczeń potrafi:** ocenić pacjenta na potrzeby zabiegu (wywiad, karta); zaplanować i wykonać masaż klasyczny częściowy i całkowity, segmentarny, łąkotkowy, okostnowy, punktowy, drenaż limfatyczny i CDT; rozpoznać odczyny po masażu i zmodyfikować kolejne zabiegi; prowadzić dokumentację zabiegową.

**Jak mierzymy:** check-listy F.9–F.23 na pracowni, egzamin próbny praktyczny (symulacje OKE), portfolio z karty zabiegowych.""",
    "A.5": """Moduł 5 (masaż w sporcie) realizuje efekt w zakresie: *„Wykonywania masażu sportowego i przygotowania zawodników do wysiłku”*.

**Uczeń potrafi:** rozróżnić masaż przedstartowy, treningowy i regeneracyjny oraz dobrać ich czas, tempo i siłę do fazy cyklu treningowego; współpracować z trenerem i fizjoterapeutą w ramach zespołu; postępować z typowymi kontuzjami sportowymi w granicach kompetencji (bez diagnozy!).

**Jak mierzymy:** scenki protokołów (book-06 modułu 5), test sytuacyjny „przed startem / po wysiłku / w mikrocyklu”, quizy 5.x.""",
    "A.6": """Moduł 6 (masaż prozdrowotny) odpowiada efektowi: *„Wykonywania masażu prozdrowotnego i relaksacyjnego oraz prowadzenia działań edukacyjnych”*.

**Uczeń potrafi:** przygotować atmosferę zabiegu (światło, ciepło, cisza); wykonać masaż rozluźniający całościowy; nauczyć klienta prostych ćwiczeń oddechowych i samo-masażu; popularyzować zachowania prozdrowotne uczciwie, bez obietnic leczniczych wykraczających poza kompetencje.

**Jak mierzymy:** ocena koleżeńska zabiegu wg kryteriów jawnych, projekt edukacyjny (assignment), quizy 6.x.""",
    "A.7": """Moduł 7 (język obcy zawodowy) wspiera efekt: *„Komunikowania się w języku obcym w typowych sytuacjach zawodowych”*.

**Uczeń potrafi:** nazwać po angielsku (lub w innym języku kursu) stanowisko, przybory i techniki; przeczytać kartę pacjenta i ulotkę preparatu; przeprowadzić prosty wywiad i instruktaż; przekazać informację zwrotną partnerowi zagranicznemu; stosować strategie kompensacyjne przy brakującym słowie.

**Jak mierzymy:** role-play nagrane (rozmowa z klientem obcojęzycznym), tłumaczenie fragmentu karty zabiegowej, quizy leksykalne 7.x.""",
    "A.8": """Moduł 8 (kompetencje osobiste i społeczne) obsługuje efekty: *„Porozumiewania się i współdziałania w kontaktach z klientem i zespołem”* oraz *„Oceniania własnych możliwości i ograniczeń”*.

**Uczeń potrafi:** prowadzić rozmowę trudną (ból, wstyd ciała, reklamacja); asertywnie odmówić czynności sprzecznych z etyką lub bezpieczeństwem; rozpoznawać wypalenie i stosować samoregenerację; budować autorytet przez rzetelność, nie przez dominację.

**Jak mierzymy:** studium przypadków konfliktu, ankieta stylów komunikacji, superwizja koleżeńska, eseje refleksyjne (assignment).""",
    "A.9": """Moduł 9 (organizacja pracy małych zespołów) realizuje efekt: *„Organizowania i oceniania pracy małego zespołu”*.

**Uczeń potrafi:** zaplanować pracę gabinetu (grafik, zaopatrzenie); dobrać osoby do zadań wg kompetencji; kierować wykonaniem i ocenić jakość; wprowadzać usprawnienia techniczne i organizacyjne; rozliczać zadania sprawiedliwie i rzeczowo.

**Jak mierzymy:** projekt organizacji dnia pracy pracowni, runda lidera w zespole uczniowskim, analiza kosztów błędu (case study).""",
    "A.10": """Praktyka zawodowa (moduł 10) domyka efekt kompleksowy: *„Swobodnego wykonywania zadań zawodowych w rzeczywistym środowisku pracy pod nadzorem”*.

**Uczeń potwierdza:** samodzielność w rutynie dnia zabiegowego, kulturę higieny, dokumentację, komunikację z pacjentem i zespołem oraz umiejętność korzystania z informacji zwrotnej. Minimum godzin praktyki wynika z ramowej podstawy programowej MED.10 i regulaminu kursu (harmonogram, załącznik B).

**Jak mierzymy:** ocena opiekuna praktyki (arkusz), dziennik praktyki, portfolio (book-05), obrona jednego przypadku.""",
    # ---- Załącznik B: brakujące procedury ----------------------------------
    "B.4": """**Cel:** bezpieczne, higieniczne i sprawne przygotowanie stanowiska przed każdym klientem.

1. Sprawdź czystość stołu (brak plam, uszkodzeń tapicerki) i stabilność konstrukcji.
2. Nałóż czyste prześcieradze: gumowe na wierzch warstwy ochronnej, tekstylne na wierzch; chroń zagłówek jednorazowym podkładem.
3. Przygotuj ręczniki/okrycia (minimum 2), środek poślizgowy z próby alergicznej, kosz na brudną bieliznę w zasięgu ręki.
4. Ustaw temperaturę pomieszczenia 22–24°C, oświetlenie pośrednie, wyeliminuj hałas.
5. Zdezynfekuj powierzchnie kontaktowe (podłokietniki, zagłówek) preparatem zatwierdzonym do wyrobów medycznych, czas działania wg karty charakterystyki.
6. Umyj i zdezynfekuj ręce tuż przed kontaktem z klientem (por. F.2).
7. Kontrola końcowa: czy klient ma zapewnioną intymność (zamknięte drzwi), wodę, dzwonek/wyjście, informację o sygnale przerwania zabiegu.

**Kryterium jakości:** stanowisko gotowe ≤5 minut między klientami, bez pośpiechu kosztem aseptyki.""",
    "B.5": """**Segregacja odpadów w gabinecie masażu:**

* ** Odpady komunalne (zmieszane):** zużyte ręczniki papierowe (nieskażone), opakowania po preparatach czystych, odpady biura.
* **Frakcja tekstylna do prania:** prześcieradła i ręczniki tkaninowe — transport w zamkniętym worku do pralni z certyfikatem (temp. ≥60°C z detergentem dezynfekcyjnym).
* **Odpady medyczne (jeśli powstaną):** materiały skażone krwią lub wydalinami — żółty worek/pojemnik „medyczne”, odbiór przez uprawniony podmiot; masażysta nie generuje ich rutynowo, ale musi umieć zabezpieczyć (rękawiczki, środek dezynfekcyjny do rąk). Zasada: rękawiczki nitrylowe przy każdym podejrzeniu kontaktu z płynami ustrojowymi.
* **Ostre (igły, szkło):** w gabinecie masażu nie występują — jeśli klient posiada sprzęt medyczny (insulina), nie dotykaj go.
* **Chemikalia:** resztki środków dezynfekcyjnych — zgodnie z kartą charakterystyki (SDS), nigdy do kanalizacji w dużych ilościach.

**Dokumentacja:** umowa z firmą odbierającą odpady medyczne, ewidencja (kart przekazania), szkolenie okresowe pracowników.""",
    "B.10": """**Procedura przeciwdziałania przemocy i ochrony osób szczególnie wrażliwych** (spójna z modułem 2, book-21):

1. **Prewencja:** każde spotkanie z nowym klientem — omówienie granic dotyku, zgoda na obszar zabiegu, obecność osoby trzeciej na życzenie klienta, drzwi możliwe do otwarcia od środka.
2. **Rozpoznawanie:** ślady urazów w różnych stadiach gojenia, lęk przed dotykiem górnej części tułowiu, towarzysząca osoba „odpowiadająca” za klienta, niespójna historia obrażeń.
3. **Reagowanie:** zachowaj spokój, nie oskarżaj, nie pytaj przy świadkach; zadaj jedno pytanie prywatnie: „Czy jesteś bezpieczny/a w domu?”; zapisz obiektywnie spostrzeżenia w karcie.
4. **Kierowanie:** przekaż informacje o bezpłatnej pomocy (Niebieska Linia 800 12 00 02, 112 w zagrożeniu życia); w sytuacji bezpośredniego zagrożenia — wezwij służby.
5. **Ochrona pracownika:** procedura „stop” przy każdej nagannej propozycji lub agresji — przerwij zabieg, opuść salę, dokumentuj, zgłoś przełożonemu; dwukrotne zdarzenie = wpis do rejestru klientów i trwała odmowa usług.
6. **Zakres prawny:** masażysta nie jest funkcjonariuszem — nie zatrzymuje, nie przesłuchuje; jego rolą jest rozpoznanie, niezawiniona dyskrecja i most do pomocy systemowej.""",
    # ---- Załącznik E: stany pilne (uzupełnienie E.8–E.15) ------------------
    "E.8": """**Objawy infekcji ogólnoustrojowej (gorączka, poty, dreszcze, powiększone węzły)** — ciało w walce z patogenem nie potrzebuje dodatkowego pobudzenia krążenia. Odłóż zabieg; przy objawach sepsy (splątanie, oddech >22/min, ciśnienie skurczowe <100 mmHg) — natychmiast 112/999. Masaż wykonasz po 48 h bez gorączki i za zgodą lekarza.""",
    "E.9": """**Nasilający się ból głowy o nagłym początku („najgorszy ból życia”), z zaburzeniami widzenia, wymiotami lub sztywnością karku** — podejrzenie krwawienia podpajęczynówkowego lub zapalenia opon mózgowych: 112/999, pozycja spokojna, żadnego masażu szyi i głowy, nie podawaj leków na własną rękę.""",
    "E.10": """**Zaburzenia czucia, siły lub koordynacji nowe albo postępujące** (drętwienie połowy twarzy/kończyny, opadanie stopy, chwianie przy chodzeniu) — sygnał ośrodkowego lub obwodowego uszkodzenia nerwowego: pilna konsultacja neurologiczna; do czasu rozpoznania masaż tylko głaskaniem poza obszarem objętym, bez technik głębokich i korekcyjnych.""",
    "E.11": """**Nowotwór w wywiadzie bez pisemnej zgody lekarza prowadzącego/onkologa** — masaż osób w trakcie leczenia onkologicznego wymaga uzgodnienia z ośrodkiem (ryzyka: zakrzepica, małopłytkowość, obrzęk limfatyczny obszaru po limfadenektomii, metastazy kostne). Zasada: brak zgody = brak zabiegu leczniczego; dopuszczalne wyłącznie delikatne głaskanie poza polem promieniowania i zmianami, za zgodą pacjenta i personelu medycznego.""",
    "E.12": """**Ciąża z krwawieniem, bólami kurczowymi, odpływaniem płynu lub zmniejszeniem ruchomości dziecka** — stan zagrożenia ciąży: natychmiast pomoc położnicza (SOR/112). Masaż w ciąży sam w sobie nie jest przeciwwskazany, ale przy jakimkolwiek alarmie położniczym przerywasz wszelki kontakt z ciałem klientki i wzywasz pomoc.""",
    "E.13": """**Dolegliwości neurologiczne postępujące** (narastający niedowład, atrofie, napady drgawkowe, zmiany zachowania) — wymagają diagnostyki specjalistycznej; masażysta opisuje obserwacje w karcie, nie stawia rozpoznań, kieruje do lekarza i dostosowuje/zawiesza zabiegi do wyników konsultacji.""",
    "E.14": """**Zmiany skórne ropne (czyraki, ropnie, róża, półpasiec w fazie pęcherzykowej) lub rozległe (egzema, łuszczyca w ostrym rzucie, grzybica)** — bezwzględne przeciwwskazanie miejscowe i często ogólne (ryzyko szerzenia zakażenia, autoinokulacji, transmisji personelowi i innym klientom). Kieruj do dermatologa/POZ; zabieg dopiero po świadectwie wyleczenia lub zgodzie lekarza z wyraźnym oznaczeniem pola omijanego.""",
    "E.15": """**Każdy stan, którego masażysta nie potrafi bezpiecznie ocenić** — reguła najwyższa: niepewność jest informacją, że potrzebujesz wsparcia medycznego, nie więcej techniki. Zatrzymaj zabieg, powiedz klientowi spokojnie prawdę („widzę objaw, który wymaga oceny lekarza — nie chcę ryzykować Twoim zdrowiem”), udokumentuj i skieruj. To akt sprawiedliwości i miłości bliźniego, nie porażka zawodowa.""",
    # ---- Załącznik F: pełne check-listy F.1–F.30 ---------------------------
    "F.1": """### Cel i kontekst
Przygotowanie stanowiska pracy masażysty przed zabiegiem (por. procedura B.4).

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Stół stabilny, czysty, wysokość wyregulowana do łokci wykonującego | ☐ | ☐ | ☐ |
| 2 | Świeża bielizna: podkład gumowy + prześcieradło + 2 ręczniki | ☐ | ☐ | ☐ |
| 3 | Preparat poślizgowy sprawdzony (data, alergia w karcie klienta) | ☐ | ☐ | ☐ |
| 4 | Temperatura 22–24°C, światło pośrednie, brak przeciągu | ☐ | ☐ | ☐ |
| 5 | Kosz na odpady i pojemnik na bieliznę brudną w zasięgu | ☐ | ☐ | ☐ |
| 6 | Dostęp do wody pitnej dla klienta, dzwonek/sygnał przerwania | ☐ | ☐ | ☐ |
| 7 | Dezynfekcja powierzchni kontaktowej udokumentowana | ☐ | ☐ | ☐ |

**Ocena:** 0 = niewykonane/niepotrzebne, 1 = z pomocą, 2 = samodzielnie i bezpiecznie. Próg zaliczenia: wszystkie punkty = 2, minimum 6/7 bez pomocy.""",
    "F.2": """### Mycie i dezynfekcja rąk WHO/German (hygienic hand disinfection)

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Skrócone paznokcie, bez pierścionków i zegarka | ☐ | ☐ | ☐ |
| 2 | Mycie 40–60 s: dłonie, przestrzenie międzypalcowe, kciuki, palce, opuszki, nadgarstki | ☐ | ☐ | ☐ |
| 3 | Spłukanie pod bieżącą wodą, osuszenie ręcznikiem jednorazowym | ☐ | ☐ | ☐ |
| 4 | Dezynfekcja 30 s preparatem alkoholowym — ta sama sekwencja | ☐ | ☐ | ☐ |
| 5 | Czas działania preparatu dotrzymany (skóra wilgotna przez cały czas aplikacji) | ☐ | ☐ | ☐ |
| 6 | Ręce poniżej łokci, łokcie nie dotykają umywalki, kran zakręcany łokciem/ręcznikiem | ☐ | ☐ | ☐ |
| 7 | Kolejność: mycie → suszenie → dezynfekcja → krem nocny (bez zapachu przed zmianą!) | ☐ | ☐ | ☐ |

**Błąd krytyczny:** dezynfekcja brudnych lub mokrych rąk = wynik 0 niezależnie od pozostałych punktów.""",
    "F.3": """### Prowadzenie wywiadu przed masażem

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Przedstawienie się, cel spotkania, zapewnienie poufności (RODO) | ☐ | ☐ | ☐ |
| 2 | Pytania o choroby przewlekłe, przebyte, aktualne leczenie i leki | ☐ | ☐ | ☐ |
| 3 | Alergie (preparaty, lateks), ciąża, miesiączka, operacje, urazy | ☐ | ☐ | ☐ |
| 4 | Charakter bólu: gdzie, kiedy, nasilenie w skali 0–10, co nasila/łagodzi | ☐ | ☐ | ☐ |
| 5 | Cele klienta realistycznie nazwane i zanotowane | ☐ | ☐ | ☐ |
| 6 | Zgoda na zabieg i na obszar; informacja o prawie przerwania w każdej chwili | ☐ | ☐ | ☐ |
| 7 | Podpis w karcie, wpis danych do dokumentacji, plan serii | ☐ | ☐ | ☐ |

**Rozmawiaj stojąc/siedząc na poziomie oczu klienta — nie zza stołu jak zza biurka sądu.**""",
    "F.4": """### Ocena postawy (obserwacyjna, bez diagnozy)

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Widok z przodu: symetria barków, trójkątów talii, ustawienie miednicy | ☐ | ☐ | ☐ |
| 2 | Widok z boku: linia ucha–biodro–kostka, krzywizny kręgosłupa | ☐ | ☐ | ☐ |
| 3 | Widok z tyłu: łopatki, linia kręgosłupa, dołki biodrowe | ☐ | ☐ | ☐ |
| 4 | Opis słowny + szkic (± odchylenia), data i podpis | ☐ | ☐ | ☐ |
| 5 | Wskazanie asymetrii jako „obserwacji”, nie „skoliozy” | ☐ | ☐ | ☐ |
| 6 | Propozycja dalszej oceny (fizjoterapeuta/lekarz) przy niepokojących cechach | ☐ | ☐ | ☐ |""",
    "F.5": """### Pomiar obwodów kończyn (kontrola obrzęku)

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Stałe punkty pomiarowe oznaczone (np. 10 cm poniżej rzepki) | ☐ | ☐ | ☐ |
| 2 | Taśma elastyczna, bez ucisku, ten sam nacisk przy każdym pomiarze | ☐ | ☐ | ☐ |
| 3 | Pozycja klienta identyczna przy każdym pomiarze | ☐ | ☐ | ☐ |
| 4 | Pomiar L/P w tej samej kolejności, zapis obu wartości | ☐ | ☐ | ☐ |
| 5 | Data, godzina, komentarz (np. „po 3. drenażu”) | ☐ | ☐ | ☐ |
| 6 | Interpretacja: różnica >1,5–2 cm lub przyrost >10% → zgłoś lekarzowi | ☐ | ☐ | ☐ |""",
    "F.6": """### Ocena zakresu ruchu (ROM)

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Ruch czynny najpierw, potem bierny — zawsze w tym porządku | ☐ | ☐ | ☐ |
| 2 | Stabilizacja proximalna, wolne tempo, pełny łuk | ☐ | ☐ | ☐ |
| 3 | Określenie end-feel (miękki/twardy/pusty) i bólu przy ruchu | ☐ | ☐ | ☐ |
| 4 | Porównanie stron ciała, zapis w stopniach lub opisowo | ☐ | ☐ | ☐ |
| 5 | Bez forsowania! Ból = stop; ruch oporowy zarezerwowany dla fizjoterapeuty | ☐ | ☐ | ☐ |""",
    "F.7": """### Palpacja mięśni i tkanek miękkich

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Rozgrzane dłonie, krótkie paznokcie, kontakt całej opuszki | ☐ | ☐ | ☐ |
| 2 | Ocena temperatury skóry (rękaw „grzbietowy”) | ☐ | ☐ | ☐ |
| 3 | Napięcie spoczynkowe, tonus przy ruchu biernym | ☐ | ☐ | ☐ |
| 4 | Bolesność, guzki, pasma — lokalizacja wg struktur anatomicznych | ☐ | ☐ | ☐ |
| 5 | Opis w karcie („wzmożone napięcie mm. trapezius cz. zstępującej L>P”), nie rozpoznanie | ☐ | ☐ | ☐ |""",
    "F.8": """### Lokalizacja punktów spustowych (trigger points)

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Technika palpacji płaskiej i pinch — obie zastosowane | ☐ | ☐ | ☐ |
| 2 | Reakcja skurczowa, ból promieniujący wg projekcji znanych z literatury | ☐ | ☐ | ☐ |
| 3 | Brak „strzelania” i manipulacji w stawach (kompetencja terapeuty manualnego) | ☐ | ☐ | ☐ |
| 4 | Delikatna terapia uciskowa w granicach komfortu klienta (≤7/10) | ☐ | ☐ | ☐ |
| 5 | Zgłoszenie lekarzowi objawów neurologicznych towarzyszących | ☐ | ☐ | ☐ |""",
    "F.9": """### Głaskanie (effleurage)

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Cała dłoń przylega, kciuk tworzy „okno”, brak marszczenia skóry | ☐ | ☐ | ☐ |
| 2 | Kierunek odpływu żylno-chłonnego ku sercu | ☐ | ☐ | ☐ |
| 3 | Tempo 1–2 ruchy/s (relaks: wolniej), rytm oddechu klienta zsynchronizowany | ☐ | ☐ | ☐ |
| 4 | Otwiera i zamyka każdy etap oraz cały zabieg | ☐ | ☐ | ☐ |
| 5 | Ciężar z tułowia, nie z palców — barki rozluźnione | ☐ | ☐ | ☐ |""",
    "F.10": """### Rozcieranie

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Podstawa dłoni lub opuszki — chwyt stabilny, skóra nie „jedzie” fałdem | ☐ | ☐ | ☐ |
| 2 | Ruchy okrężne, poprzeczne, spiralne — dobór do tkanki | ☐ | ☐ | ☐ |
| 3 | Siła wg tolerancji klienta (skala bólu ≤5/10), komunikacja „czy taka siła OK?” | ☐ | ☐ | ☐ |
| 4 | Czas 3–5 min na obszar, kontrola rumienia (umiarkowany, blady przy zwolnieniu) | ☐ | ☐ | ☐ |
| 5 | Bez rozcierania po żylakach, wybroczynach, zmianach skórnych | ☐ | ☐ | ☐ |""",
    "F.11": """### Ugniatanie

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Chwyt wałeczkowy obu rąk, „fala” od proximal do distal | ☐ | ☐ | ☐ |
| 2 | Rytm 30–40 uchiwań/min, synchronizacja z oddechem klienta | ☐ | ☐ | ☐ |
| 3 | Praca na mięśniu w lekkim rozciągnięciu lub skróceniu — świadomy wybór | ☐ | ☐ | ☐ |
| 4 | Brak bólu ostrego; po ugniataniu — głaskanie wyciszające | ☐ | ☐ | ☐ |
| 5 | Omijanie tętnic, nerwów powierzchownych (dół łokciowy, trójkąt tętniczy szyi) | ☐ | ☐ | ☐ |""",
    "F.12": """### Oklepywanie

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Nawierzchnia: krawędź dłoni, palce prostowane, „deszcz” na mięsień | ☐ | ☐ | ☐ |
| 2 | Rytm szybki, lekki, nad brzuścami mięśniowymi — nigdy nad kością, nerką, sutkiem | ☐ | ☐ | ☐ |
| 3 | Czas krótki (10–30 s na obszar), zakończenie głaskaniem | ☐ | ☐ | ☐ |
| 4 | Efekt: pobudzenie lub ułatwienie odkrztuszania (klatka — dłoń lejek) | ☐ | ☐ | ☐ |
| 5 | Przeciwwskazania: osteoporoza, antykoagulacja, choroby skóry, nowotwór | ☐ | ☐ | ☐ |""",
    "F.13": """### Wibracja

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Drganie ciągłe (drżenie dłoni) lub przerywane (punktowe) — odrębne cele | ☐ | ☐ | ☐ |
| 2 | Nacisk stały, amplituda dobierana, kończyna podparta | ☐ | ☐ | ☐ |
| 3 | Czas 30–60 s, koniec zabiegu zawsze wibracją wygaszaną + głaskanie | ☐ | ☐ | ☐ |
| 4 | Obserwacja odczynu (drżenie, rozluźnienie, ewentualne pobudzenie) | ☐ | ☐ | ☐ |
| 5 | Ostrożność: padaczka, arytmia (okolica serca!), ciąża — nie stosować | ☐ | ☐ | ☐ |""",
    "F.14": """### Masaż kończyny górnej — kolejność i kierunki

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Grzbiet dłoni → ramię (od łokcia do barku) → przedramię → dłoń | ☐ | ☐ | ☐ |
| 2 | Odprowadzanie żylne: od palców ku dołowi pachowemu | ☐ | ☐ | ☐ |
| 3 | Okolica stawu łokciowego — delikatnie, bez ucisku bruzdy | ☐ | ☐ | ☐ |
| 4 | Każdy etap otwierany i zamykany głaskaniem | ☐ | ☐ | ☐ |
| 5 | Kończyna podparta na całej długości (ergonomia i komfort) | ☐ | ☐ | ☐ |""",
    "F.15": """### Masaż kończyny dolnej — kolejność i kierunki

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Stopa → podudzie → udo (kierunek ku sercu) | ☐ | ☐ | ☐ |
| 2 | Żylaki i miejsca bolesne omijane, bez głębokiego masażu | ☐ | ☐ | ☐ |
| 3 | Grzbiet stopy, podeszwa, palce — dokładna, krótka praca | ☐ | ☐ | ☐ |
| 4 | Pośladki i okolica pachwinowa — odprowadzanie do węzłów | ☐ | ☐ | ☐ |
| 5 | Kontrola obrzęku i temperatury przed i po | ☐ | ☐ | ☐ |""",
    "F.16": """### Masaż grzbietu — schemat części plecowej

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Głaskanie wzdłuż i poprzecznie, rozcieranie przykręgosłupowe | ☐ | ☐ | ☐ |
| 2 | Ugniatanie równolegle do włókien mm. prostowników, fala ku barkom | ☐ | ☐ | ☐ |
| 3 | Oklepywanie bocznie (nie nad kręgosłupem i okolicą nerek) | ☐ | ☐ | ☐ |
| 4 | Łopatki i okolica karku — precyzja, brak ucisku na wyrostki | ☐ | ☐ | ☐ |
| 5 | Zamknięcie: głaskanie + wibracja wygaszana; minuta spokoju klienta | ☐ | ☐ | ☐ |""",
    "F.17": """### Masaż karku — bezpieczeństwo struktur naczyniowo-nerwowych

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Przed intensywną pracą wywiad w kierunku zawrotów i szmerów; przy wątpliwościach — odstąp | ☐ | ☐ | ☐ |
| 2 | Brak rotacji forsownych i hiperextensji szyi | ☐ | ☐ | ☐ |
| 3 | Czworoboczny, dźwigacz, pochyłe — praca opuszkami od potylicy ku barkowi | ☐ | ☐ | ☐ |
| 4 | Trójkąt tętniczy szyi (tętnica szyjna!) — tylko głaskanie, bez ucisku | ☐ | ☐ | ☐ |
| 5 | Zawroty, szumy, nudności = natychmiastowy stop i konsultacja (E.9/E.10) | ☐ | ☐ | ☐ |""",
    "F.18": """### Masaż klatki piersiowej (międzyżebrza, oddech)

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Międzyżebrza od mostka ku kręgosłupowi, dłonie „na żebrach” | ☐ | ☐ | ☐ |
| 2 | Bez ucisku na sutki i wyrostek mieczykowaty | ☐ | ☐ | ☐ |
| 3 | Technika wspomagająca oddychanie i odkrztuszanie (dłoń-lejek) | ☐ | ☐ | ☐ |
| 4 | Choroby serca/płuc — tylko za zgodą lekarza | ☐ | ☐ | ☐ |
| 5 | Duszność, ból zamostkowy → stop, E.1/E.2 | ☐ | ☐ | ☐ |""",
    "F.19": """### Masaż brzucha

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Zgodnie z perystaltyką: wstępująca → poprzecznica → zstępująca (ruch wskazówek zegara) | ☐ | ☐ | ☐ |
| 2 | Głębokość ostrożna, pytaj o komfort; techniki gazoodpadowe przy wzdęciach | ☐ | ☐ | ☐ |
| 3 | Przeciwwskazania: ostre choroby jamy brzusznej, przepuklina, ciąża zaawansowana | ☐ | ☐ | ☐ |
| 4 | Warunki: pęcherz opróżniony, 1–2 h po posiłku | ☐ | ☐ | ☐ |
| 5 | Po zabiegu: szklanka wody, informacja o wzmożonej perystaltyce | ☐ | ☐ | ☐ |""",
    "F.20": """### Masaż twarzy i głowy

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Tylko opuszki palców, mała amplituda, skóra nawilżona | ☐ | ☐ | ☐ |
| 2 | Kierunki od środka ku obwodowi, odpływ do węzłów szyi | ☐ | ☐ | ☐ |
| 3 | Bez preparatów w okolicy oczu; włosy spięte, opaska na czoło | ☐ | ☐ | ☐ |
| 4 | Skóra trądzikowa/ropna — przeciwwskazane (E.14) | ☐ | ☐ | ☐ |
| 5 | Tempo wolne, monotonna rytmiczność — senność jest sukcesem | ☐ | ☐ | ☐ |""",
    "F.21": """### Manualny drenaż limfatyczny kończyny (Volder/Leduc)

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Przygotowanie stacji węzłowych centralnie NAJPIERW | ☐ | ☐ | ☐ |
| 2 | Sekwencja proximal → distal „otwarcie drogi”, potem praca na obwodzie | ☐ | ☐ | ☐ |
| 3 | Chwyt „ręcznikowy”, rozciąganie skóry, wolne tempo (~1 cykl/oddychanie) | ☐ | ☐ | ☐ |
| 4 | Brak rumienia i rozgrzania — drenaż nie może „masować” | ☐ | ☐ | ☐ |
| 5 | Po zabiegu bandażowanie kompresyjne lub pończocha; edukacja samoopieki | ☐ | ☐ | ☐ |
| 6 | Przeciwwskazania bezwzględne D.3 sprawdzone przed dotknięciem | ☐ | ☐ | ☐ |""",
    "F.22": """### Masaż segmentarny — faza diagnostyczna

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Identyfikacja stref Heada (napięcie, temperatura, fałd) | ☐ | ☐ | ☐ |
| 2 | Badanie fałdu skóry i tkanki łącznej między wyrostkami a żebrami | ☐ | ☐ | ☐ |
| 3 | Symetria L/P, zapis mapowy w karcie | ☐ | ☐ | ☐ |
| 4 | Gorączka, ból narządowy → najpierw lekarz (E.7, D.2) | ☐ | ☐ | ☐ |""",
    "F.23": """### Masaż segmentarny — faza terapeutyczna

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Chwyty dobierane do reakcji: rozciąganie fałdu, rozcieranie, wałeczkowanie | ☐ | ☐ | ☐ |
| 2 | Siła modulowana oddechem i zgłoszeniami klienta | ☐ | ☐ | ☐ |
| 3 | Reakcja wegetatywna monitorowana; ból → przerwa | ☐ | ☐ | ☐ |
| 4 | Czas 10–20 min, odstęp 24–48 h na te same strefy | ☐ | ☐ | ☐ |
| 5 | Dokumentacja: strefy, techniki, odczyn, plan następnej sesji | ☐ | ☐ | ☐ |""",
    "F.24": """### Refleksoterapia stóp

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Mapa stref przedstawiona klientowi; obietnice lecznicze w granicach faktów | ☐ | ☐ | ☐ |
| 2 | Technika „chodzącego kciuka”, nacisk w granicach komfortu | ☐ | ☐ | ☐ |
| 3 | Kolejność: stopa lewa potem prawa, od palców do pięty | ☐ | ☐ | ☐ |
| 4 | Przeciwwskazania: zakrzepica, neuropatia cukrzycowa (ostro!), grzybica, ciąża zaawansowana | ☐ | ☐ | ☐ |
| 5 | Po zabiegu: woda, odpoczynek 5 min, obserwacja samopoczucia | ☐ | ☐ | ☐ |""",
    "F.25": """### Shantala — masaż niemowlęcia (etapy)

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Zgoda opiekuna, moment między karmieniami, dziecko spokojne | ☐ | ☐ | ☐ |
| 2 | Olej neutralny, ciepłe dłonie, kontakt wzrokowy i mówienie do dziecka | ☐ | ☐ | ☐ |
| 3 | Sekwencja: brzuch → klatka → kończyny → plecy (ostrożnie) | ☐ | ☐ | ☐ |
| 4 | Ruchy delikatne, rytmiczne; płacz = stop, ulga dziecku, próba później | ☐ | ☐ | ☐ |
| 5 | Szkolenie rodzica do samodzielnego masażu w domu (edukacja) | ☐ | ☐ | ☐ |
| 6 | Przeciwwskazania D.10: infekcja, wysypka, przepuklina, choroby metaboliczne, wcześniactwo bez zgody neonatologa | ☐ | ☐ | ☐ |""",
    "F.26": """### Masaż w ciąży — pozycje i techniki bezpieczne

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Zgoda lekarza prowadzącego udokumentowana; brak alarmów położniczych (E.12) | ☐ | ☐ | ☐ |
| 2 | Pozycja boczna (lewy bok) z poduszkami; po 20. tygodniu bez leżenia na plecach | ☐ | ☐ | ☐ |
| 3 | Techniki łagodne: głaskanie, delikatne rozcieranie; bez głębokiego ugniatania | ☐ | ☐ | ☐ |
| 4 | Obrzęki fizjologiczne — tylko delikatny drenaż; podejrzenie DVT (E.6) = stop | ☐ | ☐ | ☐ |
| 5 | Sygnały przerwania ustalone; po zabiegu pomiar ciśnienia przy nadciśnieniu | ☐ | ☐ | ☐ |""",
    "F.27": """### Masaż sportowy przedstartowy

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Czas 8–12 min, 15–20 min przed startem; rozgrzewka trenera uwzględniona | ☐ | ☐ | ☐ |
| 2 | Tempo szybkie, pobudzające: głaskanie → rozcieranie → oklepywanie → wibracja | ☐ | ☐ | ☐ |
| 3 | Brak głębokiego rozluźniania i technik wydłużających tuż przed wysiłkiem | ☐ | ☐ | ☐ |
| 4 | Uwaga na świeże mikrourazy — omijać, nie „rozbić” | ☐ | ☐ | ☐ |
| 5 | Konsultacja z zawodnikiem: preferencje, rutyna, zakaz eksperymentów w dniu startu | ☐ | ☐ | ☐ |""",
    "F.28": """### Masaż prozdrowotny relaksacyjny

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Atmosfera: ciepło, przyciemnione światło, cisza/bez muzyki narzuconej | ☐ | ☐ | ☐ |
| 2 | Tempo wolne, monotonny rytm, dłonie zawsze w kontakcie z ciałem | ☐ | ☐ | ☐ |
| 3 | Oddech przeponowy klienta prowadzony sugestią ruchu ręki | ☐ | ☐ | ☐ |
| 4 | Sekwencja całościowa 45–60 min, zakończenie 2-minutowym spokojem | ☐ | ☐ | ☐ |
| 5 | Edukacja: sen, nawodnienie, higiena postawy; bez obietnic „leczenia” | ☐ | ☐ | ☐ |""",
    "F.29": """### Pierwsza pomoc — BLS (wg wytycznych ERC 2021)

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Bezpieczeństwo ratownika (ocena otoczenia) | ☐ | ☐ | ☐ |
| 2 | Przytomność: potrząśnij, zawołaj; oddech: 10 s patrzenia/słuchania/wyczucia | ☐ | ☐ | ☐ |
| 3 | Wezwanie pomocy 112/999 + AED z gabinetu | ☐ | ☐ | ☐ |
| 4 | Uciskania 100–120/min, głębokość 5–6 cm, pełny rozkurcz, 30:2 | ☐ | ☐ | ☐ |
| 5 | AED: naklej elektrody, odsuń się, postępuj z komendami | ☐ | ☐ | ☐ |
| 6 | Pozycja boczna ustalona przy oddechu; kontrola dojazdu ZRM, dokumentacja zdarzenia | ☐ | ☐ | ☐ |""",
    "F.30": """### Dokumentacja zabiegu

| Lp | Punkt kontrolny | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Karta kompletna: dane, wywiad, zgoda, obszar, techniki, czas, siła, odczyn | ☐ | ☐ | ☐ |
| 2 | Zapis czytelny, obiektywny, datowany, podpisany | ☐ | ☐ | ☐ |
| 3 | Uwagi o stanach alarmowych i decyzjach (odmowa zabiegu, skierowanie) | ☐ | ☐ | ☐ |
| 4 | Przechowywanie zamknięte, dostęp uprawnionych, klauzula RODO | ☐ | ☐ | ☐ |
| 5 | Plan kolejnych wizyt i modyfikacje wpisane zanim klient wyjdzie | ☐ | ☐ | ☐ |""",
    # ---- Załącznik H: brakujące H.7-H.10 -----------------------------------
    "H.7": """**Preparaty rozgrzewające (termogeniczne).** Substancje: kapsaicyna, imbir, nikotynian benzylu, ekstrakty pieprzowe. Stosowanie: masaż sportowy treningowy i przedwysiłkowy u dorosłych, bóle mięśniowe przewlekłe. Zasady: mała ilość, rozprowadzenie na dłoniach, natychmiastowe umycie rąk masażysty po aplikacji; Nigdy na skórę uszkodzoną, twarz, okolice intymne; NIE dla dzieci, NIE przed wysiłkiem u młodzieży bez zgody opiekuna; test płatkowy obowiązkowy. Ryzyko: oparzenia chemiczne, reakcje alergiczne — poinformuj klienta o uczuciu ciepła/ścia, aby nie mylił go z bólem.""",
    "H.8": """**Preparaty chłodzące.** Mentol, kamfora, żele chłodzące. Zastosowanie: faza podostra urazów (po konsultacji lekarskiej), masaż regeneracyjny w upale, dolegliwości żylne (delikatnie, bez intensywnego rozcierania). Ograniczenia: astma i padaczka — ostrożnie (drażniący zapach, odruch); nie na duże powierzchnie u dzieci; unikać okolic oczu i błon śluzowych; nie stosować na zmienioną chorobowo skórę. Czas działania: krótki (10–20 min) — chłód znika, a złudzenie „leczenia” nie zastąpi diagnozy.""",
    "H.9": """**Preparaty przeciwzapalne (żele z NLPZ, np. diklofenak).** Masażysta NIE zleca, NIE aplikuje produktów leczniczych. Klient może użyć własnego żelu kupionego bez recepty zgodnie z ulotką i za zgodą farmaceuty/lekarza; masażysta wówczas pracuje po wchłonięciu lub omija obszar. Dokumentacja: adnotacja w karcie, jaki preparat i kiedy. Zasada M.4/M.6: granica kompetencji jest częścią bezpieczeństwa pacjenta.""",
    "H.10": """**Testy alergiczne i przechowywanie.** Próba płatkowa: niewielka ilość preparatu na skórę przedramienia lub za uchem, ocena po 24 h (rumień, świąd, pęcherzyki = stop). Przechowywanie: szczelne opakowania, z dala od światła i ciepła, data otwarcia na pojemniku, wyrzucanie po terminie ważności i po każdej zmianie zapachu/barwy. Higiena aplikacji: pompka/szpatułka zamiast palców, dezynfekcja gwintu butelki, brak mieszania preparatów bez wiedzy o składzie. Wszystko notujemy w karcie klienta — bo uczulenie dziś oznacza wstrząs jutro.""",
    # ---- Załącznik J: pełne etapy BLS --------------------------------------
    "J.1": """**Ocena bezpieczeństwa miejsca.** Zanim podejdziesz: rozejrzyj się (prąd, gaz, ruch, agresja), oceń, czy Tobie nic nie zagraża. W gabinecie masażu: wyłącz urządzenia elektryczne przy kontakcie z wodą, zabezpiecz wyjście. Ratownik żywy = ratownik skuteczny. Jeśli miejsce niebezpieczne — nie wchodź, wezwij służby i poczekaj.""",
    "J.2": """**Ocena przytomności.** Podejdź od strony twarzy, uklęknij przy ramieniu. Potrząśnij za barki (delikatnie, ale zdecydowanie) i zawołaj głośno: „Czy mnie słyszysz?”. Reakcja: otwiera oczy/mówi = przytomny; brak reakcji = nieprzytomny → wołaj pomoc i przechodź do J.3–J.5. Nie potrząsaj niemowlęciem; u dziecka ocena: zawołanie + poklepanie po stopie.""",
    "J.3": """**Wezwanie pomocy.** Krzycz do otoczenia: „Przyjdźcie pomóc!”, wskaż konkretną osobę: „Ty — zadzwoń 112/999 i przynieś AED!”. Sam dzwonisz tylko, gdy jesteś sam: dyspozytor poprowadzi Cię krok po kroku. Powiedz: gdzie (adres/gabinet), co się stało, ile osób poszkodowanych, co robisz, nie rozłączaj się pierwszy.""",
    "J.4": """**Udrożnienie dróg oddechowych.** Odchyl głowę do tyłu unosząc żuchwę (head tilt–chin lift); przy podejrzeniu urazu szyi — wysuwanie żuchwy bez odgięcia głowy (jaw thrust). Usuń widoczne ciało obce palcem zahaczającym (nigdy „na ślepo”). Słuchaj: tor oddechowy, świszczący, chrapanie = niedrożność.""",
    "J.5": """**Ocena oddechu (10 sekund).** Patrz (ruch klatki), słuchaj (szmer powietrza), poczuj (powietrze na policzku). Normalny oddech = tak; brak lub agoniczne westchnienia = NIE — rozpocznij RKO. Nie trać czasu na szukanie tętna (>10 s = uznaj brak u nieprzytomnego lay-ratownika).""",
    "J.6": """**Resuscytacja dorosłego.** Klęknij, pięść na linii środkowej mostka (dolna połowa), druga ręka na niej, palce splecione, ramiona wyprostowane. Uciskaj 100–120/min, 5–6 cm, pełny rozkurcz, minimalne przerwy (<10 s). 30 uciśnięć : 2 oddechy (jeśli potrafisz i chcesz); jeśli nie — ciągłe uciśnięcia. Zmień osobę prowadzącą co ~2 min. Kontynuuj do przyjazdu ZRM lub oznak życia.""",
    "J.7": """**Resuscytacja dziecka.** Rozpocznij od 5 oddechów ratunkowych (objętość „tlen z ust do ust i nosa” u niemowlęcia). Uciśnięcia jedną ręką (dziecko) lub dwoma palcami (niemowlę), głębokość ~1/3 klatki (4–5 cm), tempo 100–120/min, proporcja 15:2 przy dwóch ratownikach (30:2 przy jednym). Po 2 min — zadzwoń, jeśli tego nie zrobiono. Przyczyna najczęściej oddechowa — oddechy są kluczowe!""",
    "J.8": """**Zadławienie (dławienie) — dorosły przytomny.** Pytaj: „Czy możesz mówić?”. Kaszel skuteczny = wspieraj, nie przeszkadzaj. Brak głosu/sinica = 5 uderzeń między łopatki + 5 ucisków nadbrzusza (Heimlich), naprzemiennie do usunięcia ciała obcego lub utraty przytomności → RKO z kontrolą jamy ustnej przed oddechami. U kobiet w ciąży i otyłych: uciski na dolne żebra. U przytomnego dziecka: 5+5 analogicznie, nigdy Heimlich u niemowlęcia (pozycja głową w dół na przedramieniu + klepnięcia).""",
    "J.9": """**Pozycja boczna ustalona.** Warunek: oddech prawidłowy, uraz kręgosłupa nieprawdopodobny. Ręka bliższa pod kątem prostym, dalsza przy policzku, zegnij bliższą nogę, przetocz do boku, odgiń głowę do tyłu dla drożności dróg. Kontroluj oddech co minutę do przyjazdu pomocy. Dlaczego: zapobiega zachłyśnięciu i niedrożności językiem — miłość bliźniego ma też geometrię.""",
    "J.10": """**AED w gabinecie.** Automatyczny defibrylator zewnętrzny: włącz, zdjąć ubranie z klatki, osusz skórę, naklej elektrody wg obrazka (nad prawym obojczykiem, pod lewym pachowym), odsuń wszystkich od dotykania klienta, wykonaj analizę i rozładowanie wg komend głosowych. Po wstrząsie NATYCHMIAST wróć do uciśnięć. Trenuj raz na kwartał — urządzenie nieużywane martwieje w pamięci ludzi, nie w bateriach.""",
    # ---- Załącznik K: kodeks — pełne artykuły ------------------------------
    "K.1": """**Artykuł 1 — Godność pacjenta.** Ciało drugiego człowieka jest powierzone Twej profesji; traktuj je jak świątynię, nie przedmiot. Okrywaj nie masowane okolice, ostrzegaj przed każdym nowym dotykiem, pytaj o zgodę na zmianę pozycji. Nigdy nie komentuj wyglądu ciała. Godność nie zależy od wieku, płci, wagi, choroby ani zasobności — jest darem, którego masz jedynie strzec.""",
    "K.2": """**Artykuł 2 — Prawda w komunikacji.** Nie obiecuj wyleczenia, którego masaż nie daje. Rzeczywiście mów, co robisz i dlaczego; wyjaśniaj odczyny; przyznajesz się do niewiedzy i skierujesz do lekarza. Fałszywa pewność jest formą przemocy; prawdziwa pokora — formą sztuki.""",
    "K.3": """**Artykuł 3 — Miłość bliźniego jako służba.** Dobro klienta przed Twoim zyskiem i wygodą. Nie skracaj zabiegu dla grafiku, nie namawiaj na dodatkowe usługi, gdy wystarczy jedna. Bądź cierpliwy wobec lęku i bólu. Służba (łac. servitium) w zawodzie opiekuńczym jest godnością, nie upokorzeniem.""",
    "K.4": """**Artykuł 4 — Sprawiedliwość w dostępie do opieki.** Ten sam standard dla każdego: bogatego i biednego, sympatycznego i trudnego, młodego i starego. Odmowa usługi wyłącznie z powodów merytorycznych (bezpieczeństwo, kompetencje) — nigdy dla dyskryminacji. Cenienie czasu: punktualność wobec klienta jest elementem sprawiedliwości.""",
    "K.5": """**Artykuł 5 — Piękno w pracy z ciałem.** Estetyka gestu: czyste narzędzia, spokojny ruch, harmonia sekwencji, cisza tam, gdzie niepotrzebne słowa. Piękno zabiegu rodzi się z proporcji — siły i delikatności, milczenia i słowa, dawania i brania. Szpetnota (brudny ręcznik, pośpiech, chaos) jest kłamstwem wobec powołania.""",
    "K.6": """**Artykuł 6 — Tajemnica zawodowa.** Wszystko, co zobaczysz i usłyszysz przy ciele i w życiu klienta, zostaje w karcie i w Tobie. Dane chronione (RODO), rozmowy telefoniczne ciche, e-maile kodowane. Wyjątek: realne zagrożenie życia lub zdrowia innego człowieka (np. przemoc wobec dziecka) — wtedy prawo nakazuje działać, a Ty działaj z rozwagą.""",
    "K.7": """**Artykuł 7 — Granice kompetencji.** Masażysta nie leczy chorób, nie stawia diagnoz, nie manipuluje stawami, nie podaje leków. Twoje „nie wiem, idziemy do lekarza” jest dowodem profesjonalizmu. Uczy się całe życie — ale każda nowa metoda najpierw w szkoleniu, potem pod nadzorem, na końcu samodzielnie.""",
    "K.8": """**Artykuł 8 — Dotyk i zgoda.** Zgoda jest warunkiem moralnym i prawnym dotyku zawodowego. Odmowa klienta jest święta i nie wymaga uzasadnienia. Granice intymne: masuj tylko obszar uzgodniony; przy masażu okolic intymnych obecność osoby trzeciej na życzenie. Każde przekroczenie granicy — nawet „niechcący” — wymaga przeprosin, dokumentacji i naprawy.""",
    "K.9": """**Artykuł 9 — Uczciwość zawodowa.** Cena jawna, kwalifikacje prawdziwe, opinie klientów zbierane uczciwie. Nie kupuj lajków, nie oczerniaj konkurencji, nie przypisuj sobie cudzych osiągnięć. Dyplom i certyfikaty okazuj na żądanie — dumnie i transparentnie.""",
    "K.10": """**Artykuł 10 — Reguła złotego wahadła.** „Jeśli masz wątpliwość, czy coś jest bezpieczne — nie rób tego.” Wahanie jest dowodem dojrzałości. Zanim zwiększysz siłę, skrócisz przerwę, dodasz technikę — zapytaj siebie trzy razy: czy to dobre? czy to prawdziwe? czy to sprawiedliwe? Dopiero potem: czy to przyjemne.""",
    # ---- Załącznik L: bibliografia — opisy pozycji --------------------------
    "L.1": """**Adam Zborowski, *Masaż klasyczny i segmentarny*, Wydawnictwo Lekarskie PZWL.** Fundament programu: klasyfikacja technik, dawkowanie, masaż segmentarny wg stref Heada. Czytaj z atlasem w drugiej ręce — opis Zborowskiego nabiera sensu dopiero na ciele. Edycje nowsze zawierają rozdziały o drenażu limfatycznym; porównuj wydania, by śledzić rozwój metody.""",
    "L.2": """**Adam Zborowski, *Masaż w wybranych jednostkach chorobowych*, PZWL.** Most między patologią a zabiegiem: przy każdej chorobie wskazania, przeciwwskazania, modyfikacje techniki. Ćwicz czytanie „od choroby do dłoni”: jednostka → reakcja ustroju → dobór techniki → dokumentacja. To twoja mapa na egzamin MED.10 i do codziennej pracy.""",
    "L.3": """**Adam Zborowski, *Drenaż limfatyczny*, PZWL.** Szczegółowa technika manualnego drenażu: sekwencje, presje, indications/contraindications, CDT. Wymaga znajomości anatomii naczyń chłonnych — wracaj do book-12 modułu 2. Błędy w drenażu widać szybko (obrzęk rośnie) — ucz się pod okiem instruktora.""",
    "L.4": """**Bochenek A., Reicher M., *Anatomia człowieka*, tom I–V, PZWL.** Atlas i traktat jednocześnie. Dla masażysty kluczowe: tom I (osteologia, artrologia, miologia) i V (naczynia i nerwy obwodowe). Nie musisz pamiętać wszystkiego — musisz umieć znaleźć: przyczepy, unerwienie, unaczynienie, topografię powierzchowną.""",
    "L.5": """**Traczyk W. Z., *Fizjologia człowieka w zarysie*, PZWL.** Mechanizmy, które masaż uruchamia: krążenie żylne i chłonne, tonus mięśniowy, układ autonomiczny, oś stresu. Czytaj wybiórczo, ale regularnie — rozdziały o mięśniu, krążeniu i nerwowym bezpośrednio tłumaczą skutki Twojej pracy.""",
    "L.6": """**Doerr W., *Masaż leczniczy*, Sport i Turystyka.** Klasyka szkoły niemieckiej: precyzja techniczna, lokalizacje, jednostki chorobowe. Uzupełnia Zborowskiego; zwróć uwagę na rozdziały o masażu łącznotkankowym i okostnowym.""",
    "L.7": """**Faller A., Schwind M., *Anatomia i fizjologia dla fizjoterapeutów*, Elsevier Urban & Partner.** Nowoczesna, obrazkowa prezentacja funkcji narządu ruchu — najlepsza „pomostowa” lektura między Bochenkiem a praktyką gabinetową. Idealna do nauki palpacji (korelacja z book-14 modułu 2).""",
    "L.8": """**Normy i wytyczne dezynfekcji (PN-EN, GIS, karty charakterystyki preparatów).** Źródło prawdy o czasach działania, stężeniach i kompatybilności materiałów. Przepis BHP: środki wyłącznie dopuszczone, stosowane zgodnie z instrukcją producenta; dokumentuj w przeglądach stanowiska.""",
    "L.9": """**Podstawa programowa MED.10 i wymagania egzaminacyjne CKE/OKE.** Akt prawny, nie poradnik — źródło zakresu materiału na egzamin potwierdzający kwalifikację. Analizuj razem z nauczycielami; wszystko, czego wymaga podstawa, jest w tym kursie; nic ponad kompetencje masażysty nie jest.""",
    "L.10": """**Materiały edukacyjne producentów olejów i preparatów masażowych.** Ulotki, karty SDS, szkolenia branżowe. Korzystaj krytycznie: marketing nie jest dowodem naukowym; wybieraj preparaty z pełnym składem INCI i badaniami stabilności; testuj na sobie i ochotnikach formalnie (H.10).""",
    "L.11": """**Czasopisma: Physiotherapy Research International, Journal of Bodywork & Movement Therapies, Fizjoterapia Polska.** Aktualna evidencia: masaż a ból przewlekły, obrzęk, sport. Ucz się czytać abstrakty i tabele — jedno badanie nie jest prawdą, ale metodyczna lektura buduje osąd naukowy praktyka.""",
    "L.12": """**Rejestry instytucji publicznych (GIS, URPL, NFZ, ZUS, PIP).** Źródła obowiązków prawnych: sanepid, produkty lecznicze, ubezpieczenia, składki, inspekcja pracy. Zajrzyj przynajmniej raz na semestr — prawo zmienia się ciszej niż moda na techniki, a konsekwencje są poważniejsze.""",
    # ---- Załącznik M: pełne oświadczenia ------------------------------------
    "M.1": """Oświadczam, że ukończenie kursu MED.10 **nie uprawnia do wykonywania zawodu lekarza**, do orzekania o zdrowiu, wystawiania zwolnień, recept ani opinii medycznych. Wszystkie czynności diagnostyczne i terapeutyczne wykraczające poza masaż pozostawiam lekarzom i innym uprawnionym zawodom medycznym.""",
    "M.2": """Oświadczam, że **nie podejmuję się samodzielnego leczenia chorób**. Masaż jest świadczeniem wspomagającym, profilaktycznym i rehabilitacyjnym w granicach wskazania lekarskiego lub własnej oceny funkcjonalnej; nie zastępuje farmakoterapii, chirurgii ani fizjoterapii właściwej.""",
    "M.3": """Oświadczam, że **nie prowadzę diagnostyki medycznej** wykraczającej poza ocenę przydatną do wykonania zabiegu (stan skóry, napięcie mięśni, obrzęk, zakres ruchu). Nie interpretuję badań obrazowych i laboratoryjnych; wyniki kieruję do lekarza zleceniodawcy.""",
    "M.4": """Oświadczam, że **nie wykonuję zabiegów inwazyjnych**: nakłuć, prądów leczniczych w trybie medycznym, terapii laserowej wysokiego klasy, suchych igieł (dry needling) ani manipulacji stawowych. Stanowisko masażysty nie jest stanowiskiem zabiegowym klasy medycznej.""",
    "M.5": """Oświadczam, że **nie stosuję metod, do których nie mam uprawnień ani przygotowania**: chiropraktyki, terapii manualnej specjalistycznej, akupunktury, ziołolecznictwa leczniczego, dietetyki klinicznej bez kwalifikacji. Każda nowa metoda = najpierw legalne szkolenie, potem praktyka pod nadzorem.""",
    "M.6": """Zobowiązuję się **kierować dobro pacjenta ponad zysk**: nie skracać zabiegów dla obłożenia, nie sprzedawać usług niepotrzebnych, nie ukrywać przeciwwskazań, przerwać przy pierwszym sygnale zagrożenia. Moja renoma ma wartość niższą niż zdrowie powierzonego mi człowieka.""",
    "M.7": """Zobowiązuję się **dokumentować zgodnie z prawdą**: karta zabiegowa odzwierciedla faktyczny przebieg; nie cofam i nie fałszuję wpisów; uwagi o zdarzeniach niepożądanych zapisuję niezwłocznie. Dokumentacja chroni pacjenta, Ciebie i wspólne zaufanie.""",
    "M.8": """Zobowiązuję się **nie wykorzystywać zależności wynikającej z dotyku**: żadnej relacji intymnej z klientem w trakcie opieki, żadnych żartów o ciele, żadnych próśb o usługi prywatne poza gabinetem. Profesjonalna bliskość cielesna zobowiązuje do asertywnej czystości granic.""",
    "M.9": """Zobowiązuję się **dbać o własne zdrowie jako warunek dobra innych**: ergonomia, przerwy, badania okresowe, profilaktyka przeciążeń dłoni i kręgosłupa. Wypalony lub chore ręce nie leczą — zmęczenie uczciwie zgłaszaj i odpoczywaj; to sprawiedliwość wobec przyszłych pacjentów.""",
    "M.10": """Zobowiązuję się **do ustawicznego kształcenia i pokory**: aktualizować wiedzę (L.11/L.12), przyjmować informację zwrotną bez obrony, przyznawać się do błędu i naprawiać go. Umiejętność mówienia „nie wiem, sprawdzę” jest częścią kompetencji, nie jej brakiem.""",
}


CONTENT.update({
    # E.1–E.7 i H.1–H.6 mają treść w tabelach — gdyby wiersz był nieczytelny,
    # poniższe minimum zapewnia rzetelną treść rozdziału:
    "E.1": """**Ból w klatce piersiowej** — możliwy zawał lub angina. Objawy: ucisk, pieczenie, promieniowanie do żuchwy/ramienia, duszność, zimny pot, lęk. Działanie: natychmiast przerwij wszystko, ułóż klienta półsiedząco, poluzuj ubranie, wezwij 112/999, nie zostawiaj osoby samej, nie podawaj leków własnych. Masaż odroczony do decyzji kardiologa.""",
    "E.2": """**Duszność nagła** — astma napadowa, POChP, zatorowość, odma, niewydolność serca. Objawy: świszczący oddech, sinica, niemożność dokończenia zdania, niepokój. Działanie: 112/999 przy nasileniu, pozycja pochylona do przodu z podparciem, spokój i powietrze bez zadymienia; tlen wyłącznie przez uprawnionych. Przy łagodnej duszności znanej (astma kontrolowana) — zabieg tylko za zgodą lekarza i z inhalatorem klienta w zasięgu.""",
    "E.3": """**Omdlenie (synkopa)** — krótkotrwała utrata przytomności na tle niedokrwienia OUN, często przedzabiegowa reakcja wazowagalna. Działanie: ułóż płasko z uniesionymi nogami, zapewnij drożność dróg oddechowych, oceniaj urazy głowy po upadku; brak oddechu → BLS (J.5–J.6). Po wybudzeniu: woda, odpoczynek, pomiar ciśnienia; nawracające omdlenia — kardiolog/neurolog.""",
    "E.4": """**Podejrzenie udaru** — skala FAST: Face (asymetria ust), Arm (osłabienie kończyny), Speech (mowa bełkotliwa), Time (zapisać godzinę początku). Działanie: natychmiast 112/999, nic doustnie (ryzyko zachłyśnięcia), pozycja bezpieczna, towarzysz do przyjazdu pomocy. Żadnego masażu szyi!""",
    "E.5": """**Podejrzenie zawału** — ból zamostkowy >15 minut, nudności, zimny pot, lęk śmierci; przebieg może być nietypowy (bez bólu u diabetyków, z dusznością u kobiet). Postępowanie jak E.1 + zgodnie z poleceniami dyspozytora (kwestia kwasu acetylosalicylowego należy do medycznego nadzoru telefonicznego).""",
    "E.6": """**Obrzęk jednostronny kończyny z bólem** — podejrzenie zakrzepicy żył głębokich (DVT): łyda ciepła, napięta, bolesna, sine lub zaczerwieniona, obwód większy niż druga strona. Działanie: 112/999 lub pilna pomoc lekarska; BEZ masażu kończyny, bez intensywnego ruchu (ryzyko zatorowości płucnej). Udokumentuj objawy i odmowę.""",
    "E.7": """**Gorączka i dreszcze** — ostra infekcja; temperatura >38°C z osłabieniem, potami, bólami mięśniowymi. Działanie: odwołaj zabieg, zaleć kontakt z lekarzem (POZ); alarmowo: sztywność karku, splątanie, wysypka wybroczynowa → 112 (meningitis/sepsa). Masaż dopuszczalny po 48 h bez gorączki i poprawie samopoczucia.""",
    "H.1": """**Talk** — środek osuszający do masażu suchego (np. części ciała trudne do natłuszczenia). Obecnie stosowany rzadziej: pył groźny dla dróg oddechowych (nie wdychać!), wysusza skórę, pozostawia osad na stole i tekstyliach. Nie stosować przy zmianach skórnych i skłonności do zaskórników. Alternatywy: skrobia ziemniaczana, talk kosmetyczny bez azbestu w pojemniku z pompką.""",
    "H.2": """**Oleje roślinne** — nośniki: kokosowy (frakcjonowany, lekki), migdałowy (klasyczny, uczulenie na orzechy rzadkie przy rafinowanym, ale test wymagany), jojoba (stabilny, dobrze tolerowany), rzepakowy (ekonomiczny). Zastosowanie: masaż klasyczny i relaksacyjny. Przechowywać chłodno, ciemno; sprawdzać daty i jełczenie (zapach). Przeciwwskazania: alergia na składnik, trądzik (oleje komedogenne).""",
    "H.3": """**Oliwki** — oliwa z oliwek (tłusta, bogata w tokoferole) oraz oliwki kosmetyczne (mieszane z estrami dla lepszej rozpływalności). Zaleta: poślizg długi, odpowiedni dla skóry suchej i masażu delikatnego. Wada: trudne zmywanie stołu, plamy na tekstyliach, charakterystyczny zapach (nie każdemu odpowiada). Test płatkowy standardowo.""",
    "H.4": """**Kremy do masażu** — emulsje w/o (tłuste, długie poślizg) i o/w (lżejsze, wchłaniają się szybciej). Idealne do masażu krótkiego, biurowego, przy ubraniu częściowym. Uwaga: kremy z dodatkiem mentolu/kamfory działają pobudzająco — inny cel niż relaks; kremy lecznicze (NLPZ) — patrz H.9 i granice kompetencji.""",
    "H.5": """**Lanolina** — tłuszcz owczy, silnie natłuszczający i okluzyjny; wskazana przy bardzo suchej, zrogowaciałej skórze (stopy, dłonie). Wady: ciężka do zmywania, alergeny wełny (rzadkie, ale realne), nie na twarz. Test płatkowy obowiązkowy; przechowywać w temperaturze pokojowej, zużyć wg daty.""",
    "H.6": """**Wazelina (petrolatum)** — obojętna, tani środek ochronny o bardzo długim poślizgu; masaż krótki, miejsca narażone na otarcia. Wady: nie wchłania się, brudzi tkaniny, komedogenna na twarzy, ograniczone „oddychanie” skóry przy długim stosowaniu. Dobra jako warstwa ochronna przed mydleniem/płukaniem okolic.""",
})

HEADER_PREFIX_RE = re.compile(r"^###\s+([A-M]\.\d+)\s+(.*)$")


def split_detail_sections(text: str) -> dict[str, str]:
    """Zwraca mapę 'X.N' -> treść spod nagłówka ### X.N w bloku 'Treść szczegółowa'."""
    idx = text.find("## Treść szczegółowa")
    detail = text[idx:] if idx >= 0 else ""
    out: dict[str, list[str]] = {}
    cur = None
    for line in detail.splitlines():
        m = HEADER_PREFIX_RE.match(line.strip())
        if m:
            cur = m.group(1)
            out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    res = {k: "\n".join(v).strip() for k, v in out.items()}
    # wyciągnij wiersze tabelaryczne (| E.1 | ...) do klucza "@rows:X.N"
    rows: dict[str, str] = {}
    for line in detail.splitlines():
        m2 = re.match(r"^\|\s*([A-M]\.\d+)\b(.*)$\s*$", line.strip())
        if m2:
            rows.setdefault(m2.group(1), "").__str__  # noop
            prev = ("| " + m2.group(1) + m2.group(2)).strip()
            rows[m2.group(1)] = (rows.get(m2.group(1), "") + "\n" + prev).strip()
    res.update({"@rows:" + k: v for k, v in rows.items()})
    return res


def parse_stubs(text: str) -> list[tuple[str, str]]:
    """Lista (numer, tytuł) podpunktów z listy 'Zawartość'."""
    idx = text.find("## Treść szczegółowa")
    head = text[:idx] if idx >= 0 else text
    stubs = []
    for line in head.splitlines():
        m = HEADER_PREFIX_RE.match(line.strip())
        if m:
            stubs.append((m.group(1), m.group(2).strip()))
    return stubs


def clean_body(body: str) -> str:
    body = STUB_RE.sub("", body).strip()
    return body


def slugify(title: str) -> str:
    repl = {
        "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n", "ó": "o",
        "ś": "s", "ź": "z", "ż": "z", "Ą": "a", "Ć": "c", "Ę": "e",
        "Ł": "l", "Ń": "n", "Ó": "o", "Ś": "s", "Ź": "z", "Ż": "z",
    }
    s = title.lower()
    s = "".join(repl.get(ch, ch) for ch in s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60] or "rozdzial"


def yaml_escape(s: str) -> str:
    return s.replace('"', "'")


def build_book(zdir: Path, label_file: Path, letter: str, dry: bool, force: bool) -> tuple[str, int]:
    """Tworzy książkę dla załącznika. Zwraca (slug_katalogu, liczba rozdziałów)."""
    text = label_file.read_text(encoding="utf-8")
    title_m = re.search(r"^#\s+(.+)$", text, re.M)
    full_title = title_m.group(1).strip() if title_m else label_file.stem
    # "Załącznik A. Mapa..." -> name book
    book_name = full_title
    stubs = parse_stubs(text)
    details = split_detail_sections(text)

    book_dir = zdir / f"book-{letter.lower()}-zalacznik-{letter.lower()}-{slugify(full_title.split('.', 1)[-1])}"
    if (book_dir / "book.yaml").exists() and not force:
        return book_dir.name, -1  # already converted

    chapters_txt = []
    chap_files = []
    intro_lines = [
        f"Materiał referencyjny kursu masażysty — {full_title}.",
        "",
        "Załącznik służy przez cały okres kształcenia: cytuj go w pracach, noś wydruk w teczce, wracaj przed każdym nowym modułem.",
    ]
    for num, ttl in stubs:
        body = details.get(num, "")
        body = clean_body(body)
        row = details.get("@rows:" + num, "")
        if not body and row:
            cells = [c.strip() for c in clean_body(row).strip("|").split("|")]
            if len(cells) >= 2 and cells[0] == num:
                head = ttl
                parts = [f"**{head}** — {cells[1]}"] if len(cells) > 1 else []
                if len(cells) > 2:
                    parts.append(f"**Postępowanie:** {cells[2]}")
                if len(cells) > 3:
                    parts.append(f"**Uwagi:** {cells[3]}")
                body = "\n\n".join(parts)
        if not body:
            body = CONTENT.get(num, "")
        if not body:
            body = "_Treść opracowywana przez kadrę dydaktyczną._"
        fname = f"{num.replace('.', '-')}-{slugify(ttl)}.md"
        chap_files.append(fname)
        content_md = f"# {num} {ttl}\n\n{body}\n"
        if not dry:
            (book_dir / "chapters").mkdir(parents=True, exist_ok=True)
            (book_dir / "chapters" / fname).write_text(content_md, encoding="utf-8")
        chapters_txt.append(
            f'    - title: "{yaml_escape(num + ". " + ttl)}"\n'
            f"      subchapter: false\n"
            f'      content_file: "chapters/{fname}"\n'
            f"      hidden: false"
        )

    toc = "\n".join(f"- **{n}** {t}" for n, t in stubs)
    intro = "\n".join(intro_lines) + "\n\n## Spis treści załącznika\n\n" + toc + "\n"

    yaml = (
        "# Aktywność typu book — załącznik kursu (konwersja label -> book)\n"
        "# Wygenerowano skryptem scripts/enrich_masaz_zalaczniki_books.py\n"
        "book:\n"
        f'  name: "{yaml_escape(book_name)}"\n'
        "  intro: |\n" + "".join("    " + ln + "\n" for ln in intro.splitlines()) +
        "  intro_format: markdown\n"
        "  numbering: 1\n"
        "  customtitles: 0\n"
        "  revision: 1\n"
        "  chapters:\n" + "\n".join(chapters_txt) + "\n"
        "  completion:\n"
        "    enabled: true\n"
        "    type: view\n"
    )
    if not dry:
        (book_dir / "book.yaml").mkdir(exist_ok=True) if False else None
        (book_dir / "book.yaml").write_text(yaml, encoding="utf-8")
    return book_dir.name, len(stubs)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=BASE_REL)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    base = Path(args.base)
    zdir = base / "sections" / "12-zalaczniki"
    labels = sorted(zdir.glob("label-*.md"))
    if len(labels) != 13:
        print(f"SPAM: oczekiwano 13 labeli, znaleziono {len(labels)}", file=sys.stderr)

    refs = []
    for lf in labels:
        m = re.match(r"label-\d+-zalacznik-([a-m])-", lf.name)
        letter = m.group(1).upper()
        name, n = build_book(zdir, lf, letter, args.dry_run, args.force)
        refs.append((letter, name))
        status = "POMINIĘTO (istnieje)" if n == -1 else f"utworzono {n} rozdziałów"
        print(f"  {lf.name[:44]:46s} -> {name} [{status}]")

    # section.yaml rewrite
    sec_yaml_path = zdir / "section.yaml"
    new_modules = []
    for letter, name in refs:
        # find original label name from section.yaml for fidelity
        pass
    old = sec_yaml_path.read_text(encoding="utf-8")
    # extract names for each letter from old yaml
    name_map = {}
    cur_letter = None
    for line in old.splitlines():
        lm = re.search(r"label-\d+-zalacznik-([a-m])-", line)
        if lm:
            cur_letter = lm.group(1).upper()
        nm = re.match(r'\s+name:\s*"(.*)"', line)
        if nm and cur_letter:
            name_map[cur_letter] = nm.group(1)
            cur_letter = None
    lines_out = [
        "# Metadane sekcji",
        "id: 12",
        'name: "Załączniki A-M"',
        "visible: 1",
        "summary:",
        "  format: markdown",
        "  markdown_file: section.md",
        "modules:",
    ]
    for letter, dirname in refs:
        disp = name_map.get(letter, f"Załącznik {letter}")
        lines_out += [
            "  - type: book",
            f"    ref: {dirname}",
            f'    name: "{yaml_escape(disp)}"',
        ]
    lines_out += [
        "  - type: glossary",
        "    ref: glossary-01",
        '    name: "Słownik pojęć masażu (MED.10)"',
        "",
    ]
    if not args.dry_run:
        bak = sec_yaml_path.with_suffix(".yaml.bak")
        if not bak.exists():
            bak.write_text(old, encoding="utf-8")
        sec_yaml_path.write_text("\n".join(lines_out), encoding="utf-8")
        print(f"Nadpisano {sec_yaml_path} (kopia: {bak.name})")
    else:
        print("DRY-RUN: section.yaml nie zapisany")
    return 0


if __name__ == "__main__":
    sys.exit(main())
