from contextlib import suppress
import time
import struct

import blupio


class MC24AA025E48:
    """Microchip 24AA025E48 EEPROM with ID"""

    def __init__(self, I2Cbus, I2Caddr, retries=3, I2Cwait=0.02):
        self.I2Cbus = I2Cbus
        self.I2Caddr = I2Caddr
        self.Handle = None
        self.Retries = retries
        self.I2Cwait = I2Cwait
        self.pi = blupio.pi()

    def __enter__(self):
        print(self.i2c_open())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Closing I2C handle:", self.Handle)
        self.i2c_close()

    def i2c_open(self):
        self.Handle = self.pi.i2c_open(self.I2Cbus, self.I2Caddr)
        return True

    def i2c_close(self):
        with suppress(Exception): self.pi.i2c_close(self.Handle)
        self.Handle = None


    def read(self, addr, count):
        """reads 1 to 32 byte starting at address (0x00-0xFF)"""
        if count not in range(1, 33):
            raise ValueError("byte count must be 1 to 32")
        time.sleep(self.I2Cwait)
        num, data = self.pi.i2c_read_i2c_block_data(self.Handle, addr, count)
        return data

    def read_string(self, addr):
        """read length from addr and string of length from addr+1"""
        l = self.read_byte(addr)
        b = self.read(addr+1, l)
        s = b.decode('utf-8')
        # print("reading string from addr ", addr, "type", type(s), " : ", s)
        return s

    def read_float32(self, addr):
        """reads 4 bytes starting at addr and converts to float32"""
        data = self.read(addr, 4)
        f, = struct.unpack('<f', data)
        return f

    def read_byte(self, addr):
        """reads one byte from address (0x00-0xFF)"""
        data = self.read(addr, 1)
        b, = struct.unpack('<B', data)
        # print("reading byte from addr ", addr, " type ", type(b), " : ", b)
        return b

    def write(self, addr, data):
        """write bytearray (len 1-16) to address (0x00-0x7F)"""
        if len(data) not in range(1, 17):
            raise ValueError("byte count must be 1 to 16")
        self.pi.i2c_write_device(self.Handle, bytearray((addr,)) + bytearray(data))
        time.sleep(self.I2Cwait)

    def write_string(self, addr, s):
        """"write length to addr and string to addr+1 (length max 16)"""
        self.write_byte(addr, len(s))
        b = bytearray()
        b.extend(s[:16].encode('utf-8'))
        self.write(addr+1, b)

    def write_float32(self, addr, data):
        """write bytearray (len 1-16) to address (0x00-0x7F)"""
        self.write(addr, struct.pack('<f', data))

    def write_byte(self, addr, byte):
        """write one byte to address (0x00-0x7F)"""
        self.pi.i2c_write_device(self.Handle, bytearray((addr,)) + bytearray((byte,)))
        time.sleep(self.I2Cwait)

    def read_id(self):
        """returns unique 48bit ID of the EEPROM as hex string"""
        time.sleep(self.I2Cwait)
        num, ba_data = self.pi.i2c_read_i2c_block_data(self.Handle, 0xFA, 6)
        str_data = ''
        for i in range(len(ba_data)):
            str_data += "{:02X}".format(ba_data[i], )
        return str_data
