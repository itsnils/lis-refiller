import pigpio
from contextlib import suppress

pi = pigpio.pi()

for i in range(25,127):
    print(i)
    with suppress(Exception): pi.i2c_close(i)
    with suppress(Exception): pi.spi_close(i)