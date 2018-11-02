import threading
import config
import time
from contextlib import suppress

import pump
from weighingring import WeighingRing
from ringcontrolloop import RingControlLoop
from buttonhandler import Buttons

if __name__ == '__main__':

    LedGPIO = {"Red": (6, 19),
               "Green": (5, 13),
               }
    LedSeq = {"Off": ("Off",),
              "SteadyRed": ("Red",),
               "FastRed": ("Red","Off",),
               "SlowRed": ("Red","Red","Red","Off","Off","Off","Off",),
               "FastGreen": ("Green","Off",),
               "SlowGreen": ("Green","Green","Off","Off","Off","Off",),
               "SteadyGreen": ("Green",)
               }
    LED = [None, None]
    LedSeqIter = [None, None]

    #load or create config.json
    Config = config.load()

    #create ButtonQ list and Buttons object and initialize
    ButtonQ = {}
    ButtonQLock = threading.Lock()
    Buttons(ButtonQ, ButtonQLock)

    #create Pump object and initialize
    Pump = pump.Pump(51200)

    #create weighing ring objects and initialize
    Rings = [WeighingRing(bus=0, config=Config["Left"])] # fixme, WeighingRing(bus=1, config=Config["Right"])]
    #create weighing ring control loop thread objects and start
    threads = []
    for Ring in Rings:
        thread = RingControlLoop(Ring, Pump, ButtonQ)
        thread.setName("RingControlLoop" + str(Ring.I2Cbus))
        threads.append(thread)
        thread.start()

    #controller control loop
    while True:
        time.sleep(2)
        with ButtonQLock:
            if len(ButtonQ):
                print("Button: ", ButtonQ)
                ButtonQ.clear()





"""
    for L in LedSeq:
        # print("L:", L)
        for Ring in Rings:
            Ring.LED = L

        # print("range(len(Rings)", range(len(Rings)))
        for x in range(20):
            for i in range(len(Rings)):
                # print("i:", i)
                if LED[i] != Rings[i].LED:
                    LED[i] = Rings[i].LED
                    LedSeqIter[i] = iter(LedSeq[LED[i]])
                # print("i:", i, "  LED[i]: ", LED[i], "  LedSeq[LED[i]]: ", LedSeq[LED[i]])
                for n in LedGPIO:
                    Pump.pi.write(LedGPIO[n][i], 0)
                try:
                    # print("next")
                    col = next(LedSeqIter[i])
                except StopIteration:
                    # print("renew")
                    LedSeqIter[i] = iter(LedSeq[LED[i]])
                    col = next(LedSeqIter[i])
                print("col:", col)
                if col in LedGPIO:
                    Pump.pi.write(LedGPIO[col][i], 1)
                    # print(LedGPIO[col][i], 1)
            time.sleep(0.25)
            
"""






