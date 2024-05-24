import rpyc

class rpyccontrol:
    def __init__(self, addr):
        return

class ControlService(rpyc.Service):
    def __init__(self,mainexp):
        self.mainexp = mainexp
        return

    def on_connect(self, conn):
        # code that runs when a connection is created
        # (to init the service, if needed)
        print('Connected ok!')
        pass

    def on_disconnect(self, conn):
        # code that runs after the connection has already closed
        # (to finalize the service, if needed)
        pass

    def exposed_unit_test(self):
        self.mainexp.list_terminal_cmdqueue.addItem("setval('mw1freq', 2724500000.0)")
        self.mainexp.thread_terminal.submit_cmd()
        return

    def exposed_check_is_running(self):
        # if nothing running, return 0. Otherwise
        # return 1 for sweep running, 2 for confocal scan, 3 for tracker running
        state = 0
        if self.mainexp.thread_sweep.isRunning():
            state = 1
        elif self.mainexp.thread_confocal.isRunning():
            state = 2
        elif self.mainexp.thread_tracker.isRunning():
            state = 3
        return state

    def exposed_send_command(self,cmd):
        if type(cmd) is str:
            self.mainexp.list_terminal_cmdqueue.addItem(cmd)
            self.mainexp.thread_terminal.submit_cmd()
        return

    def exposed_get_answer(self): # this is an exposed method
        return 42