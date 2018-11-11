import threading
import time


class WatchDog(threading.Thread):

    def __init__(self, leds):
        super().__init__()
        self.Leds = leds
        self.ThreadList = {}
        self.Lock = threading.Lock()
        self.Interval = 0
        self.Active = True

    def calm(self, side, duration):

        self.ThreadList.update({side: duration})

    def run(self, interval=3):

        self.Interval = interval
        while self.Active:
            break # fixme
            time.sleep(self.Interval)
            with self.Lock:
                for side in self.ThreadList:
                    self.ThreadList.update({side: self.ThreadList[side] - self.Interval})
                    if self.ThreadList[side] < 0:
                        with self.Leds.QLock:
                            self.Leds.Q.append(("Head", "Blue", "Slow"))
                    else:
                        # print(self.ThreadList)
                        pass
