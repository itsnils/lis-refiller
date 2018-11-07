"""tmc5130 module docstring

        examples:
        
                import tmc5130
                m = tmc5130.Motor()
                m.moveby(relpos=-7000, speed=2000)
                -> turns the motor backwards 7000 microsteps at 2000 microsteps per second
                ->returns the motor position before the move

                import tmc5130
                p = tmc5130.Pump(51200)
                p.pump(vol=-10.5, flow=0.2) # pumpa 10.5 ml at 0.2 ml/s
"""

import struct
import time

import pigpio   
 
class Motor:
    """
    defines the TMC5130 stepper driver as an object
    """
        
    GSTAT = 0x01
    GCONF = 0x00
    CHOPCONF = 0x6C
    IHOLD_IRUN = 0x10
    RAMPMODE = 0x20 # 0: Position, 1: Right Turn, 2: Left Turn
    XACTUAL = 0x21
    VACTUAL = 0x22
    VSTART = 0x23 # < VSTOP, Default 0
    A1 = 0x24 # Acceleration VSTART->V1
    V1 = 0x25 # (0: disables V1, A1, D1)
    AMAX = 0x26 # Accelelation V1->VMAX
    VMAX = 0x27
    DMAX = 0x28 # Deceleration VMAX->V1
    D1 = 0x2A # Deceleration V1->VSTOP
    VSTOP = 0x2B # > VSTART, Default 10
    TZEROWAIT = 0x2C
    XTARGET = 0x2D

   
    def __init__(self):
        """
        initializes the TMC5130 according to the datasheet example for positioning
        """
        self.pi = pigpio.pi()
        self.h = self.pi.spi_open(0, 500000, 0b0000000000000000000011) # SPI mode 3, default for everything else
        self.Status = None
        self.Pos = None
        self.reg(self.GSTAT) # read GSTAT 0x01 to clear reset flag
        self.reg(self.GCONF,6)
        self.reg(self.CHOPCONF, 0x000100C5) # CHOPCONF 0x6C: TOFF=3, HSTRT=4, HEND=1, TBL=2, CHM=0 (spreadCycle)
        self.reg(self.IHOLD_IRUN, 0x00061C02) # IHOLD_IRUN 0x10: IHOLD=02, IRUN=31 (max. current), IHOLDDELAY=6
        self.reg(self.A1, 1000)
        self.reg(self.V1, 5000)
        self.reg(self.AMAX, 5000)
        self.reg(self.VMAX, 20000)
        self.reg(self.DMAX, 5000)
        self.reg(self.D1, 5000)
        self.reg(self.VSTOP, 10)        
        self.reg(self.RAMPMODE, 0) # RAMPMODE 0x20 = 0 (Target position move)

    def reg(self,
            regnum,
            val = None,
            signed = False
            ):        
        """ returns the current value of the register
            if a value is given, it is written to the register
            self.Status is updates with the current status byte
        """
        if signed:
            f = '>Bl' # format string for signed long
        else:
            f = '>BL' # format string for unsigned long
        if (val == None):
            # print("read", hex(regnum))
            self.pi.spi_xfer(self.h, struct.pack(f, regnum, 0)) # read
        else:
            # print("write", hex(regnum | 0x80), hex(val))
            self.pi.spi_xfer(self.h, struct.pack(f, regnum | 0x80, val))# write
        n, r = self.pi.spi_xfer(self.h, struct.pack(f, regnum, 0)) #r e-read to get current value
        self.Status, v = struct.unpack(f, r)
        # print(1, regnum, val, self.Status, v) # debug
        return v
       

    def move(self,
            relpos = None,  # [microsteps]
            abspos = None,  # [microsteps]
            speed = None    # [microstep/s]
             ):
        """ moves the motor to a relative or absolute position at the speed given
            updates self.Status with the current status byte
            returns the position before the move                    
        """
        # moves the motor and returns the status and the current position
        # all arguments are optional
        # if only speed [rotations/s] is given, the sign determines the direction
        # if abspos or relpos are given, the sign of the optional speed is ignored
        # if relpos is given, abspos is ignored
        self.Pos = self.reg(self.XACTUAL)
        if not relpos == None:
            self.reg(self.RAMPMODE, 0)
            if not speed == None:
                self.reg(self.VMAX, abs(speed))
            self.TargetPos = (self.Pos + relpos) % 2**32
            self.reg(self.XTARGET, self.TargetPos)
        elif not abspos == None:
            self.reg(self.RAMPMODE, 0)
            if not speed == None:
                self.reg(self.VMAX, abs(speed))
            self.TargetPos = abspos % 2**32
            self.reg(self.XTARGET, self.TargetPos)
        elif not speed == None:
            if speed < 0:
                self.reg(self.RAMPMODE, 2)
            else:
                self.reg(self.RAMPMODE, 1)
            self.reg(self.VMAX, abs(speed))
        return self.Pos

    def moveby(self,
            relpos = None,  # [microsteps]
            speed = None    # [microstep/s]
             ):
        """ moves the motor to a relative or absolute position at the speed given
            updates self.Status with the current status byte
            returns the position before the move                    
        """
        # moves the motor and returns the status and the current position
        # all arguments are optional
        # if only speed [rotations/s] is given, the sign determines the direction
        # if relpos is given, the sign of the optional speed is ignored
        self.Pos = self.reg(self.XACTUAL)
        if not relpos == None:
            self.reg(self.RAMPMODE, 0)
            if not speed == None:
                self.reg(self.VMAX, abs(speed))
            self.TargetPos = (self.Pos + relpos) % 2**32
            self.reg(self.XTARGET, self.TargetPos)
        elif not speed == None:
            if speed < 0:
                self.reg(self.RAMPMODE, 2)
            else:
                self.reg(self.RAMPMODE, 1)
            self.reg(self.VMAX, abs(speed))
        return self.Pos

    def moveto(self,
            abspos = None,  # [microsteps]
            speed = None    # [microstep/s]
             ):
        """ moves the motor to a relative or absolute position at the speed given
            updates self.Status with the current status byte
            returns the position before the move                    
        """
        # moves the motor and returns the status and the current position
        # all arguments are optional
        # if only speed [rotations/s] is given, the sign determines the direction
        # if abspos is given, the sign of the optional speed is ignored
        self.Pos = self.reg(self.XACTUAL)
        if abspos != None:
            self.reg(self.RAMPMODE, 0)
            if not speed == None:
                self.reg(self.VMAX, abs(speed))
            self.TargetPos = abspos % 2**32
            self.reg(self.XTARGET, self.TargetPos)
        elif not speed == None:
            if speed < 0:
                self.reg(self.RAMPMODE, 2)
            else:
                self.reg(self.RAMPMODE, 1)
            self.reg(self.VMAX, abs(speed))
        return self.Pos

    def status(self):
        """ updates self.Status with the current status byte and returns it
        """
        self.reg(self.XACTUAL)
        return self.Status
            
    def stopped(self):
        """ updates self.Status with the current status byte
            returns True if the motor is stopped
        """
        self.reg(self.XACTUAL) # some read command to update the status
        return ((self.Status & 0x08) > 0)

    def arrived(self):
        """ updates self.Status with the current status byte
            returns True if the motor is at the target position
        """
        self.reg(self.XACTUAL) # some read command to update the status
        return ((self.Status & 0x20) > 0)

    def stalled(self):
        """ updates self.Status with the current status byte
            returns True if ???
        """
        self.reg(self.XACTUAL) # some read command to update the status
        return ((self.Status & 0x04) > 0)

    def error(self):
        """ updates self.Status with the current status byte
            returns True if the error bit is set
        """
        self.reg(self.XACTUAL) # some read command to update the status
        return ((self.Status & 0x02) > 0)

    def resetoccured(self):
        """ updates self.Status with the current status byte
            returns True if a reset has occurred
        """
        self.reg(self.XACTUAL) # some read command to update the status
        return ((self.Status & 0x02) > 0)


class Pump(Motor):
    """ takes driver/micro steps per milliliter as an initialization argument
        (remains accessible as F)
    """
    def __init__(self, stepspermilliliter):
        """ initializes the TMC5130
            sets the volume/step conversion factor
            zeroes the positive and negative totals and the position
        """
        self.F = stepspermilliliter
        self.TotalP = 0
        self.TotalM = 0
        Motor.__init__(self)
        self.Oldpos = self.move(relpos=0)


