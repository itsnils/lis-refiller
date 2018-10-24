import time
import pigpio

class MC24AA025E48:
    """Microchip 24AA025E48 EEPROM with ID"""

    def __init__(self, I2Cbus, I2Caddr):
        self.I2Cbus = I2Cbus
        self.I2Caddr = I2Caddr
        self.pi = pigpio.pi()

    def __enter__(self):
        print(self.i2c_open())
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Closing I2C handle:", self.Handle)
        self.i2c_close()

    def i2c_open(self):
        try:
            self.Handle = self.pi.i2c_open(self.I2Cbus, self.I2Caddr)
            return True
        except pigpio.error:
            print("pigpio.error: ", pigpio.error)
            print("Faild to open I2C bus ", self.I2Cbus, " address ", self.I2Caddr)
            self.Handle = None
            raise(ConnectionError)

    def i2c_close(self):
        try:
            self.pi.i2c_close(self.Handle)
        except pigpio.error:
            pass

    def read(self, addr, count):
        """reads 1 to 32 byte starting at address (0x00-0xFF)"""
        if count not in range(1, 33):
            raise ValueError("byte count must be 1 to 32")
        num, data = self.pi.i2c_read_i2c_block_data(self.Handle, addr, count)
        return data

    def read_byte(self, addr):
        """reads one byte from address (0x00-0xFF)"""
        num, data = self.pi.i2c_read_i2c_block_data(self.Handle, addr, 1)
        return data[0]

    def write(self, addr, data):
        """write bytearray (len 1-16) to address (0x00-0x7F)"""
        if len(data) not in range(1, 17):
            raise ValueError("byte count must be 1 to 16")
        self.pi.i2c_write_device(self.Handle, bytearray((addr,)) + bytearray(data))
        time.sleep(0.001)

    def write_byte(self, addr, byte):
        """write one byte to address (0x00-0x7F)"""
        self.pi.i2c_write_device(self.Handle, bytearray((addr,)) + bytearray((byte,)))
        time.sleep(0.01)

    def read_id(self):
        """returns unique 48bit ID of the EEPROM as hex string"""
        num, ba_data = self.pi.i2c_read_i2c_block_data(self.Handle, 0xFA, 6)
        str_data = ''
        for i in range(len(ba_data)):
            str_data += "{:02X}".format(ba_data[i], )
        return str_data

"""
try:
    e = MC24AA025E48(1, 0x51)
    e.i2c_open()
    print(e.read_id())
    print(e.write_byte(0x65, 111))
    print(e.read_byte(0x65))
    print(e.read(0x45, 5))
finally:
    e.i2c_close()
"""



