from PyQt5.QtCore import pyqtSignal
import PyDAQmx, time, datetime
import numpy as np
import warnings

from . import ExpThread


class Confocal(ExpThread.ExpThread):

    # Define signals for communicating with mainexp
    signal_confocal_grab_screenshots = pyqtSignal()

    signal_confocal_initplot = pyqtSignal()
    signal_confocal_updateplot = pyqtSignal(int)

    def __init__(self, mainexp, wait_condition):
        super().__init__(mainexp, wait_condition)

        # Make references to the main DAQmx Channels
        self.galpie = mainexp.galpie
        self.ctrapd = mainexp.ctrapd
        self.ctrclk = mainexp.ctrclk
        self.ctrtrig = mainexp.ctrtrig

        self.acqtime = 0.001

        self.mode = 0  # scanning mode (0: XY, 1: XZ, 2: YZ)

        self.var1_id = 0  # x-axis
        self.var2_id = 1  # y-axis
        self.var3_id = 2  # z-axis

        self.var1 = []
        self.var2 = []
        self.var3 = []

        self.autoZ = False
        self.isESR = False  # Use for alternating ESR on-off. There should be a better place to put this though.
        self.isLive = False
        self.confocal_live_stacks = []
        self.confocal_live_avg = 1
        # Connect signals
        self.signal_confocal_grab_screenshots.connect(self.mainexp.confocal_grab_screenshots)

        self.signal_confocal_initplot.connect(mainexp.confocal_initplot)
        self.signal_confocal_updateplot.connect(mainexp.confocal_updateplot)

        self.plane_coef = [0, 0, 1, 5]  # coefficients for Ax + By + Cz = D for autoZ

    def setup_ctr(self):
        self.ctrapd.reset()
        self.ctrclk.reset()
        self.ctrtrig.set_time(0.001)
        self.ctrtrig.reset()
        self.galpie.reset()

        self.galpie.set_sample_clock(self.mainexp.inst_params['instruments']['ctrclk']['addr_out'],
                                     PyDAQmx.DAQmx_Val_Rising,
                                     len(self.var1) + 1)
        self.galpie.set_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'],
                                      PyDAQmx.DAQmx_Val_Rising)

        # create a self.ctrapd running on clock from self.ctrclk and wait for trigger from self.ctrtrig
        self.ctrapd.set_source(self.mainexp.inst_params['instruments']['ctrapd']['addr_src'])
        self.ctrapd.set_sample_clock(self.mainexp.inst_params['instruments']['ctrclk']['addr_out'],
                                     PyDAQmx.DAQmx_Val_Rising,
                                     len(self.var1) + 1)
        self.ctrapd.set_arm_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'],
                                          PyDAQmx.DAQmx_Val_Rising)

        # creates a clock using pulses on self.ctrclk (output to PFI7)
        self.ctrclk.set_freq(1/self.acqtime)
        self.ctrclk.start()

    def setup_ctr_2d(self):
        self.ctrapd.reset()
        self.ctrclk.reset()
        self.ctrtrig.set_time(0.001)
        self.ctrtrig.reset()
        self.galpie.reset()

        self.galpie.set_sample_clock(self.mainexp.inst_params['instruments']['ctrclk']['addr_out'],
                                     PyDAQmx.DAQmx_Val_Rising,
                                     len(self.var1)*len(self.var2) + 1)
        self.galpie.set_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'],
                                      PyDAQmx.DAQmx_Val_Rising)

        # create a self.ctrapd running on clock from self.ctrclk and wait for trigger from self.ctrtrig
        self.ctrapd.set_source(self.mainexp.inst_params['instruments']['ctrapd']['addr_src'])
        self.ctrapd.set_sample_clock(self.mainexp.inst_params['instruments']['ctrclk']['addr_out'],
                                     PyDAQmx.DAQmx_Val_Rising,
                                     len(self.var1)*len(self.var2) + 1)
        self.ctrapd.set_arm_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'],
                                          PyDAQmx.DAQmx_Val_Rising)

        # creates a clock using pulses on self.ctrclk (output to PFI7)
        self.ctrclk.set_freq(1/self.acqtime)
        self.ctrclk.start()

    def prep_mainexp(self):
        self.mainexp.datasaved = False

        # enable and disable the right buttons here
        self.mainexp.set_gui_btn_enable('all', False)
        self.mainexp.set_gui_input_enable('confocal', False)
        self.mainexp.btn_confocal_stop.setEnabled(True)
        self.mainexp.chkbx_confocal_autolevel.setChecked(True)
        if self.isLive:
            self.mainexp.btn_confocal_live.setEnabled(True)

        if self.mainexp.btn_confocal_autoZ.isChecked():
            self.plane_fit()

    def update(self):
        self.autoZ = self.mainexp.btn_confocal_autoZ.isChecked()
        self.mode = self.mainexp.btn_confocal_mode.checkedId()
        self.isESR = self.mainexp.chkbx_confocal_esr.isChecked()
        self.confocal_live_avg = self.mainexp.int_confocal_live_avg.value()

    def prepsweep(self):
        mainexp = self.mainexp

        if self.mode == 0:  # XY Scan. Possible to do z-stacks
            self.var1_id = 0
            self.var2_id = 1
            self.var3_id = 2

            self.var1 = np.linspace(mainexp.dbl_confocal_x_start.value(), mainexp.dbl_confocal_x_stop.value(),
                                    mainexp.int_confocal_x_numdivs.value() + 1)
            self.var2 = np.linspace(mainexp.dbl_confocal_y_start.value(), mainexp.dbl_confocal_y_stop.value(),
                                    mainexp.int_confocal_y_numdivs.value() + 1)

            self.plane_coef = [0, 0, 1, 5]  # default to 0*x + 0*y + 1*z = 5

            if not self.autoZ and mainexp.int_confocal_z_numdivs.value():
                self.var3 = np.linspace(mainexp.dbl_confocal_z_start.value(), mainexp.dbl_confocal_z_stop.value(),
                                        mainexp.int_confocal_z_numdivs.value() + 1)
            else:
                # ignore the z-range setting
                self.var3 = np.linspace(mainexp.dbl_tracker_zpos.value(), mainexp.dbl_tracker_zpos.value(), 1)

        if self.mode == 1:  # XZ Scan. No stacks
            self.var1_id = 0
            self.var2_id = 2
            self.var3_id = 1

            self.var1 = np.linspace(mainexp.dbl_confocal_x_start.value(), mainexp.dbl_confocal_x_stop.value(),
                                    mainexp.int_confocal_x_numdivs.value() + 1)
            self.var2 = np.linspace(mainexp.dbl_confocal_z_start.value(), mainexp.dbl_confocal_z_stop.value(),
                                    mainexp.int_confocal_z_numdivs.value() + 1)
            self.var3 = np.linspace(mainexp.dbl_tracker_ypos.value(), mainexp.dbl_tracker_ypos.value(), 1)
            self.autoZ = False

        if self.mode == 2:  # YZ Scan. No stacks
            self.var1_id = 1
            self.var2_id = 2
            self.var3_id = 0

            self.var1 = np.linspace(mainexp.dbl_confocal_y_start.value(), mainexp.dbl_confocal_y_stop.value(),
                                    mainexp.int_confocal_y_numdivs.value() + 1)
            self.var2 = np.linspace(mainexp.dbl_confocal_z_start.value(), mainexp.dbl_confocal_z_stop.value(),
                                    mainexp.int_confocal_z_numdivs.value() + 1)
            self.var3 = np.linspace(mainexp.dbl_tracker_xpos.value(), mainexp.dbl_tracker_xpos.value(), 1)
            self.autoZ = False

        mainexp.confocal_mode = self.mode
        mainexp.confocal_rngx = self.var1
        mainexp.confocal_rngy = self.var2
        mainexp.confocal_rngz = self.var3

        self.acqtime = mainexp.dbl_confocal_acqtime.value()

    def initplots(self):
        self.mainexp.confocal_pl = np.empty((self.var1.size, self.var2.size, self.var3.size))
        # self.mainexp.confocal_pl[:][:][:] = np.NaN
        self.mainexp.confocal_pl[:][:][:] = 1000.0
        # self.mainexp.confocal_pl[0][0][0] = 1.0
        self.confocal_live_stacks = np.array([])

        self.signal_confocal_initplot.emit()
        self.signal_confocal_updateplot.emit(0)

        if self.isRunning():
            self.wait_for_mainexp()

        self.log_clear()
        self.log('%s started at %s' % (self.mainexp.label_filename.text(),
                                                            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    def sweep1d(self, x_i, x_f, y_i, y_f, z_i, z_f, numpnts):
        xstart = x_i
        xstop = x_f
        acqtime = self.acqtime

        # create a list of positions
        xlist = np.linspace(xstart, xstop, numpnts)
        # repeat the last point to park and read counts
        xlist = np.append(xlist, xlist[-1])
        ylist = np.linspace(y_i, y_f, len(xlist))
        zlist = np.linspace(z_i, z_f, len(xlist))

        self.galpie.set_positions([self.var1_id, self.var2_id, self.var3_id],
                                  [xlist.tolist(), ylist.tolist(), zlist.tolist()])
        # set arm start on the tasks that are hardware-timed so they are ready to be triggered
        self.galpie.start()
        self.ctrapd.start()

        self.ctrtrig.start()
        self.ctrtrig.wait_until_done()
        self.ctrtrig.stop()

        ctr_raw = self.ctrapd.get_counts(numpnts + 1)
        ctr_read = np.diff(ctr_raw) / acqtime

        self.galpie.wait_until_done()
        self.ctrapd.wait_until_done()
        self.galpie.stop()
        self.ctrapd.stop()

        return list(ctr_read)

    def sweep2d(self):
        # Not doing stacks, not using any Z piezo. Not running MW. For now....
        if len(self.var3) == 1 and not self.autoZ and self.mode == 0 and not self.isESR:
            self.galpie.reset()
            self.galpie.set_position(self.var3_id, self.var3[0])
            self.sweep2d_fast()
        else:
            # Define the indices separately, otherwise they will cause problems when passed into the signal
            index_z = 0
            autoZ = self.autoZ

            # conventional 2d scan in multiple z-slices

            for z in self.var3:
                if not self.cancel:
                    index_y = 0

                    self.galpie.reset()
                    self.galpie.set_position(self.var3_id, z)
                    self.setup_ctr()
                    time.sleep(0.5)

                    xvect = list(self.var1)
                    for y in self.var2:
                        if not self.cancel:
                            x_i = xvect[0]
                            x_f = xvect[-1]
                            y_i = y
                            y_f = y

                            if not autoZ:
                                z_i = z
                                z_f = z
                            else:
                                z_i = self.calcZ(x_i, y)
                                z_f = self.calcZ(x_f, y)

                            # return the linecut containing counts per second
                            if not self.isESR:
                                xlinecut = self.sweep1d(x_i, x_f, y_i, y_f, z_i, z_f, len(xvect))
                            else:
                                self.mainexp.mw1.set_output(0)
                                self.mainexp.pb.set_cw()
                                time.sleep(0.1)
                                xlinecut_1 = np.array(self.sweep1d(x_i, x_f, y_i, y_f, z_i, z_f, len(xvect)))
                                self.mainexp.mw1.set_output(1)
                                self.mainexp.pb.set_cw_custom(['green', 'mw1'])
                                time.sleep(0.1)
                                xlinecut_2 = np.array(self.sweep1d(x_i, x_f, y_i, y_f, z_i, z_f, len(xvect)))
                                xlinecut = list(xlinecut_1 - xlinecut_2)

                            if np.mod(index_y, 2) == 1:
                                xlinecut.reverse()

                            for i in range(len(xlinecut)):
                                self.mainexp.confocal_pl[i][index_y][index_z] = xlinecut[i]

                            # if np.mod(index_y + 1, 10) == 0 or y == self.var2[-1]:
                            self.signal_confocal_updateplot.emit(index_z)
                            xvect.reverse()

                            index_y += 1

                    if self.isRunning():
                        self.wait_for_mainexp()

                    index_z += 1

            self.ctrclk.stop()

            if self.isESR:
                self.mainexp.mw1.set_output(0)
                self.mainexp.pb.set_cw()

    def sweep2d_fast(self):
        rev = False

        exit_loop = False
        while not exit_loop:
            if len(self.confocal_live_stacks):
                self.confocal_live_stacks = np.append(self.confocal_live_stacks,
                                                      np.empty((self.var1.size, self.var2.size, 1)), axis=2)
            else:
                self.confocal_live_stacks = np.empty((self.var1.size, self.var2.size, 1))
            self.confocal_live_stacks[:][:][-1] = np.NaN
            if self.confocal_live_stacks.shape[2] > self.confocal_live_avg:
                self.confocal_live_stacks = self.confocal_live_stacks[:, :, -self.confocal_live_avg:]

            self.sweep2d_fast_single_frame(rev=rev)
            rev = ~rev

            if self.cancel:
                exit_loop = True
            else:
                if not self.isLive:
                    exit_loop = np.atleast_3d(self.confocal_live_stacks).shape[2] == self.confocal_live_avg
                else:
                    exit_loop = not self.mainexp.btn_confocal_live.isChecked() and \
                                np.atleast_3d(self.confocal_live_stacks).shape[2] == self.confocal_live_avg

    def sweep2d_fast_single_frame(self, rev=False):
        if not self.cancel:
            self.setup_ctr_2d()

            # Build a sweep list
            xlist = np.array([])
            ylist = np.array([])
            zlist = np.array([])

            for i, y in enumerate(self.var2):
                if not i % 2:
                    xlist = np.append(xlist, self.var1)
                else:
                    xlist = np.append(xlist, np.flip(self.var1, axis=0))

                ylist = np.append(ylist, np.ones(len(self.var1)) * y)
                zlist = np.append(zlist, np.ones(len(self.var1)) * self.var3[0])

            if rev:
                xlist = np.flip(xlist, axis=0)
                ylist = np.flip(ylist, axis=0)
                zlist = np.flip(zlist, axis=0)

            xlist = np.append(xlist, xlist[-1])
            ylist = np.append(ylist, ylist[-1])
            zlist = np.append(zlist, zlist[-1])

            self.galpie.set_positions([self.var1_id, self.var2_id, self.var3_id],
                                      [xlist.tolist(), ylist.tolist(), zlist.tolist()])

            # set arm start on the tasks that are hardware-timed so they are ready to be triggered
            self.galpie.start()
            self.ctrapd.start()
            self.ctrtrig.start()
            self.ctrtrig.wait_until_done()
            self.ctrtrig.stop()

            self.mainexp.seqapd_pl = np.array([])

            numpnts1 = len(self.var1)
            numpnts2 = len(self.var2)

            last_counter = self.mainexp.ctrapd.get_counts(1)[0]

            for index_y in range(numpnts2):
                if not self.cancel:
                    # This will wait until the entire row is read
                    ctr_raw = self.mainexp.ctrapd.get_counts(numpnts1)
                    ctr_diff = np.diff(np.append([last_counter], ctr_raw)) / self.acqtime

                    last_counter = ctr_raw[-1]

                    # Forward meander scan (increasing yvals)
                    if not rev:
                        if not index_y % 2:
                            self.confocal_live_stacks[:, index_y, -1] = ctr_diff
                        else:
                            self.confocal_live_stacks[:, index_y, -1] = np.flipud(ctr_diff)
                        self.mainexp.confocal_pl[:, index_y, 0] = np.nanmean(self.confocal_live_stacks[:, index_y, :], axis=1)
                    # Reverse meander scan (decreasing yvals)
                    else:
                        if not index_y % 2:
                            self.confocal_live_stacks[:, -(index_y+1), -1] = np.flipud(ctr_diff)
                        else:
                            self.confocal_live_stacks[:, -(index_y+1), -1] = ctr_diff
                        self.mainexp.confocal_pl[:, -(index_y+1), 0] = np.nanmean(self.confocal_live_stacks[:, -(index_y+1), :], axis=1)

                    self.signal_confocal_updateplot.emit(0)

            if hasattr(PyDAQmx.DAQmxFunctions, 'DAQWarning'):
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', PyDAQmx.DAQmxFunctions.DAQWarning)  # for ignoring warnings when plotting NaNs

                    self.mainexp.ctrclk.stop()
                    self.mainexp.ctrclk.reset()
                    try:
                        self.mainexp.ctrapd.stop()
                    except PyDAQmx.DAQmxFunctions.DAQError:
                        # It is normal for the PyDAQmx to throw an error when stopped prematurely
                        pass
                    self.mainexp.ctrapd.reset()

            if self.isRunning():
                self.wait_for_mainexp()

    def cleanup(self):
        self.log('%s finished at %s' % (self.mainexp.label_filename.text(),
                                                             datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        # stop nidaq tasks if they haven't already
        self.mainexp.galpie.reset()
        self.mainexp.ctrapd.reset()
        self.mainexp.ctrclk.reset()
        self.mainexp.ctrtrig.reset()

        if self.mainexp.chkbx_autosave.isChecked() and not self.mainexp.datasaved:
            self.save()
            self.mainexp.datasaved = True

        self.mainexp.set_gui_btn_enable('all', True)
        self.mainexp.set_gui_input_enable('confocal', True)
        self.mainexp.btn_confocal_stop.setEnabled(False)

    def save(self, ext=False):
        if self.isRunning() and not ext:
            self.signal_confocal_grab_screenshots.emit()
            self.wait_for_mainexp()
            time.sleep(0.1)
        else:  # For use when save_esr is called from a button
            self.mainexp.confocal_grab_screenshots()

        graph = self.mainexp.pixmap_confocal_graph
        fig = self.mainexp.pixmap_confocal_fig
        filename = self.mainexp.label_filename.text()
        data_dict = {'pl': self.mainexp.confocal_pl,
                     'xvals': self.mainexp.confocal_rngx,
                     'yvals': self.mainexp.confocal_rngy,
                     'zvals': self.mainexp.confocal_rngz}

        self.save_data(filename, data_dict, graph=graph, fig=fig)

    def plane_fit(self):
        """
        a, b, c, d = planeFit(points)

        return the coefficients of the plane equation ax + by + cz = d
        from a list of three numpy vectors
        """
        table = self.mainexp.table_confocalZ
        if table.rowCount() >= 3:
            if table.rowCount() > 3:
                self.log('More than  three points defined. Using only the first three.')

            p0 = np.array([float(table.item(0, 0).text()), float(table.item(0, 1).text()), float(table.item(0, 2).text())])
            p1 = np.array([float(table.item(1, 0).text()), float(table.item(1, 1).text()), float(table.item(1, 2).text())])
            p2 = np.array([float(table.item(2, 0).text()), float(table.item(2, 1).text()), float(table.item(2, 2).text())])

            v1 = p1 - p0
            v2 = p2 - p0

            norm = np.cross(v1, v2)

            a = norm[0]
            b = norm[1]
            c = norm[2]

            d = a * p0[0] + b * p0[1] + c * p0[2]

            self.plane_coef = [a, b, c, d]
            self.mainexp.label_confocalZ_eq.setText('z = %.3f + %.3fx + %.3fy' % (d / c, -a / c, -b / c))

    def calcZ(self, x, y):
        [a, b, c, d] = self.plane_coef
        return (d - a*x - b*y)/c

    def run(self):
        self.cancel = False

        self.prep_mainexp()
        self.update()

        self.prepsweep()
        self.initplots()

        self.sweep2d()
        self.cleanup()
        self.isLive = False

    def __del__(self):
        self.wait()
