# -*- coding: utf-8 -*-
"""
Packaging pulse blaster functions into a class
"""

import ctypes


def enum(**enums):
    """Helper function to create instructions container"""
    return type('Enum', (), enums)


class PBESRPro:
    constants={}
    PULSE_PROGRAM = 0
    
    def __init__(self):
        # load the spinapi which contains all the C functions
        try:
            self.spinapi = ctypes.CDLL("spinapi64")
        except:
            print("Failed to load spinapi library")
            pass
        
        # populate the constants
        self.constants = {'ns': 1.0, 'us': 1000.0, 'ms': 1000000.0}
        self.constants.update({'MHz': 1.0, 'kHz': 0.001, 'Hz': 0.000001})
        # population the Instruction container
        self.inst_set = enum(
            CONTINUE = 0,
            STOP = 1,
            LOOP = 2,
            END_LOOP = 3,
            JSR = 4,
            RTS = 5,
            BRANCH = 6,
            LONG_DELAY = 7,
            WAIT = 8,
            RTI = 9
            )
            
        # set the return and input argument types
        self.spinapi.pb_get_version.restype = (ctypes.c_char_p)
        self.spinapi.pb_get_error.restype = (ctypes.c_char_p)
        self.spinapi.pb_read_status.restype = (ctypes.c_int)


        self.spinapi.pb_count_boards.restype = (ctypes.c_int)

        self.spinapi.pb_init.restype = (ctypes.c_int)

        self.spinapi.pb_select_board.argtype = (ctypes.c_int)
        self.spinapi.pb_select_board.restype = (ctypes.c_int)

        self.spinapi.pb_set_debug.argtype = (ctypes.c_int)
        self.spinapi.pb_set_debug.restype = (ctypes.c_int)

        self.spinapi.pb_set_defaults.restype = (ctypes.c_int)

        self.spinapi.pb_core_clock.argtype = (ctypes.c_double)
        self.spinapi.pb_core_clock.restype = (ctypes.c_int)

        self.spinapi.pb_start_programming.argtype = (ctypes.c_int)
        self.spinapi.pb_start_programming.restype = (ctypes.c_int)

        self.spinapi.pb_stop_programming.restype = (ctypes.c_int)

        self.spinapi.pb_start.restype = (ctypes.c_int)
        self.spinapi.pb_stop.restype = (ctypes.c_int)
        self.spinapi.pb_reset.restype = (ctypes.c_int)
        self.spinapi.pb_close.restype = (ctypes.c_int)

        self.spinapi.pb_inst_pbonly64.argtype = (
            ctypes.c_uint,      # flags
            ctypes.c_int,       # inst
            ctypes.c_int,       # inst_data
            ctypes.c_double,    # length (double)
            )

        self.spinapi.pb_inst_pbonly64.restype = (ctypes.c_int)

    def pb_get_version(self):
        """Return library version as UTF-8 encoded string."""
        ret = self.spinapi.pb_get_version()
        return str(ctypes.c_char_p(ret).value.decode("utf-8"))
        
    def pb_get_error(self):
        """Return library error as UTF-8 encoded string."""
        ret = self.spinapi.pb_get_error()
        return str(ctypes.c_char_p(ret).value.decode("utf-8"))

    def pb_count_boards(self):
        """Return the number of boards detected in the system."""
        return self.spinapi.pb_count_boards()

    def pb_init(self):
        """Initialize currently selected board."""
        return self.spinapi.pb_init()

    def pb_set_debug(self,debug):
        '''txt file printed with log, useful to send to spincore if problems'''
        return self.spinapi.pb_set_debug(debug)

    def pb_select_board(self,board_number):
        """Not necessary if we only have one board"""
        return self.spinapi.pb_select_board(board_number)
 
    def pb_core_clock(self,clock):
        '''tell driver what clock frequency to use, not an instruction 
        for the hardware'''
        return self.spinapi.pb_core_clock(ctypes.c_double(clock))
 
    def pb_start_programming(self, target):
        '''only PULSE_PROGRAM allowed for pb esr pro'''
        return self.spinapi.pb_start_programming(target)

    def pb_stop_programming(self):
        '''finish programming started by start_programming'''
        return self.spinapi.pb_stop_programming()
 
    def pb_start(self):
        '''software trig to the board to start running'''
        return self.spinapi.pb_start()

    def pb_stop(self):
        '''stops output and brings to ground. identical to reset?'''
        return self.spinapi.pb_stop()

    def pb_reset(self):
        '''stops output and brings to ground. identical to stop?'''
        return self.spinapi.pb_reset()

    def pb_close(self):
        '''End comm with the board. Called as the last line in a program.
        reinit comm with pb_init(). Any pulsing already started will continue.'''
        return self.spinapi.pb_close()

    def pb_inst_pbonly64(self,*args):
        '''instruction command for pulseblaster and esr pro boards'''
        t = list(args)
        t[3] = ctypes.c_double(t[3])
        args = tuple(t)
        return self.spinapi.pb_inst_pbonly64(*args)

    def pb_read_status(self):
        '''Read status from the board'''
        '''1 - stopped'''
        '''2 - reset'''
        '''4 - running'''
        '''8 - waiting'''

        return self.spinapi.pb_read_status()
