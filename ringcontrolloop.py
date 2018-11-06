import threading
import time
import config
from contextlib import suppress


class RingControlLoop(threading.Thread):

    def __init__(self, ring, pump, leds, buttons, watchdog=None, interval=1):
        print("init RingControlLoop ", ring.I2Cbus)
        super(RingControlLoop, self).__init__()
        self.Ring = ring
        self.Config = self.Ring.Config[self.Ring.Side]
        self.Pump = pump
        self.Leds = leds
        self.Buttons = buttons
        self.Interval = interval
        self.Watchdog = watchdog
        self.NextInterval = None
        self.Active = True
        self.CurrentID = None
        self.Ring.Status = "absent"

    def set_led(self, color, mode):
        with self.Leds.QLock:
            if color == "Green":
                self.Leds.Q.append((self.Ring.Side, "Green", mode))
                self.Leds.Q.append((self.Ring.Side, "Red", "Off"))
            elif color == "Red":
                self.Leds.Q.append((self.Ring.Side, "Green", "Off"))
                self.Leds.Q.append((self.Ring.Side, "Red", mode))
            else:
                self.Leds.Q.append((self.Ring.Side, color, mode))

    def run(self):

        """run the control loop for the weighing ring at a fixed interval
        (or as fast as possible) and update the status of the weighing ring"""
        try:
            print(self.Config)
            while self.Active:

                self.NextInterval = time.process_time() + self.Interval
                #print("Watchdog:", self.Ring.Side, 10)
                self.Watchdog.calm(side=self.Ring.Side, duration=10) # fixme
                # print("Ring Status: ", self.Ring.Status, "on bus", self.Ring.I2Cbus, self.Ring.Handle)
                try:
                    if "absent" == self.Ring.Status:
                        # print(self.Ring.Side + " absent")
                        self.set_led("Red", "Off")
                        self.Ring.connect()
                        if self.CurrentID == self.Ring.ID:
                            self.Ring.Status = "found"
                            # print("refound ring ", self.Ring.ID)  # fixme
                        else:
                            self.Ring.Status = "foundnew"

                    if "foundnew" == self.Ring.Status:  # fixme
                        self.Ring.initialize_adc()
                        self.CurrentID = self.Ring.ID
                        self.Ring.Status = "present"

                    if "found" == self.Ring.Status:
                        self.Ring.initialize_adc()
                        self.Ring.Status = "present"

                    if "present" == self.Ring.Status:
                        w = self.Ring.read_weight()
                        t = self.Ring.read_t()

                        if self.Ring.Side in self.Buttons.Q:
                            with self.Buttons.QLock:
                                self.Buttons.Q.clear()
                            print("Zeroing...")
                            if self.Config["AbsoluteMinWeight"] < w < self.Config["AbsoluteMaxWeight"]:
                                self.Config.update({"Zero": w-3})
                                self.Config.update({"SerialNumber": self.Ring.ID})
                                config.save(self.Ring.Config)
                                print(self.Ring.Side + " New Zero: " + str(self.Config["Zero"]))
                                print(self.Ring.Side + " Zero: " + str(self.Config["Zero"]) + "g")
                            else:
                                self.Config.update({"Zero": 0})  # LED slowRed
                                print(self.Ring.Side + " Zeroing failed")

                        if not self.Config["AbsoluteMinWeight"] < w < self.Config["AbsoluteMaxWeight"]:
                            self.set_led("Red", "Fast")
                            # fixme self.Leds.Q.append((self.Ring.Side, "Beep", "Bibip"))

                            msg2 = "Column too light or to heavy -- check"  # LED fastRed
                            msg1 = (self.Ring.Side +
                                    " Weight: " + str(round(w, 1)) +
                                    "g Zero: " + str(self.Config["Zero"]) +
                                    "g : " + str(round(t, 1)) + "°C " + str(self.Buttons.Q))
                        elif not (self.Config["Zero"] - self.Config["RelativeMinWeight"]
                                  < w <
                                  self.Config["Zero"] + self.Config["RelativeMaxWeight"]):
                            self.set_led("Red", "Slow")
                            # fixme self.Leds.Q.append((self.Ring.Side, "Beep", "Bip"))

                            msg2 = "Weight difference too large -- check & zero"  # LED slowRED
                            msg1 = (self.Ring.Side + " Weight: " + str(round(w, 1)) +
                                    "g Zero: " + str(self.Config["Zero"]) + "g : " +
                                    str(round(t, 1)) + "°C " + str(self.Buttons.Q))
                        else:
                            msg1 = (self.Ring.Side + " Weight: " + str(round(w, 1)) +
                                    "g Zero: " + str(self.Config["Zero"]) +
                                    "g : " + str(round(t, 1)) + "°C " + str(self.Buttons.Q))
                            if w < self.Config["Zero"]:
                                if not self.Pump.Lock.locked():
                                    self.Pump.pump(self.Config["PumpVolume"]*self.Config["PumpDir"], self.Config["PumpRate"])
                                msg2 = "Pumping 15ml"  # LED slowGreen
                                self.set_led("Green", "Slow")
                                # fixme self.Leds.Q.append((self.Ring.Side, "Beep", "Off"))

                            else:
                                msg2 = "ok"  # LED steadyGreen
                                self.set_led("Green", "Steady")
                                # fixme self.Leds.Q.append((self.Ring.Side, "Beep", "Off"))

                        print(str(round(time.time()/3600,3)),msg1, msg2)

                    if "lost" == self.Ring.Status:
                        self.Ring.stop()
                        self.Ring.Status = "absent"
                        self.Ring.LED = "Off"

                except ConnectionError:
                    self.Ring.Status = "absent"
                    self.Ring.i2c_close()
                    self.Ring.EEPROM.i2c_close()
                    if self.Ring.Status != "absent":
                        print("Ring lost on bus", self.Ring.I2Cbus)  # fixme
                    # else: print("Ring absent on bus", self.Ring.I2Cbus)
                with suppress(Exception):
                    time.sleep(self.NextInterval - time.process_time())

        finally:
            self.Pump.stop()
            self.Ring.stop()
            self.Active = False




