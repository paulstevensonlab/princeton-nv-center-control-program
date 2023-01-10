import PyDAQmx as pydaqmx
import numpy as np
import ctypes
import time

from instruments import DAQmxChannel


class DAQmxAnalogOutput(DAQmxChannel.DAQmxChannel):

    def __init__(self, dev, minval=-10, maxval=10):
        super().__init__(dev)

        self.minval = minval
        self.maxval = maxval
        self.volt_per_micron = 1
        self.offset = 0

        self.currentVoltage = 0.0
        self.lastSweepVoltage = 0.0

        self.create_task()

    def create_task(self, minval=-10, maxval=10):
        super().create_task()
        pydaqmx.DAQmxCreateAOVoltageChan(self.th, self.dev, '', self.minval, self.maxval, pydaqmx.DAQmx_Val_Volts, '')

    def set_range(self, minval, maxval):
        self.minval = minval
        self.maxval = maxval
        self.clear_task()
        self.create_task()

    def set_voltage(self, v):
        if v < self.minval:
            print('V < Vmin. Setting Vmin')
            self.setVoltage(self.minval)
        elif v > self.maxval:
            print('V > Vmax. Setting Vmax')
            self.setVoltage(self.maxval)
        else:
            autostart = 1
            timeout = -1
            # print(v)
            # print(self.dev)
            pydaqmx.DAQmxWriteAnalogScalarF64(self.th, autostart, timeout, v, None)
            self.currentVoltage = v

    def get_voltage(self):
        return self.currentVoltage

    def set_voltages(self, v):
        if min(v) < self.minval or max(v) > self.maxval:
            print('value out of range')
        else:
            autostart = 0
            timeout = -1
            writeval = ctypes.c_int32()
            pydaqmx.DAQmxWriteAnalogF64(self.th, len(v), autostart, timeout, pydaqmx.DAQmx_Val_GroupByChannel, v, writeval, None)
        self.lastSweepVoltage = v[-1]

    # These should really be a Galvo/Piezo Class, but Peace is lazy.
    def set_scale(self, volt_per_micron, offset):
        if type(volt_per_micron) is str:
            volt_per_micron = eval(volt_per_micron)
        if type(offset) is str:
            offset = eval(offset)
        self.volt_per_micron = volt_per_micron
        self.offset = offset

    def set_position(self, p):
        # p given in microns, takes into account the galvo offsets
        v = p*self.volt_per_micron + self.offset
        self.set_voltage(v)
        # print(p)

    def set_positions(self, p):
        # same as above, but for a sweep
        v = p * self.volt_per_micron + self.offset
        # print(p)
        self.set_voltages(v)

    def wait_until_done(self):
        super().wait_until_done()
        self.currentVoltage = self.lastSweepVoltage


class GalvoPiezo(DAQmxChannel.DAQmxChannel):
    '''
    to be tested - Peace 08/21/16
    A class that handles moving the galvo and piezo.
    This class would allow for simultaneously sweeping multiple variables.
    Intended to take over DAQmxAnalogOutput for galvos and piezo.
    '''
    def __init__(self, aoX, aoY, aoZ):
        super().__init__('%s,%s,%s' % (aoX, aoY, aoZ))

        self.minval = -10
        self.maxval = 10
        self.volt_per_micron = [1, 1, 1]
        self.offset = [0, 0, 0]

        self.create_task()

        self.currentVoltage = [0, 0, 0]
        self.currentPosition = [0, 0, 0]

        self.lastSweepVoltage = [0, 0, 0]
        self.lastSweepPosition = [0, 0, 0]

    def create_task(self):
        super().create_task()
        pydaqmx.DAQmxCreateAOVoltageChan(self.th, self.dev, '', self.minval, self.maxval, pydaqmx.DAQmx_Val_Volts, '')

    def set_scale(self, volt_per_micron, offset):
        for ind in range(len(volt_per_micron)):
            if type(volt_per_micron[ind]) is str:
                volt_per_micron[ind] = eval(volt_per_micron[ind])
        self.volt_per_micron = volt_per_micron
        self.offset = offset

    def set_voltage(self, vx, vy, vz):
        # this function should not be called from outside
        if self.isTimed:
            self.reset()
            self.set_voltages([vx], [vy], [vz], autostart=1)
        else:
            self.set_voltages([vx], [vy], [vz], autostart=1)
        self.currentVoltage = [vx, vy, vz]

    def set_voltages(self, vx, vy, vz, autostart=0):
        # this function should not be called from outside
        # check if piezo is getting negative voltage and replace with 0
        replaceval = False
        for ind in range(len(vz)):
            if vz[ind] < 0:
                vz[ind] = 0
                replaceval = True
        if replaceval:
            print('below piezo range, replacing negative vals with 0')

        if not (len(vx) == len(vy) and len(vx) == len(vz)):
            print('Vectors v1, v2, v3 must have equal length')
        else:
            timeout = -1
            writeval = ctypes.c_int32()
            v_concat = np.float64(np.append(np.append(vx, vy), vz))
            pydaqmx.DAQmxWriteAnalogF64(self.th, len(vx), autostart, timeout, pydaqmx.DAQmx_Val_GroupByChannel, v_concat, writeval, None)
            self.lastSweepVoltage = [vx[-1], vy[-1], vz[-1]]

    def set_position(self, ax, p):
        '''
        p should be a list of the positions
        Example: set_position([0, 2], [x, z])
        '''

        if type(ax) is not list and type(p) is not list:
            ax = [ax]
            p = [p]
        if not len(ax) == len(p):
            print('number of data is not equal to the number of axes')
        else:
            p_vec = self.currentPosition
            i = 0
            for a in ax:
                # single axis setting
                p_vec[a] = p[i]
                i += 1
            v_vec = np.multiply(p_vec, self.volt_per_micron) + self.offset
            self.set_voltage(v_vec[0], v_vec[1], v_vec[2])
            self.currentPosition = p_vec

    def set_positions(self, ax, p):
        '''
        p should be a LIST containing LISTS of positions.
        Even for a single-axis sweep, it should look like [[1,2,3,4]]
        Example: set_positions([0, 2], [[x1,x2,...], [z1,z2,...]])
        '''

        if type(ax) is not list:
            ax = [ax]
            p = [p]

        lastSweepPosition = self.currentPosition
        if not len(ax) == len(p):
            print('number of data is not equal to the number of axes')
        else:
            vx = np.repeat(self.currentVoltage[0], len(p[0]))
            vy = np.repeat(self.currentVoltage[1], len(p[0]))
            vz = np.repeat(self.currentVoltage[2], len(p[0]))

            v = [vx, vy, vz]

            i = 0
            for a in ax:
                # single axis setting
                v[a] = np.array(p[i])*self.volt_per_micron[a] + self.offset[a]
                i += 1

            self.set_voltages(v[0], v[1], v[2])
            self.lastSweepPosition = lastSweepPosition

    def wait_until_done_thd(self, thd):
        daqmx_running = 1
        while daqmx_running != 0 and not thd.cancel:
            try:
                daqmx_running = pydaqmx.DAQmxWaitUntilTaskDone(self.th, 0)
            except:
                time.sleep(0.01)
        if thd.cancel:
            self.currentVoltage = self.lastSweepVoltage
            self.currentPosition = self.lastSweepPosition
            return 1
        else:
            return 0

    def set_X(self, p):
        self.set_position(0, p)

    def set_Y(self, p):
        self.set_position(1, p)

    def set_Z(self, p):
        self.set_position(2, p)


class Galvo(DAQmxChannel.DAQmxChannel):
    '''
    A class that mimics GalvoPiezo, but does nothing to the set_Z
    '''
    def __init__(self, aoX, aoY):
        super().__init__('%s,%s' % (aoX, aoY))

        self.minval = -10
        self.maxval = 10
        self.volt_per_micron = [1, 1]
        self.offset = [0, 0]

        self.create_task()

        self.currentVoltage = [0, 0]
        self.currentPosition = [0, 0]

        self.lastSweepVoltage = [0, 0]
        self.lastSweepPosition = [0, 0]

    def create_task(self):
        super().create_task()
        pydaqmx.DAQmxCreateAOVoltageChan(self.th, self.dev, '', self.minval, self.maxval, pydaqmx.DAQmx_Val_Volts, '')

    def set_scale(self, volt_per_micron, offset):
        for ind in range(len(volt_per_micron)):
            if type(volt_per_micron[ind]) is str:
                volt_per_micron[ind] = eval(volt_per_micron[ind])
        self.volt_per_micron = volt_per_micron
        self.offset = offset

    def set_voltage(self, vx, vy, vz):
        # this function should not be called from outside
        if self.isTimed:
            self.reset()
            self.set_voltages([vx], [vy], [vz], autostart=1)
        else:
            self.set_voltages([vx], [vy], [vz], autostart=1)
        self.currentVoltage = [vx, vy, vz]

    def set_voltages(self, vx, vy, vz, autostart=0):
        # this function should not be called from outside
        if not (len(vx) == len(vy) and len(vx) == len(vz)):
            print('Vectors v1, v2, v3 must have equal length')
        else:
            timeout = -1
            writeval = ctypes.c_int32()
            v_concat = np.float64(np.append(vx, vy))
            pydaqmx.DAQmxWriteAnalogF64(self.th, len(vx), autostart, timeout, pydaqmx.DAQmx_Val_GroupByChannel, v_concat, writeval, None)
            self.lastSweepVoltage = [vx[-1], vy[-1]]

    def set_position(self, ax, p):
        '''
        p should be a list of the positions
        Example: set_position([0, 2], [x, z])
        '''

        if type(ax) is not list and type(p) is not list:
            ax = [ax]
            p = [p]
        if not len(ax) == len(p):
            print('number of data is not equal to the number of axes')
        else:
            p_vec = self.currentPosition
            i = 0
            for a in ax:
                # single axis setting
                if a < 2:
                    p_vec[a] = p[i]
                    i += 1
            v_vec = np.multiply(p_vec, self.volt_per_micron) + self.offset
            self.set_voltage(v_vec[0], v_vec[1], 0.0)
            self.currentPosition = p_vec

    def set_positions(self, ax, p):
        '''
        p should be a LIST containing LISTS of positions.
        Even for a single-axis sweep, it should look like [[1,2,3,4]]
        Example: set_positions([0, 2], [[x1,x2,...], [z1,z2,...]])
        '''

        if type(ax) is not list:
            ax = [ax]
            p = [p]

        lastSweepPosition = self.currentPosition
        if not len(ax) == len(p):
            print('number of data is not equal to the number of axes')
        else:
            vx = np.repeat(self.currentVoltage[0], len(p[0]))
            vy = np.repeat(self.currentVoltage[1], len(p[0]))
            vz = np.repeat(0.0, len(p[0]))  # Dummy values

            v = [vx, vy, vz]

            i = 0
            for a in ax:
                # single axis setting
                if a < 2:
                    v[a] = np.array(p[i])*self.volt_per_micron[a] + self.offset[a]
                    i += 1

            self.set_voltages(v[0], v[1], v[2])
            self.lastSweepPosition = lastSweepPosition

    def wait_until_done_thd(self, thd):
        daqmx_running = 1
        while daqmx_running != 0 and not thd.cancel:
            try:
                daqmx_running = pydaqmx.DAQmxWaitUntilTaskDone(self.th, 0)
            except:
                time.sleep(0.01)
        if thd.cancel:
            self.currentVoltage = self.lastSweepVoltage
            self.currentPosition = self.lastSweepPosition
            return 1
        else:
            return 0

    def set_X(self, p):
        self.set_position(0, p)

    def set_Y(self, p):
        self.set_position(1, p)

    def set_Z(self, p):
        pass
