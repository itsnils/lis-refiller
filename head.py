"""
Left channel:
    I2C bus:    0
    Green LED:  GPIO 5
    Red LED:    GPIO 6
    Button:     GPIO 21
    Pump dir:   -1

Right channel:
    I2C bus:    1
    Green LED:  GPIO 13
    Red LED:    GPIO 19
    Button:     GPIO 17
    Pump dir:   +1

Common:
    Green LED:  GPIO 16
    Red LED:    GPIO 20
    Blue LED:   GPIO 26
    Buzzer:     GPIO 12
    (WiFiBtn:    GPIO 18)

"""

import time

import pigpio

class ControllerChannels:

    pass


class Head:

    LedGPIO = {"Red": (6, 19),
               "Green": (5, 13),
               }
    LedSeq = {"Off": ("Off",),
              "SteadyRed": ("Red",),
              "FastRed": ("Red", "Off",),
              "SlowRed": ("Red", "Red", "Red", "Off", "Off", "Off", "Off",),
              "FastGreen": ("Green", "Off",),
              "SlowGreen": ("Green", "Green", "Off", "Off", "Off", "Off",),
              "SteadyGreen": ("Green",)
              }


    def __init__(self):
        self.pi = pigpio.pi

        self.pi.set_glitch_filter(21, 100000)
        self.pi.set_glitch_filter(17, 100000)
        cbButton = [self.pi.callback(21, pigpio.RISING_EDGE, self.button_handler),
                    self.pi.callback(17, pigpio.RISING_EDGE, self.button_handler)
                    ]


    def button_handler(self, gpio, level, tick):
        pass

