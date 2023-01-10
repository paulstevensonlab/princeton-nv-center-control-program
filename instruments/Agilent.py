# -*- coding: utf-8 -*-

import numpy as np

if __name__ == '__main__':
    import GPIBdev # use when running this as a main
    import instr_widget
    import GPIBdev_gui
else:
    from instruments import GPIBdev
    from instruments import GPIBdev_gui
    from instruments import instr_widget


class N9310A(GPIBdev.GPIBdev):
    '9310 signal generator class'

    def __init__(self, dev):
        super().__init__(dev)

        self.pow_min = -127
        self.pow_max = 10
        self.freq_min = 100e3
        self.freq_max = 3e9

        self.set_mod(0)
        self.set_iqmod(0)
        self.set_output(0)

    def set_freq(self, freq):
        # set generator frequency in Hz
        if (freq < self.freq_min) or (freq > self.freq_max):
            print('Freq Range Error! Tried to set to %f' % freq)
        else:
            self.gpib_write(':FREQ:CW %.6f Hz' % freq)

    def get_freq(self):
        return float(self.gpib_query(':FREQ:CW?'))

    def set_pow(self, pow):
        # set generator power in dBm
        if (pow < self.pow_min) or (pow > self.pow_max):
            print('Power Range Error! Tried to set to %f' % pow)
        else:
            self.gpib_write(':AMPL:CW %f' % pow)

    def get_pow(self):
        return float(self.gpib_query(':AMPL:CW?'))

    def set_mod(self, b):
        self.gpib_write(':MOD:STAT %d' % b)

    def set_output(self, b):
        self.gpib_write(':RFO:STAT %d' % b)

    def get_output(self):
        return int(self.gpib_query(':RFO:STAT?'))

    def set_alc(self, b):
        print('No ALC setting available on N9310A. This does nothing.')

    def set_pulsemod(self, b):
        print('External modulation on N9310A. This does nothing.')

    def set_pulsemod_src(self, src):
        print('External modulation on N9310A. This does nothing.')

    def set_iqmod(self, b):
        self.gpib_write(':IQ:STAT %d' % b)

    def get_iqmod(self):
        return int(self.gpib_query(':IQ:STAT?'))


class E8257D(GPIBdev.GPIBdev):
    'PSG signal generator class'

    def __init__(self, dev):
        # do nothing, maybe eventually do something
        super().__init__(dev)

        # limits of the device
        self.pow_min = -20
        self.pow_max = -5
        self.freq_min = 100e3
        self.freq_max = 20e9

        self.set_output(0)

    def set_freq(self, freq):
        # set generator frequency in Hz
        if (freq < self.freq_min) or (freq > self.freq_max):
            print('Freq Range Error! Tried to set to %f' % freq)
        else:
            self.gpib_write('SOUR:FREQ %.6f' % freq)

    def get_freq(self):
        return float(self.gpib_query('SOUR:FREQ?'))

    def set_pow(self, pow):
        # set generator power in dBm
        if (pow < self.pow_min) or (pow > self.pow_max):
            print('Power Range Error! Tried to set to %f' % pow)
        else:
            self.gpib_write('SOUR:POW %f' % pow)

    def get_pow(self):
        return float(self.gpib_query('SOUR:POW?'))

    def set_mod(self, b):
        self.gpib_write('OUTP:MOD %d' % b)

    def set_output(self, b):
        self.gpib_write('OUTP:STAT %d' % b)

    def set_alc(self, b):
        self.gpib_write('POW:ALC:STAT %d' % b)

    def set_pulsemod(self, b):
        self.gpib_write('PULM:STAT %d' % b)

    def set_pulsemod_src(self, src):
        self.gpib_write('PULM:SOUR ' + src)


class AWG33622A(GPIBdev.GPIBdev):
    'Keysight 33622A Function/Arbitrary Waveform Generator'

    def __init__(self, dev):
        super().__init__(dev)
        self.inst.timeout = 10000
        self.alias = ''  # alias is pb channel name

        # limits of the device
        self.vmin = -0.354
        self.vmax = +0.354

    def set_func(self, ch, fun):
        self.gpib_write('SOUR%d:FUNC %s' % (ch, fun))

    def set_alias(self, pb_chan):
        self.alias = pb_chan

    def set_freq(self, ch, freq):
        self.gpib_write('SOUR%d:FREQ %.3f' % (ch, freq))

    def set_amplitude(self, ch, amp):
        self.set_limits()
        self.gpib_write('SOUR%d:VOLT %.3f' % (ch, amp))

    def set_dc(self, ch, v):
        self.gpib_write('SOUR%d:VOLT:OFFS %.3f' % (ch, v))

    def set_amplitude_wfm(self, ch, low, high):
        # self.set_limits()
        if low == 0 and high == 0:
            self.gpib_write('SOUR%d:VOLT:LOW MIN' % (ch))
            self.gpib_write('SOUR%d:VOLT:HIGH MAX' % (ch))
        else:
            self.gpib_write('SOUR%d:VOLT:LOW %.3f' % (ch, low))
            self.gpib_write('SOUR%d:VOLT:HIGH %.3f' % (ch, high))

    def set_output(self, b):
        self.gpib_write('OUTP1 %d' % b)
        self.gpib_write('OUTP2 %d' % b)

    def set_gated(self, ch, b):
        self.gpib_write('SOUR%d:BURS:STAT %d' % (ch, b))
        if bool(b):
            self.gpib_write('SOUR%d:BURS:MODE GAT' % ch)
            self.gpib_write('SOUR%d:BURS:SOUR EXT' % ch)

    def set_triggered(self, ch, b):
        self.gpib_write('SOUR%d:BURS:STAT %d' % (ch, b))
        if bool(b):
            self.gpib_write('SOUR%d:BURS:MODE TRIG' % ch)
            self.gpib_write('SOUR%d:BURS:NCYC 1' % ch)
            self.gpib_write('TRIG%d:SOUR EXT' % ch)

    def set_wfm(self, ch, wfm, sampl=250e6):
        self.set_func(ch, 'ARB')
        self.gpib_write('SOUR%d:FUNC:ARB:SRAT %d' % (ch, sampl))
        self.gpib_write('SOUR%d:FUNC:ARB:FILT OFF' % ch)
        self.set_triggered(ch, 1)

        self.gpib_write('SOUR%d:DATA:VOL:CLE' % ch)

        wfm_array = np.array(wfm)

        header = 'SOUR%d:DATA:ARB wfm%d, ' % (ch, ch)

        self.gpib_write('FORMat:BORDer SWAP')

        # this function takes care of the binary block header by itself
        self.inst.write_binary_values(header, wfm_array)

        self.gpib_write('SOUR%d:FUNC:ARB wfm%d' % (ch, ch))

    def set_wfm_dual(self, wfm1, wfm2, sampl=250e6):
        # wfm is a list of float, normalized to 1
        self.set_wfm(1, wfm1, sampl)
        self.set_wfm(2, wfm2, sampl)

    def set_limits(self):
        self.gpib_write('SOUR1:VOLT:LIM:STAT 1')
        self.gpib_write('SOUR1:VOLT:LIM:LOW %f' % self.vmin)
        self.gpib_write('SOUR1:VOLT:LIM:HIGH %f' % self.vmax)
        self.gpib_write('SOUR2:VOLT:LIM:STAT 1')
        self.gpib_write('SOUR2:VOLT:LIM:LOW %f' % self.vmin)
        self.gpib_write('SOUR2:VOLT:LIM:HIGH %f' % self.vmax)

    def set_sequence(self, wfm_list, reps_list, name):
        # writes a sequence and set a proper command
        seq_cmd = '"%s"' % name

        if len(wfm_list) != len(reps_list):
            print('error')  # todo
        else:
            awg.gpib_write('DATA:VOLatile:CLE')

            for seq in range(len(wfm_list)):
                # <arb name>,<repeat count>,<play control>,<marker mode>,<marker point>
                wfm = wfm_list[seq]
                rep_count = reps_list[seq]
                play_control = 'repeat'
                # this shouldn't matter
                marker_mode = 'maintain'
                marker_point = 10

                # load waveform into memory
                awg.gpib_write('MMEM:LOAD:DATA "%s"' % wfm)
                seq_cmd += ',"%s",%d,%s,%s,%d' % (wfm, rep_count, play_control, marker_mode, marker_point)

            char_count = len(seq_cmd)
            n_digits = len(str(char_count))

            self.gpib_write('DATA:SEQ #%d%d%s' % (n_digits, char_count, seq_cmd))

    def get_error(self):
        err = self.gpib_query('SYST:ERR?')

        if '+0' in err:
            return ''
        else:
            error_all = ''
            max_err = 20  # maximum number of errors to read - prevent infinite loop
            itr = 0
            while '+0' not in err and itr < max_err:
                error_all += err
                err = self.gpib_query('SYST:ERR?')
                itr += 1
            if itr >= max_err:
                print('More than %d error messages occurred. You are probably doing something stupid...' % max_err)
            return error_all

    def set_view(self, mode):
        # mode: STANdard|TEXT|GRAPh|DUAL
        self.gpib_write('DISP:VIEW %s' % mode)


class E3633A(GPIBdev.GPIBdev):
    '8V 20A/25V 7A DC power supply class'

    def __init__(self, dev):
        super().__init__(dev)
        #self.inst.timeout = 10000
        # limits of the device
        self.vmin = +0
        self.vmax = +25
        self.imin = +0
        self.imax = +20

    def set_current(self, cur):
        self.gpib_write('CURR %s' % (cur))

    def get_current(self):
        curM = self.gpib_query('MEASure:CURRent?')
        return curM

    def set_voltage(self, vol):
        self.gpib_write('VOLT %s' % (vol))

    def get_voltage(self):
        voltM = self.gpib_query('MEASure:VOLTage?')
        return voltM

    def set_IV(self, cur, vol):
        self.gpib_write('APPLy %s, %s' % (vol, cur))

    def set_voltageOP(self, volOP):
        self.gpib_write('VOLTage:PROTection %s' % (volOP))

    def get_voltageOP(self):
        voltOP = self.gpib_query('VOLTage:PROTection?')
        return voltOP

    def set_output(self, outState):
        self.gpib_write('OUTPut %d' % outState)

    def set_limits(self):
        self.gpib_write('VOLTage:PROTection %f' % self.vmax)
        self.gpib_write('CURRent:PROTection %f' % self.imax)

    def btn_output(self):
        self.gpib_write('OUTPut ON')
        self.gpib_write("VOLTage:RANGe P8V")
        self.gpib_write("VOLTage:PROTection:STATe 1")

    def btn_reset(self):
        self.gpib_write('*RST')
        self.gpib_write("VOLTage:RANGe P8V")
        self.gpib_write("VOLTage:PROTection:STATe 1")


class E3633A_widget(instr_widget.GenericWidget, GPIBdev_gui.Ui_Form):
    def __init__(self, inst):
        super().__init__()
        self.setupUi(self)
        self.inst = inst

        self.btn_write.clicked.connect(self.write)
        self.btn_query.clicked.connect(self.query)

    def write(self):
        self.inst.gpib_write(self.linein_cmd.text())

    def query(self):
        self.linein_return.setText(self.inst.gpib_query(self.linein_cmd.text()))


if __name__ == '__main__':
    print('Agilent Test')

    # form.chkbox_tracktime.setChecked(False)
    # form.chkboxsave.setChecked(False)

    app.exec_()

    print('finished')
