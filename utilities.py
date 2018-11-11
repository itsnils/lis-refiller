

def rpi_temperature():
    """ returns the Raspberry Pi internal temperature sensor"""
    return int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1e3


if __name__ == '__main__':

    print("RPi Temperature", rpi_temperature(), "°C")