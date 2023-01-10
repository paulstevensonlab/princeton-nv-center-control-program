# -*- coding: utf-8 -*-

import pyvisa as visa

class SG384:
    def __init__(self, addr):
        print('Initializing SRS SG384...')
        # Connect with the device
        rm = visa.ResourceManager()
        self.inst = rm.open_resource(addr)  # you can find the address from NI MAX

        self.freq_min = 950e3
        self.freq_max = 4.05e9
        self.pow_min = -110
        # self.pow_max = 16.5
        self.pow_max = 10.5 # lowered for the amplifier: Mini-circuits ZHL-16W-43-S+

    def SRSerrCheck(self):
        err = self.inst.query('LERR?')
        if int(err) is not 0:
            print('SRS error: error code', int(err), '. Please refer to SRS manual for a description of error codes.')
            quit()

    def set_output(self, b):
        self.inst.write('ENBR %d' % b)
        self.SRSerrCheck()

    def get_output(self):
        return int(self.inst.query('ENBR?'))

    def enableSRS_RFOutput(self):
        self.inst.write('ENBR 1')
        self.SRSerrCheck()

    def disableSRS_RFOutput(self):
        self.inst.write('ENBR 0')
        self.SRSerrCheck()

    def set_pow(self, p):
        # set generator power in dBm
        if (p < self.pow_min) or (p > self.pow_max):
            print('Power Range Error! Tried to set to %f' % p)
        else:
            self.inst.write('AMPR ' + str(p) + ' ' + 'dBm')
            self.SRSerrCheck()

    def get_pow(self):
        return float(self.inst.query('AMPR?'))

    def set_freq(self, freq):
        # setSRSFreq: Sets frequency of the SRS output. The frequency is in Hertz.
        # arguments: - freq: float setting frequency of self.inst.
        #            - units: string describing units (e.g. 'MHz'). For SRS384, minimum unit is 'Hz', max 'GHz'
        if (freq < self.freq_min) or (freq > self.freq_max):
            print('Freq Range Error! Tried to set to %f' % freq)
        else:
            self.inst.write('FREQ ' + str(freq) + ' ' + 'Hz')
        self.SRSerrCheck()

    def get_freq(self):
        return float(self.inst.query('FREQ?'))

    def set_mod(self, b):
        self.SRSerrCheck()
        # Enable modulation
        self.inst.write('MODL %d' % b)
        self.SRSerrCheck()

    def set_iqmod(self, b):
        self.SRSerrCheck()
        # Enable modulation
        self.inst.write('MODL %d' % b)
        self.SRSerrCheck()
        # Set modulation type to IQ
        self.inst.write('TYPE 6')
        self.SRSerrCheck()
        # Set IQ modulation function to external
        self.inst.write('QFNC 5')

    def enableIQmodulation(self):
        self.SRSerrCheck()
        # Enable modulation
        self.inst.write('MODL 1')
        self.SRSerrCheck()
        # Set modulation type to IQ
        self.inst.write('TYPE 6')
        self.SRSerrCheck()
        # Set IQ modulation function to external
        self.inst.write('QFNC 5')

    def disableModulation(self):
        self.inst.write('MODL 0')
        self.SRSerrCheck()

    def get_iqmod(self):
        status = self.inst.query('MODL?')
        self.SRSerrCheck()
        if status == '1\r\n':
            print('SRS modulation is on...')
            IQstatus = self.inst.query('TYPE?')
            self.SRSerrCheck()
            if IQstatus == '6\r\n':
                print('...and is set to IQ')
            else:
                print('...but is not set to IQ.')
        else:
            print('SRS modulation is off.')
        return status



if __name__ == '__main__':
    print('SRS SG384 Test')

    mw1 = SG384('TCPIP0::169.254.209.144::inst0::INSTR')
    print('initialized')
    mw1.setSRS_Freq(2e6)
    mw1.setSRS_RFAmplitude(-100)
    mw1.queryModulationStatus()
    print('finished')
