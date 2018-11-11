import threading
import tmc5130
from getserial import getserial
from refill_log import logger


class Pump(tmc5130.Pump):

    def __init__(self, config):
        self.Config = config
        super().__init__(self.Config["Head"]["StepsPerML"])
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

    def pump(self, dir, vol=None, flow=None):
        """ pumps the desired volume at the desired flow rate (optional)
            updates the volume pumped per direction/channel so far, even if vol and flow are None
        """
        if self.Config["Head"]["ValveType"] == "Rectifier":
            if vol is not None:
                steps = int(dir * vol * self.F)
                if flow is not None:
                    stepspeed = int(abs(flow) * self.F)
                    newpos = self.moveby(relpos=steps, speed=stepspeed)
                else:
                    newpos = self.moveby(relpos=steps)
                if vol > 0:
                    self.CurrentDir = dir
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

        elif self.Config["Head"]["ValveType"] == "Switch":
            # set valve
            self.pi.write(self.Config["Head"]["ValveGpio"], 1 if dir > 0 else 0)
            if vol is not None:
                steps = int(abs(vol) * self.F) * self.Config["Head"]["PumpDir"]
                if flow is not None:
                    stepspeed = int(abs(flow) * self.F)
                    newpos = self.moveby(relpos=steps, speed=stepspeed)
                else:
                    newpos = self.moveby(relpos=steps)
                if vol > 0:
                    self.CurrentDir = dir
                else:
                    self.CurrentDir = 0
            else:
                newpos = self.moveby()
                self.CurrentDir = 0
            if dir > 0:
                self.TotalP += (newpos-self.Oldpos)/self.F
            else:
                self.TotalM += (newpos-self.Oldpos)/self.F
            self.Oldpos = newpos
            return self.TotalP, self.TotalM
