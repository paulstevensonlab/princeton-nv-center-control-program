# -*- coding: utf-8 -*-

from instruments import GPIBdev
# import GPIBdev # use when running this as a main


class SynthHD(GPIBdev.GPIBdev):
    'Dual Channel Signal Generator'
    def __init__(self, dev, ch=1):
        super().__init__(dev)

        self.pow_min = -60.
        self.pow_max = 20.  # Ophir can handle 10 dBm
        self.freq_min = 53.0e6
        self.freq_max = 13.9e9

        self.gpib_write('c1')
        self.gpib_write('x0')

        self.set_output(0)

    def set_freq(self, freq):
        # set generator frequency in Hz
        freq = float(freq)
        test = self.gpib_query('f?')
        print(test)
        if (float(freq) < self.freq_min) or (float(freq) > self.freq_max):
            print('Freq Range Error! Tried to set to %f' % freq)
        else:
            print('f{0:5.7f}'.format(freq))
            self.gpib_write('f{0:5.7f}'.format(freq*1e-6))
            self.gpib_write('l{0:5.7f}'.format(freq*1e-6))
            self.gpib_write('u{0:5.7f}'.format(freq*1e-6))

    def set_pow(self, pow):
        # set generator power in dBm
        pow = float(pow)
        if (pow < self.pow_min) or (pow > self.pow_max):
            print('Power Range Error! Tried to set to %f' % pow)
        else:
            self.gpib_write('W{0:2.3f}'.format(pow))
            self.gpib_write('[{0:2.3f}'.format(pow))
            self.gpib_write(']{0:2.3f}'.format(pow))

    def get_pow(self):
        retval = self.gpib_query('W?')
        print('get_pow',retval)
        pow_dbm = retval
        return pow_dbm

    def get_freq(self):
        retval = self.gpib_query('f?')
        freq = float(retval)*1e6
        return freq

    def set_output(self, b):
        if b:
            self.gpib_write('g1')
        else:
            self.gpib_write('g0')

    def get_output(self):
        retval = self.gpib_query('g?')
        if retval == '1':
            stateflag= 1
        else:
            stateflag = 0
        return float(stateflag)

    def set_mod(self, b):
        return

    # Note: IQ modulation and Burst modulation cannot be simultaneously active.
    def set_iqmod(self, b):
        pass

    def get_iqmod(self):
        return 0

    def set_mod_vector(self, b):
        return

    def get_mod_vector(self):
        return np.asarray([])

    def set_mod_burst(self, b):
        return

    def set_mod_burst_IQ(self, b):  # This should allow for bursting and switching between two states?
        return

    def set_IQ_x(self, i, q):
        return

    def set_IQ_y(self, i, q):
        return

    def gpib_write(self, str):
        super().gpib_write(str)
        # time.sleep(2)  # Wait for 2 seconds just to be safe. It's an old system.

    def set_alc(self, b):
        print('No ALC setting available on N9310A. This does nothing.')


# class SynthHD(GenericSource):
#     'SMATE200A Dual Channel Vector Signal Generator'
#     def __init__(self, dev, ch=1):
#         super().__init__(dev, ch)
#
#         self.pow_min = -60.
#         self.pow_max = 20  # Ophir can handle 10 dBm
#         self.freq_min = 14.e6
#         self.freq_max = 14.e9
#
#     '''Add vector modulation functions'''
#     def set_iqmod(self, b):
#         self.gpib_write('SOUR%d:IQ:STAT %d' % (self.ch, b))
#
#     def get_iqmod(self):
#         return int(self.gpib_query('SOUR%d:IQ:STAT?' % self.ch))

