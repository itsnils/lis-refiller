import time
import threading

import pigpio


class Buttons:


    def __init__(self, gpioL=21, gpioR=17):

        self.Q = {}
        self.QLock = threading.Lock()
        self.GpioL = gpioL
        self.GpioR = gpioR
        self.pi = pigpio.pi()
        self.TickL = 0
        self.LevelL = 0
        self.TickR = 0
        self.LevelR = 0
        self.LevelM = 0
        self.InitL = True
        self.InitR = True
        #initialize GPIOs
        self.pi.write(gpioL, 0)
        self.pi.write(gpioR, 0)
        time.sleep(0.01)
        self.pi.set_mode(gpioL, pigpio.INPUT)
        self.pi.set_mode(gpioR, pigpio.INPUT)
        self.pi.set_noise_filter(gpioL, 30000, 30000 )
        self.pi.set_noise_filter(gpioR, 30000, 30000 )
        self.CbL = self.pi.callback(gpioL,pigpio.EITHER_EDGE, self.button_handler)
        self.CbR = self.pi.callback(gpioR,pigpio.EITHER_EDGE, self.button_handler)



    def __exit__(self, exc_type, exc_val, exc_tb):
        self.CbL.cancel()
        self.CbR.cancel()

    def button_handler(self, gpio, level, tick):
        # print("button hanlder called", gpio, level, tick)
        if level:  # if some button is pressed
            self.pi.write(12,1)
            if gpio == self.GpioL:
                self.TickL = tick
                self.LevelL = 1
            elif gpio == self.GpioR:
                self.TickR = tick
                self.LevelR = 1
        else:  # if some button is released
            if self.InitL: self.InitL = False; return
            if self.InitR: self.InitR = False; return
            self.pi.write(12,0)
            if gpio == self.GpioL:
                # L is released...
                if self.LevelR:
                    # ...while R is pressed
                    self.LevelM = 1
                    self.TickM = max(self.TickL, self.TickR)
                    self.LevelL = 0
                    self.TickL = tick
                elif self.LevelM:
                    # ... and R was released while L was pressed
                    # => double press
                    self.log_event("Head", tick - self.TickM)
                    self.LevelM = 0
                    self.LevelL = 0
                    self.TickL = tick
                else:
                    # => single press
                    self.log_event("Left", tick - self.TickL)
                    self.LevelL = 0
                    self.TickL = tick
            elif gpio == self.GpioR:
                # R is released...
                if self.LevelL:
                    # ...while L is pressed
                    self.LevelM = 1
                    self.TickM = max(self.TickL, self.TickR)
                    self.LevelR = 0
                    self.TickR = tick
                elif self.LevelM:
                    # ... and L was released while R was pressed
                    # => double press
                    self.log_event("Head", tick - self.TickM)
                    self.LevelM = 0
                    self.LevelR = 0
                    self.TickR = tick
                else:
                    # => single press
                    self.log_event("Right", tick - self.TickR)
                    self.LevelR = 0
                    self.TickR = tick

    def log_event(self, e, d=None):
        d /= 1e6  # convert microseconds to seconds
        with self.QLock:
            if d > 4:
                self.Q.update({e: 4})
                # print(self.ButtonQ[e])
            elif d > 1:
                self.Q.update({e: 1})
                # print(self.ButtonQ[e])


if __name__ == '__main__':
    try:
        buttons = Buttons()
        while True:
            # print("yawn")
            time.sleep(1)
    finally:
        buttons.__exit__(None, None, None)
