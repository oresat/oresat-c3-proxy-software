from enum import auto, IntEnum, Enum, EnumType, unique
from itertools import cycle
import logging
logger = logging.getLogger()

class OpdPowerState(Enum):
    powered = auto()
    unpowered = auto()

    #expects instances to be ascending monotonic ints
    def next(self) -> OpdPowerState:
        length = self.__class__.__len__()
        #auto() starts at one, so modulo is strange
        new = ( self.value % length ) + 1
        return OpdPowerState(new)

class OpdCardState(Enum):
    powered = auto()
    unpowered = auto()

    #expects instances to be ascending monotonic ints
    def next(self) -> OpdCardState:
        length = self.__class__.__len__()
        #auto() starts at one, so modulo is strange
        new = ( self.value % length ) + 1
        return OpdCardState(new)


class BusShutdownState(Enum):
    shutdown = auto()
    nominal = auto()

    #expects instances to be ascending monotonic ints
    def next(self) -> BusShutdownState:
        length = self.__class__.__len__()
        new = ( self.value % length ) + 1
        return BusShutdownState(new)

class IspModeState(Enum):
    disabled = auto()
    enabled = auto()

    def next(self) -> IspModeState:
        length = self.__class__.__len__()
        new = (self.value % length) + 1
        return IspModeState(new)

class UartState(Enum):
    disabled = auto()
    enabled = auto()

    def next(self) -> UartState:
        length = self.__class__.__len__()
        new = (self.value % length) + 1
        return UartState(new)

class CBResetState(Enum):
    disabled = auto()
    enabled = auto()

    def next(self) -> CBResetState:
        length = self.__class__.__len__()
        new = (self.value % length) + 1
        return CBResetState(new)


@unique
class OpdAddress(IntEnum):
    ProtoCard           = 0x10
    DiodeTestCard       = 0x11
    #UNUSED              = 0x12
    #UNUSED              = 0x13
    ZpEndCard           = 0x14
    ZmEndCard           = 0x15
    ZmMidCard           = 0x16
    ZpMidCard           = 0x17
    Battery1            = 0x18
    GPS                 = 0x19
    MagCard             = 0x1A
    DxWiFi              = 0x1B
    StarTracker1        = 0x1C
    CFCProcessor        = 0x1D
    CFCSensor           = 0x1E
    Battery2            = 0x1F
    RW1                 = 0x20
    RW2                 = 0x21
    RW3                 = 0x22
    RW4                 = 0x23
    StarTracker2        = 0x24
    #UNUSED              = 0x25
    #UNUSED              = 0x26
    #UNUSED              = 0x27
    #UNUSED              = 0x28
    #UNUSED              = 0x29
    #UNUSED              = 0x2A
    #UNUSED              = 0x2B
    #UNUSED              = 0x2C
    #UNUSED              = 0x2D
    #UNUSED              = 0x2E
    #UNUSED              = 0x2F
    #UNUSED              = 0x30
    #UNUSED              = 0x31
    #UNUSED              = 0x32
    #UNUSED              = 0x33
    #UNUSED              = 0x34
    #UNUSED              = 0x35
    #UNUSED              = 0x36
    #UNUSED              = 0x37
    #UNUSED              = 0x38
    #UNUSED              = 0x39
    #UNUSED              = 0x3A
    #UNUSED              = 0x3B
    #UNUSED              = 0x3C
    #UNUSED              = 0x3D
    #UNUSED              = 0x3E
    #UNUSED              = 0x3F

#    PROTOCARD     = 0x10
#    BATTERY_1     = 0x18
#    GPS           = 0x19
#    ADCS          = 0x1A
#    DXWIFI        = 0x1B
#    STAR_TRACKER  = 0x1C
#    BATTERY_2     = 0x1D
#    CFC_OCTAVO    = 0x1E
#    CFC_SENSOR    = 0x1F
#    RW1           = 0x20
#    RW2           = 0x21
#    RW3           = 0x22
#    RW4           = 0x23


opd_table = [
    ['protocard', OpdAddress.ProtoCard],
    ['diode-test-card', OpdAddress.DiodeTestCard],
    ['z+ End Card', OpdAddress.ZpEndCard],
    ['z- End Card', OpdAddress.ZmEndCard],
    ['z- Mid Card', OpdAddress.ZmMidCard],
    ['z+ Mid Card', OpdAddress.ZpMidCard],
    ['battery-1', OpdAddress.Battery1],
    ['gps', OpdAddress.GPS],
    ['mag-card', OpdAddress.MagCard],
    ['dxwifi', OpdAddress.DxWiFi],
    ['star-tracker-1', OpdAddress.StarTracker1],
    ['cfc-processor', OpdAddress.CFCProcessor],
    ['cfc-sensor', OpdAddress.CFCSensor],
    ['battery-2', OpdAddress.Battery2],
    ['rw1', OpdAddress.RW1],
    ['rw2', OpdAddress.RW2],
    ['rw3', OpdAddress.RW3],
    ['rw4', OpdAddress.RW4],
    ['star-tracker-2', OpdAddress.StarTracker2],
]

@unique
class Max7310Reg(IntEnum):
    INPUT                   = 0x00
    ODR                     = 0x01
    POL                     = 0x02
    MODE                    = 0x03
    TIMEOUT                 = 0x04

#@dataclass(int, frozen=True)
#class Max7310PinT:
#        self.super()
    #    self.super().__init__()
@unique
class Max7310Pin(IntEnum):
    OPD_SCL                    = 0
    OPD_SDA                    = 1
    OPD_FAULT                  = 2
    OPD_EN                     = 3
    OPD_CB_RESET               = 4
    OPD_BOOT0                  = 5
    OPD_LINUX_BOOT             = 6
    OPD_PIN7                   = 7

