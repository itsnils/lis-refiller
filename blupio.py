import time
from refill_log import logger

import pigpio

retries = 3
wait = 0.01


def retry(func):
    def wrapper(*args, **kwargs):
        for i in range(retries+1):
            try:
                return func(*args, **kwargs)
            except pigpio.error:
                pi.error_count += 1
                if i >= retries:
                    # logger.error("I2C transmission error, giving up, function {}, count# {:d}".format(str(func.__name__), pi.error_count))
                    raise ConnectionError
                else:
                    # logger.warning("I2C transmission error, retry# {:d}, count# {:d}".format(i+1, pi.error_count))
                    time.sleep(wait)
                    continue
    return wrapper

class pi(pigpio.pi):

    error_count = 0

    @retry
    def i2c_write_device(self, handle, data):
        return super().i2c_write_device(handle, data)

    @retry
    def i2c_read_i2c_block_data(self, handle, reg, count):
        return super().i2c_read_i2c_block_data(handle, reg, count)

    @retry
    def i2c_write_byte(self, handle, byte_val):
        return super().i2c_write_byte(handle, byte_val)

    @retry
    def i2c_write_byte_data(self, handle, reg, byte_val):
        return super().i2c_write_byte_data(handle, reg, byte_val)

    @retry
    def i2c_read_byte_data(self, handle, reg):
        return super().i2c_read_byte_data(handle, reg)

    def i2c_open(self, i2c_bus, i2c_address, i2c_flags=0):
        return super().i2c_open(i2c_bus, i2c_address, i2c_flags=0)

    def i2c_close(self, handle):
        return super().i2c_close(handle)



