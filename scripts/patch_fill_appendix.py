#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_fill_appendix.py — naprawa mapowań i treści skryptu
scripts/fill_appendix_books_naturopata.py (kurs Naturopata, załączniki A–K).

Zakres napraw (potwierdzone audytem stanu kursu):
1. norm_key(): rozdziały Załącznika K mają w nazwach przedrostek błędny «j-»
   (zamiast «k-») — mapowanie uwzględnia teraz katalog docelowy; analogicznie
   duplikaty w F/G/H/I o przedrostkach e-/f-/g-/h- mapują się na właściwe
   słowniki sekcji.
2. Poprawki merytoryczne istniejących treści (literówki, obce znaki CJK,
   urwane zdania): b-10, f-5, f-6, g-6, g-9, h-4, h-5, j-3, k-2, k-5, k-9.
3. Usunięcie zduplikowanych linii otwierających dict B_SKILLS (b-15/b-16).
4. Dołożenie brakujących wpisów: h-16..h-30 (powtórzone pozycje spisu H),
   i-11..i-15, e-2/e-8/e-10 (dodatkowe rozdziały F) oraz nowe słowniki
   E_F/DUP_G/DUP_H/DUP_I i rejestr ALL_APPENDIX_CONTENT z wieloma mapowaniami
   na jedną sekcję.

Skrypt jest idempotentny: każdy krok sprawdza warunek przed zastosowaniem.
Użycie: python3 scripts/patch_fill_appendix.py
"""
from pathlib import Path

P = Path("/workspace/scripts/fill_appendix_books_naturopata.py")
src = P.read_text(encoding="utf-8")


def rep(old, new, required=True):
    global src
    if old in src:
        assert src.count(old) == 1, f"wieloznaczność: {old[:60]!r}"
        src = src.replace(old, new)
        print("OK :", old.splitlines()[0][:70])
    elif required:
        raise SystemExit(f"BLAD: nie znaleziono: {old[:80]!r}")
    else:
        print("SKIP (już naprawione):", old.splitlines()[0][:70])


# --------------------------------------------------------------------------
# 1. norm_key + mapowania per-sekcja
# --------------------------------------------------------------------------
OLD_NORMKEY = '''def norm_key(stem: str) -> str:
    # '01-a-1-podreczniki...' -> 'a-1'; '05-j-5-technika...' -> 'j-5' (fallback)
    m = re.match(r"^\\d+-([a-k]-\\d+)", stem.lower())
    if m:
        return m.group(1)
    m = re.match(r"^\\d+-([a-k]\\.\\d+)", stem.lower())
    if m:
        return m.group(1).replace(".", "-")
    return ""
'''
NEW_NORMKEY = '''# Prefiks literowy faktycznie używany w nazwach plików rozdziałów bywa
# przesunięty o jedną literę względem załącznika (historyczny błąd generatora):
# Załącznik K ma pliki "NN-j-M-…", dodatkowe rozdziały F mają "e-*", G "f-*",
# H "g-*", I "h-*". Poniższa tabela normalizuje klucz do literki WŁAŚCIWEJ
# dla słownika danej sekcji.
PREFIX_FIX = {
    "30-zalacznik-f-przeciwwskazania/book-01": {"e": "e"},   # dodatkowe pozycje E.*
    "31-zalacznik-g-mapy-anatomiczne/book-01": {"f": "f"},   # dodatkowe pozycje F.*
    "32-zalacznik-h-schematy-masazu/book-01": {"g": "g"},    # dodatkowe pozycje G.*
    "33-zalacznik-i-kinezyterapia/book-01": {"h": "h"},      # dodatkowe pozycje H.*
    "35-zalacznik-k-zabiegi-felczerskie/book-01": {"j": "k", "k": "k"},
}


def norm_key(stem: str, sec: str = "") -> str:
    # '01-a-1-podreczniki...' -> 'a-1'; '05-j-5-technika...' (sekcja K) -> 'k-5'
    m = re.match(r"^\\d+-([a-k]-\\d+)", stem.lower())
    if not m:
        m = re.match(r"^\\d+-([a-k]\\.\\d+)", stem.lower())
        if m:
            return m.group(1).replace(".", "-")
        return ""
    letter, num = m.group(1).split("-")
    fix = PREFIX_FIX.get(sec)
    if fix and letter in fix:
        letter = fix[letter]
    return f"{letter}-{num}"
'''
rep(OLD_NORMKEY, NEW_NORMKEY)

rep(
    'key = norm_key(ch.stem)',
    'key = norm_key(ch.stem, sec_book)',
)

# --------------------------------------------------------------------------
# 2. Poprawki merytoryczne / językowe istniejących wpisów
# --------------------------------------------------------------------------
rep('**Kryteria:** przeprowadzenie zabiegu z kartą parametrów (C.2) oraz edukacja\npacjenta o zagrożeniach (oparzenia, odmrożenia, poparzenia słoneczne, fotouczulenia ziołowe — dziurawiec, pasternak!),\nprzeciwwskazania (F.5) oraz zapis parametrów w karcie zabiegowej (C.2).',
    '**Kryteria:** przeprowadzenie zabiegu z kartą parametrów (C.2); edukacja pacjenta\no zagrożeniach (oparzenia, odmrożenia, poparzenia słoneczne, fotouczulenia\nziołowe — dziurawiec, pasternak!) i przeciwwskazaniach (F.5).')

rep(': **Hydroterapia:** kąpiele perełkowe (36–38 °C, 10–15 min), naprzemienne',
    '- **Hydroterapia:** kąpiele perełkowe (36–38 °C, 10–15 min), naprzemienne')

rep('nowotwór w obszarze, zaburzenia czucia (oparzenie!), niewydolność serca\n(generalne kąpiele gorące), ciąża (jamа brzuszna), antykoagulacja (naczynia?),\nzakrzepica, skóra uszkodzona.',
    'nowotwór w obszarze, zaburzenia czucia (oparzenie!), niewydolność serca\n(generalne kąpiele gorące), ciąża (jama brzuszna), antykoagulacja,\nzakrzepica, skóra uszkodzona.')

rep('**UV:** fotoudulenie (leki: doksycyklina, diuretytia tiazydowe, retinoidy,\nhiperycyna!), bielactwo (ryzyko), przebyte nowotwory skóry, xeroderma\npigmentosum, choroby autoimmunologiczne (toczeń — BEZWZGLĘDNIE).',
    '**UV:** fotouczulenie (leki: doksycyklina, diuretyki tiazydowe, retinoidy,\nhiperycyna!), bielactwo (ryzyko), przebyte nowotwory skóry, xeroderma\npigmentosum, choroby autoimmunologiczne (toczeń — BEZWZGLĘDNIE).')

rep('2. **Dzieci:** mięta pieprzowa/eukaliptus/kamfora < 6 lat (ryzyko skurczu krtani), kwas acetylosalicylowy zawarty w kwiatach? (ogólnie: ASA nie dziecim), lukrecja — hipertensja, senos/liście senna — odwodnienie.',
    '2. **Dzieci:** mięta pieprzowa/eukaliptus/kamfora < 6 lat (ryzyko skurczu krtani); ASA nie dla dzieci (zespół Reye’a); lukrecja — nadciśnienie; liście/senne zioła przeczyszczające (senna, kruszyna) — tylko doraźnie, ryzyko odwodnienia i zaburzeń elektrolitowych.')

rep('4. **Choroby:** nefropatia — unikać ziół z arbutiną? (ostrożeń: żółty kapsy? ) → ogólnie: przy chorobie nerek unikać dużych dawek potasu, oksalanów (szczaw, rabarbar), ziół «diuretycznych» bez kontroli; choroba wątroby — kava, żywotnik, pieprz afrykański, napar z szałwii duże ilości; hiperbilirubinia.',
    '4. **Choroby:** przy chorobie nerek unikać dużych dawek potasu (pokrzywa, mniszek), oksalanów (szczaw, rabarbar) i silnych ziół moczopędnych bez kontroli lekarskiej; przy chorobie wątroby — bez kavy, żywotnika zachodniego i dużych dawek ziół «detoksykacyjnych»; ostrożnie przy hiperbilirubinemii.')

rep('5. **Alergia krzyżowa:** Asteraceae (rumianek, arnika, krwawnik) przy alergii na bylicę/chryzantemę; pyłki brzozy → jabłko/marchew zioła?',
    '5. **Alergia krzyżowa:** Asteraceae (rumianek, arnika, krwawnik) przy uczuleniu na bylicę/chryzantemę; alergia na pyłki brzozy → reakcje krzyżowe z jabłkiem, marchwią, kminkiem.')

rep('6. **Zabiegi chirurgiczne w planie:** odstaw zioła wpływające na krzepnięcie i glikemię 2 tyg. przed (dziurawiec, czosnek, imbir, kurkuma, miłorząb, chamomile duże dawki).',
    '6. **Zabiegi chirurgiczne w planie:** odstaw zioła wpływające na krzepnięcie i glikemię na 2 tygodnie przed (dziurawiec, czosnek, imbir, kurkuma, miłorząb, duże dawki rumianku).')

rep('7. **Surowce toksyczne:** napar z nasienników? → absolutny zakaz: tojad, konwalia (glikozydy), bieluń, wroniec, napar z pestek moreli/cyjanidry; «zioła» z nieznanego źródła — metale ciężkie, pestycydy, adulteracja.',
    '7. **Surowce toksyczne — absolutny zakaz:** tojad, konwalia (glikozydy nasercowe), bieluń, wroniec, nektar/napar z pestek moreli i wiśni (cyjanidry); «zioła» z nieznanego źródła — ryzyko metali ciężkich, pestycydów i domieszek (adulteracja).')

rep('- **Du Mai (GV)** — linia pośrodkowa tyłu: GV20 Baihui (ciemieniuszko), GV14 Dazhui (poniżej C7).\n- Przykłady常用 punktów kończynowych:',
    '- **Du Mai (GV)** — linia pośrodkowa tyłu: GV20 Baihui (ciemieniowo), GV14 Dazhui (poniżej C7).\n- Przykłady często stosowanych punktów kończynowych:')

rep('2. **Płat środkowy/język** — leżenie tyłem, uniesienie boków tułowia? → pozycja: leżenie na zdrowym boku, łóżko uniesione 20–30°, poduszka pod klatkę侧.',
    '2. **Płat środkowy / jęzik lingualny (języczek)** — leżenie na zdrowym boku z rotacją tułowia o ¼ obrotu ku przodowi, łóżko uniesione 20–30°, poduszka zabezpieczająca plecy.')

rep('3. **Płat dolny segmenty apikalne** — leżenie przodem z miednicą wyżej niż głowa (Trendelenburg odwrócony 20–30°), poduszka pod brzuchem.',
    '3. **Płat dolny — segment apikalny (S6)** — leżenie przodem z miednicą wyżej niż głowa (Trendelenburg odwrócony 20–30°), poduszka pod brzuchem.')

rep('Po każdej pozycji: klepanie/fistaszting? → perkusja dłonią lejkowatą nad\ndanym polem płucnym (z dala od kręgosłupa i sutków), następnie kaszel kontrolowany\n(huffing). Astma/POChP: pozycje + oddech z oporem wydechu (usta spięte).',
    'Po każdej pozycji: perkusja (klapping) dłonią lejkowatą nad danym polem\npłucnym (z dala od kręgosłupa i sutków), następnie kaszel kontrolowany\n(huffing). Astma/POChP: pozycje + oddech z oporem wydechu (usta spięte).')

rep('3. **Profilaktyka nawrotów:** trening mięśni głębokich (brzuch «drawing-in», multitify? → prostowniki), ergonomia dźwigania, ćwiczenia McKenzie\'ego (extension prone press-ups — wg odpowiedzi directional preference), I.4? → I.8/postawa.',
    '3. **Profilaktyka nawrotów:** trening mięśni głębokich (stabilizacja «drawing-in», prostowniki grzbietu), ergonomia dźwigania, ćwiczenia McKenzie’ego (extension prone press-ups — wg odpowiedzi directional preference), korekcja postawy (I.8).')

rep('5. Mobilizacje łagodne: glide łopatki, trakcja ramienia w tolerancji; ĆWICZENIA: pendulum Codmana (3×/dzień 30 s), ściana «chodzenie palcami», rotacje z gumą (faza późna).\n\n**Zasada:** ból ≤ 3/10 w trakcie i ≤ 24 h po; faza «zamrożona» — NIE forsować\ntorebki; faza « descongelamento » — więcej mobilizacji; ocena: Ortho? skorzysta\nfizjoterapeuta.',
    '5. Mobilizacje łagodne: glide łopatki, trakcja ramienia w tolerancji; ĆWICZENIA: wahadła Codmana (3×/dzień 30 s), ściana «chodzenie palcami», rotacje z gumą (faza późna).\n\n**Zasada:** ból ≤ 3/10 w trakcie i ≤ 24 h po; faza «zamrożona» — NIE forsować\ntorebki stawowej; faza «rozmarzania» (thawing) — więcej mobilizacji; ocenę\nfunkcji prowadzi fizjoterapeuta/ortopeda.')

rep('ETAП GOTOWOŚCI (TM): [ ]K [ ]P [ ]Pr [ ]D [ ]U   pewność ../10  ważność ../10',
    'ETAPE GOTOWOŚCI (TM): [ ]K [ ]P [ ]Pr [ ]D [ ]U   pewność ../10  ważność ../10')

rep('NAGRODA/FEEDBACK (natychmiastowy): .............. (nie «self-punishment»)\nWSPIERACZE: osoba ......... aplikacja/dziennik ......... środowisko (kupić\n buty? ustawić rower przy drzwiach?) .........\nPUNKTY KONTROLI: co .... dni; metryka: ......... ( kroki/dzień, porcje warzyw,\n min aktywności, sen)\nPLAN BAWOŁA (jeśli 2× z rzędu brak realizacji):',
    'NAGRODA/FEEDBACK (natychmiastowy): .............. (nie «self-punishment»)\nWSPIERACZE: osoba ......... aplikacja/dziennik ......... środowisko (kupić\n buty? ustawić rower przy drzwiach?) .........\nPUNKTY KONTROLI: co .... dni; metryka: ......... (kroki/dzień, porcje warzyw,\n min aktywności, sen)\nPLAN AWARYJNY (jeśli 2× z rzędu brak realizacji):')

rep('rękawiczki nitinolowe? → nitrylowe jednorazowe', 'rękawiczki nitrylowe jednorazowe')

rep('3. **Narzędzia:** narzędzia jednorazowe (skalpele — ZAKAZ użycia w usługach; nożyczki do paznokci, frez podologiczny — sterylizacja autoklawem tylko przez wykwalifikowanych, dla nas: dezynfekция高水平 preparatem medycznym + wymienne końcówki).',
    '3. **Narzędzia:** narzędzia jednorazowe tam gdzie to możliwe (skalpele — ZAKAZ użycia w usługach; nożyczki do paznokci, frez podologiczny — sterylizacja autoklawem wyłącznie przez wykwalifikowanych; dla nas: dezynfekcja preparatem medycznym klasy SRR + wymienne końcówki).')

rep('**Historycznie:** felczer执行ował płukanie («wlew doodbytniczy», «detoksykacja»)\nprzy zatruciach; aparatura: syfon, irygator Esmarcha.',
    '**Historycznie:** felczer wykonywał płukanie («wlew doodbytniczy», «detoksykacja»)\nprzy zatruciach; aparatura: syfon, irygator Esmarcha.')

rep('— medycznie zbędne i ryzykowne (elektrolity, perferacja przy patologii,\nmikrobiom); «kawa» lewatywy (Gerson) — BRAK dowodów, opisywane przypadki\nśmierci (hiponatremia, oparzenia) → nie oferuj.',
    '— medycznie zbędne i ryzykowne (zaburzenia elektrolitowe, perforacja przy patologii jelita,\nnaruszenie mikrobiomu); lewatywa kawowa (metoda Gersona) — BRAK dowodów\nskuteczności, opisywane przypadki śmierci (hiponatremia, oparzenia odbytnicy)\n→ nie oferuj.')

rep('Pacjenci często proszą o: «czyszczenie wątroby» (oliwa + cytryny + «kamienie»),\n「pasożyty — zioła」, 「odkwaszenie」, 「toksyny z baniek/plastra na stopę」.',
    'Pacjenci często proszą o: «czyszczenie wątroby» (oliwa + cytryny + «kamienie»),\n«odrobaczenie ziołami», «odkwaszenie», «wyciąganie toksyn bańkami/plastrem na stopę».')

rep('- Plastry « detox» ciemnieją od własnych ekstraktów roślinnych + wilgoci — nie od toksyn.',
    '- Plastry «detox» na stopę ciemnieją od własnych ekstraktów roślinnych i wilgoci — nie od «toksyn».')

rep('piołun, czosnek, goździk) — słabe dowody, ryzyko (piołun — thujone, neurotoksyczny przy przedawkowaniu).',
    'piołun, czosnek, goździk) — słabe dowody skuteczności, ryzyko (piołun — tujon, neurotoksyczny przy przedawkowaniu).')

rep('2. Przed wizytą: ciepłe okłady 10–15 min ×3 (mogą «dojrzeć» — złagodzić), NIE выдавливать, NIE nakłuwać igłą «domowo».',
    '2. Przed wizytą: ciepłe okłady 10–15 min ×3 (mogą «dojrzeć» zmianę — złagodzić ból); NIE wyciskać, NIE nakłuwać igłą «domowo».')

rep('3. Po leczeniu lekarskim — wsparcie: wymiana opatrunków (technika jałowa), obserwacja gojenia, edukacja higieny (MRSA: ręczniki osobne, pranie 60 °C).\n4. Nawracające ropnie → immunolog/diabetolog (cukrzyca! hidradenitis suppurativa).',
    '3. Po leczeniu lekarskim — wsparcie opiekuńcze: wymiana opatrunków (technika czysta/jałowa zgodnie ze zleceniem), obserwacja gojenia, edukacja higieny (MRSA: ręczniki osobne, pranie ≥ 60 °C).\n4. Nawracające ropnie → immunolog/diabetolog (cukrzyca! hidradenitis suppurativa).')

rep('**Bańki suche/ogniowe (usługa relaksacyjna):** ssanie umiarkowane, 5–10 min,\nkierunek mięśni, nie na żylaki/znamię/brzuch w ciąży/twarz; «ślady» to\nextravasat (wybroczyny), NIE «toksyny» — wyjaśniaj mit; przeciwwskazania:\nantykoagulanty, trombocytopenia, skóra cienka/sucha, fever.',
    '**Bańki suche/ogniowe (usługa relaksacyjna):** ssanie umiarkowane, 5–10 min,\nkierunek wzdłuż włókien mięśniowych, nie na żylaki/znamię/brzuch w ciąży/twarz;\n«ślady» to wybroczyny (extravasat), NIE «toksyny» — wyjaśniaj mit;\nprzeciwwskazania: antykoagulanty, małopłytkowość, skóra cienka/sucha, gorączka.')

rep('**Bańki «masujące» (moving cup):** tylko po naoliczeniu, ruch wolny, bez\nkółek na wyrostkach — ślady łatwe do zrobienia, łatwo o uszkodzenie.',
    '**Bańki masujące (moving cup):** tylko po obfitym natłuszczeniu skóry, ruch\nwolny, zgodny z odpływem limfy; bez kółek na wyrostkach kostnych — o ślad\ni uszkodzenie skóry bardzo łatwo.')

# --------------------------------------------------------------------------
# 3. Usunięcie zduplikowanych linii otwierających wpisy b-15 / b-16
# --------------------------------------------------------------------------
rep('"b-15": """\n    "b-16": """a', '"b-15": """a', required=False)

# --------------------------------------------------------------------------
# 4. Brakujące wpisy: h-16..h-30, i-11..i-15, e-2/e-8/e-10
# --------------------------------------------------------------------------
H_EXTRA = '''    "h-16": """# H.16. Reumatoidalne zapalenie stawów — masaż segmentarny i drenaż po kinezyterapii

Rozszerzenie H.1: gdy pacjent jest PO bloku ćwiczeń (I.1 okres III), najpierw
krótka regeneracja: głaskanie odpływowe kończyn (5 min), rozcieranie wałów
przykręgosłupowych Th9–L2 (jelito/grube — wsparcie trawienia przy lekach DMARD),
drenaż limfatyczny «pompowanie» wokół zajętych stawów OBODNICY (łagodnie, bez bólu).
Czas 15–20 min; temperatura zabiegów chłodna (nie gorąca) przy obrzękowych stawach.
Współpraca: reumatolog (CRP, aktywność DAS28), fizjoterapeuta.""",
    "h-17": """# H.17. ZZSK — pozycja pacjenta i kolejność opracowania

Rozszerzenie H.2: pozycja leżąca przodem z niską poduszką pod biodrami (szara
lordozy), czas 35–45 min; kolejność: lędźwiowo-krzyżowa → piersiowa → szyjna →
klatka przód → biodra. U osób z zaawansowaną kifozą — pozycja boczna z
podparciem głowy. Zakaz: manipulacji高速 (thrust) C-spine; any nagły ból promieniujący do rąk/nóg → neurolog.""",
    "h-18": """# H.18. Choroba zwyrodnieniowa kręgosłupa — masaż rozluźniający → wzmacniający

Rozszerzenie H.3: cykl 6-tygodniowy: tydzień 1–2 — techniki rozluźniające
(głaskanie, rozcieranie powierzchowne), tydzień 3–4 — głębsze ugniatanie wałów
przykręgosłupowych + PIR, tydzień 5–6 — aktywizacja (trening stabilizacyjny I.8,
martwy ciąg rumuński lekko pod nadzorem). Ocena: ODI (Oswestry Disability Index)
co 2 tygodnie.""",
    "h-19": """# H.19. Dyskopatia i rwa kulszowa — pozycja boczna i uciski punktowe

Rozszerzenie H.4: w pozycji bocznej (zdrowa strona na dole, kolana zgięte z
poduszką między nimi) wykonaj: głaskanie grzbietu i nogi strony chorej,
rozcieranie L3–S1 przykręgosłupowo, uciski punktów: BL23 Shenshu (przy L2),
GB30 Huantiao (pośladek), BL40 Weizhong (dół podkolanowy — delikatnie!), BL60
Kunlun (za kostką boczną) — zasada: ból ≤ 3/10, 20–30 s/ punkt. Gimnastyka
rwiana → I.14.""",
    "h-20": """# H.20. Zespół bolesnego barku — masaż klasyczny i segmentarny łącznie

Rozszerzenie H.5: segmenty Th1–Th5 (punkty maksymalne przykręgosłupowe) +
okolica barku: rozcieranie czworobocznego górnego, równoległobocznych,
naramiennego; sprężynowanie żeber górnych (oddech). Faza zamrożona: tylko
wahadła Codmana + praca łopatki. Protokół oceny: Neer-Hawkins / AROM-PROM.""",
    "h-21": """# H.21. Choroby dróg oddechowych — sprężynowanie i drenaż ułożeniowy

Rozszerzenie H.6: sprężynowanie (Vibration/percussion) — rytmiczne, sprężyste
uderzenia dłonią lejkowatą 2–3 min/kwadrant w pozycji drenażowej (G.9), potem
huffing. Astma: NIE w napadzie; POChP z zaleganiem wydzieliny: 2×/dobę.
Edukacja inhalatora (krok po kroku, odstęp 30 s między dawkami, płukanie jamy
ustnej po sterydzie).""",
    "h-22": """# H.22. Choroby serca — kolejność postępowania (7 kroków)

Rozszerzenie H.7 (wg szkoły Zborowskiego, w granicach zgody kardiologa):
1 ocena RR/HR/subiektywna; 2 głaskanie kończyn odpływowo (5 min); 3 rozcieranie
powierzchowne Th1–Th5; 4 PRACA NA SEGMENTACH tylko przy braku objawów spoczynkowych;
5 kark/barki rozluźniająco; 6 oddech przeponowy; 7 cisza 5 min + pomiar powtórzny.
Przerwanie: jakikolwiek ból zamostkowy → 112.""",
    "h-23": """# H.23. Choroby naczyń obwodowych — skala Fontaine’a i Piskorza

Rozszerzenie H.8: Fontaine I (zimno, parestezje) — zabiegi dopuszczalne
łagodne; IIa (ból przy przejściu > 200 m) — program Buergera (I.7) + spacery
interwałowe; IIb (< 200 m)/III (ból spoczynkowy)/IV (martwica) — ANGIOLOG,
żadnego masażu leczniczego kończyny; ograniczyć się do edukacji i pielęgnacji
zdrowej części stopy. Skala Piskorza (nasilenie chromienia) — pomocnicza
w monitorowaniu samodzielnych raportów pacjenta.""",
    "h-24": """# H.24. Porażenia nerwów obwodowych — okresy i techniki (rozszerzenie)

Rozszerzenie H.9: okres porażenia (wieńczenie zaniku — EMG): ROM bierny +
pozycjonowanie + głaskanie; okres kompensacji: wzmacnianie mięśni
zachowanych (np. n. strzałkowy — piszczelowy tylny, dwugłowy uda) i nauka
chwytów zastępczych; okres adaptacji: ergonomia, ortezy (AFO), profilaktyka
urazów w niedoczulicy. EMS/TENS neuromuskularny — wyłącznie z uprawnieniami
medycznymi/fizjoterapeutycznymi.""",
    "h-25": """# H.25. Porażenie połowicze — metody neurofizjologiczne (kontekst)

Rozszerzenie H.10: NDT-Bobath, PNF (Kabata), Brunnstrom, Rood — techniki
wykonywane przez certyfikowanych fizjoterapeutów; NATUROPATHA role:
pozycjonowanie przeciw przykurczom, instruktaż przenoszenia/pad安全 dla rodziny,
masaż relaksacyjny strony zdrowej (przeciążonej), walka z zmęczeniem (pacing),
edukacja wtórna prewencja udaru (RR, cukier, lipidogram, papierosy — lekarz).""",
    "h-26": """# H.26. Choroby przewodu pokarmowego — zaparcia spastyczne i wiotkie

Rozszerzenie H.11: rozróżnienie obserwacyjne (za lekarzem!): spastyczne —
ból kurczowy, «owcza» stolce, napięta sigmoida → technika ROZLUZNIAJĄCA:
delikatne głaskanie + ciepły okład + oddech przeponowy; wiotkie — osłabiony
perystaltyka (seniorzy, hipotonia) → TECHNIKA STYMULUJĄCA: rozcieranie wg
okrężnicy,轻 uciski punktu ST25 Tianshu (2 cun od pępka bocznie), ćwiczenia
«vacuum» łagodne, nawodnienie + błonnik rozpuszczalny (psyllium — dowody dobre).
Alarm: krew smolista, chudnięcie → gastrolog.""",
    "h-27": """# H.27. Choroby układu moczowego — kamica: rozcieranie koliste

Rozszerzenie H.12: poza kolka: głaskanie okolicy lędźwiowej, rozcieranie
koliste przykręgosłupowo Th12–L2 (łagodne, 5–8 min), drenaż pozycyjny nerek?
(nie ma takiego drenażu — zamiast tego: nawodnienie 2–2,5 l/d, ruch). W COLCE:
ŻADNEGO masażu — ciepło miejscowe wg zaleceń lekarza + spasmolytyki; gorączka
+ kamica → SOR (niebezpieczeństwo sepsy!). Profilaktyka nawrotów: dieta
ograniczająca szczawiany/urate zależnie od typu kamicy (badanie kamienia!).""",
    "h-28": """# H.28. Choroby kobiecych narządów — stymulacja laktacji (3 fazy)

Rozszerzenie H.13: faza 1 (dobę 1–3, nabrzmiewanie): ciepły okład + delikatne
głaskanie od podstawy ku brodawce, ręczne opróżnianie «Marmet» — instruktaż
położnej; faza 2 ( ustanowienie laktacji): masaż okrężny mleczowodów,
unikanie ucisku (stanik!). faza 3 (utrzymanie): regularne karmienie/napełnianie
laktatora, odpoczynek, nawodnienie matki. Mastitis (gorączka, klin zaczerwienienia)
→ LEKARZ (antybiotyk); przepłukiwanie «ziołami» galaktogonnymi — dowody słabe
(mleko kozłka? nie); koper/kminek tradycyjnie — informuj o poziomie dowodów.""",
    "h-29": """# H.29. Stany po urazach — masaż klasyczny w 3 etapach (rozszerzenie)

Rozszerzenie H.14: etap I (unieruchomienie): praca poza obszarem — głaskanie
odpływowe, counterpart; etap II (po zdjęciu gipsu/ortezy): rozcieranie blizny
i tkanek okołostawowych, ROM, obrzęk → drenaż (B.4); etap III (functionalizacja):
ugniatanie mięśni zanikłych + trening siłowy progresywny (I.10/B.9). Każdorazowo
zgoda prowadzącego ortopedy/fizjoterapeuty; dokumentacja ROM co wizytę.""",
    "h-30": """# H.30. Wady postawy — skoliozy funkcjonalne vs. strukturalne (fazy)

Rozszerzenie H.15: funkcjonalna (posturalna, korygowalna czynnie): masaż
rozluźniający stronę napiętą + ćwiczenia korekcyjne symetryczne (I.8), efekty
możliwe pełne; strukturalna (rotacja kręgów, garb Adamsa dodatni, Cobb ≥ 10°):
ortopeda! orteoza/ćwiczenia Schroth’a u terapeuty certyfikowanego; nasz zakres:
masaż rozluźniający strony wypukłej (4–8 faz wg stanu), profilaktyka bólu,
ergonomia. Progresja > 5° w rok → skierowanie pilne.""",
'''
# wstaw h-extra przed zamknięciem H_SCHEMES
rep('''**Scoliosis:** masaż strony wypukłej (napięta) rozluźniająco, wklęsłej —
łagodnie stymulująco; CHURSCHT? → ćwiczenia korekcyjne specjaliści (orthota
Milwaukee/Boston — ortopeda). Red flag: ból nocny + skolioza progresywna
dorosłego → obrazowanie (nowotwór?)/lekarz.""",
}''',
'''**Scoliosis:** masaż strony wypukłej (napięta) rozluźniająco, wklęsłej —
łagodnie stymulująco; ćwiczenia korekcyjne — specjaliści (orteza Milwaukee/
Boston — ortopeda). Red flag: ból nocny + skolioza progresywna dorosłego →
obrazowanie (nowotwór?)/lekarz.""",
''' + H_EXTRA + '''}''')

I_EXTRA = '''    "i-11": """# I.11. Ćwiczenia w ZZSK — tor przeponowy i antykifotyczny (rozszerzenie)

Rozszerzenie I.2: blok «oddech + antykifoza»: 1) oddech przeponowy leżąc z
książką na brzuchu 5 min; 2) inspirator IMT 2×30 oddechów (opór wg tolerancji);
3) foam-extension Th7–Th12 10 powt.; 4) retrakcja łopatek z gumą face-pull
3×12; 5) prone-on-elbows 2–5 min ×2/dzień. Zakaz: ćwiczeń statycznych bezruchu
długotrwałego i mocnych oporowych w zaostrzeniu — priorytet: ruch codzienny.""",
    "i-12": """# I.12. Ćwiczenia po zawale — schemat okresów (rozszerzenie)

Rozszerzenie I.3: okres szpitalny (faza I) — opis poglądowy (siadanie, pionizacja
wg lekarza); okres rekonwalescencji (faza II) — marsz 5→30 min, RPE 11–13,
ćwiczenia oddechowe, ADL; po rekonwalescencji (faza III) — program jak I.3 +
kontrola co 12 tyg. Testy wyjścia z domu: próba 6-minutowego marszu (> 400 m
poprawa), talk-test. Leki: beta-blokery maskują HR — stosuj RPE!""",
    "i-13": """# I.13. Ćwiczenia w astmie i POChP — drenaż ułożeniowy (rozszerzenie)

Rozszerzenie I.4: pozycje wg segmentów (G.9) + techniki: klapping, wibracja,
huffing, «active cycle breathing technique» (ACBT: oddechy kontrolne →
głęboki wdech → huff). Astma kontrolowana: rozgrzewka ≥ 10 min, reliever przed
wysiłkiem wg planu lekarza; basen chlorowany — u części osób drażniący
(obserwuj, alternatywa: aqua-warm-water bez chloru? rzadko dostępne).
Zaostrzenie: STOP ćwiczeń, lekarz.""",
    "i-14": """# I.14. Gimnastyka w rwie kulszowej — schemat

Faza ostra (ból korzeniowy): pozycje odciążające (leżenie 90/90 na krześle
pod podudzi), nerwowe «gliding» (slump dynamiczny ŁAGODNIE — neural flossing,
nie tensioning!), chód krótki częsty; faza podostra: McKenzie extension press-up
10× co 2 h (preferencja kierunkowa — jeśli centralizuje ból, kontynuuj; jeśli
peryferalizuje — STOP, lekarz), mostek 3×10, bird-dog 3×8; faza przewlekła:
Martwy ciąg z bułą? NIE — hip hinge z kijem, martwy ciąg rumuński lekki,
plank boczny 3×20 s, trening pośladka średniego (clamshell). Zasada: ból
korzeniowy NIE powinien «schodzić w dół nogi» podczas programu.""",
    "i-15": """# I.15. Ćwiczenia po amputacjach — przygotowanie do protezy, nauka chodzenia

Kontekst: decyzje protetyczne i rehabilitacja — lekarz/rehabilitant/protetyk;
nasza rola wspomagająco-poeduukacyjna:
1. Faza przedprotezowa (reszta po zagojeniu): owijanie bandażem elastycznym
   (eska, nie skrętnie — modelowanie), desensytyzacja (dotyk różnymi fakturami),
   PIR zginaczy biodra i kolan (profilaktyka przykurczów — kluczowa!),
   wzmocnienie tułowia i kończyny zdrowej (mostki, wiosłowanie), ćwiczenia
   równowagi jednonóż (asekuracja!).
2. Phantom pain: mirror therapy (RCT: redukcja bólu), edukacja — nie «udawać,
   że nie boli».
3. Faza protezowa: nauka wstawania/z siadania z protezą, chód po równym →
   schody → nierówności; higiena kikuta (mycie, oględziny skóry codziennie —
   otarcie = lekarz/protetyk natychmiast).
Bezpieczeństwo: upadki — mata, poręcz, asekuranta; zawroty (objętość krwiaka?
hipotonia ortostatyczna) → przerwij.""",
'''
rep('''**Screening przed:** TUG (Time Up & Go > 12 s → ryzyko upadku, fizjo), MMSE
(cooperacja), ból spoczynkowy, ciśnienie leżąc/stojąc (orthostaza!).
Cel: niezależność funkcjonalna i upadki-prewencja — mierz Outcomes: SPPB, 30-s
chair stand.""",
}''',
'''**Screening przed:** TUG (Time Up & Go > 12 s → ryzyko upadku, fizjo), MMSE
(cooperacja), ból spoczynkowy, ciśnienie leżąc/stojąc (orthostaza!).
Cel: niezależność funkcjonalna i upadki-prewencja — mierzone outcomes: SPPB,
30-s chair stand.""",
''' + I_EXTRA + '''}''')

# --------------------------------------------------------------------------
# 5. Nowe słowniki: dodatkowe rozdziały F(e-*), G(f-*), H(g-*), I(h-*), K(k-*)
#    oraz rejestr sekcji z wieloma mapowaniami.
# --------------------------------------------------------------------------
NEW_DICTS = '''
# ---------------------------------------------------------------------------
# ZAŁĄCZNIK F — dodatkowe pozycje historycznego spisu E.2/E.8/E.10
# ---------------------------------------------------------------------------
E_EXTRA = {
    "e-2": """# E.2. Przeciwwskazania do masażu segmentarnego — katalog rozszerzony

Pozycja kursowa zgodna ze starym spisem Załącznika E (szkoła Zborowskiego).
Uzupełnia F.2 o przypadki szczegółowe:

**Bezwzględne:**
1. Ostre bakteryjne zapalenia narządów (nerki, pęcherzyk żółciowy, wyrostek,
   przydatki) — jakakolwiek praca w odpowiadającym segmencie grozi szerzeniem
   procesu i wzrostem ciśnienia wewnątrznerkowego.
2. Zakażenia ogólne z gorączką (> 38,5 °C), posocznica, stan po niedawnej
   infekcji (okres zakaźny + 48 h bez objawów).
3. Ostre stany zapalne jamy brzusznej z twardym brzuchem/rebound → chirurgia,
   nie gabinet (napięcie obronne = STOP, 112/SOR).
4. Choroby nowotworowe — bez pisemnej opinii onkologa żadnego pobudzenia
   segmentalnego; obszar przerzutów kości — absolutny zakaz.
5. Krwawienia czynne (z przewodu pokarmowego, dróg moczowych, maciczne
   obfite nieznanego pochodzenia) — przyczynę ustala lekarz.
6. Świeży zawał serca, niestabilna dławica, arytmia zagrażająca (Th1–Th5!).
7. Nadczynność tarczycy nieleczona (strefa Th1–Th2 + szyja).

**Względne (modyfikuj siłę/czas/obszar i zapisz decyzję w karcie C.2):**
menstruacja obfita, kamica w wywiadzie (poza kolka), cukrzyca z powikłaniami,
ciąża (bez L1–S2 głęboko), wiek podeszły z kruchością, antykoagulacja.

**Reguła złotej godziny:** ból trzewny + poty + nudności + tachykardia
w trakcie zabiegu = natychmiast przerwać, pozycja półsiedząca, 112.
Strefy Heada służą OBSERWACJI i pracy wspomagającej — NIE diagnozie.
""",
    "e-8": """# E.8. Przeciwwskazania do zabiegów felczerskich (cyrulicznych)

Komplementarnie do K.1–K.8 — katalog, który uczeń ma zdany w teście sytuacyjnym
na 100 % dla pozycji zakazanych:

**Bezwzględne (procedury medyczne — poza zakresem na mocy prawa):**
1. Jakiekolwiek przekłucie skóry w celu leczniczym: iniekcje, akupunktura
   igłowa, nacięcia, krew włośniczkowa «do badania» — to świadczenia zdrowotne
   wymagające uprawnień (ustawa o zawodach lekarza i lekarza dentysty;
   wykonywanie zawodu medycznego bez uprawnień — art. 58 ustawy, kara).
2. Szycie ran, nastawianie złamań/zwichnięć, repozycja przepuklin.
3. Płukanie żołądka, lewatywy «lecznicze», cewnikowanie pęcherza — procedury
   medyczne (ryzyko perforacji, bakteriemii, hiponatremii).
4. Nacinanie i drenaż ropni, usuwanie zmian skórnych «laserem domowym».
5. Upust krwi, pijawki «z hodowli niemedycznej», dermapen przez naskórek.

**Przeciwwskazania stanu klienta do zabiegów DOZWOLONYCH (opatrunek drobny,
okład, bańka sucha, keratoliza martwego nagniotka):**
gorączka, choroba zakaźna skóry (świerzb, grzybica rozsiana, liszajec),
otwarta rana w polu zabiegu, żylaki z wywiadem zakrzepicy (bańki/masaż!),
antykoagulacja i małopłytkowość (bańki), neuropatia i niedokrwienie stopy
(ciepło, keratoliza chemiczna — stopa cukrzycowa TYLKO podolog/lekarz),
zmiana barwnikowa podejrzana (ASCD — jakikolwiek «zabieg kosmetyczny» na znamieniu
jest zakazany; biopsja = dermatolog), ciąża (brzuch, lędźwie, bańki).

**Zasada dokumentu:** każdy zabieg usługowy poprzedza pytanie «czy to jest
procedura naruszająca ciągłość tkanek żywych poniżej naskórka?» — TAK =
kieruj do uprawnionego; NIE = karta C.12 + zgoda C.8.
""",
    "e-10": """# E.10. Przeciwwskazania do masażu u osób starszych — szczególne środki

Starzenie zmienia fizjologię — adaptuj całe postępowanie (komplementarnie
do F.1 i F.8; por. moduł 9.8 «Zasady wykonywania masażu u osób starszych»):

1. **Skóra:** ucieńczenie naskórka i skóry właściwej, suchość, «papierowa»
   kruchość — bez tarcia po suchej skórze (emolient!), bez oklepywań nad
   żebrami, rozcieranie tylko powierzchowne; ryzyko otarć i krwiaków
   podskórnych nawet przy prawidłowym technicznie zabiegu.
2. **Układ krążenia:** częsta hipertonia/hipotonia ortostatyczna — wstawaj
   wolno, etapy pozycji (leżenie→boczną→siedząc 2 min→stanie); RR przed/po;
   bez głębokiego masażu zatok szyjnych; niewydolność serca — pozycja
   półsiedząca zamiast leżącej, krótsze sesje.
3. **Szkielet:** osteoporoza (kruche żebra, trzony TH/L!) — zakaz nacisku
   pionowego na wyrostki, manipulacji, wibracji mocnej; endoprotezy — zakres
   ruchów bezpieczny wg protetyka (biodro posterior: zgięcie < 90°, bez
   addukcji/rotacji wewnętrznej).
4. **Leki:** antykoagulanty (siniaki — siła ↓, bez baniek), kortykosteroidy
   (skóra, kości), beta-blokery (HR nie rośnie — oceniaj RPE), diuretyki
   (odwodnienie, elektrolity — pora zabiegu), NLPZ (maskują ból ostrzegawczy
   — pytaj o komfort co minutę).
5. **Czucie i poznanie:** neuropatia cukrzycowa (kontrola temperatury okładów!),
   demencja — zgoda przedstawiciela, komunikacja krótkimi zdaniami, rutyna,
   obecność osoby bliskiej; depresja seniora — masaż jako kontakt «dotyk
   godny», kieruj do lekarza przy sygnalach rezygnacji.
6. **Termoregulacja:** większa utrata ciepła — ogrzej salę (24–26 °C),
   osłaniaj niepracowane partie; odwrotnie — ostrożnie z ciepłem lokalnym.
7. **Czas i częstotliwość:** 20–30 min zamiast 60; lepiej 4–5×/tydz. krótko
   niż 1× długo; obserwacja potreningowa 10 min (zawroty!).

**Karta C.10** notuje: pozycję, parametry, tolerancję, czerwone flagi
(ból spoczynkowy kości, nocne poty, chudnięcie → lekarz pilne).
""",
}

# ---------------------------------------------------------------------------
# ZAŁĄCZNIK G — dodatkowe pozycje f-* (historyczny spis F.*)
# ---------------------------------------------------------------------------
F_EXTRA = {
    "f-2": """# F.2 (G). Układ limfatyczny — pnie chłonne, przewód piersiowy, węzły głowy i szyi

Rozszerzenie G.2 o dokładną topografię odpływu centralnego:

- **Pnie chłonne (trunci):** lumbales dexter/sinister (kończyny dolne, miednica,
  ściana brzucha dolna), intestinales (trzewa jamy brzusznej), thoracicus sinister
  (lewa połowa klatki), iugulares dexter/sinister (szyja, głowa), subclavius
  dexter/sinister (kończyny górne, ściana klatki, gruczoł sutkowy).
- **Ductus thoracicus** zaczyna się od cisterna chyli (L1–L2, aorta/prawy
  kręg przeponowy), wstępuje przez kanał aortowy, na wysokości Th5 przechodzi
  na stronę lewą i kończy się w kąsie żylnym lewym (confluence venae
  subclaviae sinistrae + vena jugularis interna sinistra). Drains ~75 % chłonki ciała.
- **Ductus lymphaticus dexter** — prawa głowa/szyja/kończyna górna/klatka.
- **Węzły głowy i szyi (pierścienie Billrotha):** potyliczne, zauszne,
  przyuszne, żuchwowo-potasowe, szyjne powierzchowne (wzdłuż zewn. szyjnej)
  i głębokie (łańcuch wzdłuż wn. szyjnej — węzeł Virchowa nadobojczykowy LEWY
  = sygnał alarmowy nowotworu jamy brzusznej → lekarz PILNE).

Znaczenie praktyczne drenażu: kolejność zawsze «centrum → obwód»: najpierw
uwolnienie pnia/węzła docelowego (np. pompowanie kątów żylnych), potem obszary
dystalne. Masaż klasyczny kończyn: głaskanie odpływowe w kierunku węzłów
(pachwina → biodrowe → aortalne; pachowe → podobojczykowe).
""",
    "f-4": """# F.4 (G). Strefy odruchowe Heada i Mackenziego — unerwienie segmentarne skóry i mięśni (C1–Co)

Tabela pomocnicza do palpacji (rysuj na modelu wg G.4; źródła: Bochenek-Reicher,
Zborowski, patofizjologia modułu 2):

| Segment | Skóra (dermatomy) | Mięśnie (miotamy) | Narząd (odruch trzewny) |
|---|---|---|---|
| C1–C3 | potlica, górna szyja | mm. cervicales profundi, czworoboczny (część) | — , przepona (C3–C5) |
| C4 | «płaszcz» barkowy | przepona | serce (współpraga z Th1–Th5) |
| C5–C6 | boczne ramię, kłykieć/bok dłoni (kciuk) | deltoid, biceps, zginacze nadgarstka | — |
| C7–C8 | grzbiet dłoni, palec IV–V | triceps, prostowniki | — |
| Th1–Th5 | przyśrodek ramienia, klatka górna | mm. intercostales sup., pectoralis | serce, płuca, oskrzela, tarczyca |
| Th5–Th9 | epigastrium, pas środkowy klatki | proste brzucha górne | żołądek, wątroba, pęcherzyk, trzustka |
| Th9–Th12 | pas nadpępkowy–podżebrzy | brzuch środkowy | jelito cienkie, nerki (góra moczowodu) |
| L1–L3 | pachwina, udo przednie | brzuch dolny, zginacze biodra | jelito grube, moczowód dół, jądro/jajnik |
| L4–L5 | udo boczno-przyśrodkowe, goleń przyśrodkowa | czworogłowy, piszczelowy przedni | pęcherz (czucie), macica |
| S2–S4 | obszar siodłowy, krocze | dno miednicy, zwieracze | pęcherz (odpływ), odbytnica, genitalia |
| Co | szczyt ogona | — | — |

Wykorzystanie: masaży segmentarny identyfikuje wałki napieniowe i punkty
maksymalne WEDŁUG segmentu (por. G.8); różnicowanie: ból korzeniowy (kaszel
nasila, dermatom+miotom) vs. trzewny (pas + autonomiczne objawy) — obie
sytuacje alarmowe kierujemy do lekarza, zanim «masujemy dalej».
""",
    "f-8": """# F.8 (G). Punkty maksymalne w masażu segmentarnym — lokalizacja wg jednostek chorobowych

Uzupełnienie G.8 — indeks «jednostka → pola pracy» (egzamin praktyczny B.3):

- **Choroba wrzodowa żołądka/dwunastnicy:** Th6–Th10 przykręgosłupowo (lewo/
  środkowo) + punkt Epigastrium; uwaga: świeża perforacja/ostry brzuch = zakaz.
- **Kolitis/IBS:** Th9–L2 + strefa okrężnicy (obwodowo wg perystaltyki),
  esica — dół lewy brzuch.
- **Choroby nerek (przewlekłe, pielon.) :** Th12–L2 trójkąt nerki + okolica
  Costescu (bocznie L1–L3); kolka — zakaz pracy.
- **Pęcherz moczowy (hiperaktywność, ZUM nawracające):** L1–L2 + S2–S4 nad
  spojeniem łonowym (łagodnie, pełny pęcherz — najpierw mikcja!).
- **Astma/POChP:** Th1–Th7 + międzyżebrza + przepona (Costa angle).
- **Niewydolność krążenia (stab.):** Th1–Th5 + okolica przedsercowa (żeber
  IV–VI lewo), kark (kompensacyjne napięcie).
- **Dysfunkcje jajnika/prostaty:** L5–S2 + pachwina (węzły!) + dno miednicy
  (przezbrzusznie, technika powierzchowna).
- **Bóle głowy napięciowe:** C1–C4 + czworoboczny górny + podpotyliczne.

Każdy punkt oznacz na fantomie markerem, potem na współpracowniku — ćwiczenie
«mapa bolesności» z kartą C.1 (różnicuj z czerwonymi flagami F/Załącznik).
""",
    "f-9": """# F.9 (G). Pozycje drenażowe w chorobach płuc — pełny atlas segmentów

Rozszerzenie G.9 (kąt uniesienia łóżka mierzymy klinometrem/app; czas 20–30 min,
2–4×/dobę PRZED posiłkami lub 1–2 h po; zawsze po nebulizacji/inhalacji
leku rozkurczającego wg planu lekarza):

| Segment | Pozycja |
|---|---|
| Apicalis płatu górnego (S1) | siedząca pionowo, oparta (lub leżenie na plecach płasko) |
| Posterior (S2) | pochylenie przodem 30° przy siedzeniu / leżenie na brzuchu z poduszką pod biodrami 15° |
| Anterior (S3) | leżenie tyłem, poduszka pod kolanami, łóżko płaskie |
| Lingula (S4–S5) | leżenie na PRAWYM boku, łóżko uniesione 20–30°, tułów rotowany ¼ ku przodowi |
| Superior dolnego (S6) | leżenie przodem, miednica wyżej 30° (odwrócony Trendelenburg) |
| Basalis mediale/laterale/posterior (S7–S10) | leżenie tyłem/prodem, nogi powyżej poziomu głowy 30–45° |

Po każdej pozycji: perkusja klapping + wibracja wydłużona na wydechu,
następnie huffing i kaszel kontrolowany (pojemność > 15 ml wydzieliny —
plwocina do pojemnika, higiena rąk). Przeciwwskazania: krwioplucie, odma,
niewydolność serca, świeży uraz/thorax, RGE ciężki (pozycje head-down!),
nadciśnienie wewnątrzzczaszkowe. Dzieci: pozycjonowanie + wibracja zwykle
wystarczą; drenaż autogeniczny trenuje fizjoterapeuta.
""",
    "f-11": """# F.11 (G). Pozycje przeciwzrostowe wg Bruce’a (zapalenie opłucnej, stany po zapaleniu płuc)

Historyczny zestaw pozycji profilaktycznych (A.P. Bruce, szkoła Zborowskiego)
— dziś stosowany OSTROŻNIE i tylko w okresie zdrowienia, za zgodą lekarza:

1. Leżenie na CHORYM boku (blok bólowy oddechu → zapobiega przykurczowi
   przepony i zrostom bocznym) z podparciem ramienia; 20–30 min ×2–3/dzień.
2. Leżenie na zdrowym boku z odwiedzeniem chorego ramienia nad głowę
   (rozciągnięcie przestrzeni międzyżebrzowych) + oddech «w bok».
3. Pozycja «tripod» pochylona z podparciem — oddech torowo-przeponowy
   naprzemienny.
4. Rotacje tułowia czynne (bez bólu > 2/10), «wieszanie ramion» na drabinkach
   — profilaktyka zrostów wierzchołkowych.

**Współczesna weryfikacja dowodowa:** samo pozycjonowanie nie «rozsądza»
blizn opłucnowych; skuteczna jest wczesna mobilizacja + ćwiczenia oddechowe
(POChP/powikłania po pneumonii — dane umiarkowane). Ostry ból opłucnowy +
gorączka + duszność = lekarz (RSW/empyema — drenaż chirurgiczny!), NIE nasza
pozycja «przeciwzrostowa».
""",
    "f-12": """# F.12 (G). Punkty masażu punktowego — astma, bóle głowy, rwa kulszowa, kończyna górna i dolna

Indeks punktów (ciśnienie kciukiem 15–30 s, 3–5 powtórzeń, ból ≤ 3/10;
akupresura — dowody umiarkowane: nudności PC6 dobre, ból — słabe/umiarkowane;
informuj pacjenta uczciwie o poziomie evidencji):

- **Astma (wspomagająco, POZA napadem):** EX-B1 Feishu (BL13, przyłędźwiowo
  Th3), GV14 Dazhui, CV17 Danzhong (rękojeść mostka), PC6 Neiguan (nudności
  i «ściśnięta klatka»), ST36 Zusanli (ogólnie wzmacniająco-tradycyjnie).
- **Ból głowy napięciowy:** GB20 Fengchi (dołki podpotyliczne!), LI4 Hegu,
  EX-HN Taiyang (skroniowo), kark/czworoboczny (TrP — G.3). Migraina aura:
  punkt «LI4» tradycyjnie; UWAGA: ciąża — tradycyjnie unikać LI4/SP6.
- **Rwa kulszowa:** BL23 Shenshu, GB30 Huantiao, BL40 Weizhong, BL60 Kunlun,
  ASH-points (pietzisty «Ah-shi») — nigdy na ostrym korzeniowym rzucie
  (czerwone flagi → neurolog).
- **Kończyna górna (łokieć tenisisty, drętwienia):** LI11 Quchi, TE5 Waiguan,
  LU5 Chize + punkty spustowe prostowników (G.3). Zespół cieśni nadgarstka:
  PC7 Daling + pozycja neutralna; operacja kwalifikuje lekarz.
- **Kończyna dolna (kolano, łydka):** ST35 (okolica «medial eye»), SP9 Yinling
  Xiang (zastoiny wodne — tradycyjnie), KI3 Taixi (za kostką przyśrodkową —
  ostrożnie tętnica!), BL57/58 trójgłowy łydki.

**Bezpieczeństwo:** nie uciskaj tętnic (szczególnie zatoki szyjnej!), zmian
skórnych, żylaków, miejsc popromiennych; przeciwwskazania wg F.1/F.8.
""",
}

# ---------------------------------------------------------------------------
# ZAŁĄCZNIK H — dodatkowe pozycje g-* (historyczny spis G.*)
# ---------------------------------------------------------------------------
G_EXTRA = {
    "g-1": """# G.1 (H). RZS — masaż segmentarny i drenaż limfatyczny PO kinezyterapii

Rozszerzenie H.1: schemat łączony 45-minutowy (remisja!):
1. 0–10 min: rozgrzewka ogólna — głaskanie grzbietu, rozcieranie wałów
   przykręgosłupowych Th9–L2 (segment jelita — wsparcie trawienia przy DMARD/NLPZ).
2. 10–25 min: segmenty zajętych stawów (symetrycznie, siła 1–2/5): barki Th1–Th5,
   ręce C5–Th1 (przykręgosłupowo szyja), kolana L2–L4, stopy L5–S1.
3. 25–35 min: KOŃCZYNY po bloku ćwiczeń I.1: drenaż «pompowanie» wokół
   stawów obrzękniętych (bez bólu), głaskanie odpływowe, kokonowanie palców.
4. 35–45 min: relaksacja oddechowa + pozycje przeciw przykurczom.
Ocena: HAQ/DAS28 raport reumatologa; VAS bólu przed/po; zasada «ból po zabiegu
≤ baseline w ciągu 2 h». Zakazy wg F.1/H.1 (rzut ostry, gorączka, osteoporoza
sterydowa).
""",
    "g-2": """# G.2 (H). ZZSK — pozycja pacjenta i kolejność opracowania (rozszerzenie)

Rozszerzenie H.2: w zaawansowanej kifozie NIE kładziemy «na siłę» na plecach
(niestabilność C1–C2, złamanie chalk-stick!). Protokół:
1. Wywiad/ruchy: Adams? (nie dotyczy), ROM kręgosłupa w 3 płaszczyznach,
   odległość potylica-ściana, test Schobera (≥ 5 cm przyrostu — norma).
2. Kolejność opracowania: miednica i okolica lędźwiowo-krzyżowa → odcinek
   piersiowy (międzyżebrza, oddech torowy) → szyjny (tylko powierzchownie!)
   → klatka przód (pektorale rozciągane) → biodra (zginacze!) → tył uda.
3. Pozycje: boczna z poduszką «wałem» wzdłuż kręgosłupa (stabilizacja),
   prone z czołem na podkładce (jeśli toleruje), siedząc na piłce (kinetic
   control). Czas 30–40 min, 3×/tydz. + codzienna gimnastyka I.2/I.11.
4. Red flags: nagły ból po minimalnym urazie → RTG/TK (złamanie!), objawy
   rdzeniowe → neurochirurg natychmiast. Biologiczne anti-TNF pozwalają
   intensywniejszy trening — konsultacja z reumatologiem.
""",
    "g-3": """# G.3 (H). Choroba zwyrodnieniowa kręgosłupa — masaż klasyczny rozluźniający → wzmacniający + segmentarny

Rozszerzenie H.3 (cykl dwufazowy 8 tygodni):
**Faza A (dni 1–14, ból ≥ 4/10):** głaskanie + rozcieranie powierzchowne
wałków przykręgosłupowych (Th/L), ciepły okład przed (jeśli brak odczynu
ostrego), pozycje odciążające 90/90; siła 1/5, czas 20 min.
**Faza B (tydzień 3–8):** ugniatanie wałów + rozluźnianie TrP (G.3 mapy),
PIR prostowników grzbietu i zginaczy biodra, następnie AKTYWIZACJA:
bird-dog, dead-bug, mostek, chin-tuck (I.8) — masaż «otwiera okno tolerancji»
dla ćwiczeń. Segmentarnie: Th9–L3 (jelita — częste współwystępowanie
zaparć przy hipotonii/lekach), S2–S4 (pęcherz — screenings NTM!).
Ocena co 2 tyg.: ODI, rano-sztywność < 30 min (jeśli dłużej i symetrycznie
stawki obwodowe → reumatolog, nie «degeneracja»).
""",
    "g-4": """# G.4 (H). Dyskopatia i rwa kulszowa — okresy + masaż w ułożeniu bocznym + uciski punktowe + gimnastyka rwiana

Pełny protokół (rozszerzenie H.4 + H.19):
**Okres ostry (1–7 dni):** pozycja boczna z poduszką między kolanami
(strona chora u góry lub «fowler» półsiedzący), technika: głaskanie grzbietu
i nogi, rozcieranie powierzchowne wałów L2–S1; BEZ głębokiego ugniatania
pośladka (drażni korzeń!). Ćwiczenia: oddech przeponowy, naprzemienne
napinanie pośladków (izometria 5 s ×10), chód krótki co godzinę.
**Okres podostry (2–6 tyg.):** ugniatanie wałów + pośladek średni/gruszkowaty
(test FAIR — pseudorwa?), uciski punktów: BL23, GB30, BL37 Yangfu (tył uda),
BL40, BL60 (patrz F.12/G.19); neural gliding ŁAGODNIE; McKenzie wg odpowiedzi
(centralizacja = kontynuuj; peryferalizacja = STOP → lekarz).
**Okres przewlekły/profilaktyka:** trening stabilizacji (drawing-in, mostki,
clamshell), ergonomia (krzesło 90/90/90, mikro-pery co 30 min), I.8/I.14.
**Czerwone flagi (SOR):** zespół ogona końskiego (zaburzenia czucia siodłowego,
zatrzymanie moczu/nietrzymanie, obustronny deficyt), postępujący opad stopy,
gorączka + ból kręgosłupa, nowotwór w wywiadzie + ból nocny.
""",
    "g-5": """# G.5 (H). Zespół bolesnego barku (PHS) — masaż klasyczny i segmentarny, okresy

Rozszerzenie H.5/H.20:
**Okres ostry (ból spoczynkowy, nocny):** segmenty Th1–Th5 przykręgosłupowo
(łagodnie) + kark (czworoboczny górny, dźwigacz); bark: GŁASKANIE +
rozcieranie powierzchowne deltoidu, NIE forsować ROM; krioterapia 10 min ×3;
wahadła Codmana 3×/dzień.
**Okres podostry (2–6 tyg.):** ugniatanie łopatki (równoległoboczne,
podgrzebieniowy, obły), rozcieranie bruzdy dwugłowej (ścięgno długiej głowy
bicepsa — delikatnie!), mobilizacje glide łopatki, trakcja w zakresie
bezbolesnym; ćwiczenia: rotacje izometryczne z gumą (ER/IR 3×10), face-pull,
scapular setting.
**Okres przewlekły / zamrożony:** kapsulitis — fizjoterapeuta/ortopeda;
nasze: rozluźnianie pektoralnych + Th1–Th5, pozycje stretch drzwiowe 3×30 s,
stopniowa ekscentryka; «zamrożenie» nie znosi agresji — ból ≤ 3/10 zasada.
Różnicowanie alarmowe: ból po urazie + deformacja → RTG; obrzęk/gorączka →
septyczne zapalenie stawu → SOR; rzut do żuchwy przy wysiłku → serce → 112.
""",
    "g-6": """# G.6 (H). Choroby dróg oddechowych — sprężynowanie i drenaż ułożeniowy (rozszerzenie)

Rozszerzenie H.6/H.21: pełna sekwencja zabiegowa (poza napadem/gorączką):
1. Ocena: oddech/spO₂? (jeśli pulsoksymetr domowy pacjenta), kaszel, ilość
   wydzieliny, inhalator reliever 15 min PRZED zabiegiem (wg planu lekarza).
2. Segment Th1–Th7: głaskanie → rozcieranie przykręgosłupowe → ugniatanie
   równoległobocznych/prostowników (siła 2/5).
3. Międzyżebrza: rozcieranie poprzeczne na WYDECHU (mostek←→kręgosłup).
4. Przepona: rozcieranie łuku żebrowego na wydechu + oddech przeponowy
   z oporem (ręka terapeuty na brzuchu).
5. SPRĘŻYNOWANIE (wibracja wydłużona): dłonie na kwadrantach, wstrząs
   synchroniczny z wydechem, 1–2 min/kwadrant; POTEM klapping (dłoń
   lejkowata, 2–3 min) w pozycji drenażowej (F.9/G.9 atlas).
6. Huffing + kaszel kontrolowany → plwocina do pojemnika, higiena rąk.
7. Cisza 5 min, pomiar powtórny, zapis C.2.
Astma: bez bodźców zimnych/alerogenów (pyłki! sierść koców — używaj
syntetycznych prześcieradeł); POChP: edukacja energy-conservation; krwioplucie
— STOP, lekarz pilne.
""",
    "g-7": """# G.7 (H). Choroby serca — kolejność postępowania w 7 krokach (rozszerzenie)

Rozszerzenie H.7/H.22 (tylko faza III rehabilitacji kardiologicznej, za zgodą
kardiologa; ZAKAZ: decompensatio, świeży ZSC < 4–6 tyg., RR ≥ 180/110,
niestabilna angina):
1. Pomiar RR/HR w pozycji siedzącej + pytania: ból? duszność? obrzęki?
   sen? leki przyjęte? (beta-blokery → HR niska, normy wg lekarza).
2. Głaskanie odpływowe kończyn górnych i dolnych (5–8 min) — preload serca
   nie obciążać gwałtownym «powrotem objętości»: RĘCE NIŻEJ SERCA przy
   pierwszych chwytach, tempo wolne.
3. Rozcieranie powierzchowne segmentów Th1–Th5 (bez oklepywań!).
4. Okolica przedsercowa: głaskanie międzyżebrzy IV–VI lewo, oddech spokojny.
5. Kark/barki: rozluźnienie (napięcie «sercowe» rzutowane — różnicuj z
   anginą wysiłkową! ból zależny od wysiłku → lekarz).
6. Oddech przeponowy + relaksacja (efekt przywspółczulny — dane umiarkowane).
7. Cisza 5 min → RR/HR powtórnie; kryteria odstąpienia: jakikolwiek ból
   zamostkowy, poty, nudności, arytmia subiektywna → pozycja półsiedząca, 112.
Czas 20–30 min, 2–3×/tydz.; karta C.2 z wartościami przed/po.
""",
    "g-8": """# G.8 (H). Choroby naczyń obwodowych — masaż klasyczny i segmentarny; skala Fontaine’a i Piskorza

Rozszerzenie H.8/H.23:
**Żylaki (CVD przewlekła):** segmenty L1–S4 przykręgosłupowo łagodnie
(tonus żylny — tradycja szkoły), kończyna: GŁASKANIE odpływowe + kokonowanie
stopa→udo; ZAKAZ: ugniatania przebiegów żył, oklepywań, baniek, ciepła;
kompresjoterapia flebologa, Ratschow (I.7), chód 30 min/dzień.
**PAD (miażdżyca kończyn):** klasyfikacja Fontaine: I — zimno/drzętwienia
(zabiegi łagodne OK); IIa — chromienie > 200 m (program Buerger I.7 + spacery
«do bólu → odpoczynek» 30–45 min 3–5×/tydz., rzucenie palenia DECYDUJĄCE,
statyny/antyagreganty — lekarz); IIb — < 200 m (angiolog, kwalifikacja
rewaskularyzacji); III — ból spoczynkowy, IV — martwica (SOR/angiolog PILNE;
żadnego masażu leczniczego kończyny, pielęgnacja drugostronna).
Skala Piskorza (0–4 nasilenie chromienia, dystans) — monitorowanie raportem
pacjenta w karcie C.10. Czerwona flaga: nagle blada/zimna/bolesna kończyna
+ brak tętna → zator tętnicy → 112/minuty liczą się dla kończyny.
""",
    "g-9": """# G.9 (H). Porażenia nerwów obwodowych — okresy porażenia/kompensacji/adaptacji, techniki

Rozszerzenie H.9/H.24 (n. łokciowy, pośrodkowy, promieniowy, strzałkowy,
twarzowy; EMG i kwalifikacja — neurolog):
**Okres porażenia (0–6 tyg.±):** ROM bierny 2–3×/dzień (przeciw przykurczom
i CRPS), pozycjonowanie (deska «drop wrist» przy n. promieniowym — zlecenie
terapeuty), głaskanie odpływowe + rozcieranie powierzchowne mięśni
zanikających (skóra wrażliwa na niedożywienie!), ochrona czucia (oparzenia!).
**Okres kompensacji (powrót potencjału — EMG!):** ugniatanie mięśni
zachowanych tej samej grupy (cross-education — strona zdrowa trenowana
siłowo), aktywacje «intencjonalne» (chcieć ruszyć → próbować co 2 h),
EMS/TENS neuromuskularny WYŁĄCZNIE przez uprawnionego fizjoterapeutę.
**Okres adaptacji:** ortezy (AFO przy stope opadającej — ortota/protetyk),
ćwiczenia funkcjonalne ADL (pogrubione uchwyty, zapinanie guzików),
desensytyzacja blizn/neuroma, kontrola zaniku (obwody co 4 tyg.).
Alarm: nagłe wieloobjawowe porażenia, opadanie powieki/diplopia, zaburzenia
mowy → Udar/GBS → 112. Porażenie n. twarzowego (Bell) — okulista! (zamknięcie
powieki, krople), fizjoterapia mimiczna wg Manganaro — certyfikowani.
""",
    "g-10": """# G.10 (H). Porażenie połowicze — okresy, techniki masażu, metody neurofizjologiczne

Rozszerzenie H.10/H.25 (udar: faza ostra szpitalna → podostała rehab →
przewlekła — nasze wsparcie):
**Techniki masażu strony porażonej:** głaskanie odpływowe (profilaktyka DVT
i obrzęku ręki — ręka na poduszce powyżej poziomu serca!), rozcieranie
łopatki/barku (NIE ciągnąć za ramię — podwichnienie bolesne!), delikatne
ugniatanie uda/łydki (tonus ↑ — unikaj szybkiego rozciągania pobudzającego),
pozycjonowanie przeciw przykurczom (barierki, kliny, orteza AFO).
**Metody neurofizjologiczne (kontekst — wykonuje certyfikowany fizjoterapeuta):**
NDT-Bobath (hamowanie wzorców spastyczności + torowanie prawidłowych),
PNF-Kabata (diagonale D1/D2, rhythmic initiation), Brunnstrom (etapy
współruchów → izolacja), Rood (bodźce: brushing,快速 włókien — facylitacja;
ciężar/wibracja — hamowanie). Nasza rola: asysta w przenoszeniu (pivot,
slide-board), układanie w łóżku 2×/2 h, mirror therapy (dowody RCT: ROM/ból),
instruktaż rodziny (asekuracja, upadki), walka z zmęczeniem (pacing),
depresja poudarowa (screening → lekarz).
Czerwone flagi: nowy deficyt → 112 (kolejny udar!).
""",
    "g-11": """# G.11 (H). Choroby przewodu pokarmowego — zaparcia spastyczne i wiotkie; masaż brzucha

Rozszerzenie H.11/H.26 (po wykluczeniu alarmowych przez lekarza: krew,
chudnięcie, niedokrwistość, wiek > 50 nowe objawy → kolonoskopia!):
**Rozróżnienie obserwacyjne:** spastyczne — ból kurczowy, stolce «owcze»
(bristol 1), napięta sigmoida w dole lewym → ROZLUŹNIANIE: głaskanie
zgodne z okrężnicą (coesum→ascendens→transversum→descendens→sigmoid,
zgodnie z ruchem wskazówek zegara od strony pacjenta), ciepły okład,
oddech przeponowy («masaż trzewny przywspółczulny»), relaksacja;
**wiotkie** — seniorzy, hipotonia, brak parcia → STYMULACJA: rozcieranie
fałdu okrężnicy z lekka presją, ucisk punktu ST25 Tianshu (2 cun od pępka
bocznie, obustronnie), ćwiczenia: vacuum łagodny, marsz po posiłku 15 min,
nawodnienie 1,5–2 l, błonnik rozpuszczalny (psyllium — dowody dobre)
wprowadzany PRZEZ 2 tyg. (nie nagle!), probiotyki (Bifidobacterium — dane
umiarkowane w IBS).
Segmenty: Th9–L2 przykręgosłupowo + L5–S2 (esica/odbytnica).
Zakazy: ostry brzuch, przepuklina wcielona, krwawienie z PK, ciąża
(F.7/H.11). Refluks: nie masuj głęboko nadbrzusza po posiłku; IPP — lekarz.
""",
    "g-12": """# G.12 (H). Choroby układu moczowego — masaż segmentarny; kamica: rozcieranie koliste

Rozszerzenie H.12/H.27 (diagnoza i leczenie — lekarz/urolog; my wspomagamy):
**ZUM niepowikłane (kobiety, po antybiogramie/lekarzu):** prewencja:
nawodnienie 1,5–2 l/d, mikcja po stosunku, nie «przetrzymywać»; żurawina —
metaanalizy: efekt mały/żaden (uczciwie!), D-mannoza — dane mieszane.
Masaż wspomagający (faza zdrowienia, BEZ gorączki): Th12–L2 (nerki) +
S2–S4 (pęcherz) przykręgosłupowo łagodnie, brzuch głaskanie podłukowe.
**Kolka nerkowa ATAK:** ŻADNEGO masażu okolicy nerki — pozycja wygodna,
ciepło miejscowe wg zaleceń, leki spasmolityczne/ppy — dyspozytor/lekarz;
gorączka + kamica = SOR (ryzyko sepsy z niedrożności!).
**Między atakami:** rozcieranie koliste Th12–L2 (trójkąt nerki) 5–8 min,
siła 2/5; profilaktyka kamicy: typ kamienia z analizy (szczawianowy —
ogranicz szczaw/rabarbat/herbatę mocną + wapń z diety wiążący szczawiany
w jelicie; moczanowy — puryny, alkohol; fosforanowy — alkaliczny mocz),
nawodnienie «senior: budzić się na mikcję? raczej pić do 18:00 + 1 szklanka
przed snem wg nefrologa».
**NTM:** trening dna miednicy (Kegel instruktaż, biofeedback — fizjo
uroginekologiczny złoty standard), bladder drill, kofeina limit.
Białkomocz/NS: nefrolog; obrzęki — drenaż łagodny za zgodą (F.3!).
""",
    "g-13": """# G.13 (H). Choroby kobiecych narządów płciowych — masaż segmentarny; stymulacja laktacji w 3 fazach

Rozszerzenie H.13/H.28 (ginekolog/położna decydują o kwalifikacji):
**Dysmenorea czynnościowa:** segmenty L1–S2 + krzyżowo (rozcieranie),
podbrzusze głaskanie poprzeczne ciepłymi dłońmi, skośne brzucha ugniatanie
łagodne, pozycja dziecka + oddech; dowody: ciepło miejscowe działa
(metaanalizy), TENS skuteczny, akupunktura/SP6 umiarkowanie; NLPZ — lekarz.
**Endometrioza:** multidyscyplinarnie; nasz zakres: masaż RELAKSACYJNY
grzbietu/miednicy w tolerancji, bez głębokiej pracy w rzucie bólu; dieta
przeciwzapalna (omega-3 — dane obiecujące) jako wsparcie; psychologia bólu
przewlekłego.
**Stymulacja laktacji — 3 fazy:**
1. *Nabrzmiewanie (doba 1–3):* ciepły okład 3–5 min przed karmieniem,
   głaskanie od podstawy ku brodawce (ruch «Marmet» — instruktaż położnej),
   ręczne opróżnianie przy zastoinie; karmienie na żądanie co 2–3 h.
2. *Ustanowienie (tydzień 1–6):* masaż okrężny mleczowodów, unikaj ucisku
   (stanik miękki!), nawodnienie matki, sen; mastitis (gorączka, klin
   zaczerwienienia, ból) → LEKARZ (antybiotyk) + nadal opróżniaj pierś.
3. *Utrzymanie:* regularność karmień/laktatora, «drain the breast» technika,
   wsparcie doradcy laktacyjnego IBCLC.
Zioła galaktogonne ( koper, kminek, fenkuł, rue? NIE ruta!) — dowody słabe;
informuj o tym i kieruj do położnej/lekarza. Ciąża podejrzenie → zakaz
pracy na L5–S2/podbrzuszu.
""",
    "g-14": """# G.14 (H). Stany po urazach — skręcenia, zwichnięcia, złamania, amputacje; drenaż limfatyczny; masaż klasyczny w 3 etapach

Rozszerzenie H.14/H.29 (harmonogram biologiczny + zgoda ortopedy/fizjoterapeuty):
**Etap I — unieruchomienie/gojenie:** NIE pracuj w obszarze złamania/zerwania;
głaskanie odpływowe PROXIMAL i DISTAL (krążenie, DVT-prewencja), counterpart
strony zdrowej (cross-education), ROM bierny wolnych stawów; obrzęk →
metoda Polska (pompowanie 4-kierunkowe, workowanie, kokonowanie — B.4) albo
Niemiecka (Vodder) sekwencja: węzeł docelowy → obwodowo; POLICE przy skręceniu
(protect, optimal loading, ice 10–15 min ×3/d, compression, elevation).
**Etap II — po zdjęciu unieruchomienia:** rozcieranie blizny (≥ 6 tyg., tkanka
miękka; poprzecznie + okrężnie, plastrowanie taping — fizjo), ROM bierny→
czynno-bierny→czynny, drenaż obrzęku pourazowego, propriocepcja (poddudzie
na poduszce 3×30 s).
**Etap III — functionalizacja:** ugniatanie mięśni zanikłych + progresywny
trening siłowy (10 %/tydz.), ekscentryka (ścięgna — protokoły fizjo),
nauka wzorców (chód, schody, ADL).
**Amputacja:** patrz I.15 (bandażowanie kikuta, desensytyzacja, mirror
therapy, PIR zginaczy — kluczowe przeciw przykurczom!); proteza — protetyk.
**Alarm:** ból nieproporcjonalny + napięcie powięziowe (ciasnota!) → SOR;
łydka bolesna/opuchnięta (DVT) → 112/SOR; rana ropa/gorączka → chirurg.
""",
    "g-15": """# G.15 (H). Wady postawy — skoliozy funkcjonalne (masaż w 5 lub 11 fazach) i strukturalne (4 lub 8 faz); kifozy, lordozy, wady stóp

Historyczny podział szkoły Zborowskiego — tłumaczymy go uczniowi językiem
współczesnym i granicami kompetencji:
**Skolioza funkcjonalna (posturalna, korygowalna czynnie, Cobb < 10°):**
program «5 faz» (uproszczony): 1 głaskanie grzbietu; 2 rozcieranie wałów
Th/L; 3 ugniatanie strony WYPUKŁEJ (napiętej) rozluźniająco; 4 strona
WKŁĘSŁA — tylko głaskanie/rozcieranie powierzchowne (nie pobudzać jeszcze
bardziej asymetrii!); 5 oddech + ćwiczenia korekcyjne symetryczne (I.8).
Wariant «11 faz» dodaje: segmenty lędźwiowe → piersiowe → szyjne osobno +
klatka przód + biodra + pośladki + podudzia (asymetria miednicy!).
**Skolioza strukturalna (rotacja kręgów, garb Adamsa, Cobb ≥ 10°):**
ORTOPEDA — orteza/ćwiczenia Schroth u certyfikowanego terapeuty; nasz zakres:
masaż rozluźniający strony wypukłej (4 fazy skrócone: głaskanie-rozcieranie-
ugniatanie-wyciszenie) + 8 faz przy większym napięciu (dodają segmenty
i obręcz barkową); NIE «prostujemy kręgosłupa masażem» — mit!
**Kifozy (plecy okrągłe):** rozluźnić pectoralis + prostownik górny,
wzmocnić retraktory łopatek + deep neck flexors (I.8); ZZSK wykluczyć
(ból nocny, sztywność > 30 min, młody mężczyzna → reumatolog).
**Lordozy (plecy wklęsłe):** rozluźnić zginacze biodra + prostowniki L,
aktywizować core/glutes; ciąża — pozycja boczna.
**Wady stóp:** patrz I.9 (short foot, ekscentryka łydki Rathleff, obuwie);
hallux valgus — nosek szeroki, ortopeda/podolog.
Red flags: ból nocny + progresja > 5°/rok dorosłego → obrazowanie (nowotwór,
spondylolisteza) → lekarz.
""",
}

# ---------------------------------------------------------------------------
# ZAŁĄCZNIK I — dodatkowe pozycje h-* (historyczny spis H.*)
# ---------------------------------------------------------------------------
H_I_EXTRA = {
    "h-2": """# H.2 (I). Ćwiczenia w ZZSK — tor przeponowy, antykifotyczne; zakaz ćwiczeń statycznych i oporowych

Rozszerzenie I.2/I.11 (consensus ASAS/EULAR: aktywność = filar leczenia):
1. **Tor przeponowy:** leżenie tyłem, książka na brzuchu, wdech nosem «książka
   rośnie» 4 s → wydech ustami spiętymi 6–8 s ×10, 3×/dzień; IMT inspirator
   2×30 oddechów (opór 30 cmH₂O — dane: poprawa pojemności i duszności).
2. **Antykifotyczny blok (codziennie):** chin-tuck 3×10 (5 s), retrakcja
   łopatek z gumą face-pull 3×12, foam-extension Th7–Th12 10 powt.,
   doorway pec stretch 3×30 s, prone-on-elbows 2–5 min ×2, «wall angels» 3×10.
3. **ZAKAZ (w zaostrzeniu i zaawansowanej chorobie):** ćwiczeń statycznych
   (długotrwały bezruch w pozycji wymuszonej nasila przykurcze), mocnych
   oporowych i obciążeń aksjalnych (skoki, sztanga nad głową — ryzyko złamań
   «chalk-stick»), biernych manipulacji szyi (niestabilność C1–C2!).
4. Aerobik: pływanie grzbietem/dowolnym 3×/tydz., marsz 30 min, rower
   pozycja wyprostowana; tai-chi/yoga (modyfikacje bez głębokich skłonów).
Kontrola reumatologa (CRP/OB, biologiczne umożliwiają intensywniejszy
trening); red flag: nagły ból po minimalnym urazie → RTG pilne.
""",
    "h-3": """# H.3 (I). Ćwiczenia po zawale — schematy wg okresów (szpitalny, rekonwalescencji, po rekonwalescencji)

Świadomość ról (faza I szpitalna NIE nasza; opis poglądowy):
**Okres szpitalny (faza I, dni 1–7):** wczesne pionizacja wg kardiologa,
ćwiczenia oddechowe, ADL, edukacja; met: MET 2–3, brak objawów.
**Okres rekonwalescencji (faza II, tyg. 2–12, ambulatoryjny nadzór):**
marsz interwałowy 5 min rozgrzewki → 20–30 min RPE 11–13 (talk-test) →
5 min cool-down, 3–5×/tydz.; ćwiczenia dużych grup bez obciążenia
(zgięcia/prostowania, wiosłowanie guma lekka), oddech; próba wysiłkowa co etap.
**Po rekonwalescencji (faza III, mies. 3–6+):** cardio 30–40 min umiarkowanie
(40–70 % HRR Karvonen) 5×/tydz. + interwały 30 s/60 s ×6–10 2×/tydz.;
siła 2×/tydz. 8–12 RM, BEZ Valsalvy (wydech na wysiłek), bez ciężarów
nad głową; elastyczność; BSMS (badania wtórne: lipidogram, HbA1c, echo EF).
Beta-blokery maskują HR — steruj RPE! Kryteria stopu ACSM: ból zamostkowy,
duszność ≥ 7/10, zawrót, arytmia, spadek SBP > 10 mmHg → STOP, lekarz.
Profilaktyka: papierosy ZERO, Mediterranean diet (dobre dowody), sen
(bezdech → polisomnografia), depresja (screening PHQ-9 → lekarz).
""",
    "h-4": """# H.4 (I). Ćwiczenia w astmie i POChP — drenaż ułożeniowy (pozycje wg segmentów) + ćwiczenia oddechowe

Rozszerzenie I.4/I.13 (atlas pozycji: F.9/G.9):
1. Przed ćwiczeniami: reliever wg planu lekarza (astma), rozgrzewka ≥ 10 min
   (prewencja EIB — exercise-induced bronchoconstriction).
2. Drenaż ułożeniowy 20–30 min ×2–3/dobę (POSTAW: przed posiłkami):
   segment wg tabeli F.9 + klapping/wibracja + huffing + kaszel kontrolowany.
3. Oddechowe: pursed-lips (wdech nosem 2 s, wydech «przez słomkę» 4 s),
   oddech przeponowy z oporem (książka), IMT 2×30 oddechów/dzień
   (↓ duszność, ↑ siła wdychaczy — dane dobre w POChP), ACBT (active cycle
   breathing technique: oddechy kontrolne → głęboki → huff ×3 cykle).
4. Trening wysiłkowy POChP (pulmonary rehab, 6–8 tyg.): marsz/rower
   interwałowo 60–75 % max workload, ramiona: arm ergometer (↑ zdolność
   ADL!), siła nóg 2×/tydz., edukacja pacing + pozycje odpoczynku (tripod).
5. Astma: wysiłek ciągły bywa trudniejszy niż interwałowy; pływanie —
   chlor może drażnić (obserwuj); nos-breathing + powietrze ciepłe wilgotne.
Zaostrzenie (↓ PEF < 50 % best, nasilenie duszności, NOCNY relief > 2×/tydz.)
→ STOP program, lekarz pilnie; krwioplucie/odma → SOR.
""",
    "h-11": """# H.11 (I). Gimnastyka w rwie kulszowej — schemat (rozszerzenie I.14)

Program trójfazowy (po wykluczeniu czerwonych flag przez lekarza: ogon
koński, postępujący deficyt, gorączka, nowotwór):
**Faza ostra (ból korzeniowy dominujący):** pozycje odciążające 90/90
(leżenie, podudzia na krześle) 3–4×/dzień 10 min; naprzemienne napinanie
pośladków izometrycznie 5 s ×10; «pelvic tilt» mały zakres; chód krótki
częsty (co 45–60 min 2–3 min); neural FLOSSING (slump dynamiczny: głowa
+ kolano naprzemiennie — NIE rozciągać nerwu «na siłę!»).
**Faza podostra:** McKenzie press-up 10 powt. co 2–3 h (JEŚLI centralizuje
ból — kontynuuj; peryferalizuje → STOP, lekarz); mostek 3×10, bird-dog 3×8,
clamshell 3×15, side-plank kolana 3×20 s; march w miejscu z wysokim kolanem
bez bólu 3×30 s.
**Faza przewlekła/prewencja:** hip-hinge z kijem (martwy ciąg rumuński lekki
3×10), plank przód/bok 3×30 s, przysiady do pudełka 3×10, spacer 30 min
3–5×/tydz.; ergonomia: krzesło 90/90/90 + mikro-pery co 30 min, dźwiganie
«przy ciele, przez biodra», sen na boku z poduszką między kolanami.
Zasada bezpieczeństwa: ból ≤ 3/10 w trakcie i ≤ 24 h; promieniowanie
«schodzące w dół nogi» podczas programu = regresja → lekarz/fizjo.
""",
    "h-12": """# H.12 (I). Ćwiczenia po amputacjach — przygotowanie do protezy, nauka chodzenia

Rozszerzenie I.15 (wszystko za zgodą i we współpracy z rehabilitantem/protetykiem):
**Faza przedprotezowa (kikut po zagojeniu rany, ok. 6–8 tyg.):**
1. Bandażowanie elastyczne (technika «figure-of-eight» przez chirurga/pielęgniarkę
   pokazana; modelowanie kikuta, NIE skrętnie — ryzyko ischemii).
2. PIR/rozwój zginaczy: biodro (wykrok stretch 3×30 s, prone «leżenie
   przodem» 20 min ×2 — przeciw przykurczowi zgięciowemu BIODRA!), kolano
   (prostowanie pod piętą 3×10 min/dzień) — przykurcz = główny wróg protezy.
3. Siła: tułów (dead-bug, bird-dog), kończyna zdrowa (wiosłowanie, mostki,
   farmer carry), równowaga jednonóż z asekuracją 3×20 s.
4. Desensytyzacja kikuta (dotyk fakturami 5 min 2×/dzień) + oględziny skóry
   codziennie (otarcie ⇒ lekarz/protetyk natychmiast).
5. Mirror therapy 30 min/dzień (ból fantomowy — RCT: redukcja; «nie udawaj,
   że nie boli» — edukacja).
**Faza protezowa:** wstawanie z siadu z protezą (poręcz/krzesło), przenoszenie
ciężaru na protezę (weight-shift 3×10), chód po równym → nierówności → schody
(«uszkodzony stopień pierwszy w górę, ostatni w dół» — zasady asekuracji),
stanie na jednej nodze z podparciem; higiena kikuta i lejka protezy (mycie
codziennie, skarpetki bawełniane bez szwów).
**Bezpieczeństwo:** mata, poręcz, asekuranta; zawroty (hipotonia ortostatyczna,
objętość?) → przerwij i ocena lekarska; rana/protezowe otarcie → STOP trening.
""",
}

# ---------------------------------------------------------------------------
# ZAŁĄCZNIK K — brakujące pozycje k-11, k-12
# ---------------------------------------------------------------------------
K_EXTRA = {
    "k-11": """# K.11. Pozycje transportowe — boczna ustalona, przeciwwstrząsowa, siedząca

**Boczna ustalona (nieprzytomny oddychający, brak urazu podejrzanego):**
1. Osoba na plecach; najbliższa ręka nad głowę (pod głowę po obrocie).
2. Dalsza noga: zegnij kolano, stopa płasko — «przepchnij» przez kolano
   na bok ku sobie (rolowanie na bliższy bok).
3. Górna noga zgięta — «klin» stabilizujący; głowa na ręce, twarz w dół
   (odpływ wydzieliny), drożne drogi.
4. Kontrola oddechu co minutę; NIE w urazie kręgosłupa/miednicy/kości
   (tam: oczekiwanie PRM, stabilizacja manualna głowy, jeśli szkolenie).
**Przeciwwstrząsowa (wstrząs hipowolemiczny/rozszerzeniowy, przytomny,
BEZ duszności/urazu głowy):** leżenie płasko, nogi uniesione ~20–30°
(maks. 30 cm — nie «na stojaka»!), termoochrona (koc), spokój, NIC doustnie,
112; przy duszności → półsiedząca; przy urazie kończyny → nie unosimy jej.
**Siedząca (duszność kardiogenna/astma, trauma klatki):** półsiedząc
45–90°, podpory, kolana lekko ugięte (zmniejsza powrót żylny przy obrzęku
płuc), NIE zostawiać samego (ryzyko omdlenia → pozycja leżąca + boczna).
Inne: «tripod» przy POChP; kolano-pierś przy napadnie dychawicznym? (dzieci
— według wskazań pediatry/PRM). Zasada ogólna: ocena ABC → pozycja →
monitoring → 112 dokumentacja czasu i stanu (C.10).
""",
    "k-12": """# K.12. Wyposażenie apteczki felczerskiej (usługowej) — lista

Norma: apteczka przeglądowana co 3 miesiące (data ważności!), dostępna
natychmiast, osoba przeszkolona (B.15/K.10) zna jej zawartość.

**Bariery i ochrona:** rękawiczki nitrylowe ×5 par (rozmiary), maseczka
do RRC (jednokierunkowy wentyl), płyn do dezynfekcji rąk EN1500,
chusteczki alkoholowe (alkohol 70 % w sprayu).
**Opatrunki:** gazy jałowe 5×5/10×10, kompresy niejałowe, bandaż elastyczny
8 cm i 10 cm ×2, plastry z opatrunkiem assortment, hydrożel + folia
(oparzenia/otarcia), nożyczki Listera (końce tępe), pęseta płaska,
klamerki do opatrunków, plaster tkaninowy/«paper tape».
**Dezynfekcja pola:** octenidyna lub chlorheksydyna wodna, NaCl 0,9 %
(ampułki/plastik do irygacji), woda pitna butelkowana awaryjnie.
**Termika i urazy:** pack żelowy zimny (okład owinięty!), termofor/koc
ratunkowy NRC (folia aluminiowa), trójkątna chusta (temblier), szyna
unieruchamiająca (opcja — tylko po szkoleniu z unieruchomienia K.8/BLS),
poduszka-klin.
**Pomiary:** ciśnieniomierz (walidowany), stetoskop? (opcjonalnie),
termometr, pulsoksymetr (opcja), glukometr z paskami (cukrzyca w gabinecie
— edukacja, nie diagnostyka «na gorąco» bez szkolenia), waga łazienkowa.
**Farmacja OTC (tylko zgodnie z ulotką, NIE «recepta»):** — nie podawamy leków klientowi bez wskazań lekarza/farmaceuty; dopuszczalne:
woda, cukierki/glukoza dla przytomnego hipoglikemika (zasada 15 g),
żel chłodzący na ukąszenia.
**Dokumenty:** karta C.8/C.12/C.9, protokół zdarzeń (wypadek przy pracy!),
lista telefonów (112, PRM, sanepid, odbiór odpadów medycznych), harmonogram przeglądów.
**Odpady:** pojemnik UB na igły (jeśli cokolwiek kłujesz — a nie powinieneś),
worki na odpad medyczny (umowa firm utylizacyjnych).
Egzamin: «audit zawartości apteczki» — 20 punktów checklisty w 5 minut.
""",
}

ALL_APPENDIX_CONTENT_MULTI = {
    "25-zalacznik-a-wykaz-lektur/book-01": A_BOOK,
    "26-zalacznik-b-umiejetnosci/book-01": B_SKILLS,
    "27-zalacznik-c-dokumentacja/book-01": C_FORMS,
    "30-zalacznik-f-przeciwwskazania/book-01": [F_CONTRA, E_EXTRA],
    "31-zalacznik-g-mapy-anatomiczne/book-01": [G_MAPS, F_EXTRA],
    "32-zalacznik-h-schematy-masazu/book-01": [H_SCHEMES, G_EXTRA],
    "33-zalacznik-i-kinezyterapia/book-01": [I_EX, H_I_EXTRA],
    "34-zalacznik-j-coachingu/book-01": J_COACH,
    "35-zalacznik-k-zabiegi-felczerskie/book-01": [K_CIRR, K_EXTRA],
}


'''
rep('ALL_APPENDIX_CONTENT = {', NEW_DICTS + 'ALL_APPENDIX_CONTENT = {')

# main(): obsługa listy słowników + poprawne raportowanie nieużytych kluczy
rep('''        used_keys = set()
        for ch in sorted(chdir.glob("*.md")):
            key = norm_key(ch.stem, sec_book)
            text = ch.read_text(encoding="utf-8")
            if GENERIC_MARKER not in text:
                skipped_content += 1
                continue
            content = mapping.get(key)''',
'''        used_keys = set()
        maps = mapping if isinstance(mapping, list) else [mapping]
        for ch in sorted(chdir.glob("*.md")):
            key = norm_key(ch.stem, sec_book)
            text = ch.read_text(encoding="utf-8")
            if GENERIC_MARKER not in text:
                skipped_content += 1
                continue
            content = ""
            for mp in maps:
                if key in mp:
                    content = mp[key]
                    break''')

rep('''        unused = set(mapping) - used_keys''',
'''        all_keys = set()
        for mp in maps:
            all_keys |= set(mp)
        unused = all_keys - used_keys''')

P.write_text(src, encoding="utf-8")
print("\nZapisano:", P)

