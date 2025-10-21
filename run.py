# ================================================
# Aby zainstalowac wymagane pakiety:
# To install dependencies:
#     pip install -r requirements.txt
# ================================================

#!/usr/bin/env python3
\"\"\" 
PL: DTMF->SSTV server dla Raspberry Pi + MT8870 z rozroznianiem krotkiego i dlugiego tonu.
EN: DTMF->SSTV server for Raspberry Pi + MT8870 with short vs long press handling.

\"\"\"

# PL: Importy
# EN: Imports
import os
import time
import subprocess
from datetime import datetime

# PL: Zaleznosci: pip install pillow pysstv RPi.GPIO fswebcam
# EN: Dependencies: pip install pillow pysstv RPi.GPIO fswebcam
try:
    from PIL import Image
    from pysstv.color import Robot36, MartinM1, ScottieS1, ScottieS2, ScottieDX, PD120, PD240
except Exception as e:
    print(\"Brak bibliotek pysstv/Pillow - zainstaluj pip install pysstv Pillow\" )
    raise

import RPi.GPIO as GPIO

# PL: GPIO mapowanie - dostosuj do swojego podlaczenia
# EN: GPIO mapping - adjust to your wiring
PIN_D0 = 5    # PL: D0 -> GPIO5  EN: D0 -> GPIO5
PIN_D1 = 6    # D1 -> GPIO6
PIN_D2 = 13   # D2 -> GPIO13
PIN_D3 = 19   # D3 -> GPIO19
PIN_STROBE = 26  # Strobe/Data ready -> GPIO26

PTT_PIN = 21  # PL: GPIO do sterowania PTT (poprzez tranzystor) EN: GPIO for PTT control

# PL: Parametry rozrozniania krotkiego/dlugiego nacisniecia (sekundy)
# EN: Parameters for distinguishing short/long press (seconds)
LONG_PRESS_THRESHOLD = 1.5   # >= 1.5s traktujemy jako dlugie nacisniecie
DEBOUNCE_MS = 50

# PL: Setup GPIO
# EN: Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup([PIN_D0, PIN_D1, PIN_D2, PIN_D3, PIN_STROBE], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(PTT_PIN, GPIO.OUT)
GPIO.output(PTT_PIN, GPIO.LOW)  # PTT inactive (assuming LOW = unkey)

# PL: Mapa DTMF (BCD) do znakow (0..15) - sprawdz datasheet Twojego modulu!
# EN: DTMF (BCD) map to keys
DTMF_BCD_TO_KEY = {
    0x0: 'D',
    0x1: '1',
    0x2: '2',
    0x3: '3',
    0x4: '4',
    0x5: '5',
    0x6: '6',
    0x7: '7',
    0x8: '8',
    0x9: '9',
    0xA: '0',
    0xB: '*',
    0xC: '#',
    0xD: 'A',
    0xE: 'B',
    0xF: 'C'
}

# PL: Mapa klawiszy do trybow SSTV (krotkie nacisniecie)
# EN: Map keys to SSTV modes (short press)
KEY_TO_SSTV = {
    '1': 'ROBOT36',
    '2': 'MARTIN_M1',
    '3': 'SCOTTIE_S1',
    '4': 'SCOTTIE_S2',
    '5': 'SCOTTIE_DX',
    '6': 'PD120',
    '7': 'PD240',
}

# PL: Mapa klawiszy do komend dlugiego nacisniecia (np. obraz kontrolny)
# EN: Map keys to long-press commands (e.g., control image)
KEY_TO_LONG_CMD = {
    # PRZYKLAD: dlugie nacisniecie '1' -> wyslij obraz kontrolny 'testcard1'
    '1': 'TESTCARD1',
    '2': 'TESTCARD2',
    '3': 'STATUS_IMAGE',
}

# PL: Funkcja odczytu 4-bitowego kodu z GPIO
# EN: Read 4-bit code from GPIO
def read_bcd():
    b0 = GPIO.input(PIN_D0)
    b1 = GPIO.input(PIN_D1)
    b2 = GPIO.input(PIN_D2)
    b3 = GPIO.input(PIN_D3)
    val = (b3 << 3) | (b2 << 2) | (b1 << 1) | b0
    return val

# PL: Funkcja capture zdjecia z USB webcam (fswebcam) - dostosuj parametry
# EN: Capture photo from USB webcam (fswebcam) - adjust parameters
def capture_image_usb(output_path):
    timestamp = datetime.utcnow().strftime(\"%Y%m%d_%H%M%S\")
    cmd = [\"fswebcam\", \"-r\", \"1280x720\", \"--no-banner\", output_path]
    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(\"Blad robienia zdjecia (fswebcam):\", e)
        return False

# PL: Funkcja generujaca plik WAV dla trybu SSTV (uzywa pysstv)
# EN: Generate WAV file for given SSTV mode using pysstv
def generate_sstv_wav(image_path, wav_out, mode_key):
    mode_key = mode_key.upper()
    img = Image.open(image_path).convert('RGB')
    # Resize if needed
    img = img.resize((640, 496))
    if mode_key == \"ROBOT36\" or mode_key == \"TESTCARD1\" or mode_key == \"TESTCARD2\" or mode_key==\"STATUS_IMAGE\":
        s = Robot36(img)
    elif mode_key == \"MARTIN_M1\":
        s = MartinM1(img)
    elif mode_key == \"SCOTTIE_S1\":
        s = ScottieS1(img)
    elif mode_key == \"SCOTTIE_S2\":
        s = ScottieS2(img)
    elif mode_key == \"SCOTTIE_DX\":
        s = ScottieDX(img)
    elif mode_key == \"PD120\":
        s = PD120(img)
    elif mode_key == \"PD240\":
        s = PD240(img)
    else:
        s = Robot36(img)
    s.save_wav(wav_out)
    return True

# PL: PTT
# EN: PTT
def ptt_key():
    GPIO.output(PTT_PIN, GPIO.HIGH)
    time.sleep(0.12)

def ptt_unkey():
    GPIO.output(PTT_PIN, GPIO.LOW)
    time.sleep(0.12)

# PL: Odtwarzanie WAV
# EN: Play WAV via aplay
def play_wav(wav_path):
    cmd = [\"aplay\", wav_path]
    subprocess.run(cmd)

# PL: Funkcja wyslania 'obraz kontrolny' - moze wysylac gotowy plik lub zrobic zdjecie i oznaczyc jako kontrolny.
# EN: Send 'control image' - can send a prepared file or capture image and mark it as control.
def send_control_image(cmd_key):
    # PL: Przyklad: mozemy miec kilka testcardow w katalogu /opt/dtmf_sstv/
    # EN: Example: have testcards in /opt/dtmf_sstv/
    base_dir = \"/opt/dtmf_sstv/"
    if cmd_key == 'TESTCARD1':
        img = os.path.join(base_dir, 'testcard1.png')
    elif cmd_key == 'TESTCARD2':
        img = os.path.join(base_dir, 'testcard2.png')
    elif cmd_key == 'STATUS_IMAGE':
        # PL: Przyklad generowania statusu: zrob zdjecie i naklada napis
        # EN: Example status: capture image and overlay text
        tmp = \"/tmp/status_capture.jpg\"
        if capture_image_usb(tmp):
            # prosta nakladka tekstu
            try:
                im = Image.open(tmp).convert('RGB')
                draw = ImageDraw.Draw(im)
                draw.text((10,10), \"STATUS: OK\", fill=(255,0,0))
                im.save('/tmp/status_image.jpg')
                img = '/tmp/status_image.jpg'
            except Exception as e:
                print('Blad przy przygotowaniu status image', e)
                img = tmp
        else:
            print('Nie mozna zrobic zdjecia statusowego')
            return
    else:
        print('Nieznana komenda kontrolna:', cmd_key)
        return

    wav = img.replace('.jpg', '_control.wav')
    generate_sstv_wav(img, wav, 'ROBOT36')
    ptt_key()
    play_wav(wav)
    ptt_unkey()
    # opcjonalnie usun plik wav
    try:
        os.remove(wav)
    except Exception:
        pass

# PL: Glowna petla z wykrywaniem krotkiego/dlugiego nacisniecia
# EN: Main loop with short/long press detection
try:
    print(\"DTMF->SSTV server (long/short press) started\")
    while True:
        # Czekaj na Strobe
        if GPIO.input(PIN_STROBE):
            start = time.time()
            # debouncing: poczekaj male opoznienie
            time.sleep(DEBOUNCE_MS / 1000.0)
            # czekaj az Strobe spadnie aby zmierzyc dlugosc
            while GPIO.input(PIN_STROBE):
                time.sleep(0.01)
            duration = time.time() - start
            # odczytaj kod BCD
            code = read_bcd()
            key = DTMF_BCD_TO_KEY.get(code, None)
            print(\"DTMF code:\", hex(code), \"key:\", key, \"dur:\", duration)
            if not key:
                continue
            # sprawdz dlugosc nacisniecia
            if duration >= LONG_PRESS_THRESHOLD:
                # DLUGIE NACISNIECIE - wykonaj komende kontrolna jesli przypisana
                long_cmd = KEY_TO_LONG_CMD.get(key)
                if long_cmd:
                    print('Wykryto dlugie nacisniecie. Wykonuje komende:', long_cmd)
                    send_control_image(long_cmd)
                else:
                    print('Dlugie nacisniecie, brak przypisanej komendy dla klawisza', key)
            else:
                # KROTKIE NACISNIECIE - normalny tryb SSTV
                sstv_mode = KEY_TO_SSTV.get(key)
                if sstv_mode:
                    print('Krotkie nacisniecie. Tryb SSTV:', sstv_mode)
                    img_path = f\"/tmp/sstv_{int(time.time())}.jpg\"
                    if capture_image_usb(img_path):
                        wav_path = img_path.replace('.jpg', '.wav')
                        generate_sstv_wav(img_path, wav_path, sstv_mode)
                        ptt_key()
                        play_wav(wav_path)
                        ptt_unkey()
                        try:
                            os.remove(img_path)
                            os.remove(wav_path)
                        except Exception:
                            pass
                else:
                    print('Klawisz nie przypisany do trybu SSTV:', key)
        time.sleep(0.01)

except KeyboardInterrupt:
    print('Koniec')
finally:
    GPIO.cleanup()
