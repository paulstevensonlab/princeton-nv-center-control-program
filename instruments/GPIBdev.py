import pyvisa as vs
import warnings

# Uncomment to enable exhaustive pyvisa debug output.
# vs.log_to_screen()

class GPIBdev:

    def __init__(self, dev, **kwargs):
        self.dev = dev
        self.connected = False
        rm = vs.ResourceManager()

        try:
            self.inst = rm.open_resource(dev, access_mode=4, **kwargs) # access_mode set to load interface params from NI-Max
            self.connected = True
        except:
            warnings.warn('Dev %s not found.' % self.dev)

    def gpib_connect(self, **kwargs):
        rm = vs.ResourceManager()
        try:
            self.inst = rm.open_resource(self.dev, access_mode=4, **kwargs) # access_mode set to load interface params from NI-Max
            self.connected = True
        except:
            warnings.warn('Dev %s not found.' % self.dev)

    def gpib_write(self, str):
        if self.connected:
            self.inst.write(str)
        else:
            try:
                self.gpib_connect()
                self.inst.write(str)
            except:
                warnings.warn('Cannot write to the instrument %s.' % self.dev)

    def gpib_query(self, str):
        if self.connected:
            return self.inst.query(str)
        else:
            return -1

    def gpib_read(self):
        if self.connected:
            return self.inst.read()
        else:
            return -1