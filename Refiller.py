import threading
import json
import time
from contextlib import suppress

import pump
import weighingring
import ringcontrolloop

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

#create Pump object and initialize
Pump = pump.Pump(51200)


#create weighing ring objects and initialize
Rings = [weighingring.WeighingRing(bus=0),
        weighingring.WeighingRing(bus=1)
        ]

#create weighing ring control loop thread objects and start
threads = []
for Ring in Rings:
    thread = ringcontrolloop.RingControlLoop(Ring, Pump)
    thread.setName("RingControlLoop" + str(Ring.I2Cbus))
    threads.append(thread)
    # thread.start() fixme

#controller control loop
while True:

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






