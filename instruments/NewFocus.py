from instruments import DAQmxAnalogInput, DAQmxAnalogOutput
import time


class TLB6700:
    'laser'

    def __init__(self, dev):
        self.coarse_ai = None
        self.coarse_ao = None
        self.piezo_ao = None

        self.piezo_v = 0.0

        self.scale = 1.0
        self.offset = 0.0

    def set_coarse_input(self, ai):
        self.coarse_ai = DAQmxAnalogInput.DAQmxAnalogInput(ai)

    def set_coarse_output(self, ao):
        self.coarse_ao = DAQmxAnalogOutput.DAQmxAnalogOutput(ao)

    def set_piezo_output(self, ao):
        self.piezo_ao = DAQmxAnalogOutput.DAQmxAnalogOutput(ao)

    def set_piezo(self, v):
        self.piezo_ao.set_voltage(v)
        self.piezo_v = v

    def get_piezo(self):
        return self.piezo_v

    def set_scale(self, s):
        self.scale = eval(str(s))

    def set_offset(self, s):
        self.offset = eval(str(s))

    def set_coarse(self, v):
        self.coarse_ao.set_voltage(v)
        self.coarse_v = v

    def get_coarse(self):
        return self.coarse_v

    def set_voltage(self, v):
        self.piezo_ao.set_voltage(v)
        self.piezo_v = v

    def setWavelengthCoarse(self, lamb):
       return self.set_coarse((lamb-940.0)/5)

    def setTrack(self, tracking):
        if tracking == True:
            self.gpib_write('OUTPut:TRACk 1')
        else:
            self.gpib_write('OUTPut:TRACk 0')


class TLB6701(TLB6700):

    def __init__(self, addr):
        super().__init__(addr)

        self.mainexp = None

        self.pid = PID(0.05, 0, 0)
        self.pid.SetPoint = 0.0
        self.pid.setSampleTime(0.01)

    def set_piezo(self, v):
        # For the ctl laser wit wavemeter, us this set_piezo to roughly set the frequency (GHz).
        # For voltage conversion 17V/V, we could use -4 ~4 V for 60 GHz. which means 0.133V per GHz.
        print('set piezo to:')
        if v >= 4:
            print('voltage at upper bound for the laser, set to 4V')
            self.piezo_ao.set_voltage(4)
            self.piezo_v = 4
        elif v <= -4:
            print('voltage at lower bound for the laser, set to -4V')
            self.piezo_ao.set_voltage(-4)
            self.piezo_v = -4
        else:
            self.piezo_ao.set_voltage(v)
            self.piezo_v = v
            print(self.piezo_v)

    def get_freq(self):
        if self.mainexp is not None:
            if self.mainexp.wavemeter.isconnected:
                return self.mainexp.wavemeter.getLambda()
            else:
                print('Wavemter is not connected, can not get frequency')
                return 0
        else:
            raise RuntimeError('mainexp is not defined in TLB6701')

    def set_freq(self, freq):
        if self.mainexp is not None:
            if self.mainexp.wavemeter.isconnected:
                self.pid.SetPoint = freq
                current_freq = self.get_freq()
                print('current_freq before feedback is %f, current_voltage is %f', current_freq, self.get_piezo())
                freqtol = 0.02
                escape = False
                itr = 1
                itrMax = 100
                while escape == False:
                    self.pid.update(current_freq)
                    output = self.pid.output
                    current_voltage = self.get_piezo()
                    next_voltage = current_voltage + output
                    if next_voltage > 4:
                        self.set_voltage(4)
                        escape = True
                        print('Voltage at upper bond, stop wm feedback')
                    elif next_voltage < -4:
                        self.set_voltage(-4)
                        escape = True
                        print('Voltage at lower bond, stop wm feedback')
                    else:
                        self.set_voltage(next_voltage)
                        time.sleep(0.2)
                    itr = itr + 1
                    if itr >= itrMax:
                        print('Reach maxitr, stop wm feedback')
                        escape = True
                    current_freq = self.get_freq()
                    if abs(freq - current_freq) < freqtol:
                        #print('Laser frequency set to %f', current_freq)
                        escape = True
            else:
                print('wavemeter is not connected, can not set freq')

        else:
            raise RuntimeError('mainexp is not defined in TLB6701')


class PID:
    """PID Controller for laser frequency feedback.
    """

    def __init__(self, P=0.2, I=0.0, D=0.0):

        self.Kp = P
        self.Ki = I
        self.Kd = D

        self.sample_time = 0.00
        self.current_time = time.time()
        self.last_time = self.current_time

        self.clear()

    def clear(self):
        """Clears PID computations and coefficients"""
        self.SetPoint = 0.0

        self.PTerm = 0.0
        self.ITerm = 0.0
        self.DTerm = 0.0
        self.last_error = 0.0

        # Windup Guard
        self.int_error = 0.0
        self.windup_guard = 20.0

        self.output = 0.0

    def update(self, feedback_value):
        """Calculates PID value for given reference feedback
        .. math::
            u(t) = K_p e(t) + K_i \int_{0}^{t} e(t)dt + K_d {de}/{dt}
        .. figure:: images/pid_1.png
           :align:   center
           Test PID with Kp=1.2, Ki=1, Kd=0.001 (test_pid.py)
        """
        error = self.SetPoint - feedback_value

        self.current_time = time.time()
        delta_time = self.current_time - self.last_time
        delta_error = error - self.last_error

        if delta_time >= self.sample_time:
            self.PTerm = self.Kp * error
            # self.ITerm += error * delta_time # not sure why it was +=
            self.ITerm = error * delta_time

            if self.ITerm < -self.windup_guard:
                self.ITerm = -self.windup_guard
            elif self.ITerm > self.windup_guard:
                self.ITerm = self.windup_guard

            self.DTerm = 0.0
            if delta_time > 0:
                self.DTerm = delta_error / delta_time

            # Remember last time and last error for next calculation
            self.last_time = self.current_time
            self.last_error = error

            self.output = self.PTerm + (self.Ki * self.ITerm) + (self.Kd * self.DTerm)

    def setKp(self, proportional_gain):
        """Determines how aggressively the PID reacts to the current error with setting Proportional Gain"""
        self.Kp = proportional_gain

    def setKi(self, integral_gain):
        """Determines how aggressively the PID reacts to the current error with setting Integral Gain"""
        self.Ki = integral_gain

    def setKd(self, derivative_gain):
        """Determines how aggressively the PID reacts to the current error with setting Derivative Gain"""
        self.Kd = derivative_gain

    def set_windup(self, windup):
        """Integral windup, also known as integrator windup or reset windup,
        refers to the situation in a PID feedback controller where
        a large change in setpoint occurs (say a positive change)
        and the integral terms accumulates a significant error
        during the rise (windup), thus overshooting and continuing
        to increase as this accumulated error is unwound
        (offset by errors in the other direction).
        The specific problem is the excess overshooting.
        """
        self.windup_guard = windup

    def setSampleTime(self, sample_time):
        """PID that should be updated at a regular interval.
        Based on a pre-determined sampe time, the PID decides if it should compute or return immediately.
        """
        self.sample_time = sample_time

# if __name__ == '__main__':
#     print('USB TLB Test')
#
#     # import ctypes
#     # import numpy as np
#
#     # tlb = ctypes.cdll.LoadLibrary('usbdll.dll')
#     #
#     # print(tlb.newp_usb_init_system())
#     # # print(tlb.newp_usb_uninit_system())
#     # # a = bytes()
#     # #
#     # # print(tlb.newp_usb_get_device_info(a))
#     # # print(a)
#     # arInst = np.array([], dtype=np.int)
#     # arInstMod = np.array([], dtype=np.int)
#     # arInstSN = np.array([], dtype=np.int)
#     # n = 0
#     # print(tlb.GetInstrumentList(arInst, arInstMod, arInstSN, n))
#     # # print(arInst)
#     #
#
#     import clr
#     clr.AddReference('UsbDllWrap')
#
#     import Newport.USBComm
#
#     tlb = Newport.USBComm.USB()
#     tlb.EventInit(0)
#     print(tlb.OpenDevices())
#     print(tlb.GetDevInfoList())
#     print(tlb.GetDeviceTable())
