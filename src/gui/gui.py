
import sys
import collections
import numpy as np
from PyQt5.QtWidgets import (QWidget, QFileDialog, QPushButton, QTextEdit,
                             QGridLayout, QApplication, QLabel, QComboBox,
                             QCheckBox, QLineEdit, QStatusBar, QMainWindow, QSizePolicy)

from PyQt5.QtCore import pyqtSignal, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from lifetime_calc import lifetime, SRH_params, sample
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):

        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.compute_initial_figure()
        # We want the axes cleared every time plot() is called
        # self.axes.hold(False)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        # self.mpl_toolbar = NavigationToolbar(self, self.parent)

    def compute_initial_figure(self):
        pass


class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself every second with a new plot."""

    # def __init__(self, parent=None):
    #     QWidget.__init__(self, parent)
    #     self.canvas = MplCanvas()  # create canvas that will hold our plot
    #     # createa navigation toolbar for our plot canvas
    #     self.navi_toolbar = NavigationToolbar(self.canvas, self)
    #
    #     self.vbl = QVBoxLayout()
    #     self.vbl.addWidget(self.canvas)
    #     self.vbl.addWidget(self.navi_toolbar)
    #     self.setLayout(self.vbl)

    def compute_initial_figure(self):
        self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')

    def update_figure(self, SRH_pars, sample_inf):

        self.axes.cla()
        srh = SRH_params()

        srh.Et = SRH_pars['Et'][0]
        srh.tau_e = SRH_pars[u"\U0001D70F<sub>e</sub>"][0]
        srh.tau_h = SRH_pars[u"\U0001D70F<sub>h</sub>"][0]

        smp = sample()

        smp.Na = sample_inf['Na'][0]
        smp.Nd = sample_inf['Nd'][0]
        smp.thickness = sample_inf['Thickness'][0]
        smp.temp = sample_inf['Temperature'][0]

        smp.SRH.append(srh)
        print('this one is', smp.temp)
        lt = lifetime(smp, None)

        # self.fig.clear()
        self.axes.plot(smp.nxc, 1. / lt.intrinsic())
        self.axes.plot(smp.nxc, 1. / lt.extrinsic())
        self.axes.set_yscale('log')
        self.axes.set_xscale('log')
        # self._fig.canvas.draw()
        # self.show()
        self.draw()

    # def update_figure(self):
    #     # Build a list of 4 random integers between 0 and 10 (both inclusive)
    #     l = [np.random.randint(0, 10) for i in range(4)]
    #     self.axes.cla()
    #     self.axes.plot([0, 1, 2, 3], l, 'r')
        # self.draw()


class extended_QLineEdit(QLineEdit):

    # def __init__(self):
        # print('yaaass')

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
    sample = [('Na', [0, float]),
              ('Nd', [1e16, float]),
              ('Thickness', [0.018, float]),
              ('Temperature', [300, float]),
              ]

    SRH_no = [
        ('No of defects', [1, int]),
    ]
    SRH_pars = [
        ('Et', [0, float]),
        (u"\U0001D70F" + '<sub>e</sub>', [1e-3, float]),
        (u'\U0001D70F' + '<sub>h</sub>', [1e-3, float]),
    ]

    # figure = None
    inputchange = pyqtSignal()

    def __init__(self, parent):
        self.sample = collections.OrderedDict(self.sample)
        self.SRH_no = collections.OrderedDict(self.SRH_no)
        self.SRH_pars = collections.OrderedDict(self.SRH_pars)

        super().__init__()
        self.parent = parent

        self.initUI()
        # self.figure = MyDynamicMplCanvas()

    def initUI(self):

        grid = QGridLayout()

        for row, dic in zip(range(len(self.dics)), self.dics):
            col = 0
            for key, value in dic.items():

                value.append(item(self.parent, key, *value))
                value[-1].doit()
                value[-1].connect(self.gui2dics)

                grid.addWidget(value[-1].Label,  row * 2, col)
                grid.addWidget(value[-1].Object,  row * 2 + 1, col)

                col += 1

                dic[key] = value

        self.setLayout(grid)
        self.gui2dics()
        self.dics2gui()

        # self.show()

    def params(self):

        _params = collections.OrderedDict()
        for i in [self.sample,   self.SRH_pars, ]:
            _params.update(i)

        return _params

    @property
    def dics(self):
        return [self.sample,  self.SRH_pars]

    def gui2dics(self):

        for dic in self.dics:
            for k, v in dict(dic).items():
                dic[k][0] = v[-1].value

        self.dics2gui()
        # if self.figure is not None:
        # print('about to go in')
        # self.figure.update_figure(self.SRH_pars, self.sample)

    def dics2gui(self):

        for dic in self.dics:
            for k, v in dict(dic).items():
                v[-1].value = v[0]

        self.inputchange.emit()


class Widget_holder(QWidget):

    def __init__(self, parent):
        # super(LossAnalysisGui, self).__init__(parent)
        super().__init__()
        self.parent = parent

        self.initUI()

    def initUI(self):

        grid = QGridLayout()
        self.fv = fitting_values(self.parent)

        # cont = start_the_measurement(self.parent)
        self.dc = MyDynamicMplCanvas(self.parent, width=5, height=4, dpi=100)
        # la = LoadFiles(self.parent)
        # print(fv.SRH_pars.values(), fv.sample)
        self.fv.inputchange.connect(self.update_figure)

        grid.addWidget(self.fv, 0, 0)
        # grid.addWidget(cont, 1, 0)
        grid.addWidget(self.dc, 0, 1)

        # lo.hide_panel.connect(la.check_visability)
        # la.hide_panel.connect(lo._show)

        self.setLayout(grid)
        self.show()

    def update_figure(self):
        self.dc.update_figure(self.fv.SRH_pars, self.fv.sample)

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

if __name__ == '__main__':

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
