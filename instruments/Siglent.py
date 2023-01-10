from instruments import GPIBdev
import numpy as np



class SDG6022X_RF(GPIBdev.GPIBdev):
    'SDG6022X AWG RF Output only Class'

    def __init__(self, dev):
        # do nothing, maybe eventually do something
        super().__init__(dev)

        # limits of the device
        self.pow_min = -110
        self.pow_max = 33
        self.freq_min = 1.
        self.freq_max = 200.e6

        self.gpib_write('C1:BSWV WVTP,SINE')
        self.set_output(0)


    def set_freq(self, freq):
        # set generator frequency in Hz
        if (freq < self.freq_min) or (freq > self.freq_max):
            print('Freq Range Error! Tried to set to %f' % freq)
        else:
            self.gpib_write('C1:BSWV FRQ,%d' % freq)

    def set_pow(self, pow):
        # set generator power in dBm
        if (pow < self.pow_min) or (pow > self.pow_max):
            print('Power Range Error! Tried to set to %f' % pow)
        else:
            # Assume 50 Ohm load
            pow_Vpp = np.sqrt(np.power(10,pow/10)*1e-3*50)
            self.gpib_write('C1:BSWV AMP, %.3f' % pow_Vpp)

    def get_pow(self):
        retval = self.gpib_query('C1:BSWV?')
        start = retval.find('AMP,')+4
        end = retval.find('V,AMPVRMS')
        Vpp = float(retval[start:end])
        pow_dbm = 10*np.log10((Vpp**2/50)*1e3)
        return pow_dbm

    def get_freq(self):
        retval = self.gpib_query('C1:BSWV?')
        start = retval.find('FRQ,') + 4
        end = retval.find('HZ,')
        freq = float(retval[start:end])
        return freq

    def set_output(self, b):
        if b:
            flag = 'ON'
            self.gpib_write('C1:OUTP '+flag)
        else:
            flag = 'OFF'
            self.gpib_write('C1:OUTP ' + flag)

    def get_output(self):
        retval = self.gpib_query('C1:OUTP?')
        start = retval.find('OUTP ')
        end = retval.find('OUTP ') + 2
        if retval[start:end] == 'ON':
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
