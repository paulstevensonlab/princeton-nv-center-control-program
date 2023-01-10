
#Instrument class for SolsTis-PSX

#Transmission ID is mandatory and definitivily pairs the server response with the cleint message.
#status convention is command specific, but in general status = 0 is successful. See manual.
# optional report must be queried after the main recieved transmission.  e.g. after s.sendall() must run s.recv() twice if option report enabled.
import sys
import time
import socket
import simplejson as json
import numpy as np

class SolsTiS:
    def __init__(self, ip='192.168.1.222', pcIPin = '192.168.1.100'):
        print('picIPin: %s' % pcIPin)
        self.RemotePort = 4068 # Port set for remote communications in SolsTis web GUI
        self.SolsTisIP = ip #ip adress of SolsTis (ICE-BLOCK)
        self.pcIP = pcIPin #ip address of remote PC
        self.transmission_id = 1
        self.isconnected = False

        ###  laser specific parameters  ### I figured out the max Etalon V and resonator V just manually from the web GUI
        self.minLamb = 697 #nm
        self.maxLamb = 1000 # nm

        self.maxEtalonV = 197# volts
        self.etalonRange = 250 # GHz
        self.tolerance = 0.01 # nm Needs to match the initial value put on the ESR params table
        self.maxResonatorV = 197# volts
        self.resonatorRange = 30 # GHz
        self.NAvePLESlow = 1
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("Socket successfully created")
        except socket.error as err:
            print("socket creation failed with error %s" % (err))
            sys.exit()  #correct?

        try:
            self.host_ip = socket.gethostbyname(self.SolsTisIP)
        except socket.gaierror:
            # this means could not resolve the host
            print("There was an error resolving the SolsTiS PSX-XF host")
            sys.exit() #correct?

        self.connect()

        if self.isconnected:
            self.startLink()
        if self.isconnected:
            time.sleep(1)
            self.tuneEtalon(50)
            self.tuneResonator(50)
            self.setWavelengthTolerance(self.tolerance)
    def connect(self):
        try:
            self.s.settimeout(1) #seconds?
            self.s.connect((self.host_ip,self.RemotePort))
            self.isconnected = True
            print('Connected to SolsTiS PSX-XF.')
        except socket.error:
            print('Error connecting to SolsTiS PSX-XF.')
            self.isconnected = False

    def queryJSON(self, data, recSize = 1000):
        try:
            jsonObj = json.dumps(data)
            self.s.sendall(jsonObj.encode('utf-8'))
            received = self.s.recv(recSize)
        except AttributeError:
            print('Error in queryJSON.')
        return received

    def receiveJSON(self, recSize = 1000):
        try:
            received = self.s.recv(recSize)
        except AttributeError:
            print('Error in receiveJSON.')
        return received

    def startLink(self):
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'start_link', 'parameters':{'ip_address': self.pcIP}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        self.transmission_id += 1
        try:
            ip = temp['message']['parameters']['ip_address']
            status = temp['message']['parameters']['status']
            if status == 'ok':
                print('Succesful startLink with SolsTis-PSX at ip: %s' % ip)
            else:
                print('Unsuccessful startLink with SolsTis-PSX')
                self.isconnected = 0
            return status
        except:
            print('Error in startLink, check ip addresses.')
            self.isconnected = 0
            return -1


    def pingLink(self):
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'ping', 'parameters':{'text_in':'Hello Laser'}}}
        print(self.queryJSON(data))
        self.transmission_id += 1

    def setWavelength(self, lambSet):
        data = {'message': {'transmission_id':[self.transmission_id], 'op':'set_wave_m', 'parameters':{'wavelength':[lambSet]}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        lambRet = temp['message']['parameters']['wavelength'][0]
        status = temp['message']['parameters']['status'][0]
        #print('Wavelength set to: %f (nm)' % lambRet)  #float
        #print('Status: %d'% status)
        self.transmission_id += 1
        return status

    def setWavelengthTolerance(self,tolerance):
        self.tolerance=tolerance
        data = {'message':{'transmission_id':[self.transmission_id],'op':'set_wave_tolerance_m','parameters':{'tolerance':[tolerance]}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        # print('Wavelength set to: %f (nm)' % lambRet)  #float
        # print('Status: %d'% status)
        self.transmission_id += 1


    def getWavelengthTolerance(self):
        return self.tolerance

    def setNAvePLESlow(self, Nave):
        self.NAvePLESlow = Nave

    def getNAvePLESlow(self):
        return self.NAvePLESlow

    # def setWavelengthScan(self, lambSet):
    #     #tolerance = 0.001 #nm
    #     itrMax = 100
    #     itr = 0
    #     escape = False
    #     self.unlockWavelength()
    #     self.setWavelength(lambSet)
    #     while escape == False:
    #         itr+=1
    #         lambC = self.getWavelength()
    #         print('After get wavelength: %f' % lambC)
    #         time.sleep(0.3)
    #         if(abs(lambC-lambSet) < self.tolerance):
    #             escape = True
    #             self.stopWaveTune()
    #             self.lockWavelength()
    #             #print('setWavelengthScan converged')
    #         if(itr >= itrMax):
    #             escape = True
    #             self.stopWaveTune()
    #             print('setWavelengthScan reached itrMax without converging')
    def setWavelengthScan(self, lambSet):
        #tolerance = 0.001 #nm
        itrMax = 100
        itr = 0
        escape = False
        self.unlockWavelength()
        self.setWavelength(lambSet)
        while escape == False:
            itr+=1
            (lambC,status) = self.getWavelengthStatus()
            #print('After get wavelength: %f' % lambC)
            time.sleep(0.3)
            if(status == 0):
                self.setWavelength(lambSet)
            if(status == 3):
                escape = True
                self.stopWaveTune()
                #print('Final wavelength: %f' % lambC)
                #print('status %d'%status)
                #self.lockWavelength()
                #print('setWavelengthScan converged')
            if(itr >= itrMax):
                escape = True
                self.stopWaveTune()
                print('setWavelengthScan reached itrMax: lambSet=%f, lambCur=%f' % (lambSet,lambC))

    def getWavelength(self):
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'poll_wave_m'}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        lambRet = temp['message']['parameters']['current_wavelength'][0]
        status = temp['message']['parameters']['status'][0] #0 tuning not active,1 no wm link, 2 tuning in progress, 3 wavelength being maintained
        self.transmission_id += 1
        if status == 1:
            print('No WM Link')
        #elif status == 2:
            #print('Tuning in progress')
        #return lambRet
        return lambRet

    def getWavelengthStatus(self):
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'poll_wave_m'}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        lambRet = temp['message']['parameters']['current_wavelength'][0]
        status = temp['message']['parameters']['status'][0] #0 tuning not active,1 no wm link, 2 tuning in progress, 3 wavelength being maintained
        self.transmission_id += 1
        if status == 1:
            print('No WM Link')
        #elif status == 2:
            #print('Tuning in progress')
        #return lambRet
        return (lambRet,status)

    def lockWavelength(self):
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'lock_wave_m', 'parameters':{'operation':'on'}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1
        # if status == 0:
        #     print('Wavelength locked successfully.')
        # else:
        #     print('No link to wave meter or no meter configured.')
        return status

    def unlockWavelength(self):
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'lock_wave_m', 'parameters':{'operation':'off'}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1
        # if status == 0:
        #     print('Wavelength unlocked successfully.')
        # else:
        #     print('No link to wave meter or no meter configured.')
        return status


    def stopWaveTune(self):
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'stop_wave_m'}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        lamb = temp['message']['parameters']['current_wavelength'][0]  #current wavelength after stop tune
        self.transmission_id += 1
        # if status == 0:
        #     print('Successful stopWaveTune.')
        # else:
        #     print('Unsuccessful in stopWaveTune.')
        return status

    def startWaveTuneTable(self, lambSet): ######start table tune.  No wavemeter needed.
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'move_wave_t', 'parameters':{'wavelength':[lambSet]}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1

        if status == 2:
            print('startWaveTuneTable: Set wavelength out of range.')
        elif status>0:
            print('Unsuccessful in startWaveTuneTable.')
        return status

    def pollTableTune(self, delay=0): #status: 0 = tuning complete, 1 = tuning in progress, 2 = tuning operation failed
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'poll_move_wave_t'}}
        time.sleep(delay)
        received = self.queryJSON(data)
        temp = json.loads(received)
        lamb = temp['message']['parameters']['current_wavelength'][0]
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1
        return (lamb, status)

    def pollTableTuneFromField(self): #status: 0 = tuning complete, 1 = tuning in progress, 2 = tuning operation failed
        time.sleep(0.3)
        status = 1
        while status != 0:
            data = {'message':{'transmission_id':[self.transmission_id], 'op':'poll_move_wave_t'}}
            received = self.queryJSON(data)
            temp = json.loads(received)
            lamb = temp['message']['parameters']['current_wavelength'][0]
            status = temp['message']['parameters']['status'][0]
            self.transmission_id += 1
        return lamb

    # def pollTableTuneNoStatus(self): #status: 0 = tuning complete, 1 = tuning in progress, 2 = tuning operation failed
    #     data = {'message':{'transmission_id':[self.transmission_id], 'op':'poll_move_wave_t'}}
    #     received = self.queryJSON(data)
    #     temp = json.loads(received)
    #     lamb = temp['message']['parameters']['current_wavelength'][0]
    #     status = temp['message']['parameters']['status'][0]
    #     self.transmission_id += 1
    #     return lamb

    def stopTableTune(self):
        data = {'message': {'transmission_id':[self.transmission_id], 'op':'stop_move_wave_t'}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1
        if status == 0:
            print('stopTable Tune Completed.')
        else:
            print('Unsuccessful in stopTableTune')
        return status

    def tuneEtalon(self, percent):  #optional report and percent parameters is 0-100
        if(percent < 0 or percent > 100):
            print('Error in tuneEtalon, percent out of range.')
            return -1
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'tune_etalon', 'parameters':{'setting':[percent]}}}
        print('sent: {}'.format(json.dumps(data)))
        received = self.queryJSON(data)
        temp = json.loads(received)
        print('recieved: {}'.format(temp))
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1
        if status == 0:
            print('tuneEtalon completed.')
        else:
            print('Unsuccessful in tuneEtalon')
        return status

    def getEtalon(self):
        (wavelength, temperature, etalonLock, etalonLock, etalonV, resonatorV, outputMonitor, etalonPD, status) = self.systemStatus()
        return etalonV[0]/self.maxEtalonV*100

    def getEtalonFromField(self):
        time.sleep(1)
        (wavelength, temperature, etalonLock, etalonLock, etalonV, resonatorV, outputMonitor, etalonPD,
         status) = self.systemStatus()
        return etalonV[0] / self.maxEtalonV * 100

    def tuneResonator(self, percent):  #optional report and percent parameters is 0-100
        if(percent < 0 or percent > 100):
            print('Error in tuneResonator, percent out of range.')
            return -1
        data = {'message': {'transmission_id':[self.transmission_id], 'op':'tune_resonator', 'parameters':{'setting':[percent]}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1
        if status == 0:
            print('tuneResonator completed.')  #change to log
        else:
            print('Unsuccessful in tuneResonator')
        return status

    def getResonator(self):
        (wavelength, temperature, etalonLock, etalonLock, etalonV, resonatorV, outputMonitor, etalonPD, status) = self.systemStatus()
        print('ResonatorV = %f', resonatorV)
        return resonatorV[0]/self.maxResonatorV*100

    def getResonatorFromField(self):
        time.sleep(1)
        (wavelength, temperature, etalonLock, etalonLock, etalonV, resonatorV, outputMonitor, etalonPD, status) = self.systemStatus()
        print('ResonatorV = %f', resonatorV)
        return resonatorV[0] / self.maxResonatorV * 100

    #difference between fine_tune_resonator and tune_resonator?
    def fineTuneResonator(self, percent):  #optional report and percent parameters is 0-100
        if(percent < 0 or percent > 100):
            print('Error in fineTuneResonator, percent out of range.')
            return -1
        data = {'message': {'transmission_id':[self.transmission_id], 'op':'fine_tune_resonator', 'parameters':{'setting':[percent]}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1
        if status == 0:
            print('fineTuneResonator completed.')
        else:
            print('Unsuccessful in fineTuneResonator')
        return status

    def lockEtalon(self):
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'etalon_lock', 'parameters':{'operation':'on'}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1
        # if status == 0:
        #     print('Etalon locked successfully.')
        if status != 0:
            print('Etalon lock unsuccesful.')
        return status

    def unlockEtalon(self):
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'etalon_lock', 'parameters':{'operation':'off'}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1
        # if status == 0:
        #     print('Etalon unlocked successfully.')
        if status != 0:
            print('Etalon unlock unsuccesful.')
        return status
    def setEtalonLockFromField(self, input):
        if input == 1:
            self.etalonLockSearch()
        elif input == 0:
            self.unlockEalon()

    def etalonLockSearch(self):
        self.lockEtalon()
        condition, status = self.etalonLockStatus()
        if condition == 'on':
            escapeFlag = True
        else:
            escapeFlag = False
        etalonI = int(self.getEtalon())

        #print('Here in etalonLockSearch')
        #print('etalonI = %d' % etalonI)
        #print(np.arange(etalonI,0,-1))
        if escapeFlag == False:
            for ii in np.arange(etalonI,0,-1):

                self.tuneEtalon(int(ii))
                condition, status = self.etalonLockStatus()
                if condition == 'on':
                    escapeFlag = True
                    break

        if escapeFlag == False:
            for ii in np.linspace(0, 100,101):
                self.tuneEtalon(int(ii))
                condition, status = self.etalonLockStatus()
                if condition == 'on':
                    escapeFlag = True
                    break

        if escapeFlag == True:
            print('Etalon is locked')
        else:
            print('Etalon lock search failed')


    def etalonLockStatus(self): # 0 = completed, 1 = failed
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'etalon_lock_status'}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        condition = temp['message']['parameters']['condition'] #'off','on','debug','error','search','low'
        self.transmission_id += 1
        if status == 1:
            print('Error in query etalonLockStatus.')
        return (condition, status)

    def etalonLockStatusFromField(self):
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'etalon_lock_status'}}
        time.sleep(1)
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        condition = temp['message']['parameters']['condition'] #'off','on','debug','error','search','low'
        #print('etalonLockStatusFromField')
        #print('sent{}'.format(data))
        #print('received {}'.format(received))
        self.transmission_id += 1
        if status == 1:
            print('Error in query etalonLockStatus.')
        if condition == 'off':
            return 0
        elif condition == 'on':
            return 1
        else:
            return -1

    #general system query
    def systemStatus(self):
        data = {'message': {'transmission_id': [self.transmission_id], 'op': 'get_status'}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        wavelength = temp['message']['parameters']['wavelength'][0]
        temperature = temp['message']['parameters']['temperature'][0]
        etalonLock = temp['message']['parameters']['etalon_lock']
        etalonV = temp['message']['parameters']['etalon_voltage']
        resonatorV = temp['message']['parameters']['resonator_voltage']
        outputMonitor = temp['message']['parameters']['output_monitor']
        etalonPD = temp['message']['parameters']['etalon_pd_dc']
        self.transmission_id += 1
        if status == 1:
            print('Error in query systemStatus.')
        return (wavelength, temperature, etalonLock, etalonLock, etalonV, resonatorV, outputMonitor, etalonPD, status)

    #APAM
    def getAlignmentstatus(self):
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'get_alignment_status'}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        condition = temp['message']['parameters']['condition']
        status = temp['message']['parameters']['condition'][0]  #todo: status return parameter isn't in get_alignment_status documentation.. check if real
        xVol= temp['message']['parameters']['x_alignment'][0]
        yVol = temp['message']['parameters']['y_alignment'][0]
        self.transmission_id += 1
        if status == 1:
            print('Error in query etalonLockStatus.')
        return (xVol, yVol, condition)

    def runAlignment(self, mode): #mode: 1 - Manual, 2 - Automatic, 3 - Stop, 4 - One shot
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'beam_alignment', 'parameters':{'mode':[mode]}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1
        if status == 1:
            print('Error in runAlignement.')
        return status

    #todo: add x and y manual adjustment

    def initTeraScan(self, type='line', start=697, stop=1000, rate=20, units='GHz/s'):  #coarse not currently available????
        #todo: only allow correct input for start, stop, rate

        #first make sure units matches the scan type
        if type=="medium":
            if units=="Mhz/s" or units=="KHz/s":
                print('Error no units of type: %s for scan type:medium.' % units)
                return -1
        if type=="fine":
            if units=="KHz/s":
                print('Error no units of type: %s for scan type:fine.' % units)
                return -1
        #second make sure rate is valid given units and type
        if units=="GHz/s":
            if type=="medium":
                rateList = [100,50,20,15,10,5,2,1]
                if not rate in rateList:
                    print('initTeraScan: Error invalid rate!!!')
                    return -1
            if type=="fine" or type=="line":
                rateList = [20,10,5,2,1]
                if not rate in rateList:
                    print('initTeraScan: Error invalid rate!!!')
                    return -1
        if units=="MHz/s": # must be fine or narrow from filtering before
            rateList = [500,200,100,50,20,10,5,2,1]
            if not rate in rateList:
                print('initTeraScan: Error invalid rate!!!')
                return -1
        if units=="kHz/s":
            rateList = [500,200,100,50]
            if not rate in rateList:
                print('initTeraScan: Error invalid rate!!!')
                return -1
        data = {'message': {'transmission_id':[self.transmission_id], 'op':'scan_stitch_initialise','parameters':{'scan':type, 'start':[start], 'stop':[stop], 'rate':[rate], 'units':units}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1
        if status == 1:
            print('initTeraScan: Start out of range.')
        elif status == 2:
            print('initTeraScan: Stop out of range.')
        elif status == 3:
            print('initTeraScan: Scan out of range.')
        elif status == 4:
            print('initTeraScan: not available.')
        return status

    def operateTeraScan(self, type='line', operation='start'):
        data = {'message': {'transmission_id':[self.transmission_id], 'op':'scan_stitch_op', 'parameters':{'scan':type, 'operation':operation}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1
        if status == 1:
            print('operateTeraScan: failed')
        if status == 2:
            print('operateTeraScan: Terascan not available.')
        return status

    def continueTeraScan(self):
        data = {'message': {'transmission_id': [self.transmission_id], 'op': 'terascan_continue'}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        if status == 1:
            print('continueTeraScan: Operation failed, TeraScan was not pause.')
        if status == 2:
            print('continueTeraScan: TeraScan not available.')
        return status

    def statusTeraScan(self, type='line'):
        data = {'message': {'transmission_id':[self.transmission_id], 'op':'scan_stitch_status', 'parameters':{'scan':type}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        curLamb = -1
        curOp = -1
        if status == 1: #scan in progress
            curLamb = temp['message']['parameters']['current'][0]
            curOp = temp['message']['parameters']['operation'][0]
        self.transmission_id += 1
        if status == 2:
            print('statusTeraScan: Terascan not available.')
        return (curLamb, curOp, status)

    #legacy scan_stitch_output
    def configLambdaOutTeraScan(self, operation='start'): #start = start wavelength transmissions, stop = stop wavelength transmissions
        data = {'message': {'transmission_id': [self.transmission_id], 'op': 'scan_stitch_output','parameters':{'operation':operation}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1
        if status == 1:
            print('configLambdaOutTeraScan: operation failed.')
        elif status == 2:
            print('configLambdaOutTeraScan: Unused.')
        elif status == 3:
            print('configLambdaOutTeraScan: TeraScan not available.')
        return status

    def configOutputTeraScan(self, operation='start', delay=0, update=0, pause='off'): #start = start wavelength transmissions, stop = stop wavelength transmissions
        data = {'message': {'transmission_id': [self.transmission_id], 'op': 'terascan_output','parameters':{'operation':operation, 'delay':[delay], 'update':[update], 'pause':pause}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1
        if status == 1:
            print('configOutputTeraScan: operation failed.')
        elif status == 2:
            print('configOutputTeraScan: Delay period out of range.')
        elif status == 3:
            print('configOutputTeraScan: Update step out of range.')
        elif status == 4:
            print('configOutputTeraScan: TeraScan not available.')
        return status

    # todo: add monitor for wavelength reply "scan_stitch_wavlength"
    #need to decide how to implement this and return the wavelength in a semi fast manner.
    #also what happens when you ask for received and no message exists? maybe set timeout? does it return empty?
    def monitorTeraScanOutput(self):
        endF = False
        while not endF:
            received = self.receiveJSON()
            #sleep?
            temp = json.loads(received)
            curLamb = temp['message']['parameters']['wavelength']
            status = temp['message']['parameters']['status']
            if status=="end":
                endF = True

    def startFastScan(self, scan='etalon_continuous', width=100, time=10): #time in seconds, width in GHz
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'fast_scan_start','parameters':{'scan':scan, 'width':[width], 'time':[time]}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1
        if status == 1:
            print('startFastScan: Failed, scan width too great for current tuning position.')
        elif status == 2:
            print('startFastScan: Failed, reference cavity not fitted.')
        elif status == 3:
            print('startFastScan: Failed, ERC not fitted.')
        elif status == 4:
            print('startFastScan: Invalid scan type.')
        elif status == 5:
            print('startFastScan: Error, Time > 10000 seconds')
        return status

    def pollFastScan(self, scan='etalon_continuous'): #time in seconds, width in GHz
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'fast_scan_poll','parameters':{'scan':scan}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        tunerValue = temp['message']['parameters']['tuner_value'][0]
        self.transmission_id += 1
        if status == 2:
            print('pollFastScan: Failed, reference cavity not fitted.')
        elif status == 3:
            print('pollFastScan: Failed, ERC not fitted.')
        elif status == 4:
            print('pollFastScan: Invalid scan type.')
        return (tunerValue, status)

    def stopFastScan(self, scan='etalon_continuous'): #stop fast scan and return to start position
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'fast_scan_stop', 'parameters':{'scan':scan}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        self.transmission_id += 1
        status = temp['message']['parameters']['status'][0]
        if status == 2:
            print('stopFastScan: Failed, reference cavity not fitted.')
        elif status == 3:
            print('stopFastScan: Failed, ERC not fitted.')
        elif status == 4:
            print('stopFastScan: Invalid scan type.')
        return status

    def stopFastScanNR(self, scan='etalon_continuous'): #stop fast scan and do NOT return to start position
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'fast_scan_stop_nr','parameters':{'scan':scan}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        status = temp['message']['parameters']['status'][0]
        self.transmission_id += 1
        if status == 1:
            print('stopFastScanNR: Operation failed.')
        elif status == 2:
            print('stopFastScanNR: Failed, reference cavity not fitted.')
        elif status == 3:
            print('stopFastScanNR: Failed, ERC not fitted.')
        elif status == 4:
            print('stopFastScanNR: Invalid scan type.')
        return status

    def getWavelengthRange(self):
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'get_wavelength_range'}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        self.transmission_id += 1
        minLamb = temp['message']['parameters']['minimum_wavelength'][0]
        maxLamb = temp['message']['parameters']['maximum_wavelength'][0]
        numZones = temp['message']['parameters']['extended_zones'][0]
        #status = temp['message']['parameters']['status'][0]  #does status exist for this command?
        return (minLamb,maxLamb,numZones)

    def setWMChannel(self, chan=0, recovery=2): #for use with a multi-channel wavemeter and a fiber switch
        #recovery: 1=Reset the meter and proceed, 2 = wait for the meter to return to the channel, 3 = abandon the request
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'set_w_meter_channel', 'parameters':{'channel':[chan], 'recovery':[recovery]}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        self.transmission_id += 1
        status = temp['message']['parameters']['status'][0]
        if status == 1:
            print('setWMChannel: Command Failed')
        elif status == 2:
            print('setWMChannel: Channel out of range')
        return status

    def goToLambdaAndLock(self, lamb=946, operation='on'):
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'lock_wave_m_fixed','parameters':{'operation':operation, 'lock_wavelength':[lamb]}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        self.transmission_id += 1
        status = temp['message']['parameters']['status'][0]
        if status == 1:
            print('goToLambdaAndLock: no link to wavelength meter or no meter configured.')
        return status

    #todo: will need to fix/test readAllADC, not sure the format of some of the outputs
    def readAllADC(self):
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'read_all_adc'}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        self.transmission_id += 1
        status = temp['message']['parameters']['status'][0]
        if status == 1:
            print('readAllADC: operation failed.')
            return status
        elif status == 0:
            chcount = temp['message']['parameters']['channel count'][0]
            namArr = {''}
            valArr = np.zeros([chcount,1])
            unitArr = {''} #string of value?
            for i in range(0,chcount-1):
                namArr[i] = temp['message']['parameters']['channel %d' % i]
                valArr[i] = temp['message']['parameters']['value %d' % i][0]
                unitArr[i] = temp['message']['parameters']['units %d' % i]
            return (status, namArr, valArr, unitArr)

    def applyMonitorA(self,signal=2):
        #signal 1=etalon dither, 2=etalon voltage, 5=Resonator fast V, 6=resonator slow V, 7=Aux output PD, 8=Etalon Error
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'monitor_a', 'parameters':{'signal':[signal]}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        self.transmission_id += 1
        status = temp['message']['parameters']['status'][0]
        if status==1:
            print('applyMonitorA: operation failed')
        return status

    def applyMonitorB(self,signal=8):
        #signal 1=etalon dither, 2=etalon voltage, 5=Resonator fast V, 6=resonator slow V, 7=Aux output PD, 8=Etalon Error
        data = {'message':{'transmission_id':[self.transmission_id], 'op':'monitor_b', 'parameters':{'signal':[signal]}}}
        received = self.queryJSON(data)
        temp = json.loads(received)
        self.transmission_id += 1
        status = temp['message']['parameters']['status'][0]
        if status==1:
            print('applyMonitorA: operation failed')
        return status
