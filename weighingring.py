import time
import statistics

from ads122c04 import ADS122C04  # 24-bit ADC TI ADS122C04
from eeprom import EEPROM
from runningmean import AdaptiveRunningMean
from refill_log import logger


class WeighingRing(ADS122C04):
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

    def __init__(self, side, config):
        logger.debug("WeighingRing.__init__()")
        self.Side = side
        self.Config = config
        self.ID = None
        self.Handle = None
        self.Weight = 0
        self.WeightAvg = 0
        self.Mean = AdaptiveRunningMean(minwidth=10, maxwidth=32, fup=0.6, fdown=0.4)
        super().__init__(I2Cbus=self.Config[self.Side]["I2cBus"], I2Caddr=self.I2Caddr, **self.GeneralParms)
        self.EEPROM = EEPROM(self.Config[self.Side]["I2cBus"], self.EEPROM_I2Caddr)
        self.Status = "absent"
        logger.debug("WeighingRing.__init__() done")

    def connect(self):
        self.EEPROM.i2c_open()
        self.i2c_open()
        try:
            self.reset()
            self.EEPROM.update()
            self.ID = self.EEPROM.read_device_specific_data()
        except ConnectionError:
            self.EEPROM.i2c_close()
            self.i2c_close()
            raise
        logger.info("on bus {} found weighing ring {}".format(str(self.I2Cbus), str(self.ID)))
        return True

    def stop(self):
        self.i2c_close()

    def initialize_adc(self):
            self.reset()
            time.sleep(0.1)
            self.set_parms(**self.SetupParms)

    def read2(self):
        v1 = self.read(**self.Ch1Parms) / 0x01000000 / 0.0024 / 9.81 / 8 * 1000 * 2
        v2 = self.read(**self.Ch2Parms) / 0x01000000 / 0.0024 / 9.81 / 8 * 1000 * 2
        v = (v1 + v2)
        return v

    def read_weight(self, average=False, tempcomp=False,):
        w = self.read2() * self.EEPROM.AdcGain + self.EEPROM.AdcOffset
        if tempcomp:
            w = w * self.EEPROM.AdcTemperatureGain + self.EEPROM.AdcTemperatureOffset
        self.Weight = w
        self.WeightAvg = self.Mean.do(w, func=statistics.median)
        if average:
            return self.WeightAvg
        else:
            return self.Weight
