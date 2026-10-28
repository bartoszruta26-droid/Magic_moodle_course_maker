#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deepen_shortest_naturopata.py — pogłębienie najmniejszych treściowo rozdziałów
kursu „Kwalifikacyjny Kurs Zawodowy – Naturopata” (tych, które nawet po
uzupełnieniach pozostają poniżej ~2000 B).

Podejście: dla wskazanych plików dopisuje sekcję „## Pogłębienie tematu” z
treścią merytoryczną właściwą dla danego rozdziału (kodeks etyczny, księga
powitalna, karty dokumentacji, techniki felczerskie, algorytm BLS).

Zasady jak w pozostałych skryptach kursu: append-once, idempotentność przez
marker, treść prawdziwa (źródła: Pismo Święte, *Dignitas personae*, Hipokrates,
wytyczne ERC 2021, ustawa o prawach pacjenta), piękna i sprawiedliwa.

Użycie:
    python3 scripts/deepen_shortest_naturopata.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CUR = ROOT / "courses" / "03-kwalifikacyjny-kurs-zawodowy-naturopaty" / "sections"
MARKER = "## Pogłębienie tematu"

CONTENT: dict[str, str] = {
    # ——— Księga powitalna (sekcja 00) ———
    "00-ogloszenia/book-01/chapters/01-slowo-wstepne-dyrektora-kursu.md": """
### Słowo do rozpoczynających naukę

Drogi Kursancie, przyjęcie do tego kursu jest początkiem drogi, na której
zdobywa się nie tylko dyplom, ale i zaufanie ludzi chorych. Proszę Cię o trzy
postawy już od pierwszego dnia:

1. **Pokorę wobec wiedzy** — medycyna jest dziedziną, w której każdy z nas
   wie za mało; uczciwe „nie wiem” ratuje więcej istnień niż brawurowa pewność.
2. **Sumienność w ćwiczeniu rąk** — technika, którą wykonasz setki razy na
   fantomie i partnerze ćwicznym, u pacjenta będzie bezpieczna; technika
   niedotrenowana stanie się bronią.
3. **Wrażliwość na drugiego człowieka** — pacjent opowie Ci więcej o bólu
   tonem głosu niż skala NRS; ucz się słuchać ciała i osoby jednocześnie.

Program obejmuje 23 moduły i załączniki A–K rozłożone na cztery semestry.
Kolejność pracy w każdej sekcji: książka → quiz → zadanie praktyczne. Nie
przeskakuj etapów; systematyka jest formą szacunku wobec przyszłego pacjenta.

Na koniec — pamiętaj, że końcem tej drogi nie jest egzamin, lecz spotkany
człowiek, który odda w Twoje ręce swoje zdrowie. Niech Cię tu nigdy nie
zabraknie, gdy będzie potrzebny.
""",
    "00-ogloszenia/book-01/chapters/02-misja-naturopaty.md": """
### Rysopis zawodu — czym naturopata jest, a czym nie jest

**Jest:** edukatorem zdrowia, terapeutą manualnym, opiekunem w profilaktyce
i rehabilitacji, towarzyszem procesu zdrowienia, łącznikiem między stylem życia
a fizjologią; osobą prowadzącą pacjenta drogą higieny, żywienia, ruchu, ziela
i dotyku — zawsze w granicach kompetencji i zawsze we współpracy z lekarzem.

**Nie jest:** diagnostą chorób, preskryptorem leków wydawanych z przepisu
lekarza, terapeutą chorób ostrego przebiegu ani zastępcą lekarza POZ. Tam,
gdzie zaczyna się choroba wymagająca rozpoznania i leczenia przyczynowego,
naturopata ma obowiązek skierować — nie leczyć «na własną rękę».

**Rdzeń misji** wyraża pięć filarów tradycyjnej medycyny naturalnej (w ujęciu
europejskiej naturaterapii i Sebastiana Kneippa): *vis medicatrix naturae*
(lecznicza siła natury), *primum non nocere* (po pierwsze nie szkodzić),
*tollere causam* (usuń przyczynę), *docere* (ucz pacjenta), *cura hominem,
non morbum* (lecz człowieka, nie tylko chorobę). Każdy moduł kursu przyporządkowuje treść do któregoś
z filarów — dzięki temu wiedza układa się w postawę, nie w zbiór ciekawostek.

Misja realizuje się codziennie w drobnych wiernościach: punktualność, czyste
ręczniki, aktualna wiedza, szczerość rokowania, czas dla pacjenta starszego i
niespokojnego. Kto te rzeczy zaniedbuje, ten zaniedbuje samą misję.
""",
    "00-ogloszenia/book-01/chapters/03-jak-korzystac-z-kursu.md": """
### Praktyczny rytm nauki (propozycja tygodniowa)

| Dzień | 60–90 minut | Cel |
|-------|-------------|-----|
| Poniedziałek | lektura jednego rozdziału book + notatka studyjna | zrozumienie |
| Wtorek | powtórka notatek + fiszki (terminologia z Załącznika D) | utrwalenie |
| Środa | ćwiczenie praktyczne (technika wg Załącznika B) | umiejętność |
| Czwartek | lektura drugiego rozdziału + materiały z Załącznika A | pogłębienie |
| Piątek | quiz sekcji + analiza błędów | kontrola |
| Sobota | zadanie modułowe (assignment) | zastosowanie |
| Niedziela | odpoczynek, krótkie czytanie Kodeksu etycznego | formacja |

**Zasady porządkowe:**
- Postęp zaznaczaj w checklistie Załącznika B — samoocena co dwa tygodnie.
- Pytania, których nie wyjaśniłeś na bieżąco, zapisuj w jednym pliku «do
  prowadzącego» i zabieraj na zjazd; pytanie odroczone wraca jako wątpliwość
  w gabinecie.
- Materiały multimedialne pobieraj raz i kataloguj (rok–moduł–temat); chaos
  w zbiorach kradnie czas przeznaczony pacjentom.
- Prace oddawaj przed terminem — ostatnia doba należy do redakcji i oddechu.
""",
    "00-ogloszenia/book-01/chapters/04-zasady-bezpieczenstwa.md": """
### Procedury bezpieczeństwa — wersja skrócona do gabinetu

1. **Przed pierwszym dotykiem:** wywiad przesiewowy (gorączka, leki, ciąża,
   nowotwór, zakrzepica, choroby skóry), zgoda świadoma, warunki lokalowe
   (temperatura 22–24 °C, oświetlenie, dostęp do wyjścia).
2. **W trakcie:** stały kontakt słowny z pacjentem przy technikach głębokich;
   objawy alarmowe (ból ostry, zawrót głowy, kołatanie serca, drętwienie)
   → natychmiastowe przerwanie, pozycja bezpieczna, ocena, decyzja: dalszy
   ciąg / zakończenie / pomoc.
3. **Stany nagłe:** utrata przytomności z oddechem → pozycja boczna
   bezpieczna, obserwacja oddechu, 112; brak oddechu → BLS wg Załącznika
   K.10 i modułu 12.4; duszność, ból w klatce, objawy udaru (Zespół FAST) →
   112 bez zwłoki. Apteczka i telefon z numerami alarmowymi muszą być
   dostępne w każdym gabinecie, w którym pracujesz.
4. **Po incydencie:** wpis do książki zdarzeń, informacja do przełożonego/
   prowadzącego, analiza przyczyn — nie szukanie winnych.
5. **Ergonomia terapeuty:** zasada ciężaru ciała zamiast siły palców,
   przerwy co drugi zabieg, rotacja okolic; zmęczona ręka jest ręką
   niebezpieczną.
6. **Farmakologiczne i zielarskie:** żadnego preparatu nie podajesz bez
   sprawdzenia interakcji z lekami pacjenta (Załącznik A.9) i bez zapisu
   dawki; przy alergiach w wywiadzie — test śladowy i obserwacja.

Bezpieczeństwo nie jest dodatkiem do zabiegu — jest jego pierwszą częścią.
""",
    # ——— Kodeks etyczny (Załącznik E) ———
    "29-zalacznik-e-kodeks-etyczny/book-01/chapters/02-rozdzial-i-prawda-w-praktyce.md": """
### Jak stosować zasadę prawdy — sytuacje trudne

1. **«Inna metoda mnie uzdrowiła»** — odpowiadam: «Cieszę się, że Pan/Pani
   lepiej się czuje; opiszę, co zrobiłem, i co mówi piśmiennictwo». Nie
   przywłaszczam sobie efektów, których nie mogę wykazać. Rokowanie oparte
   na dowodach oznaczam źródłem; hipotezy — jako hipotezy.
2. **Pacjent prosi o «potwierdzenie» diagnozy znalezionej w internecie** —
   nie potwierdzam i nie zaprzeczam diagnozy (to nie moja kompetencja);
   tłumaczę, jakie badania ją weryfikują, i kieruję do lekarza.
3. **Błąd własny** (np. zbyt intensywna technika, siniak) — mówię otwarcie,
   przepraszam, dokumentuję, proponuję postępowanie naprawcze. Ukrywanie
   błędu jest drugim, cięższym przewinieniem wobec pacjenta.
4. **Reklama i social media** — nie używam słów «gwarantuję», «skutecznie
   leczy nowotwory», «detoksykuje»; nie publikuję wizerunku pacjenta bez
   pisemnej zgody i bez anonimizacji kontekstu klinicznego.
5. **Granice komplementarności** — jeśli pacjent kończy leczenie konwencjonalne
   «bo zioła wystarczą», informuję o ryzyku i namawiam do rozmowy z lekarzem;
   milczenie byłoby współwiną.

Prawda zawodowa ma trzy wymiary: zgodność słów z faktami, słów z intencją
oraz czynów ze słowami. Kodeks wymaga wszystkich trzech.
""",
    "29-zalacznik-e-kodeks-etyczny/book-01/chapters/04-rozdzial-iii-sprawiedliwosc.md": """
### Sprawiedliwość — zastosowania codzienne

1. **Sprawiedliwość rozdzielcza** — ten sam standard procedury dla każdego:
   taki sam wywiad, taka sama higiena rąk, taka sama długość zabiegu niezależnie
   od napiwku, wyglądu czy poglądów pacjenta. Preferencje osobiste nie mogą
   zmieniać jakości usługi.
2. **Sprawiedliwość wobec czasu** — nie umawiam dwóch pacjentów na tę samą
   godzinę «na wszelki wypadek»; spóźnienie wobec jednego jest kradzieżą
   wobec drugiego.
3. **Sprawiedliwość wobec konkurencji** — nie oczerniam innych praktyków,
   nie kupuję reklam w wyszukiwarkach pod hasłami szydzonymi z medycyny
   konwencjonalnej; różnicę jakości ogłaszam czynem, nie kampanią.
4. **Sprawiedliwość cenowa** — cena odpowiada realnemu czasowi i kosztom;
   praktyka przewiduje zniżki lub godziny pro bono dla osób ubogich, chorych
   przewlekle i samotnych — bo miłość bliźniego ma również wymiar ekonomiczny.
5. **Sprawiedliwość wobec prawa** — płacę podatki, mam ubezpieczenie OC
   działalności, odprowadzam składki; praca «na czarno» krzywdzi pacjenta
   (brak ochrony) i zawód (brak odpowiedzialności).
6. **Sprawiedliwość pokoleniowa** — przekazuję wiedzę uczniom uczciwie,
   bez zawyżania własnych osiągnięć; dbam, by środowisko zawodowe nie było
   skażone oszustwem.
""",
    "29-zalacznik-e-kodeks-etyczny/book-01/chapters/06-rozdzial-v-pokora-i-rozwoj.md": """
### Rachunek sumienia naturopaty — pytania do comiesięcznej refleksji

1. Czy w tym miesiącu odmówiłem zabiegu tam, gdzie powinienem odmówić
   (przeciwwskazania, wątpliwa diagnostyka)? Czy skierowałem do lekarza
   bez ociągania?
2. Czy nauczyłem się czegoś nowego z literatury (Załącznik A), czy tylko
   powtarzałem nawyki? Kiedy ostatnio przeczytałem artykuł, który zmienił
   moje postępowanie?
3. Czy superwizja/konsultacja koleżeńska miała miejsce, czy jej unikałem
   z wygody lub lęku przed oceną?
4. Czy zadbałem o własne ciało — sen, ruch, ręce? Wypalony terapeuta jest
   zagrożeniem dla pacjentów, nie ofiarą systemu.
5. Czy nie obiecałem za wiele? Czy nie przypisałem sobie cudzego dobra?
6. Czy traktowałem «trudnego» pacjenta tak samo starannie jak «wdzięcznego»?
7. Co w tym miesiącu zrobiłem źle — i co konkretnie zmieniam w przyszłym?

Rozwój zawodowy dokumentuję w dzienniczce praktyk (godziny, zakres,
superwizje, kursy) — służy on przy re-certyfikacji i jest dowodem kultury
pokory, nie biurokracji. Pokora nie oznacza braku pewności siebie; oznacza
pierwszeństwo prawdy nad moim ego.
""",
    "29-zalacznik-e-kodeks-etyczny/book-01/chapters/07-rozdzial-vi-wymiar-duchowy-poslugi.md": """
### Wymiar duchowy — jak przeżywać go profesjonalnie i nienachalnie

1. **Źródło postawy.** Dla wierzącego naturopaty służba choremu jest
   uczestnictwem w miłości Boga do człowieka («Byłem chory, a odwiedziliście
   Mnie» — Mt 25,36). Dla niewierzącego — ta sama postawa wyraża się jako
   bezwarunkowy szacunek dla godności osoby. Kodeks respektuje obie drogi;
   żadnej nie narzuca pacjentowi.
2. **Co wolno, czego nie:** wolno zapytać chorego, czy życzy się modlitwy
   lub obecności kapłana; wolno samemu zachować chwilę ciszy przed zabiegiem.
   Nie wolno uzależniać usługi od wyznania, nie wolno moralizować przy stole
   zabiegowym, nie wolno twierdzić, że choroba jest «karą» lub «lekcją» —
   to słowa, które ranią bardziej niż niosą pocieszenie.
3. **Troska o duszę terapeuty.** Regularny odpoczynek, sakramenty lub praktyka
   wewnętrzna według własnej tradycji, kierownictwo duchowe/superwizja —
   to nie luksus, lecz zabezpieczenie pacjenta przed moim wypaleniem.
4. **U kresu życia.** Gdy pacjent umiera mimo opieki — towarzyszenie, wsparcie
   rodziny, odsunięcie własnej bezradności na bok. Naturopata nie jest
   heroldem sukcesu; jest sługą także w chorobie nieuleczalnej, zgodnie
   z zasadą *ambulare cum patiente* — iść z chorym do końca.
5. **Pokora wobec tajemnicy.** Nie wszystko w medycynie da się wyjaśnić;
   uzdrowienie bywa większe niż nasza procedura. Dziękczynienie po dobrej pracy
   i westchnienie po pracy daremnej należą do tego samego rzemiosła miłości.
""",
    "29-zalacznik-e-kodeks-etyczny/book-01/chapters/01-preambula.md": "",  # już rozbudowany
    # ——— Załącznik J — karta superwizji ———
    "34-zalacznik-j-coachingu/book-01/chapters/08-j-8-karta-superwizji-wzor.md": """
### Jak wypełniać kartę superwizji — instrukcja

1. **Kto i kiedy.** Superwizant (coach/mentee) zgłasza przypadek superwizorowi
   raz na kwartał lub po zdarzeniu krytycznym (konflikt, podejrzenie szkody,
   silna reakcja własna). Spotkanie trwa 45–60 minut; wpis do karty robi
   superwizant, podpisują obie strony.
2. **Sekcje karty:** dane identyfikacyjne sesji (data, forma, czas), opis
   przypadku ANONIMOWO (bez imion, dokładnego wieku, miejsca), postawione
   pytanie superwizyjne (np. «czy moja interwencja była proporcjonalna?»),
   analiza: co zadziałało, co pominąłem, jaki był mój transfer emocjonalny,
   ustalenia naprawcze i termin przeglądu.
3. **Granice.** Superwizja nie jest terapią własną — gdy temat dotyczy
   osobistych ran superwizanta, kierujemy go do psychoterapeuty; superwizor
   nie ocenia osoby, tylko metodę i bezpieczeństwo klienta.
4. **Archiwizacja.** Karty przechowamy 5 lat (dane wrażliwe — zgodnie z RODO);
   stanowią one dowód rozwoju zawodowego przy re-certyfikacji i chronią
   klienta, ponieważ wymuszają regularną autorefleksję.
5. **Wartość duchowa.** Uczciwa superwizja jest aktem pokory (Rozdz. V kodeksu)
   i sprawiedliwości (Rozdz. III) — najlepszym dowodem miłości bliźniego jest
   kwestionowanie własnej pewności, zanim zrobi to życie pacjenta.
""",
    # ——— Załącznik K — techniki felczerskie ———
    "35-zalacznik-k-zabiegi-felczerskie/book-01/chapters/05-j-5-technika-lewatywy-i-wlewu-doodbytniczego.md": """
### Uwagi bezpieczeństwa i wskazań (lewatywa / wlew doodbytniczy)

1. **Wskazania praktyczne:** zalegający stolec twardy przy parciu (wg
   zalecenia lekarza), przygotowanie do badań, podanie leku/ziela drogą
   doodbytniczą przy przeciwwskazaniu do doustnej. **Nie jest to** metoda
   «odtruwania» czy «detoksu» — takich obietnic nie składam i nie reklamuję.
2. **Przeciwwskazania bezwzględne:** ostry ból brzucha z podejrzeniem
   chirurgicznym, krwawienie z przewodu pokarmowego, uchyłkowica w ostrym
   epizodzie, świeży zabieg operacyjny jelita/odbytnicy, hemoroidy IV stopnia
   lub szczelina krwawiąca, toksyczne megacolon.
3. **Parametry:** objętość dorosły 500–1000 ml (roztwór ciepły 36–38 °C,
   izotoniczny lub wg zlecenia), ciśnienie słupa wody ≤ 60 cm, głębokość
   introdukcji kanuli 7–10 cm, pozycja lewa z zgiętymi kolanami. U dzieci
   dawki znacznie mniejsze i wyłącznie na zlecenie lekarza.
4. **Przebieg:** wyjaśnienie i zgoda, prywatność, badanie stanu okolicy
   odbytu, delikatna introdukcja bez siły, zatrzymanie przy bólu/oporze,
   obserwacja wydalanej treści (ilość, konsystencja, domieszki — zapis!).
5. **Powikłania (rzadkie, groźne):** perforacja (ból ostry, gorączka →
   NATYCHMIAST 112), zaburzenia elektrolitowe przy powtarzanych wlewach
   fosforanowych, odruch wagalny z omdleniem. Dlatego dokumentuję każde
   wykonanie i nigdy nie powtarzam procedury «profilaktycznie».
""",
    "35-zalacznik-k-zabiegi-felczerskie/book-01/chapters/06-j-6-technika-plukania-zoladka.md": """
### Granice i bezpieczeństwo płukania żołądka

1. **Stan faktyczny:** płukanie żołądka (*lavatio gastrica*) jest procedurą
   ostrego dyżuru medycznego, wykonywaną niemal wyłącznie w warunkach
   szpitalnych, zwykle przy zabezpieczeniu dróg oddechowych. Współczesne
   wytyczne (toksykologia kliniczna) ograniczają jej wskazania do niewielu
   sytuacji (duże dawki substancji wchłanialnych w pierwszej godzinie,
   trucizny nierentgenowskie) i odradzają rutynowe stosowanie.
2. **Rola naturopaty/felczera:** ROZPOZNANIE zagrożenia i WEZWANIE pomocy
   (112 / Centrum Informacji Toksykologicznej), przygotowanie pacjenta,
   zebranie danych (co, ile, kiedy, opakowanie), ewentualne PODANIE tlenu,
   ułożenie boczne przy nieprzytomności. Nie wywołuję wymiotów u dziecka,
   osoby nieprzytomnej ani po środkach żrących/pianych — to grozi
   perforacją i aspiracją.
3. **Jeżeli procedura została zlecona przez lekarza i nadzorowana:**
   zgoda, pozycja siedząca lub boczna z głową niżej (zapobieganie aspiracji),
   sondę dobieram wg wzrostu (pomiar nos–mieczyk–wyrostek mieczykowaty),
   płuczę porcjami 200–300 ml do uzyskania przejrzystego wypływu, kontroluję
   saturację i przytomność, dokumentuję objętość płynów i charakter treści.
4. **Alarm:** spieniona treść, krew, ból zamostkowy, spadek SpO₂, bezdechy
   → przerwanie i natychmiastowa pomoc lekarska.
5. **Zasada nadrzędna:** w zatruciach czas liczy się w minutach, a nie
   w godzinach «domowych zabiegów». Moja uczciwość wobec pacjenta każe
   dzwonić 112 wcześniej niż później — każda zwłoka jest udziałem w krzywdzie.
""",
    "35-zalacznik-k-zabiegi-felczerskie/book-01/chapters/07-j-7-technika-naciecia-i-drenazu-ropnia.md": """
### Nacięcie i drenaż ropnia — co wolno, czego nie

1. **Status prawny.** Otwarcie ropnia jest procedurą chirurgiczną; w Polsce
   mieści się w zakresie świadczeń lekarskich i pielęgniarskich w określonych
   warunkach. Felczer/naturopata może rozpoznać zmianę, zabezpieczyć i
   skierować; samodzielne nacinanie dopuszczalne jest wyłącznie w sytuacji
   wyjątkowej (brak dostępu do pomocy, zagrożenie sepsą) i nigdy «z przyzwyczajenia».
2. **Ocena przed decyzją:** wielkość (> 1 cm?), otoczka zapalna, miejscowy
   wzrost temperatury, ból tętniący, gorączka > 38 °C, cukrzyca, immunosupresja,
   lokalizacja (twarz «trójkąt niebezpieczny», okolica kanału słuchowego,
   dno miednicy → zawsze do lekarza).
3. **Postępowanie, gdy zmiana kwalifikuje się do pilnej pomocy lekarskiej:**
   ciepłe okłady 3×15 min (dojrzewanie), antyseptyka powierzchni, jałowy
   opatrunek, analgezja bez maskowania objawów, wizyta chirurgiczna w 24 h,
   przy gorączce — tego samego dnia.
4. **Po drenażu wykonanym przez uprawnionego:** wymiana opatrunków wg zlecenia,
   kontrola sączenia, temperatury, obwodowego zaczerwienienia (wędrówka czerwonej linii =
   limfangitis → pilnie!), edukacja higieny rąk i prania pościeli (MRSA).
5. **Dokumentacja:** opis lokalizacji, wyglądu, dat, zleceń i reakcji pacjenta;
   przy podejrzeniu zaniedbania lub przemocy — tryb ochrony osoby.
""",
    "35-zalacznik-k-zabiegi-felczerskie/book-01/chapters/10-j-10-algorytm-bls-aed-sekwencja-czynnosci.md": """
### Algorytm BLS/AED — rozwinięcie wg wytycznych ERC 2021

1. **Bezpieczeństwo ratującego** — ocena otoczenia (ruch, prąd, gaz), rękawiczki,
   asekuracja własna; potem: przytomność? oddech prawidłowy? (max 10 sekund
   patrzenia na klatkę, słuchania, czucia policzkiem).
2. **Wezwanie pomocy:** 112 (głośno, konkret: «dorosły mężczyzna, nie oddycha,
   ulica…, telefon…»), AED z budynku/pojazdu, osoba do przyjęcia dyspozytora.
   Przy dziecku — najpierw 1 min resuscytacji, potem telefon (jeśli jestem sam).
3. **Uciskania:** środek mostka, głębokość 5–6 cm (dziecko ~1/3 przednio-tylnej wymiaru klatki),
   częstość 100–120/min, pełny rozstęp, minimalne przerwy (< 10 s), wymiana
   co 2 min lub przy zmęczeniu.
4. **Oddechy:** 30:2 po udrożnieniu dróg (czoło–żuchwa); u dorosłego z doświadczeniem
   możliwe samo uciskanie; u dziecka i przy asfiksji — obligatoryjne oddechy.
5. **AED:** włączyć, nakleić elektrody (pod prawym obojczykiem, po lewej stronie
   klatki pod pachą), nie dotykać pacjenta przy analizie/wyładowaniu, natychmiast
   wracać do uciskania po wyładowaniu przez 2 min.
6. **Zmiana ratującego:** kontynuować do przyjazdu ZRM, zmiany co 2 min; nie
   przerywać «żeby sprawdzić puls» poza rytmem cykli.
7. **Po zatrzymaniu krążenia:** pozycja boczna przy powrocie oddechu, kontrola
   oddychania co minutę, cieplne okrycie, rozmowa uspokajająca; dokumentacja
   czasu rozpoczęcia RKO i kolejnych faz dla zespołu ratownictwa.

Ćwicz sekwencję na fantomie minimum raz na kwartał — pamięć mięśniowa ratuje,
gdy adrenalina odbiera rozum.
""",
    "35-zalacznik-k-zabiegi-felczerskie/book-01/chapters/12-j-12-wyposazenie-apteczki-felczerskiej-lista.md": """
### Zasady gospodarowania apteczką

1. **Przegląd kwartalny:** data ważności środków jałowych i leków, stan
   plomb, kompletność wg listy; zużyte pozycje uzupełniam NATYCHMIAST po
   zdarzeniu, nie «na następny przegląd».
2. **Warunki przechowywania:** 15–25 °C, sucho, ciemność, poza zasięgiem
   dzieci; adrenalinę w ampułkach trzymam w miejscu najbardziej dostępnym,
   nie w najgłębszej szufladzie.
3. **Podział funkcjonalny apteczki:** (a) oddech/drożność — ambu, rurki
   ustno-gardłowe, ssak; (b) krążenie/rany — opaski elastyczne, gazy,
   plastry hemostatyczne, nożyce Listera; (c) układanie/unieruchomienie —
   szyny, kołnierz; (d) ochrona — rękawiczki, fartuch, okulary; (e)
   dokumentacja — karty, długopis wodoodporny.
4. **Etyka wyposażenia:** sprzęt nieużywany psuje się w szafie — ćwiczymy
   na nim co miesiąc; apteczka, która «jest, ale nie działa», jest
   sprawiedliwością pozorną i pozorem bezpieczeństwa.
5. **Komplet mobilny** (wizyty domowe): rękawiczki, maseczki, dezynfekcja,
   opatrunki uciskowe, koc termiczny, telefon z ładowarką powerbank, lista
   alarmowa (112, toksykologia, lekarz POZ pacjenta).
""",
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Pogłębienie najmniejszych rozdziałów kursu Naturopata")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not CUR.is_dir():
        print(f"BLAD: brak katalogu {CUR}", file=sys.stderr)
        return 2
    written = 0
    for rel, block in CONTENT.items():
        if not block.strip():
            continue
        path = CUR / rel
        if not path.is_file():
            print(f"  POMINIĘTO (brak pliku): {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        if MARKER in text:
            print(f"  POMINIĘTO (marker): {rel}")
            continue
        new = text.rstrip() + "\n\n---\n\n" + MARKER + "\n" + block.strip() + "\n"
        if not args.dry_run:
            path.write_text(new, encoding="utf-8")
        written += 1
        print(f"  {'[DRY-RUN] ' if args.dry_run else ''}POGŁĘBIONO: {rel} ({len(text.encode())} B -> ~{len(new.encode())} B)")
    print(f"\nPODSUMOWANIE{' [DRY-RUN]' if args.dry_run else ''}: pogłębionych plików={written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
