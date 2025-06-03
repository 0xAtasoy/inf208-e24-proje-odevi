import RPi.GPIO as GPIO
from time import sleep
import atexit

# GPIO pin numaraları
MOTOR_A = 16  # IN1
MOTOR_B = 18  # IN2
MOTOR_ENABLE = 22  # ENA

# GPIO ayarları
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(MOTOR_A, GPIO.OUT)
GPIO.setup(MOTOR_B, GPIO.OUT)
GPIO.setup(MOTOR_ENABLE, GPIO.OUT)

# Başlangıçta motoru durdur
GPIO.output(MOTOR_ENABLE, GPIO.LOW)
GPIO.output(MOTOR_A, GPIO.LOW)
GPIO.output(MOTOR_B, GPIO.LOW)

# Motor durumu
motor_running = False

def basla():
    """Motoru ileri yönde çalıştır."""
    global motor_running
    try:
        # Önce motoru durdur
        durdur()
        sleep(0.1)  # Kısa bir bekleme
        
        # İleri hareket için pin durumları
        GPIO.output(MOTOR_A, GPIO.HIGH)
        GPIO.output(MOTOR_B, GPIO.LOW)
        GPIO.output(MOTOR_ENABLE, GPIO.HIGH)
        motor_running = True
        return True
    except Exception as e:
        print(f"Motor başlatma hatası: {e}")
        return False

def durdur():
    """Motoru durdur."""
    global motor_running
    try:
        # Motoru durdurmak için tüm pinleri LOW yap
        GPIO.output(MOTOR_ENABLE, GPIO.LOW)
        GPIO.output(MOTOR_A, GPIO.LOW)
        GPIO.output(MOTOR_B, GPIO.LOW)
        motor_running = False
        return True
    except Exception as e:
        print(f"Motor durdurma hatası: {e}")
        return False

def durum_kontrol():
    """Motorun çalışma durumunu kontrol et."""
    return motor_running

def temizle():
    """GPIO pinlerini temizle."""
    try:
        # Önce motoru durdur
        durdur()
        sleep(0.1)  # Kısa bir bekleme
        GPIO.cleanup()
    except Exception as e:
        print(f"GPIO temizleme hatası: {e}")

# Program sonlandığında otomatik temizleme
atexit.register(temizle)

# Test için
if __name__ == "__main__":
    try:
        print("DC Motor Testi")
        print("İleri hareket")
        basla()
        sleep(2)
        
        print("Motor durdu")
        durdur()
        sleep(1)
        
        print("Geri hareket")
        GPIO.output(MOTOR_A, GPIO.LOW)
        GPIO.output(MOTOR_B, GPIO.HIGH)
        GPIO.output(MOTOR_ENABLE, GPIO.HIGH)
        sleep(2)
        
        print("Motor durdu")
        durdur()
        
    except Exception as e:
        print(f"Test hatası: {e}")
    finally:
        temizle() 