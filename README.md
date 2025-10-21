# DTMF‑SSTV Station / Server

Projekt: serwer DTMF → obraz SSTV  
Cel: po odebraniu tonu DTMF drogą radiową moduł zwraca bieżące zdjęcie zakodowane w SSTV  
Wersja: 1.0  
Autor: SQ2MTG

---

## Opis projektu / What it does

Ten projekt uruchamia serwis, który nasłuchuje sygnałów DTMF (moduł MT8870), a następnie:

- rozpoznaje klawisz (0–9, A–D, *, #) w formacie BCD,  
- rozróżnia **krótkie** i **długie** naciśnięcie,  
  - krótkie: wykonuje przejście standardowe — robi zdjęcie z kamery USB, koduje SSTV w wybranym trybie (zgodnie z mapowaniem klawisza) i nadaje przez radio (PTT + audio),  
  - długie: wykonuje **komendę kontrolną** (np. wysyła obraz kontrolny / statusowy), np. testcard albo zdjęcie z nałożonym tekstem statusowym.  
- obsługuje kamerę USB (domyślnie używa `fswebcam`)  
- steruje PTT (przez GPIO + tranzystor)  
- generuje plik WAV zawierający SSTV i odtwarza go do wyjścia audio  

Dzięki temu można, np. przez DTMF w radiu, poprosić urządzenie → ono wysyła aktualne zdjęcie (w SSTV) — podobnie do opisanego projektu we Wrocławiu.

---

## Wymagania i zależności / Requirements

### Python i pakiety pip

Projekt używa Pythona 3.x. Wszystkie pakiety Pythonowe są w `requirements.txt`.

Zawiera m.in.:
- `flask`  
- `gpiozero`  
- `pillow`  
- `opencv-python` (opcjonalnie, jeśli chcesz używać `cv2`)  
- `sounddevice` / `pyaudio` (opcjonalnie)  
- `pyserial`  
- `requests`  

Instalacja:
```bash
pip install -r requirements.txt
```

### Pakiety systemowe (Debian / Raspberry Pi OS)
```bash
sudo apt update
sudo apt install fswebcam sox python3-gpiozero python3-opencv python3-pil python3-flask
# opcjonalnie:
sudo apt install python3-pyaudio python3-numpy python3-requests
```

---

## Instalacja i uruchomienie / How to install and run

1. Skopiuj / sklonuj repo:  
   ```bash
   git clone <adres_repo>  
   cd <folder>
   ```

2. Zainstaluj zależności Python:
   ```bash
   pip install -r requirements.txt
   ```

3. Podłącz sprzęt według schematu (GPIO, MT8870, konwersja poziomów, PTT, audio, kamera USB).

4. Uruchom skrypt:
   ```bash
   sudo python3 dtmf_sstv_server_with_longpress.py
   ```

5. Po uruchomieniu skrypt nasłuchuje sygnałów DTMF i obsługuje komendy (krótkie / długie naciśnięcie).

---

## Mapowania i konfiguracja / Key mappings & config

W skrypcie (`dtmf_sstv_server_with_longpress.py`) zdefiniowane są:

- `DTMF_BCD_TO_KEY` — mapowanie kodu BCD (0x0–0xF) na znak DTMF.  
- `KEY_TO_SSTV` — mapowanie klawiszy na tryby SSTV.  
- `KEY_TO_LONG_CMD` — mapowanie długich naciśnięć na komendy kontrolne.  
- `LONG_PRESS_THRESHOLD` — czas graniczny między krótkim i długim naciśnięciem (domyślnie 1.5 s).  

---

## Schemat połączeń / Wiring & schematic

Schemat połączeń (GPIO, MT8870, konwersja poziomów, PTT, audio, kamera USB) jest dostępny w repo:

- `dtmf_sstv_schematic.svg`  
- `dtmf_sstv_schematic.png`

Zalecenia:

- MT8870 działa zwykle na 5 V — linie wyjściowe D0..D3 (5 V) **nie można** podłączać bezpośrednio do GPIO 3.3 V — użyj dzielników rezystorowych lub konwertera poziomów.  
- GND MT8870, Raspberry Pi i radio **muszą** być wspólne.  
- Sterowanie PTT przez tranzystor / optoizolator.  
- Audio wyjście z USB soundcard → przez izolator audio → wejście mikrofonowe radia.  

---

## Przykładowe komendy DTMF / Use cases

| Sytuacja | DTMF (krótkie) | DTMF (długie) | Co się dzieje |
|-----------|----------------|----------------|----------------|
| Zdjęcie aktualne | `1` | — | kamera robi zdjęcie i nadaje SSTV |
| Obraz kontrolny | — | `1` (przytrzymane) | wysyła testcard/status image |

---

## Testowanie i debugowanie / Testing & debugging

- Testuj bez radia (dummy load).  
- Sprawdź poziomy audio, działanie `fswebcam`, `aplay`.  
- Monitoruj wyjścia w terminalu.  

---

## Licencja / License

MIT License

---

## Podziękowania / Acknowledgements

- Inspiracja projektem Wrocław: DTMF → SSTV  
- pySSTV — biblioteka do generacji SSTV  
- fswebcam, sox — narzędzia pomocnicze  
- Społeczność radioamatorska  
