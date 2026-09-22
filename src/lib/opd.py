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



class OpdAddress(IntEnum):
    PROTOCARD     = 0x10
    BATTERY_1     = 0x18
    GPS           = 0x19
    ADCS          = 0x1A
    DXWIFI        = 0x1B
    STAR_TRACKER  = 0x1C
    BATTERY_2     = 0x1D
    CFC_OCTAVO    = 0x1E
    CFC_SENSOR    = 0x1F
    RW1           = 0x20
    RW2           = 0x21
    RW3           = 0x22
    RW4           = 0x23


opd_table = [
    ['protocard', OpdAddress.PROTOCARD],
    ['battery-1', OpdAddress.BATTERY_1],
    ['gps', OpdAddress.GPS],
    ['adcs', OpdAddress.ADCS],
    ['dxwifi', OpdAddress.DXWIFI],
    ['star-tracker', OpdAddress.STAR_TRACKER],
    ['battery-2', OpdAddress.BATTERY_2],
    ['cfc-octavo', OpdAddress.CFC_OCTAVO],
    ['cfc-sensor', OpdAddress.CFC_SENSOR],
    ['rw1', OpdAddress.RW1],
    ['rw2', OpdAddress.RW2],
    ['rw3', OpdAddress.RW3],
    ['rw4', OpdAddress.RW4],
#    ['TESTING', 24],
#    ['ina226-default', 0x40]
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

