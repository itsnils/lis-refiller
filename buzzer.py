import pigpio
import blupio


if __name__ == '__main__':
    pi = blupio.pi()
    pi.write(12, 0)