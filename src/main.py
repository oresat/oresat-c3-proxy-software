import sys
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QPushButton, QMainWindow, QWidget, QApplication, QLabel, QHBoxLayout, QVBoxLayout, QSplitter, QListWidget, QListWidgetItem
from lib.mcp2221a import getMcp2221as
from lib.opd import opd_table
from smbus2 import i2c_msg
import logging
logger = logging.getLogger(__name__)

#python inheritence is dumb dumb stoopid
#class mcpListItem(QListWidgetItem):
#    chipIndex = 0
#    def __init__(self, text):
#        super().__init__(self, text, type=super().ItemType.UserType)




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(500, 500, 500, 500)
        self.setWindowTitle("C3-Proxy Software")
        self.selectedChip = 0
        self.chipSelector = None
        self.chips = []
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
    def updateChipSelector(self):
        self.chipSelector.clear()
        for chip in self.chips:
            chip.__del__()
        self.chips.clear()
        logger.info(f"here's chips {self.chips}")
        self.chips = getMcp2221as()
        for idx, chip in enumerate(self.chips):
            item = QListWidgetItem(self.chipSelector)
            itemWidget = QWidget()
            itemWidget.setFixedSize(350, 20)
            lineText = QLabel(f"{idx}: {chip.usbPath.decode()}")
            OPDPushButton = QPushButton("OPD_PWR")
            OPDPushButton.setObjectName(str(idx))
            SDPushButton = QPushButton("SD")
            SDPushButton.setObjectName(str(idx))
            logger.info(f"idx is {idx}")
            #create a new scope with another lambda so they stay seperate between loop iterations
            OPDPushButton.clicked.connect((lambda c: lambda : c.toggleOPDPWR())(chip))
            SDPushButton.clicked.connect((lambda c: lambda : c.toggleSD())(chip))
            itemLayout = QHBoxLayout(itemWidget)
            itemLayout.setContentsMargins(10, 4, 5, 2)
            itemLayout.addWidget(lineText)
            itemLayout.addStretch()
            itemLayout.addWidget(OPDPushButton)
            itemLayout.addWidget(SDPushButton)
            self.chipSelector.addItem(item)
            self.chipSelector.setItemWidget(item, itemWidget)



            #item = QListWidgetItem()
            #QListWidgetItem(f"{idx}: {chip.usbPath.decode()}", self.chipSelector)
            #QPushButton(text="idk", parent=item)
            #self.chipSelector.addItem(item)


        self.chips[0].probe_bus()

    def chipSelected(self, item):
        #this is super jank, but inhereting the QListWidgetItem is really weird and stinky, + this works + ratio + bozo no CS degree   ~\(:/)/~
        self.selectedChip = self.chipSelector.row(item)#item.text()[0]
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

        chip = self.chips[self.selectedChip]


        for row in opd_table:

            if(chip.probe_addr(row[1])):


                item = QListWidgetItem(opdList)
                widget = QWidget()
                widget.setFixedSize(350, 20)

                label = QLabel(f"{row[0]}, {row[1]}")
                opdButton = QPushButton("Enable")
                opdButton.clicked.connect((lambda _row : lambda : chip.opd_enable_disable_node(_row[1], True))(row))
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
        #opdRoot.setStyleSheet("background-color: grey")
        opdLabel = QLabel("Opd Menu", opdRoot)
        opdScanButton = QPushButton(text="scan")
        opdList = QListWidget(opdRoot)
        opdScanButton.clicked.connect((lambda _list : lambda : self.updateOpdMenu(_list))(opdList))
        self.updateOpdMenu(opdList)
        opdRootLayout = QVBoxLayout(opdRoot)
        opdRootLayout.addWidget(opdLabel)
        opdRootLayout.addWidget(opdList)
        opdRootLayout.addWidget(opdScanButton)



    def initUI(self):
        root = QWidget()
        self.setCentralWidget(root)

        rootLayout = QHBoxLayout()
        rootSplitter = QSplitter(root)


        panelLayout = QHBoxLayout()
        #panel = QWidget()
        panelSplitter = QSplitter(QtCore.Qt.Orientation.Vertical, rootSplitter)
        panelSplitter.setChildrenCollapsible(False)
        panelLayout.addWidget(panelSplitter)


        chipSelectorPane = QSplitter(QtCore.Qt.Orientation.Vertical, panelSplitter)
        chipSelectorPane.setChildrenCollapsible(False)
        chipSelectorPane.setHandleWidth(0)
        chipSelectorPaneLayout = QHBoxLayout()
        chipSelectorPaneLayout.addWidget(chipSelectorPane)

        self.chipSelector = QListWidget(chipSelectorPane)#QLabel("Chip Selector")
        #self.chipSelector.setStyleSheet("background-color: grey")
        self.chipSelector.itemClicked.connect(self.chipSelected)

        chipSelectorTitle = QLabel("Chip Selector")
        chipSelectorTitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        #chipSelectorTitle.setStyleSheet("background-color: grey")
        chipSelectorRefreshButton = QPushButton(text="REFRESH")
        chipSelectorRefreshButton.clicked.connect(self.updateChipSelector)
        #chipSelectorRefreshButton.setStyleSheet("background-color: grey")

        chipSelectorPane.addWidget(chipSelectorTitle)
        chipSelectorPane.addWidget(self.chipSelector)
        chipSelectorPane.addWidget(chipSelectorRefreshButton)
        self.updateChipSelector()



        opdMenu = QWidget() #QLabel("OPD Control")
        self.drawOpdMenu(opdMenu)


        panelSplitter.addWidget(chipSelectorPane)
        panelSplitter.addWidget(opdMenu)


        label2 = QLabel("REPLACE MEEEE", self)
        #label2.setStyleSheet("background-color: grey")

        rootLayout.addWidget(rootSplitter)
        root.setLayout(rootLayout)
        rootSplitter.addWidget(panelSplitter)
        rootSplitter.setChildrenCollapsible(False)
        rootSplitter.addWidget(label2)

def main():

    logging.basicConfig(level=logging.DEBUG)
    logger.info('started c3-proxy software')
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())



main()
