#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fill_appendix_books_naturopata.py — prawdziwa treść merytoryczna rozdziałów
książek (book) załączników A–K kursu „Kwalifikacyjny Kurs Zawodowy – Naturopata”.

Motywacja
---------
Rozdziały książek załączników były szkicami generycznymi (ten sam szablon
„Cel szczegółowy / Zakres materiału / Uwagi etyczne” dla każdego tematu).
Niniejszy skrypt zastępuje je PRAWDZIWĄ, przedmiotową treścią: konkretne
podręczniki i wydania (A), punkty umiejętności z kryteriami zaliczenia (B),
pełne wzory kart dokumentacji (C), katalog przeciwwskazań (F), mapy anatomiczne
(G), schematy masażu leczniczego wg A. Zborowskiego (H), zestawy ćwiczeń
(I), protokoły coachingu (J) i procedury zabiegów felczerskich (K).

Bezpieczeństwo / idempotentność
-------------------------------
* Nadpisuje WYŁĄCZNIE pliki rozpoznane jako generyczny szkic (znak firmowy
  szablonu: zdanie „omówienie pojęcia, celów i miejsca zagadnienia”).
* Rozdziały zawierające już treść właściwą są pomijane — powtórne uruchomienie
  nic nie zmienia.
* Tryb --dry-run wypisuje plan bez zapisów.

Zasady treści: prawdziwa (oparta na uznanej literaturze i prawie PL; brak
obietnic leczniczych bez dowodów; czerwone flagi i skierowania do lekarza),
piękna (porządek, szacunek dla godności pacjenta), sprawiedliwa (jasne granice
kompetencji naturopaty, RODO, primum non nocere).

Użycie
------
    python3 scripts/fill_appendix_books_naturopata.py [--base PATH] [--dry-run] [--list-missing]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

GENERIC_MARKER = "omówienie pojęcia, celów i miejsca zagadnienia"
DEFAULT_BASE = Path("courses/03-kwalifikacyjny-kurs-zawodowy-naturopaty")

ETHICS = """## Uwagi etyczne

Treści tego kursu przekazujemy w duchu Bożej miłości, prawdy, piękna i
sprawiedliwości: bez fałszywych obietnic, z poszanowaniem godności każdej osoby
i zasady *primum non nocere*. Tam, gdzie dowody naukowe milczą, mówimy otwarcie,
że milczą. Wszystkie dane osobowe w dokumentacji chronimy zgodnie z RODO."""


def code(text: str) -> str:
    return f"\n```\n{text.strip()}\n```\n"


# ---------------------------------------------------------------------------
# ZAŁĄCZNIK A — Wykaz lektur
# ---------------------------------------------------------------------------
A_BOOK = {
    "a-1": """# A.1. Podręczniki anatomii i fizjologii

Obowiązkowa baza naukowa modułu 1. Korzystaj z wydań najnowszych; starsze
dopuszczalne dla porównania terminologii.

**Anatomia:**
- F. Bochenek, M. Reicher, *Anatomia człowieka*, t. I–V, Wydawnictwo Medyczne Urban & Partner / PZWL — systematyczny atlas całego ciała; dla naturopaty kluczowe tomy: ruchu (narząd ruchu) i krążenia–limfy.
- P. H. Rauber, A. W. Kierschbaum, *Atlas Anatomii Człowieka*, Elsevier Urban & Partner — atlas przekrojów topograficznych; podstawowa pomoc przy masażu segmentarnym i analizie unerwienia segmentarnego.
- E. Traczyk, *Fizjologia człowieka z elementami fizjologii klinicznej*, PZWL — podręcznik modułowy 1.2.

**Fizjologia:**
- W. Buzielski (red.), *Fizjologia człowieka*, PZWL.
- Guyton, Hall, *Traktat o fizjologii medycznej*, Elsevier Advanced Press — pogłębione mechanizmy regulacyjne (krążenie, oddechowanie, nerki).

**Zastosowanie praktyczne:** każdy zabieg dobieraj do znanej anatomii okolicy
(kierunek włókien mięśniowych, przebieg naczyń i węzłów chłonnych, segmenty
nerwowe); nazwy łacińskie utrwalaj ze słownika (Załącznik D).""",
    "a-2": """# A.2. Podręczniki masażu leczniczego

- **A. Zborowski**, *Masaż klasyczny i segmentarny*, PZWL — główny podręcznik modułów 6–9 i Załącznika H: klasyfikacja chwytów, dobór siły i czasu, schematy postępowania w jednostkach chorobowych.
- **A. Zborowski**, *Masaż w wybranych jednostkach chorobowych*, PZWL — uzupełnienie Załącznika H (astma, RZS, ZZSK, dyskopatia, stany po urazach).
- **L. Przywieczowska-Nawrotek i in.**, *Masaż*, WSiP — przystępne wprowadzenie do techniki klasycznej dla początkujących.
- **V. Chaitow**, *Masaż tkanki łącznej i odruchowej*, Amber — wprowadzenie do technik reflektorycznych z zachowaniem krytycyzmu dowodowego.
- **B. Foldi, M. Foldi**, *Podstawy drenażu limfatycznego* (wyd. pol., Uppercase) — pozycja odniesienia modułu 8; skuteczność drenażu w obrzękach limfatycznych jest dobrze udokumentowana.

**Uwaga metodyczna:** masaż klasyczny ma umiarkowaną moc dowodową w bólu
przewlekłym niespecyficznym i lęku; nie przypisuj mu działania leczniczego
w chorobie trzewnej — działa wspomagająco, objawowo i relaksacyjnie.
""",
    "a-3": """# A.3. Podręczniki fitoterapii i zielarstwa

- **Z. E. Susurna (red.)**, *Fitoterapia i leki roślinne*, PZWL — farmakognozja zgodna z polskim rejestrem; punkt wyjścia oceny dowodowej.
- **W. Teske, J. Trentmann**, *Formularz receptury aptecznej i zielarskiej*, PZWL — receptura przetworów.
- **Commission E Monographs** (EMA/HMPC listy) — monografie niemieckiej Komisji E: dziurawiec, głóg, kawałek (Valeriana), liść brzozy; standard bezpieczeństwa interakcji.
- **European Scientific Cooperative on Phytotherapy (ESCOP)**, *Monographs on the Medicinal Uses of Plant Drugs*.
- Farmakopea Polska XII + wykaz środków dopuszczonych przez URPL — weryfikacja legalności surowca.

**Twarda reguła bezpieczeństwa:** dziurawiec wchodzi w interakcje z lekami
przeciwzakrzepowymi (acenocumarol, warfaryna), antykoncepcyjnymi,
immunosupresyjnymi i przeciwdepresyjnymi (ryzyko zespołu serotoninowego) —
przed każdą rekomendacją sprawdź listę leków pacjenta. Nie stosuj preparatów
hepatotoksycznych (np. pieprznicy/kava, żywotnik w dużych dawkach) bez wiedzy
o próbach wątrobowych.""",
    "a-4": """# A.4. Podręczniki dietetyki i medycyny żywienia

- **H. Cybulska-Hejduk (red.)**, *Praktyczna dietetyka*, PZWL — diety lecznicze i profilaktyczne.
- **M. Jarosz (red.)**, *Normy żywienia dla populacji Polski*, IŻŻ/NIZP-PZH (aktualne wydanie) — normy energii i składników pokarmowych, bezpieczne górne granice spożycia (UL).
- **H. Weker, P. Gertig**, *Zasady prawidłowego żywienia dzieci i młodzieży oraz wskazówki do ich realizacji*, IŻŻ.
- Opinie **EFSA** i raporty **WHO** — ocena dowodów (błonnik a lipidemia, sód a ciśnienie, dieta śródziemnomorska a choroby sercowo-naczyniowe).
- **Ocena stanu odżywienia**: antropometria (BMI, obwód talii, WHR), plicometria, bioimpedancja (BIA) wg standardów WHO.

**Granica kompetencji:** żywienie w cukrzycy typu 1, chorobie nerek,
jadłowstręcie psychicznym i wrodzonych chorobach metabolicznych prowadzi
dietetyk kliniczny/lekarz — naturopata wspiera edukację i monitoruje realizację
ustaleń zespołu terapeutycznego.
""",
    "a-5": """# A.5. Podręczniki kinezyterapii i treningu medycznego

- **P. Kasperczyk**, *Badanie przedmiotowe i funkcjonalne w ortopedii i traumatologii narządu ruchu*, REHAS — standard badania funkcjonalnego (ROM, siła, testy specjalne).
- **A. Zborowski**, *Masaż klasyczny i segmentarny* oraz rozdziały rehabilitacyjne serii PZWL „Rehabilitacja” — podstawy kinezyterapii stosowanej.
- **G. Wilczyński**, *Podstawy rehabilitacji*, PZWL — systematyka ćwiczeń leczniczych.
- **ACSM**, *Guidelines for Exercise Testing and Prescription* (wyd. amerykańskie lub opracowania PT) — FITT (częstotliwość, intensywność, czas, rodzaj), progresja obciążeń, przeciwwskazania do wysiłku.
- Stanowiska **EULAR/ASAS** (ZZSK, RZS) i **WHO** (aktywność fizyczna dorosłych i seniorów) — aktualne wytyczne aktywności.

**Priorytet dowodowy:** aktywność fizyczna ma najmocniejsze dowody wśród metod
niefarmakologicznych (wtórna prewencja choroby niedokrwienną serca, cukrzyca
typu 2, depresja łagodna/umiarkowana, nadciśnienie). Trening dobieraj wg
tolerancji wysiłku pacjenta (test 6-minutowego marszu, tętno rezerwowe).
""",
    "a-6": """# A.6. Podręczniki medycyny komplementarnej i integracyjnej

- **E. Ernst, S. Singh**, *Trick or Treatment? Alternative Medicine on Trial* — rzetelna, oparta na dowodach krytyczna ocena terapii komplementarnych (dostępna w bibliotekach uczelnianych).
- **NCCIH** (National Center for Complementary and Integrative Health) — arkusze informacyjne: akupunktura, chiropraktyka, joga, mindfulness; materiały na wolnych licencjach.
- **Cochrane Library** — przeglądy systematyczne interwencji komplementarnych (np. akupunktura w bólu przewlekłym — efekt niewielki, ale statystycznie istotny; homeopatia — ponad placebo brak).
- Stanowiska **Polskiego Towarzystwa Lekarskiego** i towarzystw naukowych dot. medycyny integracyjnej — najnowsze komunikaty.

**Stanowisko kursu:** oceniamy metody według dowodów, nie tradycji; pacjentowi
przedstawiamy poziom pewności wprost: «to łagodzi», «nie wiadomo»,
«niebezpieczne/nieefektywne».
""",
    "a-7": """# A.7. Podręczniki coachingu i mentoringu zdrowotnego

- **J. Whitmore**, *Coaching for Performance* (wyd. pol. dostępne) — model GROW, międzynarodowy standard struktury sesji.
- **W. Rollnick, S. Miller**, *Motywujące rozmowy o zmianie zachowań* (tłum., Wyd. Naukowe PWN/PZWL) — wywiad motywujący: metoda zmiany zachowań zdrowotnych z najmocniejszą bazą metaanalityczną.
- **ICF (International Coaching Federation)** — Code of Ethics i Core Competencies — ramy etyczne zawodu coacha.
- **Prochaska, DiClemente** — model etapów gotowości do zmiany (transteoretyczny) — podstawa planowania sesji (por. J.5).
- Materiały superwizyjne certyfikowanych szkół coachingu (PTCH i in.).

**Etyka:** coaching zdrowotny nie jest psychoterapią ani leczeniem; przy
objawach depresyjnych (PHQ-9 ≥ 10) lub lękowych (GAD-7 ≥ 10) kieruj do
lekarza lub psychologa.
""",
    "a-8": """# A.8. Źródła prawa medycznego i etyki zawodowej

- **Ustawa z dnia 5 grudnia 1996 r. o zawodach lekarza i lekarza dentysty** (t.j. Dz.U. 2024 poz. 1945 ze zm.) — granice diagnozy i leczenia (art. 2, 18).
- **Ustawa z dnia 15 kwietnia 2011 r. o działalności leczniczej** (t.j. Dz.U. 2024 poz. 743) — formy udzielania świadczeń; działalność naturopaty jako usługi niefinansowane ze środków publicznych.
- **Ustawa o prawach pacjenta i Rzeczniku Praw Pacjenta** (t.j. Dz.U. 2024 poz. 1485) — zgoda świadoma (art. 16–18), dokumentacja medyczna (art. 23–27), tajemnica (art. 14).
- **RODO** (rozp. 2016/679) + **ustawa o ochronie danych osobowych** (t.j. Dz.U. 2023 poz. 1999) — dane o zdrowiu = szczególna kategoria (art. 9 RODO).
- **Kodeks etyki lekarskiej** jako punkt odniesienia; dla naturopatów — kodeksy stowarzyszeń branżowych (PZN) + Załącznik E niniejszego kursu.
- **PKWiU/PKD** i wymogi sanitarne (Sanepid) lokalu usługowego; regulamin gabinetu.

**Praktyka:** ubezpieczenie OC działalności, umowa powierzenia przetwarzania danych z serwisem księgowym/IT, rejestry czynności przetwarzania.""",
    "a-9": """# A.9. Leki współczesnej terapii (interakcje z fitoterapią)

Minimum znajomości grup leków, które pacjent bierze — zawsze pytaj o pełną listę!

| Grupa leku | Typowa interakcja ziołowa | Postępowanie naturopaty |
|---|---|---|
| Antykoagulanty (warfaryna, acenokumarol) | dziurawiec ↓ INR; czosnek, imbir, kurkuma, miłorząb ↑ ryzyka krwawienia | nie rekomenduj tych ziół; zmiany wyłącznie przez lekarza |
| Antykoncepcja hormonalna | dziurawiec (indukcja CYP3A4) ↓ skuteczność | informacja + antykoncepcja barierowa na czas kuracji |
| Digoksyna | lukrecja (hipokaliemia) ↑ toksyczności | unikać przewlekłej dawki lukrecji |
| Leki hipotensyjne | głóg, czosnek — efekt addycyjny | monitorować ciśnienie; NIE odstawiać leków! |
| Metformina/insulina | cynamon kasja, goryczka — możliwy efekt hipoglikemizujący | kontrola glikemii; decyzje dawkowania należą do lekarza |
| SSRI/SNRI | dziurawiec, 5-HTP — ryzyko zespołu serotoninowego | bezwzględnie nie łączyć |
| Cyklosporyna/takrolimus | dziurawiec ↓ stężenie — ryzyko odrzutu | nigdy nie zalecać; pilne skierowanie |
| NLPZ | lukrecja, imbir w dużych dawkach — drażnienie błony śluzowej | limit czasu, osłona, konsultacja farmaceutyczna |

**Źródła:** Charakterystyki Produktów Leczniczych (ChPL) w Rejestrze URPL;
monografie Komisji E / EMA-HMPC; bazy interakcji (pomocniczo — decyzja zawsze
po konsultacji z lekarzem lub farmaceutą).
""",
}

# ---------------------------------------------------------------------------
# ZAŁĄCZNIK B — Umiejętności praktyczne (checklist)
# ---------------------------------------------------------------------------
B_SKILLS = {
    "b-1": """# B.1. Techniki masażu klasycznego — wymagania zaliczeniowe

Uczestnik wykonuje na żywym modelu (partner szkoleniowy) komplet pięciu
chwytów podstawowych, w kolejności i prawidłowo:

1. **Głaskanie (effleurage)** — powierzchniowe i głębokie; kierunek odpływu żylnego/limfatycznego; tempo 30–40 ruchów/min; ucisk < 2 kg.
2. **Rozcieranie (friction)** — okrężne i poprzeczne; opuszkami/palcami; mobilizacja przrostów i blizn; bez tarcia skóry (ruch tkaniny względem podłoża!).
3. **Ugniatanie (petrissage)** — pełne i częściowe, podwójne kołowe; wzdłuż włókien mięśnia; faza napięcia ≤ 2 s, rozluźnienia dłuższa.
4. **Oklepywanie (tapotement)** — siekanie, stukanie, beatowanie; nad mięśniami, nigdy nad kolcami kostnymi, nerkami, węzłami.
5. **Wibracja (vibration)** — drgająca i ciągła; końcowy element partii.

**Kryteria zaliczenia:** płynność przejść, kontakt wzrokowy/słowny z modelem,
pytanie o odczucia co 2 minuty, dobór średnicy pracy do budowy, zakończenie
głaskaniem, higiena rąk i paznokci przed zabiegiem. Czas całkowity demonstracji:
15 min na jednej połowie ciała tylnej.""",
    "b-2": """# B.2. Masaż klasyczny okolic — kolejność i pułapki

Standardowe okolice i ich specyfika techniczna:

- **Kończyna dolna (przód/tył):** zawsze odpływ proximally (węzły pachwinowe); omijanie dołu podkolanowego głęboko; po zakrzepicy — tylko po pisemnej zgodzie lekarza.
- **Kończyna górna:** ostrożnie w dole pachowym; kanał nadgarstka — techniki rozluźniające, nie uciskające.
- **Grzbiet:** dwa etapy (partia lędźwiowo-krzyżowa → piersiowa → szyjno-potyliczna); paravertebrae nigdy bezpośrednio na wyrostkach kolczystych; okolica nerek — tylko głaskanie powierzchowne.
- **Szyja i kark:** bez rotacji biernych głowy; mięsień czworoboczny i dźwigacz łopatki — ugniatanie częściowe; tętnica szyjna wspólna poza obszarem pracy.
- **Klatka piersiowa i brzuch:** masaż międzyżebrzy oddechowy; brzuch — głaskanie zgodnie z perystaltyką okrężnicy (ruch wskazówek zegara), bezwzględnie przeciwwskazany w ostrym stanie jamy brzusznej.
- **Twarz i głowa:** effleurage+petrissage delikatne, drenaż zatok, mięsień żwacz i potyliczno-czołowy.

**Kryteria:** dobór pozycji klienta (leżenie przodem/tyłem/na boku, podparcia),
czas partii 5–8 min, komunikacja odczuć, dokumentacja w karcie zabiegowej (C.2).""",
    "b-3": """# B.3. Masaż segmentarny — punkty maksymalne i reakcje

Technika wg Zborowskiego: praca na skórno-naczyniowo-mięśniowych segmentach
połączonej z unerwieniem trzewnym (strefy Heada):

1. Identyfikacja **punktów maksymalnej bolesności** (badanie dotykowe i fałdem skórnym) w odpowiednich segmentach Th/L/S.
2. Kolejność: segmenty piersiowe (serce → Th1–Th5, płuca → Th1–Th7, żołądek → Th6–Th10, wątroba → Th8–Th11, jelita → Th9–L2), lędźwiowe (nerki L1–L2, jelito grube L1–L3), krzyżowe (moczowe S2–S4, rodne L5–S2).
3. Chwyty: głębsze rozcieranie fałdu, wałka mięśniowego przykurczowego; czas 10–15 min/segment; obserwacja **reakcji segmentarnej** (zniżenie napięcia, rumień, ulga trzewna).

**Środki ostrożności:** nasilenie objawów w trakcie = przerwać; never na okolicę
tarczycy bez wskazań lekarskich; ciąża — tylko odcinek szyjny/piersiowy górny
w pozycji bocznej, po konsultacji położniczej.""",
    "b-4": """# B.4. Drenaż limfatyczny — sekwencja i przepustowość

Manualny drenaż limfatyczny (MDL) wg zasad Vodder/Leduc:

1. **Otwarcie przepustów** — najpierw zbiorcze węzły (pachwinowe, pachowe, szyjne), potem obwodowo do centralnych.
2. **Techniki:** pompowanie, workowanie (circle pump), kokonowanie (cupping), pompująco-obrotowe; ruch wolny (1–2 s/cykl), rytmiczny, bez poślizgu skórnego, siła «miękka jak pióro».
3. **Kolejność obrzęku:** proximal→distal (odcentualizacja), obustronna symetria tułowia.
4. **Czas:** 45–60 min; po zabiegu bandażowanie wielowarstwowe lub rękaw kompresyjny (klasy II–III) — bez kompresji MDL mało skuteczny.

**Wskazania udowodnione:** obrzęk limfatyczny pierwotny i wtórny (np. po mastektomii — profilaktyka i leczenie; bezpieczeństwo po leczeniu nowotworowym potwierdzone przez consensusy). **Przeciwwskazania:** aktywna infekcja, niewydolność serca, zakrzepica, nowotwór nieleczony (ryzyko — opinia onkologa).""",
    "b-5": """# B.5. Terapia manualna i mobilizacje — zakres bezpieczny

Naturopata pracuje wyłącznie technikami **łagodnymi, fizjologicznymi**:

- Mobilizacje stawów obwodowych: trakcja, poślizgi (gliding), rotacje w zakresie bezzboelowym — 3 serie × 10 powtórzeń.
- Kręgosłup: mobilizacje pośrednie (posturalne, wisceralne, oddechowe) — BEZ gwałtownych manipulacji high-velocity (thrust); to domena lekarza/certyfikowanego fizjoterapeuty.
- Tkanki miękkie: rozluźnianie postizometryczne (PIR), techniki energii mięśniowej (MET) łagodne, rolowanie wałkiem (foam roller) jako samoopieka pacjenta.

**Kryteria zaliczenia:** umiejętność oceny end-feel, rozpoznawanie czerwonych
flag neurologicznych (radikulopatia, zespół ogona końskiego → natychmiast
do lekarza!), dokumentacja zakresów ROM goniometrem/przed-i-po.""",
    "b-6": """# B.6. Masaż specjalistyczny — odmiany i zastosowania

- **Masaż sportowy:** przedwysiłkowy (krótki, pobudzający: oklepywanie, szybkie rozcieranie 5–8 min), potreningowy (uspokajający, odpływowy 20–30 min), regeneracyjny (średniointensywny, 48 h po starcie).
- **Masaż bańką chińską (próżniowy):** kierunek odpływu limfy, zasada «ciemny ślad = mniejsze ssanie», przeciwwskazania: kruchość naczyń, antykoagulanty, żylaki w obszarze.
- **Masaż gorącymi kamieniami:** temperatura kamieni 50–60 °C (termometr!), próba na swoim przedramieniu, bez obszarów neuropatii (stopa cukrzycowa!).
- **Masaż tkanek głębokich:** wolne, skierowane w głąb; ból ≤ 4/10; zakaz na wyrostki kostne i nerwy powierzchowne.
- **Masaż dziecięcy:** noworodki/niedonoszone wyłącznie w ramach programów szkolonych i za zgodą neonatologa; niemowlęta — głaskanie i delikatne ruchy zgodnie z instruktażem pediatrycznym.

**Kryteria:** dobór metody do celu, parametry (siła/tempo/czas), przeciwwskazania (F), ocena efektu subiektywna i obiektywna (ROM, skala bólu VAS).""",
    "b-7": """# B.7. Ćwiczenia lecznicze — dobór i dawkowanie

Umiejętności:

1. Badanie siły mięśniowej skalą Lovetta (0–5) i dobór ćwiczeń wspomaganych/czynnych/oporowych wg wyniku.
2. Pozycje startowe i odbarczenie (leżenie, podwieszenie, 4-point kneeling).
3. Rodzaje skurczu: koncentryczny, ekscentryczny (progresja bólu ścięgna — protokół Jill Cook dla tendinopatii), izometryczny (ból ostry — 45 s × 5, 70 % MVC).
4. Dawka: 2–3 serie × 8–12 powtórzeń, 3×/tydzień minimum; progresja obciążenia ≤ 10 %/tydzień.
5. Zasada «ból dozwolony ≤ 3/10, ustępujący < 24 h».

**Kryteria zaliczenia:** napisanie 4-tygodniowego planu ćwiczeń dla
przypadku klinicznego (np. bark zamrożony, faza zamrożenia) z uzasadnieniem
doboru, kryteriami przerwania i punktami kontroli.""",
    "b-8": """# B.8. Ćwiczenia oddechowe i relaksacyjne

: **Oddech przeponowy:** leżenie, ręka na brzuchu, wdech 4 s → pauza 2 s →
  wydech 6 s; 5–10 min 2×/dzień; wskazania: POChP (wargi spięte), lęk,
  napięciowy ból głowy.
- **Rozszerzanie dolnych żeber:** opór rąk na bokach klatki, wdech nosem przez
  nos 2 s + przedłużony wydech przez zaciśnięte usta.
- **Relaksacja progresywna Jacobsona:** napnij 5–7 s → rozluźnij 15–20 s,
  grupa po grupie (stopy → twarz); własne nagranie audio studenta jako zadanie.
- **Trening autogenny Schultza** (formuły ciężkości i ciepła) — ostrożnie:
  przeciwwskazany w psychozach i ciężkiej depresji (kieruj do specjalisty).
- **Mindfulness / MBSR** 8-tygodniowy — metaanalizy: obniżenie lęku i nasilenia
  bólu przewlekłego (efekt umiarkowany).

**Kryteria:** przeprowadzenie 10-minutowej sesji dla grupy z prawidłową
instrukcją słowną, spokojnym tempem głosu i bezpieczną pozycją uczestników.
""",
    "b-9": """# B.9. Trening medyczny — programowanie

Kompetencje:

1. Wywiad + testy: tętno spoczynkowe, HRmax orientacyjnie 220−wiek (±12), Borg CR10/RPE, 6-min walk, równowaga jednonóż.
2. Strefy intensywności: HRR Karvonen (start 40–60 %), talk-test; progresja tygodniowa ≤ 10 %.
3. Komponenty programu: cardio (150 min/tydz. umiarkowanego wg WHO), siła (2×/tydz., duże grupy, 8–12 RM), mobilność, równowaga (osoby starsze — prewencja upadków).
4. Warunki szczególne: nadciśnienie (uniknąć Valsalvy), cukrzyca (buty, glukometr, pora posiłku), osteoporoza (zakaz zgięć tułowia z obciążeniem — ryzyko złamań kompresyjnych), POChP (interwały), choroba niedokrwienna (warm-up ≥ 10 min, stop przy anginie).

**Kryteria:** napisanie 12-tygodniowego programu dla dwóch przypadków z
protokołem bezpieczeństwa i kryteriami odstąpienia (ACSM red flags).""",
    "b-10": """# B.10. Zabiegi hydro- i fizykoterapeutyczne

: **Hydroterapia:** kąpiele perełkowe (36–38 °C, 10–15 min), naprzemienne
  polewania wg Kneippa (adaptacja wegetatywna; zakaz w niewydolności serca),
  okłady parowe, natryski.
- **Ciepło:** okłady parafinowe (kąpiel 52–56 °C, kontrola czucia!), podczerwień;
  przeciwwskazania: ostre stany zapalne, zaburzenia czucia, nowotwór w obszarze.
- **Zimno:** pakiet lodowy 10–15 min przez ręcznik; krioterapia miejscowa;
  zakaz w chorobie Raynauda i pokrzywce zimowej.
- **Światło:** lampy UV-B wyłącznie zleceniowo (dermatolog) — nigdy «solarium
  leczniczo»; laser niskopoziomowy (LLLT) — dowody mieszane, jedynie uzupełniająco.
- **Elektroterapia/TENS:** TENS gate-control (80–120 Hz, ból ostry) i endorfinowy
  (2–4 Hz, ból przewlekły) — instruktaż urządzenia domowego; ultradźwięki
  lecznicze — tylko pod nadzorem fizykoterapeuty.

**Kryteria:** przeprowadzenie zabiegu z kartą parametrów (C.2) oraz edukacja
pacjenta o zagrożeniach (oparzenia, odmrożenia, poparzenia słoneczne, fotouczulenia ziołowe — dziurawiec, pasternak!),
przeciwwskazania (F.5) oraz zapis parametrów w karcie zabiegowej (C.2).
""",
    "b-11": """# B.11. Przygotowanie przetworów zielarskich

Techniki laboratoryjne (gabinet/school-botanika):

1. **Herbatka (infusum):** 1–2 łyżeczki surowca/250 ml, wrzątek (liście/kwiaty) lub 90 °C (zioła lotne), parzenie 10–15 min pod przykryciem.
2. **Odwar (decoctum):** korzeń/kora — gotowanie 5–10 min (np. prawoślaz korzeń na zimno 4 h).
3. **Nalewka (tinctura):** macerat w 40–70 % etanolu; proporcja suszu do
  rozpuszczalnika zwykle 1:5; 14–21 dni, filtrować; przechowywać w ciemnym
  szkle; etykieta: surowiec, data, moc.
4. **Maść/krem:** faza olejowa (wosk pszczeli, lanolina, masło shea) + ekstrakt;
  konserwanty dopuszczone; test stabilności (4 °C / 25 °C).
5. **Olejki eteryczne:** NIGDY doustnie bez fachowca; na skórę 1–2 % (dorośli);
  dzieci < 6 lat — większość olejków przeciwwskazana (kamfora, eukaliptol —
  ryzyko skurczu krtani/nasady!).

**Kryteria:** wykonanie trzech przetworów z pełną etykietą i kartą
bezpieczeństwa; surowce wyłącznie ze źródeł badanych mikrobiologicznie
i pod kątem metali ciężkich oraz pozostałości pestycydów.
""",
    "b-12": """# B.12. Czynności przesiewowe i pomiarowe — co wolno naturopacie

Naturopata **nie stawia rozpoznań**. Może wykonywać pomiary przesiewowe,
obserwacje i edukację:

- Parametry życiowe: RR, tętno, SpO₂ (pulsoksymetr), temperatura, masa/wzrost/BMI, obwód talii.
- Glukometr domowy + dzienniczek glikemii (interpretacja — lekarz/dietetyk).
- Analiza składu ciała metodą BIA — orientacyjnie, nie jako badanie kliniczne.
- Ocena postawy (fotografia boczna/przednia, pion odciężnikowy) i zakresów ruchu (goniometr).
- Kwestionariusze przesiewowe: PHQ-9/GAD-7 (wynik wysoki → lekarz/psycholog), IPAQ (aktywność), PSQI (sen).
- Tradycyjne metody obserwacyjne (język, puls wg TCM) — wyłącznie jako kontekst edukacyjny, bez roszczeń diagnostycznych.

**Kryteria zaliczenia:** przeprowadzenie kompletu pomiarów na modelu w ≤ 30 min,
wpisanie wyników do karty C.1 i sformułowanie wniosku w formie «co mieści się
w normach, co wymaga konsultacji lekarskiej» (bez stawiania rozpoznań).
""",
    "b-13": """# B.13. Sesja coachingu zdrowotnego — struktura GROW

Demonstracja pełnej 45-minutowej sesji:

1. **Contracting** (5 min): cel spotkania, granice («nie jestem lekarzem»).
2. **Goal** (10 min): cel pacjenta w jego słowach, skalowanie wartości (dlaczego ważne 7/10?).
3. **Reality** (12 min): obecny stan, próby, bariery, zasoby; słuchanie refleksyjne, sumowania.
4. **Options** (12 min): burza mózgów bez oceniania; wybór przez pacjenta (autonomia!).
5. **Will** (6 min): konkretne SMART działanie, pierwszy krok w 48 h, wskaźnik sukcesu.
6. Domknięcie: podsumowanie słowami pacjenta, umówiona kontrola.

**Kryteria:** nagranie/transkrypt sesji pair-work; ocena wg ICF core
competencies (obecność, pytania otwarte, cisza, unikanie doradzania
przedwczesnego).""",
    "b-14": """# B.14. Sesja mentoringu — model relacji rozwojowej

Mentoring zdrowotny (pacjent przewlekły, opiekun rodzinny):

1. Struktura spotkania cyklicznego (co 2–4 tyg.): check-in → temat przewodni → przegląd dziennika zdrowia → jedna nowa umiejętność (skills teaching) → plan → wsparcie emocjonalne.
2. Modelowanie zachowań: demonstracja + wspólne wykonanie (technika inhalatora,
   pomiar RR, czytanie etykiet spożywczych).
3. Normalizacja trudności: «co zwykle przeszkadza», radzenie sobie z rzutami
   choroby bez poczucia winy.
4. Budowanie sieci wsparcia: grupy samopomocy, instytucje (NFZ, MOPS,
   organizacje chorobowe).
5. Granice: mentoring ≠ terapia psychologiczna; przy kryzysie psychicznym —
   telefon zaufania 116 123, pomoc doraźna.

**Kryteria:** przedstawienie planu 6 spotkań dla przypadku astmy u dziecka
(opiekun = rodzic) wraz z własnoręcznie przygotowanym materiałem edukacyjnym (ulotka o inhalatorze).
""",
    "b-15": """# B.15. Pierwsza pomoc — algorytmy ERC 2021

Obowiązkowe opanowanie (symulator + AED szkoleniowy):

1. **BLS dorosły:** bezpieczeństwo sceny → ocena przytomności → oddech ≤ 10 s →
   wezwanie 112/999 + AED → RRC 30:2 (5–6 cm, 100–120/min) → AED jak najszybciej
   → do przyjazdu PRM.
2. **Zakrztuszenie:** 5 uderzeń w plechy + 5 ucisków nadbrzusza (Heimlich),
   naprzemiennie; utrata przytomności → RRC.
3. **Wstrząs anafilaktyczny:** adrenalina i.m. 0,3–0,5 mg (auto-wstrzykiwacz
   pacjenta!), pozycja leżąca z uniesionymi nogami (lub półsiedząca przy duszności),
   druga dawka po 5–15 min, wezwanie PRM.
4. **Udar — FAST** (Face-Arm-Speech-Time) → natychmiast 112. **Zawał** — pozycja
   półsiedząca, spokój, oczekiwanie na PRM (aspiryna tylko wg dyspozycji dyspozytora).
5. Omdlenie, padaczka (po napadzie — pozycja boczna ustalona), hipoglikemia
   (przytomny → 15–20 g cukru prostego; nieprzytomny → NIC doustnie, pozycja
   boczna, 112).

**Kryteria:** zdany egzamin praktyczny BLS+AED na manekinie (preferowany
certyfikat zewnętrzny, np. pierwszej pomocy medycznej).
""",
    "b-16": """# B.16. Zabiegi felczerskie (cyrulika) — historyczne i współczesne

Zakres dopuszczalny **tylko** w granicach prawa polskiego (usługi pielęgnowania
ciała; żadne procedury naruszające ciągłość tkanek bez uprawnień medycznych):

- Opatrunki proste na skaleczenia powierzchowne (dezynfekcja, plastry, rękawiczki jednorazowe, złom igieł do pojemnika).
- Usuwanie odcisków nagniotków TYLKO keratolitycznie (moczenie, salicylowa pasta, frezowanie przez wykwalifikowanego podologa — współpraca).
- Plaster/mieszanka rozgrzewająca wg receptury bezpiecznej (bez otwartych ran).
- Bańki suche/ogniowe — ograniczenia: nie na żylaki, nie > 10 min, nie codziennie; bańki «ślad» nie jest dowodem «toksyn» (mit — wyjaśniaj pacjentom).
- Upust krwi, nacinanie ropni, nastawianie złamań, «łamanie kości» — **BEZWZGLĘDNIE POZA ZAKRESEM** (to czyny medyczne; art. 65 KW/ Kodeks karny — wykonywanie zawodu medycznego bez uprawnień).

**Kryteria:** zdany test sytuacyjny «co wolno, a co wymaga lekarza» (100 %
poprawności dla pozycji zakazanych).""",
}

# ---------------------------------------------------------------------------
# ZAŁĄCZNIK C — Dokumentacja (wzory)
# ---------------------------------------------------------------------------
C_FORMS = {
    "c-1": """# C.1. Karta pacjenta — wywiad naturopatyczny

```
KARTA PACJENTA — NATUROPATA CERTYFIKOWANY     nr: .........   data: ..........
--- INFORMACJE STAŁE ---
Imię i nazwisko ............................ Data ur. ........ PESEL* (tylko gdy wymagany prawem)
Adres ............................. Telefon ................. E-mail ........................
Osoba do kontaktu w nagłym razie: ..................................................
Waga ...... kg   Wzrost ...... cm   BMI ......   Obwód talii ...... cm
Wykształcenie/zawód ................... Stan cywilny ......... Aktywność fizyczna (IPAQ) .........
--- INFORMACJE ZMIENNE ---
Skarga główna (słowami pacjenta): .......................................................
Historia obecnej dolegliwości (OLDCARTS: początek, lokalizacja, czas trwania,
charakter, nasilenie, czynniki łagodzące/nasilające, pora dnia): ....................
Rozpoznania lekarskie (dotychczasowe) i daty: ..........................................
Leki stałe (nazwa, dawka, godzina): ....................................................
Alergie (leki, pokarmy, jad owadów, lateks): ...........................................
Przeszłe operacje / hospitalizacje / urazy: .............................................
Szczepienia (kalendarz): ...............................................................
Wywiad rodzinny (choroby sercowo-naczyniowe / nowotwory / cukrzyca / psychiczne): ....
--- STYL ŻYCIA ---
Sen (h/noc, jakość): ....... Posiłki/dzień: ... Warzywa/owoce (porcje/dzień): ...
Alkohol (jednostki/tydzień): ... Palenie (PY): ... Stres (0–10): ... Ekran/hobby: ...
Opieka nad osobami bliskimi: .........................................................
--- CEL WSPÓŁPRACY ---
Czego oczekuje pacjent: ................................................................
Granice: naturopata NIE stawia rozpoznań i NIE zmienia leczenia lekarskiego.
Zgoda na przetwarzanie danych (RODO) [ ] Tak, podpis: .......... Data: ..........
Wywiad przeprowadził: .................................""",
    "c-2": """# C.2. Karta zabiegowa

```
KARTA ZABIEGOWA        nr karty pacjenta: ........   data/godz: ............
Zabieg: masaż klasyczny / segmentarny / drenaż limfatyczny / trening / fizykoterapia / inny
Obszar: ..................... Czas: ....... min   Intensywność (1–5): .....
Parametry (TENS: Hz/mA; ciepło: °C/czas; bańki: ssanie/czas; ciśnienie RR przed): ....
Przed zabiegiem: RR ....../....  HR .....  ból VAS ..../10  temperatura .....
Obserwacje w trakcie (reakcja skóry, napięcie tkanek, tolerancja, zgłaszane odczucia):
........................................................................................
Po zabiegu: ból VAS ..../10  samopoczucie .......... ROM .........
Działania niepożądane: [ ] brak [ ] zaczerwienienie [ ] ból ↑ [ ] inne: .........
Zalecenia domowe: ....................................................................
Kryterium odstąpienia przy następnej wizycie: .............................
Wykonał/a: ......................... Podpis: .............""",
    "c-3": """# C.3. Plan terapii integracyjnej (wzór)

```
PLAN TERAPII INTEGRACYJNEJ      nr pacjenta: ......   sporządzono: ........
ROZPOZNANIE LEKARSKIE (od lekarza): ...........................................
CELE (SMART, priorytet pacjenta): 1) ........ 2) ........ 3) ........
SKŁADOWE PLANU (każda: interwencja, dawka, częstotliwość, kryterium oceny):
 A. Ruch/trening medyczny: .................................................
 B. Żywienie: ..............................................................
 C. Regeneracja/sen/stres: .................................................
 D. Zabiegi wspomagające (masaż/drenaż/fizo): ..............................
 E. Fitoterapia (tylko wspomagająco, po sprawdzeniu interakcji!): ...........
 F. Coaching/mentoring: ....................................................
 KOORDYNACJA Z LEKARZEM: kto, kiedy, czego dotyczy (zmiana leków = lekarz!)
 HARMONOGRAM: wizyty co .... tyg.; kontrola parametrów: ....................
 KRITERIA SKIEROWANIA (red flags — patrz Załącznik F): ......................
 PODPISY: pacjent ......... naturopata ......... (lekarz, jeśli uczestniczy)""",
    "c-4": """# C.4. Karta konsultacji fitoterapeutycznej

```
KARTA FITOTERAPEUTYCZNA       nr pacjenta: .....   data: ......
Cel konsultacji (objaw, nie «choroba»): ....................................
Leki pacjenta (SPRAWDŹ INTERAKCJE — tabela A.9): ............................
Rekomendacja:
 Surowiec/preparat: ................. Forma: herbata/nalewka/kapsułka/maść
 Dawkowanie: ........................ Czas trwania: ...... dni
 Poziom dowodów: [ ] solidne [ ] prawdopodobne [ ] tradycyjne/brak
 Ryzyko działań niepożądanych i środki ostrożności: ........................
 Przeciwwskazania u tego pacjenta: ..........................................
 Kontrakt: «Nie odstawiam leków przepisanych; przy nasileniu objawów — lekarz.»
 Monitorowanie: objawy ......... parametry ......... wizyta kontrolna .........
Wydał: .................. Podpis pacjenta: ...............""",
    "c-5": """# C.5. Karta konsultacji dietetycznej

```
KARTA DIETETYCZNA        nr pacjenta: .....   data: .....
Analiza spożycia (24 h + 3 dni weekendowe): kalorie ~...... kcal
Białko ...... g/kg  Błonnik ...... g/d  Sól ...... g/d  Cukry dodane ...... %
Warzywa/owoce ...... porcji/d  Woda ...... l/d  Posiłki/dni ......
Deficyty do weryfikacji badaniami (lekarz!): żelazo/ferrytyna, B12, wit. D,
wapń, jod — [ ] zlecono [ ] wyniki w normie
Plan docelowy (piramida + preferencje kulturowe pacjenta):
 Śniadanie .......... II śniadanie .......... Obiad .......... Podwieczorek
 Kolacja .......... Zamiany: 1) ........ 2) ........ 3) ........
Edukacja: czytanie etykiet, indeks glikemiczny, metody obróbki ............
Osoby na diecie eliminacyjnej (vegan, bezglutenowa): suplementacja B12 itp. —
konsultacja z dietetykiem klinicznym.
Kontrola za ...... tyg. (dzienniczek + obwód talii/BMI).
Prowadził: ................""",
    "c-6": """# C.6. Karta treningu medycznego

```
KARTA TRENINGU MEDYCZNEGO   nr pacjenta: .....   data: .....   cykl: .... tyg.
Testy wejściowe: HRspo ....  RR ....  6MWD .... m  ROM ....  siła Lovett ....
RPE/Borg cel: .......  Strefa HR: ....... (Karvonen ....% HRR)
ROZGRZEWKA (10 min): ........................................
CZĘŚĆ GŁÓWNA (dzień A/B):
 A: cardio ....... min; siła: przysiad ....×..., wiosłowanie ....×..., mostek ....
 B: cardio ....... ; równowaga ....... ; mobilność .......
WYCISZENIE + rozciąganie (5–10 min): ...............................
PROGRESJA: co .... tyg. o .... % (nie więcej niż 10%/tydz.; kryteria awansu: ....)
STOP/ZMIANA: ból >3/10 utrzymujący się 24 h, duszność nieproporcjonalna,
zawroty, ból w klatce → przerwij, kontakt z lekarzem.
Samoopieka między wizytami (domy): .........................................
Kontrola za .... tyg. Prowadzący: ................""",
    "c-7": """# C.7. Karta coachingu zdrowotnego

```
KARTA COACHINGU         nr pacjenta: .....   sesja nr: .....   data: .....
Kontrakt sesji (cel w słowach pacjenta): ....................................
GOAL: cel odległy ......... «dlaczego to ważne?» ......... wartość 0–10: ....
REALITY: co teraz? ......... próby dotychczas? ......... bariery? .........
         zasoby (kim/co pomaga)? ......... pewność 0–10: ....
OPTIONS: 1) ......... 2) ......... 3) ......... (wybór klienta: ....)
WILL: działanie SMART ............. pierwszy krok (48 h) .............
      wskaźnik sukcesu ............. potencjalne przeszkody+plan B .........
Notatki procesowe (metoda: otwarte pytania/skalowanie/odzwierciedlenia):
Następna sesja: ......... Prowadzący: .........
UWAGA: brak poradnictwa medycznego; przy wynikach PHQ-9≥10/GAD-7≥10 → lekarz.""",
    "c-8": """# C.8. Formularz świadomej zgody na zabieg

```
ŚWIADOMA ZGODA NA ZABIEG (masaż/drenaż/trening/zabieg fizykalny/fitoterapia)
Ja, .................................. , oświadczam, że:
1. Zostałem/am poinformowany/a o celu, przebiegu, czasie i oczekiwanych
   efektach zabiegu: .......................................................
2. Znam możliwe odczucia (tkliwość, przemijający ból) i działania
   niepożądane (zaczerwienienie, siniak, nasilenie objawów).
3. Podałem/am kompletne informacje o zdrowiu: choroby, leki, alergie,
   ciąża/karmienie, urządzenia wszczepione (rozrusznik!, pompa insuliny).
4. Rozumiem, że naturopata NIE jest lekarzem, zabieg ma charakter
   wspomagający/relaksacyjny i NIE zastępuje leczenia.
5. Mogę przerwać zabieg w każdej chwili i cofnąć zgodę bez konsekwencji.
6. Wyrażam zgodę na przetwarzanie danych o zdrowiu (RODO) w celu
   realizacji usługi; dane nie są przekazywane podmiotom trzecim bez mojej
   zgody, z wyjątkiem lekarza przy skierowaniu.
Data i podpis pacjenta: ............ Podpis wykonawcy: ............
Osoba ubezwłasnowolniona/małoletni: zgoda przedstawiciela ustawowego .........""",
    "c-9": """# C.9. Skierowanie do lekarza (wzór noty)

```
NOTA SKIERUJĄCA DO LEKARZA            data: ........   nr pacjenta: .......
Do: [ ] lekarz POZ  [ ] specjalista: ..........  [ ] SOR/PRM (pilne!)
Powód (OBSEWACJE, nie rozpoznanie): .................................................
Objawy i czas trwania: ...............................................................
Parametry zmierzone: RR .... HR .... T .... SpO₂ .... glukoza .... (jeśli mierzono)
Leki pacjenta: .....................................................................
Co już zaproponowano / z czego zrezygnowano: .......................................
Pilność: [ ] natychmiast (czerwona flaga) [ ] 24–48 h [ ] rutynowo (termin tygodniowy)
Informuję pacjenta o konieczności wizyty; pacjent [ ] przyjął do wiadomości.
Naturopata: ..................... Tel. gabinetu: .....................
Kopia do karty pacjenta. (PAMIĘTAJ: nie stawiam diagnozy, nie zmieniam leków.)""",
    "c-10": """# C.10. Karta obserwacji pacjenta (wizyty kontrolne)

```
KARTA OBSERWACJI/KONTROLI     nr pacjenta: .....   data: .....   tydzień cyklu: ..
Poprzedni plan: realizacja [%]: ....  co ułatwiło? ....  co przeszkodziło? ....
Pomiary: waga ....  talia ....  RR ....  HR ....  ból VAS ....  sen (jakość) ....
Nowe objawy / objawy alarmowe: .....................................................
Ocena tolerancji zabiegów/treningu: ............................................
Decyzja: [ ] kontynuuj bez zmian [ ] modyfikuj: ........ [ ] skieruj do lekarza
Następna wizyta: .............  Zadanie domowe: ................................
Skrót notatki (SOAP): S ......... O ......... A ......... P .........
Prowadzący: ................""",
    "c-11": """# C.11. Karta drenażu limfatycznego

```
KARTA DRENAŻU LIMFATYCZNEGO   nr pacjenta: .....   data: .....   sesja nr ..
Obwód kończyny (kostka/łydka/udo, obie strony): .... / .... / .... cm
Stopień obrzęku wg klasyfikacji ISL/ILO (I–III): ....  znak Stemmera: [ ]tak [ ]nie
Faza: [ ] odciążająca (codziennie, 45–60 min) [ ] podtrzymująca (..x/tydz.)
Techniki: pompowanie / workowanie / kokonowanie / pompująco-obrotowe — obszary: ....
Kompresja po zabiegu: bandaż ....-warstwowy / rękaw klasa .... / pończocha ....
Edukacja samoopieki: pozycje, auto-drenaż, higiena skóry, ćwiczenia .........
Odpowiedź: obwód ↓ .... cm  ciężar/subiektywne ....  tolerancja ....
Przeciwwskazania sprawdzono (F.3): [ ] brak
Wykonał: ..............""",
    "c-12": """# C.12. Karta zabiegów felczerskich / cyrulicznych

```
KARTA ZABIEGU CYRULICZNEGO (zakres usługowy, bez procedur medycznych!)
nr pacjenta: ..... data: .....
Zabieg: opatrunek drobny / okład / bańki / keratoliza odcisku / inny .........
Opis zmiany (obserwacja, nie rozpoznanie): ...................................
Czy wymaga lekarza? [ ] nie [ ] TAK → nota C.9 (ropień, rana głęboka, podejrzana
zmiana barwnikowa, stopa cukrzycowa, objawy zakażenia: gorączka, limfangitis/wydzielina)
Materiały: jałowe/niejałowe, dezynfekcja pola, złom igieł [ ]
Efekt i zalecenia: ...........................................................
Instrukcja domowa + kryteria alarmowe: .......................................
Wykonał: ................ Podpis: ........""",
    "c-13": """# C.13. Karta szczepień (informacyjno-edukacyjna)

```
KARTA SZCZEPIEŃ — ewidencja informacji, NIE kwalifikacja (lekarz!)
nr pacjenta: ..... data wypełnienia: .....
Kalendarz podstawowy (DTap, Polio, Hib, PCV, Rotawirusy, MMM, WZW B, HPV ...):
 szczepienie / data przyjęcia / dawka / ewentualne NOP .......................
Zalecane sezonowo: grypa (rok ....), COVID-19 (....), kleszczowe zapalenie
mózgu (region, serie) .......................................................
Pytania pacjenta do lekarza (przygotuj fakty, nie opinie): ...................
Moja rola: wsparcie decyzji zgodnej z evidencją (WHO/NIZP-PZH), ulotka
«jak przygotować dziecko/dorosłego do szczepienia», monitoring NOP 48 h.
Źródła: Program Szczepień Ochronnych (GIS) rocznik .........
Prowadzący: ................""",
}

# ---------------------------------------------------------------------------
# ZAŁĄCZNIK F — Przeciwwskazania
# ---------------------------------------------------------------------------
F_CONTRA = {
    "f-1": """# F.1. Przeciwwskazania do masażu klasycznego

**Bezwzględne (całego ciała):**
gorączka i choroby zakaźne (do 24–48 h po ustąpieniu objawów), świeża zakrzepica
żył głębokich i zapalenie żył, dekompensowana niewydolność serca, niestabilne
ciśnienie (hipertonia zagrażająca), tętniaki aorty, ostre stany zapalne tkanek
miękkich, niezagojone rany/ropnie/choroby skóry w obszarze (grzybica, świerzb,
liszajec), nowotwory złośliwe bez opinii onkologa, zaawansowana osteoporoza
(złamań ryzyko), I trymestr ciąży + masaż brzucha/lędźwi głęboki.

**Względne (modyfikuj lub fragment):**
ciąża (pozycja boczna, bez deep tissue brzuch/lędźwi), menstruacja silna,
żylaki (okolica — tylko głaskanie odpływowe), nadciśnienie wyrównane, cukrzyca
(ostrożnie stopy), epilepsja (unikaj bodźców migających/intensywnych),
antykoagulacja (siniaki — mniejsza siła), stany po radioterapii (skóra!),
zaburzenia czucia (kontrola temperatury), choroby dermatologiczne rozsiane
(konsultacja).

**Do poszczególnych chwytów:** oklepywanie — nie nad nerkami, wyrostkami,
głową; rozcieranie głębokie — nie na tętnice, nerwy powierzchowne (łokieć
kanalik!), blizny świeże < 6 tyg.; wibracja — nie przy neuropatii, kamicy
(dróg żółciowych/moczowych ataka).""",
    "f-2": """# F.2. Przeciwwskazania do masażu segmentarnego

Oprócz przeciwwskazań ogólnych (F.1) masaży segmentarny wymaga dodatkowo:

1. Ostre stany zapalne narządów jamy brzusznej (zapalenie wyrostka, pęcherzyka, otrzewnej, nerek) — BEZWZGLĘDNIE; grozi szerzeniem procesu.
2. Gorączka bakteryjna/posocznica; ropnie wewnętrzne.
3. Ostry zespół wieńcowy / niestabilna dławica (segmenty Th1–Th5!) — tylko w fazie rehabilitacji kardiologicznej pod nadzorem.
4. Astma ciężka napadowa (Th1–Th7) — praca wyłącznie w remisji, łagodnie.
5. Nadczynność tarczycy (strefa szyjna Th1–Th2 + szyja) — unikać.
6. Menstruacja obfita, endometrioza w rzucie (L1–S2) — wstrzymaj lub bardzo łagodnie.
7. Kamica żółciowa/moczowa w kolce — nie pobudzaj segmentów Th8–Th11 / L1–L2.
8. Nowotwory — opinia onkologa przed pracą w danym segmencie.

**Reguła:** nasilenie bólu trzewnego, nudności, poty, tachykardia w trakcie =
natychmiast przerwać → ocena lekarska. Strefy Heada służą OBSERWACJI, nie
diagnozie.""",
    "f-3": """# F.3. Przeciwwskazania do drenażu limfatycznego

**Bezwzględne:**
- Aktywne zakażenie/lymphangitis/sepsis (do 48 h po antybiotykoterapii i ustąpieniu gorączki),
- Zakrzepica żył głębokich / zatorowość płucna (świeża; po leczeniu — za zgodą angiologa),
- Niewydolność serca III–IV NYHA (przeciążenie objętościowe),
- Nowotwór złośliwy nieleczony lub podejrzenie wznowy w obszarze drenażu (potrzebna zgoda onkologa),
- Niedoczynność tarczycy nieleczona (obrzęk śluzakowaty — lecz przyczynowo),
- Ostry obrzęk płuc.

**Względne (modyfikuj):** nadciśnienie nieuregulowane, astma (napad), ciąża
(połóg — obrzęki fizjologiczne: łagodnie), cukrzyca z neuropatią (siła!),
mastektomia z radioterapią (skóra wrażliwa — mniejsze podciśnienie baniek),
cewnik/lymfangiografia ostatnio.

**Zasada:** obrzęk asymetryczny nowy, twardy, z bólem/spoczynkowym lub objawami
ogólnymi → PRIORITET diagnostyka lekarska (zakrzepica, miednica ucisk, nowotwór).""",
    "f-4": """# F.4. Przeciwwskazania do treningu medycznego i kinezyterapii

**Bezwzględne (wstrzymaj sesję):**
ból w klatce piersiowej/spoczynkowa angina, arytmia nieuregulowana,
RR ≥ 180/110 lub hipotonia symptomyaczna, gorączka/infekcja ostra,
świeży zakrzepowo-zatorowy epizod, dekompensacja serca, odwarstwienie siatkówki
(okulistyczne ograniczenia), złamanie niestabilne bez zgody ortopedy.

**Względne (adaptuj):**
niestabilność kręgosłupa/oady (omijać skręty obciążone), endoproteza stawu
biodrowego (zakaz zgięcia >90°, addukcji, rotacji wewnętrznej — typ posterior),
osteoporoza (bez zgięć grzbietu z obciążeniem, bez oklepywań kręgosłupa),
cukrzyca (retinopatia proliferacyjna — brak Valsalvy/skłonów; neuropatia —
obuwie i kontrola stóp; hipoglikemia — zasada 15 g), anemia (<10 g/dl —
intensywność niska), ciąża (II/III trim.: bez pozycji leżącej na plecach,
bez high-impact, RPE ≤ 13–14), padaczka (unikać solo-ćwiczeń ryzykownych).

**Red flags w trakcie:** ból promieniujący do żuchwy/ręki, duszność nieadekwatna,
zawroty, sinica, omdlenie → STOP, pozycja półsiedząca, 112.""",
    "f-5": """# F.5. Przeciwwskazania do hydro- i fizykoterapii

**Ciepło (parafina, IR, okłady):** ostry stan zapalny, gorączka, krwawienia,
nowotwór w obszarze, zaburzenia czucia (oparzenie!), niewydolność serca
(generalne kąpiele gorące), ciąża (jamа brzuszna), antykoagulacja (naczynia?),
zakrzepica, skóra uszkodzona.

**Zimno:** choroba Raynauda, pokrzywka zimowa, krioglobinemia, napad dny
moczanej (nasila), zaburzenia czucia, otwarte rany, nietolerancja.

**Hydroterapia naprzemienna/Kneipp:** ciężka miażdżyca, zakrzepowe zapalenie
żył, niewydolność serca, nadciśnienie nieuregulowane, epilepsja (zimno
gwałtowne), otwarte rany w wodzie.

**UV:** fotoudulenie (leki: doksycyklina, diuretytia tiazydowe, retinoidy,
hiperycyna!), bielactwo (ryzyko), przebyte nowotwory skóry, xeroderma
pigmentosum, choroby autoimmunologiczne (toczeń — BEZWZGLĘDNIE).

**TENS/ultradźwięki/prądy:** rozrusznik serca/implant (elektrody nie wokół!),
ciąza (brzuch/lędźwie), region tarczycy (karotyk sinus), nowotwór w obszarze,
epilepsja (głowa), rany/ropnie, metalowe implanty (US nad nimi ostrożnie).""",
    "f-6": """# F.6. Przeciwwskazania do fitoterapii

1. **Ciąża i karmienie:** bez ziół o działaniu estrogennym/wywołującym skurcze (piołun, ruta, anyż gwiaździsty duże dawki, siemię w dużych ilościach, lukrecja), aloes sok (antrachinony), czarna cohosh; wiele ziół = brak badań — zasada ostrożności.
2. **Dzieci:** mięta pieprzowa/eukaliptus/kamfora < 6 lat (ryzyko skurczu krtani), kwas acetylosalicylowy zawarty w kwiatach? (ogólnie: ASA nie dziecim), lukrecja — hipertensja, senos/liście senna — odwodnienie.
3. **Interakcje lekowe** (tabela A.9): dziurawiec (CYP3A4/P-gp — setki leków!), miłorząb + antykoagulanty, żen-szeń + warfaryna/insulina, potasowe zioła (pokrzywa, mniszek) + ACE-I/spironolakton (hiperkaliemia).
4. **Choroby:** nefropatia — unikać ziół z arbutiną? (ostrożeń: żółty kapsy? ) → ogólnie: przy chorobie nerek unikać dużych dawek potasu, oksalanów (szczaw, rabarbar), ziół «diuretycznych» bez kontroli; choroba wątroby — kava, żywotnik, pieprz afrykański, napar z szałwii duże ilości; hiperbilirubinia.
5. **Alergia krzyżowa:** Asteraceae (rumianek, arnika, krwawnik) przy alergii na bylicę/chryzantemę; pyłki brzozy → jabłko/marchew zioła?
6. **Zabiegi chirurgiczne w planie:** odstaw zioła wpływające na krzepnięcie i glikemię 2 tyg. przed (dziurawiec, czosnek, imbir, kurkuma, miłorząb, chamomile duże dawki).
7. **Surowce toksyczne:** napar z nasienników? → absolutny zakaz: tojad, konwalia (glikozydy), bieluń, wroniec, napar z pestek moreli/cyjanidry; «zioła» z nieznanego źródła — metale ciężkie, pestycydy, adulteracja.

**Zasada nadrzędna:** fitoterapia wspomaga, nie zastępuje leczenia; przy braku
dowodów — informuj pacjenta wprost.""",
    "f-7": """# F.7. Przeciwwskazania do masażu powłok brzusznych

**Bezwzględne:** ostry brzuch (zapalenie wyrostka, otrzewnej, perforacja —
napięcie obronne, rebound tenderness → 112/SOR), przepuklina nieoperowana
wcielona (ryzyko uwięźnięcia), ciąża (zwłaszcza I trym., powikłana — łyżeczka
krwawienia), miesiączka bardzo obfita/bólowa (endometrioza rzut), krwawienie
z przewodu pokarmowego (smoliste stolce), kamica żółciowa/moczowa w kolce,
ropień/ropień jajnika, nowotwór jamy brzusznej bez zgody onkologa, okres
pooperacyjny brzucha (< 6–8 tyg. lub bez zgody chirurga), tętniak aorty
brzusznej (> 3 cm — pulsujący guz! → lekarz).

**Względne:** IBS z biegunką (łagodne głaskanie wg kierunku okrężnicy),
zaparcia czynnościowe (masaż wskazany — ale wyklucz przyczyny organiczne:
utrata masy, krew w stolcu → kolonoskopia za zleceniem lekarza), przepuklina
operowana (blizna > 6 tyg., techniki bez głębokiego rozcierania), RZS/jelitowe
choroby zapalne w rzucie (Crohn, WZWG — nawrotowy ból → gastrolog).

**Technika bezpieczna:** głaskanie zgodne z perystaltyką (zgodnie z ruchem
wskazówek zegara), delikatne rozcieranie fałdu, NIGDY głębokie ugniatanie
na linii białej/pępek; pytanie o komfort co 1–2 min.""",
    "f-8": """# F.8. Przeciwwskazania względne — modyfikacje

Zasada: przy przeciwwskazaniu względnym zabieg MOŻE być wykonany po ocenie
ryzyka, z modyfikacją siły/czasu/obszaru i z zapisem w karcie.

| Stan | Modyfikacja |
|---|---|
| Ciąża prawidłowa | pozycja boczna/półsiedząca, bez głębokiego lędźwi/brzucha, aromatoterapia ostrożna, skrócony czas |
| Antykoagulanty | mniejsza siła, bez oklepywań i baniek, obserwacja siniaków |
| Osteoporoza | bez rozcierania na żebrach/wyrostkach, trening oporowy adaptowany |
| Cukrzyca | kontrola glikemii przed, buty/osłony stóp, unikaj ucisku miejsc niedoczuliczych |
| Nadciśnienie wyrównane | brak Valsalvy, unikaj pozycji head-down długo, spokojne tempo |
| Żylaki | tylko głaskanie odpływowe, bez pracy na żyłach, kompresjoterapia konsultowana |
| Epilepsja | unikaj silnych wibracji/głośnych bodźców, nie zostawiaj samej w wodzie |
| Choroby skóry łuszczycowej/atopowej (remisja) | emolienty zamiast olejków drażniących, bez tarcia ognisk |
| Pacyjent w trakcie chemio/radioterapii | opinia onkologa; skóra i płytki (< 50 G/l krwawienie) decydują |
| Wieku podeszły, kruchość | krótsze partie, częstsze zmiany pozycji, termoregulacja (zimno!) |

Każdorazowo: dokumentuj decyzję i uzyskaną zgodę (C.8).""",
}

# ---------------------------------------------------------------------------
# ZAŁĄCZNIK G — Mapy i schematy anatomiczne
# ---------------------------------------------------------------------------
G_MAPS = {
    "g-1": """# G.1. Układ mięśniowy — mapa funkcjonalna terapeuty

Warstwy i kierunki włókien (mapy rysuj kredką na wydrukowanym szkielecie):

- **Grzbiet — warstwa powierzchowna:** czworoboczny (kresa potyliczna → obojczyk → wyrostki kolczyste Th1–Th12), najszerszy grzbietu (miednica/Th7–L3 → kość ramienna), dźwigacz łopatki (C1–C4 → kąt górny łopatki).
- **Grzbiet — warstwa głęboka:** prostowniki grzbietu przykręgosłupowo (multifidus, longissimus, iliocostalis), trójkąt nerki (granice: XII żebro, prostownik grzbietu, mięsień biodrowo-żebrowy).
- **Tułów przód:** prosty brzucha (linia biała), skośne zewnętrzne (kierunek „do kieszeni”) i wewnętrzne (przeciwny), przepona (przyczepy żebrowo-lędźwiowo-mostkowe; unerwienie C3–C5).
- **Kończyna dolna:** pośladkowy wielki/średni, czworogłowy (vastus lateralis/medialis/intermedius + rectus femoris), dwugłowy uda, półbłoniasty/półścięgnisty, trójgłowy łydki (gastrocnemius + soleus), piszczelowy przedni, strzałkowe, grupa podeszwowa.
- **Kończyna górna:** naramienny, piersiowy większy/mniejszy, dwugłowy/trójgłowy ramienia, przedziały zginaczy i prostowników przedramienia, obręcz: zębaty przedni, równoległoboczne.

Na mapie zapisuj przy każdym mięśniu: początek, przyczep, funkcję i unerwienie
segmentarne — to podstawa masażu segmentarnego i planowania treningu.
""",
    "g-2": """# G.2. Układ limfatyczny — mapa odpływów

Trzy filary mapy (rysuj na sylwetce przedniej i tylnej):

1. **Zbiornik mlecz (ductus thoracicus)** — odprowadza chłonkę z całej dolnej połowy ciała + lewej górnej do połączenia żyły podobojczykowej i wewnętrznej szyjnej (lewy kąt żylny); prawa strona głowy/szyi/ramienia → ductus lymphaticus dexter.
2. **Główne grupy węzłów:** podbródkowe i szyjne (powierzchowne i głębokie, łańcuch wzdłuż żyły szyjnej wewnętrznej), nadobojczykowe (węzeł Virchowa — powiększony = pilna diagnostyka lekarska!), pachowe (poziomy I–III), łokciowe, pachwinowe (grupa pozioma i pionowa; granica: więzadło pachwinowe), podkolanowe, okołoaortalne i trzewne (głębokie — nieosiągalne manualnie).
3. **Pola odpływu:** kończyna dolna przednio-przyśrodkowo → pachwina powierzchowna; tylna boczna → węzły podkolanowe → głębokie → biodrowe; tułów przód → pachowe; tułów tył → pachwinowe lub krzyżowe; szyja → szyjne.

Na mapie zaznacz kierunki «strzałek odpływu» — wyznaczają one kolejność
drenażu i głaskania masażu klasycznego (zawsze obwodowo → centralnie).""",
    "g-3": """# G.3. Punkty spustowe (trigger points) — mapy Travell & Simons

Najczęstsze zespoły bólowe regionalne (opis lokalizacji + rzutowanie bólu):

- **Czworoboczny (upper trap):** TrP nad barkiem — ból karku, głowy skroniowej, ograniczenie rotacji szyi.
- **Dźwigacz łopatki:** przyczep poprzeczne C1–C4 — ból potylicy, «sztywny kark».
- **Równoległoboczny mniejszy:** przyśrodkowy brzeg łopatki — ból między łopatkami, rzut do ramienia.
- **Najszerszy grzbietu:** boczna powierzchnia tułowia — ból rzutowany w dół ku barkowi przy ramieniu odwiedzionym.
- **Gruszkowaty (piriformis):** przez większy otwór kulszowy — rzut po bocznej stronie uda (pseudorwa kulszowa; różnicuj z dyskopatią L5/S1 → neurolog).
- **Pośladkowy średni/mały:** ból boczny biodra, rzut do kolana.
- **Czworogłowy (vastus lateralis/medialis):** ból przedniej strony kolana, uczucie «puszczania» nogi.
- **Piszczelowy przedni / strzałkowe:** ból goleni, rzut do grzbietu stopy (mylić z rwą!).
- **Trójgłowy łydki:** ból łydki i pięty, rzut na podeszwę.
- **Żwacz / skrzydłowy boczny:** ból stawu skroniowo-żuchwowego, zębów, głowy.

Mapy rysuj na sylwetkach (ból rzutowany cieniowaniem). Technika: ucisk ischemiczny
≤ 90 s, rozciąganie ze sprayem (technika dla wykwalifikowanych), PIR.
Ostrzeżenie: punkty spustowe mięśnia mostkowo-obojczykowo-sutkowego — nigdy
nie pracuj głęboko w pobliżu tętnicy szyjnej i zatoki szyjnej!""",
    "g-4": """# G.4. Strefy odruchowe Heada i Mackenziego

Mapa segmentów rdzeniowych → narządy (rytuj na kręgosłupie i tułowie):

| Segment | Narządy/rejon odruchu |
|---|---|
| C3–C5 | przepona, szyja |
| Th1–Th5 | serce, płuca, tarczyca, oskrzela, nadnercza (górne) |
| Th5–Th9 | żołądek, wątroba, pęcherzyk, trzustka, dwunastnica |
| Th9–Th12 | jelito cienkie, kręte, nerki (górny moczowód) |
| L1–L3 | jelito grube, moczowód, jądro/jajnik (część), powłoki dolnego brzucha |
| L4–L5 | pęcherz, macica, odbytnica (część), kończyny dolne |
| S2–S4 | pęcherz (odpływ), cewka, odbytnica, genitalia, dno miednicy |

Wykorzystanie mapy: identyfikacja punktów maksymalnej bolesności w masażu
segmentarnym (B.3) oraz OBSERWACJA. Pamiętaj: opasający ból jednego pasa
z pęcherzykami → półpasiec → lekarz; ból zamostkowy promieniujący do żuchwy
lub ramienia → podejrzenie zespołu wieńcowego → lekarz, nie masaż.""",
    "g-5": """# G.5. Unerwienie segmentarne narządów wewnętrznych

Schemat trzewnej nerwowości (rysuj dwie linie: wsp. i przywsp.):

- **Współczulne (thorakolumbalne):** jądra boczne rogów Th1–L2 → pień współczulny → sploty trzewne (serce Th1–Th5; płuca Th2–Th7; trzewa jamy brzusznej splot trzewny Th5–L2; miednica L1–L2). Efekt «walcz»: tachykardia, zahamowanie perystaltyki, rozszerzenie źrenic.
- **Przywspółczulne (czaszo-krzyżowe):** nerw błędny X (serce, płuca, przewód pokarmowy do zgięcia lewego okrężnicy) + nerwy miedniczne S2–S4 (jelito grube dystalne, pęcherz, narządy rodne) — efekt «odpoczynek i trawienie».
- **Sploty:** aortalny, trzewne głębokie (Solar — «mózg brzuszny»), podbrzuszne górne/dolne, splot krzyżowy.

Znaczenie praktyczne: stymulacja tonusu nerwu błędnego (spokojny oddech
z długim wydechem, śpiew, delikatna praca okolic szyi) — dowody rozwijające
się, efekt relaksacyjny prawdopodobny; przy kołataniach serca lub napadach
nadciśnienia → zawsze lekarz.""",
    "g-6": """# G.6. Meridiany i punkty akupunkturowe (orientacyjnie)

Mapa 12 meridianów podstawowych + 2 naczyń (Ren/Du Mai) wg WHO standard
lokalizacji punktów (cun-miara własna dłoni pacjenta):

- **Ren Mai (VC)** — linia pośrodkowa przodu: VC6 Qihai, VC4 Guanyuan, VC12 Zhongwan (okolica żołądka), VC17 Danzhong (okolica serca).
- **Du Mai (GV)** — linia pośrodkowa tyłu: GV20 Baihui (ciemieniuszko), GV14 Dazhui (poniżej C7).
- Przykładypowszechnie stosowane punktów kończynowych: LI4 Hegu (grzbiet dłoni, przestrzeń między I a II kością śródręcza — ból głowy; tradycyjnie unikać w ciąży), ST36 Zusanli (poniżej guzowatości piszczeli — zmęczenie, przewód pokarmowy), SP6 Sanyinjiao (4 cun powyżej szczytu kostki przyśrodkowej — ginekologia; ciąża ostrożnie), LV3 Taichong (grzbiet stopy), GB20 Fengchi (dołek pod potylicą), BL23 Shenshu (przykręgosłupowo L1), PC6 Neiguan (2 cun ponad stawem nadgarstkowym — nudności: najlepiej udokumentowany!).

**Stanowisko kursu:** akupresura łagodzi nudności (PC6 — dane dobre) i może
zmniejszać ból (dane umiarkowane); akupunktura sucha — niewielki, ale statystycznie
istotny efekt swoisty w bólu przewlekłym (Cochrane). Ten poziom niepewności
przekazujesz pacjentowi uczciwie. Przekłucie skóry igłą — wyłącznie osoby z
uprawnieniami medycznymi!""",
    "g-7": """# G.7. Refleksologia — mapy stóp i dłoni

Standaryzowane mapy (rysuj na konturze stopy prawej/lewej i dłoni):

- **Kolejność organów na stopie (pięta→palce):** okrężnica (pas poprzeczny śródstopia), nerka (centrum podeszwy, około 1/3), moczowód (linia od nerki do pęcherza — przyśrodkowo), pęcherz (przy kostce przyśrodkowej), macica/prostata (pięta przyśrodkowo), nadnercza (nad nerkami), splot słoneczny (centrum, poniżej łuku), głowa/szyja (paluchy i palce II–V), zatoki (opalce), kręgosłup (przyśrodkowa krawędź stopy od pięty do palucha).
- **Dłoń:** analogicznie, mniejsza powierzchnia — alternatywa przy nadwrażliwości stóp (cukrzyca! neuropatia — ostrożnie, bez bólu).

Technika: «walking thumb» — krok kciukiem po strefie, 3 powtórzenia na strefę,
zabieg 30–45 min. Dowody: efekt relaksacyjny;
brak wiarygodnych dowodów na leczenie chorób trzewnych — komunikuj to
pacjentowi uczciwie. Przeciwwskazania miejscowe: zakrzepica żył głębokich,
owrzodzenia i zakażenia stóp; ciąża — tradycyjna ostrożność przy strefach
miednicy i dolnej części brzucha.""",
    "g-8": """# G.8. Punkty maksymalne w masażu segmentarnym

Mapa punktów palpacyjnych wg Zborowskiego (segment → miejsce):

- Serce: Th1–Th5 przykręgosłupowo + strefa przedsercowa (żeber IV–VI lewostronnie).
- Płuca: Th1–Th7 przykręgosłupowo + okolica międzyłopatkowa.
- Przepona: Th8–Th9.
- Żołądek: Th6–Th10 przykręgosłupowo lewostronnie + epigastrium.
- Wątroba/pęcherzyk: Th8–Th11 prawostronnie + prawe podżebrze.
- Jelito cienkie: Th9–Th12 około pępka; jelito grube: L1–L3 + pasy okrężnicy.
- Nerki: Th12–L2 «trójkąt nerki» (kąt między XII żebrem a kręgosłupem) + punkty Costescu? (bocznie L1–L3).
- Pęcherz/moczowody: L1–L2 + S2–S4 nad spojeniem łonowym.
- Genitalia: L5–S2 + pachwina (węzły!).

Objawy: wzrost napięcia mięśniowego (wałki przykręgosłupowe), fałd skórny,
bolesność punktowa, «gorący/gorzej» odczuć pacjenta. Rysuj mapę na plecach
modela markerem zmywalnym jako ćwiczenie praktyczne.""",
    "g-9": """# G.9. Pozycje drenażowe w chorobach płuc

Rysunki pozycji (kąt łóżka/poduszki, czas 20–30 min, 2–3×/dobę, przed posiłkiem):

1. **Płat górny** — pozycja siedząca pochylona do przodu (lub leżenie na plecach z poduszką pod udami 15°? standard: półsiedząc) — drenaż do oskrzeli głównych.
2. **Płat środkowy/język** — leżenie tyłem, uniesienie boków tułowia? → pozycja: leżenie na zdrowym boku, łóżko uniesione 20–30°, poduszka pod klatkęstrona.
3. **Płat dolny segmenty apikalne** — leżenie przodem z miednicą wyżej niż głowa (Trendelenburg odwrócony 20–30°), poduszka pod brzuchem.
4. **Płat dolny bazalne** — leżenie tyłem, nogi powyżej poziomu głowy (poduszki pod golenie, 30°).

Po każdej pozycji: klepanie/fistaszting? → perkusja dłonią lejkowatą nad
danym polem płucnym (z dala od kręgosłupa i sutków), następnie kaszel kontrolowany
(huffing). Astma/POChP: pozycje + oddech z oporem wydechu. Przeciwwskazania:
krwioplucie, ostre zapalenie opłucnej, niewydolność serca, niedawne
operacje/thorax → lekarz.""",
    "g-10": """# G.10. Schematy masażu w jednostkach chorobowych

Indeks map poglądowych (link do Załącznika H — tam pełne schematy):

- H.1 RZS — masaż rozluźniający proximalnych grup, unikanie stawów zajętych w rzucie.
- H.2 ZZSK — grzbiet prostowniczy + klatka piersiowa (oddech żeberkowy), mobilizacja th/lumb.
- H.4 Dyskopatia/rwa — segmenty L2–S1, pośladkowe, tył uda (bez bólu korzeniowego!).
- H.5 Bark zamrożony — okolica łopatkowa + deltoid, kapsuła — tylko w zakresie bezbolesnym.
- H.6 Astma/POChP — Th1–Th7, międzyżebrza, przepona (oddechowe).
- H.7 Serce (po zawale, w rehabilitacji) — Th1–Th5 łagodnie, kończyny odpływowo (wg kardiologa fazy).
- H.8 Naczyń obwodowych — Buerger+Ratschow? → ćwiczenia, masaż tylko odpływowy przy żylakach powierzchownych.
- H.10 Porażenie połowicze — strona porażona: głaskanie + rozcieranie (tonus↓), strona zdrowa normalnie; pozycjonowanie przeciw przykurczom.
- H.11 Brzuch (zaparcia czynnościowe) — głaskanie wg okrężnicy + segmenty L1–L3.
- H.15 Wady postawy — nierównowaga mięśniowa: rozluźnić skrócone, trenować osłabione (mapa + I.8).

Każdy schemat rysuj na sylwetce: strzałki kierunków, obszary zakazane (✗),
parametry (min/intensywność).""",
}

# ---------------------------------------------------------------------------
# ZAŁĄCZNIK H — Schematy masażu leczniczego (Zborowski)
# ---------------------------------------------------------------------------
H_SCHEMES = {
    "h-1": """# H.1. Reumatoidalne zapalenie stawów (RZS) — schemat masażu

**Faza:** tylko remisja/małej aktywności (CRP/OB, ocena lekarza). W rzucie
ostrym — zabroniony masaż stawów zajętych; dopuszczalne głaskanie odpływowe
kończyn i masaż karku relaksacyjny.

**Cel:** zmniejszenie napięcia mięśni przykurczowych, zachowanie ROM, redukcja
zmęczenia i bólu (efekt objawowy, nie «przeciwwrzodowy»).

**Program (30–40 min, 2–3×/tydz.):**
1. Grzbiet: głaskanie → rozcieranie międzyłopatkowe → ugniatanie czworobocznego i prostowników (bez wyrostków!) 10 min.
2. Kończyny górne: głaskanie odpływowe, rozcieranie okolicy barku/ramienia, DELIKATNE ugniatanie przedramion; stawy ręki — tylko głaskanie, bez oklepywania.
3. Kończyny dolne: głaskanie, ugniatanie uda/podudzia (bez dołu podkolanowego głęboko), łydka.
4. Oddech przeponowy + relaksacja 5 min.

**Zakazy:** gorączka, świeże deformacje, osteoporoza wtórna (sterydy!) — brak
oklepywań kręgosłupa i żebra; ucisk na ścięgna w miejscu zapalenia (risk
zerwania — np. ścięgna prostowników palców!).

**Współpraca:** reumatolog, fizjoterapeuta (szyny, ćwiczenia I.1), ocena
dysfunkcji AHQ/HAQ.""",
    "h-2": """# H.2. Zesztywniające zapalenie stawów kręgosłupa (ZZSK)

**Cel:** utrzymania prostości kręgosłupa i ruchomości klatki piersiowej,
opóźnienie ankylozy pozycyjnej (wspomagająco do leków i ćwiczeń!).

**Program (35–45 min, 3–5×/tydz. z ćwiczeniami I.2):**
1. Leżenie przodem (poduszka pod biodra dla lordozy): głaskanie grzbietu → rozcieranie wałów przykręgosłupowych Th/L → ugniatanie prostowników grzbietu (równomiernie obustronnie) → wibracja.
2. Klatka piersiowa: rozcieranie międzyżebrzy + oddech torowy oporowany (ręka terapeuty na żebrach), rozciąganie mięśni piersiowych (leżenie tyłem, ramię odwiedzione 90°, 3×30 s).
3. Szyja: głaskanie i rozcieranie karku, dźwigacza, potylicy; ROTACJE BIERNE ZAKAZANE przy zaawansowanej chorobie (ryzyko niestabilności C1–C2 → lekarz).
4. Biodra/kolana: masaży odpływowe, PIR zginaczy biodra (pozycja półleżąca).

**Pozycjonowanie:** spanie na twardym materacu, poduszka niska, 2×/dzień
leżenie tyłem 10 min. Red flag: nagły ból kręgosłupa po urazie nawet
minimalnym → RTG (złamanie «chalk-stick»!).""",
    "h-3": """# H.3. Choroba zwyrodnieniowa kręgosłupa (degeneracja dysku/spondyloza)

**Cel:** zmniejszenie napięcia ochronnego przykręgosłupowego, poprawa
krążenia miejscowego, edukacja ergonomiczna.

**Program (30 min, 2–3×/tydz.):**
1. Głaskanie grzbietu (brzuch? nie) — rozgrzewka 3 min.
2. Rozcieranie wałów przykręgosłupowych Th/L (palce/opuszki, ruchy okrężne, NIGDY na wyrostkach kolczystych).
3. Ugniatanie czworobocznego lędźwiowego i pośladkowych (promieniowanie «rzekome» bez korzeniowego → można).
4. Mobilizacje łagodne: miednica «wahadło» w leżeniu z ugiętymi kolanami; PIR prostownika grzbietu w pozycji siedzącej.
5. Zakończenie: pozycja odciążająca (leżenie tyłem, podudzia na krześle 90/90) 5 min.

**Kryteria odstąpienia:** objawy korzeniowe (parestezje dermatomalne, osłabienie
mięśni, dodatni Lasègue) → neurolog/ortopeda; zespół ogona końskiego
(zaburzenia czucia siodłowego, nietrzymanie pęcherza) → SOR NATYCHMIAST.""",
    "h-4": """# H.4. Dyskopatia i rwa kulszowa (ischialgia korzeniowa)

**Fazy i postępowanie:**

1. **Faza ostra (dzień 1–7):** masaż LEKKO, poza obszarem bólu: kończyna dolna głaskanie odpływowe + ugniatanie uda (tolerowane), grzbiet Thczęść rozcieranie łagodne; pozycje odciążające (leżenie z podudzi na krześle, «90-90»), chód krótki częsty; LEKI i decyzje — lekarz.
2. **Faza podostra:** segmenty L2–S1 masaż przykręgosłupowy umiarkowany, pośladkowy średni i gruszkowaty (test! pseudorwa vs. korzeń), tył uda i podudzie (bez prowokacji bólu korzeniowego > 3/10).
3. **Profilaktyka nawrotów:** trening mięśni głębokich (brzuch «drawing-in», multitify? → prostowniki), ergonomia dźwigania, ćwiczenia McKenzie'ego (extension prone press-ups — wg odpowiedzi directional preference), I.4? → I.8/postawa.

**Czerwone flagi (bezwzględny zakaz zabiegu, lekarz/SOR):** postępujące
osłabienie (opadanie stopy), zanik zwieracza/czucie siodłowe, zatrzymanie
moczu, gorączka + ból kręgosłupa (ropień/kręgowe zapalenie), nowotwór w
wywiadzie + nocny ból nieustępujący.""",
    "h-5": """# H.5. Zespół bolesnego barku (PHS, impingement, zamrożony bark)

**Rozróżnienie praktyczne (obserwacja, nie diagnoza):** ból przy abdukcji 60–120°
(arc pain) → impingement; ROM bierny ≈ czynny ograniczony globalnie + ból
nocny → adhesive capsulitis (zamrożony) — często cukrzyca! → endokrynolog/ortopeda.

**Program masażu (25–35 min):**
1. Okolica łopatki: rozcieranie równoległobocznych, podgrzebieniowy, obły (rotatory — stabilizacja!).
2. Czworoboczny górny + dźwigacz łopatki (korekcja «uniesionego barku»).
3. Naramienny — ugniatanie częściowe; biceps — bruzda dwugłowa delikatnie (ścięgno long head — tendinopatia: PIR + ekscentryka).
4. Klatka piersiowa mniejsza/większa: rozluźnianie (tor neutralny, ramię 90° abduction? łagodnie).
5. Mobilizacje łagodne: glide łopatki, trakcja ramienia w tolerancji; ĆWICZENIA: pendulum Codmana (3×/dzień 30 s), ściana «chodzenie palcami», rotacje z gumą (faza późna).

**Zasada:** ból ≤ 3/10 w trakcie i ≤ 24 h po; faza «zamrożona» — NIE forsować
torebki; faza « descongelamento » — więcej mobilizacji; ocena: Ortho? skorzysta
fizjoterapeuta.""",
    "h-6": """# H.6. Choroby dróg oddechowych (astma, POChP, przewlekłe zapalenie oskrzeli)

**Cel:** obniżenie napięcia mięśni oddechowych dodatkowych, udrożnienie
sekretem (drenaż), lęk-relaks (astma!).

**Program (25–30 min, 1–2×/tydz., poza napadem):**
1. Grzbiet Th1–Th7: głaskanie → rozcieranie przykręgosłupowe → ugniatanie równoległobocznych i prostowników.
2. Międzyżebrza: rozcieranie poprzeczne od kręgosłupa do mostka (wydech!), oddech z oporem wydechu (usta spięte).
3. Klatka przód: rozcieranie mięśni piersiowych (leżenie, ramię odwiedzione), mostek — głaskanie «down»; drenaż wibracyjny (fistaszing dłonią lejkowatą, 1–2 min/kwadrant, pozycje G.9).
4. Przepona: delikatne rozcieranie pod żebrami na wydechu (Costa angle), oddech przeponowy.

**Zakazy:** napad astmy, gorączka/ropa (ropnie płuc!), krwioplucie, odma
przemienna, niewydolność oddechowa Decompensata → lekarz. Inhalacje/leki —
zgodnie z planem medycznym pacjenta (astma: kontroler vs. reliever — edukacja!).""",
    "h-7": """# H.7. Choroby serca (choroba niedokrwienna, stan po zawale — fazy rehabilitacji)

**Zasada nadrzędna:** masaż i trening WYŁĄCZNIE w porozumieniu z kardiologiem
(faza II/III rehabilitacji; faza I — szpitalna, poza nami).

**Program fazy podostrej/III (20–30 min, siła 1–2/5):**
1. Głaskanie odpływowe kończyn górnych i dolnych (profilaktyka zakrzepicy, obciążenie serca minimalne).
2. Grzbiet Th1–Th5: ROZCIERANIE POWIERZCHOWNE wałów przykręgosłupowych, bez oklepywań i głębokiego ugniatania.
3. Kark i barki: rozluźnianie (napięcie «sercowe» rzutowane do żuchwy/ramienia — różnicuj z anginą wysiłkową! ból zależny od wysiłku → lekarz).
4. Oddech przeponowy + relaksacja (wpływ na tonus przywspółczulny — dowody umiarkowane).

**Przerwać natychmiast:** ból zamostkowy, duszność, poty, nudności, arytmia
subiektywna → pozycja półsiedząca, 112. Zakaz: masażu w decompensacji,
swieżego ZSC (< 4–6 tyg. bez zgody), RR ≥ 180/110, tętniaka, ostrego zapalenia
osierdzia.""",
    "h-8": """# H.8. Choroby naczyń obwodowych (żylaki, choroba tętnic obwodowych PAD)

**Żylaki/pochlebne niewydolność żylna:**
- Wolno: głaskanie odpływowe nogi (stopa→kolano→pachwina), rozcieranie UDА (nie na żylakach!), drenaż «pompowanie» mięśni łydki? → ćwiczenia: wspięcia na palce 3×20, chód; pończochy kompresji II (flebolog!).
- Zakaz: głębokiego ugniatania przebiegów żył, oklepywań, baniek, ciepła (kąpiele gorące — poszerzenie żył).

**PAD (chromienie tętnicze):**
- Masaz TYLKO łagodny, głaskanie; NIE masować «na siłę» niedokrwionej kończyny (ból spoczynkowy, zimna stopa, brak wyczuwalnego tętna → ANGIOLOG PILNE).
- Ćwiczenia Buergera-Ratschowa (I.7) w tolerancji: 3 cykle dziennie, «spacer do bólu → odpoczynek» program nadzorowany — złoty standard zachowawczy.
- Edukacja: rzucenie palenia (decydujące!), pielęgnacja stóp (cukrzyk — podolog), leki (statyny, antyagreganty — lekarz).

**Czerwona flaga:** nagle blada, zimna, bolesna kończyna + brak tętna → OSTRY
ZATOR → 112/SOR (minuty liczą się dla kończyny).""",
    "h-9": """# H.9. Porażenia nerwów obwodowych (n. promieniowy, pośrodkowy, łokciowy, strzałkowy)

**Kontekst:** rozpoznanie i kwalifikacja (EMG!) — lekarz neurolog; my wspieramy
rehabilitację w fazie regeneracji/odnerwienia.

**Postępowanie wspomagające:**
1. Pielęgnacja kończyny: ROM bierny 2–3×/dzień (zapobiega przykurczom i
   ZSR — complex regional pain syndrome), pozycjonowanie (deska n. promieniowy
   — «drop wrist»: unieruchomienie zgięcia grzbietowego za zgodą terapeuty).
2. Masaż: głaskanie odpływowe całej kończyny; ugniatanie mięśni zachowanych
   (np. przy porażeniu n. strzałkowego — trójgłowy łydki, piszczelowy tylny);
   okolica porażona — tylko delikatne rozcieranie + TENS? (neuromuskularny
   EMS tylko pod nadzorem fizjoterapeuty/neurologa!).
3. Czucie: desensytyzacja (różne faktury) przy przeczulicy; ostrożność z
   ciepłem/zimnem w obszarze niedoczulicy (oparzenie!).
4. Funkcja: ćwiczenia kompensacyjne + ADL (uchwyty, łyżka pogrubiona).

**Alarm:** nagłe wieloobjawowe porażenia, opadanie powieki/diplopia, zaburzenia
mowy → udar/GBС → 112.""",
    "h-10": """# H.10. Porażenie połowicze (stan po udarze mózgu)

**Fazy (wg lekarza/rehabilitanta):** ostra — szpital; podostała — rehab
intensywna; przewlekła — our support.

**Program wspomagający (30–40 min, codziennie w domu, instruktaż rodziny):**
1. Głowa/szyja: głaskanie, rozcieranie karku strony NIEporażonej (kompensacyjne napięcie), delikatnie strona porażona (skóra wrażliwa!).
2. Ramię porażone: PODPARCIE (nie ciągnąć za ramię — ryzyko bolesnego podwichnięcia!); głaskanie + rozcieranie łopatki, barku; pozycja leżąca: ramię odwiedzione 30–40°, zgięte łokieć, dłoń otwarta (poduszka).
3. Tułów: rozcieranie boczne strony porażonej (asymetria postawy), mobilizacja łopatki.
4. Noga: głaskanie odpływowe (profilaktyka DVT!), rozcieranie uda, PIR zginaczy biodra i trójgłowego łydki (przykurz szpotawy → stopa opadająca — ortez AFO, fizjoterapeuta).
5. Tonowanie: techniki Bobath? → NDT-Bobath tylko certyfikowani; my: układanie, dotyk, propriocepcja, ćwiczenia bilateralne.

**Zasady bezpieczeństwa:** spastyczność — unikać bólu i szybkich ruchów
(pobudzają); półsiedzenie z podparciem; padaczka pourazowa? pourdarowa —
limit bodźców; depresja poudarowa (skala) → psychiatra/lekarz.""",
    "h-11": """# H.11. Choroby przewodu pokarmowego (zaparcia czynnościowe, IBS, refluks)

**IBS/zaparcia (po wykluczeniu alarmowych — lekarz!):**
1. Brzuch: głaskanie zgodne z okrężnicą (coesum→ascendens→transversum→descendens→sigmoid) 5 min, rozcieranie wałka esicy (LEWO podbrzusze), ugniatanie mięśni skośnych.
2. Segmenty: Th9–L3 przykręgosłupowo (jelita), rozcieranie fałdów.
3. Oddech przeponowy (masaż trzewny przywspółczulny!), relaksacja (oś mózgowo-jelitowa — dowody: hipnoterapia i CBMT skuteczne → kieruj do psychologa/terapeuty).
4. Dieta: błonnik rozpuszczalny (babka płesznik — udowodnione w IBS-B? raczej błonnik rozpuszczalny psyllium), low-FODMAP 4–6 tyg. TYLKO z dietetykiem (eliminacja nie na zawsze!).

**Refluks (NERD):** NIE masuj głęboko nadbrzusza po posiłku; pozycja półsiedząca,
dieta (małe porcje, wieczór bez tłuszczu, kofeiny), leki IPP — lekarz;
brak «cudownych ziół» (gojnik? — ograniczone dane).

**Alarm:** smoliste stolce/krew, chudnięcie, disfagia, niedokrwistość, wiek
> 50 nowe objawy → gastrolog (kolonoskopia zlecenie)!""",
    "h-12": """# H.12. Choroby układu moczowego (ZUM nawracające, nietrzymanie moczu, kamica)

**ZUM niepowikłane (kobiety):** leczenie antybiotykiem — lekarz; prewencja:
nawodnienie 1,5–2 l/d, oddawanie moczu po stosunku, żurawina large trials —
dowody słabe (uczciwie powiedz); masaż wspomagający: Th12–L2 + S2–S4
przykręgosłupowo łagodnie, brzuch głaskanie; ciepło (kąpiel) na ból pęcherza
— objawowo.

**Nietrzymanie moczu (stress/urge):**
1. Mięśnie dna miednicy: trening Kegla — instruktaż (skurcz 3 × 10/dzień, «zatrzymaj strumień» NIE jako ćwiczenie — tylko test świadomości!), biofeedback u fizjoterapeuty uroginekologicznego (złoto standard).
2. Pęcherz: bladder drill (trening rozstępu), kofeina limit.
3. Masaż: rozluźnienie dna miednicy? — tylko trained therapist (internal techniques — poza naszym zakresem bez uprawnień!).

**Kolka nerkowa:** NIE masuj okolicy nerki w ataku (Th12–L2 tylko głaskanie
dystansowo), ciepło miejscowe + leki — lekarz/SOR (gorączka + kamica =
urolog natychmiast, sepsa!).

**Białkomocz/NS:** nefrolog, masaż odpływowy kończyn obrzękowych łagodnie.""",
    "h-13": """# H.13. Choroby kobiecych narządów płciowych (dysmenorea, endometrioza, PMK)

**Dysmenorea czynnościowa (po wykluczeniu wtórnej — ginekolog):**
- Program: głaskanie podbrzusza (ruchy poprzeczne, ciepłe dłonie), rozcieranie L1–S2 przykręgosłupowo + krzyżowo (energia «dolnego grzbietu»), ugniatanie mięśni skośnych brzucha (łagodne), pozycja dziecka (balasana) + oddech.
- Dowody: ciepło miejscowe działa (metaanalizy), TENS transcutaneous — skuteczny; akupunktura/akupresura SP6 — umiarkowane dane; zioła: pieprz? → majeranek/koper (tradycyjne, słabe dane), ew. NLPZ — lekarz/farmaceuta.
- Trening dna miednicy + aerobic exercise 3×/tydz. — zmniejszają nasilenie (dobre dowody).

**Endometrioza:** multidyscyplinarnie (ginekolog, ból — specjalista); masaż
RELAKSACYJNY grzbietu/miednicy w tolerancji, unikać głębokiej pracy w rzucie
bólu; psychologia (ból przewlekły), dieta przeciwzapalna jako wsparcie (omega-3
dane obiecujące).

**PMK:** ruch + sen + CBT; wapń/magnez/wit. B6 — dane mieszane (uczciwie);
kalcycyt? → nie obiecuj.

**Ciąża podejrzenie:** brak masażu brzucha/lędźwi głębokiego, krwawienie/ból →
położna/lekarz.""",
    "h-14": """# H.14. Stany po urazach (złamienia gojące, skręcenia, szwy po operacjach)

**Zasada:** zgoda lekarza prowadzącego/fizjoterapeuty na każdym etapie;
harmonogram biologiczny:

1. **Unieruchomiony segment:** NIE masować okolicy złamania; masuj PROXIMAL i DISTAL (głaskanie odpływowe, utrzymanie krążenia, DVT profilaktyka), counterpart contralateralny (efekt «cross-education» — trening siły strony zdrowej).
2. **Po zdjęciu unieruchomienia:** ROM bierny→czynny, głaskanie + rozcieranie delikatne blizny (po 6 tyg.? dopiero po zagojeniu; masaż blizny: poprzeczne rozcieranie, plastrowanie? — fizjo), obrzęk — drenaż (B.4).
3. **Skręcenie stawu skokowego (ostre):** zasada POLICE (protect, optimal loading, ice 10–15 min ×3/d, compression, elevation) — masaż odpływowy stopy/goleni poza obszarem więzadeł; po 72 h — rozcieranie obwodowe.
4. **Szwy/blizny operacyjne:** masaż blizny od 6. tyg. (miękka tkanka), techniki rozluźniania zrostów; przeciwwskazane: infekcja rany, dehiscencja.

**Alarm:** ból nieproporcjonalny, zimna/blada kończyna (zespół ciasnoty!),
nasilenie obrzęku + ból łydki (DVT) → SOR.""",
    "h-15": """# H.15. Wady postawy (plecy okrągłe, lordoza, kifolordoza, scoliosis)

**Ocena (nasza, obserwacyjna):** fotografia boczna/przód, Adams forward bend
(kąt garbu — escoliosis > 5–7° → ortopeda, RTG Cobbs angle), plumb-line,
ROM, test Thomasa (flexor hip), płaszczyzny barków/miednicy.

**Program wspomagający (masaż + ćwiczenia I.8):**
1. Rozluźnić skrócone: pectoralis (rozcieranie + rozciąganie drzwiowe), prostownik grzbietu górny (Th kyphosis — rozcieranie wałów), zginacze biodra (Thomas stretch 3×30 s), czworoboczny górny/dźwigacz (kark).
2. Wzmocnić osłabione (trening, nie masaż): rhomboids/mid-trap (wiosłowanie, face-pull), deep neck flexors (chin tuck 3×10), glutes (mostek), core (dead bug, bird dog).
3. Nawyki: ergonomia biurka (monitor eye-level, mikro-pery co 30 min), plecak dwuramienny, sen na boku z poduszką międzybiodrową.

**Scoliosis:** masaż strony wypukłej (napięta) rozluźniająco, wklęsłej —
łagodnie stymulująco; CHURSCHT? → ćwiczenia korekcyjne specjaliści (orthota
Milwaukee/Boston — ortopeda). Red flag: ból nocny + skolioza progresywna
dorosłego → obrazowanie (nowotwór?)/lekarz.""",
}

# ---------------------------------------------------------------------------
# ZAŁĄCZNIK I — Kinezyterapia (ćwiczenia)
# ---------------------------------------------------------------------------
I_EX = {
    "i-1": """# I.1. Ćwiczenia w RZS — okresy I–IV

**Okres I (rzut ostry):** UNIERUCHOMIENIE funkcjonalne wg lekarza/szpyny;
nasze: izometryczne napięcia mięśni zdrowych partii (5 s × 10, 2×/dzień),
oddech przeponowy, pozycje przeciw przykurczom (rękaw? kolano prostowane
20 min kilka razy/dzień).

**Okres II (wygasanie):** ruchy bierne-czynne w odciążeniu (w wodzie 34–36 °C!
basen — dowody: zmniejszenie bólu i aktywności choroby), ROM 2×/dzień,
stabilizacja proximalna (łopatka, miednica).

**Okres III (remisja):** wzmacnianie: opór gumowy niski, 2–3×/tydz., izolacja
stawów zajętych (uchwyty pogrubione, łyżki adaptacyjne); aerobik nisko-uderzeniowy
(rower, spacer, aqua) 3×20 min; równowaga.

**Okres IV (utrzymanie):** trening siłowy umiarkowany (metaanalizy: BEZPIECZNY
i skuteczny w RZS — nie «rusza choroby»), aktywność życiowa, superwizja
reumatologiczna (DMARDs adherence).

**Zasada:** ból ≤ 3/10 w trakcie, powrót do baseline ≤ 2 h po.""",
    "i-2": """# I.2. Ćwiczenia w ZZSK (Bekhterew)

Codzienny blok 20–30 min (dowody: aktywność = najlepsza prewencja deformacji):

1. **Kręgosłup:** chin tuck + retrakcja (3×10), extension prone press-up (McKenzie, 10 powt. 3×/dzień — toleruj), «cat-cow» ćw. kot-krówka (10 powt.).
2. **Klatka piersiowa:** rozciąganie drzwiowe (3×30 s), oddech głęboki z oporem (metry? inspirator SMRTH? — inspiratory muscle training dane pozytywne), rotation seated (bez bólu).
3. **Biodra:** mostek 3×12, clamshell z gumą 3×15, zginacz — wykrok stretch 3×30 s/stronę.
4. **Szyja:** retrakcja + rotacje czynne (BIERNE manipulacje ZAKAZANE — niestabilność C-spine!).
5. **Aerobik:** pływanie (grzbiet! styl dowolny; motylek ostrożnie), rower stacjonarny pozycja wyprostowana, taniec/chód marszowy 30 min 3–5×/tydz.
6. **Pozycjonowanie:** materac twardy, poduszka niska, 2×/dzień prone-on-elbows 2–5 min (przeciw kyphozie szyjnej).

**Farmako kontekst:** biologiczne (anti-TNF) pozwalają aktywniejszy trening;
aktywna choroba + ból ostry — zmniejsz intensywność, nie rezygnuj (consensus ASAS/EULAR).""",
    "i-3": """# I.3. Ćwiczenia po zawale serca (fazy rehabilitacji kardiologicznej)

**Faza I (szpital, dni 1–7) — nie nasza rola; opis dla świadomości.**
**Faza II (ambulatoryjna, tyg. 2–12, pod nadzorem):** spacer interwałowy:
5 min rozgrzewki → 20–30 min marsz RPE 11–13 (talk test) → 5 min cool-down;
3–5×/tydz.; ćwiczenia małych grup (zgięcia kończyn bez obciążenia, oddech).
**Faza III (podtrzymanie, mies. 3–6+):**
- Cardio: 30–40 min umiarkowanie (40–70 % HRR Karvonen) 5×/tydz. + 2×/tydz. interwały (30 s szybciej/60 s wolniej ×6–10) wg tolerancji.
- Siła: 2×/tydz., 8–12 RM, duże grupy, BEZ Valsalvy (wydech na wysiłek), bez ćwiczeń nad głową ciężko.
- Elastyczność + oddech.

**Kryteria stopu (ACSM):** ból/clenched jaw, duszność ≥ 7/10, zawrót,
arytmia, spadek SBP > 10 mmHg przy wzroście workload → STOP, lekarz.
Kontrola: echo EF, próba wysiłkowa co etap, leki (beta-blokery — HRmax
obniżona! używaj RPE). Profilaktyka wtórna: rzucenie palenia, lipidogram,
cukier, sen (bezdech? → polisomnografia).""",
    "i-4": """# I.4. Ćwiczenia w astmie i POChP

**Astma (kontrolowana — PEF dzienniczek!):**
- Rozgrzewka 10–15 min (zapobiega EIB — exercise-induced bronchoconstriction); interwałowy wysiłek lepiej tolerowany niż ciągły; pływanie chlor? — somewrażliwy; nose breathing + warm humid air; leki reliever przed wysiłkiem wg planu lekarza.
- Trening mięśni oddechowych IMT (30 cmH₂O, 2×30 oddechów/dzień) — dowody: ↓ duszność.
- Oddech pursed-lips + przeponowy (technika «wdychaj nosem 2s, wydech przez zaciśnięte usta 4s»).

**POChP (stabilna, GOLD faza rehab):**
- Pulmonary rehab program: 6–8 tyg., 2–3×/tydz.: rower/ marsz interwałowy (ERG 60–75 % max workload), siła kończyn 2×/tyg. (quads, arms — arm ergometer!), edukacja energetyczna (pacing).
- Pursed-lips podczas wysiłku; pozycje odpoczynku (tripod leaning).
- Tlenoterapia — tylko zlecenie lekarza (SpO₂ < 88 %); trening z tlenu przepływowego.

**Zakaz:** świeża zaostrzenie (exacerbation), krwioplucie, odma → lekarz.""",
    "i-5": """# I.5. Ćwiczenia po udarze (neurorehabilitacja wspomagająca)

**Zasady:** neuroplastyczność — powtarzalność (setki repetycji/dzień),
specyfika zadań (task-oriented), intensywność; koordynacja z fizjoterapeutą
NDT/Bobath/PNF (certyfikowani).

**Blok domowy (2×/dzień po 20–30 min, rodzic/instruktor asystuje):**
1. Pozycjonowanie (przeciw przykurczom): ramię odwiedzione na poduszce, dłoń otwarta, stopa 90° (orteza AFO nocna?).
2. Aktywacja asymetryczna: weight-shift siedząc (przenoszenie na stronę porażoną 3×10), unoszenie miednicy (bridge), «table-top» reach.
3. Góra kończyna: assisted movement (ręka zdrowa prowadzi porażoną — ideokinetic), mirror therapy (lustro 30 min/dzień — dowody RCT: ból fantomowy/ROM), czynnościami (serwetki, kubki — adaptacja uchwytu).
4. Chód: wstawanie sit-to-stand 3×10, marsz z asekuracją (rollator/rama), step-y na schodku; równowaga stojąca eyes-open→closed.
5. Bezpieczeństwo: porażona strona NIGDY nie ciągniemy za ramię; upadki — mata, osoba asystująca; depresja poudarowa — screening → lekarz.

**Fatigue pourazowy/pouder:** pacing (praca 20 min/odpoczynek 10), sen,
aerobic umiarkowany 3×/tydz. (dowody: zmniejsza zmęczenie).""",
    "i-6": """# I.6. Ćwiczenia Frenkela (zaburzenia równowagi — móżdżkowe/przedsionkowe)

Protokół Frenkela (klasyczny, 5-stopniowy; dobowo 2–3 bloki po 15–20 min,
ASEKURACJA — osoba lub poręcz!):

1. Leżenie: zgięcia/prostowanie kończyn, «nożyce», krążenia ramion, unoszenie wyprostowanej nogi (3–5 powt., tempo wolne).
2. Siedzenie: warianty ćwiczeń leżących + dotykanie kolan, wahadło; równowaga siedząca (oczy otwarte→zamknięte).
3. Stanie: ciężar przenoszenie bocznie/przód-tył, stopy razem, potem tandem (stań na linii), oczy otwarte→zamknięte.
4. Chodzenie: po linii prostej, z zatrzymaniami, skrętami na «stop», po obwodzie koła, w tył.
5. Ćwiczenia złożone: marsz z zadaniem poznawczym (podwójne zadanie), chód nerwowy (heel-toe), schody.

**Przedsionkowe dodatkowe (BPPV po manewrach lekarza — Epley; vestib habituation):**
gaze stabilization (X1/X2), head turns while walking — przez fizjoterapeutę
vestibular-trained.

**Czerwone flagi:** nagły vertigo + diplopia/dysarthria/dysfagia/ataksja
(new DEFIICITS) → UDER tylnego dołu → 112.""",
    "i-7": """# I.7. Ćwiczenia Buergera i Ratschowa (niedokrwienie obwodowe, żylaki profilaktyka)

**Buerger-Allen (niedokrwienie tętnicze — PAD Fontaine II; konsultacja
angiologa!):** 3×/dzień po 10 min:
1. Leżenie, nogi w górze 90° (na ścianie/poduszkach) 1–2 min — bladość → odczekać.
2. Siedzenie, nogi swobodnie w dół 2–3 min — przekrwienie (czerwoność) — norma.
3. Leżenie poziomo 5 min + aktywność: zgięcia grzbietowe/podeszwowe stóp, krążenia, zaciskanie pięści — 2–3 min.
Cykl powtórz 2–3×. Mechanizm: «pompowanie» + autoregulacja; dowody umiarkowane,
bezpieczne.

**Ratschow (venous insufficiency / profilaktyka zakrzepicy):**
- Leżenie wysoko nogi, «jazda na niewidzialnym rowerze» pionowo (pedaling w powietrzu) 2–5 min ×3/dzień; napinanie i rozluźnianie łydek.
- Wspięcia na palce stojąc 3×20, «skurcze-ćwiczenia» łydki (muscle pump).

**Zakaz:** świeża zakrzepica (DVT — leczenie, potem po zgodzie), tętniak,
niewydolność serca (pozycja head-down!), rany otwarte.""",
    "i-8": """# I.8. Ćwiczenia w wadach postawy (kifolordoza, plecy okrągłe, scoliosis)

**Blok codzienny 15–20 min (Schroth-inspired + siła core):**

1. **Otwarcie klatki:** doorway pec stretch 3×30 s; foam-extension thoracic (wałek pod Th7–Th12, ramiona za głowę, wydech) 10 powt.
2. **Deep neck flexor:** chin tuck supine 3×10 (5 s hold).
3. **Core:** dead bug 3×8/stronę, bird dog 3×8, side plank kolana 3×20 s.
4. **Glute/hip:** mostek jednonóż 3×10, clamshell guma 3×15, martwy «bird» (extension hips) 3×10.
5. **Scoliosis (konkrawna strona):** korekcyjne oddech «rotational angular breathing» — tylko pod okiem Schroth-therapist; ogólne: symetryczne wzmacnianie + unikanie asymetrycznych przeciążeń (torebka na jedno ramię!).
6. **Nawyki:** microbreaks co 30 min (standing, shoulder circles), monitor eye level, telefon na wysokości oczu.

**Ocena postępów:** zdjęcie boczne co 8 tyg., kąt Adamsa, SRT (surface
rotation), subiektywny ból. Progresja wad strukturalnych → ortopeda (RTG).""",
    "i-9": """# I.9. Ćwiczenia w wadach stóp (płaskostopie, hallux valgus, ostroga piętowa)

**Płaskostopie poprzeczne/podłużne (dorosły — elastyczne!):**
- Short foot exercise (skrócenie stopy bez zginania palców) 3×10 2×/dzień;
- unoszenie palców / zginanie (toe yoga), «zbieranie ręcznika» palcami;
- wzmacnianie tibialis posterior: eversion z gumą 3×15;
- łydka: ekscentryczne wspięcia ze schodka 3×15 (ostroga/plantar fasciitis — protokół Rathleff/Rudavsky: 3×12 raz/dzień, 12 tyg. — dowody dobre);
- obuwie szerokie, wkładki pronacyjne — ortopeda/podolog.

**Hallux valgus:** separacja palców (toe spreader) 10 min/dzień, krótki
skurcz (short foot), mobilizacja I MPF (terapeuta), BUTY: nosek szeroki,
obcas < 3 cm; ból + zapalenie kaletki → ortopeda (korekcja operacyjna opcja).

**Ostroga/pięta:** rozciąganie rozcięgna podeszwowego ( piłeczka zamrożona
roll 5 min 2×/dzień), łydka stretch 3×30 s, night splint? → ortopeda;
fala uderzeniowa ESWT — placówka medyczna.

**Stopa cukrzycowa:** NIE lecz sam! Codzienna oględziny, podolog, obuwie
ortopedyczne; rana → lekarz (osteomyelitis risk).""",
    "i-10": """# I.10. Trening medyczny w geriatrii (sarkopenia, równowaga, funkcjonalność)

**Program (Sundhed? → standard: Otago + resistance wg ACSM senior):**

1. **Siła 2–3×/tydz.:** 8–10 ćwiczeń dużych grup (sit-to-stand, wall push-up, seated row guma, hip abduction standing, calf raise, farmer carry lekkie hantle 1–3 kg), 2–3 serie × 10–15, RPE 5–7/10.
2. **Równowaga 3×/tydz.:** tandem stand 3×30 s, single-leg stance z podparciem 3×20 s/stronę, chód heel-toe po linii, «turn around» slalom, Tai Chi 12-Forms 2×/tydz. (dowody: −30 % upadków).
3. **Cardio:** marsz 3×20–30 min/tydz. (talk test), rower recumbent, aqua.
4. **Funkcjonalność:** wstawanie z krzesła bez rąk, sięganie półki, noszenie zakupów (carry tasks), siad-wstanie schody.
5. **Zasady:** rozgrzewka 10 min, nawodnienie, pora lekka (nie zaraz po insulinie?), ocena wzroku/słuchu (środowisko), leki (beta-blokery — RPE zamiast HR; diuretyki — potas/nawodnienie).

**Screening przed:** TUG (Time Up & Go > 12 s → ryzyko upadku, fizjo), MMSE
(cooperacja), ból spoczynkowy, ciśnienie leżąc/stojąc (orthostaza!).
Cel: niezależność funkcjonalna i upadki-prewencja — mierz Outcomes: SPPB, 30-s
chair stand.""",
}

# ---------------------------------------------------------------------------
# ZAŁĄCZNIK J — Coaching i mentoring
# ---------------------------------------------------------------------------
J_COACH = {
    "j-1": """# J.1. Struktura sesji coachingu zdrowotnego — model GROW

Pełny scenariusz 45-minutowej sesji (do przećwiczenia w parach — B.13):

1. **Opening/contracting (5 min):** powitanie, cel sesji w jednym zdaniu pacjenta, przypomnienie granic («nie jestem lekarzem, nie radzę medycznie»).
2. **Goal (10 min):** «Co chciałbyś osiągnąć do końca współpracy?»; skalowanie wartości (0–10 «jak ważne?»); cel SMART na dziś.
3. **Reality (12 min):** «Jak jest teraz? Co próbowałeś? Co pomogło choć trochę?»; słuchanie aktywne (parafraza, odzwierciedlenie emocji), pytania otwarte (CO/JAK, dlaczego→ostrożnie, bo oceniająco brzmi).
4. **Options (12 min):** «Co jeszcze mogłoby zadziałać?» — brainstorming bez ocen, pomysły pacjenta najpierw; zasoby (kto, co, gdzie pomoże); kryteria wyboru (skala pewności 0–10).
5. **Will (5 min):** konkretne działanie SMART + pierwszy krok w 48 h; «co może przeszkodzić?» — plan if-then (implementation intentions — Sheeran metaanalizy: efekt umiarkowany).
6. **Closing (1 min):** podsumowanie słowami pacjenta, data kontroli.

**Narzędzia uzupełniające:** koło życia zdrowia, «best possible self», ważenie
pros/cons (decisional balance z TM).""",
    "j-2": """# J.2. Kwestionariusz wywiadu coachingowego

Struktura (wypełnij z pacjentem, nie «za» niego):

**A. Styl życia (snapshot):** sen (godziny, jakość, ekrany), aktywność (typ/
min/tydz. — IPAQ short), odżywianie (warzywa/owoce porcje/dzień, alkohol
jednostki/tydz., palenie PY), praca/stres (ocena 0–10), relacje/spiritualność.
**B. Zdrowie:** rozpoznania lekarskie, leki (lista!), ostatnie badania,
hospitalizacje, ból (VAS, lokalizacja), NOP.
**C. Cele i wartości:** «Co daje ci energię?», «Jak chcesz, aby wyglądało twoje
zdrowie za rok?», ranking wartości (zdrowie vs. kariera vs. rodzina…).
**D. Gotowość do zmiany (TM):** etap: prekontemplacja/kontemplacja/przygotowanie/
działanie/utrzymanie; pewność 0–10, ważność 0–10, «co podniosło pewność o 1 punkt?»
**E. Bariery i zasoby:** «co najbardziej przeszkadza?», «kto wspiera?»,
«co już działa?»
**F. Preferencje współpracy:** forma kontaktu, częstotliwość, język (metafory,
humor), granice intymności.

**Etyka:** poufność (RODO), dane tylko niezbędne, wgląd pacjenta na żądanie.""",
    "j-3": """# J.3. Plan zmiany zachowań zdrowotnych — wzór

```
PLAN ZMIANY ZACHOWAŃ              klient: ........   data: .....   review: .....
CEL (SMART): ....................................................................
DLACZEGO TO WAŻNE (własnymi słowami): .........................................
ETAП GOTOWOŚCI (TM): [ ]K [ ]P [ ]Pr [ ]D [ ]U   pewność ../10  ważność ../10
OPERACJE (konkretne działania):
 1) ............... kiedy/częstość: ......... wyzwalacz (cue): .............
 2) ............... .......................................................
 3) ............... .......................................................
PLAN IF–THEN (przeszkody): «Jeśli ..., wtedy ...» ×3:
 1) Jeśli pada deszcz, wtedy 15 min wideo-aerobiku w salonie.
 2) Jeśli ... wtedy ...
 3) Jeśli ... wtedy ...
NAGRODA/FEEDBACK (natychmiastowy): .............. (nie «self-punishment»)
WSPIERACZE: osoba ......... aplikacja/dziennik ......... środowisko (kupić
 buty? ustawić rower przy drzwiach?) .........
PUNKTY KONTROLI: co .... dni; metryka: ......... ( kroki/dzień, porcje warzyw,
 min aktywności, sen)
PLAN BAWOŁA (jeśli 2× z rzędu brak realizacji): [ ] zmniejszyć próg (mniejszy
 krok) [ ] zmienić cue [ ] dodać partnera [ ] wrócić do etapu poprzedniego.
Podpis klienta: ............ Coach: ............""",
    "j-4": """# J.4. Dziennik zdrowia pacjenta — wzór

```
DZIENNIK ZDROWIA        klient: ........   okres: ........
DZIENNIE (rubryka tygodniowa):
 · Sen: .... h, jakość 1–5: .. · Aktywność: typ .... min RPE ..
 · Posiłki: śniadanie/obiad/kolacja (opis + warzywa? porcja) · Woda: .. l
 · Ból/objawy: VAS .., lokalizacja .., trigger? ..
 · Nastrój/energia 1–5: .. · Stres 1–5: .. + technika użyta: ....
 · Alkohol: .. j. Papierosy: .. · Leki przyjęte: [ ]
 · Udane mikrozadania (co zrobiłem mimo trudności?): ..............
TYGODNIOWO:
 · Cel tygodnia: ......... realizacja %: ....
 · Największa przeszkoda: ......... co pomogło: .........
 · Jedna rzecz wdzięczności/ciała (positive embodiment): .........
MIESIĘCZNIE: waga/talia/RR (jeśli zalecono), przegląd celów, aktualizacja
planu zmiany (J.3).
ZASADA: dziennik służy klientowi (wgląd + dane do rozmowy), nie ocenie moralnej.
Dane wrażliwe — przechowywanie RODO-safe (papier w szafce / aplikacja szyfrowana).""",
    "j-5": """# J.5. Skala motywacji i gotowości do zmiany — narzędzia

1. **Termometr gotowości (0–10):** «Jak jesteś gotów zacząć?» + «dlaczego nie niżej?» (evokes change-talk — MI spirit).
2. **Balance sheet (decisional balance):** kolumny: korzyści zmiany / koszta zmiany / korzyści status quo / koszta status quo — wypełnia klient.
3. **Ring of readiness:** etapy TM z zadaniami coacha:
   - Prekontemplacja: informacja bez presji, budowanie relacji;
   - Kontemplacja: exploring ambivalencji (MI core: OARS — Open questions, Affirmations, Reflective listening, Summaries);
   - Przygotowanie: małe kroki, środowisko;
   - Działanie: plan + monitoring;
   - Utrzymanie: radzenie z lapsami (lapse ≠ relapse — normalizuj bez dramatu).
4. **Self-efficacy Bandura:** «Na ile jesteś pewien, że potrafisz …?» + mastery experiences (historyjne dowody «umiałem już…»).
5. **Intrinsic motivation (SDT):** autonomia (wybór klienta), kompetencja (małe zwycięstwa), relatedness (wsparcie społeczne) — projektuj sesję wokół tych trzech.

**Ostrzeżenie:** motywacja to stan, nie cecha; nie etykietuj «zdemotywowany».""",
    "j-6": """# J.6. Protokół mentoringu w chorobie przewlekłej

Model 6–12 spotkań (co 2–4 tyg., 45–60 min), pacjent: cukrzyca typu 2,
nadciśnienie, POChP, RZS…

1. **Spotkanie 1 — kontrakt i mapa choroby:** zrozumienie rozpoznania (własnymi słowami), leki (adherence bariery: cena? zapominalstwo? strach NOP?), cele pacjenta.
2. **Spotkanie 2 — samomonitoreng:** glucometer/BP domowy (technika pomiaru — demonstracja, powtórka), dziennik (J.4), «co oznaczają liczby — kiedy dzwonić do lekarza».
3. **Spotkanie 3 — żywienie:** 24-h recall, jeden cel wymiany (np. słodki napój → woda z cytryną), etykiety, gotowanie razem (kitchen lesson).
4. **Spotkanie 4 — ruch:** ocena barier, plan FITT (B.9), buty/ścieżka, «park walk» wspólny.
5. **Spotkanie 5 — stres/sen:** techniki oddechu/relaksu (B.8), higiena snu, granice pracy.
6. **Spotkanie 6 — system opieki:** przygotowanie pytań do lekarza, koordynacja (kto co bada kiedy), prawa pacjenta, skierowania (C.9).
7. **Kontrola co 3 miesiące:** przegląd celów, red flags, aktualizacja z lekarzem.

**Etyka mentoringu:** nie «naprawiam» pacjenta — idziemy razem; autonomia >
posłuszeństwo; przy depresji/lęku — psycholog/lekarz.""",
    "j-7": """# J.7. Protokół mentoringu opiekunów rodzinnych

Opiekun osoby zależnej (demencja, udar, choroba terminalna, niepełnosprawność):

1. **Potrzeby opiekuna (nie pacjenta!) — assessment:** czas opieki/dzień,
   obowiązki dodatkowe, sen, izolacja, finanse, poczucie winy.
2. **Edukacja praktyczna:** transfer osób (pivot, slide-board, «never pull
   axilla»), higiena i pielęgnacja (odleżyny — pozycje 2×/2 h, materac
   przeciwodleżynowy), karmienie (dysfagia — pozycja upright, konsystencje —
   logopeda), bezpieczeństwo domu (maty, poręcze, leki zamykane).
3. **Wsparcie psychospołeczne:** grupy opiekunów (Alzheimer Polska, hospicjum
   domowe), odciążenie respite (pomoc instytucjonalna), «maska tlenowa» —
   dbanie o siebie nie jest zdradą.
4. **Wypalenie opiekuna (Zarit Burden Interview screening):** objawy: chroniczny
   zmęczenie, cynizm, bezsenność → interwencja: delegowanie, granice,
   profesjonalista.
5. **Aspekty formalne:** ZUK zasiłek pielęgnacyjny, orzeczenia, OPW (opieka
   wytchnieniowa), hospicjum — informuj, nie załatwiaj.
6. **Komunikacja z osobą z demencją:** walidacja emocji (NICE: validation
   therapy), krótkie zdania, rutyna, zachowanie godności.

**Twoja rola:** mentoring i edukacja; kryzys psychiczny opiekuna → lekarz/psycholog.""",
    "j-8": """# J.8. Karta superwizji — wzór

```
KARTA SUPERWIZJI PRZYPADKU   coach/mentor: ........   superwizor: ........
data: ......   spotkanie nr: ......   forma: [ ]indywidualna [ ]grupowa
Opis przypadku (ANONIMIZACJA! inicjały, wiek zakres): .......................
Relacja: kontrakt, cele, transfer/przeciwtransfer (co czuję wobec klienta?):
Moje interwencje i efekty: .................................................
Wątpliwości/dylematy etyczne: .............................................
Granice kompetencji: czy coś powinno było trafić do lekarza/terapeuty? ....
Co chcę dostać od superwizji: [ ]perspektywa [ ]technika [ ]wsparcie [ ]etyka
Pytania do superwizora: 1) ........ 2) ........
Ustalenia/rozwoj: .........................................................
Zapis o zgodzie klienta na prezentację przypadku (anonim): [ ]tak [ ]nie
Podpisy: ................ / ................
SUPERWIZJA obowiązkowa: min. 1×/kwartał przy praktyce samodzielnej (standard
zawodowy ICF/PTE). Dbałość o klienta = dbałość o siebie i swój rozwój.""",
}

# ---------------------------------------------------------------------------
# ZAŁĄCZNIK K — Zabiegi felczerskie / cyruliczne (w granicach prawa)
# ---------------------------------------------------------------------------
K_CIRR = {
    "k-1": """# K.1. Historia cyrulika i felczera — kontekst zawodu

Cyrulik (barber-surgeon) i felczer (chirurg polowy) byli przodkami chirurgii:
golili, puszkowali krew, nastawiali kości, leczyli rany (np. «świąty opatrunek»
Ambrożego Paré). W Polsce XVII–XVIII w. felczerei podlegali Trybunałowi
Medycznemu; w XIX w. zawód zanikł wobec rozwoju medycyny uniwersyteckiej.

**Współcześnie:** «zabiegi felczerskie» w ofercie usługowej mogą obejmować
TYLKO czynności pielęgnacyjne i relaksacyjne niesięgające do tkanek żywych
poniżej naskórka oraz niebędące świadczeniem zdrowicznym w rozumieniu ustawy
o działalności leczniczej. Nastawianie złamań, puszczanie krwi, nacinanie
ropni, «leczenie» chorób — są CZYNAMI MEDYCZNYMI i wykonanie ich bez uprawnień
grozi odpowiedzialnością karną (art. 58–59 ustawy o zawodach lekarza… + art.
65 KW) i cywilną.

**Etos, który przekazujemy:** historyczna ciekawość + nowoczesna pokora
wobec kompetencji — «nie szkodzić» jest ważniejsze niż «wyglądać na wszechmocnego».""",
    "k-2": """# K.2. Higiena i aseptyka w usługach cyrulicznych

Standard gabinetu usługowego (Sanepid, RODO, BHP):

1. **Ręce:** mycie 30 s + dezynfekcja (alkoholowy preparat, EN1500) przed i po KAŻDYM kliencie; rękawiczki nitinolowe? → nitrylowe jednorazowe przy kontakcie ze skórą zmienioną.
2. **Pole zabiegu:** skóra czysta, sucha; dezynfekcja pola (oktenidyna/chlorheksydyna 0,5–2 %) przy opatrunku drobnych ran.
3. **Narzędzia:** narzędzia jednorazowe (skalpele — ZAKAZ użycia w usługach; nożyczki do paznokci, frez podologiczny — sterylizacja autoklawem tylko przez wykwalifikowanych, dla nas: dezynfekcjawysoki poziom preparatem medycznym + wymienne końcówki).
4. **Tekstylia:** ręczniki/prześcieradła jednorazowe lub 60 °C+; fartuch czysty na zmianę.
5. **Odpady:** ostrza/igły → pojemnik UB (igloo); gazy z krwią → odpad medyczny (umowa z firmą utylizacyjną); chemia → segregacja.
6. **Dokumentacja:** lista środków dezynfekujących (poświadczenia, daty), harmonogram przeglądów, ewidencja wypadków ekspozycyjnych (ukłucie → PRM/wypadkowy).

**Umiejętność zaliczeniowa:** przeprowadzenie «audit higiene» własnego
stanowiska wg checklisty 20 punktów.""",
    "k-3": """# K.3. Opatrunki drobnych ran powierzchownych

Zakres usługowy: otarcia, pęknięcia, zadrapania bez cech zakażenia i bez
ryzyka głębszych struktur.

1. Ocena: czy rana wymaga lekarza? (głębokość > naskórek/skóra właściwa,
   rozstęp brzegów, ciało obce, ugryzienie, zanieczyszczenie glebą,
   krwawienie > 10 min ucisku, lokalizacja: oko/dłoń/staw, tetanus nieaktualny
   → lekarz/POZ!).
2. Irrygacja: sol fizjologiczna (NaCl 0,9 %, butelka jałowa) lub woda bieżąca
   pitna — ciśnienie strumienia usuwa bakterie; NIE wcierać mydła w ranę.
3. Dezynfekcja około-ranny: chlorheksydyna wodna; jodyna tylko okołorannie
   (nie na ranę otwartą — cytotoksiczna).
4. Opatrunek: gazik jałowy + plaster/przymocowanie; wilgotne gojenie (hydrożel
   + folia) dla otarć — mniej blizn; zmiana co 24–48 h lub gdy mokry.
5. Instrukcja domowa: nie moczyć dłużej, nie zrywać strupów, signs infection
   (narastający ból, ropa, czerwona pręga, gorączka) → lekarz.
6. Dokumentacja: karta C.12, zdjęcie za zgodą (RODO) dla przebiegu.

**Zakaz:** szycie ran, klejenie «na siłę» rozstępujących się, usuwanie głębokich
ciał obcych, «wypalanie» i «nakłuwanie».""",
    "k-4": """# K.4. Pielęgnacja stóp i keratoliza (współpraca z podologiem)

Usługowo wolno: moczenie, mechaniczne ścieranie HYPERKERATOZY MARTWEJ
(pemzka, frez ONLY trained podolog — my: pilnik jednorazowy), kremy z mocznikiem
10–40 % (keratolitycznie), plaście z kwasem salicylowym 40 % na odcisk
(okolice zdrowej skóry zabezpieczyć pastą cynkową!), skracanie paznokci na
prosto (wbrew «zaokrąglaniu» — zapobiega wrastaniu).

**Kategorycznie poza zakresem (kieruj do podologa/lekarza):**
- stopa cukrzycowa (każda zmiana = podolog + diabetolog; neuropatia/ischemia — ryzyko amputacji),
- wrastający palec z zapaleniem (partial nail avulsion — tylko lekarz/podolog),
- brodawki wirusowe (krioterapia/keratoliza — lekarz/podolog; rozróżnić z rogowaceniem),
- grzybica paznokci (leki — lekarz; «octowe» domowe — słabe dowody, informuj),
- rana/owrzodienie ANY.

**Edukacja:** skarpetki bawełniane, buty wentylowane, rotacja obuwia,
oględziny codzienne (lusterko/rodzina), sucho między palcami.""",
    "k-5": """# K.5. Technika płukania żołądka i lewatywy — HISTORYCZNIE i WSPÓŁCZEŚNIE

**Historycznie:** felczerwykonanieował płukanie («wlew doodbytniczy», «detoksykacja»)
przy zatruciach; aparatura: syfon, irygator Esmarcha.

**Współcześnie (Polska):** płukanie żołądka jest PROCEDURĄ MEDYCZNĄ ratunkową
(w zatruciach, w warunkach szpitalnych, z zabezpieczeniem dróg oddechowych) —
ZAKAZ wykonywania w gabinecie usługowym. Lewatywy oczyszczające «detoksykacyjne»
— medycznie zbędne i ryzykowne (elektrolity, perferacja przy patologii,
mikrobiom); «kawa» lewatywy (Gerson) — BRAK dowodów, opisywane przypadki
śmierci (hiponatremia, oparzenia) → nie oferuj.

**Co wolno usługowo:** edukacja o prawidłowej perystaltyce (woda, błonnik,
ruch, pozycja kuczna podnóżek), preparaty OTC (makrogol — dowody dobre;
farmaceuta/lekarz przy problemach przewlekłych), czopelek glicerynowy doraźnie.

**Red flags:** brak stolca + wymioty + brak gazów → niedrożność → SOR;
krwisty stolec/lewatywa krwista → lekarz natychmiast.""",
    "k-6": """# K.6. Technika nacięcia i drenażu ropnia — poza zakresem!

Nacięcie i drenaż (I&D) ropnia jest ŚWIADCZENIEM ZDROWOTNYM (chirurgicznym):
wymaga rozpoznania, znieczulenia, aseptyki operacyjnej, sometimes packing i
antybiotykoterapii. Wykonanie przez osobę nieuprawnioną = przekroczenie
uprawnień + zagrożenie życia (martwicze zapalenie powięzi, sepsa).

**Nasza rola (usługowa/edukacyjna):**
1. Rozpoznanie sytuacji: «gorący, czerwony, bolesny guz + fala dreszczy» → PILNE lekarz/SOR (chirurg).
2. Przed wizytą: ciepłe okłady 10–15 min ×3 (mogą «dojrzeć» — złagodzić), NIE выдавливать, NIE nakłuwać igłą «domowo».
3. Po leczeniu lekarskim — wsparcie: wymiana opatrunków (technika jałowa), obserwacja gojenia, edukacja higieny (MRSA: ręczniki osobne, pranie 60 °C).
4. Nawracające ropnie → immunolog/diabetolog (cukrzyca! hidradenitis suppurativa).

**Egzamin:** sytuacyjna decyzja «co robię w godzinie 20:00 u klienta z ropniem
pod pachą» → telefon do lekarza dyżurnego/SOR, nie «zabieg».""",
    "k-7": """# K.7. Bańki i «krwawe» praktyki — co jest dozwolone

**Bańki suche/ogniowe (usługa relaksacyjna):** ssanie umiarkowane, 5–10 min,
kierunek mięśni, nie na żylaki/znamię/brzuch w ciąży/twarz; «ślady» to
extravasat (wybroczyny), NIE «toksyny» — wyjaśniaj mit; przeciwwskazania:
antykoagulanty, trombocytopenia, skóra cienka/sucha, fever.

**Bańki «masujące» (moving cup):** tylko po naoliczeniu, ruch wolny, bez
kółek na wyrostkach — ślady łatwe do zrobienia, łatwo o uszkodzenie.

**Krwawe praktyki historyczne (upust, hirudoterapia «samodzielna»):**
- Puszczanie krwi — ZAKAZ (procedura medyczna, ryzyko krwawienia/infekcji).
- Hirudoterapia (pijawki medyczne) — WYŁĄCZNIE produkt leczniczy z hodowli medycznej, stosowany przez uprawnionych (lekarz/fizjoterapeuta? w PL — świadczenie zdrowotne); «pijawki z stawu» kupowane luzem — ryzyko zakażeń (Aeromonas!) i krwawień (antykoagulanty!) → nie oferuj.
- Mikroigły/skalpel kosmetyczny (dermapen «domowy») — przekracza naskórek: w PL interpretowane jako zabieg medyczny przy celach leczniczych; ryzyko blizn — nie podejmuj bez uprawnień.

**Stanowisko kursu:** piękno tradycji cyrulickiej zachowujemy w edukacji
historycznej i w bezpiecznych formach (bańki łagodne, opatrunki drobne).""",
    "k-8": """# K.8. Nastawianie złamań i «ludowa chirurgia» — granice

Historyczne felczerskie «nastawianie kości» dziś: repozycja złamań =
wyłącznie lekarz (RTG, znieczulenie, immobilizacja). Próby «nastawiania»
przez osoby nieuprawnione grożą: uszkodzeniem nerwów/naczyń, embolią tłuszczową,
złamaniem patologicznym (nowotwór!), śmiercią (miednica).

**Co wolno i trzeba umieć (pierwsza pomoc, B.15):**
1. Unieruchomienie «tak jak leży» (szyna air-cast, poduszka, peleryna — immobilizacja przed transportem), obejrzenie tętna/czucia distalnie PRZED i PO.
2. Zwichnięcie barku: nie nastawiać! — pozycja komfortowa (sling), SOR.
3. Krwotok: ucisk bezpośredni, opaska uciskowa, NIE «improwizowane turniquety» bez szkolenia (ratownicy: tak); zmiażdżenia — szpital.
4. Kleszcz «własnoręcznie»: usunięcie pęsetą przy skórze (chwycić przy głowie kleszcza, prosto, nie wykręcać) — OK; rumień > 5 cm / objawy grypopodobne → lekarz (borelioza: doksycyklina przepisuje lekarz).

**Egzamin:** case «babcia upadła, boli biodro, nie może wstać» → nie ruszać
(nie «rozmasować»), wezwać PRM, ciepło, spokój, dokumentacja zdarzenia.""",
    "k-9": """# K.9. Zabiegi «odgrzybiające» i «detoksykujące» — sceptycyzm i empatia

Pacjenci często proszą o: «czyszczenie wątroby» (oliwa + cytryny + «kamienie»),
「pasożyty — zioła」, 「odkwaszenie」, 「toksyny z baniek/plastra na stopę」.

**Fakty (prawda, którą mamy obowiązek szanować):**
- «Kamienie» z «wątróbki» to mydła oliwne (saponifikacja w jelitach, analiza pokazuje kwasy tłuszczowe + wapń).
- pH krwi jest buforowane (7,35–7,45); «dieta alkaliczna» nie zmienia pH krwi (moczu — tak, bez znaczenia klinicznego).
- Plastry « detox» ciemnieją od własnych ekstraktów roślinnych + wilgoci — nie od toksyn.
- Pasożyty: diagnoza w laboratorium (jaja/cysty w kale ×3, serologia) — leki (albendazol etc.) przepisuje lekarz; «anty-pasożytnicze» zioła ( piołun, czosnek, goździk) — słabe dowody, ryzyko (piołun — thujone, neurotoksyczny przy przedawkowaniu).

**Empatia (miłość bliźniego):** nie wyśmiewaj lęku i frustracji pacjenta;
powiedz: «rozumiem, że szukasz pomocy; proponuję, żebyśmy zrobili badania i
porozmawiali z lekarzem, a ja wesprę pana/panią dietą i ruchem, które realnie
obciążają wątrobę mniej». Oddziel potrzebę (ulgę) od mitu (metodę).

**Dokumentuj:** co odradzono i dlaczego (ochrona pacjenta i Twoja).""",
    "k-10": """# K.10. Algorytm BLS/AED — sekwencja czynności (ERC 2021)

Sekwencja pojedynczego ratownika (dorosły):

1. **Bezpieczeństwo sceny** (ruch, prąd, agresja) — ocena 5 s.
2. **Sprawdź przytomność:** potrząśnij, głośno: «Czy pan mnie słyszy?»
3. **Brak reakcji → wołaj pomoc:** «Ty! zadzwoń 112 i przynieś AED!» (wskaż osobę palcem), odkryj klatkę.
4. **Oddychanie:** drożne drogi (head tilt-chin lift; uraz? → jaw thrust), patrz-słuchaj-czuj ≤ 10 s. Brak/gasping → RRC.
5. **RRC 30:2:** kolana przy klatce, pięść na pięść środek mostka, łokcie proste, 5–6 cm, 100–120/min, pełna rekoil, przerwy < 10 s; ventilations po 30 uciśnięciach (1 s, widoczny rise). Sam bez sprzętu: continuous compressions.
6. **AED jak najszybciej:** włącz, elektrody (pod prawym obojczykiem, pod lewym pachowym bokiem), odsuń ludzi, ANALIZA (nie dotykać), SHOCK → natychmiast wznów RRC 2 min → kolejna analiza; pediatryczne elektrody/tryb child < 8 lat/25 kg.
7. **Zmiana co 2 min** (jeśli drugi ratownik), do przyjazdu PRM lub powrotu krążenia (normalny oddech + ruch + reakcja → pozycja boczna ustalona, monitoring oddechu co minutę).

**Zakrztuszenie przytomny:** 5 uderzeń w plechy (pochylonego) + 5 ucisków
nadbrzusza; nieprzytomny → RRC + zajrzenie do ust przed wentylacją.
**Praktyczny zaliczeniowy scenariusz:** manekin + AED szkoleniowy, ocena
jakości uciśnięć (feedback device).""",
}

ALL_APPENDIX_CONTENT = {
    "25-zalacznik-a-wykaz-lektur/book-01": A_BOOK,
    "26-zalacznik-b-umiejetnosci/book-01": B_SKILLS,
    "27-zalacznik-c-dokumentacja/book-01": C_FORMS,
    "30-zalacznik-f-przeciwwskazania/book-01": F_CONTRA,
    "31-zalacznik-g-mapy-anatomiczne/book-01": G_MAPS,
    "32-zalacznik-h-schematy-masazu/book-01": H_SCHEMES,
    "33-zalacznik-i-kinezyterapia/book-01": I_EX,
    "34-zalacznik-j-coachingu/book-01": J_COACH,
    "35-zalacznik-k-zabiegi-felczerskie/book-01": K_CIRR,
}


def norm_key(stem: str) -> str:
    # '01-a-1-podreczniki...' -> 'a-1'; '05-j-5-technika...' -> 'j-5' (fallback)
    m = re.match(r"^\d+-([a-k]-\d+)", stem.lower())
    if m:
        return m.group(1)
    m = re.match(r"^\d+-([a-k]\.\d+)", stem.lower())
    if m:
        return m.group(1).replace(".", "-")
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Wypełnianie rozdziałów book załączników A–K kursem naturopaty")
    ap.add_argument("--base", type=Path, default=DEFAULT_BASE)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    root = args.base if args.base.is_dir() else Path.cwd() / args.base
    sections = root / "sections"
    if not sections.is_dir():
        print(f"BLAD: brak katalogu {sections}", file=sys.stderr)
        return 2

    written = skipped_content = missing = 0
    for sec_book, mapping in ALL_APPENDIX_CONTENT.items():
        chdir = sections / sec_book / "chapters"
        if not chdir.is_dir():
            print(f"  BRAK KATALOGU: {chdir}")
            missing += 1
            continue
        used_keys = set()
        for ch in sorted(chdir.glob("*.md")):
            key = norm_key(ch.stem)
            text = ch.read_text(encoding="utf-8")
            if GENERIC_MARKER not in text:
                skipped_content += 1
                continue
            content = mapping.get(key)
            if not content:
                print(f"  POMINIETO (brak mapowania): {sec_book}/chapters/{ch.name}")
                missing += 1
                continue
            new_text = content.rstrip() + "\n\n" + ETHICS + "\n"
            written += 1
            used_keys.add(key)
            tag = "[DRY-RUN] " if args.dry_run else ""
            print(f"  {tag}UZUPUENIONO: {sec_book}/chapters/{ch.name} ({key})")
            if not args.dry_run:
                ch.write_text(new_text, encoding="utf-8")
        unused = set(mapping) - used_keys
        for u in sorted(unused):
            print(f"  UWAGA: treść '{u}' nie miała generycznego pliku-do-wypełnienia (sprawdź nazewnictwo)")

    print(f"\nPODSUMOWANIE: {'[DRY-RUN] ' if args.dry_run else ''}"
          f"wypełniono={written}, pominięto(mają treść)={skipped_content}, "
          f"braki/niezmapowane={missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
