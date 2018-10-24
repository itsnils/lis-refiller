"""Datasheet URL http://www.ti.com/lit/ds/symlink/ads122c04.pdf """

import pigpio
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

    def __init__(self, I2Cbus, I2Caddr, **kwargs):
        self.pi = pigpio.pi()
        self.Status = "absent"
        self.I2Cbus = I2Cbus
        self.I2Caddr = I2Caddr
        self.SetupParms = kwargs

    def __enter__(self):
        self.i2c_open()
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.i2c_close()

    def i2c_open(self):
        try:
            self.Handle = self.pi.i2c_open(self.I2Cbus, self.I2Caddr)
            # print("Openend I2C bus ", self.I2Cbus, " address ", self.I2Caddr, " at handle ", self.Handle)  # fixme
            return True
        except pigpio.error:
            # print("pigpio.error: ", pigpio.error)  # fixme
            # print("Faild to open I2C bus ", self.I2Cbus, " address ", self.I2Caddr)  # fixme
            self.Handle = None
            raise ConnectionError

    def i2c_close(self):
        try:
            self.pi.i2c_close(self.Handle)
        except pigpio.error:
            pass

    def read(self, **kwargs):
        """single ADC read operation"""
        try:
            self.set_parms(**kwargs)
            self.start()
            time.sleep(0.01)
            while not self.parm('DRDY'):
                # print("waiting for DRDY") fixme
                time.sleep(0.01)
            c, r = self.pi.i2c_read_i2c_block_data(self.Handle, 0x10, 3)
            val = int.from_bytes(r, "big", signed=True)
            return val
        #except pigpio.error:
        except TypeError:
            print('pigpio.error : ', pigpio.error) #fixme
            raise

    def read_t(self):
        """read ADC internal temp sensor"""
        self.Temperature = self.read(TS=1)
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
            cmd =  0x20 | (regnum << 2)   # assemble read command byte
            currentbyte = self.pi.i2c_read_byte_data(self.Handle, cmd)
            if val != None:
                # print("setting ", name, " to ", val) fixme
                newbyte = (currentbyte & ~mask) | (val << bitpos)
                cmd = 0x40 | (regnum << 2)  # assemble write command byte
                self.pi.i2c_write_byte_data(self.Handle, cmd, newbyte)
                # print(hex(cmd), hex(newbyte)) fixme
            return  (currentbyte & mask) >> bitpos   # extract value read

    def reset(self):
        self.pi.i2c_write_byte(self.Handle, 0x06) # Reset

    def start(self):
        self.pi.i2c_write_byte(self.Handle, 0x08)  # Start/Sync

    def sync(self):
        self.start()



