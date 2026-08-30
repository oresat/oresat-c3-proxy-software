from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QPushButton, QMainWindow, QWidget, QApplication, QLabel, QHBoxLayout, QSplitter, QListWidget
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(500, 500, 500, 500)
        self.initUI()

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

        chipSelector = QListWidget(panelSplitter)#QLabel("Chip Selector")
        chipSelector.addItem("maybechip1")
        chipSelector.addItem("sometimes chip 2")
        chipSelector.addItem("chip 3? good luck...")
        chipSelector.setStyleSheet("background-color: grey")
        opdControl = QLabel("OPD Control")
        opdControl.setStyleSheet("background-color: grey")
        panelSplitter.addWidget(chipSelector)
        panelSplitter.addWidget(opdControl)


        label2 = QLabel("REPLACE MEEEE", self)
        label2.setStyleSheet("background-color: grey")

        rootLayout.addWidget(rootSplitter)
        root.setLayout(rootLayout)
        rootSplitter.addWidget(panelSplitter)
        rootSplitter.setChildrenCollapsible(False)
        rootSplitter.addWidget(label2)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


main()
