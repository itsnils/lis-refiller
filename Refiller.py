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



if __name__ == '__main__':

    #load or create config.json
    Config = config.load()

    #create LedQ list and LedControlLoop, initialize and start
    Leds = LedControlLoop(Config, interval=0.2)
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
        thread.setName("RingControlLoop" + str(Ring.Side))
        threads.append(thread)
        thread.start()

    #controller control loop
    while True:
        time.sleep(2)
        with Buttons.QLock:
            if len(Buttons.Q):
                print("Button: ", Buttons.Q)
                Buttons.Q.clear()







