import os
import sys
import numpy as np
import ruamel.yaml as yaml
import json


def save_data(fname, data):

    if '_Raw_Data.dat' not in fname:
        fname = fname + '_Raw_Data.dat'

    variables = 'Time (s)\tGeneration (V)\tPC (V)\tPL (V)'
    np.savetxt(fname, data, delimiter='\t', header=variables)


def save_settings_json(fname, settings):
    '''
    Saves the settings of the exp
        inputs:
        fname: the file to be saved to
        settings:  a dictionary of the settings
    '''

    if '.json' not in fname:
        fname = fname + '.json'

    serialised_json = json.dumps(
        settings,
        sort_keys=True,
        indent=4,
        separators=(',', ': ')
    )

    with open(fname, 'w') as text_file:
        text_file.write(serialised_json)


def save_settings(fname, settings_dic):
    '''
    Saves the settings of the exp
        inputs:
        fname: the file to be saved to
        settings:  a dictionary of the settings
    '''
    _settings_dic = dict(settings_dic)

    if '.yaml' not in fname:
        fname = fname + '.yaml'

    for dic in settings_dic.keys():
        for key, value in settings_dic[dic].items():
            if isinstance(value, (np.ndarray, np.generic)):

                _settings_dic[dic][key] = float(value)

    with open(fname, 'w') as text_file:
        yaml.dump(settings_dic, text_file, default_flow_style=False,
                  indent=4, Dumper=yaml.RoundTripDumper)


def load_metadata(fname):
    with open(fname, 'r') as text_file:
        test = yaml.load(text_file)

    return metadata_dict


def load_metadata_json(fname):
    """
    Loads metadata file and returns a python dictionary
    """

    with open(fname, 'r') as f:
        file_contents = f.read()
        metadata_dict = json.loads(file_contents)

    return metadata_dict


class data():

    data = [None]
    settings = [None]
    _data_sets = 0

    def __init__(self):
        pass

    def add_data_set(self):
        if self.data[-1] is not None:
            self.data.append(None)
            self.settings.append(None)

        self._data_sets = len(self.data)

    @property
    def current_setting(self):
        self.settings[-1]

    @current_setting.setter
    def current_setting(self, value):
        self.settings[-1] = value.copy()

    @property
    def current_data(self):
        self.data[-1]

    @current_data.setter
    def current_data(self, value):
        self.data[-1] = value
