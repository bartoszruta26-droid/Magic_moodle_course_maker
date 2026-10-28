#!/usr/bin/env python3
"""Generator schematycznej struktury kursu Moodle: kwalifikacyjny kurs masażysty (MED.10).
Tworzy wyłącznie puste pliki (szkielet), bez treści."""
import re, os, unicodedata

SRC = os.path.join(os.path.dirname(__file__), '..', 'kurs_masazu.txt')
DST = '/workspace/courses/03-kurs-masazysta-med10'

def slugify(s, maxlen=45):
    s = s.lower()
    trans = {'ą':'a','ć':'c','ę':'e','ł':'l','ń':'n','ó':'o','ś':'s','ź':'z','ż':'z'}
    s = ''.join(trans.get(c, c) for c in s)
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:maxlen].strip('-')

text = open(SRC, encoding='utf-8').read()

# --- Moduły: "## MODUŁ N" następnie "## TYTUŁ" ---
mods = re.findall(r'^## (MODUŁ \d+)\s*^## (.+?)\s*$', text, re.M)
print('Moduły znalezione:', len(mods))
for num, title in mods:
    print(' ', num, '=>', title)

# --- Rozdziały wewnątrz modułów: "### N.K. Tytuł" ---
chapters = re.findall(r'^### (\d+\.\d+)\.\s+(.+?)\s*$', text, re.M)
print('Rozdziały znalezione:', len(chapters))

os.makedirs(DST, exist_ok=True)

# Pliki katalogu głównego kursu (puste)
for f in ['course.yaml', 'course.md', 'tags.yaml', 'settings.yaml',
          'completion.yaml', 'grades.yaml', 'changelog.md']:
    open(os.path.join(DST, f), 'w').close()

# Sekcja 0 – ogłoszenia
sec0 = os.path.join(DST, 'sections', '00-ogloszenia')
os.makedirs(sec0, exist_ok=True)
open(os.path.join(sec0, 'section.yaml'), 'w').close()
open(os.path.join(sec0, 'page.md'), 'w').close()

# Sekcje = moduły kursu
for i, (num, title) in enumerate(mods, start=1):
    n = int(re.search(r'\d+', num).group())
    dirname = f'{n:02d}-{slugify(title)}'
    p = os.path.join(DST, 'sections', dirname)
    os.makedirs(p, exist_ok=True)
    open(os.path.join(p, 'section.yaml'), 'w').close()
    open(os.path.join(p, 'section.md'), 'w').close()

# Bank pytań (puste)
qb = os.path.join(DST, 'question-bank')
for sub in ['multichoice', 'truefalse', 'shortanswer', 'matching', 'essay']:
    d = os.path.join(qb, sub)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'set-01.gift'), 'w').close()
open(os.path.join(qb, 'categories.yaml'), 'w').close()

# Katalogi mediów (puste, z .gitkeep)
for sub in ['images', 'audio', 'videos', 'documents']:
    d = os.path.join(DST, 'media', sub)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, '.gitkeep'), 'w').close()

print('Utworzono szkielet w:', DST)
