import threading
import config
import time
from contextlib import suppress
from itertools import cycle

import pigpio
import blupio


class LedControlLoop(threading.Thread):
    LedSeq = {"Off": (0,),
              "Steady": (1,),
              "Fast": (1, 0,),
              "Slow": (1, 1, 1, 1, 1, 0, 0, 0, 0, 0,),
              }

    def __init__(self, config, interval=0.2):
        super().__init__()
        self.Config = config
        self.Q = []
        self.QLock = threading.Lock()
        self.Interval = interval
        self.pi = blupio.pi()
        self.Active = True
        self.Leds = {}
        for side in self.Config:
            if not side in self.Leds:
                self.Leds.update({side: {}})
            for color in self.Config[side]["LedGpio"]:
                if not color in self.Leds[side]:
                    self.Leds[side].update({color: ["Off", cycle([0,])]})
        print("Leds", self.Leds)
        self.clear()

    def run(self):
        while self.Active:
            self.NextInterval = time.process_time() + self.Interval
            with self.QLock:
                for side, color, mode in self.Q:
                    currentmode = self.Leds[side][color][0]
                    if not mode == currentmode:
                        seq = cycle(self.LedSeq[mode])
                        self.Leds[side].update({color:[mode, seq]})
                        # print("New LedSeq: ", side, color, mode, currentmode)
                self.Q.clear()
            for side in self.Leds:
                for color in self.Leds[side]:
                    self.pi.write(self.Config[side]["LedGpio"][color], next(self.Leds[side][color][1]))
                """
                for side in self.Leds:
                    for a in self.LedQ:
                        b = self.LedSeq[a[2]]
                        c = cycle(b)
                        self.Leds[a[0]].update({a[1]: c})
                    self.LedQ.clear()
                for side in self.Leds:
                    for color in self.Leds[side]:
                        self.pi.write(self.Config[side]["LedGpio"][color], next(self.Leds[side][color]))
                """
            with suppress(Exception):
                time.sleep(self.NextInterval - time.process_time())

    def stop(self):
        self.clear()

    def clear(self):
        for side in self.Leds:
            for color in self.Leds[side]:
                self.pi.set_mode(self.Config[side]["LedGpio"][color], pigpio.OUTPUT)
                self.pi.write(self.Config[side]["LedGpio"][color], 0)

    def test(self, n=1):
        for i in range(n):
            for side in self.Config:
                for color in self.Config[side]["LedGpio"]:
                    self.pi.write(self.Config[side]["LedGpio"][color], 1)
                    time.sleep(0.5)
                    self.pi.write(self.Config[side]["LedGpio"][color], 0)



if __name__ == "__main__":
    try:
        Lock = threading.Lock()
        Conf = config.load()
        with Lock:
            Queue = []
        L = LedControlLoop(Conf, Queue, Lock)
        L.test(5)
        time.sleep(2)

        L.start()
        time.sleep(2)

        with Lock:
            Queue.append(("Left", "Green", "Slow"))
            Queue.append(("Left", "Red", "Steady"))
            Queue.append(("Right", "Green", "Slow"))
            Queue.append(("Right", "Red", "Fast"))
        time.sleep(10)

        with Lock:
            Queue.append(("Left", "Green", "Off"))
            Queue.append(("Left", "Red", "Fast"))
            Queue.append(("Right", "Green", "Slow"))
            Queue.append(("Right", "Red", "Off"))



        while True:
            time.sleep(1)
    finally:
        L.stop()

