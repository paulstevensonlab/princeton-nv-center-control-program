/**                                                                      */
/* \file clcamdll.h                                                      */
/* $------------------------------------------------------------------$  */
/*                                                                       */
/* $Workfile:: cldevdll.h                                             $  */
/* $Revision:: 4                                                      $  */
/* $Date:: 5/19/06 1:22p                                              $  */
/* $Author:: Daves                                                    $  */
/*                                                                       */
/* $------------------------------------------------------------------$  */
/*                                                                       */
/* $Description::                                                     $  */
/* Critical Link Device DLL Interface Header File.
 *
 */
/*                                                                       */
/* $------------------------------------------------------------------$  */
/*                                                                       */
/* $History:: cldevdll.hmnZopLeft
                                              $  */
/*                                                                        */
/*   *****************  Version 4  *****************                      */
/*   User: Daves        Date: 5/19/06    Time: 1:22p                      */
/*   Updated in $/Bristol/621/Software/PC_Software/common                 */
/*                                                                        */
/*   *****************  Version 3  *****************                      */
/*   User: Daves        Date: 1/18/06    Time: 5:55p                      */
/*   Updated in $/Bristol/621/Software/PC_Software/common                 */
/*                                                                        */
/*   *****************  Version 2  *****************                      */
/*   User: Daves        Date: 8/19/05    Time: 6:11p                      */
/*   Updated in $/Bristol/621/Software/PC_Software/common                 */
/*                                                                        */
/*   *****************  Version 1  *****************                      */
/*   User: Daves        Date: 7/25/05    Time: 5:00p                      */
/*   Created in $/Bristol/621/Software/PC_Software/common                 */
/*                                                                        */
/*   *****************  Version 1  *****************                      */
/*   User: DaveS        Date: 5/11/05    Time: 10:56a                     */
/*   Created in $/Critical Link/Device/PC_Software/common                 */
/*                                                                       */
/* $------------------------------------------------------------------$  */
/*                                                                       */
/*    o  0                                                               */
/*    | /       Copyright (c) 2005                                       */
/*   (CL)---o   Critical Link, LLC                                       */
/*     \                                                                 */
/*      O                                                                */
/*************************************************************************/

#ifndef DEVSDK_H
#define DEVSDK_H

// DLL name
#define DLL_NAME                        TEXT("devsdk.dll")

#define CCD_DATA_LEN 1024

enum { LAMBDA_UNIT_NM, LAMBDA_UNIT_GH, LAMBDA_UNIT_CM};
enum { POWER_UNIT_MW, POWER_UNIT_DB};
enum { MEDIUM_VACUUM, MEDIUM_AIR };
enum { ACQMODE_MEAS, ACQMODE_CAL, ACQMODE_ALIGN };

/// Make this header file usable by both the DLL and the user of the DLL
#ifdef BUILDING_THE_DLL
   #define DECLSPEC    __declspec(dllexport)
#else
   #define DECLSPEC    __declspec(dllimport)
#endif

/**
 * @mainpage
 *
 * @section intro_sec Introduction
 *
 * The CLDevice interface library provides a C dynamic link library interface
 * to any number of Critical Link products powered by the MightyDSP framework.
 * The CLDevice interface supports communication to Critical Link products
 * using a standard Serial COM port (at 115 kBaud), a USB port (at 900 kBaud) and
 * also over Ethernet TCP/IP protocol.
 *
 * All Critical Link Devices handle commands in a pipeline fashion.
 *
 * @section example_sec Example
 *
 *
 */

#pragma pack(push,1)
/**
 * @name Device Measurement Info
 * This structure contains the measurement data
 */
//typedef struct TCLDeviceMeasurement
//{
//  unsigned int    RefFringeCount;   //!< Reference fringe count
//  unsigned int    InputFringeCount; //!< InputFringeCount
//  float           StartPhase;       //!< Start Phase
//  float           EndPhase;         //!< End Phase
//  float           Temperature;      //!< Temperature
//  float           Pressure;         //!< Pressure
//  unsigned short  RefPower1;        //!< ReferencePower A/D reading
//  unsigned short  RefPower2;        //!< ReferencePower A/D reading
//  float           InputPower;       //!< Input power 10nW to 20mW
//} DEVICE_MEASUREMENT;



typedef struct
{
    unsigned int    ScanIndex;
    unsigned int    Status;
    unsigned int    RefFringeCnt;
    unsigned int    InpFringeCnt;
    float           StartPhase;
    float           EndPhase;
    float           Temperature;
    float           Pressure;
    unsigned short  RefPower1;
    unsigned short  RefPower2;
    float           InputPower;
    double          Wavelength;
} tsMeasurementDataType;


#define MAX_K                   32
#define NUM_FIFO_DWORDS         6
typedef struct
{
    unsigned int mnNumEntries;
    unsigned int mnReferenceBlockCount;
    unsigned int mnReferenceBlockSize;
    unsigned int    Filler;

    unsigned int maFringeData[MAX_K][NUM_FIFO_DWORDS];

} tsScanDataType;


#define RESPONS_TBL_LEN     32
#define VERS_LEN            8
#define RESPONS_ENTRIES     16
#define RESPONS_WAVE        0
#define RESPONS_VAL         1

typedef struct
{
    unsigned int    mnZopLeft;
    unsigned int    mnZopRight;
    unsigned int    mnSerialNumber;
    float           mnCorrectionWavelength1;
    float           mnCorrectionCoefficient_1;
    float           mnCorrectionWavelength2;
    float           mnCorrectionCoefficient_2;
    float           mnPowerCalibrationCoeff;
    char            maFirmwareVersion[VERS_LEN];
    char            maSoftwareVersion[VERS_LEN];
    int             mnMaxRefIntensity;
    float           mnTemperatureOffset;
    float           mnPressureOffset;
    unsigned char   mnUnitModel;
    unsigned char   meLaserType;
    unsigned char   mnRefGainSetting;
    unsigned char   mnUnusedC2;
    float           mnSelfCalCoef;
    float           mnSelfCalTemp;
    float           mnPowerCalibrationOffset;
    float           mnSelfCalTempCoef;
    unsigned int    mnConfigBits;
    float           mnInpGainThreshA;
    float           mnInpGainThreshB;
    float           mnInpGainThreshC;
    unsigned int    mnUnused7;
    unsigned int    mnUnused8;
    float           maDetectorResponsivity[RESPONS_ENTRIES][2];
} tsUnitInfoTypeA;

typedef struct
{
//  unsigned int    mnZopLeft;
    float           mnEtlAThick;
    float           mnEtlBThick;
//  unsigned int    mnZopRight;
    unsigned int    mnSerialNumber;
    float           mnCorrectionWavelength1;
    float           mnCorrectionCoefficient_1;
    float           mnCorrectionWavelength2;
    float           mnCorrectionCoefficient_2;
//  float           mnPowerCalibrationCoeff;
    unsigned short  mnCalLocA;
    unsigned short  mnCalLocB;
    char            maFirmwareVersion[VERS_LEN];
    char            maSoftwareVersion[VERS_LEN];
    int             mnMaxRefIntensity;
    float           mnTemperatureOffset;
    float           mnPressureOffset;
    unsigned char   mnUnitModel;
    unsigned char   meLaserType;
    unsigned char   mnRefGainSetting;
    unsigned char   mnUnusedC2;
    float           mnSelfCalCoef;
    float           mnSelfCalTemp;
    float           mnPowerCalibrationOffset;   //nope
    float           mnSelfCalTempCoef;
    unsigned int    mnConfigBits;
    float           mnInpGainThreshA;
    float           mnInpGainThreshB;
    float           mnInpGainThreshC;
    unsigned int    mnUnused7;
    unsigned int    mnUnused8;
    float           maDetectorResponsivity[RESPONS_ENTRIES][2];
    float           maDetectorCalCurves[RESPONS_ENTRIES][3];
} tsUnitInfoTypeB;

enum {AUTO_SND_OFF, AUTO_SND_UNUSED, AUTO_SND_MEAS, AUTO_SND_SCAN};

enum {MODEL_UNDEF, MODEL_621A, MODEL_621B, MODEL_521};

//typedef struct
//{
//  tsMeasurementDataType   msMeasData;
//} tsMeasHBType;
#define tsMeasHBType tsMeasurementDataType


struct tsHeartBeatType
{
    unsigned int            mnScanIndex;
    unsigned int            mnStatus;
    tsMeasurementDataType   msMeasData;
    tsScanDataType          msScanData;
    double                  maWaveLengths[MAX_K];
};


typedef struct
{
    unsigned int            mnScanIndex;
    unsigned int            mnStatus;
    unsigned short          maCCDdata[CCD_DATA_LEN];
} tsCCDdataType;
#pragma pack(pop)


/**
 * This is the required function prototype that an application must use to register
 * a callback for the Critical Link Camera HeartBeat Data.
 *
 * \param data A pointer to the DLL allocated data structure.  This structure is not
 *             valid after the callback function returns.  The Application should copy
 *             any data from this structure prior to returning from the callback function.
 */
typedef void (*MEASHBCALLBACK)(tsMeasHBType* data);

/**
 * This is the required function prototype that an application must use to register
 * a callback for the Critical Link Camera HeartBeat Data.
 *
 * \param data A pointer to the DLL allocated data structure.  This structure is not
 *             valid after the callback function returns.  The Application should copy
 *             any data from this structure prior to returning from the callback function.
 */
typedef void (*HEARTBEATCALLBACK)(tsHeartBeatType* data);

typedef void (*IMAGECALLBACK)(unsigned char *data);

// Function prototypes

#ifdef __cplusplus
extern "C" {    // only need to export C interface if
                // used by C++ source code
#endif



//=====================================================================
//
//      SETUP COMMANDS
//
//=====================================================================

/**
 * Get the current version level of the CLDevice Interface Dynamic Link Library.
 *
 * \return integer representation of version in decimal, the DLL version number is
 *         a time stamp, printed as Ymmddhhmm in decimal.
 */
DECLSPEC int __cdecl CLGetDllVersion();


/**
 * This functions checks to see if device is ready
 *
 * \param DeviceHandle  Handle to a tcCLDevice that was opened.
 */
DECLSPEC int __cdecl CLisDeviceReady(int DeviceHandle);


/**
 * Open a CLDevice using an RS-232 Serial Port Interface.
 * \param ComNumber the windows COM Port number (1 through 4)
 * \return a valid CLDevice Handle, or -1 on failure
 */
DECLSPEC int __cdecl CLOpenSerialDevice(int ComNumber);

/**
 * Open a CLDevice using an USB Serial Port Interface.
 * \param ComNumber the windows COM Port number (1 through 8)
 * \return a valid CLDevice Handle, or -1 on failure
 */
DECLSPEC int __cdecl CLOpenUSBSerialDevice(int ComNumber);

/**
 * Close/Clean up resouces associated with a CLDevice Handle
 *
 * \param DeviceHandle a valid CLDevice Handle
 * \return non-zero on error
 */
DECLSPEC int __cdecl CLCloseDevice(int DeviceHandle);




/**
 * Method to write to the CLDevice zero-bias DAC controlled.
 *
 * \note Should this method be available in the DLL?
 *
 * \param DeviceHandle a valid CLDevice Handle
 * \param DACaddr      Address of the DAC
 * \param DACdata      Value to write to the DAC
 * \return non-zero on error.
 */
//DECLSPEC int __cdecl CLWriteDAC( int DeviceHandle, unsigned char DACaddr, unsigned short  DACdata);

/**
 * Sets a user defined callback function in order to receive measurement heartbeat information.
 * The pointer in the callback function may not be valid following a return from the callback
 * function.  Users should make local copies of the data if it is necessary to preserve the
 * information following the callback processing.
 *
 * \param CameraHandle a valid CLCamera Handle
 * \param ProcessHeartBeatData User Supplied Callback Function
 * \return non-zero on error
 */
DECLSPEC int __cdecl CLSetMeasHBCallback(int DeviceHandle, MEASHBCALLBACK ProcessMeasHBData);

/**
 * Sets a user defined callback function in order to receive scan heartbeat information.
 * The pointer in the callback function may not be valid following a return from the callback
 * function.  Users should make local copies of the data if it is necessary to preserve the
 * information following the callback processing.
 *
 * \param CameraHandle a valid CLCamera Handle
 * \param ProcessHeartBeatData User Supplied Callback Function
 * \return non-zero on error
 */
DECLSPEC int __cdecl CLSetHeartBeatCallback(int DeviceHandle, HEARTBEATCALLBACK ProcessHeartBeatData);

DECLSPEC int __cdecl CLSetImageCallback(int DeviceHandle, IMAGECALLBACK ProcessImageData);


#if(1 == 3)
/**
 * This function resets the communications link between the camera and PC
 * and stops any camera operation that is pending.
 *
 * \param DeviceHandle a valid CLDevice Handle
 * \return non-zero on error.
 */
DECLSPEC int __cdecl CLDeviceReset (int DeviceHandle);
#endif

/**
 * Read a 32 bit register from the Critical Link Device embedded Mighty DSP.
 *
 * \note Should this method be available in the DLL?
 *
 * \param DeviceHandle  a valid CLDevice Handle
 * \param peekAddr Address to Read
 * \param *peekData pointer to location to store read value
 * \return non-zero on error.  This method is a blocking call.
 */
DECLSPEC int __cdecl CLRead32Data(int DeviceHandle, unsigned long peekAddr,unsigned long *peekData);

/**
 * Write a 32 bit register to the Critical Link Device embedded Mighty DSP.
 *
 * \note Should this method be available in the DLL?
 *
 * \param DeviceHandle  a valid CLDevice Handle
 * \param pokeAddr Addres to Write
 * \param pokeData value to write
 * \return non-zero on error.  This method is a blocking call.
 */
DECLSPEC int __cdecl CLWrite32Data(int DeviceHandle, unsigned long pokeAddr,unsigned long pokeData);

/**
 * Utility command used to pass engineering commands to the DLL software.
 *
 * \note Should this method be available in the DLL?
 *
 * Current commands include:
 * 2 - turn on detailed logging
 * 1 - disable detailed logging
 *
 * \param DeviceHandle  a valid CLDevice Handle
 * \param command       integer command (1-2 are supported)
 * \param pData         data block for optional command parameters
 * \return non-zero on error.  This method is a blocking call.
 */
DECLSPEC int __cdecl CLEngineeringCommand(int DeviceHandle, int command, char * pData);


/**
 * Sets the number of Averages to do when Average is enabled
 *
 *
 *
 * \param DeviceHandle a valid CLDevice Handle
 * \param Averages is number of averages
 * \return non-zero on error.
 */
DECLSPEC int __cdecl CLSetAverageValue (int DeviceHandle, unsigned int Averages);

/**
 * Enables averaging
 *
 *
 *
 * \param DeviceHandle a valid CLDevice Handle
 * \param Enable  0 - disable averaging, 1 - enable
 * \return non-zero on error.
 */
DECLSPEC int __cdecl CLSetAverageEnable (int DeviceHandle, char Enable);

/**
 * Reads the current CCD temperature on the CLDevice.
 *
 * \param DeviceHandle a valid CLDevice Handle
 * \param *temp        location to write the temperature (signed short, LSB = 0.1 degrees C)
 * \return  non-zero on error. This is a blocking function call.
 */
//DECLSPEC int __cdecl CLGetMeasurment(int DeviceHandle, short *temp);

DECLSPEC int __cdecl CLUnitInfo(int DeviceHandle, short *temp);

DECLSPEC int __cdecl CLGetA2DReading(int DevHandle, unsigned int channel, unsigned int *value);

DECLSPEC int __cdecl CLSetDacValue(int DevHandle, unsigned int channel, unsigned int value);

DECLSPEC int __cdecl CLGetMeasurementData(int DevHandle, tsMeasurementDataType *data);

DECLSPEC int __cdecl CLGetLambdaReading2(int DevHandle, double *data);

DECLSPEC int __cdecl CLGetScanData(int DevHandle, tsScanDataType *data);

DECLSPEC int __cdecl CLGetUnitInfo(int DevHandle, tsUnitInfoTypeA *data);

DECLSPEC int __cdecl CLSetUnitInfo(int DevHandle, tsUnitInfoTypeA *data);

DECLSPEC int __cdecl CLGetUnitInfoB(int DevHandle, tsUnitInfoTypeB *data);

DECLSPEC int __cdecl CLSetUnitInfoB(int DevHandle, tsUnitInfoTypeB *data);

DECLSPEC int __cdecl CLSetAutoSend(int DevHandle, unsigned int Mode);

DECLSPEC int __cdecl CLSetCalibrationPeriod(int DevHandle, int Minutes);

DECLSPEC int __cdecl CLSetMotorSpeed(int DevHandle, unsigned int speed);

DECLSPEC int __cdecl CLSetPowerGain(int DevHandle, unsigned int gains);

DECLSPEC int __cdecl CLSetLambdaUnits(int DevHandle, unsigned int LambaUnits);
DECLSPEC int __cdecl CLSetPowerUnits(int DevHandle, unsigned int PowerUnits);
DECLSPEC double __cdecl CLGetLambdaReading(int DevHandle);
DECLSPEC float __cdecl CLGetPowerReading(int DeviceHandle);
DECLSPEC int __cdecl CLSetMedium(int DevHandle, unsigned int medium);
DECLSPEC int __cdecl CLUserCalibrate(int DevHandle);
DECLSPEC int __cdecl CLSetAcqFreq(int DevHandle, unsigned int freq);

DECLSPEC int __cdecl CLGetCCDdata(int DevHandle, tsCCDdataType *data);
DECLSPEC int __cdecl CLSetAcqMode(int DevHandle, int Mode);
DECLSPEC int __cdecl CLSetUnusedCmd1(int DevHandle, int un);
DECLSPEC int __cdecl CLSetUnusedCmd2(int DevHandle, int un);
DECLSPEC int __cdecl CLGetUnusedCmd1(int DevHandle, void *un);


#ifdef __cplusplus
}
#endif


#endif

