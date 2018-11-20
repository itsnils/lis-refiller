"""extension of MC24AA025E48 to handle device-specific condiguration data"""

import json

from mc24aa025e48 import MC24AA025E48


class EEPROM(MC24AA025E48):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.AdcGain = 1
        self.AdcOffset = 0
        self.AdcTemperatureGain = 1
        self.AdcTemperatureOffset = 0
        self.MaxWeight = 600
        self.MinWeight = 200
        self.ID = None
        self.RingType = None

    def update(self, filepath='/home/pi/Refiller/eeprom.json'):
        """updates eeprom.json from the current values, updates EEPROM with new values from eeprom.json if present"""
        with open(filepath, "r") as f:
            deviceSpecific = json.load(f)
            ringid = self.read_id()
            if ringid in deviceSpecific:
                self.write(0, b'xyz')  # write 'LIS' to addr 0-2
                for key in deviceSpecific[ringid]:
                    addr, dtype = deviceSpecific[ringid][key][0:2]
                    if dtype == "string":
                        deviceSpecific[ringid][key][2] = self.read_string(addr)
                    elif dtype == "byte":
                        deviceSpecific[ringid][key][2] = self.read_byte(addr)
                    elif dtype == "float32":
                        deviceSpecific[ringid][key][2] = self.read_float32(addr)
                    if len(deviceSpecific[ringid][key]) == 4:
                        addr, dtype, old, new = deviceSpecific[ringid][key]
                        if dtype == "string" and len(new) in range(1, 16):
                            self.write_string(addr, new)
                        elif dtype == "byte":
                            self.write_byte(addr, int(new))
                        elif dtype == "float32":
                            self.write_float32(addr, new)
                        deviceSpecific[ringid][key].pop(-2)
                self.write(0, b'LIS')  # write 'LIS' to addr 0-2
        # with open(filepath, "w") as f:
                # fixme json.dump(deviceSpecific, f, indent=4)
        return json.dumps(deviceSpecific, indent=4)

    def build_filekey_from_template(self, filepath='/home/pi/Refiller/eeprom.json'):
        """build eeprom.json key entry for hardware ID from EEPROM values and template"""
        with open(filepath, "r") as f:
            deviceSpecific = json.load(f)
            ringid = self.read_id()
            if self.read(0x00, 3) == b'LIS':
                if ringid not in deviceSpecific:
                    deviceSpecific[ringid].update({})
                    for key in deviceSpecific["template"]:
                        val = None
                        addr, dtype = deviceSpecific["template"][key]
                        if dtype == "byte":
                            val = self.read_byte(addr)
                        elif dtype == "string":
                            val = self.read_string(addr)
                        elif dtype == "float32":
                            val = self.read_float32(addr)
                        deviceSpecific[ringid][key].update([addr, dtype, val])
            else:
                raise ValueError("EEPROM not initialized")
                pass

    def read_device_specific_data(self, **kwargs):
        """read device-specific data from EEPROM"""
        self.__dict__.update(kwargs)  # make/update instance variables from all arguments, can be used to set defaults
        self.ID = self.read_id()
        if self.read(0x00, 3) == b'LIS':   # check if address 0-2 contain 'LIS'
            self.RingType = self.read_byte(3)
            if self.RingType >= 1:
                self.AdcGain = self.read_float32(4)
                self.AdcOffset = self.read_float32(8)
                self.AdcTemperatureGain = self.read_float32(12)
                self.AdcTemperatureOffset = self.read_float32(16)
                self.MaxWeight = self.read_float32(32)
            if self.RingType >= 2:
                pass  # assignments for future versions
        return self.ID


if __name__ == '__main__':
    for i in range(2):
        try:
            e = EEPROM(i, 0x51)
            e.i2c_open()
            print("id: ", i, e.read_id())
            print("update(): ", e.update())
            print("read_device_specific_data(): ", e.read_device_specific_data())
            # print(e.read_byte(3))
        finally:
            e.i2c_close()
