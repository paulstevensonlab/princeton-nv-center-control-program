from instruments import GPIBdev
import numpy as np
import time



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

class BK1688B(GPIBdev.GPIBdev):
    'Korad power supply class DC power supply class'

    def __init__(self, dev):
        super().__init__(dev, read_termination='\r', write_termination='\r')
        #self.inst.timeout = 10000
        # limits of the device
        self.vmin = +0
        self.vmax = +18
        self.imin = +0
        self.imax = +20
        print('Here')

    def set_current(self, cur):
        if cur<1.0:
            stradd = 'CURR00'
        elif cur<10.0:
            stradd = 'CURR0'
        else:
            stradd = 'CURR'
        cval = str(int(round(10*cur)))
        setstr = stradd+cval
        print(cur, setstr)
        self.gpib_query(setstr)

    def get_current(self):
        time.sleep(0.5)
        alldat = self.gpib_query('GETD')
        if alldat == 'OK':
            alldat = self.gpib_query('GETD')
        print(alldat)
        curM = alldat[4:8]
        return float(curM)/100.

    def set_voltage(self, vol):
        if vol < 1.0:
            stradd = 'VOLT00'
        elif vol<10.0:
            stradd = 'VOLT0'
        else:
            stradd = 'VOLT'
        vval = str(round(10*vol))
        setstr = stradd+vval
        self.gpib_query(setstr)

    def get_voltage(self):
        time.sleep(0.5)
        alldat = self.gpib_query('GETD')
        if alldat == 'OK':
            alldat = self.gpib_query('GETD')
        volM = alldat[0:4]
        return float(volM)/100.

    # def set_IV(self, cur, vol):
        # self.gpib_write('APPLy %s, %s' % (vol, cur))

    def set_voltageOP(self, volOP):
        return

    def get_voltageOP(self):
        # voltOP = self.gpib_query('VOLTage:PROTection?')
        return True

    def set_output(self, outState):
        return True
        # self.gpib_write('OUTPut %d' % outState)

    def set_limits(self):
        # self.gpib_write('VOLTage:PROTection %f' % self.vmax)
        # self.gpib_write('CURRent:PROTection %f' % self.imax)
        return

    def btn_output(self):
        # self.gpib_write('OUTPut ON')
        # self.gpib_write("VOLTage:RANGe P8V")
        # self.gpib_write("VOLTage:PROTection:STATe 1")
        return

    def btn_reset(self):
        # self.gpib_write('*RST')
        # self.gpib_write("VOLTage:RANGe P8V")
        # self.gpib_write("VOLTage:PROTection:STATe 1")
        return

class KA3005P(GPIBdev.GPIBdev):
    'Korad power supply class DC power supply class'

    def __init__(self, dev):
        super().__init__(dev)
        #self.inst.timeout = 10000
        # limits of the device
        self.vmin = +0
        self.vmax = +20
        self.imin = +0
        self.imax = +5
        print('Here')

    def set_current(self, cur):
        self.gpib_write('ISET1:%s' % (cur))

    def get_current(self):
        curM = self.gpib_query('ISET1?')
        return curM

    def set_voltage(self, vol):
        self.gpib_write('VSET1:%s' % (vol))

    def get_voltage(self):
        voltM = self.gpib_query('VSET1?')
        return voltM

    # def set_IV(self, cur, vol):
        # self.gpib_write('APPLy %s, %s' % (vol, cur))

    def set_voltageOP(self, volOP):
        return

    def get_voltageOP(self):
        # voltOP = self.gpib_query('VOLTage:PROTection?')
        return True

    def set_output(self, outState):
        return True
        # self.gpib_write('OUTPut %d' % outState)

    def set_limits(self):
        # self.gpib_write('VOLTage:PROTection %f' % self.vmax)
        # self.gpib_write('CURRent:PROTection %f' % self.imax)
        return

    def btn_output(self):
        # self.gpib_write('OUTPut ON')
        # self.gpib_write("VOLTage:RANGe P8V")
        # self.gpib_write("VOLTage:PROTection:STATe 1")
        return

    def btn_reset(self):
        # self.gpib_write('*RST')
        # self.gpib_write("VOLTage:RANGe P8V")
        # self.gpib_write("VOLTage:PROTection:STATe 1")
        return
