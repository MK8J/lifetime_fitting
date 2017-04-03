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
import sys
import os
import functools
import copy

import numpy as np
import ruamel.yaml as yaml
import matplotlib.pylab as plt

# now import things from this program
from .utility import data_processing as proc

from .hardware.daq import USB6356
from .hardware.LightSource import light_control
from .hardware.preamp import preamp_handeller


from .data import IO


class dark_conductance():
    '''
    A class that allows measurement of the dark voltage and hence
    calculation of a dark conductance.
    '''

    dark_conductance = {
        'get_dark_conductance': True,
        'dark_voltage': None,
    }

    dc_settings = {
        'repeats': 1,
        'LED_itensity': 0.0,  # float in volts
        'time_of_illumination': 1e-5,  # float in seconds
        'time_offset_after': 100,  # float in mili seconds
        'zero_voltage': 0,  # float in voltage
        'auto_gain': False,
        'background': False,
        'samplerate': 1e6,
        'performed': False
    }

    def __init__(self, QSSPL_measurement):
        QSSPL_measurement.dark_conductance = self.dark_conductance
        QSSPL_measurement._dics.append('dark_conductance')

    def __call__(self, func):

        def wrapped_func(attrs):

            # if we want dark conductance do it!
            if attrs['get_dark_conductance'] and not self.dc_settings['performed']:
                temp = dict(attrs)
                # set the new settings
                attrs.update(self.dc_settings)

                import tkinter
                from tkinter import messagebox
                root = tkinter.Tk()
                root.withdraw()
                s = 'Please remove the sample from the stage'
                messagebox.showinfo("Action required", s)
                root.destroy()

                attrs, data = func(attrs)
                pc_col = attrs['channel_names'].index(
                    'pc')+1

                root = tkinter.Tk()
                root.withdraw()
                s = "Please place the sample on the stage"
                messagebox.showinfo("Action required", s)
                root.destroy()

                attrs.update(temp)

                self.dark_conductance['dark_voltage'] = np.mean(
                    abs(data[:, pc_col])).item()
                attrs['dark_voltage'] = np.mean(abs(data[:, pc_col]))
                self.dc_settings['performed'] = True

            elif attrs['get_dark_conductance'] and self.dc_settings['performed']:
                attrs, data = func(attrs)
                attrs['dark_voltage'] = self.dark_conductance['dark_voltage']

            attrs, data = func(attrs)

            return attrs, data
        return wrapped_func


class adding_gain_control():
    '''
    A class that allows gain control
    '''
    preamp = {
        'auto_gain': False,
        'preamp_type': None,
        'preamp_channels': None
    }

    def __init__(self, QSSPL_measurement):

        QSSPL_measurement.preamp = self.preamp
        QSSPL_measurement._dics.append('preamp')

        self.preamp.update({'gain_{0}'.format(name): None
                            for name in QSSPL_measurement().attrs['preamp_channels']})

        # check the gain names are in the channel names
        assert all(
            [i in QSSPL_measurement().attrs['channel_names']
             for i in QSSPL_measurement().attrs['preamp_channels']])

        self.preamp.update(
            {'preamp_type': QSSPL_measurement().attrs['preamp_type']})

        QSSPL_measurement.preamp.update(self.preamp)

    def __call__(self, func):

        def wrapped_func(kwargs):
            pa = preamp_handeller(**kwargs)

            attrs, data = func(kwargs)

            pl_col, gen_col = attrs['channel_names'].index(
                'pl')+1, attrs['channel_names'].index('gen')+1

            maxgen, maxpl = np.max(abs(data[:, gen_col])), np.max(
                abs(data[:, pl_col]))

            while pa.check_gains({'pl': maxpl, 'gen': maxgen}):

                attrs, data = func(kwargs)

                if pa.gain_pl is None or pa.gain_gen is None or pa.auto_gain is False:
                    break
                else:
                    maxgen, maxpl = np.max(abs(data[:, gen_col])), np.max(
                        abs(data[:, pl_col]))
                # print(maxgen, maxpl,data.shape, np.amax(abs(data), axis=0))

            attrs.update(pa.attrs)
            return kwargs, data
        return wrapped_func


class bkg_correction():
    '''
    A simple class to acquire background data
    '''

    background = {
        'bkg_correction': True,
    }

    bk_settings = {
        'repeats': 1,
        'LED_itensity': 0.0,  # float in volts
        'time_of_illumination': 1e-5,  # float in seconds
        'time_offset_after': 100,  # float in mili seconds
        'zero_voltage': 0,  # float in voltage
        'auto_gain': False,
        'background': False,
        'samplerate': 1e6,
        'dark_voltage': None
    }

    def __init__(self, QSSPL_measurement):

        self.background.update({'bkg_{0}'.format(name): None
                                for name in QSSPL_measurement().attrs['channel_names']})

        self.background.update({'bkg_{0}_std'.format(name): None
                                for name in QSSPL_measurement().attrs['channel_names']})

        QSSPL_measurement.background = self.background
        QSSPL_measurement._dics.append('background')

    def __call__(self, func):

        def wrapped_func(attrs):

            pl_col,pc_col, gen_col = attrs['channel_names'].index(
                'pl')+1, attrs['channel_names'].index(
                    'pc')+1, attrs['channel_names'].index('gen')+1

            # take the measurement
            attr, data = func(attrs)

            # if we want background correction do it
            if attrs['bkg_correction']:

                # save the original settings
                temp = dict(attrs)
                # set the new settings
                attrs.update(self.bk_settings)
                # do the background
                attr, bk_data = func(attrs)
                # save the values
                vals = {'bkg_gen': np.mean(bk_data[:, gen_col]),
                        'bkg_pc': np.mean(bk_data[:, pc_col]),
                        'bkg_pl': np.mean(bk_data[:, pl_col]),
                        'bkg_gen_std': np.std(bk_data[:, gen_col]),
                        'bkg_pc_std': np.std(bk_data[:, pc_col]),
                        'bkg_pl_std': np.std(bk_data[:, pl_col]),
                        }

                temp.update(vals)

            return temp, data
        return wrapped_func


class invert():
    '''
    A simple class to invert the data
    '''

    def __init__(self, QSSPL_measurement):

        self.invert = {'invert_{0}'.format(name): False
                       for name in QSSPL_measurement().attrs['channel_names']}

        QSSPL_measurement.invert = self.invert
        QSSPL_measurement._dics.append('invert')

    def __call__(self, func):

        def wrapped_func(attrs):
            # take the measurement
            attr, data = func(attrs)

            for key in self.invert.keys():

                if attrs[key]:
                    data[:, attrs['channel_names'].index(
                        key.replace('invert_', '')) + 1] *= -1

            return attrs, data
        return wrapped_func


class QSSPL_measurement():

    measurement = {
        'binning': None,
        'repeats': None,
        'time': None,  # this ends up being the total length of the measurement
    }

    illumination_settings = {
        'waveform_type': None,  # sin, cos, square, MJ, triangle
        'LED_itensity': None,  # float in volts
        'time_of_illumination': None,  # float in seconds
        'time_offset_after': None,  # float
        'time_offset_before': None,  # float
        'zero_voltage': None,  # float in voltage
        'output_current_gain': None,  # high or low
        'flash': None,  # are you using the flash and not an LED
        'LED_off_voltage': None
    }

    daq_settings = {
        'output_channel': None,
        'samplerate': None,
        'InputVoltageRange': None,
        'OutputVoltageRange': None,
        'Daq_Channels_Number': None,
        'samplerate': 1e6,
        'channel_names': None
    }

    sample = {
        'doping': None,
        'thickness': None,
        'reflection': None,
        'name': None,
        'Fs': None,
        'Ai': None,
        'doping_type': None
    }

    _dics = [
        'measurement',
        'illumination_settings',
        'daq_settings',
        'sample']

    def __init__(self, **kwargs):
        # get the system settings from the yaml file
        folder = os.path.dirname(__file__)
        with open(os.path.join(folder, 'system_config.yaml'), 'r') as f:
            a = yaml.safe_load(f.read())
        # not sure what the following line does but it most likley does something
        # self.attrs = dict(pair for d in L for pair in self.dics.items())
        self.attrs = a
        self.attrs = kwargs

    @property
    def dics(self):
        '''
        Just a function to join all the above dictionaries together for external use.
        '''
        dic_lst = []
        for dic in self._dics:
            dic_lst.append(getattr(self, dic))

        return dic_lst

    @property
    def attrs(self):
        big_dic = {}
        for dic in self.dics:
            big_dic.update(dic)
        return big_dic

    @property
    def dicofdic(self):
        big_dic = {}

        for dic in self._dics:
            big_dic[dic] = getattr(self, dic)
        return big_dic

    @attrs.setter
    def attrs(self, kwargs):

        assert type(kwargs) == dict

        for key, value in kwargs.items():
            if value is not None:
                for dic in self.dics:
                    if key in dic.keys():
                        dic[key] = value
                        break

    def _checks(self):
        assert len(self.daq_settings['channel_names']) == self.daq_settings[
            'Daq_Channels_Number']

    def measure(self):
        self.attrs, data = measure(self.attrs)
        return data


@bkg_correction(QSSPL_measurement)
@adding_gain_control(QSSPL_measurement)
@invert(QSSPL_measurement)
@dark_conductance(QSSPL_measurement)
def measure(attrs):
    '''
    A simple function that measure stuff
    '''

    ls = light_control(**attrs)
    # updating keeps us finding mistakes!
    attrs.update(ls.attrs)

    assert attrs['repeats'] >= 1

    maxpl, maxgen = attrs[
        'InputVoltageRange'] * 2, attrs['InputVoltageRange'] * 2

    try:
        daq = USB6356(ls.waveform(), **attrs)

        data = proc.bin(daq.run(), attrs['binning'])

        for i in range(attrs['repeats'] - 1):
            new_data = proc.bin(daq.run(), attrs['binning'])
            data = proc.average(data, new_data, i)

    except:
        print('Counld not run daq? erro', sys.exc_info())
        data = np.ones((20, 4))

    return attrs, data


class batch_QSSPL():

    mea_list = None
    mea_list_copy = None

    def __init__(self, mea_list):
        self.mea_list = mea_list[::-1]
        # self.mea_list_copy = mea_list[:]

        self.single = QSSPL_measurement()
        self.data = IO.data()

    def measure(self):

        for i in range(len(self.mea_list)):

            self.single.attrs = self.mea_list.pop()
            self.data.add_data_set()

            data = self.single.measure()

            self.data.current_data = data
            self.data.current_setting = copy.deepcopy(self.single.dicofdic)

    def save(self, fname=None):
        fname = fname or self.single.attrs['name']
        print('the file name is',fname)
        for i in range(len(self.data.data)):
            IO.save_data(fname + '_' + str(i), self.data.data[i])
            IO.save_settings(fname + '_' + str(i), self.data.settings[i])


# if __name__ == '__main__':
#
#     def check_batch():
#         settings = [{
#             'binning': 10,
#             'repeats': 1,
#             'waveform_type': 'sin',  # sin, cos, square, MJ, triangle
#             'LED_itensity': 0.8,  # float in volts
#             'time_of_illumination': 0.1,  # float in seconds
#             'time_offset_after': 1,  # float in mili seconds
#             'time_offset_before': 10,  # float
#             'zero_voltage': 0,  # float in voltage
#             'output_current_gain': 'high',  # high or low
#             'samplerate': 1e6,
#             'InputVoltageRange': 10,
#             'OutputVoltageRange': 10,
#             'Daq_Channels_Number': 3,
#             'gain_pl': None,
#             'gain_gen': None,
#             'doping': None,
#             'thickness': None,
#             'reflection': None,
#             'name': 'fakesample',
#         }, {'binning': 1}]
#
#         a = batch_QSSPL(settings)
#         a.measure()
#
#     def check_single():
#         a = QSSPL_measurement(reflection=0.1)
#         a.attrs = {'reflection': 0.2}
#         a.attrs = {
#             'binning': 10,
#             'repeats': 3,
#             'waveform_type': 'sin',  # sin, cos, square, MJ, triangle
#             'LED_itensity': 0.50,  # float in volts
#             'time_of_illumination': 1.08,  # float in seconds
#             'time_offset_after': 10,  # float in mili seconds
#             'time_offset_before': 1,  # float
#             'zero_voltage': 0,  # float in voltage
#             'LED_off_voltage': -0.5,  # float in voltage
#             'output_current_gain': 'low',  # high or low
#             'samplerate': 1e6,
#             'InputVoltageRange': 10,
#             'OutputVoltageRange': 10,
#             'Daq_Channels_Number': 3,
#             'doping': None,
#             'thickness': None,
#             'reflection': None,
#             'name': 'fakesample',
#             'flash': False,
#             'auto_gain': False,
#         }
#
#         data = a.measure()
#         plt.plot(data[:, 0], data[:, 1], label='1')
#         plt.plot(data[:, 0], data[:, 2], label='2')
#         plt.plot(data[:, 0], data[:, 3], label='3')
#
#         plt.legend(loc=0)
#
#     def check_single_gain():
#         a = QSSPL_measurement(reflection=0.1)
#         a.attrs = {'reflection': 0.2}
#         a.attrs = {
#             'binning': 10,
#             'repeats': 1,
#             'waveform_type': 'sin',  # sin, cos, square, MJ, triangle
#             'LED_itensity': 0.80,  # float in volts
#             'time_of_illumination': 0.1,  # float in seconds
#             'time_offset_after': 10,  # float in mili seconds
#             'time_offset_before': 1,  # float
#             'zero_voltage': 0,  # float in voltage
#             'LED_off_voltage': -0.5,  # float in voltage
#             'output_current_gain': 'high',  # high or low
#             'samplerate': 1e6,
#             'InputVoltageRange': 10,
#             'OutputVoltageRange': 10,
#             'Daq_Channels_Number': 3,
#             'gain_pl': 1e8,
#             'gain_gen': 1e4,
#             'auto_gain': True,
#             'doping': None,
#             'thickness': None,
#             'reflection': None,
#             'name': 'fakesample',
#             'flash': False
#         }
#
#         data = a.measure()
#         print(a.attrs['bkg_gen'])
#         print(a.attrs['bkg_gen'])
#         print(a.attrs['bkg_correction'])
#         print(a.attrs['gain_gen'])
#
#         # plt.plot(abs(data[:, 1] - a.attrs['bkg_gen']) / a.attrs['gain_gen'],
#         #          abs(data[:, 3] - a.attrs['bkg_pl']) / a.attrs['gain_pl'])
#         #
#         # plt.plot(abs(data[:, 1] - a.attrs['bkg_gen']) / a.attrs['gain_gen'],
#         #          abs(data[:, 3] - a.attrs['bkg_pl']) / a.attrs['gain_pl'], '--')
#         #
#         # a.attrs = {'LED_itensity': 1,
#         #            'time_of_illumination': 0.5,
#         #            'output_current_gain': 'low',
#         #            'samplerate': 1e4,
#         #            'repeats': 1,
#         #            'binning': 10,
#         #            'zero_voltage': 0.11
#         #            }
#         #
#         # data = a.measure()
#         # print(a.attrs['gain_gen'] / 1e5, a.attrs['gain_pl'] / 1e9)
#         # plt.plot(abs(data[:, 1] - a.attrs['bkg_gen']) / a.attrs['gain_gen'],
#         #          abs(data[:, 3] - a.attrs['bkg_pl']) / a.attrs['gain_pl'])
#         # #
#         # a.attrs = {
#         #     'LED_itensity': 5,
#         #     'samplerate': 1e5,
#         #     'binning': 100,
#         # }
#         # #
#         # data = a.measure()
#         # # print(a.attrs['gain_gen']/1e5,a.attrs['gain_pl']/1e9)
#         # plt.plot(abs(data[:, 1] - a.attrs['bkg_gen']) / a.attrs['gain_gen'],
#         #          abs(data[:, 3] - a.attrs['bkg_pl']) / a.attrs['gain_pl'])
#         #
#         # plt.loglog()
#
#     check_single()
#     plt.show()
