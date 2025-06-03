import RPi.GPIO as GPIO
import time

# GPIO pin numaraları
MOTOR_PIN1 = 18  # IN1
MOTOR_PIN2 = 23  # IN2
ENABLE_PIN = 24  # ENA

# GPIO ayarları
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(MOTOR_PIN1, GPIO.OUT)
GPIO.setup(MOTOR_PIN2, GPIO.OUT)
GPIO.setup(ENABLE_PIN, GPIO.OUT)

# PWM nesnesi oluştur (frekans = 100Hz)
pwm = GPIO.PWM(ENABLE_PIN, 100)
pwm.start(0)  # Başlangıçta motor kapalı

def basla():
    """DC motoru başlat."""
    try:
        # Motoru ileri yönde döndür
        GPIO.output(MOTOR_PIN1, GPIO.HIGH)
        GPIO.output(MOTOR_PIN2, GPIO.LOW)
        pwm.ChangeDutyCycle(100)  # Tam hız
        return True
    except Exception as e:
        print(f"Motor başlatma hatası: {e}")
        return False

def durdur():
    """DC motoru durdur."""
    try:
        # Motoru durdur
        GPIO.output(MOTOR_PIN1, GPIO.LOW)
        GPIO.output(MOTOR_PIN2, GPIO.LOW)
        pwm.ChangeDutyCycle(0)
        return False
    except Exception as e:
        print(f"Motor durdurma hatası: {e}")
        return True

def durum_kontrol():
    """DC motorun durumunu kontrol et."""
    try:
        # ENABLE_PIN'in durumunu kontrol et
        return GPIO.input(ENABLE_PIN) == GPIO.HIGH
    except Exception as e:
        print(f"Motor durum kontrolü hatası: {e}")
        return False

def cleanup():
    """GPIO pinlerini temizle."""
    try:
        pwm.stop()
        GPIO.cleanup()
    except Exception as e:
        print(f"GPIO temizleme hatası: {e}")

if __name__ == "__main__":
    try:
        print("DC Motor Testi")
        print("Motor başlatılıyor...")
        basla()
        time.sleep(2)
        print("Motor durduruluyor...")
        durdur()
        cleanup()
    except KeyboardInterrupt:
        print("\nProgram sonlandırıldı.")
        cleanup() 