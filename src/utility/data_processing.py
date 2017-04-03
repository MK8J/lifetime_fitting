
import numpy as np


def average(current_data, new_data, measurement_num):
    '''
    Returns the average of data.
    This function is to be used when running sequential measurements.
    You call it after each run, and averages the data with the correct weights
    so it is equilavent until waiting to the end and averaging all the data.
    '''

    # stack = np.vstack((new_data, current_data)).T

    return (new_data + current_data*(measurement_num+1))/(measurement_num+2)



def bin(data, BinAmount):
    '''
    Bins data by the binning amount
    '''

    if BinAmount == 1:
        return data
    # This is part of a generic binning class that I wrote.
    # IT lets binning occur of the first axis for any 2D or 1D array
    if len(data.shape) == 1:
        data2 = np.zeros((data.shape[0] // BinAmount))
    else:
        data2 = np.zeros((data.shape[0] // BinAmount, data.shape[1]))

    for i in range(data.shape[0] // BinAmount):

        data2[i] = np.mean(data[i * BinAmount:(i + 1) * BinAmount], axis=0)

    return data2
