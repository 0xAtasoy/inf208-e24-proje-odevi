import RPi.GPIO as GPIO
import time
import threading

SERVO_PIN = 18

# Global durum değişkenleri
running = False
servo_thread = None
pwm = None

def set_angle(angle):
    duty = 2 + (angle / 18)
    GPIO.output(SERVO_PIN, True)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    GPIO.output(SERVO_PIN, False)
    pwm.ChangeDutyCycle(0)

def servo_loop():
    global running
    while running:
        set_angle(0)
        time.sleep(1)
        set_angle(180)
        time.sleep(1)

def basla():
    global running, servo_thread, pwm

    if not running:
        print("Servo dönmeye başladı...")

        # Her başlatmada GPIO ayarları yapılır
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SERVO_PIN, GPIO.OUT)
        pwm = GPIO.PWM(SERVO_PIN, 50)  # 50Hz PWM
        pwm.start(0)

        running = True
        servo_thread = threading.Thread(target=servo_loop)
        servo_thread.start()

def durdur():
    global running, pwm
    if running:
        print("Servo durduruluyor...")
        running = False
        if servo_thread:
            servo_thread.join()
        pwm.stop()
        GPIO.cleanup()

def durum_kontrol():
    """Servo motor şu anda çalışıyor mu?"""
    return running
