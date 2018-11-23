import threading
import time
import config
from contextlib import suppress

from refill_log import logger


class RingControlLoop(threading.Thread):

    def __init__(self, ring, pump, leds, buttons, watchdog=None, interval=1, stayalive=True):
        logger.info("RingControlLoop.__init__()  ring= {}".format(str(ring)))
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
        skip_log = 0
        self.Watchdog.calm(self.Ring.Side, duration=20)  # fixme
        while self.Active:
            try:
                self.NextInterval = time.process_time() + self.Interval
                self.Watchdog.calm(self.Ring.Side, duration=20)
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
                                    logger.info("{:6} zeroing...".format(self.Ring.Side))
                                    if self.RingConfig["AbsoluteMinWeight"] < w < self.RingConfig["AbsoluteMaxWeight"]:
                                        # Zero
                                        self.Ring.pi.write(self.Ring.Config["Head"]["BuzzerGpio"], 1)  # fixme preliminary buzzer signal
                                        self.RingConfig.update({"Zero": wavg - (self.RingConfig["PumpVolume"]/2)})
                                        self.RingConfig.update({"SerialNumber": self.Ring.ID})
                                        self.Ring.pi.write(self.Ring.Config["Head"]["BuzzerGpio"], 0)  # fixme preliminary buzzer signal
                                        time.sleep(0.2)   # fixme preliminary buzzer signal
                                        config.save(self.Ring.Config)
                                        self.Ring.pi.write(self.Ring.Config["Head"]["BuzzerGpio"], 1)  # fixme preliminary buzzer signal
                                        logger.info("{:6}   New Zero: {: 6.1f}"
                                                    .format(self.Ring.Side, self.RingConfig["Zero"]))
                                        self.Ring.pi.write(self.Ring.Config["Head"]["BuzzerGpio"], 0)  # fixme preliminary buzzer signal
                                    else:
                                        self.RingConfig.update({"Zero": 0})  # LED slowRed
                                        logger.warning(self.Ring.Side + " zeroing failed")
                                elif self.Buttons.Q[self.Ring.Side] >= 4:
                                    pass
                            except KeyError:
                                pass

                        msg1 = "{:6}  W{:6.1f} g  Wavg{:6.1f} g  Zero{:6.1f} g  Ring {:5.1f} °C  Head {:5.1f} °C  I2Cerr {:<7d}  {}"\
                            .format(self.Ring.Side, w, wavg, self.RingConfig["Zero"],
                                    t, self.Pump.rpi_temperature(), self.Ring.pi.error_count, self.Buttons.Q)

                        if not self.RingConfig["AbsoluteMinWeight"] < w < self.RingConfig["AbsoluteMaxWeight"]:
                            # Weight is out of range
                            self.Pump.stop(self.RingConfig["PumpDir"])
                            self.set_led("Red", "Fast")
                            self.Ring.Mean.reset()
                            msg2 = "Column too light or to heavy -- check"  # LED fastRed
                            skip_log = 0
                        elif not (self.RingConfig["Zero"] - self.RingConfig["RelativeMinWeight"]
                                  < w <
                                  self.RingConfig["Zero"] + self.RingConfig["RelativeMaxWeight"]):
                            # Weight deviates too much from zero
                            self.Pump.stop(self.RingConfig["PumpDir"])
                            self.set_led("Red", "Slow")
                            self.Ring.Mean.reset()
                            msg2 = "Weight difference too large -- check & zero"  # LED slowRED
                            skip_log = 0
                        else:
                            # weight is plausible
                            if wavg < self.RingConfig["Zero"] and w < self.RingConfig["Zero"] \
                                    and self.Ring.Mean.Width > self.Ring.Mean.MinWidth:
                                # need for refill detected
                                if self.Pump.rpi_temperature() < self.Ring.Config["Head"]["MaxTemp"]:
                                    # pump temperature ok
                                    if not self.Pump.Lock.locked():
                                        self.Pump.pump(self.RingConfig["PumpDir"],
                                                       self.RingConfig["PumpVolume"],
                                                       self.RingConfig["PumpRate"])
                                    msg2 = "Refill"  # LED slowGreen
                                else:
                                    # pump temperature too high
                                    msg2 = "Pump too hot, refill deferred"
                                skip_log = 0
                                self.set_led("Green", "Slow")
                            else:
                                # no need to refill
                                msg2 = "ok"  # LED steadyGreen
                                self.set_led("Green", "Steady")

                        if skip_log <= 0:
                            logger.info(msg1 + msg2)
                            skip_log = 30
                        else:
                            skip_log -= 1

                    if "lost" == self.Ring.Status:
                        self.Ring.stop()
                        self.Ring.Status = "absent"
                        self.Ring.LED = "Off"

                except ConnectionError as exc:
                    self.Ring.Status = "lost"
                    self.Ring.i2c_close()
                    self.Ring.EEPROM.i2c_close()
                    if self.Ring.Status != "absent":
                        logger.warning("Ring lost on bus {}".format(str(self.Ring.I2Cbus))) # fixme

                with suppress(Exception):
                    time.sleep(self.NextInterval - time.process_time())

            except Exception as exc:
                if self.StayAlive:
                    logger.error("Exception:", exc)
                    self.Pump.stop(direction=self.RingConfig["PumpDir"])
                    self.Ring.stop()
                    self.Ring.Status = "absent"
                else:
                    raise

        self.Active = False

    def stop(self):
        self.Active = False
