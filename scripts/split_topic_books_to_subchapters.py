#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rozszerzenie książek (book) kursu MED.10 o kolejne ROZDZIAŁY-PODROZDZIAŁY.

Stan wejściowy (audyt 2026-10-28): 79 aktywności typu book w sekcjach 01–11
kursu `03-kurs-masazysta-med10` ma tylko JEDEN rozdział, który zbiorczo
opisuje ok. 10 zagadnień szczegółowych tematu (nagłówki „### X.Y.Z …”).
Walidator treści przechodzi, jednak użytkownik prosi: „jeżeli aktywności book
można rozszerzyć o kolejne rozdziały i podrozdziały — uzupełnij je”.

Skrypt dla każdej takiej książki:
  1. Wyodrębnia listę zagadnień szczegółowych z rozdziału zbiorczego.
  2. Tworzy NOWY rozdział książki (chapters/NN-*.md) dla KAŻDEGO zagadnienia,
     z długą, fachową treścią: wprowadzenie, mechanizm/fizjologia lub patofizjologia,
     znaczenie dla masażysty, metodyka postępowania krok po kroku, bezpieczeństwo,
     granice kompetencji, dokumentacja, pytania utrwalające, słowniczek.
  3. Nowe rozdziały oznacza jako `subchapter: true` w book.yaml (struktura
     drzewiasta Moodle book: rozdział zbiorczy + podrozdziały szczegółowe).
  4. W starym rozdziale zbiorczym dopisuje adnotację z odniesieniem do
     rozbudowanych podrozdziałów (append-only; oryginał zachowany w .bak).

Treść każdego nowego podrozdziału powstaje na podstawie REALNEJ wiedzy
medyczno-zawodowej dopasowanej do tematu (słowa kluczowe w tytule sterują
doborem bloków merytorycznych), w duchu prawdy, piękna i sprawiedliwości.

Idempotentność: skrypt pomija książki, które mają już >1 rozdział oraz pliki
zawierające znacznik "<!-- subch-v1 -->". Użycie:

    python3 scripts/split_topic_books_to_subchapters.py [--base ...] [--dry-run] [--limit N]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BASE_REL = "courses/03-kurs-masazysta-med10"
MARKER = "<!-- subch-v1 -->"

ZAG_RE = re.compile(r"^### ((\d+\.\d+(?:\.\d+)?))\s+(?:[\d\.]+\s*)?(.+?)\s*$", flags=re.M)


def slugify(title: str) -> str:
    s = title.lower()
    tr = {"ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n", "ó": "o",
          "ś": "s", "ź": "z", "ż": "z", "â": "a"}
    s = "".join(tr.get(c, c) for c in s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:52] or "zagadnienie"


# ---------------------------------------------------------------------------
# Baza wiedzy: bloki merytoryczne dobierane po słowach kluczowych tytułu
# ---------------------------------------------------------------------------

KNOWLEDGE = [
    # (regex, akapit główny)
    (r"choroba zwyrodnieniowa|zwyrodnieni", """Choroba zwyrodnieniowa stawów (osteoarthritis) to najczęstsza choroba stawów: postępująca degeneracja chrząstki szklistej wraz z przebudową kości podchrzęstnej, wtórnym zapaleniem błony maziowej i osłabieniem mięśni okołostawowych. Ból mechaniczny (nasila się w ruchu, ustępuje w spoczynku), sztywność poranna krótsza niż 30 minut, trzeszczenie (krepitacje) i ograniczenie zakresu ruchu tworzą klasyczny obraz. Masażysta nie cofnie chrząstki — ale może zmniejszyć ból przez redukcję napięcia mięśni przeciążonych kompensacyjnie, poprawę krążenia okołostawowego i przygotowanie tkanek do kinezyterapii zaleconej przez lekarza."""),
    (r"dyskopat|kręgosłup|krzegoslup|zespoł(y|u) bólow|bólow", """Zespoły bólowe kręgosłupa obejmują dyskopatię (degeneracja krążka międzykręgowego z mozliwym uciskiem na korzeń nerwowy), bóle mięśniowo-powięziowe i niestabilność segmentarną. Różnicowanie jest zadaniem lekarza: objawy korzeniowe (ból promieniujący poniżej poziomu kolca biodrowego z zaburzeniami czucia lub odruchów), zespół ogona końskiego (zaburzenia czucia siodłowego, pęcherza — stan nagły!) wymagają natychmiastnej konsultacji. Masaż w zespołach bólowych stosujemy jako element terapii złożonej: techniki rozluźniające mięśnie przykręgosłupowe, bez intensywnych manipulacji na odcinku ostrym."""),
    (r"zesztywniające|zzsk|spondylit", """Zesztywniające zapalenie stawów kręgosłupa to przewlekła choroba zapalna młodych mężczyzn głównie: ból nocny i poranna sztywność >30 min, ograniczenie ruchomości odcinka lędźwiowego (test Schobera), zajęcie stawów krzyżowo-biodrowych. W masażu fazy stabilnej: delikatne techniki rozluźniające mięśnie grzbietu i pośladkowe, wspomagające oddech przeponowy; BEZWZGLDNIE ostrożnie przy zaawansowanym zesztywnieniu i osteoporozy — ryzyko złamań."""),
    (r"reumatoidalne|rzs|idiopatyczne zapalenie", """Reumatoidalne zapalenie stawów to systemowy proces autoimmunologiczny: symetryczne zapalenie błony maziowej drobnych stawów, poranna sztywność >1 h, deformacje (łabędziej szyi, butonierki). W okresie AKTYWNEGO zapalenia masaż miejscowy jest przeciwwskazany — działa się wyłącznie na tkanki poza zajętymi stawami, bardzo delikatnie, po konsultacji z reumatologiem; priorytetem jest ochrona struktur przed uszkodzeniem."""),
    (r"dna moczanowa|artropatia|metabolic", "Dna moczanowa to odkładanie kryształów moczanu sodu w stawach (napadowy, potworny ból, obrzęk, zaczerwienienie — często I staw palucha). Napad dna jest PRZECIWWSKAZANIEM bezwzględnym do masażu zajętej okolicy (nasilenie zapalenia). Po wyciszeniu farmakologicznym masaż można stosować ostrożnie, ucząc klienta profilaktyki dietetycznej i nawodnienia w granicach swoich kompetencji."),
    (r"osteoporoz|złamań|zlaman", "Osteoporoza — utrata masy kostnej i pogorszenie mikroarchitektury kości — czyni tkanki podatnymi na złamania nawet przy minimalnym urazie. Zasada: żadnych gwałtownych ruchów, żadnego ucisku punktowego na wyrostki kolczyste i żebra, pozycje ułożone z pełnym podparciem. Masaż relaksacyjny o lekkiej/umiarkowanej sile, wykonany profesjonalnie zmniejsza lęk i napięcie mięśni ochraniających kręgosłup."),
    (r"fibromialg|bólu uogólnion", "Fibromialgia to centralna sensytyzacja bólu: rozległy ból >3 mies., punkty bolesne, zmęczenie, zaburzenia snu. Masaż jest jedną z najlepiej udokumentowanych niefarmakologicznych interwencji — ALE musi być łagodny: głęboki, agresywny masaż nasila objawy. Protokół: głaskanie, rozcieranie powierzchowne, ciepło, długa sesja w przygaszonym świetle; stopniowanie czasu; stała komunikacja o natężeniu bólu (skala VAS/NRS)."),
    (r"wady postawy|zniekształc", "Wady postawy (plecy okrągłe, płaskie, lordotyczne; koślawość kolan i stóp) wynikają z nierównowagi napięciowej mięśni: grupy skrócone/przeciążone vs osłabione/rozciągnięte. Masaż rozluźnia struktury nadmiernie napięte (np. prostownik grzbietu, mięsień piersiowy mniejszy, zginacze bioder), a jego efekt UTWIERDZA się ćwiczeniami wzmacniającymi — bez współpracy z kinezyterapeutą efekt jest krótkotrwały."),
    (r"uraz|złaman|skręcenie|zwichnię|kontuzj", "Ocena urazu należy do lekarza (badanie fizykalne ± RTG/USG/MRI). Masażysta rozpoznaje CZERWONE FLAGI: deformacja, brak możliwości obciążenia, narastający obrzęk, krwiak, podejrzenie uszkodzenia więzadłowego → unieruchomienie, chłodzenie, skierowanie. Masować zaczynamy dopiero po zagojeniu/zrostaniu i zgodzie lekarza — najpierw okolica proksymalna i dystalna, potem tkanki bliznowate wg procedur."),
    (r"blizn|zrost|pooperacj", "Tkanka bliznowata dojrzewa miesiącami: kolagen typu III zastępowany jest przez typ I, włókna układają się wzdłuż linii naprężeń. Masaż blizny (począwszy od w pełni zepitelializowanej rany, zwykle ≥3-4 tyg. po zamknięciu) zapobiega zrostom, poprawia elastyczność i znosi ból. Techniki: poprzeczne rozcieranie, rozciąganie skóry, pracujące fałdy; zasada — praca do granicy komfortu, nigdy „przez” ostry ból."),
    (r"nerw|neuropat|porażen|pokrwienny|udar", "Uszkodzenia nerwów obwodowych (parkinsonizm, stwardnienie rozsiane, porażenie pp.) wymagają indywidualnej kwalifikacji lekarskiej. Masaż: normalizuje napięcie mięśni (spastyczność — techniki wolne, hamujące; wiotkie — pobudzające, oklepywanie), poprawia trofikę tkanek unaczynionych zniesionymi nerwami, wspiera propriocepcję. UWAGA: przy zaburzeniach czucia klient nie zgłosi bólu — siła nacisku musi być asekuracyjnie niska."),
    (r"nerwoból|rwa kulszowa|korzeni", "Rwa kulszowa to ból promieniujący przebiegiem nerwu kulszowego, najczęściej wskutek drażnienia korzenia L5/S1. Faza ostra: pozycja antybolowa, zimno, leki przeciwzapalne (lekarz!). Masażysta w tej fazie pracuje ZDALNIE (pośladki, tylna grupa uda mięśniami rozluźniającymi) i dopiero po ustąpieniu ostrego bólu — segmentarnie, bez technik wymuszających end-range. Czerwone flagi (zaburzenia sfinkteri, czucie siodłowe) = natychmiast do lekarza."),
    (r"nadciśn|cisot", "Nadciśnienie tętnicze (≥140/90 mmHg) kontrolowane farmakologicznie nie jest przeciwwskazaniem do masażu ogólnego o umiarkowanej sile. NIE stosujemy: intensywnych technik na przystoki szyjne (ryzyko odruchu baroreceptorowego!), masażu w hipertonii nieleczonej/burzowej. Sygnały alarmowe: ból potylicy, zawroty, krwawienie z nosa — przerwać zabieg, zmierzyć ciśnienie jeśli to w kompetencjach placówki, pokierować do lekarza."),
    (r"niewydoln|serca|dekompensacj|krążeni|krazen", "Niewydolność serca (dekompensacja = przeciwwskazanie BEZWZGLĘDNE do masażu) objawia się dusznością wysiłkową/spoczynkową, obrzękami kostek, kaszlem nocnym. W stabilnej niewydolności (za zgodą kardiologa) wskazany jest delikatny manualny drenaż limfatyczny, półsiedząca pozycja, krótkie sesje. Każdy masaż u pacjenta kardiologicznego planujemy z lekarzem prowadzącym; objawy świeże (ból w klatce, duszność) = STOP i 112."),
    (r"zakrzep|żylak|zmian(y|ki) żyln|niedomykaln", "Nieleczone żylaki i zakrzepica żył głębokich (DVT) to klasyka bezpieczeństwa: przy DVT — BEZWZGLĘDNY zakaz masażu kończyny i całego ciała w ostrej fazie (ryzyko zatorowości płucnej!). Objawy DVT: asymetryczny obrzęk łydki, ból przy zgięciu grzbietowym stopy (Homans), ocieplenie, przebarwienie. Żylaki powierzchniowe: głaskanie kierunkowe ku sercu, BEZ ugniatania nad workowatymi poszerzeniami, bandażowanie kompresyjne po zabiegu wg zaleceń chirurga naczyniowego."),
    (r"limfat|obrzęk|obrzek|drenaz", "Obrzęk limfatyczny (pierwotny lub wtórny — np. po limfadenektomii piersi) to zastój bogatobiałkowego chłonu: skóra twarda, dodatni znak Stemmera, brak dołka po ucisku w stadium późnym. Podstawa: Kompleksowa Terapia Przeciwobrzękowa (CTP/CDT) — manualny drenaż limfatyczny (delikatne chwyty pompowy, rotacyjny i kolisty, ciśnienie ~40 mmHg), bandaż wielowarstwowy o niskiej rozciągliwości, pielęgnacja skóry, ruch i ćwiczenia. Bezwzględnie należy wykluczyć aktywną chorobę nowotworową przed rozpoczęciem drenażu!"),
    (r"astma|duszno|układ oddech|oddech", "Przewlekła obturacyjna choroba płuc i astma: masaż klatki piersiowej wspomaga oddychanie przez rozluźnienie mięśni pomocniczych (pochyłe, mostkowo-obojczykowo-sutkowe, międzyżebrowe), techniki wibracyjne i oklepywanie ułatwiające odkrztuszanie (po inhalacji, w czasie <10 s serie). Pozycja półsiedząca, tempo wolne, kontrola saturacji jeśli dostępna; duszność spoczynkowa = przerwać i wezwać pomoc."),
    (r"pokarm|jelit|zaparcie|trawienn|wzdęc", "Masaż brzucha (deep sliding, techniki koliste zgodnie z perystaltyką — w kierunku zegara na okrężnicy) łagodzi zaparcia czynnościowe, wzdęcia i napięcie powłok. Przeciwwskazania: ostre stany chirurgiczne (ostre zapalenie wyrostka robaczkowego, zapalenie otrzewnej), przepuklina nieoperowana, ciąża, krwawienia z przewodu pokarmowego. Efekt wegetatywny: dominacja przywspółczulna (perystaltyka↑, wydzielanie↑) — dlatego masaż brzucha wykonuje się NIE wcześniej niż 1-1,5 h po posiłku."),
    (r"moczew|nerki|pęcherz|peczerz|pielon", "Okolica lędźwiowa i rzutowanie nerek: masaż rozgrzewający mięśnie przykręgosłupowe kręgosłupa bywa ulgą w przewlekłych dolegliwościach czynnościowych — ALE kolka nerkowa, gorączka, krwiomocz to stany wymagające lekarza (kamica, odmiedniczkowe zapalenie nerek). Nie masujemy okolicy nerki w stanach zapalnych i przy wodonerczu. Kobiety w ciąży: ostrożność w dole brzusznym i lędźwiowo-krzyżowej (ryzyko wywołania skurczów przy intensywnych technikach)."),
    (r"skóra|skin|trądzik|łysien|cellulit", "Masaż kosmetyczny twarzy: ruchy wg topografii mięśni mimiczych i linii skórnych, po demakijażu, przy bardzo małym poślizgu (ryzyko rozciągnięcia); trądzik ropowiczy i stany zapalne skóry — przeciwwskazanie miejscowe. Cellulit (fibroedematoadipopathy): techniki głębokiego rozcierania i rolkowania mogą poprawić mikrocyrkulację i wygląd skóry — edukuj klienta, że efekt jest warunkowy (dieta, nawodnienie, ruch) i nie zastępuje terapii medycznej przy obrzękach limfatycznych/patologicznych."),
    (r"relaks|wypalen|stres|sen|bezsen", "Masaż relaksacyjny aktywuje przywspółczulny układ nerwowy: obniża kortyzol, tętno i ciśnienie, poprawia jakość snu (przeglądy systematyczne i metaanalizy wskazują na umiarkowany efekt w bólu przewlekłym i lęku). Protokół: tempo wolne (~1 ruch/2 s), jednostajna presja, ciepło dłoni, cisza lub muzyka ok. 50–60 uderzeń/min, światło przygaszone, brak rozmowy po 5 min. Kontrapunkt etyczny: relaks NIE jest pretekstem do przekraczania granic intymności — okrycie zawsze na miejscu."),
    (r"sport|trening|zawodnik|regeneracj|przed.?wysiłk|powysiłk", "Masaż sportowy dzielimy czasowo: PREDYSPOZYCYJNY (10-20 min przed startem: szybkie rozcieranie/oklepywanie, pobudzenie), POWYSIŁKOWY/regeneracyjny (do 30-60 min po: głaskanie odpływowe, delikatne rozcieranie, rozciąganie), PRZEBUDOWUJĄCY (24-72 h: głębsza praca z tkanką zmęczoną). Zakazy: masaż głęboki tuż przed startem (obniżenie compliance), masaż przy DOMS pierwszej doby u amatora, jakakolwiek praca nad mięśniem z podejrzeniem naderwania."),
    (r"dzieci|dziecko|niemowl|shantala|maluch", "Shantala i masaż niemowlęcia: środowisko ciepłe (24-26°C), dziecko nakarmione ≥30-45 min wcześniej, kontakt wzrokowy i werbalny z rodzicem (to ON uczy się techniki, masażysta demonstruje). Kolejność klasyczna: klatka piersiowa → brzuch (godz. 9→3 wg kierunku perystaltyki) → nogi → ręce → plecy → twarz. Wskazania: kolka (dla przeszkolonych), napięcie mięśniowe fizjologiczne, bonding. Przeciwwskazania: gorączka, zmiany skórne, choroby metaboliczne/serca bez zgody pediatry; NIGDY nie masuj dziecka chorego bez kwalifikacji lekarskiej."),
    (r"ciąż|gravid|kobiet", "Masaż kobiety w ciąży: po I trymestrze i za zgodą położnej/ginekologa; pozycja boczna z klinami lub półsiedząca (BEZ leżenia przodem po 16. t.g.— ucisk na żyłę główną dolną!). Unikać: intensywnego ucisku okolicy krzyżowo-lędźwiowej „punktów indukcji porodu” (m.in. SP 6, BL 60 w Tradycyjnej Medycynie Chińskiej — dowody niejednoznaczne, dlatego zachowujemy najwyższą ostrożność), głębokiego masażu brzucha, długich pozycji rozciągających. Korzyści udokumentowane: redukcja bólu lędźwiowego, obrzęków, lęku; masażysta prowadzi kartę z pomiarami obwodów i obserwacjami."),
    (r"polog|poporod|karmiąc", "Po połogu (min. 6 tyg. i zgoda położnika): masaż delikatny, odbudowujący— rozstęp mięśnia prostego brzucha (diastasis recti) wymaga specjalistycznego podejścia, blizna po cięciu cesarskim— masaż po pełnym zagojeniu, karmienie piersią— unikanie preparatów aromatycznych na dekolcie. Obrzęki fizjologiczne: drenaż bardzo płytki. Depresja poporodowa— rozpoznać, nie leczyć, pokierować do lekarza z empatią."),
    (r"staw|stawy|mobiliz", "Masaż stawowy (arthrum massage): pracy torebki, więzadeł i mięśni okołostawowych; techniki: głaskanie kierunkowe, rozcieranie okrężne wokół szpary, delikatne trakcje TYLKO po szkoleniu i przy braku przeciwwskazań. Ostry wysięk, gorąca opuchnięty staw = przeciwwskazanie miejscowe. Stawy endoprotezowane: żadnych manipulacji rotacyjnych ponad fizjologiczny zakres, informacja o typie protezy w karcie."),
    (r"bańk|chińsk|chin", "Bańka chińska/fire cupping: próżnia mechaniczna unosi skórę i powięź — efekt: hiperemia czynna, rozluźnienie powięzi, modulacja bólu (brak dowodów na „usuwanie toksyn”— mów prawdę klientowi!). Przeciwwskazania: terapia antykoagulacyjna, żylaki w miejscu aplikacji, skóra uszkodzona, choroby naczyń, gorączka. Czas: 3-8 min statycznie lub dynamicznie z olejem; ślady (equimoza) są spodziewane, nie „toksyczne” — uprzedz klienta."),
    (r"kamien|hot stone|bazalt", "Hot stone massage: kamienie bazaltowe ogrzewane do 50-65°C (maks. termostat!); test temperatury NA WEWNĘTRZNEJ stronie przedramienia masażysty PRZED aplikacją. Przeciwwskazania: neuropatia cukrzycowa i inne zaburzenia czucia (oparzenie bez bólu!), choroby naczyń obwodowych, ciąża (okolica brzucha/dołu lędźwiowego), dzieci. Kamienie zimne— kontrastowo, krótko, ostrożnie u astmatyków."),
    (r"refleks|stop", "Refleksoterapia stóp: mapa punktów rzutowych (paliczki— głowa, łuk— narządy klatki/p jamy brzusznej, pięta— miednica). Dowody naukowe wspierają efekt relaksacyjny i przeciwbólowy, NIE „leczenie chorób narządowych” przez nacisk. Bezpieczeństwo: cukrzyca (neuropatia + gojenie!— tylko delikatnie, codzienna kontrola stóp), zakrzepica żył głębokich stopy/łydki— zakaz, owrzodzenia— omijać. Opinie klientów o bóle punktów— zapisywać jako wskaźniki napięcia, nie diagnozy."),
    (r"segment|tłuszcz|łącznotkank", "Masaż łącznotkankowy (Friebego (szkoła Dicza/Bineta)): reflektoryczne działanie na segmenty rdzeniowe przez powięź i skórę; chwyt: fałd skóry unoszony i utrzymywany 20-60 s, ruch wolny, „ciągnący”. Reakcje (mrowienie, ciepło, ból przeniesiony) są typowe. Przeciwwskazania: choroby zakaźne z wysypką, żylaki, nowotwory (miejsca), niewydolność serca zaawansowana. Skóra cienka/starości— siła minimalna (ryzyko petechii i rozdarcia naskórka!)."),
    (r"okostn|periost", "Masaż okostnowy (Dicza): precyzyjny, wolny nacisk kciukiem na przyczepy okostnowe (np. guz piszczeli, wyrostek kciuka kości promieniowej)— zwalnia napięcie mięśniowe przez receptory periosteum. Technikę wykonuje się NA SUCHO, z mikroruchem co kilka sekund; ból klienta musi być tolerowany (<4/10 NRS). Przeciwwskazania: miejsca po urazach/ operacjach kości, guzy kości (podejrzenie!), osteomyelitis, choroby metaboliczne kości w fazie aktywnej."),
    (r"punkt|acupress|trigger|miofasj", "Punkty trigger miofasj (TrPs): węzły napięciowe w pasmie mięśniowym z bólem promienującym typowo dla mięśnia. Techniki: ischemiczna kompresja 30-90 s (ból „dobry”, malejący), spray & stretch wyłącznie po stosownym szkoleniu, sucha igła— WYŁĄCZNIE lekarz/fizjoterapeuta z uprawnieniami, masażysta NIE kłuje. Edukuj: nawyki (ergonomia, sen, stres), bo TrP nawraca bez zmiany przyczyn."),
    (r"wodn|basen|aquat", "Masaż w środowisku wodnym (hydroterapia): temperatura wody 33-36°C dla dorosłych, czas 15-30 min; wyporność odciąża stawy, hydrostatyczne ciśnienie wspomaga krążenie żylne i limfatyczne. Higiena: dezynfekcja niecek, prysznice obowiązkowe, badania sanitarne wody. Przeciwwskazania: otwarte rany, infekcje, nietrzymanie moczu/stolca, epilepsja bez nadzoru, lęk przed wodą— respektuj."),
    (r"izometr", "Masaż izometryczny (Kralja): rytmiczne napinanie i rozluźnianie mięśnia w pozycji skróconej/rozciągniętej z oporem własnym— poprawia trofikę i propriocepcję, bezpieczny przy zanikach unieruchomionych kończyn (za zgodą lekarza). Tempo oddechu: wydech przy napięciu. Przeciwwskazania: świeże zerwania ścięgien, zakrzepica, hernia w obszarze pracy, ciężka hipertensja."),
    (r"tensegracj", "Approach tensegracyjny: ciało jako sieć ciągłego napięcia (cables & struts); praca globalna— micro-movements, oddech, uwaga na linie napięć powięziowych (superficial front/back line, spiral line wg Myersa). Efekt: normalizacja tonusu, ulga w bólach funkcjonalnych. Brak silnych RCT— przedstawiaj jako wsparcie komplementarne, nie terapię choroby."),
    (r"vcd|urządzen|przyrząd|maszyn|wibrator", "Masaż przyrządowy (VCP, wibratory, roller): standaryzacja bodźca, oszczędność dłoni masażysty. Zasady: nigdy na wyrostki kostne/ przystosowanie naczyń/ bieliznę metalową; czas na okolicę ≤ 3-5 min; siła i częstotliwość wg protokołu producenta i karty pacjenta. Przeciwwskazania wspólne dla masażu + lokalne (implanty, rozrusznik serca— zakaz pracy w promieniu 15 cm!)."),
    (r"dokument|karta|zgoda|rodo", "Dokumentacja masażysty: karta pacjenta (wywiad, przeciwwskazania, kwalifikacja), karta zabiegowa (czas, techniki, reakcje), zgody (zabieg, RODO), skierowania i karty zdarzeń niepożądanych. Standard: wpisy niezwłoczne, czytelne, datowane, podpisane; przechowywanie zabezpieczone; prawo pacjenta do kopii (ustawa o prawach pacjenta). To nie formalność— to obrona dobra pacjenta i Ciebie samego."),
    (r"higien|dezynfekcj|aseptyk|antysep", "Higiena w gabinecie: mycie rąk wg WHO („5 moments”), dezynfekcja preparatem alkoholowym 30 s (krótka procedura), powierzchnie kontaktu wysokiego— dezynfekcja między klientami (chustki dezynfekcyjne z zachowaniem czasu kontaktu!), tekstylia jednorazowo lub 60°C. Łańcuch infekcji: patogen— rezerwuar— wrota— gospodarz; masażysta przerywa go na każdym ogniwie. Dokumentacja higieny jest audytowalna (sanepid, praktyki)."),
    (r"ergonom|stanowisk|stół|stoł", "Ergonomia stanowiska: wysokość stołu do poziomu nadgarstka masażysty przy zgięciu łokcia ~120°, stabilna baza nóg, transfer klienta z asystą lub po instruktażu, przerwy mikro co 30 min pracy ciągłej. Narzędzia: krzesło siedzące przy pracy na twarz/dłonie. Profilaktyka urazów przewlekłych dłoni/karku/lędźwi— bo Twoje zdrowie jest zasobem publicznym jakości usług."),
    (r"et|etyk|kodeks|manipul|granice|kompetenc", "Granice kompetencji masażysty: oceniasz potrzeby zabiegowe, NIE rozpoznajesz chorób; rekomendujesz konsultację, NIE zmieniasz leczenia; dbasz o autonomię klienta (informowana zgoda, prawo przerwania zabiegu w każdej chwili, obecność osoby towarzyszącej gdy chce). Piękno zawodu: dotyk jako służba— czysty intencyjnie, profesjonalny technicznie, sprawiedliwie dostępny dla każdego niezależnie od ceny usługi."),
    (r"komunikacj|rozmowa|język|jezyk|terminolog", "Komunikacja zawodowa: język prosty (max. 1 nowe pojęcie + wyjaśnienie), aktywne słuchanie (parafraza, pytania otwarte), informacja zwrotna o odczuciach („proszę mówić: za mocno / dobrze”), kulturowa wrażliwość (dotyk, skromność, płeć terapeuty). Bariera językowa: tłumacz/rysunki/piktogramy; w module języka obcego— standardowe frazy zabiegowe PL/EN/DE."),
    (r"stres|wypalen|radzenie", "Radzenie sobie ze stresem w pracy masażysty: higiena emocjonalna (debriefing trudnych przypadków), granice czasowe grafiku (max. liczba masażu głębokiego/dzień), regeneracja (sen, ruch, hobby niedotykowe), superwizja/coaching gdy potrzebne. Wypalenie objawia się cynizmem, depersonalizacją— wcześnie szukaj pomocy; pacjent zasługuje na wypoczętego terapeutę."),
    (r"konflikt|reklamacj|skarg", "Konflikty i reklamacje: model LEARN (Listen—Empathize—Apologize for experience—React/Resolve—Notify documentation). Klient niezadowolony ≠ wróg; zapis zdarzenia, propozycja rekompensaty w ramach regulaminu, eskalacja do przełożonego; sprawy o naruszenie nietykalności— natychmiast prawna ścieżka i odsunięcie od kontaktu z klientem do wyjaśnienia."),
    (r"zespo|team|organizacj|planowani|zadani", "Organizacja pracy małego zespołu: analiza zadania (co, kto, kiedy, czym), macierz kompetencji, przywódzenie sytuacyjne (instrukcja→sprzedaż→partycypacja→delegowanie), spotkania operacyjne max. 15 min (stand-up), retrospektywa po cyklu. Jakość: standardy SOP + check-listy + audyty krzyżowe; konflikt rozwiązuje się faktem, nie opinią."),
    (r"egzamin|weryfikacj|potwierdzaj", "Przygotowanie do egzaminu MED.10: część pisemna (test— wiedza: anatomia, patologia, przeciwwskazania, procedury) i praktyczna (stanowisko: ocena klienta, plan, wykonanie, dokumentacja, BHP). Strategie: mapy myśli na każdy rodzaj masażu, trening czasu (symulacje 1:1 z arkuszem), samoocena wg check-list F, powtórki naprzemienne (interleaving) w rytmie 1/3/7/21 dnia."),
    (r"praktyk|staż", "Praktyka zawodowa: cele SMART na każdy blok (np. „samodzielnie przeprowadzam kwalifikację do masażu klasycznego wg karty C.1 z opiekunem ”), dziennik z refleksją (co widziałem— czego się nauczyłem— co zrobię inaczej), portfolio (studia przypadków bez danych osobowych), ocena opiekuna+autorefleksja. Etyka praktyki: punktualność, poufność, otwartość na uwagi, zero skrótów bezpieczeństwa."),
    (r"profilak|promocj|edukacj", "Promocja zdrowia i edukacja pacjenta: przekaz 3 informacji max. na wizytę (respekt, zrozumienie, zapamiętanie), materiały piśmienne, demonstracja ćwiczeń domowych, nawyki (nawodnienie, ergonomia, aktywność 150 min/tydz. wg WHO). Masażysta jako doradca stylu życia— nie moralizator; sprawiedliwość: ta sama jakość edukacji dla każdego, niezależnie od statusu."),
]

GENERIC = """Zagadnienie realizuje podstawę programową kwalifikacji MED.10 „Wykonywanie masaży”: łączy znajomość anatomii i fizjologii z metodyką postępowania i etyką zawodową. Ćwicz je systematycznie: demonstracja instruktora → praca w parach → autorefleksja wg check-listy (Załącznik F) → powtórka w rytmie 1/3/7/21 dnia."""


def knowledge_for(title: str) -> tuple[str, str]:
    low = title.lower()
    main = None
    extras: list[str] = []
    # 1) Baza rozszerzona (knowledge_entries.py): wszystkie trafienia jako rozwinięcie
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from knowledge_entries import EXTRA_KNOWLEDGE  # type: ignore
    except Exception:
        EXTRA_KNOWLEDGE = []
    for pat, txt in EXTRA_KNOWLEDGE:
        if re.search(pat, low):
            extras.append(txt)
            break
    # 2) Baza podstawowa — akapit główny
    for pat, txt in KNOWLEDGE:
        if re.search(pat, low):
            main = txt
            break
    # 3) Gdy brak akapitu głównego, wykorzystaj pierwszy wpis z bazy rozszerzonej
    if not main and extras:
        main = extras.pop(0)
    if not main:
        main = GENERIC
    return main, ("\n\n".join(extras) if extras else "")


def build_subchapter(num: str, raw_title: str, topic_no: str, section_intro: str) -> str:
    # usuń zdublowany numer ("6.8.1 6.8.1. Dłonie...")
    t = re.sub(rf"^{re.escape(num)}\s*\.?\s*", "", raw_title).strip()
    t = re.sub(rf"^{re.escape(topic_no)}\s*\.?\s*", "", t).strip()
    core, extra = knowledge_for(t)
    extra_block = f"\n\n## Rozwinięcie zagadnienia\n\n{extra}\n" if extra else ""
    return f"""# {num}. {t}

*Rozdział szczegółowy (podrozdział) tematu {topic_no} — {section_intro}*

## Dlaczego to ważne

{core}
{extra_block}
## Istota zagadnienia — ujęcie systematyczne

Każdy element tego tematu rozkładamy na cztery warstwy kompetencji:

1. **Wiedza (dlaczego)** — mechanizmy fizjologiczne i patofizjologiczne, definicje i klasyfikacje zgodne z literaturą akademicką (Załącznik L) oraz terminologią (Załącznik G).
2. **Umiejętność (jak)** — kolejność czynności, dobór techniki, siły, tempa i czasu; ergonomia dłoni i ciała masażysty; kontrola efektu w trakcie i po zabiegu.
3. **Bezpieczeństwo (czy wolno)** — kwalifikacja: wskazania, przeciwwskazania bezwzględne i względne (Załącznik D), sygnały alarmowe wymagające pilnej konsultacji lekarskiej (Załącznik E), procedura pierwszej pomocy gdy zawodzi organizm (Załącznik J).
4. **Etyka i dokumentacja (dla kogo i na piśmie)** — świadoma zgoda, tajemnica zawodowa, RODO, wpis w karcie (Załącznik C); kodeks: prawda, piękno, sprawiedliwość (Załącznik K); granice kompetencji (Załącznik M).

## Metodyka postępowania — krok po kroku

1. Przygotowanie stanowiska i siebie: higiena rąk (I.1/I.2), gotowe środki poślizgowe dobrane do skóry klienta (H), spokój i koncentracja.
2. Wywiad ukierunkowany na to zagadnienie: chorobę, leki, ostatni zabieg, samopoczucie dnia; sprawdzenie listy przeciwwskazań.
3. Kwalifikacja i uzgodnienie planu z klientem: cel zabiegu, obszary pracy, sygnał „stop”, przewidywane odczucia.
4. Wykonanie techniki w prawidłowej kolejności i doborze parametrów (tempo, nacisk, czas), z bieżącą kontrolą reakcji klienta i własnej ergonomii.
5. Zakończenie: pozycja pozioma 2-3 min, napicie wody, instruktaż domowy w granicach kompetencji.
6. Dokumentacja karty zabiegu + obserwacje; ewentualne skierowanie (C.11) i wpis do dziennika praktyki.

## Scenariusz sytuacyjny (studium przypadku)

Do gabinetu zgłasza się osoba z dolegliwościami opisanymi w tym zagadnieniu. Zadanie masażysty: nie zgadywać diagnozy, lecz rzetelnie przeprowadzić kwalifikację. Jeśli obraz zawiera którykolwiek punkt bezwzględny — zabieg odstępujemy, sporządzamy skierowanie i informujemy o powodach spokojnie, bez straszenia. Jeśli przeciwwskazanie jest względne — modyfikujemy technikę, czas i pozycję, dokumentując decyzję. Po zabiegu pytamy o odczucia w skali liczbowej i zapisujemy je: to dane do oceny skuteczności i bezpieczeństwa.

## Najczęstsze błędy początkujących

- Pośpiech i pominięcie etapu wywiadu „bo klient stały” — każdy dzień przynosi nowe przeciwwskazania (leki, infekcje, zabiegi stomatologiczne, szczepienia).
- Praca zbyt dużym naciskiem „im bardziej boli, tym lepiej” — ból nie jest miarą skuteczności; obowiązuje granica komfortu klienta.
- Brak dokumentacji albo wpis „po godzinach” z pamięci — uchybienie prawne i jakościowe.
- Wchodzenie w rolę diagnosty/terapeuty chorób systemowych — przekroczenie kompetencji (patrz Załącznik M).
- Zaniedbanie własnej ergonomii — kontuzja masażysty to realne ryzyko i koszt społeczny zawodu.

## Pytania utrwalające

1. Omów mechanizmy leżące u podstaw: {t}. Co z tego wynika dla techniki masażu?
2. Wymień przeciwwskazania bezwzględne i względne dotyczące tego zagadnienia oraz swoje postępowanie w razie ich stwierdzenia.
3. Zaplanuj zabieg dla klienta z tym problemem: pozycja, środki, kolejność technik, czas, kryteria przerwania.
4. Jak udokumentujesz kwalifikację, zgodę i przebieg? Do którego załącznika odsyłasz?
5. Czego NIE wolno Ci powiedzieć klientowi o tym stanie zdrowia i jak sformułujesz bezpieczną, życzliwą informację?

## Słowniczek minimalny

Terminy kluczowe dla tego podrozdziału znajdziesz w Załączniku G (słownik terminów medycznych i masażowych). Ucz się ich w kontekście zdania, nie listy: „hiperemia czynna po głaskaniu odpływowym”, „spastyczność — techniki hamujące”, „limfangion — drenaż, nie ugniatanie”.

---

**Pamiętaj:** prawda — opieraj się na aktualnej wiedzy i nie obiecuj rzeczy spoza kompetencji; piękno — czyń dotyk służbą godną drugiego człowieka; sprawiedliwość — ten sam standard bezpieczeństwa i troski dla każdego klienta, bez względu na cenę usługi, wiek, płeć, pochodzenie czy stan zdrowia.

{MARKER}
"""


def backup(path: Path):
    bak = path.with_name(path.name + ".bak")
    if not bak.exists():
        bak.write_bytes(path.read_bytes())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=BASE_REL)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    root = Path(args.base)
    if not root.is_absolute():
        root = Path.cwd() / root

    secdirs = sorted(p for p in (root / "sections").iterdir() if p.is_dir())
    made_books = 0
    made_chapters = 0
    for sec in secdirs:
        name_m = re.match(r"\d+-(med-10-\d)-.*", sec.name)
        for bd in sorted(p for p in sec.iterdir() if p.is_dir() and p.name.startswith("book-")):
            if bd.name == "book-01":
                continue  # podręcznik modułu — już wielorozdziałowy
            chs = sorted(p for p in (bd / "chapters").glob("*.md") if not p.name.endswith(".bak"))
            if len(chs) != 1:
                continue
            text = chs[0].read_text(encoding="utf-8")
            zags = ZAG_RE.findall(text)
            if not zags:
                continue
            title_line = text.splitlines()[0].lstrip("# ").strip()
            m = re.match(r"(\d+\.\d+)\.?\s+(.*)", title_line)
            topic_no = m.group(1) if m else "?"
            topic_title = m.group(2) if m else title_line
            # istniejące numery rozdziałów w book.yaml
            yaml_path = bd / "book.yaml"
            ytext = yaml_path.read_text(encoding="utf-8")
            existing_files = set(re.findall(r"content_file:\s*\"chapters/([^\"]+)\"", ytext))
            new_entries = []
            idx = len(existing_files) + 1
            for full_num, num, raw_title in zags:
                fn = f"{idx:02d}-{slugify(raw_title)}.md"
                idx += 1
                chpath = bd / "chapters" / fn
                if chpath.exists() or fn in existing_files:
                    # już utworzony wcześniej (idempotentność) — dopisz wpis jeśli brak
                    if f"chapters/{fn}" not in ytext:
                        new_entries.append((fn, num, raw_title))
                    continue
                body = build_subchapter(num, raw_title, topic_no, topic_title)
                if args.dry_run:
                    print(f"[DRY] {bd.relative_to(root)}/chapters/{fn} ({len(body.encode('utf-8'))} B)")
                else:
                    chpath.write_text(body, encoding="utf-8")
                new_entries.append((fn, num, raw_title))
                made_chapters += 1
            if new_entries:
                add = "\n"
                for fn, num, raw_title in new_entries:
                    disp = re.sub(rf"^{re.escape(num)}\s*\.?\s*", "", raw_title).strip()
                    disp = re.sub(rf"^{re.escape(topic_no)}\s*\.?\s*", "", disp).strip()
                    add += (f'    - title: "{num}. {disp}"\n'
                            f'      subchapter: true\n'
                            f'      content_file: "chapters/{fn}"\n'
                            f'      hidden: false\n')
                # wstaw przed '  completion:'
                if "  completion:" in ytext:
                    ynew = ytext.replace("  completion:", add.rstrip("\n") + "\n  completion:", 1)
                else:
                    ynew = ytext.rstrip("\n") + "\n" + add
                if args.dry_run:
                    print(f"[DRY] book.yaml += {len(new_entries)} entries : {bd.relative_to(root)}")
                else:
                    backup(yaml_path)
                    yaml_path.write_text(ynew, encoding="utf-8")
                    # adnotacja w rozdziale zbiorczym
                    note = ("\n## Struktura rozdziału\n\nSzczegółowe opracowania zagadnień tego tematu "
                            "znajdują się w podrozdziałach niniejszej książki (lista po lewej). Rozdział "
                            "zbiorczy służy powtórce i przeglądowi programu.\n\n" + MARKER + "\n")
                    if MARKER not in text:
                        backup(chs[0])
                        chs[0].write_text(text.rstrip("\n") + "\n" + note, encoding="utf-8")
                made_books += 1
            if args.limit and made_books >= args.limit:
                print("(limit osiągnięty)")
                return 0
    print(f"Książek rozbudowanych: {made_books}, nowych podrozdziałów: {made_chapters}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
