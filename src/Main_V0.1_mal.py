# -*- coding: utf-8 -*-

################
# This is a GUI for the QSSPL system. It interfaces with USB6356 NI DAQ card.
# Currently it is assumed that the NI card is DEV1, and it reads three channels, and outputs on 1. This could all be changed, but i'm not sure why I want to yet.
#
#   To use this the NI drives need to be installed!
#
# Things to improve:
#
#   Definition of Dev/ and channels
#   Selectable inputs and output voltage ranges.
#   Make that you cna't load incorrect values (int and floats at least)
##############


# importing wx files
import wx
import sys
import os

# import the newly created GUI file
import gui.main as gui

sys.path.append('/home/mattias/Dropbox/CommonCode/Constants')
sys.path.append('C:\Users\mattias\Dropbox\CommonCode\Constants')
sys.path.append('C:\Users\Shanoot\Dropbox\CommonCode\Constants')
sys.path.append('C:\Users\z3186867\Dropbox\CommonCode\Constants')

from ConstantsClass import *
from CanvasClass import *

from matplotlib.pylab import *
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas

import tkFileDialog  # for saving

import numpy as np

import time

import ctypes
import threading
import matplotlib.pylab as plt
from math import pi
# load any DLLs
nidaq = ctypes.windll.nicaiu  # load the DLL
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

# max is float64(1e6), well its 1.25MS/s/channel
DAQmx_InputSampleRate = float64(1.2e6)
DAQmx_OutPutSampleRate = float64(1.2e6)  # Its 3.33MS/s


class WaveformThread(threading.Thread):
    DAQmx_Val_Cfg_Default = int32(-1)
    DAQmx_Val_Volts = 10348
    DAQmx_Val_Rising = 10280
    DAQmx_Val_FiniteSamps = 10178
    DAQmx_Val_ContSamps = 10123
    DAQmx_Val_GroupByChannel = 0
    Daq_Channels_Number = 3

    DAQmx_Val_Diff = int32(-1)
    # this controls the input voltage range. (=-10,=-5, =-2,+-1)
    InputVoltageRange = 10
    # this controls the  output voltage range. Minimum is -5 to 5
    OutputVoltageRange = 10
    # this places the points one at a time from each channel, I think
    DAQmx_Val_GroupByScanNumber = 0
    """
    This class performs the necessary initialization of the DAQ hardware and
    spawns a thread to handle playback of the signal.
    It takes as input arguments the waveform to play and the sample rate at which
    to play it.
    This will play an arbitrary-length waveform file.
    """

    def __init__(self, waveform, Channel, Time):
        self.running = True
        self.sampleRate = DAQmx_OutPutSampleRate
        # self.periodLength = len( waveform )
        self.periodLength = int(Time * DAQmx_OutPutSampleRate)
        self.Time = Time

        self.Write_data = numpy.zeros(
            (self.periodLength, ), dtype=numpy.float64)

        for i in range(self.periodLength):

            self.Write_data[i] = waveform[i]

        # plot(self.Write_data)
        # show()
        self.taskHandle_Write = TaskHandle(0)
        self.taskHandle_Read = TaskHandle(1)
        self.Channel = Channel

        self.Setup_Write()
        self.Setup_Read(Time)

    def Setup_Write(self):
        # convert waveform to a numpy array

        # setup the DAQ hardware
        self.CHK(nidaq.DAQmxCreateTask("",
                                       ctypes.byref(self.taskHandle_Write)))

        self.CHK(nidaq.DAQmxCreateAOVoltageChan(self.taskHandle_Write,
                                                "Dev1/" + self.Channel,
                                                "",
                                                float64(-
                                                        self.OutputVoltageRange),
                                                float64(
                                                    self.OutputVoltageRange),
                                                self.DAQmx_Val_Volts,
                                                None))

        self.CHK(nidaq.DAQmxCfgSampClkTiming(self.taskHandle_Write,
                                             "/Dev1/ai/SampleClock",
                                             # samples per channel
                                             self.sampleRate,
                                             # active edge
                                             self.DAQmx_Val_Rising,
                                             self.DAQmx_Val_FiniteSamps,
                                             uInt64(self.periodLength)))

        self.CHK(nidaq.DAQmxWriteAnalogF64(self.taskHandle_Write,  # TaskHandel
                                           # num of samples per channel
                                           int32(self.periodLength),
                                           # autostart, if this is not done, a
                                           # NI-DAQmx Start function is
                                           # requried
                                           0,
                                           float64(-1),  # Timeout
                                           # Data layout
                                           self.DAQmx_Val_GroupByChannel,
                                           # write array
                                           self.Write_data.ctypes.data,
                                           # samplers per channel written
                                           None,
                                           None))  # reserved
        threading.Thread.__init__(self)

        return self.Write_data.ctypes.data

    def Setup_Read(self, Time):

        self.max_num_samples = int(
            numpy.float32(DAQmx_InputSampleRate) * 3 * Time)
        # print Time
        self.CHK(nidaq.DAQmxCreateTask("", ctypes.byref(self.taskHandle_Read)))

        self.CHK(nidaq.DAQmxCreateAIVoltageChan(self.taskHandle_Read, "Dev1/ai0:2", "",
                                                # DAQmx_Val_Diff,
                                                # DAQmx_Val_RSE,
                                                # DAQmx_Val_Cfg_Default, #this
                                                # is the rise type
                                                self.DAQmx_Val_Diff,
                                                float64(-self.InputVoltageRange), float64(
                                                    self.InputVoltageRange),
                                                self.DAQmx_Val_Volts,
                                                None))

        self.CHK(nidaq.DAQmxCfgSampClkTiming(self.taskHandle_Read,
                                             # "/Dev1/ao/SampleClock",#"ao/SampleClock",#"Dev1/"+self.Channel+"/SampleClock"-doesn;t work,
                                             "",
                                             DAQmx_InputSampleRate,
                                             self.DAQmx_Val_Rising,
                                             self.DAQmx_Val_FiniteSamps,
                                             uInt64(self.max_num_samples)
                                             ))
        # DAQmxCfgSampClkTiming(taskHandle,"",sampleRate,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,sampsPerChan);
        # DAQmx Start Code
        self.Read_Data = numpy.zeros(
            (self.max_num_samples,), dtype=numpy.float64)
        self.read = int32()

    def CHK(self, err):
        """a simple error checking routine"""
        if err < 0:
            buf_size = 100
            buf = ctypes.create_string_buffer('\000' * buf_size)
            nidaq.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
            raise RuntimeError(
                'nidaq call failed with error %d: %s' % (err, repr(buf.value)))
        if err > 0:
            buf_size = 100
            buf = ctypes.create_string_buffer('\000' * buf_size)
            nidaq.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
            raise RuntimeError(
                'nidaq generated warning %d: %s' % (err, repr(buf.value)))

    def run(self):
        counter = 0
        self.CHK(nidaq.DAQmxStartTask(self.taskHandle_Write))
        self.CHK(nidaq.DAQmxStartTask(self.taskHandle_Read))

        # DAQmx Read Code
        #tic = time.clock()

        self.CHK(nidaq.DAQmxReadAnalogF64(self.taskHandle_Read,  # Task handle
                                          # numSamples per channel, -1 reads as
                                          # many samples as possible
                                          -1,
                                          float64(10.0),  # Timeout in seconds
                                          # DAQmx_Val_GroupByChannel,
                                          # DAQmx_Val_GroupByScanNumber
                                          self.DAQmx_Val_GroupByScanNumber,
                                          # read array
                                          self.Read_Data.ctypes.data,
                                          # samples per channel
                                          self.max_num_samples,
                                          # The actual number of samples read
                                          # per channel (its an output)
                                          ctypes.byref(self.read),
                                          None))  # reserved for future use, pass none to this
        #toc = time.clock()
        # print self.Time
        self.time = np.linspace(0, self.Time, self.read.value)
        # print self.time[0]

        # This check was performed to drtermine if the set frequency was actually what was measured. It appears it is.
        # print self.read.value
        ## print (toc - tic)*1e6
        # print 'Minimum time reading',(toc - tic)*1e6/(self.read.value)
        # plot(self.Read_Data)
        # show()
        # print self.read
        return self.Read_Data

    def stop(self):
        self.running = False
        if self.taskHandle_Write.value != 0:
            nidaq.DAQmxStopTask(self.taskHandle_Write)
            nidaq.DAQmxClearTask(self.taskHandle_Write)

        if self.taskHandle_Read.value != 0:
            nidaq.DAQmxStopTask(self.taskHandle_Read)
            nidaq.DAQmxClearTask(self.taskHandle_Read)
        # show()

    def clear(self):
        nidaq.DAQmxClearTask(self.taskHandle_Write)
        nidaq.DAQmxClearTask(self.taskHandle_Read)


class LightPulse():
    def __init__(self, Waveform, Amplitude, Offset_Before, Offset_After, Time, Voltage_Threshold):
        self.Waveform = Waveform
        self.A = Amplitude
        self.Offset_Before = Offset_Before  # ms
        self.Offset_After = Offset_After  # ms
        self.Time = Time  # ms
        self.OutputSamples = float32(DAQmx_OutPutSampleRate)
        self.Voltage_Threshold = Voltage_Threshold

    def Define(self):

        V_before = np.zeros(
            (int(self.OutputSamples * self.Offset_Before / 1000)))
        V_after = np.zeros(
            (int(self.OutputSamples * self.Offset_After / 1000)))

        if self.Waveform == 'FrequencyScan':
            V, self.t = getattr(self, self.Waveform)(self.Time)

        else:
            self.t = np.linspace(0, self.Time, self.OutputSamples * self.Time)
            V = getattr(self, self.Waveform)(self.t)

            V = self.Adjust_For_Threshold(V)

        self.Time = self.t[-1]
        # print self.Time
        Voltage_waveform = np.concatenate((V_before, V, V_after))

        Total_Time = self.Offset_Before / 1000 + \
            self.Offset_After / 1000 + self.Time
        self.t = np.linspace(0, Total_Time, Voltage_waveform.shape[0])

        return Voltage_waveform

    def Adjust_For_Threshold(self, V):
        # eveything is reversed becomes of the negitive
        Max = np.amax(abs(V))

        scale = (Max - self.Voltage_Threshold) / Max

        Addition = self.Voltage_Threshold

        V *= scale
        V -= Addition

        return V

    def Sin(self, t):
        return -(self.A) * np.abs(np.sin(pi * t / t[-1]))

    def FrequencyScan(self, number):

        V = np.zeros(self.OutputSamples * .1)
        T = np.linspace(0, 0.1, self.OutputSamples * .1)
        t0 = T[-1]
        for f in np.logspace(self.Offset_Before, self.Offset_After, int(number))[::-1]:

            t = np.arange(0, 5 / f, 1. / self.OutputSamples)

            V = np.append(V, 0.02 * self.A * np.sin(2 * np.pi * f * t))
            T = np.append(T, t + t0)
            t0 += t[-1]

        return -V - self.A, T

    def Square(self, t):
        return -self.A * np.ones((t.shape[0]))

    def Cos(self, t):
        return -(self.A) * np.abs(np.cos(pi * t / t[-1]))

    def Triangle(self, t):
        halfway = t.shape[0] / 2
        return -1 * np.concatenate((self.A * 2 / t[-1] * t[:halfway], -self.A * 2 / t[-1] * t[:halfway] + self.A))

    def MJ(self, t):
        fraction = 0.01
        t_shift = t.shape[0] * fraction
        t0_index = t.shape[0] * (0.5 - fraction)
        t_halfway_index = t.shape[0] / 2
        t_halfway = t[t_halfway_index]
        t0 = t[t0_index]

        # Funtions are:
        # G = C/t
        #G = Bx^4 + Amplitude
        # These are then spliced together at t0

        B, C = -self.A * t[t_shift]**(-4) / 5., 4. / 5 * self.A * t[t_shift]
        f = np.concatenate(
            (-C / (t[:t0_index] - t_halfway), B * (t[t0_index:t_halfway_index] - t_halfway)**4 + self.A))
        return -1 * np.concatenate((f, f[::-1]))


class OutPutData():
    Path = os.getcwd()
    LoadPath = os.getcwd()

    def Save_data(self, Data, waveform=None):
        # print 'am i here',self.file_opt

        dialog = wx.FileDialog(
            None, 'Pick a filename dude!', self.Path, '', r'*.Raw Data.dat', wx.FD_SAVE)

        # filename = tkFileDialog.asksaveasfilename(**self.file_opt)
        # print filename
        Varaibles = 'Time (s)\tGeneration (V)\tPC (V)\tPL (V)\t Waveform (V)'
        if dialog.ShowModal() == wx.ID_OK:

            self.Path = dialog.GetPath()[::-1].split('\\', 1)[-1][::-1]
            self.SaveName = dialog.GetPath()[:-13]

            if waveform is not None:
                if waveform.shape[0] = Data.shape[0]:
                    Data = np.vstack((Data, waveform)).T
                else:
                    print 'light pulse is the wrong size'

            numpy.savetxt(
                dialog.GetPath(), Data, delimiter='\t', header=Varaibles)
        else:
            print 'Canceled save'
        dialog.Destroy()

    def Save_Inf(self, List):
        # Requies the SaveData to be run first

        del List['event']
        del List['self']
        s = 'MJ system\r\nList of vaiables:\r\n'
        for i in List:
            # if i != and i !='self':
            s += '{0}:\t{1}\r\n'.format(i, List[i])

        with open(self.SaveName + '.inf', 'w') as text_file:
            text_file.write(s)

    def Load_Inf(self):

        dialog = wx.FileDialog(
            None, 'Pick a Setting File dude!', self.LoadPath, '', r'*.inf', wx.FD_OPEN)

        self.LoadPath = dialog.GetPath()[::-1].split('\\', 1)[-1][::-1]
        if dialog.ShowModal() == wx.ID_OK:

            with open(dialog.GetPath(), 'r') as f:
                s = f.read()

        dialog.Destroy()
        List = {}
        for i in s.split('\n')[2:-1]:
            # print i.split(':\t')[1]
            List[i.split(':\t')[0].strip()] = i.split(':\t')[1].strip()
        return List


class TakeMeasurements():
    def __init__(self, OutPutVoltage, Averaging, Channel, Time):
        self.OutPutVoltage = OutPutVoltage
        self.SampleRate = DAQmx_OutPutSampleRate
        self.Time = Time
        # print self.Time,Time
        self.Averaging = int(Averaging)
        self.Channel = Channel

    def SingleMeasurement(self):

        # start playing waveform

        mythread = WaveformThread(self.OutPutVoltage, self.Channel, self.Time)

        mythread.run()

        mythread.stop()

        self.time = mythread.time
        return mythread.Read_Data

    def Average(self):
        # If there is an error, put this line inside SingleMeasurement

        RunningTotal = self.SingleMeasurement()

        for i in range(self.Averaging - 1):

            RunningTotal = np.vstack((self.SingleMeasurement(), RunningTotal))
            # The running total is weigged for the number of points inside it
            RunningTotal = np.average(RunningTotal, axis=0, weights=(1, i + 1))
        return RunningTotal

    def Measure(self):
        NoChannls = 3.
        if self.Averaging > 0:

            data = self.Average()
            # Here the 3 stands for the number of channels what are going to be
            # read
            Data = numpy.empty((int(data.shape[0] / NoChannls), NoChannls))
            # print Data.shape,data.shape
            for i in range(int(NoChannls)):
                # The data should be outputted one of each other, so divide it
                # up and roll it out
                Data[:, i] = data[i * Data.shape[0]:(i + 1) * Data.shape[0]]

            return vstack((self.time, Data.T)).T
        else:
            print 'Averaging Too low'


class Test(gui.MyFrame1, OutPutData):
    # constructor
    measurement_type = 'Standard'

    def __init__(self, parent):
        # initialize parent class
        gui.MyFrame1.__init__(self, parent)

        self.Fig1 = CanvasPanel(self.Figure1_Panel)
        self.Fig1.labels('Raw Data', 'Time (s)', 'Voltage (V)')
        self.Data = array([])
        # CanvasPanel(self.Figure2_Panel)

    def Determine_Digital_Output_Channel(self):
        # Just a simple function choosing the correct output channel based on
        # the drop down box
        if self.Channel == 'High (2A/V)':
            Channel = 'ao0'
            Voltage_Threshold = self.Threshold / \
                1840.  # 1840 comes from exp measurements

        elif self.Channel == 'Low (50mA/V)':
            Channel = 'ao1'
            Voltage_Threshold = self.Threshold / \
                66.  # 66 comes from exp measurements
            # Voltage_Threshold = 0 #apparently this is an equiptment thing
        return Channel, Voltage_Threshold

    def Save(self, event):
        # temp call to GetVAlues
        getattr(self, 'GetValues_' + self.measurement_type)(event)

        self.Save_data(self.Data, self.LP)
        data = self.Data
        # print info locals
        self.Save_Inf(self.Make_List_For_Inf_Save(event))

        event.Skip()

    def Load(self, event):

        List = self.Load_Inf()

        self.m_Intensity.SetValue(List['Intensity_v'])
        self.m_Threshold.SetValue(List['Threshold_mA'])
        self.m_Waveform.SetStringSelection(List['Waveform'])
        # print List['Waveform'],List['Channel']
        self.m_Output.SetStringSelection(List['Channel'])
        self.m_Averaging.SetValue(List['Averaging'])
        self.m_Binning.SetValue(List['Binning'])
        self.m_Offset_Before.SetValue(List['Offset_Before_ms'])
        self.m_Period.SetValue(List['Peroid_s'])
        self.m_Offset_After.SetValue(List['Offset_After_ms'])

        event.Skip()

    def GetValues_Standard(self, event):
        self.Intensity = self.CHK_float(self.m_Intensity, event)
        self.Binning = self.CHK_int(self.m_Binning, event)
        self.Averaging = self.CHK_int(self.m_Averaging, event)
        self.Peroid = self.CHK_float(self.m_Period, event)
        self.Offset_Before = self.CHK_float(self.m_Offset_Before, event)
        self.Offset_After = self.CHK_float(self.m_Offset_After, event)
        self.Waveform = self.m_Waveform.GetStringSelection()
        self.Channel = self.m_Output.GetStringSelection()
        self.Threshold = self.CHK_float(self.m_Threshold, event)
        # print self.Binning
        # print self.lo

    def Make_List_For_Inf_Save(self, event):

        Intensity_v = self.CHK_float(self.m_Intensity, event)
        Threshold_mA = self.CHK_float(self.m_Threshold, event)
        Waveform = self.m_Waveform.GetStringSelection()
        Channel = self.m_Output.GetStringSelection()
        Averaging = self.CHK_int(self.m_Averaging, event)
        Binning = self.CHK_int(self.m_Binning, event)
        Offset_Before_ms = self.CHK_float(self.m_Offset_Before, event)
        Peroid_s = self.CHK_float(self.m_Period, event)
        Offset_After_ms = self.CHK_float(self.m_Offset_After, event)
        return locals()

    def Perform_Standard_Measurement(self, event):
        self.measurement_type = 'Standard'
        self.Perform_Measurement(event)
        self.PlotData()

    def Perform_Measurement(self, event):

        # this is what happens when the go button is pressed

        # first thing is all the inputs are grabbed
        # A check is performed, and if failed, event is skipped

        # print event.GetEventType()
        # print event.IsCommandEvent()
        # print event.GetId()

        getattr(self, 'GetValues_' + self.measurement_type)(event)

        # find what channel we are using, and what the voltage offset then is
        Channel, Voltage_Threshold = self.Determine_Digital_Output_Channel()
        self.CHK_Voltage_Threshold(Voltage_Threshold, event)

        # This the event hasn't been skipped then continue with the code.
        self.m_scrolledWindow1.Refresh()
        if event.GetSkipped() == False:

            # Then the light pulse is defined, but the lightpulse class
            lightPulse = LightPulse(
                self.Waveform, self.Intensity, self.Offset_Before, self.Offset_After, self.Peroid, Voltage_Threshold)

            # We determine what channel to output on
            self.LP = lightPulse.Define()
            t = lightPulse.t

            # We put all that info into the take measurement section, which is
            # a instance definition. There are also global variables that go
            # into this
            Go = TakeMeasurements(self.LP, self.Averaging, Channel, t[-1])

            # Go.Measure()
            # print 'here'
            # USing that instance we then run the lights, and measure the
            # outputs
            self.Data = self.Bin_Data(Go.Measure(), self.Binning)
            # self.Data = lightPulse.Define()
            # We then plot the datas, this has to be changed if the plots want
            # to be updated on the fly.

            event.Skip()
        else:

            self.m_scrolledWindow1.Refresh()

    def PlotData(self, e=None):

        self.Fig1.clear()
        labels = ['Reference', 'PC', 'PL']
        # t = np.linspace(0,t[-1],self.Data.shape[0])
        colours = ['b', 'r', 'g']

        # this is done not to clog up the plot with many points
        if self.Data.shape[0] > 1000:
            num = self.Data.shape[0] // 1000
        else:
            num = 1

        if self.ChkBox_PL.GetValue():
            self.Data[:, 3] *= -1
        if self.ChkBox_PC.GetValue():
            self.Data[:, 2] *= -1
        if self.ChkBox_Ref.GetValue():
            self.Data[:, 1] *= -1

        # This plots the figure
        # print self.Data
        # print self.Data.shape,t.shape
        for i, label, colour in zip(self.Data[:, 1:].T, labels, colours):
            # print i,label,colour,
            # print colour
            # print i.shape,t.shape
            self.Fig1.draw_points(
                self.Data[::num, 0], i[::num], '.', Color=colour, Label=label)
            # self.Fig1.draw_line(t[::num],i[::num],'--',Color=colour,Label = label)
        self.Fig1.legend()
        self.Fig1.update()
        if e != None:
            e.skip()

    def Bin_Data(self, data, BinAmount):

        if BinAmount == 1:
            return data
        # This is part of a generic binning class that I wrote.
        # IT lets binning occur of the first axis for any 2D or 1D array
        if len(data.shape) == 1:
            data2 = zeros((data.shape[0] // BinAmount))
        else:
            data2 = zeros((data.shape[0] // BinAmount, data.shape[1]))

        for i in range(data.shape[0] // BinAmount):

            data2[i] = mean(data[i * BinAmount:(i + 1) * BinAmount], axis=0)

        return data2

    def onChar(self, event):
        # This function is for ensuring only numerical values are placed inside
        # the textboxes
        key = event.GetKeyCode()

        # print ord(key)
        acceptable_characters = "1234567890."
        if key < 256 and key != 8:
            if chr(key) in acceptable_characters:
                event.Skip()
                return

            else:
                return False
        # This is for binding the F2 key to run
        elif key == 341:
            self.Run_Me(event)
            return
        else:
            event.Skip()
            return

    def Run_Me(self, event):
        # This function is for ensuring only numerical values are placed inside
        # the textboxes
        key = event.GetKeyCode()

        if key == 341:
            self.Perform_Measurement(event)
        else:
            event.Skip()
            return

    def onChar_int(self, event):
        # This function is for ensuring only numerical values are placed inside
        # the textboxes
        key = event.GetKeyCode()
        # print key
        # print ord(key)
        acceptable_characters = "1234567890"
        if key < 256 and key != 8:
            if chr(key) in acceptable_characters:
                event.Skip()
                return

            else:
                return False
        elif key == 341:
            self.Run_Me(event)
            return
        else:
            event.Skip()
            return

    def Num_Data_Points_Update(self, event):
        # what is the point of this function?
        getattr(self, 'GetValues_' + self.measurement_type)(event)
        time = self.Peroid + self.Offset_Before / 1000. + self.Offset_After / \
            1000.

        self.m_DataPoint.SetValue(
            '{0:.2e}'.format((time * float32(DAQmx_InputSampleRate) / self.Binning)[0]))

        self.m_Frequency.SetValue('{0:3.3f}'.format(1. / time))
        event.Skip()

    def CurrentLimits(self, event):
        # print
        # self.m_Output.GetStringSelection(),self.m_Intensity.GetValue(),float(self.m_Intensity.GetValue())>1.5

        # This is function to determine the approiate current limit for the box
        # A 10V limit is imposed owing to limitations on the output voltage of
        # the datcard
        try:
            if self.m_Output.GetStringSelection() == 'Low (50mA/V)':
                if float(self.m_Intensity.GetValue()) > 10:
            # self.m_Intensity.SetBackgroundColour('RED')
                    self.m_Intensity.SetValue('10')
                # else:
                #     self.m_Intensity.SetBackgroundColour(wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ))
            # A 1.5V limit is imposed as a limit owing to the current limit of
            # the power supply.
            elif self.m_Output.GetStringSelection() == 'High (2A/V)':

                if float(self.m_Intensity.GetValue()) > 1.5:
                    # self.m_Intensity.SetBackgroundColour('RED')
                    self.m_Intensity.SetValue('1.5')

            return False
        except:

            return False

    def CHK_Voltage_Threshold(self, Voltage_Threshold, event):
        if Voltage_Threshold > self.Intensity:
            # self.m_Threshold.SetBackgroundColour('RED')
            event.Skip()
        else:
            self.m_Threshold.SetBackgroundColour(
                wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))

    def CHK_int(self, Textbox, event):
        try:
            return int(Textbox.GetValue())
            Textbox.SetBackgroundColour(
                wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        except:
            Textbox.SetBackgroundColour('RED')
            event.Skip()

    def CHK_float(self, Textbox, event):
        try:
            # print Textbox.GetValue(),float(Textbox.GetValue())
            Textbox.SetBackgroundColour(
                wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            return float(Textbox.GetValue())
        except:
            # print'yeah'
            Textbox.SetBackgroundColour('RED')

            event.Skip()
            return 0

# mandatory in wx, create an app, False stands for not deteriction stdin/stdout
# refer manual for details
app = wx.App(False)

# create an object of CalcFrame
frame = Test(None)
# show the frame
frame.Show(True)
# start the applic
app.MainLoop()
# t = np.linspace(0,10,10000)
# a=LightPulse()
# a.A = 1
# V=a.Triangle(t)
# plot(t,V)
# V=a.MJ(t)
# plot(t,V)
# show()
