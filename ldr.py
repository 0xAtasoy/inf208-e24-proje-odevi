import os
import time
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

# LDR sensörü için pin numarası (BOARD modunda)
LDR_PIN = 5  # GPIO3'ün BOARD modundaki karşılığı

def get_lux():
    reading = 0
    GPIO.setup(LDR_PIN, GPIO.OUT)
    GPIO.output(LDR_PIN, GPIO.LOW)
    time.sleep(0.1)

    GPIO.setup(LDR_PIN, GPIO.IN)
    while (GPIO.input(LDR_PIN) == GPIO.LOW):
        reading += 1
    return reading

def cleanup():
    GPIO.cleanup()


