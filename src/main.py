import sys
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QPushButton, QMainWindow, QWidget, QApplication, QLabel, QHBoxLayout, QVBoxLayout, QSplitter, QListWidget, QListWidgetItem, QSizePolicy
from lib.mcp2221a import Mcp2221a, getMcp2221as
from lib.opd import Max7310Pin, Max7310Reg, OpdAddress, BusShutdownState, OpdCardState, OpdPowerState, opd_table, IspModeState, UartState, CBResetState
import pyqtgraph as pg
import logging
import numpy as np
logger = logging.getLogger(__name__)

MENUBARWIDTH= 300

class OPDPWRPushButton(QPushButton):
    def __init__(self, text, chip: Mcp2221a):
        super().__init__()
        self.setText(text)
        self.clicked.connect(self.toggle_power)
        self.chip = chip
        self.setStyleSheet("background-color: red")

    def toggle_power(self):
        match self.chip.toggleOPDPWR():
            case OpdPowerState.unpowered:
                self.setStyleSheet("background-color: red")
            case OpdPowerState.powered:
                self.setStyleSheet("background-color: green")
            case _ as val:
                raise RuntimeError("toggleOPDPWR returned unknown value", val)


class SDPushButton(QPushButton):
    def __init__(self, text, chip: Mcp2221a):
        super().__init__()
        self.setText(text)
        self.clicked.connect(self.toggle_shutdown)
        self.chip = chip
        self.setStyleSheet("background-color: red")

    def toggle_shutdown(self):
        match self.chip.toggleSD():
            case BusShutdownState.shutdown:
                self.setStyleSheet("background-color: red")
            case BusShutdownState.nominal:
                self.setStyleSheet("background-color: green")
            case _:
                raise RuntimeError("toggleSD returned unknown value")

class OPDENPushButton(QPushButton):
    def __init__(self, text, chip: Mcp2221a, cardID: int):
        super().__init__()
        self.setText(text)
        self.clicked.connect(self.toggle_EN)
        self.chip = chip
        self.id = cardID
        self.state = OpdCardState.unpowered
        self.updateState()

    def updateState(self):
        match self.state:
            case OpdCardState.unpowered:
                self.setStyleSheet("background-color: red")
            case OpdCardState.powered:
                self.setStyleSheet("background-color: green")
            case _:
                raise RuntimeError("button state doesn't make sense")

    def toggle_EN(self):
        logger.debug(f"TOGGLING CARD #{self.id}")
        next = True if self.state.next() == OpdCardState.powered else False
        self.state = self.chip.set_node_EN(self.id, next)
        self.updateState()

class OPDIspPushButton(QPushButton):
    def __init__(self, text, chip: Mcp2221a, cardID: int):
        super().__init__()
        self.setText(text)
        self.clicked.connect(self.toggle_isp)
        self.chip = chip
        self.id = cardID
        self.state = IspModeState.disabled
        self.updateState()

    def updateState(self):
        match self.state:
            case IspModeState.disabled:
                self.setStyleSheet("background-color: red")
            case IspModeState.enabled:
                self.setStyleSheet("background-color: green")
            case _:
                raise RuntimeError("button state doesn't make sense")

    def toggle_isp(self):
        logger.debug(f"TOGGLING ISPMODE FOR CARD #{self.id}, current state is: {self.state}")
        newstate = self.state.next()
        logger.debug(f" new state is {newstate}")
        next = True if newstate == IspModeState.enabled else False
        self.state = self.chip.set_node_ISP(self.id, next)
        self.updateState()

class OPDUartPushButton(QPushButton):
    def __init__(self, text, chip: Mcp2221a, cardID: int):
        super().__init__()
        self.setText(text)
        self.clicked.connect(self.toggle_uart)
        self.chip = chip
        self.id = cardID
        self.state = UartState.disabled
        self.updateState()

    def updateState(self):
        match self.state:
            case UartState.disabled:
                self.setStyleSheet("background-color: red")
            case UartState.enabled:
                self.setStyleSheet("background-color: green")
            case _:
                raise RuntimeError("button state doesn't make sense")

    def toggle_uart(self):
        logger.debug(f"TOGGLING UART FOR CARD #{self.id}, current state is: {self.state}")
        newstate = self.state.next()
        logger.debug(f" new state is {newstate}")
        next = True if newstate == UartState.enabled else False
        self.state = self.chip.set_node_UART(self.id, next)
        self.updateState()

class OPDCBResetPushButton(QPushButton):
    def __init__(self, text, chip: Mcp2221a, cardID: int):
        super().__init__()
        self.setText(text)
        self.clicked.connect(self.toggle_cb_reset)
        self.chip = chip
        self.id = cardID
        self.state = CBResetState.disabled
        self.updateState()

    def updateState(self):
        match self.state:
            case CBResetState.disabled:
                self.setStyleSheet("background-color: red")
            case CBResetState.enabled:
                self.setStyleSheet("background-color: green")
            case _:
                raise RuntimeError("button state doesn't make sense")

    def toggle_cb_reset(self):
        logger.debug(f"TOGGLING CB RESET FOR CARD #{self.id}, current state is: {self.state}")
        newstate = self.state.next()
        logger.debug(f" new state is {newstate}")
        next = True if newstate == CBResetState.enabled else False
        self.state = self.chip.set_node_CB_RESET(self.id, next)
        self.updateState()

class RollingPlot():
    def __init__(self, parent: QWidget, outer: MainWindow):
        #pane =  QWidget(parent)
        self.graphWidget = pg.PlotWidget(parent)
        self.graphWidget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        #self.setCentralWidget(self.graphWidget)
        self.buffer = np.zeros((3, 200)).tolist()

        self.t = np.arange(200)
        self.i = np.zeros(200)
        self.v = np.zeros(200)
        self.p = np.zeros(200)

        self.showCurrent: bool = True
        self.showVoltage: bool = True
        self.showPower: bool = True

        self.outer = outer

        self.graphWidget.setBackground("w")
        self.graphWidget.setTitle("card current consumption")
        self.graphWidget.setLabel("left", "mA")
        self.graphWidget.setLabel("bottom", "Time")

        currentButton = QPushButton("current", parent)
        currentButton.clicked.connect((lambda : self.toggle_current()))
        voltageButton = QPushButton("voltage", parent)
        voltageButton.clicked.connect((lambda : self.toggle_voltage()))
        powerButton = QPushButton("power", parent)
        powerButton.clicked.connect((lambda : self.toggle_power()))


        layout = QVBoxLayout(parent)
        layout.addWidget(self.graphWidget)
        layout.addWidget(currentButton)
        layout.addWidget(voltageButton)
        layout.addWidget(powerButton)

        blue = pg.mkPen(color=(0, 0, 255), width=2)
        red = pg.mkPen(color=(255, 0, 0), width=2)
        purple = pg.mkPen(color=(255, 0, 255), width=2)
        self.current_line = self.graphWidget.plot(self.t, self.i, pen=blue)
        self.voltage_line = self.graphWidget.plot(self.t, self.v, pen=red)
        self.power_line = self.graphWidget.plot(self.t, self.p, pen=purple)

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

    def update_plot_data(self):
        self.t = np.roll(self.t, -1)
        self.t[-1] = self.t[-2] + 1

        self.i = np.roll(self.i, -1)
        self.v = np.roll(self.v, -1)
        self.p = np.roll(self.p, -1)
        current_mA = self.outer.chips[self.outer.selectedChip].ina226.current_mA
        voltage = self.outer.chips[self.outer.selectedChip].ina226.bus_voltage
        power_mW = self.outer.chips[self.outer.selectedChip].ina226.power_mW
        self.i[-1] = current_mA
        self.v[-1] = voltage
        self.p[-1] = power_mW
        #logger.debug(f"reading data {sample}")
        if (self.showCurrent):
            self.current_line.setData(self.t, self.i)
        else:
            self.current_line.setData(self.t, np.zeros(len(self.t)))
        if (self.showVoltage):
            self.voltage_line.setData(self.t, self.v)
        else:
            self.voltage_line.setData(self.t, np.zeros(len(self.t)))
        if (self.showPower):
            self.power_line.setData(self.t, self.p)
        else:
            self.power_line.setData(self.t, np.zeros(len(self.t)))



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(500, 500, 500, 500)
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

                label = QLabel(f"{row[0]}, {row[1]}")
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
