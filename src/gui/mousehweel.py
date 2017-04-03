from PyQt5 import QtWidgets
import sys

class MyWindow(QtWidgets.QMainWindow):
  def __init__(self):
    QtWidgets.QMainWindow.__init__(self)
    self.label = QtWidgets.QLabel("No data")
    self.setCentralWidget(self.label)
    self.setWindowTitle("QMainWindow WheelEvent")
    self.x = 0

  def wheelEvent(self,event):
    self.x =self.x + event.angleDelta().y()/120
    self.label.setText("Total Steps: " + str(self.x))

def main():
  app = QtWidgets.QApplication(sys.argv)
  window = MyWindow()
  window.show()
  return app.exec_()

if __name__ == '__main__':
 main() 
