# 🎯 Jednoduchý Návod - Ako Vytvoriť a Spustiť Test

## 👶 Pre Malé Dieťa (Krok za krokom)

Predstav si, že máš magický nástroj, ktorý sa dokáže naučiť klikať na webovú stránku presne tam, kde ty chceš! Tento nástroj sa volá ScreenAI a funguje ako veľmi chytrý robot.

### 🏠 Krok 1: Priprav si domček pre svoj test

```bash
# Choď do hlavného adresára (to je ako tvoj domček)
cd /Volumes/DATA/Python/ScreenAI

# Vytvor si špeciálnu škatulku na test súbory
mkdir -p test_cases

# Vytvor si škatulku na obrázky
mkdir -p screenshots/objednavka

# Vytvor si škatulku na výsledky
mkdir -p flows
```

### 📝 Krok 2: Napíš si zoznam čo chceš robiť (Test Case)

Vytvor súbor, kde napíšeš čo chceš, aby robot robil:

```bash
# Otvor textový editor a vytvor nový súbor
nano test_cases/moj_prvy_test.txt
```

Do súboru napíš jednoduchý zoznam úloh (ako keď si robíš zoznam na nákup):

```text
1. Otvor https://testsk.unilabs.pro
2. Počkaj 3 sekundy
3. Urobenie screenshot
4. Klikni na "Prihlasovacie meno"
5. Zadaj "admin@unilabs.sk"
6. Klikni na "Heslo" 
7. Zadaj "malina"
8. Klikni na "Prihlasit sa"
9. Počkaj 5 sekúnd
10. Urobenie screenshot
11. Klikni na "Nová objednávka"
```

Ulož súbor (Ctrl+X, potom Y, potom Enter).

### 🤖 Krok 3: Spusti magického robota (Generovanie YAML)

Teraz povieš robotovi, aby si prečítal tvoj zoznam a naučil sa ho:

```bash
# Robot si prečíta tvoj zoznam a vytvorí si vlastné inštrukcie
python -m src.main test_cases/moj_prvy_test.txt
```

Robot teraz:
- Otvorí internetový prehliadač 
- Zoberie obrázky webovej stránky
- Pomocou umelej inteligencie nájde tlačidlá a polia
- Vytvorí súbor `flows/moj_prvy_test.yaml` s presnými inštrukciami

### 👀 Krok 4: Spusti sledovača (Watcher System)

Sledovač je ako strážny pes, ktorý sleduje, či sa objavili nové obrázky:

```bash
# V prvom okne terminálu spusti sledovača
./start_watcher.sh
```

Uvidíš:
```
🚀 Starting ScreenAI Coordinate Watcher
📁 Watching: screenshots/objednavka/
📄 Updating: flows/objednavka.yaml
🚀 Start your Maestro test now!
```

### 🎬 Krok 5: Spusti test (Maestro)

V druhom okne terminálu spusti samotný test:

```bash
# Otvor nové okno terminálu a spusti test
maestro test flows/moj_prvy_test.yaml
```

### 🎉 Krok 6: Sleduj kúzlo!

Teraz sa deje kúzlo:

1. **Maestro** začne robiť test - otvára stránku, robí obrázky
2. **Sledovač** okamžite zachytí každý nový obrázek  
3. **AI robot** analyzuje obrázok a nájde tlačidlá
4. **Sledovač** aktualizuje koordináty v YAML súbore
5. **Maestro** použije nové koordináty na kliknutie na správne miesto

Výstup v sledovači vyzerá:
```
🖼️  New screenshot detected: objednavka_step_03.png
🔍 Analyzing screenshot: screenshots/objednavka/objednavka_step_03.png
✅ TODO → Updated: 'Prihlasovacie meno' → 73%,19% (matched: 'Prihlasovacie meno' score: 95.0)
✅ TODO → Updated: 'Heslo' → 73%,25% (matched: 'Heslo' score: 100.0)
💾 Saved updated coordinates to moj_prvy_test.yaml
📁 Moved to FINISHED: objednavka_step_03_analyzed.png
```

## 📚 Pokročilejšie Možnosti

### Rôzne Typy Test Cases

**Jednoduchý test prihlásenia:**
```text
1. Otvor https://example.com
2. Klikni na "Login"
3. Zadaj "mojemeno"
4. Klikni na "Password"
5. Zadaj "mojeHeslo123"
6. Klikni na "Submit"
```

**Test s čakaním a scrollovaním:**
```text
1. Otvor https://dlhastrana.com
2. Počkaj 3 sekundy
3. Scrolluj dole
4. Klikni na "Ďalej"
5. Urobenie screenshot
6. Klikni na "Dokončiť"
```

**Test s viacerými krokmi:**
```text
1. Otvor https://eshop.sk
2. Klikni na "Produkty"
3. Klikni na "Telefóny"  
4. Klikni na "iPhone"
5. Klikni na "Pridať do košíka"
6. Klikni na "Košík"
7. Klikni na "Objednať"
```

### Kde Uložiť Test Cases

```bash
# Všetky test cases daj do tejto zložky:
test_cases/
├── login_test.txt          # Test prihlásenia
├── objednavka_test.txt     # Test objednávky  
├── registracia_test.txt    # Test registrácie
└── nakup_test.txt          # Test nákupu
```

### Ako Spustiť Všetky Testy Naraz

```bash
# Spusti všetky test cases v zložke
python -m src.main test_cases/

# Sledovač stále beží v pozadí a aktualizuje všetky YAML súbory
```

### Výsledné Súbory

Po spustení budeš mať:

```bash
flows/
├── login_test.yaml         # Maestro inštrukcie pre prihlásenie
├── objednavka_test.yaml    # Maestro inštrukcie pre objednávku
├── registracia_test.yaml   # Maestro inštrukcie pre registráciu
└── nakup_test.yaml         # Maestro inštrukcie pre nákup

screenshots/objednavka/
├── step_01.png            # Obrázky z testov
├── step_02.png
└── FINISHED/              # Analyzované obrázky
    ├── step_01_analyzed.png
    └── step_01_analyzed_summary.txt
```

## 🆘 Ak Niečo Nefunguje

**Robot nenašiel tlačidlo:**
```text
❌ TODO → Not found: 'Neexistujúce tlačidlo'
```
- Skontroluj názov tlačidla na obrázku
- Možno má iný text ako si myslíš

**Sledovač nevidí nové obrázky:**
```bash
# Reštartuj sledovača
Ctrl+C  # Zastav starý sledovač
./start_watcher.sh  # Spusti nový
```

**Test sa zasekol:**
```bash
# Zastav test
Ctrl+C

# Skontroluj YAML súbor
cat flows/moj_test.yaml

# Spusti znovu
maestro test flows/moj_test.yaml
```

## 🎯 Zhrnutie pre Malé Dieťa

1. **Napíš zoznam** čo chceš robiť (test_cases/moj_test.txt)
2. **Spusti robota** aby sa naučil (python -m src.main test_cases/moj_test.txt)  
3. **Spusti sledovača** (./start_watcher.sh)
4. **Spusti test** (maestro test flows/moj_test.yaml)
5. **Sleduj kúzlo** - robot klikaním presne tam kde má! 🎉

Robot je teraz naučený a môže opakovať tvoj test kedykoľvek chceš! Je to ako keby si mal pomocníka, ktorý nikdy nezabudne čo má robiť a nikdy sa neunudí. 🤖✨