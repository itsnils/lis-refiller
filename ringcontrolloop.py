import threading
import time
from contextlib import suppress

import config



class RingControlLoop(threading.Thread):

    def __init__(self, ring, pump, buttonQ, interval=1):
        print("init RingControlLoop ", ring.I2Cbus)
        super(RingControlLoop, self).__init__()
        self.Ring = ring
        self.Pump = pump
        self.ButtonQ = buttonQ
        self.Interval = interval
        self.Active = True
        self.CurrentID = None

    def run(self):
        """run the control loop for the weighing ring at a fixed interval (or as fast as possible) and update the status of the weighing ring"""
        try:
            print(self.Ring.Config)
            while self.Active:

                self.NextInterval = time.process_time() + self.Interval
                # print("Ring Status: ", self.Ring.Status, "on bus", self.Ring.I2Cbus, self.Ring.Handle)
                try:
                    if "absent" == self.Ring.Status:
                        self.Ring.connect()
                        if self.CurrentID == self.Ring.ID:
                            self.Ring.Status = "found"
                            # print("refound ring ", self.Ring.ID)  # fixme
                        else:
                            self.Ring.Status = "foundnew"
                        self.Ring.LED = "SteadyRed"

                    if "foundnew" == self.Ring.Status: # fixme
                        self.Ring.initialize_adc()
                        self.CurrentID = self.Ring.ID
                        self.Ring.Status = "present"
                        self.Ring.LED = "SlowRed"

                    if "found" == self.Ring.Status:
                        self.Ring.initialize_adc()
                        self.Ring.Status = "present"
                        self.Ring.LED = "SlowRed"

                    if "present" == self.Ring.Status:
                        w = self.Ring.read_weight()
                        t = self.Ring.read_t()
                        if "L" in self.ButtonQ:
                            print("Zeroing...")
                            self.Ring.Config.update({"Zero": w})
                            print("Zero: ", self.Ring.Config["Zero"], "g")
                        elif not (self.Ring.Config["AbsoluteMinWeight"] < self.Ring.Config["Zero"] < self.Ring.Config["AbsoluteMaxWeight"]):
                            print("Check and zero")
                            print("Weight: ", round(w, 1), "g : delta ------ g : ", round(t, 1), "°C ", self.ButtonQ)
                        else:
                            d = w - self.Ring.Config["Zero"]
                            print("Weight: ", round(w, 1), "g : delta ", round(d, 1), "g : ", round(t, 1), "°C ", self.ButtonQ)
                            if d > 50:
                                print("Too heavy - check and re-zero")
                            elif d < -50:
                                print("Too light - check & re-zero")
                            elif d < 0:
                                print("Pumping 15ml")


                        # fixme
                        """
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
                        """
                        pass

                    if "lost" == self.Ring.Status:
                        self.Ring.stop()
                        self.Ring.Status = "absent"
                        self.Ring.LED = "Off"

                except ConnectionError:
                    self.Ring.Status = "absent"
                    self.Ring.i2c_close()
                    self.Ring.EEPROM.i2c_close()
                    if self.Ring.Status != "absent": print("Ring lost on bus", self.Ring.I2Cbus)  # fixme
                    # else: print("Ring absent on bus", self.Ring.I2Cbus)

                sleep = self.NextInterval - time.process_time()
                with suppress(Exception): time.sleep(sleep)

        finally:
            self.Pump.stop()
            self.Ring.stop()
            self.Active = False




