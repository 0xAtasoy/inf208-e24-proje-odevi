import time
import RPi.GPIO as GPIO

GPIO.setwarnings(False)

LDR_PIN = 5
GPIO_MODE_SET = False

# Senin ölçtüğün değerlere göre kalibrasyon
MIN_RAW = 5       # Çok aydınlıkta ölçülen minimum değer
MAX_RAW = 1000    # Tam karanlıkta ölçülen maksimum değer

def gpio_init():
    global GPIO_MODE_SET
    if not GPIO_MODE_SET:
        GPIO.setmode(GPIO.BOARD)
        GPIO_MODE_SET = True

def rc_time(pin):
    reading = 0

    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
    time.sleep(0.1)

    GPIO.setup(pin, GPIO.IN)
    while GPIO.input(pin) == GPIO.LOW:
        reading += 1
        if reading > MAX_RAW:
            break
    return reading

def get_lux():
    """
    Ölçülen RC zamanını normalize ederek 0–1000 arası göreli bir lux değeri döndürür.
    Işık arttıkça değer artar.
    """
    gpio_init()
    raw = rc_time(LDR_PIN)

    # Sınırlandır: ölçüm aralığı dışında kalan değerleri kes
    raw = max(MIN_RAW, min(raw, MAX_RAW))

    # Normalize et: (MAX_RAW - raw) doğrudan orantı sağlar
    lux = (MAX_RAW - raw) / (MAX_RAW - MIN_RAW) * 1000
    lux = float(int(lux))
    return lux

# Test döngüsü (doğrudan çalıştırıldığında)
if __name__ == "__main__":
    try:
        while True:
            lux = get_lux()
            print(f"Tahmini ışık şiddeti: {lux:.2f}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Program sonlandırıldı.")
    finally:
        GPIO.cleanup()
