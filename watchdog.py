import threading
import time
from os import kill
from signal import SIGKILL

from refill_log import logger



class WatchDog(threading.Thread):

    def __init__(self, leds):
        super().__init__()
        self.Leds = leds
        self.MyThreads = {}
        self.Lock = threading.Lock()
        self.Interval = 0
        self.Active = True

    def calm(self, thread_to_watch, duration):

        with self.Lock:
            self.MyThreads.update({thread_to_watch: duration})

    def shutdown(self):

        for i in range(10):
            activethreads = threading.enumerate()
            for t in activethreads:
                try:
                    t.stop()
                except AttributeError:
                    pass
            time.sleep(0.3)

    def run(self, interval=3):

        self.Interval = interval
        while self.Active:
            # break  # fixme watchdog deactivated
            time.sleep(self.Interval)
            with self.Lock:
                for thread_to_watch in self.MyThreads:
                    timeLeft = self.MyThreads[thread_to_watch] - self.Interval
                    self.MyThreads.update({thread_to_watch: timeLeft})
                    logger.debug("Watchdog {} : {}".format(thread_to_watch, str(timeLeft)))
                    if self.MyThreads[thread_to_watch] < 0:
                        logger.critical("Watch dog is missing {}. Restarting refiller service.".format(thread_to_watch))
                        self.Active = False
                        kill(0, SIGKILL)

