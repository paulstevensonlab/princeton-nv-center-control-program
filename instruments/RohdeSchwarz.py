# -*- coding: utf-8 -*-

from instruments import GPIBdev
# import GPIBdev # use when running this as a main


class GenericSource(GPIBdev.GPIBdev):
    'Dual Channel Signal Generator'
    def __init__(self, dev, ch=1):
        super().__init__(dev)

        self.pow_min = None
        self.pow_max = None
        self.freq_min = None
        self.freq_max = None

        self.ch = ch
        self.set_ch(ch)

    def set_ch(self, num):
        # set whether to use ch1 or ch2
        # todo: make special case for ch0 to be LF frequency?
        self.ch = num
        self.set_iqmod(0)
        self.set_output(0)

    def set_freq(self, freq):
        # set generator frequency in Hz
        if (freq < self.freq_min) or (freq > self.freq_max):
            print('Freq Range Error! Tried to set to %f' % freq)
        else:
            self.gpib_write('SOUR%d:FREQ %.6f Hz' % (self.ch, freq))

    def get_freq(self):
        return float(self.gpib_query('SOUR%d:FREQ:CW?' % self.ch))

    def set_pow(self, p):
        # set generator power in dBm
        if (p < self.pow_min) or (p > self.pow_max):
            print('Power Range Error! Tried to set to %f' % p)
        else:
            self.gpib_write('SOUR%d:POW %.2f' % (self.ch, p))

    def set_mod(self, b):
        # set_mod not available for RhodeSchwarz. Need to define a function for compatibility with mainexp
        pass

    def get_pow(self):
        return float(self.gpib_query('SOUR%d:POW?' % self.ch))

    def set_output(self, b):
        self.gpib_write('OUTP%d:STAT %d' % (self.ch, b))

    def get_output(self):
        return int(self.gpib_query('OUTP%d?' % self.ch))

    def set_alc(self, b):
        if type(b) == int:
            self.gpib_write('SOUR%d:POW:ALC %d' % (self.ch, b))
        else:
            self.gpib_write('SOUR%d:POW:ALC %s' % (self.ch, b))

    def set_pulsemod(self, b):
        self.gpib_write('SOUR%d:PULM:STAT %d' % (self.ch, b))
        self.gpib_write('SOUR%d:PULM:POL NORM' % self.ch)

    def get_pulsemod(self):
        return int(self.gpib_query('SOUR%d:PULM:STAT?' % self.ch))

    def set_pulsemod_src(self, src):
        # Set Pulse Modulation Source: EXT, INT
        self.gpib_write('SOUR%d:PULM:SRC %s' % (self.ch, src))

    def set_pulsemod_src(self):
        return self.gpib_query('SOUR%d:PULM:SRC?' % self.ch)

    def set_iqmod(self, b):
        pass

    def get_iqmod(self):
        return 0


class SMATE200A(GenericSource):
    'SMATE200A Dual Channel Vector Signal Generator'
    def __init__(self, dev, ch=1):
        super().__init__(dev, ch)

        self.pow_min = -145
        self.pow_max = 20  # Ophir can handle 10 dBm
        self.freq_min = 100e3
        self.freq_max = 6e9

    '''Add vector modulation functions'''
    def set_iqmod(self, b):
        self.gpib_write('SOUR%d:IQ:STAT %d' % (self.ch, b))

    def get_iqmod(self):
        return int(self.gpib_query('SOUR%d:IQ:STAT?' % self.ch))


class SMATE200A_1(SMATE200A):
    def __init__(self, dev):
        super().__init__(dev, ch=1)


class SMATE200A_2(SMATE200A):
    def __init__(self, dev):
        super().__init__(dev, ch=2)


class SMB100A(GenericSource):
    'SMB100A Analog Signal Generator'

    def __init__(self, dev, ch=1):
        super().__init__(dev, ch)

        self.pow_min = -20
        self.pow_max = 14
        self.freq_min = 100e3
        self.freq_max = 20e9


if __name__ == '__main__':
    print('R&S Test')

    mw = SMATE200A_1('SMATE200A')
    # mw.set_ch(1)
    mw2 = SMATE200A_2('SMATE200A')
    # mw2.set_ch(2)
    print('initialized')

    mw.set_freq(6e9)
    mw.set_pow(-100)
    mw.set_iqmod(0)
    mw.set_output(0)
    mw.set_alc('AUTO')

    mw2.set_freq(6e9)
    mw2.set_pow(-100)
    mw2.set_iqmod(0)
    mw2.set_output(0)

    print(mw.get_freq())
    print(mw.get_pow())
    print(mw.get_iqmod())
    print(mw.get_output())
    print('finished')
