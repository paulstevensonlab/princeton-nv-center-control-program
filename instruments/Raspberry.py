import socket
import time


class Shutter:
    def __init__(self, IP='192.168.1.108'):
        print('Phidget Shutter IP Address %s' % IP)

        self.Shutter_IP = IP
        self.PORT = 5005
        self.BUFFER_SIZE = 1024
        self.isconnected = False

        self.minPos = 0.0
        self.maxPos = 180.0

        self.open_pos = 0
        self.close_pos = 90
        self.ch = 0

        self.state = 0

        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("Socket successfully created")
            self.s.connect((self.Shutter_IP, self.PORT))
            print("Connection made")
            self.s.close()
            self.isconnected = True
        except socket.error as err:
            print("Connection Failed with error %s" % (err))

    def set_open_pos(self, s):
        if s >= self.minPos and s <= self.maxPos:
            self.open_pos = s
        else:
            print("Check exp_params; open state is outside allowed range")

    def set_close_pos(self, s):
        if s >= self.minPos and s <= self.maxPos:
            self.close_pos = s
        else:
            print("Check exp_params; closed state is outside allowed range")

    def set_channel(self, s):
        self.ch = s

    def set_shutter(self, state):
        if state == 0:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.Shutter_IP, self.PORT))
            self.MESSAGE = "SHUTTER," + str(self.close_pos) + "," + str(self.ch)
            self.s.send(self.MESSAGE.encode('utf8'))
            data = self.s.recv(self.BUFFER_SIZE)
            self.s.close()
            self.state = 0
            time.sleep(0.1)
        elif state == 1:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.Shutter_IP, self.PORT))
            self.MESSAGE = "SHUTTER," + str(self.open_pos) + "," + str(self.ch)
            self.s.send(self.MESSAGE.encode('utf8'))
            data = self.s.recv(self.BUFFER_SIZE)
            self.s.close()
            self.state = 1
            time.sleep(0.1)
        else:
            print("State must be 0 (Closed) or 1 (Open); please try again")

    def get_shutter(self):
        return self.state








