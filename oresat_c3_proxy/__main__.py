import sys
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QPushButton, QMainWindow, QWidget, QApplication, QLabel, QHBoxLayout, QVBoxLayout, QSplitter, QListWidget, QListWidgetItem, QSizePolicy

from .lib.mcp2221a import Mcp2221a, getMcp2221as
from .lib.opd import opd_table, IspModeState, UartState, CBResetState
from .buttons import OPDPWRPushButton, SDPushButton, OPDENPushButton, OPDIspPushButton, OPDIspPushButton, OPDUartPushButton, OPDCBResetPushButton

import pyqtgraph as pg
import logging
import numpy as np
import pandas as pd
import datetime


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

csv_title = ""
csv_header = ["time", "mA", "V", "mW"]
#if someone passed a csv file to write to
if (len(sys.argv) > 1):
    csv_title = sys.argv[1]
    logger.debug("csv file passed, writing to" + csv_title)
    with open(csv_title, 'a') as fd:
        fd.write(",".join(csv_header) + "\n")


MENUBARWIDTH= 500


class RollingPlot():
    def __init__(self, parent: QWidget, outer: MainWindow):
        self.pw = pg.PlotWidget()
        self.pw.setBackground(background=None) #make background transparent
        self.outer = outer

        self.colorI = (35, 35, 163)    #blue
        self.colorV = (173,0,0)        #red
        self.colorP = (136, 24, 201)   #purble

        self.showCurrent: bool = True
        self.showVoltage: bool = True
        self.showPower: bool = True

        #central plotItem for curve 1
        #only axis on the left
        self.p1 = self.pw.plotItem
        self.p1.setLabels(left='Power (mW)', bottom='Time (s)')
        self.p1.getAxis('left').setPen(color=self.colorP)
        #self.p1.showGrid(x=True, y=True, alpha=0.3)
        self.p1.vb.sigResized.connect(self.update_views)

        #new ViewBox for curve 2
        #inner axis on the right
        self.p2 = pg.ViewBox()
        self.p1.showAxis('right')
        self.p1.scene().addItem(self.p2)
        self.p1.getAxis('right').linkToView(self.p2)
        self.p2.setXLink(self.p1)
        self.p1.getAxis('right').setLabel('Current (mA)', color=self.colorI)
        self.p1.getAxis('right').setPen(color=self.colorI)

        #new ViewBox for curve 3
        #outer axis on the right
        self.p3 = pg.ViewBox()
        self.ax3 = pg.AxisItem('right')
        self.p1.layout.addItem(self.ax3, 2, 3)
        self.p1.scene().addItem(self.p3)
        self.ax3.linkToView(self.p3)
        self.p3.setXLink(self.p1)
        self.ax3.setLabel('Voltage (mV)', color=self.colorV)
        self.ax3.setPen(color=self.colorV)

        self.buffer = np.zeros((3, 200)).tolist()
        self.t = np.arange(200)
        self.i = np.zeros(200)
        self.v = np.zeros(200)
        self.p = np.zeros(200)


        self.powerCurve = self.p1.plot(self.t, self.p, pen=pg.mkPen(self.colorP, width=5), name="Axis 1")
        #self.p1.addItem(self.powerCurve)

        self.currentCurve = pg.PlotCurveItem(self.t, self.i, pen=pg.mkPen(self.colorI, width=5), name="Axis 2")
        self.p2.addItem(self.currentCurve)
        self.voltageCurve = pg.PlotCurveItem(self.t, self.v, pen=pg.mkPen(self.colorV, width=5), name="Axis 3")
        self.p3.addItem(self.voltageCurve)

        self.outer = outer

        currentButton = QPushButton("current", parent)
        currentButton.clicked.connect((lambda : self.toggle_current()))
        voltageButton = QPushButton("voltage", parent)
        voltageButton.clicked.connect((lambda : self.toggle_voltage()))
        powerButton = QPushButton("power", parent)
        powerButton.clicked.connect((lambda : self.toggle_power()))

        layout = QVBoxLayout(parent)
        layout.addWidget(self.pw)
        layout.addWidget(currentButton)
        layout.addWidget(voltageButton)
        layout.addWidget(powerButton)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

    def toggle_current(self):
        self.showCurrent = not self.showCurrent

    def toggle_voltage(self):
        self.showVoltage = not self.showVoltage

    def toggle_power(self):
        self.showPower = not self.showPower

    def update_views(self):
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
        self.p3.setGeometry(self.p1.vb.sceneBoundingRect())
        self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)
        self.p3.linkedViewChanged(self.p1.vb, self.p3.XAxis)

    def update_plot_data(self):
        self.t = np.roll(self.t, -1)
        self.t[-1] = self.t[-2] + 1

        self.i = np.roll(self.i, -1)
        self.v = np.roll(self.v, -1)
        self.p = np.roll(self.p, -1)
        if (len(self.outer.chips) != 0):
            current_mA = self.outer.chips[self.outer.selectedChip].ina226.current_mA
            voltage_V = self.outer.chips[self.outer.selectedChip].ina226.bus_voltage
            power_mW = self.outer.chips[self.outer.selectedChip].ina226.power_mW
            if (csv_title): #if a csv path was passed, then write to it
                df = pd.DataFrame([[datetime.datetime.now(), current_mA, voltage_V, power_mW]], columns=csv_header)
                df.to_csv(csv_title, index=False, mode='a', header=False)
        else:
            current_mA = voltage_V = power_mW = 0

        self.i[-1] = current_mA
        self.v[-1] = voltage_V
        self.p[-1] = power_mW
        #logger.debug(f"reading data {sample}")
        self.currentCurve.setData(self.t, self.i)
        self.voltageCurve.setData(self.t, self.v)
        self.powerCurve.setData(self.t, self.p)
        if (self.showCurrent): #current
            if not self.p2.allChildren().__contains__(self.currentCurve):
                self.p2.addItem(self.currentCurve)
        else:
            self.currentCurve.setData(self.t, np.zeros(len(self.t)))
            if self.p2.allChildren().__contains__(self.currentCurve):
                self.p2.removeItem(self.currentCurve)

        if (self.showVoltage): #voltage
            if not self.p3.allChildren().__contains__(self.voltageCurve):
                self.p3.addItem(self.voltageCurve)
        else:
            if self.p3.allChildren().__contains__(self.voltageCurve):
                self.p3.removeItem(self.voltageCurve)

        if (self.showPower): #power
            if not self.p1.vb.allChildItems().__contains__(self.powerCurve):
                self.p1.addItem(self.powerCurve)
        else:
            if self.p1.vb.allChildItems().__contains__(self.powerCurve):
                self.p1.removeItem(self.powerCurve)



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(500, 500, 1500, 500)
        self.setWindowTitle("C3-Proxy Software")
        self.selectedChip = 0
        self.chipSelector = None
        self.chips: list[Mcp2221a] = []
        self.plot: RollingPlot
        self.initUI()

    def scanChips(self):
        for chip in self.chips:
            chip.__del__()
        self.chips.clear()
        self.chips = getMcp2221as()
        logger.info(f"here's chips {self.chips}")

    def updateChipSelector(self):
        self.chipSelector.clear()
        self.scanChips()
        for idx, chip in enumerate(self.chips):
            item = QListWidgetItem(self.chipSelector)
            itemWidget = QWidget()
            itemWidget.setFixedSize(MENUBARWIDTH, 20)
            lineText = QLabel(f"{idx}: {chip.usbPath.decode()}")
            lineText.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)
            opdPushButton = OPDPWRPushButton("OPD_PWR", chip)
            opdPushButton.setObjectName(str(idx))
            sdPushButton = SDPushButton("SD", chip)
            sdPushButton.setObjectName(str(idx))
            logger.info(f"idx is {idx}")
            itemLayout = QHBoxLayout(itemWidget)
            itemLayout.setContentsMargins(10, 2, 10, 2)
            itemLayout.addWidget(lineText)
            #itemLayout.addStretch()
            itemLayout.addWidget(opdPushButton)
            itemLayout.addWidget(sdPushButton)
            self.chipSelector.addItem(item)
            self.chipSelector.setItemWidget(item, itemWidget)


    def chipSelected(self, item):
        self.selectedChip = self.chipSelector.row(item)
        self.plot.update_plot_data()
        logger.info(f"chip selected {self.selectedChip}")


    def updateOpdMenu(self, opdList: QListWidget):
        opdList.clear()

        logger.debug(f"selected chip is {self.selectedChip}, self.chips is {self.chips}")

        if (len(self.chips) == 0):
            logger.debug("no chips detected")
            return

        chip = self.chips[self.selectedChip]

        for row in opd_table:

            addr = row[1]
            if(chip.probe_addr(row[1])):

                chip.max7310_initialize(addr)

                item = QListWidgetItem(opdList)
                widget = QWidget()
                #widget.setFixedSize(MENUBARWIDTH, 20)

                label = QLabel("{}, {:02X}".format(row[0], row[1]))
                enButton = OPDENPushButton("EN", chip, int(row[1]))
                #enButton.clicked.connect((lambda : enButton.toggle_EN))

                ispButton = OPDIspPushButton("ISP", chip, int(row[1]))
                #ispButton.clicked.connect((lambda  : lambda : ispButton.toggle_isp)())
                uartButton = OPDUartPushButton("UART", chip, int(row[1]))
                #uartButton.clicked.connect((lambda  : lambda : uartButton.toggle_uart)())
                resetButton = OPDCBResetPushButton("CB-RESET", chip, int(row[1]))
                #resetButton.clicked.connect((lambda  : lambda : resetButton.toggle_cb_reset)())

                layout = QHBoxLayout(widget)
                layout.setContentsMargins(10, 2, 10, 2)
                layout.addWidget(label)
                layout.addStretch()
                layout.addWidget(enButton)
                layout.addWidget(ispButton)
                layout.addWidget(uartButton)
                layout.addWidget(resetButton)
                opdList.addItem(item)
                opdList.setItemWidget(item, widget)

                #opdList.addItem(f"{row[0]}, {row[1]}, {self.chips[self.selectedChip].probe_addr(row[1])}")

        logger.info("current: {:.3f}mA, voltage: {:.3f}V".format(chip.ina226.current_mA, chip.ina226.bus_voltage))


    def drawOpdMenu(self, opdRoot: QWidget):
        label = QLabel("Opd Menu", opdRoot)
        label.setSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Minimum)
        opdScanButton = QPushButton(text="scan")
        opdScanButton.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        opdScanButton.setMinimumWidth(MENUBARWIDTH)
        opdList = QListWidget(opdRoot)
        opdScanButton.clicked.connect((lambda _list : lambda : self.updateOpdMenu(_list))(opdList))
        self.updateOpdMenu(opdList)
        layout = QVBoxLayout(opdRoot)
        layout.addWidget(label)
        layout.addWidget(opdList)
        layout.addWidget(opdScanButton)


    def drawChipSelector(self, parent: QSplitter):
        label = QLabel("Chip Selector", parent)
        label.setSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Minimum)
        refreshButton = QPushButton(text="REFRESH")
        refreshButton.clicked.connect(self.updateChipSelector)
        refreshButton.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        refreshButton.setMinimumWidth(MENUBARWIDTH)
        #refreshButton.setMinimumHeight(50)

        self.chipSelector = QListWidget(parent)
        self.chipSelector.itemClicked.connect(self.chipSelected)
        self.scanChips()

        layout = QVBoxLayout(parent)
        layout.addWidget(label)
        layout.addWidget(self.chipSelector)
        layout.addWidget(refreshButton)
        #layout.setSizeConstraints(QtWidgets.QLayout.SizeConstraint.SetMinimumSize, QtWidgets.QLayout.SizeConstraint.SetMinimumSize)
        #layout.setHorizontalSizeConstraint(CHIPSELECTORWIDTH)
        #layout.setMinimumWidth(CHIPSELECTORWIDTH)


    def drawSidePanel(self, parent: QSplitter):
        #root and layout
        panelLayout = QHBoxLayout()
        splitter = QSplitter(QtCore.Qt.Orientation.Vertical, parent)
        splitter.setChildrenCollapsible(False)
        panelLayout.addWidget(splitter)
        parent.addWidget(splitter)

        self.drawChipSelector(splitter)

        opdMenu = QWidget()
        self.drawOpdMenu(opdMenu)
        splitter.addWidget(opdMenu)

    def initUI(self):
        root = QWidget()
        self.setCentralWidget(root)

        layout = QHBoxLayout()
        splitter = QSplitter(root)

        self.drawSidePanel(splitter)

        graphPane = QWidget(root)
        self.plot = RollingPlot(graphPane, self)

        layout.addWidget(splitter)
        root.setLayout(layout)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(graphPane)


def main():

    logging.basicConfig(level=logging.DEBUG)
    logger.info('started c3-proxy software')
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())



main()
