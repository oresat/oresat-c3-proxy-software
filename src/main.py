import sys
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QPushButton, QMainWindow, QWidget, QApplication, QLabel, QHBoxLayout, QVBoxLayout, QSplitter, QListWidget, QListWidgetItem
from lib.mcp2221a import Mcp2221a, getMcp2221as
from lib.opd import MAX7310_AD_POL, BusShutdownState, OpdCardState, OpdPowerState, opd_table
from smbus2 import i2c_msg
import pyqtgraph as pg
import logging
import numpy as np
logger = logging.getLogger(__name__)

#python inheritence is dumb dumb stoopid
#class mcpListItem(QListWidgetItem):
#    chipIndex = 0
#    def __init__(self, text):
#        super().__init__(self, text, type=super().ItemType.UserType)


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
                raise RunTimeError("toggleSD returned unknown value")

class OPDCardPushButton(QPushButton):
    def __init__(self, text, chip: Mcp2221a, cardID: int):
        super().__init__()
        self.setText(text)
        self.clicked.connect(self.toggle_card)
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

    def toggle_card(self):
        #match self.chip.toggleOPDPWR():
        logger.debug(f"TOGGLING CARD #{self.id}")
        next = True if self.state.next() == OpdCardState.powered else False
        self.state = self.chip.opd_enable_disable_node(self.id, next)

class RollingPlot():
    def __init__(self, parent: QWidget, outer: MainWindow):
        self.graphWidget = pg.PlotWidget()
        #self.setCentralWidget(self.graphWidget)

        self.x = np.arange(200)
        self.y = np.zeros(200)
        self.outer = outer

        self.graphWidget.setBackground("w")
        self.graphWidget.setTitle("Live Sensor Data")
        self.graphWidget.setLabel("left", "Amplitude")
        self.graphWidget.setLabel("bottom", "Time")

        pen = pg.mkPen(color=(255, 0, 0), width=2)
        self.data_line = self.graphWidget.plot(self.x, self.y, pen=pen)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

    def update_plot_data(self):
        self.x = np.roll(self.x, -1)
        self.x[-1] = self.x[-2] + 1

        self.y = np.roll(self.y, -1)
        sample = self.outer.chips[self.outer.selectedChip].ina226.current_mA
        self.y[-1] = sample
        logger.debug(f"reading data {sample}")
        self.data_line.setData(self.x, self.y)


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




#    def toggleOPD(self, idx):
#        if self.selectedChip == None:
#            return
#
#        chip = self.chips[idx]
#        chip.toggleOPD()
#
#
#    def toggleSD(self, idx):
#        if self.selectedChip == None:
#            return
#
#        chip = self.chips[idx]
#        chip.toggleShutdown()

        #change app state to represent which chip is active
        #function to get called on refresh

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
            itemWidget.setFixedSize(350, 20)
            lineText = QLabel(f"{idx}: {chip.usbPath.decode()}")
            opdPushButton = OPDPWRPushButton("OPD_PWR", chip)
            opdPushButton.setObjectName(str(idx))
            sdPushButton = SDPushButton("SD", chip)
            sdPushButton.setObjectName(str(idx))
            logger.info(f"idx is {idx}")
            #create a new scope with another lambda so they stay seperate between loop iterations
            itemLayout = QHBoxLayout(itemWidget)
            itemLayout.setContentsMargins(10, 4, 5, 2)
            itemLayout.addWidget(lineText)
            itemLayout.addStretch()
            itemLayout.addWidget(opdPushButton)
            itemLayout.addWidget(sdPushButton)
            self.chipSelector.addItem(item)
            self.chipSelector.setItemWidget(item, itemWidget)



            #item = QListWidgetItem()
            #QListWidgetItem(f"{idx}: {chip.usbPath.decode()}", self.chipSelector)
            #QPushButton(text="idk", parent=item)
            #self.chipSelector.addItem(item)


        #self.chips[0].probe_bus() #TODO: replace with scan button

    def chipSelected(self, item):
        #this is super jank, but inhereting the QListWidgetItem is really weird and stinky, + this works + ratio + bozo no CS degree   ~\(:/)/~
        self.selectedChip = self.chipSelector.row(item)#item.text()[0]
        self.plot.update_plot_data()
        logger.info(f"chip selected {self.selectedChip}")


    def updateOpdMenu(self, opdList: QListWidget):
        opdList.clear()

        #address = 0x40
        #reg = 0x00
        #buf = bytearray([0x48, 0xdf])

        #print("(main)ina226 i2c write ", address, reg, buf)



        ##write = i2c_msg.write(0x40, [0x48, 0xDF])   # select register
        ##read  = i2c_msg.read(0x40, 2)          # read 2 bytes back
        #self.chips[self.selectedChip].i2c.write_block_data(address, reg, buf)

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
                widget.setFixedSize(350, 20)

                label = QLabel(f"{row[0]}, {row[1]}")
                opdButton = OPDCardPushButton("toggle OPD", chip, int(row[1]))
                opdButton.clicked.connect((lambda  : lambda : opdButton.toggle_card)())
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(5, 2, 5, 2)
                layout.addWidget(label)
                layout.addStretch()
                layout.addWidget(opdButton)
                opdList.addItem(item)
                opdList.setItemWidget(item, widget)

                #opdList.addItem(f"{row[0]}, {row[1]}, {self.chips[self.selectedChip].probe_addr(row[1])}")

        logger.info("current: {:.3f}mA, voltage: {:.3f}V".format(chip.ina226.current_mA, chip.ina226.bus_voltage))


    def drawOpdMenu(self, opdRoot: QWidget):
        label = QLabel("Opd Menu", opdRoot)
        opdScanButton = QPushButton(text="scan")
        opdList = QListWidget(opdRoot)
        opdScanButton.clicked.connect((lambda _list : lambda : self.updateOpdMenu(_list))(opdList))
        self.updateOpdMenu(opdList)
        layout = QVBoxLayout(opdRoot)
        layout.addWidget(label)
        layout.addWidget(opdList)
        layout.addWidget(opdScanButton)


    def drawChipSelector(self, parent: QSplitter):
        label = QLabel("Chip Selector", parent)
        refreshButton = QPushButton(text="REFRESH")
        refreshButton.clicked.connect(self.updateChipSelector)

        self.chipSelector = QListWidget(parent)
        self.chipSelector.itemClicked.connect(self.chipSelected)
        self.scanChips()

        layout = QVBoxLayout(parent)
        layout.addWidget(label)
        layout.addWidget(self.chipSelector)
        layout.addWidget(refreshButton)


    def drawSidePanel(self, parent: QSplitter):
        #root and layout
        panelLayout = QHBoxLayout()
        splitter = QSplitter(QtCore.Qt.Orientation.Vertical, parent)
        splitter.setChildrenCollapsible(False)
        panelLayout.addWidget(splitter)
        parent.addWidget(splitter)

        #children
        chipSelectorMenu = QWidget()
        self.drawChipSelector(splitter)

        opdMenu = QWidget() #QLabel("OPD Control")
        self.drawOpdMenu(opdMenu)
        splitter.addWidget(opdMenu)

    def initUI(self):
        root = QWidget()
        self.setCentralWidget(root)

        layout = QHBoxLayout()
        splitter = QSplitter(root)

        self.drawSidePanel(splitter)
        #self.updateChipSelector()

        #label2 = QLabel("REPLACE MEEEE", self)
        #label2.setStyleSheet("background-color: grey")
        self.plot = RollingPlot(root, self)

        layout.addWidget(splitter)
        root.setLayout(layout)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.plot.graphWidget)


def main():

    logging.basicConfig(level=logging.DEBUG)
    logger.info('started c3-proxy software')
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())



main()
