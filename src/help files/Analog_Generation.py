"""
This is an interpretation of the example program
C:\Program Files\National Instruments\NI-DAQ\Examples\DAQmx ANSI C\Analog Out\Generate Voltage\Cont Gen Volt Wfm-Int Clk\ContGen-IntClk.c
This routine will play an arbitrary-length waveform file.
This module depends on:
numpy
Adapted by Martin Bures [ mbures { @ } zoll { . } com ]
"""
# import system libraries
import ctypes
import numpy
import threading
import matplotlib.pylab as plt
from math import pi
import tkFileDialog, tkMessageBox, tkSimpleDialog
# load any DLLs
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
DAQmx_Val_ContSamps = 10123
DAQmx_Val_GroupByChannel = 0

DAQmx_Val_Diff = int32(-1)
DAQmx_Val_GroupByScanNumber = 1
DAQmx_SampleRate = float64(1e5) #max is float64(1e6)

##############################
class WaveformThread( threading.Thread ):
    """
    This class performs the necessary initialization of the DAQ hardware and
    spawns a thread to handle playback of the signal.
    It takes as input arguments the waveform to play and the sample rate at which
    to play it.
    This will play an arbitrary-length waveform file.
    """
    def __init__( self, waveform, sampleRate ):
        self.running = True
        self.sampleRate = sampleRate
        self.periodLength = len( waveform )
        self.taskHandle = TaskHandle( 0 )
        self.data = numpy.zeros( ( self.periodLength, ), dtype=numpy.float64 )
        # convert waveform to a numpy array
        for i in range( self.periodLength ):
            self.data[ i ] = waveform[ i ]
        # setup the DAQ hardware
        self.CHK(nidaq.DAQmxCreateTask("",
                          ctypes.byref( self.taskHandle )))
        self.CHK(nidaq.DAQmxCreateAOVoltageChan( self.taskHandle,
                                   "Dev1/ao0",
                                   "",
                                   float64(-10.0),
                                   float64(10.0),
                                   DAQmx_Val_Volts,
                                   None))

        self.CHK(nidaq.DAQmxCfgSampClkTiming( self.taskHandle,
                                "", 
                                float64(self.sampleRate),
                                DAQmx_Val_Rising,
                                DAQmx_Val_FiniteSamps,
                                uInt64(self.periodLength)));
        self.CHK(nidaq.DAQmxWriteAnalogF64( self.taskHandle,
                              int32(self.periodLength),
                              0,
                              float64(-1),
                              DAQmx_Val_GroupByChannel,
                              self.data.ctypes.data,
                              None,
                              None))
        threading.Thread.__init__( self )
    def CHK( self, err ):
        """a simple error checking routine"""
        if err < 0:
            buf_size = 100
            buf = ctypes.create_string_buffer('\000' * buf_size)
            nidaq.DAQmxGetErrorString(err,ctypes.byref(buf),buf_size)
            raise RuntimeError('nidaq call failed with error %d: %s'%(err,repr(buf.value)))
        if err > 0:
            buf_size = 100
            buf = ctypes.create_string_buffer('\000' * buf_size)
            nidaq.DAQmxGetErrorString(err,ctypes.byref(buf),buf_size)
            raise RuntimeError('nidaq generated warning %d: %s'%(err,repr(buf.value)))
    def run( self ):
        counter = 0
        self.CHK(nidaq.DAQmxStartTask( self.taskHandle ))
    def stop( self ):
        self.running = False
        nidaq.DAQmxStopTask( self.taskHandle )
        nidaq.DAQmxClearTask( self.taskHandle )

    def Read_Vals(self,Time):
        taskHandle = TaskHandle(1)

        max_num_samples = int(numpy.float32(DAQmx_SampleRate)*3*Time)

        data = numpy.zeros((max_num_samples,),dtype=numpy.float64)
        self.CHK(nidaq.DAQmxCreateTask("",ctypes.byref(taskHandle)))

        self.CHK(nidaq.DAQmxCreateAIVoltageChan(taskHandle,"Dev1/ai0:2","",          
                                                   DAQmx_Val_Diff,            #DAQmx_Val_Diff,   #DAQmx_Val_RSE,       #DAQmx_Val_Cfg_Default,
                                                   float64(-10.0),float64(10.0),
                                                   DAQmx_Val_Volts,
                                                   None))

        self.CHK(nidaq.DAQmxCfgSampClkTiming(taskHandle,
                                        "",
                                        DAQmx_SampleRate,
                                        DAQmx_Val_Rising,
                                        DAQmx_Val_FiniteSamps,
                                        uInt64(max_num_samples)))
        # DAQmxCfgSampClkTiming(taskHandle,"",sampleRate,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,sampsPerChan);      
        #DAQmx Start Code
        self.CHK(nidaq.DAQmxStartTask(taskHandle))



        read = int32()
        #DAQmx Read Code
        self.CHK(nidaq.DAQmxReadAnalogF64(taskHandle,
                                                 -1,
                                                 float64(10.0),    #Timeout in seconds
                                                 DAQmx_Val_GroupByScanNumber,       #DAQmx_Val_GroupByChannel,    #DAQmx_Val_GroupByScanNumber
                                                 data.ctypes.data, #the vairable being assinged?
                                                 max_num_samples,   #maximum number of samples
                                                 ctypes.byref(read),None))

        # print "Acquired %d points"%(read.value)
        if self.taskHandle.value != 0:
            nidaq.DAQmxStopTask(taskHandle)
            nidaq.DAQmxClearTask(taskHandle)

        Data = numpy.empty((max_num_samples/read.value,read.value))
        for i in range(max_num_samples/read.value):
            Data[i,:]= data[i::max_num_samples/(read.value-1)]
        # print 'Number of poitns collected:',Data.shape
        return Data


class LightPulse():

    A = 0.25

    def SinWave(self,t):
        xoff = numpy.zeros((int(SampleRate*0.1*t[-1])))
        x = -self.A*numpy.abs(numpy.sin(pi*t/t[-1]))

        return numpy.concatenate((xoff,x,xoff))

    def Square(self,t):
        xoff = numpy.zeros((int(SampleRate*0.1*t[-1])))
        x = -self.A*numpy.ones((t.shape[0]))

        return numpy.concatenate((xoff,x,xoff))

    def CosWave(self,t):
        xoff = numpy.zeros((int(SampleRate*0.1*t[-1])))
        x = -self.A*numpy.abs(numpy.cos(pi*t/t[-1]))

        return numpy.concatenate((xoff,x,xoff))

class OutPutData():
    def __init__( self ):
        self.file_opt = options = {}
        options['title'] = 'Save you data Dude!'
        options['defaultextension'] = r'Raw Data.dat'
        options['filetypes'] = [('Raw Data Files', r"Raw Data.*"),('all files', '.*')]

    def Save(self,Data):
        filename = tkFileDialog.asksaveasfilename(**self.file_opt)
        # print filename
        if not filename:
            print 'Canceled save'
        else:

            numpy.savetxt(filename,Data,delimiter='\t')

class TakeMeasurements():
    def __init__( self,x,Time,SampleRate):
        self.x=x
        self.Time=Time
        self.SampleRate=SampleRate
    def Measure(self):
        
        mythread = WaveformThread( self.x, self.SampleRate )
        # start playing waveform

        mythread.start()
        self.Data=mythread.Read_Vals(self.Time)

        mythread.stop()

if __name__ == '__main__':

    # generate a time signal 5 seconds long with 250Hz sample rate
    Time = 1
    SampleRate = 25000.0
   
    t = numpy.arange( 0, Time, 1.0/SampleRate )
    # generate sine wave with 0.1s where the LED if off

    xoff = numpy.zeros((SampleRate*0.1))

 

    x=LightPulse().SinWave(t)
    Time*=1.2
    Mea = TakeMeasurements(x,Time,SampleRate)
    Mea.Measure()

    x = numpy.linspace(0,Time,Mea.Data.shape[1])
    num=1
    fig=plt.figure('Raw Data')
    for i in range(3):
        if Mea.Data.shape[1]>10000:
            num=   Mea.Data.shape[1]//10000

        plt.plot(x[::num],Mea.Data[i,::num],'.',label='Channel: '+str(i))
        # plt.semilogy()
    plt.legend(loc=0)
    fig.show()
    OutPutData().Save(Mea.Data)
    plt.close(fig)
