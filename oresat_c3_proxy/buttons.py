
from .lib.opd import Max7310Pin, Max7310Reg, OpdAddress, BusShutdownState, OpdCardState, OpdPowerState, opd_table, IspModeState, UartState, CBResetState
from PySide6.QtWidgets import QPushButton

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


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


