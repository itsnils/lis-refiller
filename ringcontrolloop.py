import threading
import time
from contextlib import suppress

import config



class RingControlLoop(threading.Thread):

    def __init__(self, ring, pump):
        #print("init RingControlLoop")
        super(RingControlLoop, self).__init__()
        self.Ring = ring
        self.Pump = pump
        self.Active = True
        self.Config = config.load()

    def run(self):
        """run the control loop for the weighing ring at a fixed interval (or as fast as possible) and update the status of the weighing ring"""
        try:
            self.NextInterval = time.process_time() + self.Ring.Interval

            while self.Active:
                if "absent" == self.Ring.Status:
                    if self.Ring.connect():
                        id = self.Ring.EEPROM.read_id()
                        if self.Ring.ID == id:
                            self.Ring.Status = "found"
                            print("refound ring ", id)  # fixme
                        else:
                            self.Ring.Status = "foundnew"
                            self.Ring.ID = id
                            print("found new ring ", id)  # fixme
                        self.Ring.LED = "SteadyRed"
                    else:
                        self.Ring.Status = "absent"
                        self.Ring.LED = "Off"
                elif "found" == self.Ring.Status:
                    if self.Ring.initializeADC():
                        self.Ring.Status = "present"
                        self.Ring.LED = "SlowRed"
                    else:
                        self.Ring.Status = "lost"
                        self.Ring.LED = "SteadyRed"
                elif "present" == self.Ring.Status:
                    if self.Ring.update():
                        self.Ring.Status = "present"
                        if self.Ring.check():
                            if self.Ring.Weight > self.Ring.Zero:
                                self.Ring.LED = "SteadyGreen"
                            else:
                                self.Pump(self.Ring.Sign * self.Ring.VolumeStep, self.Ring.PumpSpeed)
                                self.Ring.LED = "SlowGreen"
                        else:
                            self.Ring.LED = "SlowRed"
                    else:
                        self.Ring.Status = "lost"
                        self.Ring.LED = "SteadyRed"
                elif "lost" == self.Ring.Status:
                    if self.Ring.connect():
                        self.Ring.Status = "found"
                    else:
                        self.Ring.stop()
                        self.Ring.Status = "absent"
                        self.Ring.LED = "Off"
                else:
                    raise(SystemError, "Ring Status = " + self.Ring.Status)

                sleep = self.NextInterval - time.process_time()
                with suppress(Exception): time.sleep(sleep)
        finally:
            self.Pump.stop()
            self.Ring.stop()
            self.Active = False




