####
# This moduel is for calibrating a PL measurement self consistently
# It reques:
#          A QSS measurement where the G the same order at dPL/dt
# Note:
#   The order of Ai must be set correctly for the fitting to converge
####

import sys,os
import numpy as np 
sys.path.append('/home/mattias/Dropbox/CommonCode')
sys.path.append('C:\Users\mattias\Documents\My Dropbox\CommonCode')
sys.path.append('C:\Users\mattias\Dropbox\CommonCode')

from Recombination_v2_01 import Radiative
from NumericalDifferentiation import Finite_Difference,Regularisation
from scipy.optimize import minimize
from scipy.interpolate import interp1d

import matplotlib.pylab as plt

class SelfConsistentMethod():
        
        def __init__(self,Ai=1e4,LowerLimit = 0.15,Width=None,Doping=None):

            self.Ai = Ai
            self.Ai_Order = 1e-16
            self.LowerLimit = LowerLimit  # This is the fraction of th max generationr  used to find Ai
            self.Doping = Doping
            self.Analysis = 'simple'
            self.Width=Width





        def Cal_Deltan_simple(self,PL,Ai,Doping=None):
            if Doping==None:
                self.Deltan = PL/Ai/self.Ai_Order/Radiative().Blow
            else:
                for i in range(3):
                    self.Deltan = PL/Ai/Doping/Radiative().B(self.Deltan,Doping)
                

        def Cal_Deltan_Full(self,PL,Ai):
            self.Deltan = (-self.Doping +np.sqrt(self.Doping**2+4*PL/Ai/self.Ai_Order/Radiative().Blow))/2
            # print 'The stating Delta n is',Deltan

            for i in range(3):
                self.Deltan = (-self.Doping +np.sqrt(self.Doping**2+4*PL/Ai/self.Ai_Order/Radiative().B(self.Deltan,self.Doping)))/2
            # if np.sum(self.Deltan) == 0 :
                # self.Cal_Deltan_simple(PL,Ai,self.Doping)
            # print Ai,


        def Generalised_Lifetime(self,time,Gen,PL,Ai=None):
            #this function includes the effects of doping. Ai still includes the doping term until and is seperated at the end.  
            if Ai==None:
                Ai = self.Ai
            
            if self.Doping == None:
                self.Analysis = 'simple'


            Cal_Deltan = getattr(self,'Cal_Deltan_'+self.Analysis)
            Cal_Deltan(PL,Ai)

            dDeltan_dt = Regularisation().FirstDerivative(time,self.Deltan,1e-20)

            return self.Deltan/(Gen- dDeltan_dt)


        def Minimisation_Function(self,Ai):
            #This has to return a value based on the splitting of the curve
            #The split in the function 
          

            Tau_Lower = self.Generalised_Lifetime(self.time[self.Analysis_Lower],  self.Gen[self.Analysis_Lower],   self.PL[self.Analysis_Lower],Ai=abs(Ai)  )
            Tau_Upper = self.Generalised_Lifetime(self.time[self.Analysis_Upper],  self.Gen[self.Analysis_Upper],   self.PL[self.Analysis_Upper],Ai=abs(Ai)  )

            Tau_Adjust = interp1d(self.PL[self.Analysis_Upper],Tau_Upper,kind='linear',bounds_error=False,fill_value =Tau_Lower[0])
            # print Ai, sum(abs(Tau_Lower-Tau_Adjust(self.PL[self.Analysis_Lower]))/Tau_Lower)
            if Ai<0:
                return sum(abs(Tau_Lower-Tau_Adjust(self.PL[self.Analysis_Lower]))/Tau_Lower)**2
            else:
                return sum(abs(Tau_Lower-Tau_Adjust(self.PL[self.Analysis_Lower]))/Tau_Lower)

        def Checks(self):
            ###
            #This function performs the checks to ensure nothing went wrong. These include:
            #   Low Injection
            #   Constant effective Lifetime?
            if self.Doping ==None:
                Doping = 1e16
            else:
                Doping = self.Doping


            if np.amax(self.Deltan) > Doping/100 :
                print 'Warning, Deltan Values used Not in low injection'




            # Limited_Index = np.where((self.Gen<=Max_gen*LowerLimit))[0]
            # if self.Tau[Limited_Index] < 50:
                # print 'Warning, lifetime values used may cause problems'




        def Find_AI(self,time, Gen,PL):
            #Need to supply Tau and PL for a fast speed
            
            #This is done by assuming at one PL value there should only be one tau value, then this occurs though changing Ai
            #We also restrict the data to a 'Good Region'
            if self.Width==None:
                print 'Need to input Width in cm'
                return False

            self.Gen = Gen/self.Width
            self.PL = PL
            self.time = time


            Max_gen = np.amax(self.Gen)
            Max_Time = np.amax(self.time)

            self.Limited_Index = np.where((self.Gen>=Max_gen*self.LowerLimit))[0]
            Max_Index = np.where((self.Gen==Max_gen))[0]

            Analysis_Upper = np.where((self.time>=self.time[Max_Index]))[0]
            Analysis_Lower = np.where((self.time<=self.time[Max_Index]))[0]

            self.Analysis_Upper = np.intersect1d(Analysis_Upper,self.Limited_Index)
            self.Analysis_Lower = np.intersect1d(Analysis_Lower,self.Limited_Index)


            res = minimize(self.Minimisation_Function,self.Ai,tol=1e-0)
            self.Ai = abs(res.x)
            


            self.Tau = self.Generalised_Lifetime(self.time,self.Gen,self.PL,self.Ai)

        def Perform_SelfConsistent_Measumrement(self,event):
            self.Perform_Measurement(self,event,'SelfConsistent1')
            self.QSS = self.Data
            self.Perform_Measurement(self,event,'SelfConsistent2')

        def GetValues_SelfConsistent1(self,event):
            self.Intensity = self.CHK_float(self.m_Intensity,event)
            self.Binning = self.CHK_int(self.m_Binning,event)
            self.Averaging = self.CHK_int(self.m_Averaging,event)
            self.Peroid = self.CHK_float(self.m_Period,event)
            self.Offset_Before= self.CHK_float(self.m_Offset_Before,event)
            self.Offset_After= self.CHK_float(self.m_Offset_After,event)
            self.Waveform = self.m_Waveform.GetStringSelection()  
            self.Channel = self.m_Output.GetStringSelection()  
            self.Threshold = self.CHK_float(self.m_Threshold,event)


        def GetValues_SelfConsistent2(self,event):

            self.Binning = self.CHK_int(self.m_Binning,event)
            self.Averaging = self.CHK_int(self.m_Averaging,event)
            self.Peroid = self.CHK_float(self.m_Period,event)
            self.Offset_Before= self.CHK_float(self.m_Offset_Before,event)
            self.Offset_After= self.CHK_float(self.m_Offset_After,event)



def Bin_Data(data,BinAmount):
    
        
        if BinAmount ==1:
            return data
        #This is part of a generic binning class that I wrote.
        #IT lets binning occur of the first axis for any 2D or 1D array
        if len(data.shape)==1:
            data2 = np.zeros((data.shape[0]//BinAmount))
        else:
            data2 = np.zeros((data.shape[0]//BinAmount,data.shape[1]))

        
        for i in range(data.shape[0]//BinAmount):

            data2[i] = np.mean(data[i*BinAmount:(i+1)*BinAmount],axis=0)

        return data2



if __name__ == "__main__":
    #This is to test if it works
    Roll_Num = 5.5e-6*-0.01

    Ais = []
    os.chdir('C:\Users\mattias\Desktop\QSSPL Delays')
    Files = ['808nm_Fall-47hz_1.Raw Data.dat']#,'808nm_Fall-90hz_1.Raw Data.dat','808nm_Fall-166hz_1.Raw Data.dat']
    # Files2 = ['808nm_Fall-47hz_2.Raw Data.dat','808nm_Fall-90hz_2.Raw Data.dat','808nm_Fall-166hz_2.Raw Data.dat']
    # for i in Files2:
        # Files.append(i)
    print Files
    for roll in [-4,0,4]: 
        roll_Val = 5.6e-6*roll
        for File in Files:
            data = np.genfromtxt(File,names=True,delimiter='\t')
            
            index = np.where(data['Time_s']<.9e-3)[0]

            data['Gen_V']-=np.average(data['Gen_V'][index])
            data['PL_V'] -= np.average(data['PL_V'][index])
            # data['PL_V'] -= data['PL_V'][index]

            if '2' in File:
                # print 'changed columns'
                temp = abs(data['Gen_V'])
                data['Gen_V']=abs(data['PL_V'])
                data['PL_V'] = temp
                # plt.figure()
                # plt.figure('test')
                # plt.plot(data['Time_s'],data['PL_V'],'r-')
                # plt.plot(data['Time_s'],data['Gen_V'],'b-')
                # plt.figure('other')

            data['Gen_V']*= .555*1.24e16
            # data['PL_V'] = np.roll(data['PL_V'],int(Roll_Num/data['Time_s'][1]))
            data['PL_V'] = np.roll(data['PL_V'],int(roll_Val/data['Time_s'][1]))
            
            
            Wafer = SelfConsistentMethod()
            Wafer.Width = 0.0152
            Wafer.Doping = 6.33e15
            Wafer.Ai = 1
            Wafer.Analysis = 'Full'

            print 'Here we go:\t', File,int(Roll_Num/data['Time_s'][1])
            Wafer.Find_AI(data['Time_s'],data['Gen_V'],data['PL_V'])
            Ais.append(Wafer.Ai[0]*Wafer.Ai_Order)
            # plt.plot(Wafer.Deltan,Wafer.Tau,'k.',label=File)
            plt.plot(Bin_Data(Wafer.Deltan[Wafer.Limited_Index],50),Bin_Data(Wafer.Tau[Wafer.Limited_Index]*1e6,50),'.',label=roll_Val*1e6)
            plt.title('Self Consistent affect of offset')
    plt.semilogx()
    plt.xlabel('Excess Carrier Density (us)')
    plt.ylabel('Lifetime (us)')
    plt.legend(loc=0,title = 'Introduced offset (us)')
    plt.show()
    data = np.genfromtxt('808nm_Fall-1hz_1.Raw Data.dat',names=True,delimiter='\t')



    data['Gen_V']*= .555*1.24e16/Wafer.Width
    print np.amax(data['Gen_V'])
    data['PL_V'] = np.roll(data['PL_V'],int(Roll_Num/data['Time_s'][1]))
    # print Ais/Wafer.Doping
    for Ai in Ais:
        print Ai,1./Ai
    for Ai in Ais:
        print 'Comparing time!!!!'
        # Wafer.Ai = Ai/Wafer.Ai_Order

        Tau = Wafer.Generalised_Lifetime(data['Time_s'],data['Gen_V'],data['PL_V'],Ai/Wafer.Ai_Order)
        
        plt.plot(Wafer.Deltan[::10],Tau[::10]*1e6,'k,',label=File)
    # plt.loglog()
    plt.xlim(3e12,2e14)
    plt.ylim(1e-5,1e-3)
    plt.ylim(1e-5*1e6,2e-4*1e6)
    plt.show()
