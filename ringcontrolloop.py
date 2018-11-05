import threading
import time
from contextlib import suppress

import config



class RingControlLoop(threading.Thread):

    def __init__(self, ring, pump, ledQ, ledQlock, buttonQ, buttonQlock, interval=1):
        print("init RingControlLoop ", ring.I2Cbus)
        super(RingControlLoop, self).__init__()
        self.Ring = ring
        self.Pump = pump
        self.LedQ = ledQ
        self.LedQLock = ledQlock
        self.ButtonQ = buttonQ
        self.ButtonQLock = buttonQlock
        self.Interval = interval
        self.Active = True
        self.CurrentID = None

    def set_led(self, color, mode):
        with self.LedQLock:
            if color == "Green":
                self.LedQ.append((self.Ring.Side, "Green", mode))
                self.LedQ.append((self.Ring.Side, "Red", "Off"))
            elif color == "Red":
                self.LedQ.append((self.Ring.Side, "Green", "Off"))
                self.LedQ.append((self.Ring.Side, "Red", mode))
            else:
                self.LedQ.append((self.Ring.Side, color, mode))


    def run(self):

        msg1 = ""
        msg2 = ""
        """run the control loop for the weighing ring at a fixed interval (or as fast as possible) and update the status of the weighing ring"""
        try:
            print(self.Ring.Config)
            while self.Active:

                self.NextInterval = time.process_time() + self.Interval
                # print("Ring Status: ", self.Ring.Status, "on bus", self.Ring.I2Cbus, self.Ring.Handle)
                try:
                    if "absent" == self.Ring.Status:
                        print(self.Ring.Side + " absent")
                        self.set_led("Red", "Steady")
                        self.Ring.connect()
                        if self.CurrentID == self.Ring.ID:
                            self.Ring.Status = "found"
                            # print("refound ring ", self.Ring.ID)  # fixme
                        else:
                            self.Ring.Status = "foundnew"

                    if "foundnew" == self.Ring.Status: # fixme
                        self.Ring.initialize_adc()
                        self.CurrentID = self.Ring.ID
                        self.Ring.Status = "present"

                    if "found" == self.Ring.Status:
                        self.Ring.initialize_adc()
                        self.Ring.Status = "present"

                    if "present" == self.Ring.Status:
                        w = self.Ring.read_weight()
                        t = self.Ring.read_t()

                        if self.Ring.Side in self.ButtonQ:
                            with self.ButtonQLock:
                                self.ButtonQ.clear()
                            print("Zeroing...")
                            if (self.Ring.Config["AbsoluteMinWeight"] < w < self.Ring.Config["AbsoluteMaxWeight"]):
                                self.Ring.Config.update({"Zero": w})
                                print(self.Ring.Side + " New Zero: " + str(self.Ring.Config["Zero"]))
                                print(self.Ring.Side + " Zero: " + str(self.Ring.Config["Zero"]) + "g")
                            else:
                                self.Ring.Config.update({"Zero": 0})  # LED slowRed
                                print(self.Ring.Side + " Zeroing failed")

                        if not self.Ring.Config["AbsoluteMinWeight"] < w < self.Ring.Config["AbsoluteMaxWeight"]:
                            self.set_led("Red", "Fast")
                            msg2 = ("Column too light or to heavy -- check")  # LED fastRed
                            msg1 = (self.Ring.Side + " Weight: " + str(round(w, 1)) + "g Zero: " + str(self.Ring.Config["Zero"]) + "g : " + str(round(t, 1)) +  "°C " +  str(self.ButtonQ))
                        elif not (self.Ring.Config["Zero"] - self.Ring.Config["RelativeMinWeight"] < w < self.Ring.Config["Zero"] + self.Ring.Config["RelativeMaxWeight"]):
                            self.set_led("Red", "Slow")
                            msg2 = ("Weight difference too large -- check & zero")  # LED slowRED
                            msg1 = (self.Ring.Side + " Weight: " + str(round(w, 1)) + "g Zero: " + str(self.Ring.Config["Zero"]) + "g : " + str(round(t, 1)) + "°C " + str(self.ButtonQ))
                        else:
                            msg1 = (self.Ring.Side + " Weight: " + str(round(w, 1)) + "g Zero: " + str(self.Ring.Config["Zero"]) + "g : " + str(round(t, 1)) + "°C " + str(self.ButtonQ))
                            if w < self.Ring.Config["Zero"]:
                                msg2 = ("Pumping 15ml")  # LED slowGreen
                                self.set_led("Green", "Slow")
                            else:
                                msg2 = ("ok")  # LED steadyGreen
                                self.set_led("Green", "Steady")
                        print(msg1, msg2)

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
                with suppress(Exception): time.sleep(self.NextInterval - time.process_time())

        finally:
            self.Pump.stop()
            self.Ring.stop()
            self.Active = False




