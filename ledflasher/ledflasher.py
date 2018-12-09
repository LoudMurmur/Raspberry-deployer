#!/usr/bin/env python
# --*-- encoding: utf-8 --*--

import RPi.GPIO as GPIO
import time

led1 = 16
led2 = 20
led3 = 21
time_betwen_flashes = 0.1

GPIO.setmode(GPIO.BCM)
GPIO.setup(led1, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(led2, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(led3, GPIO.OUT, initial=GPIO.LOW)

while True:
	GPIO.output(led1, GPIO.HIGH)
	time.sleep(time_betwen_flashes)
	GPIO.output(led1, GPIO.LOW)
	GPIO.output(led2, GPIO.HIGH)
	time.sleep(time_betwen_flashes)
	GPIO.output(led2, GPIO.LOW)
	GPIO.output(led3, GPIO.HIGH)
	time.sleep(time_betwen_flashes)
	GPIO.output(led3, GPIO.LOW)
