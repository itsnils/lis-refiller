from contextlib import suppress
import threading
import time

import pigpio
import ads122c04  #24-bit ADC TI ADS122C04
import mc24aa025e48 #1024-bit eeprom with unique 48-bit ID Microchip MC24AA025E48
import runningmean
import config

class WeighingRing(ads122c04.ADS122C04):
    I2Caddr = 0x45
    EEPROM_I2Caddr = 0x51
    Interval = 1  # seconds
    RunningMeanWidth = 16
    GeneralParms = {'VREF': 0b10,
                    'I1MUX': 0,
                    'I2MUX': 0,
                    'GAIN': 0b011,
                    'DR': 0b000
                    }
    Ch1Parms = {'MUX': 0}
    Ch2Parms = {'MUX': 7}

    def __init__(self, bus):
        self.Config = config.load()
        self.ID = None
        self.Handle = None
        self.Status = "absent"
        self.Zero = 0
        self.Sign = 1
        self.Weight = 0
        self.Mean = runningmean.RunningMean(self.RunningMeanWidth)
        super().__init__(I2Cbus=bus, I2Caddr=self.I2Caddr, **self.GeneralParms)
        self.EEPROM = mc24aa025e48.EEPROM(bus, self.EEPROM_I2Caddr)

        self._LED = "SlowRed"  # fixme

    def connect(self):
        try:
            self.EEPROM.i2c_open()
            self.EEPROM.read_config()
            print("on bus ", self.I2Cbus, "found weighing ring ", self.ID)
            self.i2c_open()
            return True
        except ConnectionError:
            return False

    def stop(self):
        self.i2c_close()

    def initializeADC(self):
        try:
            self.reset()
            time.sleep(0.1)
            self.set_parms(**self.SetupParms)

            return True
        except pigpio.error:
            return False

    def read2(self):
        v1 = self.read(**self.Ch1Parms) / 0x01000000 / 0.0024 / 9.81 / 8 *1000
        v2 = self.read(**self.Ch2Parms) / 0x01000000 / 0.0024 / 9.81 / 8 *1000
        v = (v1 + v2)
        return v

    def read_weight(self, average=False, tempcomp=False,):
        if average:
            w = self.read2() * self.EEPROM.AdcGain + self.EEPROM.AdcOffset # fixme
        else:
            w = self.read2() * self.EEPROM.AdcGain + self.EEPROM.AdcOffset
        if tempcomp:
            w = w * self.EEPROM.AdcTemperatureGain + self.EEPROM.AdcTemperatureOffset
        self.Weight = w
        return w


