# Fix pentru Python 3.14 pe Windows

## Problema
Python 3.14 este prea nou și numpy nu are încă wheel-uri pre-compilate.

## Soluții (alege una):

### ✅ Soluția 1: Instalează numpy pre-compilat (RECOMANDAT)
```powershell
# Instalează numpy separat, forțând wheel pre-compilat
pip install numpy==2.0.2 --only-binary numpy

# Apoi instalează restul
pip install -r receiver/requirements.txt
```

### ✅ Soluția 2: Folosește Python 3.11 sau 3.13 (CEL MAI SIMPLU)
1. Descarcă Python 3.13 de pe: https://www.python.org/downloads/
2. Instalează și asigură-te că bifezi "Add to PATH"
3. Deschide un nou PowerShell/CMD
4. Rulează: `pip install -r receiver/requirements.txt`

### ✅ Soluția 3: Instalează Visual Studio Build Tools
Doar dacă vrei să rămâi cu Python 3.14:

1. Descarcă: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Instalează "Desktop development with C++"
3. Restart computer
4. Rulează: `pip install -r receiver/requirements.txt`

## Quick Fix pentru a continua ACUM:

```powershell
# Opțiunea rapidă - instalează tot pe rând
pip install aiortc
pip install aiohttp
pip install opencv-python
pip install av
pip install numpy --only-binary numpy
pip install Pillow
```

## Verificare instalare:
```powershell
python -c "import aiortc, cv2, av, numpy, PIL; print('✅ All dependencies OK!')"
```

## Test rapid:
```powershell
# Testează că totul funcționează
python receiver/signaling_server.py
# Ar trebui să pornească fără erori
```

## Dacă totul eșuează:
Cel mai sigur: **folosește Python 3.11 sau 3.13** - sunt versiunile stabile și testate.
