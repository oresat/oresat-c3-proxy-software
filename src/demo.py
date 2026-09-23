#import mcp2221a
from lib.mcp2221a import *
from lib.opd import *

chips = getMcp2221as()
chip = chips[0]
print(chip)

#print(chip.scanChips())
chip.setOPDPWR(OpdPowerState.powered)
chip.setSD(BusShutdownState.shutdown)

target = OpdAddress.PROTOCARD

chip.max7310_initialize(target)


while (True):
    chip.set_node_EN(target, True)
    time.sleep(1)
    chip.setSD(BusShutdownState.nominal)
    time.sleep(2)
    chip.setSD(BusShutdownState.shutdown)
    time.sleep(1)
    chip.set_node_EN(target, False)
    time.sleep(1)
