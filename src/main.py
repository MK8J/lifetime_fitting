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

# import the newly created GUI file
import gui.gui as gui
import sys
# from pyqt5 import QApplication

if __name__ == '__main__':
    gui.main()
    # print(gui.__dict__.keys())
    # # logfile = open('traceback_log.txt', 'w')
    # app = QApplication(sys.argv)
    # # try:
    # lag = App()
    # # except:
    # # traceback.print_exc(file=logfile)
    #
    # lag.show()
    # app.exec_()
    # # logfile.close()
    # sys.exit(app.exec_()
