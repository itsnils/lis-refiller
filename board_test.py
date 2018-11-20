#!/usr/bin/env python3

import tmc5130
import pigpio
from itertools import cycle
import time


def motor_test(duration=10):
    m = tmc5130.Motor()
    for i in range(duration//2):
        while not m.arrived():
            time.sleep(0.01)
        m.moveby(relpos=25000, speed=25000)
        while not m.arrived():
            time.sleep(0.01)
        m.moveby(relpos=-25000, speed=25000)
    return "Motor test done"


def gpio_test(duration=10, gpio_list=(5, 6, 13, 19, 16, 20, 26, 12)):
    pi = pigpio.pi()
    gpios = cycle(gpio_list)
    for i in range(duration*2):
        gpio = next(gpios)
        pi.write(gpio, 1)
        time.sleep(0.5)
        pi.write(gpio, 0)
    return "GPIO test done"


if __name__ == '__main__':

    print(motor_test(duration=10))
    print(gpio_test(duration=10, gpio_list=(5, 6, 13, 19, 16, 20, 26, 12)))

