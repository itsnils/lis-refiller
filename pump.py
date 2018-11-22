import threading
import tmc5130
from refill_log import logger


class Pump(tmc5130.Pump):

    def __init__(self, config):
        self.Config = config
        super().__init__(self.Config["Head"]["StepsPerML"])
        self.Lock = threading.Lock()
        self.CurrentDir = 0
        logger.info("Pump.__init__()")
        self.Temperature = self.rpi_temperature()
        return

    def rpi_temperature(self):
        """ returns the Raspberry Pi internal temperature sensor"""
        try:
            self.Temperature = int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1e3
            return self.Temperature
        except:
            return -999.9

    def stop(self, direction=None):
        if direction == self.CurrentDir or direction is None:
            self.moveby(relpos=0)
            return True
        else:
            return False

    def pump(self, direction, vol=None, flow=None):
        """ pumps the desired volume at the desired flow rate (optional)
            updates the volume pumped per direction/channel so far, even if vol and flow are None
        """

        t = self.rpi_temperature()
        if vol is not 0 and t > self.Config["Head"]["MaxTemp"]:
            return self.TotalP, self.TotalM
        if self.Config["Head"]["ValveType"] == "Rectifier":
            if vol is not None:
                steps = int(direction * vol * self.F)
                if flow is not None:
                    stepspeed = int(abs(flow) * self.F)
                    newpos = self.moveby(relpos=steps, speed=stepspeed)
                else:
                    newpos = self.moveby(relpos=steps)
                if vol > 0:
                    self.CurrentDir = direction
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
            self.pi.write(self.Config["Head"]["ValveGpio"], 1 if direction > 0 else 0)
            if vol is not None:
                steps = int(abs(vol) * self.F) * self.Config["Head"]["PumpDir"]
                if flow is not None:
                    stepspeed = int(abs(flow) * self.F)
                    newpos = self.moveby(relpos=steps, speed=stepspeed)
                else:
                    newpos = self.moveby(relpos=steps)
                if vol > 0:
                    self.CurrentDir = direction
                else:
                    self.CurrentDir = 0
            else:
                newpos = self.moveby()
                self.CurrentDir = 0
            if direction > 0:
                self.TotalP += (newpos-self.Oldpos)/self.F
            else:
                self.TotalM += (newpos-self.Oldpos)/self.F
            self.Oldpos = newpos
            return self.TotalP, self.TotalM
