# -*- coding: utf-8 -*-

from instruments import GPIBdev
# import GPIBdev # use when running this as a main
import time


class GRF5022A(GPIBdev.GPIBdev):
    'Ophir Amplifier'
    def __init__(self, dev):
        # do nothing, maybe eventually do something
        super().__init__(dev)

        self.set_mode('VVA')
        self.set_output(0)

    def set_mode(self, m):
        self.gpib_write('MODE %s' % m)

    # def get_mode(self):
    #     return self.gpib_query('MODE?')

    def set_output(self, b):
        if bool(b):
            self.gpib_write('ONLINE')
        else:
            self.gpib_write('STANDBY')

    # def get_output(self):
    #     if 'ONLINE' in self.get_mode():
    #         return 1
    #     else:
    #         return 0

    def set_gain(self, g):
        self.gpib_write('VVA_LEVEL %.1f' % g)

    # def get_gain(self):
    #     lvl = self.gpib_query('VVA_LEVEL?')
    #     return float(lvl[0:-3])

    def set_vswr(self, v):
        self.gpib_write('VSWR_ALARM %.1f' % v)

    # def get_vswr(self):
    #     return self.gpib_query('VSWR_ALARM?')

    # def get_error(self):
    #     return self.gpib_query('FAULTS?')

    def clear_error(self):
        self.gpib_write('ACK_FAULTS')

    def gpib_write(self, str):
        super().gpib_write(str)
        time.sleep(0.1)

if __name__ == '__main__':
    print('Ophir Test')
    amp = GRF5022A('GPIB0::5::INSTR')
    amp.set_gain(100.0)
    amp.set_vswr(2)
    # print(amp.get_mode())

    print('finished')



