import pigpio
import json
import config
import time

Config = config.load()

pi = pigpio.pi()
gpio = Config["Head"]["LedGpio"]["Blue"]

while True:
    time.sleep(0.5)
    pi.write(gpio, 1)
    time.sleep(0.5)
    pi.write(gpio, 0)