from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QPushButton
import pyqtgraph as pg
import sys
from random import randint
from smbus2 import SMBus, i2c_msg
import gpiod



GPIOCHIP = "/dev/gpiochip2"
I2CADDR = 27

def i2c_setup():
    print(f"""using gpio:  {GPIOCHIP}
    using i2c address: {I2CADDR}
        is this correct? y/n""")
    if (input() != "y"):
        exit()



    print("gpiochip: ", gpiod.is_gpiochip_device(GPIOCHIP))
    with gpiod.Chip(GPIOCHIP) as chip:
        info = chip.get_info()
        print(f"{info.name}, [{info.label}] ({info.num_lines} lines)")

def temp_read():

    with SMBus(I2CADDR) as bus:
        # Read 64 bytes from address 80
        write = i2c_msg.write(24, [0b0101])
        read = i2c_msg.read(24, 2)
        bus.i2c_rdwr(write, read)
    #    print("result of write: ", write.buf)
    #    print("result of read: ", read.buf)
        rtn = int(0)
        #for k in range(read.len):
        #    h = read.len-k
        #    print(read.len, read.buf[0], read.buf[1])
        #rtn << 8
        rtn += int.from_bytes(read.buf[1])
        rtn = rtn >> 2
        return rtn

#i2c_setup()
#while(True):
#    print(temp_read())


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

        self.x = list(range(100))  # 100 time points
        self.y = [0 for _ in range(100)]  # 100 data points

        self.graphWidget.setBackground("w")

        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line = self.graphWidget.plot(self.x, self.y, pen=pen)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

        centerBtn = QPushButton(text="Center", parent=self)
        centerBtn.setFixedSize(100, 60)

    def update_plot_data(self):
        self.x = self.x[1:]  # Remove the first x element.
        self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.

        self.y = self.y[1:]  # Remove the first y element.
        self.y.append(temp_read())  # Add a new random value.

        self.data_line.setData(self.x, self.y)  # Update the data.


app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
w.show()
sys.exit(app.exec())
