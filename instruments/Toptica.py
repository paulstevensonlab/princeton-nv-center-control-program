import socket
import time
import numpy as np

class CTL:
    def __init__(self, IP='192.168.1.107'):
        print('CTL IP Address %s' % IP)

        self.DLC_IP = IP
        self.PORT_MON = 1999
        self.PORT_COM = 1998
        self.BUFFER_SIZE = 1024

        self.isconnected = False

        self.minLamb = 910
        self.maxLamb = 980
        self.minV = 0
        self.maxV = 140

        try:
            self.s_command = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("Command Socket successfully created")
        except socket.error as err:
            print("Command Socket creation failed with error %s" % (err))
            sys.exit()

        try:
            self.s_monitor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("Monitor Socket successfully created")
        except socket.error as err:
            print("Monitor Socket creation failed with error %s" % (err))
            sys.exit()

        # set WL and piezo to default values

        #self.s_command = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s_command.setsockopt(socket.SOL_SOCKET, socket.TCP_NODELAY, 1)
        self.s_command.connect((self.DLC_IP, self.PORT_COM))  # connect to DLC command channel



        #self.s_command.sendall("(param-set! 'laser1:ctl:wavelength-set 950) \n".encode('utf8'))  # move to new wavelength
        #self.s_commandbuffer = self.s_command.recv(self.BUFFER_SIZE)
        #self.s_command.sendall("(param-set! 'laser1:dl:pc:voltage-set 70) \n".encode('utf8'))  # move to new wavelength
        #self.s_commandbuffer = self.s_command.recv(self.BUFFER_SIZE)
        #self.s_command.close()  # close DLC command channel


        # now populate some of fields
        self.s_monitor.setsockopt(socket.SOL_SOCKET, socket.TCP_NODELAY, 1)
        self.s_monitor.connect((self.DLC_IP, self.PORT_MON))  # connect to DLC

        self.s_monitor.sendall("(query 'laser1:ctl:wavelength-set) \n".encode('utf8'))  # query current WL
        current_wl_raw = self.s_monitor.recv(self.BUFFER_SIZE)  # receive current WL
        current_wl_temp = str(current_wl_raw.decode().split("set ", 1)[1])  # extract WL from string
        current_wl_temp = current_wl_temp[:-3]  # extract WL from string
        self.current_wl = float(current_wl_temp)

        self.s_monitor.sendall("(query 'laser1:ctl:scan:speed) \n".encode('utf8'))  # query scan speed
        current_scanspeed_raw = self.s_monitor.recv(self.BUFFER_SIZE)  # receive current scan speed
        current_scanspeed = str(current_scanspeed_raw.decode().split("speed ", 1)[1])  # extract scan speed from string
        self.scanspeed = float(current_scanspeed[:-3])  # extract scan speed from string

        self.s_monitor.sendall("(query 'laser1:dl:pc:voltage-act) \n".encode('utf8'))  # query current WL
        current_PV_raw = self.s_monitor.recv(self.BUFFER_SIZE)  # receive current WL
        current_PV_temp = str(current_PV_raw.decode().split("act ", 1)[1])  # extract WL from string
        current_PV_temp = current_PV_temp[:-3]  # extract WL from string
        self.current_PV = float(current_PV_temp)
        #self.s_monitor.close()

    def SetWavelength(self, lamb):
        if lamb > self.maxLamb:
            print("Wavelength larger than maximum allowed")
            return
        elif lamb < self.minLamb:
            print("Wavelength smaller than minimum allowed")
            return

        comm_string = "(param-set! 'laser1:ctl:wavelength-set " + str(lamb) + ") \n"

        #self.s_command = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.s_command.connect((self.DLC_IP, self.PORT_COM))  # connect to DLC command channel
        self.s_command.sendall(comm_string.encode('utf8'))  # move to new wavelength
        self.s_commandbuffer = self.s_command.recv(self.BUFFER_SIZE)
        #self.s_command.close()  # close DLC command channel

        delaytime = np.abs(self.current_wl-lamb)/self.scanspeed

        time.sleep(delaytime)

        #self.s_monitor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.s_monitor.connect((self.DLC_IP, self.PORT_MON))  # connect to DLC command channel
        self.s_monitor.sendall("(query 'laser1:ctl:wavelength-set) \n".encode('utf8'))  # query current WL
        current_wl_raw = self.s_monitor.recv(self.BUFFER_SIZE)  # receive current WL
        current_wl_temp = str(current_wl_raw.decode().split("set ", 1)[1])  # extract WL from string
        current_wl_temp = current_wl_temp[:-3]  # extract WL from string
        self.current_wl = float(current_wl_temp)
        print(self.current_wl)
        #self.s_monitor.close()

    def GetWavelength(self):
        #time.sleep(0.1)
        #self.s_monitor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.s_monitor.connect((self.DLC_IP, self.PORT_MON))  # connect to DLC command channel
        #self.s_monitor.sendall("(query 'laser1:ctl:wavelength-set)".encode('utf8'))  # query current WL
        #current_wl_raw = self.s_monitor.recv(self.BUFFER_SIZE)  # receive current WL
        #current_wl_temp = str(current_wl_raw.decode().split("set ", 1)[1])  # extract WL from string
        #current_wl_temp = current_wl_temp[:-3]  # extract WL from string
        #self.current_wl = float(current_wl_temp)
        #self.s_monitor.close()
        return self.current_wl


    def ScanWavelength(self, lambst, lambend, duration):
        self.SetWavelength(lambst)
        set_scanspeed = np.abs(lambst - lambend) / duration

        if set_scanspeed > 10:
            print("That scan speed is too fast! Setting scan speed to 10 nm/s and adjusting duration of experiment")
            duration = np.abs(lambst - lambend) / 10

        speed_string = "(param-set! 'laser1:ctl:scan:speed " + str(set_scanspeed) + ") \n"
        start_string = "(param-set! 'laser1:ctl:scan:wavelength-begin " + str(lambst) + ") \n"
        end_string = "(param-set! 'laser1:ctl:scan:wavelength-end " + str(lambend) + ") \n"
        go_string = "(exec 'laser1:ctl:scan:start) \n"

        #self.s_command = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.s_command.connect((self.DLC_IP, self.PORT_COM))  # connect to DLC command channel

        self.s_command.sendall(speed_string.encode('utf8'))  # set speed
        self.s_commandbuffer = self.s_command.recv(self.BUFFER_SIZE)

        self.s_command.sendall(start_string.encode('utf8'))  # set start point
        self.s_commandbuffer = self.s_command.recv(self.BUFFER_SIZE)

        self.s_command.sendall(end_string.encode('utf8'))  # set end point
        self.s_commandbuffer = self.s_command.recv(self.BUFFER_SIZE)

        self.s_command.sendall(go_string.encode('utf8'))  # start
        self.s_commandbuffer = self.s_command.recv(self.BUFFER_SIZE)
        #self.s_command.close()  # close DLC command channel

    def SetPiezo(self, PV):
        if PV > self.maxV:
            print("Voltage larger than maximum allowed")
            return
        elif PV < self.minV:
            print("Voltage smaller than minimum allowed")
            return

        comm_string = "(param-set! 'laser1:dl:pc:voltage-set " + str(PV) + ") \n"

        #self.s_command = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.s_command.connect((self.DLC_IP, self.PORT_COM))  # connect to DLC command channel
        self.s_command.sendall(comm_string.encode('utf8'))  # move to new wavelength
        self.s_commandbuffer = self.s_command.recv(self.BUFFER_SIZE)
        #self.s_command.close()  # close DLC command channel

        delaytime = 0.05  # wait for the laser to move before reading position
        time.sleep(delaytime)

        #self.s_monitor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.s_monitor.connect((self.DLC_IP,self.PORT_MON))
        self.s_monitor.sendall("(query 'laser1:dl:pc:voltage-set) \n".encode('utf8'))  # query current WL
        current_PV_raw = self.s_monitor.recv(self.BUFFER_SIZE)  # receive current WL
        current_PV_temp = str(current_PV_raw.decode().split("set ", 1)[1])  # extract WL from string
        current_PV_temp = current_PV_temp[:-3]  # extract WL from string
        self.current_PV = float(current_PV_temp)
        #self.s_monitor.close()

    def GetPiezo(self):
        return self.current_PV

