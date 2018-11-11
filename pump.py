import threading
import tmc5130
from getserial import getserial
from refill_log import logger


class Pump(tmc5130.Pump):

    def __init__(self, StepsPerMilliliter=None):
        super().__init__(StepsPerMilliliter)
        self.SerialNumber = getserial()
        self.Lock = threading.Lock()
        self.CurrentDir = 0
        logger.info("RPi serial# " + str(self.SerialNumber))
        return

    def serial_number(self):
        return self.SerialNumber

    def stop(self, dir = None):
        if dir == self.CurrentDir or dir is None:
            self.moveby(relpos=0)
            return True
        else:
            return False

    def pump(self, vol=None, flow=None, valve="Rectifier"):
        """ pumps the desired volume at the desired flow rate (optional)
            updates the positive and negative volume pumped so far, even if vol and flow are None
        """
        if valve == "Rectifier":
            if vol is not None:
                steps = int(vol * self.F)
                if flow is not None:
                    stepspeed = int(abs(flow) * self.F)
                    newpos = self.moveby(relpos=steps, speed=stepspeed)
                else:
                    newpos = self.moveby(relpos=steps)
                if vol > 0:
                    self.CurrentDir = 1
                elif vol < 0:
                    self.CurrentDir = -1
                else:
                    self.CurrentDir = 0
            else:
                newpos = self.moveby()
                self.CurrentDir = 0
            if self.Oldpos < newpos:
                self.TotalP += (newpos-self.Oldpos)/self.F
            else:
                self.TotalM += (self.Oldpos-newpos)/self.F
            self.Oldpos = newpos
            return self.TotalP, self.TotalM
        elif valve == "Switch":
            pass
