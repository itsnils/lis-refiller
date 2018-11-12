#!/usr/bin/python3

import refill_log
from refill_log import logger

import subprocess
import json
import config
import time
from contextlib import suppress

import pump
import blupio
from weighingring import WeighingRing
from ringcontrolloop import RingControlLoop
from buttonhandler import Buttons
from ledcontrolloop import LedControlLoop
from watchdog import WatchDog


def set_led(color, mode):
    with Leds.QLock:
        if color == "Green":
            Leds.Q.append(("Head", "Green", mode))
            Leds.Q.append(("Head", "Red", "Off"))
        elif color == "Red":
            Leds.Q.append(("Head", "Green", "Off"))
            Leds.Q.append(("Head", "Red", mode))
        else:
            Leds.Q.append(("Head", color, mode))


def free_handles():
    for i in range(25, 127):
        with suppress(Exception):
            pi.i2c_close(i)
        with suppress(Exception):
            pi.spi_close(i)


def fiat_nox(conf):
    pi.write(conf["Head"]["BuzzerGpio"], 0)
    for side in conf:
        for color in conf[side]["LedGpio"]:
            pi.write(conf[side]["LedGpio"][color], 0)


def beep(conf, duration=0.05):
    pi.write(conf["Head"]["BuzzerGpio"], 1)
    time.sleep(duration)
    pi.write(conf["Head"]["BuzzerGpio"], 0)


def red_alert(conf):
    for side in conf:
        for color in conf[side]["LedGpio"]:
            pi.write(conf[side]["LedGpio"][color], 1) if color == "Red" else pi.write(conf[side]["LedGpio"][color], 0)


def check_wifi_state():
    try:
        iwconfig_out = subprocess.check_output('/sbin/iwconfig', stderr=subprocess.STDOUT).decode('utf-8')
    except Exception as exc:
        logger.error("Wifi Dection failed:" + str(exc))
    else:
        logger.debug('iwconfig' + str(iwconfig_out))
        if "Mode:Master" in iwconfig_out:
            return "ap_mode"
        elif ("Access Point: Not-Associated" in iwconfig_out) or ("ESSID:off" in iwconfig_out):
            return "off"
        else:
            return "connected"


if __name__ == '__main__':

    logger.info("Refiller.py starting up")

    pi = blupio.pi()

    free_handles()

    # load or create config.json
    Config = config.load()
    logger.debug(json.dumps(Config))
    with suppress(KeyError):
        StayAlive = Config["Head"]["StayAlive"]
    beep(Config, 0.1)  # greeting
    fiat_nox(Config)   # switch off LEDs

    # create LedQ list and LedControlLoop, initialize and start
    Leds = LedControlLoop(Config, interval=0.2, stayalive=StayAlive)

    wifi_configmode_flag = False

    # create Watchdog and start
    Watchdog = WatchDog(Leds)
    Leds.Watchdog = Watchdog

    # start LED and Watchdog threads
    Watchdog.start()
    Leds.start()

    # create ButtonQ dict and Buttons object and initialize
    Buttons = Buttons()

    # create Pump object and initialize
    Pump = pump.Pump(Config)
    PumpStop = None

    # create weighing ring objects and initialize
    Rings = [WeighingRing(side="Left", config=Config), WeighingRing(side="Right", config=Config)]
    # create weighing ring control loop thread objects and start
    threads = []
    for Ring in Rings:
        thread = RingControlLoop(Ring, Pump, Leds, Buttons, interval=0.5, stayalive=StayAlive)
        thread.Watchdog = Watchdog
        thread.setName("RingControlLoop" + str(Ring.Side))
        threads.append(thread)
        thread.start()

    # controller control loop
    while True:
        try:
            time.sleep(1)
            Watchdog.calm("Head", 10)
            if not Buttons.QLock.locked():
                with Buttons.QLock:
                    if len(Buttons.Q):
                        print("Button: ", Buttons.Q)
                        try:
                            if Buttons.Q["Left"] >= 4:
                                Buttons.Q.pop("Left")
                                wifi_configmode_flag = True
                                with Leds.QLock:
                                    Leds.Q.append(("Head", "Blue", "Fast"))
                                logger.info("Enter Wifi Config...")
                                Pump.stop()
                                config.save(Config)
                                with open("/home/pi/Refiller/wifi_conf_flag", "w") as f:
                                    f.write("start wifi configuration")
                                    logger.debug("Setting wifi_conf_flag")
                            else:
                                # put other double button actions here
                                Buttons.Q.pop("Left")
                        except KeyError:
                            pass

            # set Wifi status LED
            if not wifi_configmode_flag:
                WifiState = check_wifi_state()
                with Leds.QLock:
                    if WifiState == "connected":
                        Leds.Q.append(["Head", "Blue", "Steady"])
                    elif WifiState == "ap_mode":
                        Leds.Q.append(["Head", "Blue", "Slow"])
                    else:
                        Leds.Q.append(["Head", "Blue", "Off"])

            # set head status LED
            if not Pump.arrived():
                set_led("Green", "Slow")
                if not Pump.Lock.locked():
                    Pump.Lock.acquire()
            else:
                set_led("Green", "Alive")
                try:
                    Pump.Lock.release()
                except RuntimeError:
                    pass

        # keep alive if exception
        except Exception as exc:
            if StayAlive:
                logger.error("Trying to go on after Exception" + str(exc))
                print(exc)
            else:
                logger.error("Exiting on Exception" + str(exc))
                beep(Config, 1)
                red_alert(Config)
                raise
        except KeyboardInterrupt:
            logger.info("Exiting on Keyboard Interrupt")
            Leds.Active = False
            for thread in threads:
                thread.Active = False
            red_alert(Config)
            beep(Config, 1)
            raise
        except BaseException as exc:
            logger.error("Exiting on BaseException" + str(exc))
            for thread in threads:
                Leds.Active = False
                thread.Active = False
                red_alert(Config)
            # beep(Config, 10)
            raise
