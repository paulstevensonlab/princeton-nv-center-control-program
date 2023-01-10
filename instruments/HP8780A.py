from instruments import GPIBdev


class HP8780A(GPIBdev.GPIBdev):
    'HP8780A Vector Signal Generator Class'
    'This instrument uses an obsolete HP-IB language.'

    def __init__(self, dev):
        # do nothing, maybe eventually do something
        super().__init__(dev)

        # limits of the device
        self.pow_min = -110
        self.pow_max = 10 # Ophir can handle 10 dBm  # don't use more than -10 with the DEER amp. Instrument max +10 dBm
        self.freq_min = 10e6
        self.freq_max = 3e9

        self.set_output(0)


    def set_freq(self, freq):
        # set generator frequency in Hz
        if (freq < self.freq_min) or (freq > self.freq_max):
            print('Freq Range Error! Tried to set to %f' % freq)
        else:
            self.gpib_write('FR %d HZ' % freq)

    def set_pow(self, pow):
        # set generator power in dBm
        if (pow < self.pow_min) or (pow > self.pow_max):
            print('Power Range Error! Tried to set to %f' % pow)
        else:
            self.gpib_write('LV %.3f DBM' % pow)

    def get_pow(self):
        retval = self.gpib_query('LP1')
        start = retval.find('LV') + 2
        end = retval.find('DBM')
        return float(retval[start:end])

    def get_freq(self):
        retval = self.gpib_query('LP1')
        start = retval.find('FR') + 2
        end = retval.find('HZ')
        return float(retval[start:end])

    def set_output(self, b):
        self.gpib_write('RF%d' % b)

    def get_output(self):
        retval = self.gpib_query('LP1')
        start = retval.find('RF') + 2
        end = retval.find('RF') + 3
        return float(retval[start:end])

    def set_mod(self, b):
        self.set_mod_burst(b)

    # Note: IQ modulation and Burst modulation cannot be simultaneously active.
    def set_mod_vector(self, b):
        self.gpib_write('VM%d' % b)

    def get_mod_vector(self):
        retval = self.gpib_query('LP1')
        start = retval.find('VM') + 2
        end = retval.find('VM') + 3
        return float(retval[start:end])

    def set_mod_burst(self, b):
        self.gpib_write('BR%d' % b)
        self.gpib_write('IPI 3 EN')  # invert the burst input so Lo = Off

    def set_mod_burst_IQ(self, b):  # This should allow for bursting and switching between two states?
        self.gpib_write('BR%d' % b)
        self.gpib_write('IPI 3 EN')  # invert the burst input so Lo = Off
        self.gpib_write('TS%d' % b)

    def set_IQ_x(self, i, q):
        self.gpib_write('IO %.3f EN' % i)
        self.gpib_write('QO %.3f EN' % q)

    def set_IQ_y(self, i, q):
        self.gpib_write('IT %.3f EN' % i)
        self.gpib_write('QT %.3f EN' % q)

    def gpib_write(self, str):
        super().gpib_write(str)
        # time.sleep(2)  # Wait for 2 seconds just to be safe. It's an old system.

    def set_alc(self, b):
        print('No ALC setting available on N9310A. This does nothing.')
