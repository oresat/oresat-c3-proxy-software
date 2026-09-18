from enum import auto, IntEnum, Enum, EnumType
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
    def next(self) ->BusShutdownState:
        length = self.__class__.__len__()
        new = ( self.value % length ) + 1
        return BusShutdownState(new)



OPD_I2C_ADDRESS_PROTOCARD     = 0x10
OPD_I2C_ADDRESS_BATTERY_1     = 0x18
OPD_I2C_ADDRESS_GPS           = 0x19
OPD_I2C_ADDRESS_ADCS          = 0x1A
OPD_I2C_ADDRESS_DXWIFI        = 0x1B
OPD_I2C_ADDRESS_STAR_TRACKER  = 0x1C
OPD_I2C_ADDRESS_BATTERY_2     = 0x1D
OPD_I2C_ADDRESS_CFC_OCTAVO    = 0x1E
OPD_I2C_ADDRESS_CFC_SENSOR    = 0x1F
OPD_I2C_ADDRESS_RW1           = 0x20
OPD_I2C_ADDRESS_RW2           = 0x21
OPD_I2C_ADDRESS_RW3           = 0x22
OPD_I2C_ADDRESS_RW4           = 0x23


opd_table = [
    ['protocard', OPD_I2C_ADDRESS_PROTOCARD],
    ['battery-1', OPD_I2C_ADDRESS_BATTERY_1],
    ['gps', OPD_I2C_ADDRESS_GPS],
    ['adcs', OPD_I2C_ADDRESS_ADCS],
    ['dxwifi', OPD_I2C_ADDRESS_DXWIFI],
    ['star-tracker', OPD_I2C_ADDRESS_STAR_TRACKER],
    ['battery-2', OPD_I2C_ADDRESS_BATTERY_2],
    ['cfc-octavo', OPD_I2C_ADDRESS_CFC_OCTAVO],
    ['cfc-sensor', OPD_I2C_ADDRESS_CFC_SENSOR],
    ['rw1', OPD_I2C_ADDRESS_RW1],
    ['rw2', OPD_I2C_ADDRESS_RW2],
    ['rw3', OPD_I2C_ADDRESS_RW3],
    ['rw4', OPD_I2C_ADDRESS_RW4],
#    ['TESTING', 24],
#    ['ina226-default', 0x40]
]

MAX7310_AD_INPUT                   = 0x00
MAX7310_AD_ODR                     = 0x01
MAX7310_AD_POL                     = 0x02
MAX7310_AD_MODE                    = 0x03
MAX7310_AD_TIMEOUT                 = 0x04

OPD_SCL                    = 0
OPD_SDA                    = 1
OPD_FAULT                  = 2
OPD_EN                     = 3
OPD_CB_RESET               = 4
OPD_BOOT0                  = 5
OPD_LINUX_BOOT             = 6
OPD_PIN7                   = 7

