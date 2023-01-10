# -*- coding: utf-8 -*-

import numpy as np

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



