import numpy as np
if __name__ == '__main__':
    import GPIBdev # use when running this as a main
else:
    from instruments import GPIBdev


class Model325(GPIBdev.GPIBdev):  # Updated by Peace. Cleaned up and remove unused functions. - 04/15/19
    def __init__(self, dev, ch=1):
        super().__init__(dev)

        # limits of the device
        self.temp_min = 1.0
        self.temp_max = 423  # Max temp of ST-400: 150C

        self.ch = ch

    def set_ch(self, ch):
        self.ch = ch

    def gpib_query(self, s):
        return super().gpib_query(s).split(';')[0]

    def set_temp_setpoint(self, t):
        self.gpib_write('SETP %d, %f' % (self.ch, t))

    def get_temp_setpoint(self):
        return float(self.gpib_query('SETP? %d' % self.ch))

    def get_temp(self):
        return float(self.gpib_query('KRDG? %s' % input))

    def get_sensor(self):
        return float(self.gpib_query('SRDG? %s' % input))

    def get_output(self):
        htr = float(self.gpib_query('HTR? %d' % self.ch))
        return htr

    def set_heater_mode(self, range):
        self.gpib_write('RANGE %d,%d' % (self.ch, range))

    def get_heater_mode(self):
        return int(self.gpib_query('RANGE? %d' % self.ch))
