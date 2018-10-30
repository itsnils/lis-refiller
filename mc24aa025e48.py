import time
import json
import struct
import pigpio


class MC24AA025E48:
    """Microchip 24AA025E48 EEPROM with ID"""

    def __init__(self, I2Cbus, I2Caddr, retries = 3, I2Cwait = 0.01):
        self.I2Cbus = I2Cbus
        self.I2Caddr = I2Caddr
        self.Retries = retries
        self.I2Cwait = I2Cwait
        self.pi = pigpio.pi()

    def __enter__(self):
        print(self.i2c_open())
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Closing I2C handle:", self.Handle)
        self.i2c_close()

    def i2c_open(self):

        for i in range(self.Retries + 1):
            try:
                self.Handle = self.pi.i2c_open(self.I2Cbus, self.I2Caddr)
                return True
            except pigpio.error:
                print("Faild to open I2C bus ", self.I2Cbus, " address ", self.I2Caddr)
                if i >= self.Retries:
                    self.Handle = None
                    raise # ConnectionError(("couldn't close I2C bus " + self.I2Cbus))
                else:
                    time.sleep(self.I2Cwait)
                    continue

    def i2c_close(self):
        if self.Handle in range(255):
            for i in range(self.Retries+1):
                try:
                    self.pi.i2c_close(self.Handle)
                    self.Handle = None
                    return True
                except pigpio.error:
                    if i >= self.Retries:
                        self.Handle = None
                        raise # ConnectionError(("couldn't close I2C bus " + self.I2Cbus + " handle " + self.Handle))
                    else:
                        time.sleep(self.I2Cwait)
                        continue

    def read(self, addr, count):
        """reads 1 to 32 byte starting at address (0x00-0xFF)"""
        if count not in range(1, 33):
            raise ValueError("byte count must be 1 to 32")
        for i in range(self.Retries + 1):
            try:
                num, data = self.pi.i2c_read_i2c_block_data(self.Handle, addr, count)
                return data
            except pigpio.error:
                if i >= self.Retries:
                    raise # ConnectionError("could not read from I2C bus ", self.I2Cbus)
                else:
                    time.sleep(self.I2Cwait)
                    continue

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
        for i in range(self.Retries+1):
            try:
                self.pi.i2c_write_device(self.Handle, bytearray((addr,)) + bytearray(data))
                time.sleep(self.I2Cwait)
                return
            except pigpio.error:
                if i >= self.Retries:
                    raise # ConnectionError
                else:
                    time.sleep(self.I2Cwait)
                    continue

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
        num, ba_data = self.pi.i2c_read_i2c_block_data(self.Handle, 0xFA, 6)
        str_data = ''
        for i in range(len(ba_data)):
            str_data += "{:02X}".format(ba_data[i], )
        return str_data


class EEPROM(MC24AA025E48):

    def update(self, filepath='eeprom.json'):
        """updates eeprom.json from the current values, updates EEPROM with new values from eeprom.json if present"""
        with open(filepath, "r") as f:
            conf = json.load(f)
            id = self.read_id()
            if id in conf:
                self.write(0, b'xyz')  # write 'LIS' to addr 0-2
                for key in conf[id]:
                    addr, dtype = conf[id][key][0:2]
                    if dtype == "string":
                        conf[id][key][2] = self.read_string(addr)
                    elif dtype == "byte":
                        conf[id][key][2] = self.read_byte(addr)
                    elif dtype == "float32":
                        conf[id][key][2] = self.read_float32(addr)
                    if len(conf[id][key]) == 4:
                        addr, dtype, old, new = conf[id][key]
                        if dtype == "string" and len(new) in range(1,16):
                            self.write_string(addr,new)
                        elif dtype == "byte":
                            self.write_byte(addr, int(new))
                        elif dtype == "float32":
                            self.write_float32(addr, new)
                        conf[id][key].pop(-2)
                self.write(0, b'LIS')  # write 'LIS' to addr 0-2
        with open(filepath, "w") as f:
            json.dump(conf, f, indent=4)
        return json.dumps(conf, indent=4)

    def build_filekey_from_template(self,filepath='eeprom.json' ):
        with open(filepath, "r") as f:
            conf = json.load(f)
            id = self.read_id()
            if self.read(0x00, 3) == b'LIS':
                if id not in conf:
                    conf[id].update({})
                    for key in conf["template"]:
                        val = None
                        addr, dtype = conf["template"][key]
                        if dtype == "byte": val = self.read_byte(addr)
                        elif dtype == "string": val = self.read_string(addr)
                        elif dtype == "float32": val = self.read_float32(addr)
                        conf[id][key].update([addr, dtype, val])
            else:
                raise ValueError("EEPROM not initialized")
                pass

    def read_config(self):
        self.ID = self.read_id()
        if self.read(0x00,3) == b'LIS':   #check if address 0-2 contain 'LIS'
            self.RingType = self.read_byte(3)
            if self.RingType in range(1,1):
                self.AdcGain = self.read_float32(0x04)
                self.AdcOffset = self.read_float32(0x08)
                self.AdcTemperatureGain = self.read_float32(0x0C)
                self.AdcTemperatureOffset = self.read_float32(0x10)



if __name__ == '__main__':
    try:
        e = EEPROM(1, 0x51)
        e.i2c_open()
        print(e.read_id())
        print(e.update())
        # print(e.read_byte(3))
    finally:
        e.i2c_close()




