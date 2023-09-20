# -*- coding: utf-8 -*-

import numpy as np
import socket

class RemoteActuator:
    'remote server for moving bias magnet actuator'

    def __init__(self, addr):
        self.vmax = 3.4
        self.vmin = 0.0
        self.scale = 1.0

        self.ipaddress = str(addr)
        self.port = int(9999)

        self.connected = True

    def move_to(self,pos):
        if pos>self.vmax:
            pos = self.vmax
        elif pos<self.vmin:
            pos = self.vmin

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.ipaddress,self.port))
            sock.sendall(bytes('POS '+str(pos) + "\n", "utf-8"))
            received = str(sock.recv(1024), "utf-8")

    def get_position(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.ipaddress,self.port))
            sock.sendall(bytes('POS?' + "\n", "utf-8"))
            received = str(sock.recv(1024), "utf-8")
            print(float(received))
            return float(received)




class servo_1061():
    '1061 Phidgets Control Board -RC Servo only version'

    def __init__(self, dev):
        # do nothing, maybe eventually do something
        self.boardnum = -1

    def set_board(self, num):
        self.boardnum = num



if __name__ == '__main__':
    print('Phidgets Test')


    print('finished')



