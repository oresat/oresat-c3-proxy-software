from opd import OpdPowerState, BusNShutdownState


class Mcp2221a:
    i2c = ""
    serial = ""
    gpio = ""
    opdState = OpdPowerState
    nShutdownState = BusNShutdownState

    def __init__(self, i2c, serial, gpio):
        self.i2c = i2c
        self.serial = serial
        self.gpio = gpio
        self.opdState = OpdPowerState.idling
        self.nShutdown = BusNShutdownState.idling



mychip = Mcp2221a("a", "b", "c")

print(mychip.i2c, mychip.serial, mychip.gpio, mychip.opdState, mychip.nShutdown)
