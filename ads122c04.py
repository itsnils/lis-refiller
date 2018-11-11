"""Datasheet URL http://www.ti.com/lit/ds/symlink/ads122c04.pdf """
from contextlib import suppress
import blupio
import time


class ADS122C04:

    register = {'GAIN': (0, 1, 3),  # Register 0 datasheet P42
                'MUX': (0, 4, 4),
                'PGA_BYPASS': (0, 0, 1),  # END
                'DR': (1, 5, 3),  # Register 1 datasheet P43
                'MODE': (1, 4, 1),
                'CM': (1, 3, 1),
                'VREF': (1, 1, 2),
                'TS': (1, 0, 1),  # END
                'DRDY': (2, 7, 1),  # Register 2 datasheet P44
                'DCNT': (2, 6, 1),
                'CRC': (2, 4, 2),
                'BCS': (2, 3, 1),
                'IDAC': (2, 0, 3),  # END
                'I1MUX': (3, 5, 3),  # Register 3 datasheet P45
                'I2MUX': (3, 2, 3),
                'RESERVED': (3, 0, 2),  # END ??????????
                }

    def __init__(self, I2Cbus, I2Caddr, retries = 5, I2Cwait = 0.01, **kwargs):
        self.pi = blupio.pi()
        self.I2Cbus = I2Cbus
        self.I2Caddr = I2Caddr
        self.Handle = None
        self.Retries = retries
        self.I2Cwait = I2Cwait
        self.SetupParms = kwargs
        self.Temperature = None

    def i2c_open(self):
        self.Handle = self.pi.i2c_open(self.I2Cbus, self.I2Caddr)
        return True

    def i2c_close(self):
        with suppress(Exception): self.pi.i2c_close(self.Handle)
        self.Handle = None

    def read(self, **kwargs):
        """single ADC read operation"""
        self.set_parms(**kwargs)
        self.start()
        time.sleep(0.01)
        while not self.parm('DRDY'):
            # print("waiting for DRDY")
            time.sleep(0.01)
        c, r = self.pi.i2c_read_i2c_block_data(self.Handle, 0x10, 3)
        val = int.from_bytes(r, "big", signed=True)
        return val

    def read_t(self):
        """read ADC internal temp sensor"""
        a = self.read(TS=1)
        b = a >> 10
        if (b & 0b10000000000000):
            t = ((b - 1) ^ 0b11111111111111) * -0.03125
        else:
            t = b * 0.03125
        self.Temperature = t
        self.set_parms(TS=0)
        return self.Temperature

    def set_parms(self, **kwargs):

        for parm in kwargs:
            self.parm(parm, kwargs[parm])

    def parm(self, name, val=None):

        if name in self.register:
            regnum = self.register[name][0]   # register the parameter resides in
            bitpos = self.register[name][1]   # starting bit position (lsb)
            bitnum = self.register[name][2]   # number of bits
            mask = (1 << bitnum) - 1 << bitpos   # generate bitmask
            cmd = 0x20 | (regnum << 2)   # assemble read command byte
            currentbyte = self.pi.i2c_read_byte_data(self.Handle, cmd)
            if val is not None:
                # print("setting ", name, " to ", val)
                newbyte = (currentbyte & ~mask) | (val << bitpos)
                cmd = 0x40 | (regnum << 2)  # assemble write command byte
                self.pi.i2c_write_byte_data(self.Handle, cmd, newbyte)
            return (currentbyte & mask) >> bitpos   # extract value read

    def reset(self):
        self.pi.i2c_write_byte(self.Handle, 0x06)  # Reset

    def start(self):
        self.pi.i2c_write_byte(self.Handle, 0x08)  # Start/Sync

    def sync(self):
        self.start()


if __name__ == '__main__':
    bus = 0
    adc = ADS122C04(bus, I2Caddr=0x45)
    adc.i2c_open()
    try:
        while True:
            L, R, T = adc.read(GAIN=3, MUX=0), adc.read(GAIN=3, MUX=7), adc.read_t()
            print(L, R, T)
            # time.sleep(0.1)
    finally:
        adc.i2c_close()
