import pigpio
import blupio

pi = blupio.pi()

pin = 12
wave =[
    pigpio.pulse(1<<pin, 0, 200e3),
    pigpio.pulse(0, 1<<pin, 800e3),
    pigpio.pulse(1<<pin, 0 )
    ]

if __name__ == '__main__':
    pi = blupio.pi()
    pi.write(12, 0)