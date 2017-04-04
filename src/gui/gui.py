
import sys
import collections
import numpy as np
from PyQt5.QtWidgets import (QWidget, QFileDialog, QPushButton, QTextEdit,
                             QGridLayout, QApplication, QLabel, QComboBox,
                             QCheckBox, QLineEdit, QStatusBar, QMainWindow, QSizePolicy, QTabWidget)

from PyQt5.QtCore import pyqtSignal, QTimer
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as
# FigureCanvas

from calculations.lifetime import lifetime, SRH_recombiation, sample, surface_recombaition
from loader import loader
# import matplotlib.pyplot as plt
# from matplotlib.figure import Figure
import pyqtgraph as pg

from pyqtgraph import QtGui


class CustomViewBox(pg.ViewBox):

    def __init__(self, parent=None):
        """
        Constructor of the CustomViewBox
        """
        super().__init__(parent)
        # print(self.__dict__.keys())

        # print(self.__dict__.keys(), '\n\n')
        #
        # print(self.__dict__['menu'].__dict__.keys())
        # print(self.__dict__['menu']['leftMenu'])
        # self._viewbox.fftCheck.setObjectName("fftCheck")

        # self.viewAll = QtGui.QRadioButton("Vue d\'ensemble")
        # self.viewAll.triggered.connect(self.autoRange)
        # self.menu.addAction(self.viewAll)
        # print(self.menu.__dict__['leftMenu'].__dict__)


class plotwidget(pg.PlotWidget):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    plot_type = 'lifetime'

    def __init__(self, parent=None):

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        super().__init__(name='Plot1', viewBox=CustomViewBox())

        for i in self.getViewBox().allChildren():
            print(i.__dict__)

        self.addLegend()
        self.setLogMode(x=True, y=True)

        self.p1 = self.plot(name='Intrinsic')
        self.p2 = self.plot(name='Shockley Read Hall')
        self.p3 = self.plot(name='Surface')
        self.p4 = self.plot(name='Effective')
        self.p5 = self.plot(name='Measured', symbol='o')

        self.setLabel('bottom', '&Delta;n', 'cm<sup>-3 </sup> ')

        self.p1.setPen('r', width=3)
        self.p2.setPen('g', width=3)
        self.p3.setPen('b', width=3)
        self.p4.setPen('k', width=3, style=pg.QtCore.Qt.DotLine)
        self.p4.setPen('k', width=3, style=pg.QtCore.Qt.DotLine)

    def compute_initial_figure(self):
        pass

    def update_rawdata(self, nxc, tau):
        self.plot_data(self.p5, nxc,  1. / tau, False)

    def update_modelling(self, SRH_pars, sample_inf, surface_recom, plot_type):
        # self.axes.cla()

        srh = SRH_recombiation()

        for k in SRH_pars.keys():
            if hasattr(srh, k):
                setattr(srh, k, SRH_pars[k]['value'])

        surface_rec = surface_recombaition()
        for k in surface_recom.keys():
            if hasattr(surface_rec, k):
                setattr(surface_rec, k, surface_recom[k]['value'])

        smp = sample()
        for k in sample_inf.keys():
            if hasattr(smp, k):
                setattr(smp, k, sample_inf[k]['value'])

        smp.SRH.append(srh)
        smp.surface = surface_rec

        self.lt = lifetime(smp, None)

        self.plot_data(self.p1, smp.nxc,  self.lt.intrinsic())
        self.plot_data(self.p2, smp.nxc,  self.lt.extrinsic())
        self.plot_data(self.p3, smp.nxc,  self.lt.J0())
        self.plot_data(self.p4, smp.nxc,  self.lt.J0() +
                       self.lt.extrinsic() + self.lt.intrinsic(), False)

    def plot_data(self, plot_ref, nxc, itau, constitute=True):

        if self.plot_type == 'lifetime':
            y = 1. / itau

        elif self.plot_type == 'Auger corrected lifetime':
            if not constitute:
                self.lt.sample.nxc = nxc
                y = 1 / (itau - self.lt.intrinsic())
            else:
                y = 1. / itau

        elif self.plot_type == 'inverse lifetime':
            y = itau

        elif self.plot_type == 'Inverse Auger corrected lifetime':
            if not constitute:
                self.lt.sample.nxc = nxc
                y = (itau - self.lt.intrinsic())
            else:
                y = itau

        else:
            y = None

        plot_ref.setData(
            x=nxc, y=y)


class extended_QLineEdit(QLineEdit):

    def wheelEvent(self, event):

        drct = event.angleDelta().y() / 1200

        x = float(self.text())
        x = x * (1. + drct)
        self.setText('{0:.3e}'.format(x))
        self.editingFinished.emit()


class item():

    def __init__(self, parent, name, value, _type, values=None):
        self.parent = parent
        self.name = name
        self.type = _type
        self._value = value
        self.values = values

    def doit(self):
        getattr(self, 'create_' + str(self.type).split("'")[1])()

    def create_list(self):

        self.Object = QComboBox(self.parent)
        for value in self.values:
            self.Object.addItem(str(value))
        self.Label = QLabel(self.name.replace('_', ' '))
        # return Object, Label

    def create_float(self):
        self.Object = extended_QLineEdit('{0:.2e}'.format(self._value))
        self.Label = QLabel(self.name.replace('_', ' '))
        # return Object, Label

    def create_bool(self):
        self.Object = QCheckBox(self.parent)
        if self._value:
            self.Object.toggle()
        self.Label = QLabel(self.name.replace('_', ' '))
        # return Object, Label

    def create_int(self):
        self.Object = QLineEdit('{0:.0f}'.format(self._value))
        self.Label = QLabel(self.name.replace('_', ' '))
        # return Object, Label

    def create_btn(self):
        self.Object = QPushButton(self._value)

    def create_str(self):
        self.Object = QLabel('{0:.0f}'.format(self._value))
        self.Label = QLabel(self.name.replace('_', ' '))

    def connect(self, function):
        self.Object.editingFinished.connect(function)

    @property
    def value(self):
        return getattr(self, 'get_' + str(self.type).split("'")[1])()

    @value.setter
    def value(self, value):
        return getattr(self, 'set_' + str(self.type).split("'")[1])(value)

    def get_float(self):
        return float(self.Object.text())

    def get_int(self):
        return int(float(self.Object.text()))

    def get_bool(self):
        return self.Object.isChecked()

    def get_list(self):
        return str(self.Object.currentText())

    def get_str(self):
        return str(self.Object.text())

    def set_float(self, value):
        self.Object.setText('{0:.2e}'.format(value))

    def set_int(self, value):
        self.Object.setText(str(value))
        pass

    def set_bool(self, value):
        pass

    def set_list(self, value):
        if value in self.values:
            index = self.values.index(value)
            self.Object.setCurrentIndex(index)
        pass

    def set_str(self, value):
        self.Object.setText(str(value))
        pass


class fitting_values(QWidget):

    SRH_no = [
        ('No of defects', [1, int]),
    ]

    modelling_changed = pyqtSignal()

    def __init__(self, parent):
        # load the sample values
        self.sample = collections.OrderedDict()
        for k, v in sample().params().items():
            self.sample[k] = {'value': v, '_type': float}
            self.sample[k]['name'] = k

        self.SRH_no = collections.OrderedDict(self.SRH_no)
        # load the SRH parameters
        self.SRH_pars = collections.OrderedDict()
        for k, v in SRH_recombiation().params().items():
            self.SRH_pars[k] = {'value': v, '_type': float}
        # get the human readable names
        for k, v in SRH_recombiation().hr_params().items():
            self.SRH_pars[k]['name'] = v

        # load the SRH parameters
        self.surface_pars = collections.OrderedDict()
        for k, v in surface_recombaition().params().items():
            self.surface_pars[k] = {'value': v, '_type': float}

        for k, v in surface_recombaition().hr_params().items():
            self.surface_pars[k]['name'] = v

        super().__init__()
        self.parent = parent

        self.initUI()
        # self.figure = MyDynamicMplCanvas()

    def initUI(self):

        grid = QGridLayout()

        for row, dic in zip(range(len(self.dics)), self.dics):
            col = 0
            for key, value in dic.items():
                value['item'] = item(self.parent, **value)
                value['item'].doit()
                value['item'].connect(self.gui2dics)

                grid.addWidget(value['item'].Label,  row * 2, col)
                grid.addWidget(value['item'].Object,  row * 2 + 1, col)

                col += 1

                dic[key] = value

        self.setLayout(grid)
        self.gui2dics()
        self.dics2gui()

        # self.show()

    def params(self):

        _params = collections.OrderedDict()
        for i in [self.sample,   self.SRH_pars, self.surface_pars]:
            _params.update(i)

        return _params

    @property
    def dics(self):
        return [self.sample,  self.SRH_pars, self.surface_pars]

    def gui2dics(self):

        for dic in self.dics:
            for k, v in dict(dic).items():
                dic[k]['value'] = v['item'].value

        self.dics2gui()

    def dics2gui(self):

        for dic in self.dics:
            for k, v in dict(dic).items():
                v['item'].value = v['value']

        self.modelling_changed.emit()


class RawData_widget(QWidget):
    data = None
    rawdata_changed = pyqtSignal()

    def __init__(self, parent):
            # super(LossAnalysisGui, self).__init__(parent)
        super().__init__()
        self.parent = parent

        self.initUI()

    def initUI(self):
        grid = QGridLayout()

        label = QLabel('No file selected')

        button = QPushButton('Load your data')

        grid.addWidget(button, 0, 0)
        grid.addWidget(label, 0, 1)

        button.clicked.connect(self.loadfile)
        self.setLayout(grid)

    def loadfile(self):
        exts = ''
        for k, v in loader.loadersandext.items():
            exts += '{0} ({1});;'.format(k, v)

        exts.strip(';;')

        fname, ext = QFileDialog.getOpenFileName(self, 'Open file', "", exts)

        if fname is not None:
            for k in loader.loadersandext.keys():
                if k in ext:
                    self.data = loader.loaders[k](fname)
                    self.rawdata_changed.emit()


class Widget_holder(QTabWidget):

    def __init__(self, parent):
        # super(LossAnalysisGui, self).__init__(parent)
        super().__init__()
        self.parent = parent

        self.initUI()

    def initUI(self):

        grid = QGridLayout(self)
        grid2 = QGridLayout()
        tabs = QTabWidget()

        self.fv = fitting_values(self)
        self.rd = RawData_widget(self)

        tabs.addTab(self.fv, "modelling")
        tabs.addTab(self.rd, "measured data")
        # self.addTab(self.tab2, "raw_data")
        # cont = start_the_measurement(self.parent)
        grid.addWidget(tabs, 0, 0)

        self.fv.modelling_changed.connect(self.update_modelling)
        self.rd.rawdata_changed.connect(self.update_rawdata)

        self.dc = plotwidget(self.parent)

        self.lb = QLabel('Plot type')
        self.cb = QComboBox()
        self.cb.addItems(["lifetime", "inverse lifetime",
                          "murphy", 'Auger corrected lifetime', 'Inverse Auger corrected lifetime'])

        grid2.addWidget(self.lb, 0, 0)
        grid2.addWidget(self.cb, 0, 1)

        # self.setLayout(grid2)
        grid.addWidget(self.dc, 0, 1)
        grid.addLayout(grid2, 1, 1)

        self.cb.currentIndexChanged.connect(self.plot_type_change)
        # lo.hide_panel.connect(la.check_visability)
        # la.hide_panel.connect(lo._show)

        self.fv.modelling_changed.emit()
        self.setLayout(grid)
        self.show()

    def plot_type_change(self, i):
        self.dc.plot_type = self.cb.itemText(i)
        self.update_rawdata()
        self.update_modelling()

    def update_modelling(self):
        self.dc.update_modelling(self.fv.SRH_pars, self.fv.sample,
                                 self.fv.surface_pars, 'regular')

    def update_rawdata(self):
        if self.rd.data is not None:
            self.dc.update_rawdata(self.rd.data['nxc'], self.rd.data['tau'])
        # q hack so the window size doesn't change
        # la.hide()
        # lo._show()


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'lifetime measurement system'
        self.left = 100
        self.top = 100
        self.width = 300
        self.height = 500
        self.initUI()

    def initUI(self):

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.statusBar().showMessage('Opening program')

        grid = QGridLayout()

        self.form_widget = Widget_holder(self)
        self.setCentralWidget(self.form_widget)

        self.show()


def main():

    # logfile = open('traceback_log.txt', 'w')
    app = QApplication(sys.argv)
    # try:
    lag = App()
    # except:
    # traceback.print_exc(file=logfile)

    lag.show()
    app.exec_()
    # logfile.close()
    # sys.exit(app.exec_())
