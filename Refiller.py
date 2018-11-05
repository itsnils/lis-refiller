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
    LedQ = []
    LedQLock = threading.Lock()
    Leds = LedControlLoop(Config, LedQ, LedQLock, interval=0.2)
    Leds.start()

    #create ButtonQ dict and Buttons object and initialize
    ButtonQ = {}
    ButtonQLock = threading.Lock()
    Buttons(ButtonQ, ButtonQLock)

    #create Pump object and initialize
    Pump = pump.Pump(51200)

    #create weighing ring objects and initialize
    Rings = [WeighingRing(bus=0, side="Left", config=Config), WeighingRing(bus=1, side="Right", config=Config)]
    #create weighing ring control loop thread objects and start
    threads = []
    for Ring in Rings:
        thread = RingControlLoop(Ring, Pump, LedQ, LedQLock, ButtonQ, ButtonQLock, interval=0.5)
        thread.setName("RingControlLoop" + str(Ring.Side))
        threads.append(thread)
        thread.start()

    #controller control loop
    while True:
        time.sleep(2)
        with ButtonQLock:
            if len(ButtonQ):
                print("Button: ", ButtonQ)
                ButtonQ.clear()







