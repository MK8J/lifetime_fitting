

import numpy as np
import sys
import scipy.constants as consts

# sys.path.append('D:\Dropbox\CommonCode\semiconductor\src')
sys.path.append('/home/mattias/Dropbox/CommonCode/semiconductor/src')
from semiconductor.recombination import extrinsic, intrinsic
from semiconductor.material import IntrinsicCarrierDensity as ni

import collections


class lifetime():

    def __init__(self, sample, models):
        self.sample = sample
        self.models = models
        self.intr = intrinsic.Intrinsic(
            temp=self.sample.temp, Na=self.sample.Na, Nd=self.sample.Nd, material=self.sample.material)

        self.srh = extrinsic.SRH(
            temp=self.sample.temp, Na=self.sample.Na, Nd=self.sample.Nd, material=self.sample.material, defect='Au_a')

        self.ni = ni(temp=sample.temp, material=sample.material)

    def intrinsic(self):

        return self.intr.itau(
            temp=self.sample.temp, Na=self.sample.Na, Nd=self.sample.Nd, material=self.sample.material, nxc=self.sample.nxc)

    def extrinsic(self):

        for i in sample.SRH:

            self.srh.calculationdetails = {'nxc': self.sample.nxc}
            self.srh.usr_vals(Et=i.Et, tau_e=i.tau_e,
                              tau_h=i.tau_h)
            itau = self.srh.itau()
        return itau

    def J0(self):
        _ni = self.ni.update(temp=sample.temp)

        epV = self.sample.nxc * \
            (np.amax(self.sample.Na + self.sample.Nd) + self.sample.nxc) / _ni**2
        Jrec = self.sample.surface.J0 * epV
        return Jrec / consts.e / self.sample.nxc / self.sample.thickness

    def Seff_symetric(self):
        _ni = self.ni.update(temp=sample.temp)
        # D = 25
        Jrec = consts.e * self.sample.Seff * self.sample.nxc

        if sample.J0ej is not None:

            epV = (self.sample.nxc *
                   (np.amax(self.sample.Na + self.sample.Nd) + self.sample.nxc) / _ni**2)**(1. / 1.65)
            Jrec += sample.J0ej * epV

        # if sample.J0ej is not None:
            # Jrec += sample.J0ej*_np

        # tau = self.sample.thickness / 2 / self.sample.Seff + \
        # 1. / D * (self.sample.thickness / np.pi)**2
        return Jrec / consts.e / self.sample.nxc / self.sample.thickness


class SRH_recombiation():
    # values
    Et = 0
    tau_e = 1e-4
    tau_h = 1e-4

    # human readable strings
    Et_hr = 'E<sub>t</sub>'
    tau_e_hr = u"\U0001D70F" + '<sub>e</sub>'
    tau_h_hr = u"\U0001D70F" + '<sub>h</sub>'

    def __init__(self, **kwargs):

        for i in kwargs:
            if hasattr(self, i):
                setattr(self, i, kwargs[i])

    def params(self):
        dic = collections.OrderedDict()
        dic['Et'] = self.Et
        dic['tau_e'] = self.tau_e
        dic['tau_h'] = self.tau_h
        return dic

    def hr_params(self):
        dic = {}
        for k in self.params().keys():
            dic[k] = getattr(self, k + '_hr')

        return dic


class surface_recombaition():
    J0 = 100e-15
    S_eff = None
    S_J0ej = None

    J0_hr = 'J<sub>0</sub>'

    def params(self):
        dic = collections.OrderedDict()
        dic['J0'] = self.J0
        return dic

    def hr_params(self):
        dic = {}
        for k in self.params().keys():
            dic[k] = getattr(self, k + '_hr')

        return dic


class sample():
    Na = 0
    Nd = 1e15
    temp = 300.
    thickness = 0.018
    surface = None
    SRH = []
    nxc = np.logspace(10, 17)
    material = 'Si'

    def __init__(self, **kwargs):

        for i in kwargs:
            if hasattr(self, i):
                setattr(self, i, kwargs[i])

    def params(self):
        dic = collections.OrderedDict()
        dic['Na'] = self.Na
        dic['Nd'] = self.Nd
        dic['thickness'] = self.thickness
        dic['temp'] = self.temp

        return dic

if __name__ == '__main__':
    import matplotlib.pylab as plt
    spl = sample()
    spl.SRH.append(SRH_recombiation())
    lt = lifetime(spl, None)

    plt.plot(sample().nxc, 1. / lt.intrinsic())
    plt.plot(sample().nxc, 1. / lt.extrinsic())
    plt.plot(sample().nxc, 1. / lt.J0())
    plt.plot(sample().nxc, 1. / lt.Seff_symetric())
    plt.loglog()
    plt.show()
