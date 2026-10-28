#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rozbudowa załączników A–M kursu masażysty MED.10 (sekcja 12-zalaczniki).

Stan wejściowy: pliki label-*.md w sekcji 12-zalaczniki zawierają poprawne,
ale ogólnikowe szkielety — każdy podpunkt ma ten sam zdaniowy wypełniacz
(„Pozycja załącznika … — stosowana zgodnie z regulaminem kursu …”).
Walidator `validate_masaz_course.py` nie zgłasza błędów, jednak treść
wymaga rozbudowy, by załączniki były realnie użyteczne w gabinecie i na
zajęciach praktycznych.

Skrypt robi trzy rzeczy (wszystkie IDEMPOTENTNE):

 1. UZUPEŁNIA słownik pojęć (glossary-01/glossary.yaml) o nowe hasła —
    akapit „entries” jest źródłem haseł importowanych do Moodle jako
    osobna aktywność typu glossary. Istniejące hasła NIGDY nie są
    nadpisywane ani usuwane; dopisywane są tylko terminy, których jeszcze
    nie ma (porównanie wielkimi literami, bez znaków diakrytycznych).

 2. ROZBUDOWUJE każdy plik label-XX (załącznik A–M), dopisując na końcu
    konkretną, fachową treść merytoryczną dla każdego podpunktu danego
    załącznika (np. D.1 — lista przeciwwskazań do masażu klasycznego,
    J.6 — algorytm BLS osoby dorosłej 30:2 zgodny z wytycznymi ERC/PRR
    2021). Operacja append-only: szkielet ze spisu treści pozostaje
    nietknięty, a nowa sekcja nosi nagłówek „## Treść szczegółowa”.
    Jeśli taka sekcja już istnieje, skrypt jej NIE dopisuje ponownie.

 3. ODŚWIEŻA tabelę „Mapa plików załączników” w section.md sekcji 12,
    tak aby rozmiary plików odpowiadały stanowi po rozbudowie.

ŹRÓDŁO PRAWDY: struktura i tytuły podpunktów pobierane są BEZPOŚREDNIO
ze spisu treści `kurs_masazu.txt` przez parser `course_toc.py` — skrypt
nie wymyśla nowych numeracji ani nazw, jedynie realizuje merytorycznie
to, co spis już zawiera. Treści medyczne odpowiadają stanowi wiedzy
zgodnemu z podręcznikami wymienionymi w Załączniku L (Zborowski,
Bochenek, Traczyk) oraz wytycznym Polskiej Rady Resuscytacji / ERC
(2021) i przepisom prawa polskiego (Kodeks pracy, RODO, ustawa
o prawach pacjenta). Zasady etyczne: PRAWDA (żadnych fałszywych danych
medycznych; tam gdzie wymagana jest decyzja lekarza — wyraźnie to
stwierdzamy), PIĘKNO (życzliwy, przejrzysty język służby bliźniemu),
SPRAWIEDLIWOŚĆ (te same procedury dla wszystkich, jawność zasad).

Przed zapisem każdej zmiany zakładana jest kopia .bak (jeśli jeszcze
nie istnieje). Uruchomienie z --dry-run niczego nie zapisuje.

Użycie:
    python3 scripts/enrich_masaz_zalaczniki.py [--toc kurs_masazu.txt]
        [--base courses/03-kurs-masazysta-med10] [--dry-run] [--no-backup]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from course_toc import default_source, parse_course  # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover
    print("BRAK pyyaml — zainstaluj: pip install pyyaml")
    sys.exit(2)

BASE_REL = "courses/03-kurs-masazysta-med10"
MARKER = "## Treść szczegółowa"


# ---------------------------------------------------------------------------
# 1. NOWE HASŁA SŁOWNIKA (glossary) — prawdziwe definicje, zgodne z programem
# ---------------------------------------------------------------------------

NEW_GLOSSARY_TERMS: list[tuple[str, str]] = [
    ("MED.10",
     "Kwalifikacja wyodrębniona w zawodzie technika masażysta — „Świadczenie usług w zakresie masażu”. Jej posiadanie potwierdza egzamin okręgowej komisji egzaminacyjnej OKE."),
    ("Technika podstawowa masażu",
     "Cztery główne rodzaje ruchów masażu klasycznego: głaskanie, rozcieranie, ugniatanie i oklepywanie, uzupełnione o wibrację; każda ma własne wskazania, dawkowanie i kolejność w sekwencji zabiegu."),
    ("Masaż suchy",
     "Masaż wykonywany bez środków poślizgowych, np. przy pracy na tkance łącznej lub gdy preparat jest przeciwwskazany (zmiany skórne, alergia); wymaga szczególnej dbałości o technikę, by nie uszkodzić naskórka."),
    ("Masaż pośredni",
     "Masaż wykonywany przez materiał (ręcznik, gazę) albo z użyciem przyrządu — stosowany przy wrażliwej lub uszkodzonej skórze oraz w masażu przyrządowym."),
    ("Drenaż limfatyczny metodą Voddera",
     "Manualny drenaż limfatyczny oparty na powolnych, rytmicznych chwytach pompowych i kołowych, wykonywany w kierunku węzłów chłonnych; podstawowa metoda w leczeniu obrzęków limfatycznych."),
    ("Kompleksowa terapia przeciwobrzękowa (CDT)",
     "Łączenie drenażu limfatycznego, bandażowania kompresyjnego, pielęgnacji skóry i ćwiczeń — standard postępowania w obrzękach limfatycznych wtórnych, np. po leczeniu onkologicznym; wymaga zlecenia i nadzoru lekarza."),
    ("Faza niewydolności pompy żylnej",
     "Stan, w którym krążenie żylne i limfatyczne kończyny nie odprowadza prawidłowo krwi i chłonki — objawia się obrzękiem, uczuciem ciężkości; masaż wykonuje się wtedy wyłącznie delikatnie, zgodnie ze wskazaniami, omijając miejsca niewydolnych zastawek i żylaki."),
    ("Masaż łąkotkowy (okostnowy)",
     "Masaż działający na okostną i przegrody mięśniowe przez punktowy, wolno przesuwany ucisk; odczuwalny mocno, ale nie powinien powodować bólu promieniującego ani siniaków — dobiera go lekarz/fizjoterapeuta w określonych wskazaniach."),
    ("Refleksologia",
     "Metoda odruchowego oddziaływania na stopy (lub dłonie, twarz) poprzez ucisk określonych stref; jako masaż odruchowy klasyfikowana według dowodów naukowych jako wspomagająca relaks — nie leczy chorób i nie zastępuje diagnostyki medycznej."),
    ("Linia oddechowa (respiratory line)",
     "Praca z taśmą przednią ciała (stopy – uda – brzuch – przepona – klatka piersiowa – gardło – twarz) w masażu tensegracyjnym; służy wyrównaniu napięć powięzi i pogłębieniu oddechu."),
    ("Cykl treningowy (makro-, mezo-, mikrocykl)",
     "Struktura planowania obciążeń sportowych: makrocykl (sezon), mezoocykl (kilka tygodni), mikrocykl (tydzień); masaż sportowy dobiera się do fazy cyklu — przygotowawczej, startowej lub regeneracyjnej."),
    ("Masaż przedstartowy (rozgrzewający)",
     "Krótki, szybki masaż pobudzający wykonywany kilkanaście minut przed wysiłkiem; cel: zwiększyć temperaturę tkanek i gotowość neuromięśniową, bez głębokiego rozluźniania, które mogłoby obniżyć siłę mięśniową."),
    ("Masaż powysiłkowy (regeneracyjny)",
     "Masaż wykonany po wysiłku — najpierw delikatny odprowadzający, potem umiarkowanie pogłębiający; wspomaga usuwanie metabolitów i subiektywne zmniejszenie bolesności mięśni; nie zastępuje odpoczynku ani nawodnienia."),
    ("DOMS (opóźniona bolesność mięśniowa)",
     "Zespolona bolesność mięśni pojawiająca się 12–72 h po nietypowym lub intensywnym wysiłku; masaż łagodny może przynieść ulgę subiektywną, lecz unika się mocnych technik na silnie uszkodzony mięsień."),
    ("Shantala",
     "Tradycyjny indyjski masaż niemowląt rozpowszechniony przez F. Leboyera; wykonywany bardzo delikatnie, z olejkiem, w atmosferze spokoju; wspiera więź z opiekunem — nigdy nie wykonuje się go na dziecku chorym, gorączkującym ani bezpośrednio po karmieniu."),
    ("Kinezyterapia",
     "Leczenie ruchem: ćwiczenia bierne, czynno-bierne, czynne i oporowe; masażysta współpracuje z fizjoterapeutą, znając zasady kolejności zabiegów (np. masaż przed ćwiczeniami w celu przygotowania tkanek)."),
    ("Fizykoterapia",
     "Stosowanie bodźców fizycznych (ciepło, zimno, prąd, pole magnetyczne, światło, ultradźwięki); masażysta zna jej podstawy, by bezpiecznie planować sekwencję zabiegów i rozpoznać przeciwwskazania wspólne."),
    ("Elektroterapia",
     "Podgrupa fizykoterapii wykorzystująca prąd elektryczny (np. TENS — przezskórna stymulacja nerwów w celu złagodzenia bólu); zabiegi wykonuje uprawniony personel medyczny na zlecenie lekarza."),
    ("Świadoma zgoda pacjenta",
     "Zgoda udzielona po zrozumieniu informacji o celu, rodzaju, przebiegu i ryzyku zabiegu; wyrażana dobrowolnie, możliwa do cofnięcia w każdej chwili — dokumentowana zgodnie z Załącznikiem C."),
    ("RODO",
     "Rozporządzenie Parlamentu Europejskiego i Rady (UE) 2016/679 o ochronie danych osobowych; dane o zdrowiu są szczególną kategorią danych — masażysta przechowuje je poufnie, minimalnie i tylko w celu opieki nad klientem."),
    ("Tajemnica zawodowa",
     "Obowiązek nieujawniania informacji uzyskanych w związku z wykonywaniem zawodu; dotyczy stanu zdrowia, danych osobowych i okoliczności życia klienta; uchyla ją jedynie zwolnienie ustawowe lub sądowe."),
    ("Zdarzenie niepożądane",
     "Każde niezamierzone zdarzenie podczas zabiegu (np. otarcie skóry, omdlenie, nasilenie bólu); obligatoryjnie notowane w Karcie zdarzenia niepożądanego (Załącznik C.10) i zgłaszane przełożonemu/lekarzowi zgodnie z procedurą B.6."),
    ("Ekspozycja zawodowa",
     "Narażenie na kontakt z materiałem potencjalnie zakaźnym (krew, wydzieliny) przez skaleczenie lub zachlapanie; postępowanie określa procedura I.8 — zdjęcie rękawiczek, przepłukanie, dezynfekcja, zgłoszenie, ocena ryzyka przez lekarza medycyny pracy."),
    ("Ergonomia chwytu",
     "Takie ustawienie dłoni, przedramion i tułowia masażysty, by siła pochodziła z masy ciała i dużych grup mięśniowych, a nie ze stawów — chroni przed zespołami przeciążeniowymi (np. cieśnią nadgarstka)."),
    ("Przeciążenie pourazowe",
     "Nadmierne obciążenie tkanek prowadzące do mikrourazów (np. entezopatie ścięgna Achillesa, łokieć przyśrodkowy/boczny); masażysta rozpoznaje objawy alarmowe i kieruje do lekarza, nie wykonując głębokiego masażu w ostrej fazie zapalnej."),
    ("Zmiana skórna",
     "Każde odstępstwo wyglądu lub czucia skóry (wykwit, rana, zmiana barwy znamienia); masażysta nie diagnozuje — ocenia, czy masaż jest bezpieczny, a przy zmianach ropnych, świeżych lub niepokojących przekazuje klienta lekarzowi (Załącznik E.14)."),
    ("Znamienne (pieprzyk) — zasada ABCDE",
     "Asymetria, Brzegi nieregularne, Colour (różnobarwność), Diameter >6 mm, Evolution (zmiany w czasie) — reguła ostrożności: znamiona zmienione chroni się przed tarciem i zgłasza lekarzowi; masażysta ich nie ocenia rozpoznawczo."),
    ("Palpacja",
     "Badanie dotykiem: ocena temperatury, napięcia, bolesności i ruchomości tkanek; służy kwalifikacji do zabiegu i kontroli jego efektów — zawsze w granicach kompetencji, bez stawiania rozpoznań chorobowych."),
    ("Bolesność miejscowa",
     "Odczyn tkanki na dotyk w określonym punkcie; masażysta rejestruje ją w karcie zabiegu i dostosowuje siłę technik, a przy bólu promieniującym lub nietypowym — konsultuje z lekarzem."),
    ("Tonus mięśniowy",
     "Prawidłowe, utrzymywane napięcie spoczynkowe mięśnia; w patologii bywa obniżony (wiotkość) lub podwyższony (spastyczność, sztywność pozapiramidowa); masażysta zna różnice, bo dobór techniki zależy od tonusu, a przy zaburzeniach neurologicznych działa zgodnie ze wskazaniami lekarza."),
    ("Przeciwwskazanie lokalne",
     "Stan uniemożliwiający masaż tylko w określonej okolicy (np. zmiana skórna, żylaki w miejscu zabiegu, świeża blizna); dopuszcza wykonanie masażu pozostałych części ciała po ocenie bezpieczeństwa."),
    ("Okres okołomenstruacyjny",
     "Faza cyklu miesiączkowego; masaż relaksacyjny jest zwykle dobrze tolerowany, jednak przy silnym bólu menstruacyjnym stosuje się pozycje komfortowe i techniki łagodne, a przy podejrzeniu stanu ostrego — kieruje do lekarza."),
    ("Ciąża — pozycje bezpieczne",
     "Po I trymestrze unika się pozycji leżącej na plecach (ryzyko ucisku żyły głównej dolnej); preferowane leżenie na boku z podparciem podudzi i poduszek; masaż wykonuje się delikatnie, z uwzględnieniem przeciwwskazań położniczych (Załącznik D.11)."),
    ("Diastaza mięśnia prostego brzucha",
     "Rozstąpienie linii białej po ciąży; masażysta nie wykonuje głębokich technik w okolicy osłabionej, a instruktaż ćwiczeń pozostawia fizjoterapeucie uroginekologicznemu."),
    ("Żylaki",
     "Poszerzenia żył powierzchniowych z niewydolnością zastawkową; bezwzględnie unika się głębokiego masażu i ucisku na przebieg żylaków — dopuszczalne jest jedynie delikatne głaskanie odprowadzające poza obszarem zmian, po konsultacji lekarskiej."),
    ("Zakrzepica żył głębokich (DVT)",
     "Ostre zakrzepowe zapalenie żył głębokich — przeciwwskazanie BEZWZGLĘDNE do jakiegokolwiek masażu kończyny i do zabiegów mogących zwiększyć ryzyko zatorowości płucnej; objawy (jednostronny ból, obrzęk, ocieplenie, zaczerwienienie) wymagają natychmiastowej pomocy lekarskiej (Załącznik E.6)."),
    ("Zatorowość płucna (PE)",
     "Zagrożenie życia: nagła duszność, ból w klatce, tachykardia — masażysta przerywa wszelkie czynności i wzywa pomoc (112/999), układa klienta wg potrzeby i monitoruje do przyjazdu ratowników."),
    ("Nadciśnienie tętnicze",
     "Podwyższone ciśnienie tętnicze; masaż relaksacyjny o łagodnej sile jest zwykle bezpieczny, lecz unika się technik silnie pobudzających i gwałtownych zmian pozycji; przy wartościach bardzo wysokich lub objawach — konsultacja lekarska."),
    ("Osteoporoza",
     "Zmniejszona wytrzymałość kości; masażysta stosuje techniki powierzchowne, bez głębokiego ucisku na żebra i kręgosłup, szczególnie u osób starszych; wszelkie nowe bóle kostne zgłasza lekarzowi."),
    ("Nowotwór złośliwy",
     "Choroba, w której masaż jest dopuszczalny wyłącznie za pisemną zgodą/onkologa i poza obszarem zmiany, naczyń limfatycznych po limfadenektomii oraz pola napromieniania; celem jest komfort, nie „leczenie guza” (Załącznik E.11)."),
    ("Insulina i cukrzyca",
     "U klientów z cukrzycą masażysta pyta o stabilność glikemii i sposób odżywiania; unika głębokiego masażu okolic iniekcji insuliny i ocenia czucie na stopach (neuropatia); przy objawach hipoglikemii — przerwać zabieg, podać cukier prosty, wezwać pomoc jeśli brak poprawy."),
    ("Neuropatia obwodowa",
     "Upośledzenie czucia (najczęściej stopu) — klient nie odczuwa bólu ochronnego; masażysta stosuje mniejszą siłę, sprawdza temperaturę i integralność skóry, instruując o codziennej samokontroli stóp."),
    ("Padaczka",
     "Napady drgawkowe; masaż relaksacyjny bywa dobrze tolerowany, lecz unika się silnych technik na głowę i kark, zapewnia dyskrecję i bezpieczeństwo otoczenia; w razie napadu — pozycja boczna, ochrona głowy, nie wkładać nic do ust, czas trwania >5 min = 112."),
    ("Migrena",
     "Silny, pulsujący ból głowy często z nudnościami i nadwrażliwością na bodźce; masaż karku i barków o umiarkowanej sile może pomóc w profilaktyce napięciowej, ale w trakcie ataku priorytetem jest cisza, półmrok i decyzja klienta; objawy alarmowe (nagły „najgorszy ból życia”) → pilna pomoc lekarska."),
    ("Ból",
     "Subiektywne, nieprzyjemne dozucie związane z uszkodzeniem tkanek; masażysta mierzy jego natężenie skalą liczbową (Karta oceny bólu C.5), obserwuje reakcje wegetatywne i reaguje: ból ostry, promieniujący lub narastający = sygnał do przerwania techniki i konsultacji."),
    ("Skala VAS/NRS",
     "Wizualna/skalа numeryczna oceny bólu 0–10; narzędzie komunikacji z klientem i dokumentacji zmian przed/po zabiegu; nie służy do rozpoznawania choroby, lecz do śledzenia komfortu."),
    ("Efekt analgetyczny masażu",
     "Zmniejszenie odczuwania bólu po zabiegu dzięki bramkowanemu hamowaniu nocicepcji (Teoria bramki Melzacka-Walla), poprawie krążenia i rozluźnieniu napięcia mięśniowego; efekt jest objawowy, nie przyczynowy."),
    ("Przeciwobrzękowe bandażowanie kompresyjne",
     "Stosowanie opasek o odpowiedniej gradacji ucisku w terapii obrzęków; dobór ciśnienia i techniki nakładania należy do terapeuty przeszkolonego i odbywa się na zlecenie lekarza; masażysta asystuje i uczy pielęgnacji."),
    ("Uraz zamknięty vs otwarty",
     "Zamknięty — bez przerwania ciągłości skóry (stłuczenie, skręcenie); otwarty — z raną (ryzyko zakażenia, krwawienie); w obu przypadkach pierwsza pomoc wg Załącznika J/E, a masaż w okolicy urazu wyłącznie w okresie wskazanym przez lekarza."),
    ("Pozycja bezpieczna (boczna ustalona)",
     "Układanie nieprzytomnego, oddychającego klienta na boku z zabezpieczeniem głowy — chroni drogi oddechowe przed zachłyśnięciem; element procedury J.10."),
    ("AED (automatyczny defibrylator zewnętrzny)",
     "Urządzenie analizujące rytm serca i podające wstrząs, gdy jest wskazany; masażysta umie je uruchomić i stosować zgodnie z instrukcją głosową (J.9); po każdym użyciu zgłasza zdarzenie i dokumentuje."),
    ("Rekrutacja jednostek motorycznych",
     "Proces angażowania kolejnych jednostek motorycznych do zwiększania siły skurczu; masaż izometryczny i techniki napinająco-rozluźniające wykorzystują tę zasadę w kontrolowanych warunkach szkolnych i leczniczych."),
    ("Sumacja skurczów (tężcowa/fuzja)",
     "Nakładanie się skurczów przy wysokiej częstotliwości bodźców; mechanizm wyjaśnia, dlaczego gwałtowne, częste techniki pobudzające mają ograniczenia czasowe i nie stosuje się ich u osób z nadreaktywnością nerwowo-mięśniową bez zgody lekarza."),
    ("Regeneracja potreningowa",
     "Odpoczynek, sen, żywienie i nawodnienie po wysiłku; masaż jest jednym ze środków wspomagających subiektywny komfort i elastyczność tkanek, nie substytutem snu ani leczenia kontuzji."),
    ("Odpowiedzialność pracodawcy (BHP)",
     "Obowiązek zapewnienia bezpiecznych warunków pracy, szkoleń BHP, badań profilaktycznych i środków ochrony (art. 207 Kodeksu pracy); masażysta jako pracownik współodpowiada za stosowanie procedur (Załącznik B)."),
    ("Szkolenie BHP okresowe",
     "Powtarzane szkolenie bezpieczeństwa pracowników zatrudnionych na stanowiskach związanych z obciążeniem fizycznym i kontaktem z klientem; kurs MED.10 obejmuje moduł 1 jako podstawę teoretyczną takiego szkolenia."),
    ("Środki ochrony indywidualnej (ŚOI)",
     "Rękawiczki jednorazowe, fartuch, obuwie antypoślizgowe, ewentualnie maseczka przy zabiegach z ryzykiem aerozolu; dobór do sytuacji, obowiązki zakładania i zdejmowania określa Załącznik I."),
    ("Postępowanie z odpadami medycznymi",
     "Odpady komunalne vs medyczne (np. zużyte plastry, materiały ze krwią); segregacja do pojemników oznaczonych zgodnie z procedurą B.5 i ustawą o odpadach; masażysta nie wrzuca odpadów potencjalnie zakaźnych do kosza zwykłego."),
    ("Instrukcja stanowiskowa",
     "Dokument określający zasady bezpiecznego wykonywania pracy na stanowisku masażysty: organizację stanowiska, kolejność czynności, zagrożenia i działania awaryjne (B.2)."),
    ("Audyt higieniczny",
     "Okresowa ocena zgodności praktyki z procedurami aseptyki (I.10): mycie/dezynfekcja rąk, czyszczenie stołu, stan tekstyliów, terminy preparatów; wyniki dokumentuje się i wykorzystuje do doskonalenia."),
    ("Test alergiczny preparatu",
     "Próba naniesienia niewielkiej ilości olejku/kremu na skórę przedramienia i odczekanie doby przed pierwszym użyciem u nowego klienta (H.10); zapobiega reakcjom kontaktowym i chroni klienta."),
    ("Preparaty rozgrzewające/chłodzące",
     "Środki wspomagające zawierające m.in. kapsaicynę, mentol; stosowane ostrożnie, na skórę nieuszkodzoną, bez kontaktu z oczami i błonami; nie stosuje się ich przed wysiłkiem u dzieci ani u osób z neuropatią bez zgody lekarza (H.7, H.8)."),
    ("Masaż przyrządowy",
     "Masaż wykonywany aparatem wibracyjnym lub rolką mechaniczną; dobiera się częstotliwość i czas, unika kości, naczyń, zmian skórnych; urządzenie musi mieć aktualne przeglądy (D.15)."),
    ("Gorące kamienie bazaltowe",
     "Kamienie ogrzewane zwykle do ok. 45–50°C; temperaturę zawsze sprawdzasz na własnym przedramieniu i pytasz klienta o odczucie; przeciwwskazane przy zaburzeniach czucia, żylakach, stanach zapalnych i ciąży bez zgody lekarza (D.14)."),
    ("Masaż biurowy",
     "Krótka (10–20 min) forma masażu prozdrowotnego na krześle, przez ubranie, skupiona na karku, barkach i grzbiecie; cele: redukcja napięcia i edukacja ergonomiczna; nie zastępuje diagnostyki bólów kręgosłupa."),
    ("Relaksacja progresywna",
     "Technika świadomego napinania i rozluźniania grup mięśniowych (Jacobson); masażysta łączy ją z oddechem przeponowym w masażu relaksacyjnym, tworząc bezpieczną rutynę dla klienta zestresowanego."),
    ("Oddech przeponowy",
     "Tor oddechowy z aktywną przeponą; sprzyja obniżeniu napięcia sympatycznego; masażysta instruuje go w ramach edukacji prozdrowotnej (6.9), pamiętając, że nie jest terapeutą oddechowym w sensie medycznym."),
    ("Granice kompetencji masażysty",
     "Zbiór czynności wykraczających poza kwalifikację MED.10: rozpoznawanie chorób, interpretacja badań, manipulacje stawowe wysokiego ryzyka, zabiegi invasive; przekroczenie granicy = zagrożenie zdrowia klienta i odpowiedzialność prawna (Załącznik M)."),
    ("Kwalifikacja do zabiegu",
     "Decyzja „tak / nie / do lekarza” podejmowana na podstawie wywiadu, oglądu i kart Załączników D–E; każdą wątpliwość rozstrzyga się na korzyść bezpieczeństwa klienta."),
    ("Ocena funkcjonalna w gabinecie masażu",
     "Prosta obserwacja ruchu (zakresy, wzorce, ból przy ruchu) służąca planowaniu zabiegu i komunikacji z zespołem; nie jest badaniem lekarskim ani fizjoterapeutycznym w pełnym sensie."),
    ("Zespół wielodyscyplinarny",
     "Współpraca lekarza, fizjoterapeuty, masażysty, pielęgniarki, psychologa i innych specjalistów wokół klienta; masażysta wnosi obserwacje z zabiegów i realizuje ustalenia zespołu (3.19)."),
    ("Efekty kształcenia (EK)",
     "Mierzliwe osiągnięcia ucznia po module (mapa A); formułowane w kategoriach wiedzy, umiejętności i kompetencji społecznych; służą planowaniu zajęć, ocenianiu i samoocenie gotowości do egzaminu."),
    ("Egzamin potwierdzający kwalifikację MED.10",
     "Egzamin zawodowy składający się z części pisemnej (test) i praktycznej (stanowisko egzaminacyjne); warunki przystąpienia i kryteria oceny opisuje moduł 11 i przepisy CKE/OKE."),
    ("Portfel/Portfolio praktykanta",
     "Zbiór udokumentowanych doświadczeń praktycznych: karty zabiegów, dziennik, refleksje, oceny opiekuna; wspiera samoocenę i rozmowę egzaminacyjną (moduł 10)."),
    ("Autokorekta techniki",
     "Nawyk oceniania własnego wykonania po każdym zabiegu szkolnym wg check-list F; przyspiesza nabycie płynności i eliminuje błędy przeciążeniowe."),
    ("Nauczanie kolegialne (peer teaching)",
     "Wspólne ćwiczenie w parach: raz masażysta, raz klient; uczy empatii, komunikacji i dawania informacji zwrotnej zgodnie z zasadą szacunku."),
    ("Informacja zwrotna konstruktywna",
     "Konkretny, rzeczowy komentarz o zachowaniu (nie o osobie), wskazujący co poprawić i jak; fundament kultury zajęć praktycznych i oceniania koleżeńskiego."),
    ("Spójność przekazu (język obcy zawodowy)",
     "Umiejętność przedstawienia oferty, procedury i ostrzeżeń w języku obcym na poziomie A2/B1 z wykorzystaniem słownictwa G.10; wspiera bezpieczeństwo klienta obcojęzycznego (moduł 7)."),
    ("Kompensacyjna strategia komunikacyjna",
     "Sposoby radzenia sobie z luką językową: parafraza, gest, rysunek, słownik fotograficzny, prośba o powtórzenie; etycznie niedopuszczalne jest „zgadywanie” znaczenia zagrażającego bezpieczeństwu."),
    ("Kultura organizacyjna gabinetu",
     "Wspólnie przyjęte normy: punktualność, czystość, poufność, uprzejmość wobec klienta i współpracowników; buduje bezpieczeństwo psychiczne i jakość usługi (8.1, 9.x)."),
    ("Rozwiązywanie konfliktów (mediacja)",
     "Etapy: opisać fakt, wysłuchać strony, wskazać interesy, szukać rozwiązania korzystnego; eskalacja do przełożonego, gdy bezpieczeństwo klienta jest zagrożone (8.9)."),
    ("Radzenie sobie ze stresem",
     "Techniki oddechowe, przerwy, higiena snu, wsparcie zespołu, superwizja; chroniczny stres obniża precyzję manualną i empatię — dlatego jest tematem modułu 8.6."),
    ("Ustawiczne dokształcanie",
     "Obowiązek moralny i praktyczny: śledzenie wytycznych, kursy doskonalące, lektura źródeł z Załącznika L; gwarancja, że wiedza masażysty nie staje się przestarzała (K.10)."),
]

# ---------------------------------------------------------------------------
# 2. TREŚCI SZCZEGÓŁOWE ZAŁĄCZNIKÓW A–M (append-only, marker MARKER)
# ---------------------------------------------------------------------------

DETAIL_TEXT: dict[str, str] = {
    "A": """
### Jak korzystać z mapy efektów kształcenia

Mapa porządkuje, czego uczysz się w danym module i jak to sprawdzić przed egzaminem. Przy każdym module zapisz trzy rzeczy: (1) jakie techniki manualne potrafisz wykonać samodzielnie, (2) jakie przeciwwskazania rozpoznajesz bez zaglądania do notatek, (3) jakie sytuacje musisz skierować do lekarza. To ostatnie pytanie jest najważniejsze — granica kompetencji jest częścią kwalifikacji, nie jej ubytkiem.

| Moduł | Kluczowe efekty kształcenia (umiejętności mierzalne) | Dowód opanowania |
|---|---|---|
| A.1 / MED.10.1 → Moduł 1 | Przeprowadzasz mycie i dezynfekcję rąk wg procedury; oceniasz zagrożenia stanowiska; wykonujesz BLS na fantomie; rozpoznajesz stan pilny i dzwonisz 112/999 | Check-listy F.1, F.2, F.29; quiz 1.x ≥60% |
| A.2 / MED.10.2 → Moduł 2 | Wskażesz na modelu 100 elementów anatomicznych; rozróżnisz 4 techniki podstawowe i podasz ich wskaźniki; dobierzesz środek poślizgowy do skóry klienta | Atlas + karty pracy; quiz 2.x; zadania 2.x |
| A.3 / MED.10.3 → Moduł 3 | Dla każdej z głównych jednostek chorobowych podasz wskazania i przeciwwskazania do masażu; odmówisz zabiegu uzasadniając to na piśmie | Mapy myśli 3.x; case studies; quiz 3.x |
| A.4 / MED.10.4 → Moduł 4 | Wykonasz kompletny masaż klasyczny grzbietu, kończyn, twarzy; przeprowadzisz kwalifikację do zabiegu; udokumentujesz kartę zabiegu | Check-listy F.9–F.20; ocena praktyki |
| A.5 / MED.10.5 → Moduł 5 | Dobierzesz protokół masażu przed- i powysiłkowego do dyscypliny; rozpoznasz objawy alarmowe u zawodnika; zachowasz etykę sportową | Protokoły 5.6; scenariusze 5.7; quiz 5.x |
| A.6 / MED.10.6 → Moduł 6 | Przeprowadzisz masaż relaksacyjny, biurowy i z kamieniami wg procedur bezpieczeństwa; poprowadzisz mini-edukację prozdrowotną | Scenariusze 6.4–6.8; quiz 6.x |
| A.7 / MED.10.7 → Moduł 7 | Przedstawisz ofertę i ostrzeżenia po angielsku (A2/B1); przeczytasz kartę klienta w języku obcym; użyjesz strategii kompensacyjnych | Role-play 7.8; test czytania 7.6; quiz 7.x |
| A.8 / MED.10.8 → moduły zintegrowane | Udzielisz informacji zwrotnej; rozwiążesz konflikt wg etapów; zaplanujesz dzień pracy i odpoczynek; udokumentujesz samodoskonalenie | Obserwacje na zajęciach; portfolio |
| A.9 / MED.10.9 → moduły zintegrowane | Zaplanujesz pracę zespołu w scenariuszu gabinetowym; rozdzielisz role; ocenisz jakość zadań; wprowadzisz ulepszenie | Projekt zespołowy 9.x; prezentacja |
| A.10 / Praktyka i egzamin → Moduły 10–11 | Zrealizujesz godziny praktyki z dziennikiem; przejdziesz symulację egzaminu praktycznego; złożysz oświadczenie o granicach kompetencji | Dziennik praktyk; ocena opiekuna; próbny egzamin |

### Samoocena gotowości (metoda świateł)

- **Zielone** — wykonujesz zadanie samodzielnie i potrafisz je wyjaśnić partnerowi.
- **Żółte** — wykonujesz z drobnymi wskazówkami; powtórz wg check-listy i rytmu 1/3/7/21 dni.
- **Czerwone** — potrzebujesz instruktora; nie idź na egzamin z tym tematem bez konsultacji.

Egzamin nie karze za trudność materiału, lecz za brak bezpieczeństwa klienta. Uczciwa samoocena jest aktem miłości bliźniego i sprawiedliwości wobec samego siebie.""",

    "B": """
### B.1 Regulamin BHP gabinetu masażu (skrót operacyjny)

1. Stanowisko utrzymane w czystości; droga ewakuacyjna wolna, gaśnica dostępna, numer 112/999 widoczny.
2. Przed pierwszym klientem dnia: wietrzenie, dezynfekcja powierzchni dotykowych, sprawdzenie wyposażenia (stół, podkłady, ręczniki, ŚOI).
3. Obowiązuje zakaz pracy z biżuterią, długimi paznokciami, otwartymi ranami dłoni; rękawy zadbane.
4. Oświetlenie bez olśnienia, temperatura 21–24°C, wentylacja bez przeciągów na leżącym kliencie.
5. Sygnał „przerwij zabieg”: ból ostry klienta, zawroty głowy, duszność, zmiana koloru skóry, niepokojący oddech.

### B.2 Instrukcja stanowiskowa masażysty — zagrożenia i środki

| Zagrożenie | Źródło | Środek ochrony |
|---|---|---|
| Przeciążenia układu ruchu | nachylona postawa, zbyt duży nacisk | ergonomia chwytu, wysokość stołu, mikropyłki co 30–45 min |
| Kontakt z materiałem zakaźnym | rany klienta, pot, krew | rękawiczki, dezynfekcja, procedura ekspozycji I.8 |
| Skaleczenia, potłuczenia | sprzęt, poślizg | obuwie antypoślizgowe, porządek, serwis urządzeń |
| Stres, presja czasu | grafik, trudni klienci | limit zabiegów/h, superwizja, techniki oddechowe |
| Czynniki termiczne | kamienie, lampy | kontrola temperatury, izolacja, instrukcja producenta |

### B.3 Procedura mycia i dezynfekcji rąk (skrót)

Mycie wodą z mydłem min. 40–60 s: dłonie zmoczyć, mydlić grzbety, przestrzenie międzypalcowe, kciuki, opuszki, nadgarstki; spłukać; osuszyć ręcznikiem jednorazowym. Dezynfekcja preparatem alkoholowym min. 30 s na ręce czyste i suche, do zaniku wilgoci. Kiedy: przed i po każdym kliencie, po skorzystaniu z toalety, po kontakcie z powierzchniami potencjalnie skażonymi, po zdjęciu rękawiczek.

### B.4 Procedura przygotowania stołu

Sprawdź stabilność i blokadę wysokości → nałóż czysty podkład/ prześcieradło → przygotuj ręczniki (okrycie intymne, podparcia) → ustaw pozycję neutralną klienta → sprawdź temperaturę pomieszczenia i oświetlenie → przygotuj środki poślizgowe i kartę zabiegu. Między klientami: zmiana tekstyliów, dezynfekcja powierzchni styku.

### B.5 Postępowanie z odpadami

Segregacja: odpady komunalne (czyste papier/ręczniki) vs odpady medyczne potencjalnie zakaźne (materiały z krwią, wydzielinami, zużyte plastry) — pojemniki oznaczone, odbiór przez uprawniony podmiot. Pojemniki nie przepełnione powyżej 3/4. Dokumentacja odbioru przechowywana zgodnie z regulaminem gminy/wytwórcy.

### B.6 Procedura zdarzenia niepożądanego

Zatrzymaj zabieg → zapewnij bezpieczeństwo klientowi → wezwij pomoc jeśli potrzeba → zapisz fakty w Karcie zdarzenia (C.10): co, kiedy, gdzie, świadek, podjęte działania → poinformuj przełożonego/lekarza → nie ukrywaj, nie zatajaj, nie oceniaj winy publicznie → analiza przyczyn i działanie korygujące.

### B.7 Procedura pierwszej pomocy

Bezpieczeństwo ratującego → ocena przytomności → oddech i krążenie → wezwanie pomocy (112/999) → BLS/AED wg Załącznika J → pozycja bezpieczna gdy oddycha i nie podejrzewasz urazu kręgosłupa → dokumentacja i przekazanie zespołowi ratownictwa.

### B.8 Procedura skierowania do lekarza

Gdy stwierdzisz objaw wykraczający poza ocenę zabiegową (gorączka, obrzęk jednostronny, ból w klatce, podejrzenie infekcji skóry, zmiana skórna niepokojąca, objawy neurologiczne) → przerywasz kwalifikację do masażu → informujesz klienta spokojnie i rzeczowo → wpisujesz rekomendację do karty → sugerujesz kontakt z lekarzem POZ lub wizytę pilną zależnie od stanu (patrz Załącznik E) → nie stawiasz rozpoznania.

### B.9 Procedura ochrony małoletnich

Masaż dziecka za obecnością i zgodą opiekuna prawnego; wyjaśniasz dziecku krok po kroku co będziesz robić; unikasz obszarów intymnych; kontakt fizyczny wyłącznie niezbędny do techniki; zgłaszasz niepokojące sygnały (śladы urazów, lęk) zgodnie z obowiązującymi przepisami o ochronie dzieci; nigdy nie zostajesz z dzieckiem w zamkniętym pomieszczeniu bez możliwości nadzoru.

### B.10 Przeciwdziałanie przemocy

Rozpoznajesz symptomy (lęk przed dotykiem, niespójne tłumaczenia obrażeń, izolacja) → nie konfrontujesz agresora → zapewniasz prywatność i bezpieczeństwo ofierze → dokumentujesz spostrzeżenia rzeczowo → informujesz o dostępnych instytucjach (Niebieska Linia 800 120 002, Policja 112) zgodnie z procedurą organizacyjną i prawem.

### Rejestr procedur wewnętrznych (wzór nagłówka)

Każda procedura powinna zawierać: nazwę, wersję, datę zatwierdzenia, zakres zastosowania, odpowiedzialnego, wykaz środków, schemat decyzyjny, wzór formularza pokrewnego (Załącznik C) i datę następnego przeglądu.""",

    "C": """
### C.1 Karta pacjenta (zakres obowiązkowy)

Dane identyfikacyjne i kontaktowe; wiek; wzrost/masa (opcjonalnie, za zgodą); cel wizyty; wywiad: choroby przewlekłe, leki (zwłaszcza przeciwzakrzepowe, insulina), alergie, ciąża, operacje, nowotwory, urządzenia wszczepione; stan skóry; przeciwwskazania wg Załącznika D; podpis klienta i data aktualizacji. Bez tej karty nie kwalifikujesz zabiegu.

### C.2 Karta zabiegu masażu

Data/godzina; rodzaj masażu; obszary; techniki i czas; siła (skala); pozycja klienta; preparat; reakcje w trakcie (ból, zaczerwienienie, zawroty); zalecenia domowe; podpis masażysty; numer kolejny sesji. Karta pozwala ocenić skuteczność i bezpieczeństwo w czasie.

### C.3 Zgoda na przetwarzanie danych (RODO)

Klauzula informacyjna: administrator, cel (realizacja usługi masażu i bezpieczeństwo), podstawа (zgoda/umowa/obowiązek prawny), odbiorcy (np. ubezpieczyciel za zgodą), okres przechowywania, prawa: dostęp, sprostowanie, usunięcie, ograniczenie, przenoszenie, sprzeciw, skarga do UODO. Dane o zdrowiu — szczególna kategoria: tylko niezbędne, szyfrowane, z dostępem uprawnionych.

### C.4 Zgoda na zabieg masażu

Potwierdzenie, że klient rozumie: charakter zabiegu, oczekiwane odczucia, możliwe reakcje, prawo do przerwania w każdej chwili, granice kompetencji masażysty. Osoby niepełnoletnie/niesamodzielne — zgoda opiekuna plus assent dziecka w miarę możliwości.

### C.5 Karta oceny bólu

Skala 0–10 (NRS) lubVAS; lokalizacja (rysunek ciała); charakter (piekący, tępy, promieniujący); czynniki nasilające/łagodzące; wpływ na sen i funkcje; pomiar przed i po zabiegu; trend między wizytami. Nie diagnozujesz przyczyny — rejestrujesz i komunikujesz zespołowi.

### C.6 Karta oceny obrzęku

Obwód kończyny na stałych poziomach (oznaczonych); konsystencja (miękka/uciślowa); znak dołka; temperatura skóry; odczucie ciężkości; zdjęcia (za zgodą, bez twarzy); porównanie z poprzednim pomiarem; kwalifikacja do drenażu wg 4.3 i D.3.

### C.7 Karta drenażu limfatycznego

Metoda (Vodder/Leduc), obszary, czas, ciśnienie, bandażowanie (typ, gradacja), reakcje klienta, zalecenia po (ruchy, nawodnienie, higiena skóry), przeciwwskazania wykluczone (D.3), podpis terapeuty.

### C.8 Karta masażu sportowego

Dyscyplina; faza cyklu (przygotawcza/start/regeneracja); moment względem treningu/zawodów; grupy mięśniowe; techniki i intensywność; czas; nawodnienie/temperatura; uwagi trenera/lekarza; zgoda na publikację wyników wewnątrz sztabu; obserwacje do przekazania specjaliście.

### C.9 Karta masażu prozdrowotnego

Cel (relaks/profilaktyka/dobrostan); środowisko (dom, biuro, spa); techniki; muzyka/światło/temperatura; preferencje klienta; reakcje; zalecenia prozdrowotne (ergonomia, oddech, ruch); ewentualne skierowanie do lekarza przy niepokojących objawach.

### C.10 Karta zdarzenia niepożądanego

Identyfikacja zdarzenia; czas i miejsce; opis faktów bez interpretacji winy; osoba zgłaszająca; świadek; działania natychmiastowe; decyzja o pomocy medycznej; przyczyny wstępne (czynniki ludzkie/sprzętowe/proceduralne); działanie korygujące i termin; podpis przełożonego. Karta służy nauce systemu, nie karaniu człowieka.

### C.11 Skierowanie do lekarza

Treść: co zaobserwowano, od kiedy, jakie objawy towarzyszą, jakie działania podjęto, dlaczego masaż został wstrzymany lub zmodyfikowany. Ton rzeczowy, bez rozpoznania. Klient otrzymuje kopię; oryginał w dokumentacji.

### C.12 Dziennik praktyk

Daty i godziny; miejsce; opiekun; wykonane czynności; liczba zabiegów i obszary; napotkane problemy i rozwiązania; wnioski; podpis opiekuna co tydzień; pieczęć placówki na koniec. Dziennik jest dowodem godzin i jakości kształcenia.

### C.13 Karta oceny praktyki

Kryteria: przygotowanie stanowiska, kwalifikacja klienta, technika, bezpieczeństwo, komunikacja, dokumentacja, postawa etyczna; skala opisowa; mocne strony; obszary rozwoju; ustalenia na kolejny okres; podpisy praktykanta i opiekuna.

### C.14 Oświadczenie o tajemnicy zawodowej

Potwierdzenie obowiązku zachowania poufności informacji o zdrowieniu i życiu klienta; zakres wyjątków ustawowych; sankcje cywilne i karne za naruszenie; data i podpis.

### C.15 Informacja RODO dla pacjenta

Pełna klauzula informacyjna wg art. 13 RODO wraz z klauzulą o danych zdrowotnych (art. 9) — wręczana przy pierwszej wizycie, przechowywana w wersji elektronicznej lub papierowej; dostęp dla osób ze szczególnymi potrzebami (duża czcionka, odczyt).""",

    "D": """
### D.1 Przeciwwskazania do masażu klasycznego

**Bezwzględne (do decyzji lekarza):** gorączka i ostre infekcje; stany zapalne tkanek miękkich w ostrej fazie; zakrzepica żył głębokich i zatorowość; niewyrównana niewydolność krążenia; rozległe uszkodzenia skóry, oparzenia, rany; zmiany nowotworowe w okolicy bez zgody onkologa; tętniaki; ostre urazy (do oceny lekarskiej).
**Względne (modyfikacja siły/czasu/obszaru, konsultacja):** żylaki (unikanie głębokiego masażu), nadciśnienie nieuregulowane, osteoporoza zaawansowana, ciąża (po konsultacji), miesiączka z silnym bólem, przepukliny, stany pooperacyjne wcześnie, choroby dermatologiczne poza obszarem aktywnych zmian, przyjmowanie leków przeciwzakrzepowych (ryzyko krwawień podskórnych).

### D.2 Przeciwwskazania do masażu segmentarnego

Dodatkowo: ostre stany zapalne narządów wewnętrznych, kolka (nerkowa, wątrobowa, jelitowa) bez rozpoznania, gorączka, tętniaka aorty, świeży zawał i niestabilna dławica, ostre choroby jamy brzusznej wymagające interwencji. Masaż odruchowy nie zastępuje diagnostyki!

### D.3 Przeciwwskazania do manualnego drenażu limfatycznego

Bezwzględne: Decompensatio cordis, zakrzepica/ac żylne w fazie ostrej, nieleczona nadczynność tarczycy (ryzyko tyreotoksyczne przy stymulacji), aktywne nowotworzenie bez zgody lekarza, ostra faza zapalenia żył, ropne stany skóry, obrzęk serca pochodzenia żylnego bez nadzoru. Względne: astma (dobór tempa), nadciśnienie, ciąża — ostrożnie i za zgodą lekarza.

### D.4 Przeciwwskazania do masażu łącznotkankowego

Silne pobudzenie wegetatywne => ostrożność przy nadreaktywności współczulnej, stanach zapalnych w ostrej fazie, gorączce, zmianach troficznych skóry, żylakach i przepuklinach w polu zabiegowym; nie stosować głębokich chwytów na skórze cienkiej/atroficznej u osób starszych bez zgody lekarza.

### D.5 Przeciwwskazania do masażu okostnowego

Osteoporoza (ryzyko mikrourazów), choroby metaboliczne kości, nowotwory kości, wiek dziecięcy (przrosty!), ostre zapalenia stawów, zakrzepowe zapalenie żył w okolicy, rany/odmrożenia okostnej. Technika mocna — zawsze za zgodą i w granicach wskazań lekarskich.

### D.6 Przeciwwskazania do masażu punktowego

Ostre stany zapalne, zakrzepica, żylaki, zmiany skórne w punkcie, ciąża (bez znajomości przeciwwskazań położniczych), epilepsja (silne bodźce), przyjmowanie leków przeciwzakrzepowych (krwawienia), wiek dziecięcy poniżej pewnego progu — tylko za zgodą rodzica i lekarza.

### D.7 Przeciwwskazania do refleksoterapii stóp

Uszkodzenia skóry stóp, grzybica/ropnie, zakrzepica, ostre stany zapalne, ciąża zaawansowana bez zgody lekarza, neuropatia z utratą czucia (ryzyko mikrourazów), świeże operacje stóp. Silny ból w trakcie = przerwać.

### D.8 Przeciwwskazania do masażu w środowisku wodnym

Infekcje skóry i otwarte rany, padaczka bez kontroli, lęk przed wodą, arytmie niestabilne, niewydolność oddechowa, infekcje intymne, menstruacja z dyskomfortem klienta, brak asekuracji i nadzoru. Temperatura wody wg wskazań; ryzyko wychłodzenia/przegrzania.

### D.9 Przeciwwskazania do masażu izometrycznego i stawowego

Ostre zapalenia stawów, wysięki, niestabilność stawów, świeże skręcenia/złamania, endoprotezy bez zgody chirurga, zakrzepica, zaawansowana osteoporoza, bóle o niejasnej etiologii. Mobilizacje stawowe należą do kompetencji fizjoterapeuty/lekarza — masażysta nie manipuluje.

### D.10 Przeciwwskazania do masażu Shantala

Gorączka, choroby skórne, tuż po szczepieniu (za zgodą pediatry), wrodzone wady serca bez zgody kardiologa, dysplazja bioder w fazie leczenia (konsultacja), przepuklina pachwinowa lub przepuklina pępkowa wymagająca oceny (ostrożność!), epilepsja, noworodek wcześniak bez zgody neonatologa, stan po karmieniu (odczekać 20–30 min), płacz i protest dziecka = przerwać.

### D.11 Przeciwwskazania do masażu w ciąży

Bezwzględne (do lekarza): krwawienia, bóle skurczowe, łożysko przodujące, preeklampsja, cukrzyca nieuregulowana, ciąża mnoga wysokiego ryzyka, stan po cesarskim cięciu bez zgody lekarza, odklejenie łożyska w wywiadzie. Względne: nudności, refluks, żylaki, obrzęki fizjologiczne — pozycje bezpieczne, techniki łagodne, unikanie ucisku na żyłę główną dolną po 20. tygodniu.

### D.12 Przeciwwskazania do masażu w połogu

Ostry stan zapalny, gorączka, krwawienie ponad normę, zakrzepica/zatorowość (podwyższone ryzyko połogowe), nieunormowane ciśnienie, rana krocza/cc bez zgody, depresja poporodowa w ostrym stanie — priorytet: kontakt z położną/lekarzem. Masaż łagodny, wspierający, po ocenie medycznej.

### D.13 Przeciwwskazania do masażu sportowego

Świeży uraz bez oceny (obrzęk, ból ostry, deformacja), gorączka i infekcja ogólnoustrojowa, otwarte rany, zakrzepica wysiłkowa (rzadka, ale groźna), anemia ciężka, odwodnienie i hipertermia, choroby serca nieuregulowane, stan po wstrząśnieniu mózgu (do zgody lekarza sportowego). Zawodnik nie jest „materiałem do wyniku” — zdrowie ponad medal.

### D.14 Przeciwwskazania do masażu gorącymi kamieniami

Zaburzenia czucia (neuropatia, cukrzyca), zaburzenia krążenia obwodowego, żylaki, stany zapalne skóry, owrzodzenia, nowotwory w obszarze, ciąża (bez zgody), przyjmowanie leków fotouczulających, dzieci i osoby starsze z cienką skórą — temperatura kamieni niższa i nadzór większy. Oparzenie termiczne to zdarzenie niepożądane do karty C.10.

### D.15 Przeciwwskazania do masażu przyrządowego

Urządzenie bez przeglądu/atestu; obszar żylaków, tętniaków, implantów metalowych w polu działania, rozrusznik serca (elektroterapia/vibro w pobliżu — zakaz), ciąża, nowotwory, ostre stany zapalne, epilepsja (bodźce rytmiczne intensywne), rany i zmiany skórne; ostrożność u dzieci i osób starszych. Zawsze: instrukcja producenta i szkolenie obsługi.

### Algorytm kwalifikacji przed zabiegiem (uniwersalny)

1. Czy klient ma objawy stanu pilnego (Załącznik E)? → TAK: przerwij, wezwij pomoc.
2. Czy występują przeciwwskazania bezwzględne (D.x)? → TAK: nie masuj, skieruj do lekarza (C.11).
3. Czy są przeciwwskazania względne? → TAK: zmodyfikuj technikę/czas/obszar, uzyskaj zgodę, wpisz do karty.
4. Czy masz wątpliwość? → Rozstrzygnij na korzyść bezpieczeństwa: konsultuj.
5. Zapisz decyzję i uzasadnienie w karcie pacjenta/zabiegu.""",

    "E": """
### Jak korzystać z listy stanów pilnych

Zasada nadrzędna: **w razie wątpliwości — nie masuj i szukaj pomocy medycznej.** Każdy punkt to sygnał, że ciało klienta potrzebuje lekarza, nie stołu do masażu. Twoim obowiązkiem jest rozpoznanie alarmu i spokojne, rzeczowe działanie.

| Podpunkt | Typowy obraz | Co zrobić natychmiast |
|---|---|---|
| E.1 Ból w klatce piersiowej | ucisk, pieczenie, promieniowanie do żuchwy/ramienia, duszność, poty | przerwać wszystko, 112/999, pozycja półsiedząca, luźne ubranie, nie zostawiać samej osoby |
| E.2 Duszność nagła | świszczący oddech, sinica, niemożność dokończenia zdania | 112/999, pozycja wygodna (pochylenie do przodu), tlen tylko przez uprawnionych |
| E.3 Omdlenie | utrata przytomności, bladła skóra, szybki powrót świadomości | ułożyć płasko z uniesionymi nogami, ocenić oddech, zbadać urazy głowy; brak oddechu → BLS |
| E.4 Podejrzenie udaru | asymetria twarzy, osłabienie kończyny, mowa bełkotliwa (skala FAST) | 112/999 natychmiast, zapisz godzinę początku objawów, nie podawaj nic doustnie |
| E.5 Podejrzenie zawału | ból w klatce >15 min, lęk śmierci, nudności, zimny pot | jak E.1; jeśli przytomny i brak przeciwwskazań — zgodnie z dyspozytorem medycznym |
| E.6 Obrzęk jednostronny kończyny z bólem | łyda ciepła, napięta, bolesna, sine/zaczerwienione | 112/999 lub pilna pomoc lekarska; żadnego masażu kończyny i intensywnego ruchu |
| E.7 Gorączka i dreszcze | >38°C, osłabienie, poty, bóle mięśni | odłożyć zabieg, zalecić kontakt z lekarzem; przy sztywności karku/spłotaniu → 112 |
| E.8 Krwotok | krew jasna/soka, narastający krwiak | ucisk bezpośredni, wezwanie pomocy przy dużym krwawieniu, rękawiczki, dezynfekcja po |
| E.9 Ostry uraz z deformacją | podejrzenie złamania/zwichnięcia | nie nastawiać, nie masować, unieruchomić jak uczono, 112/SOR |
| E.10 Objawy infekcji ogólnoustrojowej | wysoka gorączka, splątanie, wysypka krwotoczna | 112; wysypka nieblednąca = stan bezpośredniego zagrożenia życia |
| E.11 Nowotwór w wywiadzie bez zgody lekarza | jakakolwiek lokalizacja, leczenie w toku | nie masuj bez pisemnej zgody onkologa/lekarza prowadzącego; obrzęk limfatyczny — tylko wg wskazań |
| E.12 Ciąża z krwawieniem lub bólami | plamienie, ból podbrzusza, odpływanie płynu | 112/999, położenie na lewym boku, spokój, zero masażu |
| E.13 Dolegliwości neurologiczne postępujące | narastający niedowład, drętwienia, zaburzenia równowagi | pilna konsultacja neurologiczna; wstrzymaj zabieg |
| E.14 Zmiany skórne ropne lub rozległe | czyraki, róża, pęcherze, liszaje | nie masuj obszaru ani reszty przy rozległej zmianie; skieruj do lekarza; ochrona personelu |
| E.15 Każdy stan, którego nie potrafisz bezpiecznie ocenić | niepewność odczuwana przez Ciebie | to jest sygnał alarmowy sam w sobie: przerwij, wyjaśnij klientowi, skontaktuj z lekarzem |

### Telefon alarmowy — minimum

112 (UE) lub 999. Powiedz: KTO mówi (nazwa, stanowisko), GDZIE (adres, piętro, drzwi), CO się stało (objawy), ILE osób poszkodowanych, JAKI jest stan przytomności i oddechu, CO już zrobiono. Nie rozłączaj się pierwszy. Poproś o dostępność AED i kogoś do jego przyniesienia.""",

    "F": """
### Jak używać check-list

Ćwiczysz w parach. Najpierw sam wykonujesz zadanie, potem oceniasz wg punktów (0 = niepotrzebne/niewykonane, 1 = z pomocą, 2 = samodzielnie i bezpiecznie). Na koniec wspólnie ustalcie jedną rzecz do poprawy na następne zajęcia. Kryterium nadrzędne: bezpieczeństwo klienta i Twoja ergonomia.

| Nr | Zadanie | Punkty kontrolne (wybór kluczowych) |
|---|---|---|
| F.1 | Przygotowanie stanowiska | czystość, dezynfekcja, tekstylia, oświetlenie, temperatura, ewakuacja, karta pod ręką |
| F.2 | Mycie i dezynfekcja rąk | 40–60 s mycie, 30 s dezynfekcja, sequencja dłonie/palc/kciuki/nadgarstki, osuszenie |
| F.3 | Prowadzenie wywiadu | cele, choroby, leki, alergie, ciąża, urazy, zgoda, poufność, zapis |
| F.4 | Ocena postawy | obserwacja z przodu/boku/tyłu, asymetrie, oznaczenie punktów, opis bez diagnozy |
| F.5 | Pomiar obwodów | stałe poziomy, taśma bez ucisku, zapis z datą, porównanie L/P |
| F.6 | Ocena zakresu ruchu | ruch czynny→bierny, skala, ból przy ruchu, porównanie stron |
| F.7 | Palpacja mięśni | temperatura, napięcie, bolesność, guzki — opis, nie rozpoznanie |
| F.8 | Lokalizacja punktów spustowych | projekcja anatomiczna, reakcja skurczowa, ból promieniujący — zgłoś lekarzowi |
| F.9 | Głaskanie | kierunek serca, tempo, kontakt całej dłoni, rozpoczęcie/zakończenie zabiegu |
| F.10 | Rozcieranie | okrężne/poprzeczne, stabilna podstawa, brak marszczenia skóry, kontrola bólu |
| F.11 | Ugniatanie | chwyt wałeczkowy, fala od prox do dist, siła modulowana oddechem klienta |
| F.12 | Oklepywanie | krawędź/palce, rytm, nad mięśniami nie nad kośćmi/nerkami, czas krótki |
| F.13 | Wibracja | drganie ciągłe/przerywane, nacisk, zakończenie, obserwacja odczynu |
| F.14 | Masaż kończyny górnej | kolejność: grzbiet→ramię→łokieć→przedramię→dłoń, odprowadzanie żylne |
| F.15 | Masaż kończyny dolnej | stopa→podudzie→udo, pośladki,kierunek ku sercu, żylaki omijać |
| F.16 | Masaż grzbietu | głaskanie wzdłuż, rozcieranie przykręgosłupowe, ugniatanie równoległe, oklepywanie bocznie |
| F.17 | Masaż karku | ostrożność tętnic, brak rotacji forsownych, mięśnie scalene, potyliczne |
| F.18 | Masaż klatki piersiowej | międzyżebrza od mostka ku kręgosłupowi, bez ucisku na okolicę sutków i wyrostek mieczykowaty |
| F.19 | Masaż brzucha | kierunek zgodny z perystaltyką (zgodnie z zegarem), głębokość ostrożna |
| F.20 | Masaż twarzy i głowy | opuszki, brak olejków do oczu, włosy spięte, tempo wolne |
| F.21 | Drenaż limfatyczny kończyny | sekwencja: przygotowanie stacji węzłowych → praca na obwodzie, „ręcznikowy” chwyt, tempo wolne, bandażowanie potem |
| F.22 | Segmentarny — chwyty diagnostyczne | strefy Heada, napięcie, fałd, temperatura — opis do karty |
| F.23 | Segmentarny — chwyty lecznicze | siła dobierana, reakcja wegetatywna, przerwanie przy bólu |
| F.24 | Refleksoterapia stóp | mapa stref, technika „chodzącego” kciuka, poczęstuj wodą po zabiegu |
| F.25 | Shantala — etapy | zgodność z dzieckiem, pozycje, sekwencja: brzuch → klatka → kończyny, kontakt z opiekunem |
| F.26 | Ciąża — pozycje bezpieczne | bok lewy, poduszki, brak długotrwałego leżenia na plecach po ok. 20. tygodniu, techniki łagodne |
| F.27 | Sportowy przedstartowy | szybkość, pobudzenie, rozgrzanie, bez głębokiego rozluźniania, czas 8–12 min |
| F.28 | Prozdrowotny relaksacyjny | atmosfera, oddech, monotonia rytmu, zakończenie i poinstruowanie |
| F.29 | Pierwsza pomoc — BLS | bezpieczeństwo, przytomność, oddech, 112, 30:2, AED, pozycja boczna |
| F.30 | Dokumentacja zabiegu | karta kompletna, czytelna, podpis, przechowywanie, RODO |

### Nawyk powtórek

Check-listę F.x powtarzaj w rytmie: dzień 1 (po zajęciach), dzień 3, dzień 7, dzień 21. Pięciominutowa powtórka na telefonie liczy się bardziej niż dwugodzinne „odrabianie” raz na semestr.""",

    "G": """
### G.1 Terminy anatomiczne (przykłady używane w kursie)

proksimalny/dystalny (bliżej/dalej tułowia), przyśrodkowy/stronny, grzbietowy/brzuszny, dłoniowy/grzbietowy stopy, zgięcie/wyprost, nawrócenie/odwrócenie, przywiedzenie/odwiedzenie, płaszczyzna strzałkowa/czołowa/poprzeczna, wyrostek, guz, krętarz, kłykieć, bruzda, powięź, ścięgno, więzadło, przegroda.

### G.2 Terminy fizjologiczne

tonus, propriocepcja, nocicepcja, chemoreceptory, baroreceptory, homeostaza, perfuzja, przepływ żylany/chłonkowy, adaptacja przeciążeniowa, zmęczenie obwodowe i ośrodkowe, regeneracja, superkompensacja, oddech przeponowy, tętno spoczynkowe, HRV.

### G.3 Terminy patologiczne

obrzęk, rumień, wysięk, transsudat/exsudat, zapalenie, martwica, przykurcz, zanik, hipertrofia, zwłóknienie, zakrzep, zator, żylak, tętniak, neuropatia, neuralgia, parestezja, anestezja, ataksja, spastyczność, sztywność, bolesność punktu spustowego, odczyn oponowy, sinica, bladość, potliwość.

### G.4 Terminy masażu klasycznego

effleurage (głaskanie), petrissage (ugniatanie), friction (rozcieranie), tapotement (oklepywanie), vibration (wibracja), ruchy posuwające, wałeczkowanie, szczypanie, ugniatanie podłużne/poprzeczne, rozcieranie okrężne, wibracja ciągła/drżąca, sekwencja, dawkowanie, czas zabiegu, siła nacisku, odczyn posmasażowy.

### G.5 Terminy drenażu limfatycznego

chwyt pompowy, kołowy, „caterpillar”, „skarpeta”, rewolucja/rotacja, stacja węzłowa, tor odpływu, obrzęk limfatyczny I–III stopnia, obrzęk włóknisty, bandaż wielowarstwowy, gradient ciśnienia, samoopiekunka skóry.

### G.6 Terminy masaży odruchowych

segment, strefa Head'a, punkt motoryczny, punkt akupresurowy, strefa refleksogenna, linia oddechowa, łańcuch mięśniowo-powięziowy, odruch wegetatywny, reakcja na bodziec, zona oporowa.

### G.7 Terminy fizykoterapii

kondukcyjna/conwekcyjna transmisja, elektroterapia, galwanizacja, jonoforeza, prądy diadynamiczne/interdynensyjne, TENS, ultradźwięki, laser niskiej mocy, magnetoterapia, krioterapia, balneoterapia, fototerapia, peeling chemiczny (nie w kompetencji masażysty!).

### G.8 Terminy kinezyterapii

ćwiczenia bierne/czynno-bierne/czynne/oporowe, PNF, stabilizacja, mobilizacja, stretching, plyometria, trening siłowy, wytrzymałość, propriocepcja, ortostatyczna tolerancja, deambulator, faza ostra/podostra/przewlekła.

### G.9 Terminy prawne i etyczne

kwalifikacja zawodowa, uprawnienie, tajemnica zawodowa, RODO, dane osobowe, dane o zdrowiu, zgoda świadoma, assent, klauzula informacyjna, rejestr zdarzeń niepożądanych, odpowiedzialność cywilna, odszkodowanie, wina, rażące niedbalstwo, kodeks etyczny, konflikt interesów, dyskryminacja, molestowanie, sygnalista.

### G.10 Terminy języka obcego zawodowego (EN, przykłady)

massage table (stół do masażu), drape (prześcieradło/okrycie), glide medium (środek poślizgowy), effleurage, kneading, tapping, vibration, contraindication, consent form, pressure scale, range of motion (ROM), swelling, bruise, numbness, tingling, sharp pain, dull ache, warm/compress, side-lying position, emergency call, confidentiality.

### Jak uczyć się słownictwa

Twórz fiszki trójkowe: termin PL — termin EN — kontekst zdania z gabinetu. Raz dziennie 5 fiszek, powtórka w rytmie 1/3/7/21. Wymawiaj na głos — masażysta mówi do klienta, więc język musi być gotowy w ustach, nie tylko w oczach.""",

    "H": """
### Zasada ogólna

Preparat dobieramy do: stanu skóry klienta, techniki, czasu zabiegu, alergii w wywiadzie, środowiska (biuro/spa/sport) i łatwości zmywania. Każdorazowo: próba alergiczna (H.10) i informacja dla klienta.

| Nr | Środek | Charakterystyka | Wskazania | Uwagi i przeciwwskazania |
|---|---|---|---|---|
| H.1 | Talk | proszek, sucho | masaż suchy, potliwość | wdychanie pyłu — unikać przy problemach oddechowych; dziś rzadziej stosowany |
| H.2 | Oleje roślinne | nośnik (kokosowy, migdałowy, jojoba, rzepakowy) | masaż klasyczny, relaksacyjny | przy uczuleniu na orzechy wybieraj olej nierafinowany bez białek alergennych lub inny nośnik; test płatkowy; przechowywać chłodno, termin ważności |
| H.3 | Oliwki | oliwa z oliwek, oliwki kosmetyczne | skóra sucha, masaż delikatny | tłuste, trudne do zmycia ze stołu; alergie kontaktowe rzadkie |
| H.4 | Kremy | emulsja w/o lub o/w | masaż krótki, biurowy | wchłanianie zmienne; kremy z mentolem — ostrożnie |
| H.5 | Lanolina | tłuszcz owczy | bardzo sucha skóra | alergia na wełnę; ciężka do zmywania |
| H.6 | Wazelina | petrolatum | masaż ochronny, krótki | nie na twarz/skłonność do zaskórników; plamy na tekstyliach |
| H.7 | Preparaty rozgrzewające | kapsaicyna, imbir, nikotynian benzylu | sport, bóle mięśniowe | NIE przed wysiłkiem u dzieci, NIE na skórę uszkodzoną, NIE w okolicy oczu/śluzówek; ryzyko oparzenia |
| H.8 | Preparaty chłodzące | mentol, kamfora | urazy świeże (po konsultacji), upał | astmatycy ostrożnie; nie na duże powierzchnie u dzieci |
| H.9 | Preparaty przeciwzapalne | żele z NLPZ (np. diklofenak) — tylko zgodnie z prawem | wyłącznie wg wskazań lekarza/farmaceuty | masażysta NIE zleca, NIE aplikuje leków; klient może użyć własnego żelu za zgodą lekarza |
| H.10 | Zasady przechowywania i testów | szczelne opakowania, czystość, data otwarcia, test alergiczny 24h | wszyscy klienci | wyrzucać po terminie; nie mieszać preparatów bez wiedzy o interakcjach |

### Higiena aplikacji

Nabieraj preparatu czystą szpatułką lub pompką — nigdy palcami po zabiegu. Butelkę po użyciu zdezynfekuj (powierzchnia gwintu). Nie zostawiaj otwartych pojemników między klientami.

### Dobór do techniki

Głaskanie i rozcieranie — średni poślizg (oliwka/krem). Ugniatanie — mniejszy poślizg, większa kontrola (olej wchłaniający się). Oklepywanie — na sucho lub cienka warstwa. Drenaż — najczęściej bez preparatu lub minimalnie, by zachować czucie ciśnienia. Kamienie — oliwka odporna na temperaturę.

### Edukacja klienta

Poinstruuj: co zostało na skórze, jak to zmyć, czy można wystawiać skórę na słońce (preparaty rozgrzewające/fotouczulające), jakie objawy niepożądane zgłosić (świąd, pieczenie, wysypka).""",

    "I": """
### Cel zestawu procedur

Zapobiegać przenoszeniu drobnoustrojów: klient→klient, klient→masażysta, masażysta→klient, powierzchnie→wszyscy. Procedury są obowiązkowe i audytowalne.

### I.1 Mycie rąk — kiedy i jak

Kiedy: przed i po każdym kliencie, po toalecie, po kontakcie z odpadami, po zdjęciu rękawiczek, po kaszlu/kichnięciu. Jak: mokre ręce → mydło → 40–60 s (grzbiety, przestrzenie międzypalcowe, kciuki, opuszki, nadgarstki) → spłukać → osuszyć ręcznikiem jednorazowym → zakręcić kran ręcznikiem. Paznokcie krótkie, bez lakieru, bez biżuterii.

### I.2 Dezynfekcja rąk

Na ręce czyste i suche: preparat alkoholowy (wg normy EN 1500), min. 30 s, dokładnie wszystkie powierzchnie, do wyschnięcia. Nie zastępuje mycia przy widocznym zabrudzeniu.

### I.3 Dezynfekcja powierzchni

Powierzchnie kontaktu (stół, podłokietniki, oparcia, uchwyty, telefony, włączniki) — preparat dezynfekcyjny o udokumentowanym spektrum (bakterie, grzyby, wirusy otoczkowe; wg producenta i normy EN 14476). Czas kontaktu ściśle wg instrukcji. Materiały niestabilne chemicznie (skóra, lateks) — chronić lub zmieniać.

### I.4 Pranie tekstyliów

Prześcieradła, ręczniki, podkłady: zmiana między klientami; pranie min. 60°C z detergentem; sortowanie odzieży roboczej osobno; suszenie pełne; przechowywanie w zamkniętych szafkach. Tekstylia klienta (własne) — nie mieszamy z gabinetowymi.

### I.5 Utylizacja odpadów

Komunalne: czyste papierowe ręczniki, opakowania. Medyczne potencjalnie zakaźne: materiały z krwią/wydzielinami, zużyte plastry, rękawiczki po zabiegu z ryzykiem — pojemnik oznaczony, odbiór przez firmę uprawnioną, ewidencja. Ostre (igły) — tylko w pojemnikach na odpady ostre; masażysta nie produkuje odpadów ostrych (nie iniekuje!).

### I.6 Postępowanie przy zmianach skórnych

Aktywne zmiany ropne, wirusowe (pęcherzyki, brodawki w polu zabiegowym), grzybicze — wstrzymaj masaż obszaru, oceń rozległość, skieruj do lekarza (E.14). Po zabiegu u klienta ze zmianami: dezynfekcja stołu i powierzchni, wymiana tekstyliów, higiena rąk.

### I.7 Postępowanie przy krwawieniu

Rękawiczki → ucisk jałowym gazikiem → uniesienie kończyny → opatrzenie → dezynfekcja powierzchni skażonych krwią (preparat na bazie chloru/alkoholowy wg normy) → utylizacja odpadów z krwią → zapis w karcie zdarzenia (C.10).

### I.8 Postępowanie po ekspozycji

Skaleczenie/zachlapanie: natychmiast zdjąć rękawiczki, przepłukać ranę wodą z mydłem (śluzówki samą wodą), dezynfekcja rany, nie ssąć. Zgłosić przełożonemu, lekarzowi medycyny pracy; ocena ryzyka (HBV/HCV/HIV), ewentualne szczepienia/profilaktyka. Dokumentacja ekspozycji i dalszych kontroli.

### I.9 Dokumentacja dezynfekcji

Rejestr: data, godzina, preparat, stężenie, czas kontaktu, osoba wykonująca, obszar. Przechowywać wg regulaminu; umożliwiać audyt.

### I.10 Audyt higieniczny

Co najmniej kwartalnie: obserwacja mycia rąk, stan powierzchni, terminy preparatów, segregacja odpadów, tekstylia, sprzęt. Wynik: tabela punktów + 3 działania korygujące + termin przeglądu. Audyt to narzędzie doskonalenia, nie poszukiwania winnych.""",

    "J": """
### Kolejność działań (dorosły, dziecko, niemowlę)

**J.1 Ocena bezpieczeństwa** — czy Tobie nic nie zagraża (ruch, prąd, ogień, agresja). Nie jesteś bohaterem bezbronnych: zabezpiecz siebie, potem pomagaj.
**J.2 Ocena przytomności** — mów głośno, potrząśnij delikatnie za ramiona; brak reakcji → wołaj o pomoc.
**J.3 Wezwanie pomocy** — 112/999; głośno: adres, co się stało, stan, liczba osób; poproś o AED i kogoś, kto go przyniesie.
**J.4 Udrożnienie dróg oddechowych** — odchylenie głowy, uniesienie żuchwy (uraz szyi: ręczna stabilizacja i oddech bez hyperextensji — wg szkolenia).
**J.5 Ocena oddechu** — patrz–słuchaj–czuj max 10 s; brak prawidłowego oddechu (tylko agonalne westchnienia) = zatrzymanie krążenia.
**J.6 Resuscytacja dorosłego** — uciśnięcia: środek klatki, głębokość 5–6 cm, tempo 100–120/min, pełne rozprężenie, przerwy <10 s; oddechy 30:2 (jeśli jesteś przeszkolony i wyrażasz zgodę; AED jak najszybciej.
**J.7 Resuscytacja dziecka** — 30:2 (jeden ratownik) lub 15:2 (dwóch ratowników); głębokość ~1/3 AP klatki (5 cm); po 2 min wezwij pomoc jeśli wcześniej nie.
**J.8 Resuscytacja niemowlęcia** — dwa palce lub kciuki (dwóch ratujących), ~1/3 klatki (4 cm), 30:2; oddechy „usta-na-usta-nos”; ostrożność z głową.
**J.9 AED** — włącz, postępuj z komunikatami; sucha skóra, elektrody dobrane do wieku/masy ciała (elektrody dziecięce zwykle <8 lat i <25 kg), odsuń się przy analizie i wyładowaniu; wróć do uciśnięć natychmiast po wyładowaniu.
**J.10 Pozycja bezpieczna i dokumentacja** — przytomnie oddychający bez podejrzenia urazu kręgosłupa: pozycja boczna ustalona; zapisz czas zdarzenia, objawy, działania, reakcje; przekaż zespół ratownictwa; sporządź kartę zdarzenia (C.10).

### Ćwiczenia

Co miesiąc: fantom + AED treningowy + scenariusz „klient mdleje na stole”, „dziecko krztusi się”, „duszność u klienta z astmą”. Ćwiczenie trwa 10 minut, ratuje lata.

### Zasady etyczne

Nie zostawiasz klienta samego; nie panikujesz przy nim; mówisz krótko i spokojnie; po zdarzeniu informujesz przełożonego i bliskich klienta zgodnie z procedurą i RODO (tylko uprawnione osoby).""",

    "K": """
### Fundament

Trzy cnoty kursu: **prawda** (mówisz to, co wiesz; nie obiecujesz cudów), **dobro** (służysz zdrowiu i godności człowieka), **sprawiedliwość** (taka sama jakość dla każdego, niezależnie od ceny, płci, wieku, pochodzenia, wyglądu, orientacji czy przekonań).

### Deklaracje szczegółowe

- **K.1 Godność pacjenta** — ciało klienta jest dobrem osobowym godnym szacunku: nie komentujesz wyglądu, nie dotykasz poza koniecznością zabiegu, chronisz intymność okryciem i słowem.
- **K.2 Prawda w komunikacji** — nie obiecujesz „wyleczenia”, nie straszysz, nie zatajasz ryzyka; przy nieznaniu odpowiedzi mówisz: „tego nie wiem, sprawdzę/skieruję”.
- **K.3 Miłość bliźniego jako służba** — masaż jest darem uwagi i troski; nie towarem do maksymalizacji zysku kosztem bezpieczeństwa.
- **K.4 Sprawiedliwość w dostępie do opieki** — racjonalne grafiki, rozsądne ceny, niedyskryminowanie; pomoc osobom w potrzebie w ramach możliwości.
- **K.5 Piękno w pracy z ciałem** — estetyka gestu, czystość, harmonia sali, muzyka bez nachalności; piękno służy pokojowi klienta.
- **K.6 Tajemnica zawodowa** — żadnych plotek, zdjęć „before/after” bez zgody, publikacji danych; media społecznościowe z rozwagą.
- **K.7 Zakaz manipulacji** — nie wykorzystujesz zależności emocjonalnej, nie sprzedajesz strachem, nie sugerujesz „detoksy”, „uzdrawiania energią” jako leczenia.
- **K.8 Zakaz wykorzystywania seksualnego** — jakakolwiek seksualizacja relacji zabiegowej jest niedopuszczalna; granice techniczne jasne; przy dyskomforcie klienta — przerwać i przeprosić.
- **K.9 Zakaz dyskryminacji** — równy standard dla kobiet, mężczyzn, osób starszych, z niepełnosprawnościami, różnych kultur i wyznań.
- **K.10 Odpowiedzialność za szkolenie ustawiczne** — corocznie aktualizujesz wiedzę (BLS, wytyczne, anatomia, etyka); nie „zamrażasz” kompetencji.

### Zdanie, które warto umieścić w gabinecie

„Jeśli masz wątpliwość, czy coś jest bezpieczne — nie rób tego. Twoje wahanie jest dowodem profesjonalizmu.”

### Naruszenia kodeksu

Sygnały niepokojące (ból klienta ignorowany, żarty o ciele, prośby o „więcej”), postępowanie: rozmowa → dokumentacja → powtórna edukacja → wyciągnięcie konsekwencji organizacyjnych; przy krzywdzie klienta — obowiązki prawne (zawiadomienie, ochrona dowodów).""",

    "L": """
### Dlaczego źródła są ważne

Masażysta jest w obiegu informacji medycznej. Cytowanie wiarygodnych autorów chroni klienta przed dezinformacją, a Ciebie przed błędem. Zasada: jeśli twierdzenie nie ma oparcia w podręczniku/wytycznych — nie powtarzaj go klientowi jako faktu.

### L.1–L.3 Adam Zborowski — *Masaż klasyczny i segmentarny*, *Masaż w wybranych jednostkach chorobowych*, *Drenaż limfatyczny*

Fundament metodyczny polskich szkół masażu: techniki, wskazania, przeciwwskazania, protokoły. Korzystaj z wydań aktualnych; notuj numery stron przy cytatach w kartach pracy.

### L.4 Bochenek — *Anatomia człowieka*

Atlas i terminologia: nazwy mięśni, przyczepy, unerwienie, topografia. Ćwicz lokalizacje palpacyjne na sobie i partnerze — anatomia uczy się palcami.

### L.5 Traczyk — *Fizjologia człowieka*

Mechanizmy: skurcz, krążenie, oddech, nerwy, hormony. Fizjologia tłumaczy, dlaczego masaż działa objawowo i kiedy jest ryzykowny.

### L.6 Podstawy patofizjologii i rehabilitacji

Przegląd procesów chorobowych i logiki rehabilitacji; pomaga zrozumieć język lekarza i fizjoterapeuty w zespole.

### L.7 Wytyczne BLS Polskiej Rady Resuscytacji / ERC

Standard: 100–120 uciśnięć/min, głębokość 5–6 cm, pełne rozprężenie, AED ASAP, 30:2. Aktualizuj co roku — wytyczne się zmieniają.

### L.8 Przepisy prawa pracy, BHP, RODO

Kodeks pracy (art. 207 i nn.), rozporządzenia BHP, ustawa o prawach pacjenta i Rzeczniku Praw Pacjenta, RODO (2016/679) i krajowe przepisy o danych zdrowotnych. Znajomość chroni Ciebie i klienta.

### L.9 Podstawa programowa kwalifikacji MED.10

Oficjalne wymagania egzaminacyjne CKE; moduły, efekty, kryteria. Egzamin odzwierciedla podstawę — ucz się z niej, nie z plotek.

### L.10 Materiały dydaktyczne kursu

Niniejsze książki (book), quizy, zadania, załączniki A–M; notatki z zajęć. Materiały są do użytku kursowego; cytuj je zgodnie z licencją CC BY-SA.

### Jak cytować (styl uproszczony)

Autor, *Tytuł*, wydanie, wydawnictwo, rok, s. X. W dokumentacji gabinetowej wystarczy: „wg Zborowski, wyd. II, s. 145”. Przy wątpliwościach: dwa niezależne źródła lub wytyczne.

### Kryteria oceny źródła internetowego

Kto publikuje? Czy są przypisy? Czy data jest świeża? Czy treść zgodna z podręcznikiem? Czy autor ma kompetencje medyczne? Czy nie sprzedajesz strachem? Jeśli 3+ odpowiedzi „nie” — zamknij stronę, otwórz książkę.

### Literatura uzupełniająca (do biblioteki szkolnej)

- Physiotherapy evidence databases (PEDro) — przegląd dowodów.
- WHO — promocja zdrowia i bezpieczeństwo pacjenta.
- Normy PN/EN dotyczące dezynfekcji i sprzętu medycznego.
- Czasopisma fizjoterapeutyczne — współpraca interdyscyplinarna.""",

    "M": """
### Po co to oświadczenie

Chroni klienta przed wyobrażeniem, że masażysta leczy choroby, a Ciebie przed pokusą przekraczania kompetencji. Podpisujesz je na starcie kursu i odnosisz się do niego w codziennej praktyce.

### Treść deklaracji (wzór)

Ja, niżej podpisany/a uczestnik/czka kursu MED.10, oświadczam, że rozumiem i akceptuję:

1. **M.1** Kurs nie uprawnia do wykonywania zawodu lekarza ani do stawiania rozpoznań chorobowych.
2. **M.2** Kurs nie uprawnia do samodzielnego leczenia chorób; masaż jest usługą wspomagającą dobrostan i realizowaną w zakresie wskazań.
3. **M.3** Kurs nie uprawnia do diagnostyki medycznej wykraczającej poza ocenę przydatną do decyzji „masaż / nie masaż / do lekarza”.
4. Nie wykonuję zabiegów invasive, nie podaję leków, nie interpretuję badań laboratoryjnych ani obrazowych.
5. Nie stosuję manipulacji kręgosłupa i technik wysokiego ryzyka należących do innych zawodów medycznych.
6. Nie obiecuję wyleczenia chorób ani skutków wykraczających poza wiedzę medyczną; nie propaguję twierdzeń bez dowodów.
7. Szanuję autonomię klienta: mogę przerwać zabieg ze względu na bezpieczeństwo, klient może go przerwać w każdej chwili.
8. Zobowiązuję się do stałego dokształcania i aktualizacji procedur (BLS, aseptyka, RODO).
9. Naruszenie tych zasad traktuję jako zagrożenie dobra klienta i własnej odpowiedzialności prawnej.

Data: ....................        Podpis: ..............................

### Komu okazujesz oświadczenie

Klientowi (w formie przystępnej informacji), przełożonemu, instytucjom kontrolnym, sobie — raz w semestrze przeczytaj je na nowo.

### Zdanie końcowe

Prawdziwa profesja nie polega na wszechmocy, lecz na wierności granicom. Wolność masażysty rodzi się z odpowiedzialności; pokój klienta — z Twojej uczciwości.""",
}


def norm_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def load_existing_terms(path: Path) -> set[str]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return set()
    entries = (data.get("glossary") or {}).get("entries") or []
    return {norm_key(str(e.get("term", ""))) for e in entries if isinstance(e, dict)}


def build_glossary_yaml(existing_path: Path, new_entries: list[dict]) -> str:
    """Dopisuje nowe hasła BEZ zmian formatowania istniejących wpisów.

    Plik jest edytowany tekstowo (append na końcu bloku entries), dzięki
    czemu oryginalne cytaty i układ haseł utworzonych przez wcześniejsze
    skrypty pozostają nietknięte. Zwraca nową zawartość pliku jako string;
    zapis wykonuje wołający.
    """
    text = existing_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    # Wskaźnik ostatniej linii bloku entries, ZACHOWUJĄC wcięanie oryginału
    # (listy mogą być zagnieżdżone np. o 2 lub 4 spacje).
    last_idx = -1
    item_indent = "  "   # standardowe wcięcie "- term:" w plikach kursu
    for i, ln in enumerate(lines):
        st = ln.strip()
        if st.startswith("- term:") or st.startswith("definition:") \
           or st.startswith("format:"):
            last_idx = i
            item_indent = ln[: len(ln) - len(ln.lstrip())] + "  "
    add_lines = []
    for ne in new_entries:
        add_lines.append(f"{item_indent}- term: {yaml_q(ne['term'])}")
        add_lines.append(f"{item_indent}  definition: {yaml_q(ne['definition'])}")
        add_lines.append(f"{item_indent}  format: html")
    if last_idx == -1:
        # brak bloku entries — dopisz całość na końcu
        block = ["  entries:"] + ["  " + l for l in add_lines]
        return text.rstrip("\n") + "\n" + "\n".join(block) + "\n"
    out = lines[:last_idx + 1] + add_lines + lines[last_idx + 1:]
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def yaml_q(s: str) -> str:
    """Bezpieczne cytowanie YAML (podwójny cudzysłów)."""
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def backup_file(path: Path, do_backup: bool) -> None:
    if not do_backup or not path.exists():
        return
    bak = path.with_name(path.name + ".bak")
    if not bak.exists():
        bak.write_bytes(path.read_bytes())


def enrich_label(path: Path, letter: str, dry_run: bool, do_backup: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    detail = DETAIL_TEXT.get(letter)
    if not detail or MARKER in text:
        return False
    add = f"\n{MARKER}\n{detail.strip()}\n"
    if dry_run:
        print(f"  [dry-run] dopiszę {len(add.encode('utf-8'))} B do {path.name}")
        return True
    backup_file(path, do_backup)
    path.write_text(text.rstrip("\n") + "\n" + add, encoding="utf-8")
    return True


def refresh_section_table(sec_md: Path, base: Path, dry_run: bool, do_backup: bool) -> None:
    """Aktualizuje rozmiary plików w tabeli 'Mapa plików załączników'."""
    if not sec_md.exists():
        return
    text = sec_md.read_text(encoding="utf-8")
    if "Mapa plików załączników" not in text:
        return

    def repl(m: re.Match) -> str:
        fname = m.group(1)
        f = sec_md.parent / fname
        if not f.exists():
            return m.group(0)
        size = f.stat().st_size
        return f"| `{fname}` | {size} B |"

    new_text = re.sub(r"\| `([^`]+\.md)` \| \d+ B \|", repl, text)
    if new_text != text:
        if dry_run:
            print(f"  [dry-run] odświeżę tabelę rozmiarów w {sec_md.name}")
            return
        backup_file(sec_md, do_backup)
        sec_md.write_text(new_text, encoding="utf-8")
        print(f"  odświeżono tabelę rozmiarów: {sec_md.relative_to(base.parent)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--toc", default=None, help="ścieżka do spisu treści")
    ap.add_argument("--base", default=BASE_REL)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    repo = Path.cwd()
    base = (repo / args.base).resolve()
    if not base.is_dir():
        print(f"BŁĄD: brak katalogu kursu: {base}")
        return 1

    toc_path = Path(args.toc) if args.toc else default_source()
    course = parse_course(toc_path)
    letters = [a.letter for a in course.attachments]
    print(f"Załączniki ze spisu treści: {''.join(letters)} ({len(letters)})")

    # --- 1. glossary -------------------------------------------------------
    gl_dir = base / "sections" / "12-zalaczniki" / "glossary-01"
    gl_path = gl_dir / "glossary.yaml"
    changed_gl = False
    if gl_path.exists():
        existing = load_existing_terms(gl_path)
        new_entries = [
            {"term": t, "definition": d, "format": "html"}
            for (t, d) in NEW_GLOSSARY_TERMS
            if norm_key(t) not in existing
        ]
        if new_entries:
            print(f"Glossary: dopiszę {len(new_entries)} nowych haseł "
                  f"(istniejących: {len(existing)})")
            if not args.dry_run:
                backup_file(gl_path, not args.no_backup)
                gl_path.write_text(build_glossary_yaml(gl_path, new_entries),
                                   encoding="utf-8")
            changed_gl = True
        else:
            print("Glossary: komplet (brak nowych haseł do dopisania)")
    else:
        print(f"UWAGA: brak {gl_path}; słownik zostanie utworzony od zera")
        if not args.dry_run:
            gl_dir.mkdir(parents=True, exist_ok=True)
            entries = [{"term": t, "definition": d, "format": "html"}
                       for (t, d) in NEW_GLOSSARY_TERMS]
            payload = yaml.safe_dump({"glossary": {
                "name": "Słownik pojęć masażu (MED.10)",
                "intro": "Podstawowe terminy używane w kursie; uzupełnienie "
                         "załącznika G.\n",
                "intro_format": "markdown",
                "entries": entries}},
                allow_unicode=True, sort_keys=False, width=100)
            gl_path.write_text("# Aktywność typu glossary — słownik pojęć kursu\n"
                               + payload, encoding="utf-8")
        changed_gl = True

    # --- 2. label-e A..M ----------------------------------------------------
    sec12 = base / "sections" / "12-zalaczniki"
    labels = sorted(sec12.glob("label-*.md"))
    enriched = 0
    for lab in labels:
        m = re.search(r"zalacznik-([a-m])-", lab.name)
        if not m:
            continue
        letter = m.group(1).upper()
        if enrich_label(lab, letter, args.dry_run, not args.no_backup):
            enriched += 1
    print(f"Załączniki rozbudowane: {enriched}/{len(labels)}")

    # --- 3. tabela rozmiarów w section.md ----------------------------------
    refresh_section_table(sec12 / "section.md", base, args.dry_run,
                          not args.no_backup)

    total_new = len(NEW_GLOSSARY_TERMS)
    print("SUMA: nowe hasła słownika:", total_new,
          "| dopisane sekcje szczegółowe:", enriched,
          "| glossary zmieniony:", changed_gl)
    if args.dry_run:
        print("(dry-run — nic nie zapisano)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
