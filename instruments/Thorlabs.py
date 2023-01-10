from instruments import GPIBdev
from instruments import GPIBdev_gui
from instruments import instr_widget
import warnings
import pyvisa


class PM100D(GPIBdev.GPIBdev):
    'PM100D Power Meter'

    def __init__(self, dev):
        # do nothing, maybe eventually do something
        super().__init__(dev)
        self.scale = 1.0

        print('PM100D Connected: %s' % str(self.gpib_query('*IDN?')))

    def get_pow(self):
        try:
            if self.connected:
                return float(self.gpib_query('MEAS:POW?'))*self.scale
            else:
                return 0.0
        except pyvisa.errors.VisaIOError:
            warnings.warn('Cannot connect to %s' % self.dev)
            return 0.0

    def set_scale(self, scale):
        # P_at_objective / P_at_beampick
        print(scale)
        self.scale = eval(str(scale))
        print('set scale', self.scale)

    def btn_measure(self):
        print('%s: Power = %.6f mW' % (self.dev, self.get_pow()*1000))


class PM100D_widget(instr_widget.GenericWidget, GPIBdev_gui.Ui_Form):
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


try:
    import thorlabs_apt as apt

    class Motor(apt.Motor):
        def __init__(self, addr):
            addr = int(addr)
            list_dev = apt.list_available_devices()

            self.connected = False

            if addr in [dev[1] for dev in list_dev]:
                super().__init__(addr)
            else:
                raise Exception('Device with S/N %d not available!' % addr)

            self.connected = True

        def move_home(self):
            super().move_home(blocking=True)

        def move_to(self, value):
            super().move_to(value, blocking=True)

        def get_position(self):
            return self.position

except:
    print('thorlabs_apt not found!')



if __name__ == '__main__':
    pm = PM100D('USB_PM100D')



