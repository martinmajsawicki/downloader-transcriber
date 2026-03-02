# Metoda weryfikacji nazw produktowych

Wyekstrahowano z analizy nazw dla aplikacji macOS (marzec 2026).

---

## 1. Framework oceny: SMILE & SCRATCH

Autor: Alexandra Watkins. Sprawdzone narzędzie w branży namingowej do obiektywnej oceny siły i potencjału komercyjnego nazwy.

### SMILE — cechy dobrej nazwy

| Litera | Kryterium | Opis |
|--------|-----------|------|
| **S** | Suggestive | Wywołuje pozytywne skojarzenia z marką |
| **M** | Meaningful | Odbiorca rozumie, czym jest produkt |
| **I** | Imagery | Tworzy wizualny obraz w głowie |
| **L** | Legs | Ma potencjał do budowania szerszej komunikacji i rozszerzania marki |
| **E** | Emotional | Nawiązuje więź z użytkownikiem |

### SCRATCH — cechy, których unikamy

| Litera | Kryterium | Opis |
|--------|-----------|------|
| **S** | Spelling-challenged | Wygląda jak literówka |
| **C** | Copycat | Zbyt podobna do konkurencji |
| **R** | Restrictive | Ogranicza przyszły rozwój produktu |
| **A** | Annoying | Trudna do wymówienia lub przekombinowana |
| **T** | Tame | Nudna, nie wyróżniająca się |
| **C** | Curse of Knowledge | Zrozumiała tylko dla wtajemniczonych |
| **H** | Hard-to-pronounce | Trudna w wymowie |

---

## 2. Pięciopunktowa weryfikacja techniczna

Każda kandydacka nazwa przechodzi przez 5 niezależnych kontroli:

### 2.1. App Store (Mac/iOS)
- Sprawdzenie dostępności nazwy w Mac App Store i iOS App Store
- Narzędzie: iTunes Search API
- Wynik: Czysto / Zajęta (+ nazwa konfliktu)

### 2.2. Domena
- Sprawdzenie dostępności domeny `.app` (priorytet)
- Alternatywy: `.ai`, `get[nazwa].com`
- Narzędzie: RDAP / Namecheap lookup
- Wynik: Dostępna / Zajęta / Premium

### 2.3. Kolizje brandowe
- Obecność firm lub produktów o tej samej nazwie w branżach: productivity, AI, software
- Metoda: przegląd wyników Google, Product Hunt, Crunchbase
- Wynik: Brak / Nazwa kolizji + opis ryzyka

### 2.4. Unikalność SEO
- Jak łatwo wypozycjonować nazwę w Google
- Czy nazwa jest generycznym słowem (trudne SEO) czy unikalna
- Wynik: Wysoka / Średnia / Niska / Bardzo niska

### 2.5. Znaki towarowe (USPTO)
- Sprawdzenie bazy USPTO w kategoriach software: IC 009 (oprogramowanie), IC 042 (usługi IT)
- Status znaków: aktywne vs. martwe/anulowane
- Wynik: Czysto (0 wyników) / Czysto (martwe znaki) / Zarejestrowana (konflikt)

---

## 3. Styl pracy i proces

### Generowanie kandydatów
- Nazwy budowane wokół kluczowych funkcji produktu (wideo, audio, transkrypcja, insighty, lokalne notatki)
- Techniki: neologizmy (Clipsight, Synthex), zapożyczenia z łaciny (Notula, Vox), metafory (Capsule, Inkwell, Meridian), złożenia funkcjonalne (Audionote, Podex)
- Cel: 10-15 kandydatów o zróżnicowanym charakterze

### Ocena jakościowa (SMILE)
- Każdy kandydat oceniany pod kątem 5 kryteriów SMILE
- Opis słowny, nie punktowy — dlaczego nazwa pasuje lub nie pasuje

### Weryfikacja techniczna
- Wszystkie 5 punktów weryfikacji dla każdego kandydata
- Wyniki zebrane w tabeli zbiorczej
- Jasne statusy: Doskonała / Bardzo Dobra / Dobra / Akceptowalna / Odrzucona

### Rekomendacja
- Top 5 ranking z uzasadnieniem dla każdej pozycji
- Dla każdej nazwy: dlaczego ta pozycja + wynik SMILE + wynik weryfikacji
- Jasny faworyt z podsumowaniem

---

## 4. Tabela zbiorcza — szablon

```
| Nazwa | App Store | Domena .app | Kolizje | SEO | USPTO | Ocena |
|-------|-----------|-------------|---------|-----|-------|-------|
| ...   | Czysto/Zajęta | Dostępna/Zajęta | Brak/Opis | W/Ś/N | Czysto/Zajęta | Ocena |
```

---

## 5. Kryteria odrzucenia (knockout)

Nazwa jest odrzucana, jeśli zachodzi którykolwiek z poniższych:
- Domena `.app` zajęta ORAZ silna kolizja brandowa w tej samej branży
- Aktywny znak towarowy USPTO w kategorii software (IC 009/042)
- Zajęta w App Store przez bezpośredniego konkurenta
- Bardzo niska unikalność SEO (generyczne słowo, setki wyników)
