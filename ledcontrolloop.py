import threading
import config
import time
from contextlib import suppress
from itertools import cycle

import pigpio
import blupio
from refill_log import logger


class LedControlLoop(threading.Thread):

    def __init__(self, conf, watchdog=None, interval=0.2, stayalive=False):
        logger.debug("LedControlLoop.__init__()")
        super().__init__()
        self.Config = conf
        self.Watchdog = watchdog
        self.Q = []
        self.QLock = threading.Lock()
        self.Interval = interval
        self.StayAlive = stayalive
        self.pi = blupio.pi()
        self.Active = True
        self.LedSeq = self.Config["Head"]["LedSequence"]
        self.Leds = {}
        for side in self.Config:
            if side not in self.Leds:
                self.Leds.update({side: {}})
            for color in self.Config[side]["LedGpio"]:
                if color not in self.Leds[side]:
                    self.Leds[side].update({color: ["Off", cycle([0, ])]})
                if False: print("Leds", self.Leds)
        self.clear()
        logger.debug("LedControlLoop.__init__() done")

    def run(self):
        logger.debug("LedControlLoop.run()")
        self.Active = True
        while self.Active:
            try:
                self.NextInterval = time.process_time() + self.Interval
                self.Watchdog.calm("Leds", 10)
                with self.QLock:
                    for side, color, mode in self.Q:
                        currentmode = self.Leds[side][color][0]
                        if not mode == currentmode:
                            seq = cycle(self.LedSeq[mode])
                            self.Leds[side].update({color: [mode, seq]})
                            # print("New LedSeq: ", side, color, mode, currentmode)
                    self.Q.clear()
                for side in self.Leds:
                    for color in self.Leds[side]:
                        self.pi.write(self.Config[side]["LedGpio"][color], next(self.Leds[side][color][1]))
                with suppress(Exception):
                    time.sleep(self.NextInterval - time.process_time())
            except Exception as exc:
                if self.StayAlive:
                    logger.warning("LedControlLoop.run() trying to recover on exception")
                else:
                    logger.error("LedControlLoop.run() exiting on exception")
                    raise

    def stop(self):
        self.Active = False
        logger.debug("LedControlLoop.stop()")

    def clear(self):
        for side in self.Config:
            for color in self.Config[side]["LedGpio"]:
                self.pi.write(self.Config[side]["LedGpio"][color], 0)

    def test(self, n=1):
        for i in range(n):
            for side in self.Config:
                for color in self.Config[side]["LedGpio"]:
                    self.pi.write(self.Config[side]["LedGpio"][color], 1)
                    time.sleep(0.5)
                    self.pi.write(self.Config[side]["LedGpio"][color], 0)


if __name__ == "__main__":
    logger.debug("LedControlLoop.__main__")
    Conf = config.load()
    try:
        L = LedControlLoop(Conf)
        with L.QLock:
            Queue = []
        L.test(5)
        time.sleep(2)

        L.start()
        time.sleep(2)

        with L.QLock:
            Queue.append(("Left", "Green", "Slow"))
            Queue.append(("Left", "Red", "Steady"))
            Queue.append(("Right", "Green", "Slow"))
            Queue.append(("Right", "Red", "Fast"))
        time.sleep(10)

        with L.QLock:
            Queue.append(("Left", "Green", "Off"))
            Queue.append(("Left", "Red", "Fast"))
            Queue.append(("Right", "Green", "Slow"))
            Queue.append(("Right", "Red", "Off"))



        while True:
            time.sleep(1)
    finally:
        L.stop()

