# 🇸🇰 Slovenský Manuál - ScreenAI Test Automation Tool

## 📖 Úvod

ScreenAI Test Automation Tool je pokročilý Python nástroj, ktorý automaticky generuje Maestro test flows z text súborov pomocou analýzy screenshotov a AI detekcie UI elementov. Aplikácia používa Microsoft OmniParser model na identifikáciu tlačidiel, textových polí a iných interaktívnych prvkov na obrazovke. Následne vytvára YAML súbory kompatibilné s Maestro test frameworkom, ktoré môžu automaticky klikať na správne miesta bez manuálneho zadávania súradníc. Tento nástroj je špeciálne optimalizovaný pre slovenské webové aplikácie a podporuje OCR rozpoznávanie slovenského textu. Nástroj dokáže pracovať s Flutter web aplikáciami, kde tradičné text-based selektory často nefungují.

## 🏗️ Architektúra Aplikácie

### Hlavné Komponenty

**src/main.py** - Hlavný orchestrátor celej aplikácie
Tento súbor obsahuje hlavnú logiku, ktorá koordinuje všetky ostatné moduly a riadi celý workflow. Orchestrátor spracováva argumenty príkazového riadku, inicializuje všetky potrebné komponenty a riadi postupnosť krokov od načítania test case až po generovanie finálneho YAML súboru. Obsahuje aj špeciálny režim na analýzu screenshotov volaný z Maestro testov pomocí runScript príkazov. Pri spustení načíta všetky AI modely, pripraví OCR čítač a nastaví všetky potrebné závislosti. Taktiež obsahuje error handling pre rôzne scenáre a logging pre debugging účely.

**src/vision.py** - OmniParser integrácia a UI detekcia
Tento modul je zodpovedný za načítanie a používanie Microsoft OmniParser modelov na detekciu UI elementov na screenshotoch. Používa YOLO model na detekciu bounding boxov interaktívnych prvkov a Florence-2 model na generovanie opisov elementov. Obsahuje pokročilé OCR spracovanie pomocí EasyOCR knižnice, ktoré dokáže rozpoznať slovenský text v UI elementoch. Modul automaticky klasifikuje typy elementov (button, text_input, dropdown, atď.) na základe vizuálnych charakteristík a OCR textu. Implementuje aj systém mergingu prekrývajúcich sa detekcií, aby eliminoval duplicitné elementy v rovnakej oblasti.

**src/matcher.py** - Inteligentné párovanie UI elementov
Matcher je sofistikovaný systém na párovanie textových opisov z test cases s reálne detekovanými UI elementmi. Používa fuzzy string matching algoritmy na nájdenie najlepších zhôd medzi požadovaným textom a OCR textom z elementov. Obsahuje špeciálnu logiku pre slovenské UI vzory a podporuje normalizáciu slovenských znakov pre lepšie rozpoznávanie. Má vstavaný systém synoným a keyword detekcie, ktorý rozpozná rôzne spôsoby pomenovania rovnakých elementov. Implementuje aj kontextové párovanie, ktoré berie do úvahy pozíciu elementov a typ stránky.

**src/parser.py** - Spracovanie test case súborov
Parser načítava a interpretuje .txt súbory obsahujúce test case inštrukcie v slovenčine alebo angličtine. Rozpoznáva rôzne typy akcií ako "otvor", "klikni", "zadaj", "počkaj" a konvertuje ich do štruktúrovaných objektov. Dokáže spracovať komplexné scenáre s viacerými krokmi a prechodmi medzi stránkami. Validuje syntax test cases a upozorňuje na potenciálne problémy. Parser je flexibilný a dokáže pracovať s rôznymi formátmi zápisu inštrukcií. Obsahuje aj podporu pre komentáre a metadata v test case súboroch.

**src/generator.py** - Generovanie Maestro YAML súborov
Generator konvertuje detekované UI elementy a ich súradnice do finálneho YAML formátu kompatibilného s Maestro frameworkom. Konvertuje pixel súradnice na percentuálne hodnoty, ktoré sú resolution-independent a fungujú na rôznych zariadeniach. Generuje správnu YAML štruktúru s URL konfiguráciou pre web aplikácie alebo appId pre mobilné aplikácie. Obsahuje template systém pre rôzne typy akcií a dokáže pridať waitForAnimationToEnd príkazy tam, kde sú potrebné. Generator podporuje aj špeciálne príkazy ako scroll a swipe pre komplexnejšie interakcie.

**src/screenshot.py** - Screenshot management
Tento modul riadi zachytávanie screenshotov pomocą Selenium WebDriver pre web aplikácie. Podporuje headless režim pre CI/CD prostredie a automaticky spravuje lifecycle webových browserov. Ukladá screenshoty s timestamp názvami a vracia informácie o rozmeroch obrázkov potrebné pre konverziu súradníc. Obsahuje konfigurovateľné možnosti pre rôzne typy browserov a rozlíšení. Dokáže pracovať s existujúcimi browser session alebo otvárať nové podľa potreby.

## 🚀 Inštalácia a Nastavenie

### Požiadavky
```bash
# Python 3.8 alebo novší
python --version

# Git pre klonovanie repozitárov
git --version

# Dostatok miesta na disku (aspoň 5GB pre AI modely)
df -h
```

### Krok za krokom inštalácia
```bash
# 1. Klonuj hlavný repozitár
git clone https://github.com/user/ScreenAI
cd ScreenAI

# 2. Vytvor virtuálne prostredie
python -m venv venv
source venv/bin/activate  # Linux/Mac
# alebo
venv\Scripts\activate  # Windows

# 3. Nainštaluj závislosti
pip install -r requirements.txt

# 4. Klonuj OmniParser modely
git clone https://github.com/microsoft/OmniParser
cd OmniParser

# 5. Stiahni AI model weights (vyžaduje HuggingFace CLI)
pip install huggingface_hub
huggingface-cli download microsoft/OmniParser-v2.0 --local-dir weights/

# 6. Vráť sa do hlavného adresára
cd ..

# 7. Vytvor potrebné adresáre
mkdir -p screenshots/objednavka flows test_cases
```

## 📝 Hlavné Skripty a Použitie

### 1. Hlavný Analyzer (main.py)
```bash
# Základné spustenie - analýza konkrétneho screenshotu
python -m src.main --analyze-screenshot screenshots/objednavka/screenshot.png --update-yaml flows/objednavka.yaml

# Analýza s debug výstupom
python -m src.main --debug --analyze-screenshot screenshots/objednavka/screenshot.png --update-yaml flows/objednavka.yaml

# Spracovanie celého test case súboru
python -m src.main test_cases/priklad.txt

# Spracovanie všetkých test cases v adresári
python -m src.main test_cases/

# Pokračovanie existujúcej browser session
python -m src.main --continue test_cases/priklad.txt
```

Hlavný analyzer je srdce celej aplikácie, ktoré koordinuje všetky ostatné komponenty. Pri spustení v analyze-screenshot režime načíta screenshot, spustí AI detekciu, nájde UI elementy a aktualizuje YAML súbor s novými súradnicami. Debug režim poskytuje detailný výstup o tom, aké elementy boli nájdené a ako prebieha matching process. Pri spracovaní test case súborov orchestrátor postupne prechádza všetky kroky, robí screenshoty a generuje kompletnú Maestro flow.

### 2. Real-time Screenshot Watcher (watch_screenshots.py)
```bash
# Spustenie automatického watchera
python watch_screenshots.py

# Alebo pomocou convenience skriptu
./start_watcher.sh

# Watcher beží na pozadí a sleduje nové súbory
# Ctrl+C pre zastavenie
```

Screenshot watcher je pokročilý systém, ktorý monitoruje adresár screenshots/objednavka/ a automaticky analyzuje každý nový PNG súbor, ktorý sa tam objaví. Keď Maestro test vytvára nové screenshoty, watcher ich okamžite zachytí, spustí AI analýzu a aktualizuje koordináty v YAML súbore. Tento real-time systém umožňuje, aby Maestro testy používali aktualizované koordináty už v ďalšom kroku. Watcher presúva všetky analyzované súbory do FINISHED adresára, aby zabránil opakovanému spracovaniu.

### 3. Cleanup Script (cleanup_analyzed_files.py)
```bash
# Vyčistenie starých analyzovaných súborov
python cleanup_analyzed_files.py

# Skript presunie všetky _analyzed súbory do FINISHED adresára
chmod +x cleanup_analyzed_files.py
./cleanup_analyzed_files.py
```

Cleanup script je utility nástroj na organizáciu súborov a predchádzanie nekonečných slučiek pri analyzovaní. Prehľadá screenshots adresár, nájde všetky súbory s "_analyzed" v názve a presunie ich do FINISHED podadresára. Tento skript je užitočný pri debugging alebo keď sa nakumuluje veľa analyzovaných súborov. Cleanup script taktiež odstraňuje duplicitné súbory a loguje všetky operácie.

### 4. Test Watcher (test_watcher.py)
```bash
# Test watcher funkcionality
python test_watcher.py

# Vytvorí test screenshot a overí, či ho watcher zachytí
# Užitočné pre debugging watcher problémov
```

Test watcher je diagnostic nástroj, ktorý overuje, či screenshot watcher správne funguje. Vytvorí kópiu existujúceho screenshotu s novým timestamp názvom, čím simuluje vytvorenie nového screenshotu. Ak watcher beží, mal by okamžite zachytiť tento nový súbor a spustiť analýzu. Test script je užitočný pri riešení problémov s file monitoring alebo permissions.

## 🔄 Typický Workflow

### Príprava Test Case
```bash
# 1. Vytvor test case súbor
cat > test_cases/moj_test.txt << EOF
1. Otvor https://testsk.unilabs.pro
2. Počkaj 3 sekundy
3. Klikni na "Prihlasovacie meno"
4. Zadaj "admin@unilabs.sk"
5. Klikni na "Heslo"
6. Zadaj "malina"
7. Klikni na "Prihlasit sa"
8. Urobenie screenshot
9. Klikni na "Nová objednávka"
EOF
```

### Spustenie s Watcher Systémom
```bash
# Terminál 1: Spusti watcher
./start_watcher.sh

# Terminál 2: Spusti Maestro test
maestro test flows/objednavka.yaml

# Watcher automaticky aktualizuje koordináty počas behu testu
```

### Manuálna Analýza
```bash
# Analýza konkrétneho screenshotu
python -m src.main --analyze-screenshot screenshots/objednavka/screenshot_step_05.png --update-yaml flows/objednavka.yaml

# Zobraz výsledky analýzy
cat flows/objednavka.yaml

# Skontroluj analyzované súbory
ls -la screenshots/objednavka/FINISHED/
```

## 🛠️ Maestro Flow Syntax

### Základné Príkazy
```yaml
# URL konfigurácia pre web aplikácie
url: https://testsk.unilabs.pro
---

# Spustenie aplikácie
- launchApp

# Čakanie na animácie
- waitForAnimationToEnd:
    timeout: 5000

# Kliknutie na presné súradnice
- tapOn:
    point: 73%,19%  # Percentuálne súradnice

# Zadanie textu
- inputText: admin@unilabs.sk

# Vytvorenie screenshotu
- takeScreenshot: screenshots/objednavka/step_01

# Spustenie JavaScript kódu
- runScript:
    file: analyze_screenshot.js
    env:
      SCREENSHOT_PATH: screenshots/objednavka/step_01.png
      TEST_NAME: objednavka
      ACTION_INDEX: '1'
```

### Pokročilé Príkazy
```yaml
# Swipe gesta pre scrollovanie
- swipe:
    start: 50%,80%    # Začiatok swipe
    end: 50%,20%      # Koniec swipe

# Dlhé čakanie pre loading
- waitForAnimationToEnd:
    timeout: 25000

# Podmienené akcie (optional)
- tapOn:
    text: "Nepovinné tlačidlo"
    optional: true

# Assertie pre validáciu
- assertVisible:
    text: "Úspešne prihlásený"
```

## 📊 Výstup a Logging

### Watcher Výstup
```
🚀 Starting ScreenAI Coordinate Watcher
📁 Watching: screenshots/objednavka/
📄 Updating: flows/objednavka.yaml

INFO: 👀 Watching for screenshots in: screenshots/objednavka
INFO: 🖼️  New screenshot detected: objednavka_step_11.png
INFO: 🔍 Analyzing screenshot: screenshots/objednavka/objednavka_step_11.png

🔍 Available OCR texts in screenshot:
   1: 'Prihlasovacie meno' (confidence: 0.892, type: text_field)
   2: 'Heslo' (confidence: 0.945, type: text_field)
   3: 'Prihlasit sa' (confidence: 0.889, type: button)

🔍 Searching for element: 'Heslo'
✅ TODO → Updated: 'Heslo' → 73%,25% (matched: 'Heslo' score: 100.0)

📊 Update Summary:
   ✅ Total updated: 3
   🆕 TODO items updated: 2
   🔄 Existing items updated: 1
   ❌ Items not found: 0

💾 Saved updated coordinates to objednavka.yaml
📁 Moved to FINISHED: objednavka_step_11_analyzed.png
```

### Debug Výstup
```bash
# Spustenie s detailným logovaním
python -m src.main --debug --analyze-screenshot screenshot.png --update-yaml flow.yaml

# Výstup obsahuje:
# - Načítané AI modely
# - Detekované UI elementy s confidence scores
# - OCR text pre každý element
# - Matching algoritmus kroky
# - Finálne súradnice a dôvod výberu
```

## 🔧 Konfigurácia a Customizácia

### Nastavenie AI Modelov
```python
# V src/vision.py môžete upraviť:
def __init__(self, weights_dir: str = "weights", skip_captioning: bool = True):
    self.fuzzy_threshold = 70.0  # Threshold pre fuzzy matching
    self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
```

### Slovenské OCR Opravy
```python
# V src/matcher.py je definovaný mapping pre časté OCR chyby:
self.slovak_ocr_fixes = {
    'iekara': 'lekara',      # I vs L
    'vyhiadat': 'vyhladat',  # i vs l
    'Iekara': 'Lekara',      # Kapitálky
    'vyhIadat': 'vyhladat',  # L vs I uppercase
}
```

### Watcher Konfigurácia
```python
# V watch_screenshots.py:
timeout=30  # Timeout pre analýzu v sekundách
screenshots_dir = Path("screenshots/objednavka")  # Sledovaný adresár
yaml_file = Path("flows/objednavka.yaml")  # YAML súbor na aktualizáciu
```

## 🐛 Troubleshooting

### Časté Problémy a Riešenia

**Problem: "Cannot read property 'SCREENSHOT_PATH' from undefined"**
```bash
# Riešenie: Environment premenné v Maestro sú globálne
# V analyze_screenshot.js použite:
var screenshotPath = SCREENSHOT_PATH;  // NIE maestro.env.SCREENSHOT_PATH
```

**Problem: "Element merging: 45 → 32 elements"**
```bash
# Normálne správanie - systém spája prekrývajúce sa detekcie
# Ak je príliš agresívne, upravte v src/vision.py:
overlap_ratio > 0.5  # Znížte na 0.3 pre menej mergingu
```

**Problem: "No match found for 'Vyhľadať Lekára'"**
```bash
# Skontrolujte OCR výstup:
grep "Available OCR texts" logs.txt

# Skontrolujte slovenské znaky:
# Možno "ľ" sa rozpoznáva ako "l"
```

**Problem: Watcher nedetekuje súbory**
```bash
# Skontrolujte permissions:
ls -la screenshots/objednavka/

# Skontrolujte, či je adresár správny:
pwd
ls screenshots/

# Reštart watcher:
pkill -f watch_screenshots.py
python watch_screenshots.py
```

**Problem: "Unknown Property: direction" v Maestro**
```yaml
# Nepoužívajte scroll command, použite swipe:
# CHYBA:
- scroll:
    direction: DOWN

# SPRÁVNE:
- swipe:
    start: 50%,80%
    end: 50%,20%
```

## 📈 Optimalizácia Performance

### AI Model Performance
```bash
# Pre GPU akceleráciu:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Monitoring GPU využitia:
nvidia-smi

# Ak GPU nie je dostupná, modely bežia na CPU (pomalšie)
```

### Screenshot Processing
```python
# V src/vision.py môžete upraviť rozlíšenie pre rýchlejšie spracovanie:
results = self.yolo_model(image_np, imgsz=640, conf=0.2, iou=0.9)
# Znížte imgsz na 320 pre rýchlejšie spracovanie (horšia presnosť)
```

### Batch Processing
```bash
# Spracovanie viacerých test cases naraz:
python -m src.main test_cases/

# Paralelné spustenie (experimentálne):
for file in test_cases/*.txt; do
    python -m src.main "$file" &
done
wait
```

## 🔒 Bezpečnosť a Best Practices

### Ochrana Dát
- Nikdy necommitujte credentials do Git repozitára
- Používajte environment premenné pre citlivé údaje
- Screenshoty môžu obsahovať citlivé informácie - zabezpečte ich
- AI modely môžu obsahovať bias - validujte výsledky

### Code Quality
```bash
# Spustenie testov:
pytest tests/

# Code linting:
flake8 src/
black src/

# Type checking:
mypy src/
```

### Monitoring
```bash
# Sledovanie log súborov:
tail -f ~/.maestro/tests/*/maestro.log

# Disk space monitoring (AI modely sú veľké):
du -sh weights/
df -h
```

Tento manuál pokrýva všetky aspekty používania ScreenAI Test Automation Tool. Pre ďalšie otázky skontrolujte CLAUDE.md súbor alebo GitHub Issues.