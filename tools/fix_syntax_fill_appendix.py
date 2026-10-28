#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Naprawa błędów składniowych scripts/fill_appendix_books_naturopata.py.

Usuwa zdublowane linie kluczy słownika, skleja uszkodzone otwarcia
potrójnych cudzysłowów, uzupełnia ucięte końcówki zdań w treści oraz
poprawia literówkę (znak CJK '安全' -> 'bezpiecznej').
"""
from pathlib import Path

p = Path("scripts/fill_appendix_books_naturopata.py")
lines = p.read_text(encoding="utf-8").split("\n")

TQ = '"""'          # potrójny cudzysłów
CLOSE = TQ + ','    # zamknięcie wpisu słownika: """,

# --- 1. Usunięcie zdublowanych linii kluczy (b-15, b-16) ---
assert lines[382] == '    "b-15": ' + TQ, repr(lines[382])
assert lines[404] == '    "b-16": ' + TQ + 'a).', repr(lines[404])
assert lines[405] == '', repr(lines[405])
del lines[404:406]   # najpierw dalsze indeksy
del lines[382]       # zdublowany klucz b-15


def find_key(key):
    prefix = '    "' + key + '":'
    for i, l in enumerate(lines):
        if l.startswith(prefix):
            return i
    raise KeyError(key)


def terminator(idx):
    """Indeks linii zamykającej wpis ('"'"''"'"''"'"',) dla wpisu od idx."""
    j = idx + 1
    while not lines[j].rstrip().endswith(CLOSE):
        j += 1
    return j


# --- 2. Naprawa uszkodzonych otwarć wpisów (b-11, b-12, b-13) ---
import re as _re

BAD_OPEN = _re.compile(
    r'^    "(b-1[123])":\s+"""(?:[^#]*)?(# B\.\d+\..*)$'
)
for i, l in enumerate(lines):
    m = BAD_OPEN.match(l)
    if m:
        key, title = m.group(1), m.group(2)
        lines[i] = '    "' + key + '": ' + TQ + title
        print("naprawiono otwarcie wpisu:", key)
fixed_open = sum(1 for l in lines if _re.match(r'^    "b-1[123]": """# B\.', l))
assert fixed_open == 3, fixed_open

# --- 3. Uzupełnienie uciętych końcówek zdań przed zamknięciem ---
fixes = {
    "b-10": (
        "poparzenia słonecz",
        "poparzenia słoneczne, fotouczulenia ziołowe — dziurawiec, pasternak!),\n"
        "przeciwwskazania (F.5) oraz zapis parametrów w karcie zabiegowej (C.2).",
    ),
    "b-11": (
        "i pod kątem metali c",
        "i pod kątem metali ciężkich oraz pozostałości pestycydów.",
    ),
    "b-12": (
        "w normach, co wymaga konsultacji ",
        "w normach, co wymaga konsultacji lekarskiej» (bez stawiania rozpoznań).",
    ),
    "b-14": (
        "własnoręcznie przygotowanym materia",
        "własnoręcznie przygotowanym materiałem edukacyjnym (ulotka o inhalatorze).",
    ),
    "b-15": (
        "certyfikat zewnęt",
        "certyfikat zewnętrzny, np. pierwszej pomocy medycznej).",
    ),
}
for key, (old, new) in fixes.items():
    ki = find_key(key)
    ti = terminator(ki)
    seg = "\n".join(lines[ki:ti + 1])
    assert old in seg, key
    seg = seg.replace(old, new)
    lines[ki:ti + 1] = seg.rstrip("\n").split("\n")
    print("uzupełniono ucięcie:", key)

# --- 4. Literówka: chiński znak '安全' -> 'bezpiecznej' ---
fixed_cjk = 0
for i, l in enumerate(lines):
    if "安全" in l:
        lines[i] = l.replace("receptury安全", "receptury bezpiecznej").replace("安全", "bezpiecznej")
        fixed_cjk += 1
print("poprawiono znaków CJK:", fixed_cjk)

p.write_text("\n".join(lines), encoding="utf-8")
print("ZAPISANO", p)
