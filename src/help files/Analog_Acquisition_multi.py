#Acq_IncClk.py
# This is a near-verbatim translation of the example program
# C:\Program Files\National Instruments\NI-DAQ\Examples\DAQmx ANSI C\Analog In\Measure Voltage\Acq-Int Clk\Acq-IntClk.c
import ctypes
import numpy
import matplotlib.pylab as plt
nidaq = ctypes.windll.nicaiu # load the DLL
##############################
# Setup some typedefs and constants
# to correspond with values in
# C:\Program Files\National Instruments\NI-DAQ\DAQmx ANSI C Dev\include\NIDAQmx.h
# the typedefs
int32 = ctypes.c_long
uInt32 = ctypes.c_ulong
uInt64 = ctypes.c_ulonglong
float64 = ctypes.c_double
TaskHandle = uInt32
# the constants
DAQmx_Val_Cfg_Default = int32(-1)
DAQmx_Val_Volts = 10348
DAQmx_Val_Rising = 10280
DAQmx_Val_FiniteSamps = 10178
DAQmx_Val_GroupByChannel = 0

DAQmx_Val_Diff = int32(-1)
DAQmx_Val_GroupByScanNumber = 1
DAQmx_SampleRate = float64(1e5)
##############################
def CHK(err):
    """a simple error checking routine"""
    if err < 0:
        buf_size = 100
        buf = ctypes.create_string_buffer('\000' * buf_size)
        nidaq.DAQmxGetErrorString(err,ctypes.byref(buf),buf_size)
        raise RuntimeError('nidaq call failed with error %d: %s'%(err,repr(buf.value)))
# initialize variables
def ReadData():
    taskHandle = TaskHandle(0)
    max_num_samples = int(3e5)
    print numpy.float32(DAQmx_SampleRate)
    print max_num_samples/numpy.float32(DAQmx_SampleRate)
    data = numpy.zeros((max_num_samples,),dtype=numpy.float64)
    # now, on with the program
    # DAQmx analog voltage channel and timing parameters
    CHK(nidaq.DAQmxCreateTask("",ctypes.byref(taskHandle)))
    CHK(nidaq.DAQmxCreateAIVoltageChan(taskHandle,"Dev3/ai0:2","",          
                                               DAQmx_Val_Diff,            #DAQmx_Val_Diff,   #DAQmx_Val_RSE,       #DAQmx_Val_Cfg_Default,
                                               float64(-10.0),float64(10.0),
                                               DAQmx_Val_Volts,
                                               None))
    CHK(nidaq.DAQmxCfgSampClkTiming(taskHandle,"",DAQmx_SampleRate, DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,uInt64(max_num_samples)))
    # DAQmxCfgSampClkTiming(taskHandle,"",sampleRate,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,sampsPerChan);      
    #DAQmx Start Code
    CHK(nidaq.DAQmxStartTask(taskHandle))



    read = int32()
    #DAQmx Read Code
    CHK(nidaq.DAQmxReadAnalogF64(taskHandle,
                                             -1,
                                             float64(10.0),    #Timeout in seconds
                                             DAQmx_Val_GroupByScanNumber,       #DAQmx_Val_GroupByChannel,    #DAQmx_Val_GroupByScanNumber
                                             data.ctypes.data, #the vairable being assinged?
                                             max_num_samples,   #maximum number of samples
                                             ctypes.byref(read),None))

    print "Acquired %d points"%(read.value)
    if taskHandle.value != 0:
        nidaq.DAQmxStopTask(taskHandle)
        nidaq.DAQmxClearTask(taskHandle)

    Data = numpy.empty((max_num_samples/read.value,read.value))
    for i in range(max_num_samples/read.value):
        Data[i,:]= data[i::max_num_samples/(read.value-1)]

    return Data

Data= ReadData()
print Data.shape

# print data.shape
# print data
# print "End of program, press Enter key to quit"
# raw_input()
x = numpy.linspace(0,1,Data.shape[1])
for i in range(3):
    plt.plot(x,Data[i,:]*(-1)**i,label='Channel: '+str(i))
plt.show()