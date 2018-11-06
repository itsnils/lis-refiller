import threading
import tmc5130
from getserial import getserial

class Pump(tmc5130.Pump):
    def __init__(self, StepsPerMilliliter=None):
        super().__init__(StepsPerMilliliter)
        self.SerialNumber = getserial()
        self.Lock = threading.Lock()
        print("RPi serial# ", self.SerialNumber)
        print("TotalM ", self.TotalM, "   TotalP ",self.TotalP)
        return

    def serial_number(self):
        return self.SerialNumber

    def stop(self):
        pass




