
import os
import ctypes

# if __name__ == '__main__':
#     import GPIBdev # use when running this as a main
# else:
#     from instruments import GPIBdev

# ##########################################################################################################
# helper functions
def ptr(x):
    """Shortcut to return a ctypes.pointer to object x.
    """
    return ctypes.pointer(x)


class WaveMeter621A():
    def __init__(self, addr):
        COM = 6 # instrument COM #
        self.pathToLib = 0
        print("connecting to wavemeter...")
        if self.pathToLib is 0:
            self.pathToLib = "C:\\Users\\deleonlab\\Documents\\deleonlab\\exp_code\\instruments\\clib\\"
        self.pathToLib = os.path.join(self.pathToLib, "CLDevIFace.dll")
        self.loadLibrary()
        self.open(COM)
        self.setLambdaUnits(1) # set to GHz
        self.setPowerUnits(0) # set to mW
        self.setMedium(1) #set to air

    def loadLibrary(self):
        self.lib = ctypes.cdll.LoadLibrary(self.pathToLib)

        #C Function Prototypes defined on loadLibrary

        self.lib.CLOpenUSBSerialDevice.restype = ctypes.c_int
        self.lib.CLOpenUSBSerialDevice.argtypes = [ctypes.c_int]

        self.lib.CLCloseDevice.restype = ctypes.c_int
        self.lib.CLCloseDevice.argtypes = [ctypes.c_int]

        self.lib.CLSetLambdaUnits.restype = ctypes.c_int
        self.lib.CLSetLambdaUnits.argtypes = [ctypes.c_int, ctypes.c_uint]

        self.lib.CLSetPowerUnits.restype = ctypes.c_int
        self.lib.CLSetPowerUnits.argtypes = [ctypes.c_int, ctypes.c_uint]

        self.lib.CLGetLambdaReading.restype = ctypes.c_double
        self.lib.CLGetLambdaReading.argtypes = [ctypes.c_int]

        self.lib.CLGetPowerReading.restype = ctypes.c_float
        self.lib.CLGetPowerReading.argtypes = [ctypes.c_int]

        self.lib.CLSetMedium.restype = ctypes.c_int
        self.lib.CLSetMedium.argtypes = [ctypes.c_int, ctypes.c_uint]

    def open(self, COM):
        self.h = int(self.lib.CLOpenUSBSerialDevice(ctypes.c_int(COM)))
        if self.h is -1:
            print("Error Wavemeter not connected.")
            self.isconnected = False
        else:
            print("Wavemeter connected")
            self.isconnected = True
        return self.h

    def close(self):
        self.isconnected = False
        return int(self.lib.CLCloseDevice(ctypes.c_int(self.h)))

    # def setCallback(self, ProcessMeasHBData):
#     return self.lib.CLSetMeasHBCallback(self.h, ProcessMeasHBData)
    #
    # def getCallbackData(self, measptr):
    #     self.lib.CLGetMeasurementData(self.h, ptr(measptr))
    #     return measptr.value

    def setLambdaUnits(self, lambdaunits):
        return int(self.lib.CLSetLambdaUnits(ctypes.c_int(self.h), ctypes.c_uint(lambdaunits)))

    def setPowerUnits(self, powerunits):
        return int(self.lib.CLSetPowerUnits(ctypes.c_int(self.h), ctypes.c_uint(powerunits)))

    def getLambda(self):
        return float(self.lib.CLGetLambdaReading(ctypes.c_int(self.h)))

    def getPower(self):
        return float(self.lib.CLGetPowerReading(ctypes.c_int(self.h)))

    def setMedium(self, medium):
        return int(self.lib.CLSetMedium(ctypes.c_int(self.h), ctypes.c_uint(medium)))

    def gotoLambda(self,Lambda):
        pass