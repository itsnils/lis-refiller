import threading
import config
import time
from contextlib import suppress

import pump
import blupio
from weighingring import WeighingRing
from ringcontrolloop import RingControlLoop
from buttonhandler import Buttons
from ledcontrolloop import LedControlLoop
from watchdog import WatchDog


def set_led(color, mode):
    with Leds.QLock:
        if color == "Green":
            Leds.Q.append(("Head", "Green", mode))
            Leds.Q.append(("Head", "Red", "Off"))
        elif color == "Red":
            Leds.Q.append(("Head", "Green", "Off"))
            Leds.Q.append(("Head", "Red", mode))
        else:
            Leds.Q.append(("Head", color, mode))


if __name__ == '__main__':

    #load or create config.json
    Config = config.load()

    #create LedQ list and LedControlLoop, initialize and start
    Leds = LedControlLoop(Config, interval=0.2)

    #create Watchdog and start
    Watchdog = WatchDog(Leds)
    Leds.Watchdog = Watchdog

    Watchdog.start()
    Leds.start()

    #create ButtonQ dict and Buttons object and initialize
    Buttons = Buttons()

    #create Pump object and initialize
    Pump = pump.Pump(51200)

    #create weighing ring objects and initialize
    Rings = [WeighingRing(side="Left", config=Config), WeighingRing(side="Right", config=Config)]
    #create weighing ring control loop thread objects and start
    threads = []
    for Ring in Rings:
        thread = RingControlLoop(Ring, Pump, Leds, Buttons, interval=0.5)
        thread.Watchdog = Watchdog
        thread.setName("RingControlLoop" + str(Ring.Side))
        threads.append(thread)
        thread.start()

    #controller control loop
    while True:
        time.sleep(1)
        Watchdog.calm("Head", 10)
        if not Buttons.QLock.locked():
            with Buttons.QLock:
                if len(Buttons.Q):
                    print("Button: ", Buttons.Q)
                    Buttons.Q.clear()
        if not Pump.arrived():
            set_led("Green", "Slow")
            if not Pump.Lock.locked():
                Pump.Lock.acquire()
        else:
            set_led("Green", "Alive")
            try:
                Pump.Lock.release()
            except RuntimeError:
                pass







