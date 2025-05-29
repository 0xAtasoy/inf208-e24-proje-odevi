import os
import time
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


def get_lux():
    reading = 0
    GPIO.setup(3, GPIO.OUT)
    GPIO.output(3, GPIO.LOW)
    time.sleep(0.1)

    GPIO.setup(3, GPIO.IN)
    while (GPIO.input(3) == GPIO.LOW):
        reading += 1
    return reading


