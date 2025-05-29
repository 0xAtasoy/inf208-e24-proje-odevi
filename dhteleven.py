import RPi.GPIO as GPIO
import dht11
import time

# GPIO ayarları sadece 1 kez yapılsın
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# DHT11 sensör nesnesi (PIN 14 kullanılıyor)
instance = dht11.DHT11(pin=14)

# Önceki geçerli değerler (başlangıçta -1)
prev_temperature = 23.5
prev_humidity = 55

def get_temperature_and_humidity():
    """
    DHT11 sensöründen sıcaklık ve nem ölçümünü döndürür.
    Eğer ölçüm geçersizse bir önceki geçerli değeri döndürür.
    """
    global prev_temperature, prev_humidity

    try:
        result = instance.read()
        time.sleep(1.1)  # sensörün veri yenilemesi için yeterli süre

        if result.is_valid():
            prev_temperature = result.temperature
            prev_humidity = result.humidity
            return prev_temperature, prev_humidity
        else:
            return prev_temperature, prev_humidity

    except Exception as e:
        print(f"DHT11 okuma hatası: {e}")
        return prev_temperature, prev_humidity

def cleanup():
    GPIO.cleanup()
