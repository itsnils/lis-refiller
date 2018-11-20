import threading
import time
import config
from contextlib import suppress

from refill_log import logger


class RingControlLoop(threading.Thread):

    def __init__(self, ring, pump, leds, buttons, watchdog=None, interval=1, stayalive=True):
        logger.info("RingControlLoop.__init__()  ring=" + str(ring))
        super(RingControlLoop, self).__init__()
        self.Ring = ring
        self.RingConfig = self.Ring.Config[self.Ring.Side]
        self.Pump = pump
        self.Leds = leds
        self.Buttons = buttons
        self.Interval = interval
        self.Watchdog = watchdog
        self.StayAlive = stayalive
        self.NextInterval = None
        self.Active = True
        self.CurrentID = None
        self.Ring.Status = "absent"
        logger.debug("RingControlLoop.__init__() done ring = " + str(self.Ring.Side))

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
        # print(self.RingConfig)
        logger.debug("RingControlLoop.run()")
        self.Active = True
        while self.Active:
            try:
                self.NextInterval = time.process_time() + self.Interval
                # print("Watchdog:", self.Ring.Side, 10)
                self.Watchdog.calm(side=self.Ring.Side, duration=10)  # fixme
                # print("Ring Status: ", self.Ring.Status, "on bus", self.Ring.I2Cbus, self.Ring.Handle)
                try:
                    if "absent" == self.Ring.Status:
                        # print(self.Ring.Side + " absent")
                        self.set_led("Red", "Off")
                        try:
                            self.Ring.connect()
                        except ConnectionError:
                            pass
                        else:
                            logger.debug("Ring" + self.Ring.ID + " found on " + self.Ring.Side)
                            if self.CurrentID == self.Ring.ID:
                                self.Ring.Status = "found"
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
                        wavg = self.Ring.WeightAvg
                        t = self.Ring.read_t()

                        with self.Buttons.QLock:
                            try:
                                if self.Buttons.Q[self.Ring.Side] >= 1:
                                    self.Buttons.Q.pop(self.Ring.Side)
                                    logger.info(self.Ring.Side + " zeroing...")
                                    if self.RingConfig["AbsoluteMinWeight"] < w < self.RingConfig["AbsoluteMaxWeight"]:
                                        self.RingConfig.update({"Zero": wavg - (self.RingConfig["PumpVolume"]/2)})
                                        self.RingConfig.update({"SerialNumber": self.Ring.ID})
                                        config.save(self.Ring.Config)
                                        logger.info(self.Ring.Side + " New Zero: " + str(self.RingConfig["Zero"]))
                                    else:
                                        self.RingConfig.update({"Zero": 0})  # LED slowRed
                                        logger.warning(self.Ring.Side + " zeroing failed")
                                elif self.Buttons.Q[self.Ring.Side] >= 4:
                                    pass
                            except KeyError:
                                pass

                        if not self.RingConfig["AbsoluteMinWeight"] < w < self.RingConfig["AbsoluteMaxWeight"]:
                            self.Pump.stop(self.RingConfig["PumpDir"])
                            self.set_led("Red", "Fast")
                            self.Ring.Mean.reset()
                            msg2 = "Column too light or to heavy -- check"  # LED fastRed
                            msg1 = (self.Ring.Side +
                                    " W: " + str(round(w, 1)) +
                                    " Wavg: " + str(round(wavg, 1)) +
                                    " Zero: " + str(self.RingConfig["Zero"]) +
                                    " : " + str(round(t, 1)) + "°C " + str(self.Buttons.Q))
                        elif not (self.RingConfig["Zero"] - self.RingConfig["RelativeMinWeight"]
                                  < w <
                                  self.RingConfig["Zero"] + self.RingConfig["RelativeMaxWeight"]):
                            self.Pump.stop(self.RingConfig["PumpDir"])
                            self.set_led("Red", "Slow")
                            self.Ring.Mean.reset()
                            msg2 = "Weight difference too large -- check & zero"  # LED slowRED
                            msg1 = (self.Ring.Side +
                                    " W: " + str(round(w, 1)) +
                                    " Wavg: " + str(round(wavg, 1)) +
                                    " Zero: " + str(self.RingConfig["Zero"]) +
                                    " : " + str(round(t, 1)) + "°C " + str(self.Buttons.Q))
                        else:
                            msg1 = (self.Ring.Side +
                                    " W: " + str(round(w, 1)) +
                                    " Wavg: " + str(round(wavg, 1)) +
                                    " Zero: " + str(self.RingConfig["Zero"]) +
                                    " : " + str(round(t, 1)) + "°C " + str(self.Buttons.Q))

                            if wavg < self.RingConfig["Zero"] and w < self.RingConfig["Zero"] \
                                    and self.Ring.Mean.Width > self.Ring.Mean.MinWidth:
                                if not self.Pump.Lock.locked():
                                    self.Pump.pump(self.RingConfig["PumpDir"],
                                                   self.RingConfig["PumpVolume"],
                                                   self.RingConfig["PumpRate"])
                                msg2 = "Pumping"  # LED slowGreen
                                self.set_led("Green", "Slow")

                            else:
                                msg2 = "ok"  # LED steadyGreen
                                self.set_led("Green", "Steady")

                        if False: print(str(round(time.time()/3600, 3)), msg1, msg2)
                        logger.info(msg1 + msg2)

                    if "lost" == self.Ring.Status:
                        self.Ring.stop()
                        self.Ring.Status = "absent"
                        self.Ring.LED = "Off"

                except ConnectionError as exc:
                    self.Ring.Status = "lost"
                    self.Ring.i2c_close()
                    self.Ring.EEPROM.i2c_close()
                    if self.Ring.Status != "absent":
                        if False: print(self.Ring.Status, " lost ring", exc)
                        logger.warning("Ring lost on bus" + str(self.Ring.I2Cbus))  # fixme
                    # else: print("Ring absent on bus", self.Ring.I2Cbus)

                with suppress(Exception):
                    time.sleep(self.NextInterval - time.process_time())

            except Exception as exc:
                if self.StayAlive:
                    # print(exc)
                    logger.error("Exception:", exc)
                    self.Pump.stop(direction=self.RingConfig["PumpDir"])
                    self.Ring.stop()
                    self.Ring.Status = "absent"
                else:
                    raise

        self.Active = False

    def stop(self):
        self.Active = False
