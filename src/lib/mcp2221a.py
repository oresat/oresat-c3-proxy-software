from lib.opd import OpdPowerState, BusShutdownState, opd_table
from smbus2 import SMBus, i2c_msg
import gpiod
from gpiod import Chip
from gpiod.line import Direction, Value
import subprocess
from pathlib import Path
import time
from lib.opd import *
from lib.ina226 import INA226
import logging
logger = logging.getLogger()

SHUTDOWNPIN = 2
OPDPOWPIN = 3


class Mcp2221a:
    i2c: SMBus
    serial: str
    gpio: str
    OPDState: OpdPowerState
    SDState: BusShutdownState
    ina226: INA226

    def __init__(self, i2c: str, serial: str, gpio: str, usbPath: str):
        #try:
        self.i2c = SMBus(i2c)
        self.serial = serial
        self.gpio = gpio
        self.gpioReq = Chip(gpio).request_lines(
            consumer="mcp2221a object",
            config={
                SHUTDOWNPIN: gpiod.LineSettings(
                    direction=Direction.OUTPUT, output_value=Value.INACTIVE
                ),
                OPDPOWPIN: gpiod.LineSettings(
                    direction=Direction.OUTPUT, output_value=Value.ACTIVE
                )
            }
        )
        self.usbPath = usbPath
        self.OPDState = OpdPowerState.unpowered
        self.SDState = BusShutdownState.shutdown
        self.ina226 = INA226(self.i2c, 0x40)
        #print("ina226 is ", self.ina226)
        #except Exception as e:
        #    print("could not initialize Mcp2221a", e)

    def __del__(self):
        self.gpioReq.release()


#    #should use context manager with this
#    def getGpioRequest(self):
#        print(self.gpio)
#        request = Chip(self.gpio)
#        return request

    def setSD(self, state: BusShutdownState):
        logger.debug(f"setting nSD pin to: {state}")
        req = self.gpioReq
        match state:
            case BusShutdownState.nominal:
                req.set_value(SHUTDOWNPIN, Value.ACTIVE)
                self.SDState = BusShutdownState.nominal
            case BusShutdownState.shutdown:
                req.set_value(SHUTDOWNPIN, Value.INACTIVE)
                self.SDState = BusShutdownState.shutdown
            case _:
                raise RuntimeError("state doesn't make sense")


    def toggleSD(self) -> BusShutdownState:
        logging.debug(f"toggling shutdown: {self}")
        self.setSD(self.SDState.next())
        return self.SDState


    def setOPDPWR(self, state: OpdPowerState):
        logger.debug(f"setting OPD_PWR to: {state}")
        req = self.gpioReq
        match state:
            #the OPD_PWR pin uses inverted logic
            case OpdPowerState.powered:
                req.set_value(OPDPOWPIN, Value.INACTIVE)
                self.OPDState = OpdPowerState.powered
            case OpdPowerState.unpowered:
                req.set_value(OPDPOWPIN, Value.ACTIVE)
                self.OPDState = OpdPowerState.unpowered
            case _:
                raise RuntimeError("state doesn't make sense")


    def toggleOPDPWR(self) -> OpdPowerState:
        logger.debug(f"toggling OPD_PWR: {self}")

        self.setOPDPWR(self.OPDState.next())
        return(self.OPDState)

    def probe_addr(self, addr):
        #with SMBus(self.i2c) as bus:
        found = False
        try:
            self.i2c.write_quick(addr)
            found = True
        except Exception:
            pass
        return found


    def probe_bus(self):
        for row in opd_table:
            found = self.probe_addr(row[1])
            logger.info("I2C device at address 0x%X (%13s): %s" %(row[1], row[0], ("FOUND" if found else "not found")))

    def i2c_read_reg(self, addr, reg):
        #with SMBus(self.i2c) as bus:
        try:
            val = self.i2c.read_byte_data(addr, reg)
            logging.debug(f"i2c read reg: {reg:#02x}, value: {val:#02x}")
            return val
        except Exception as e:
            logger.error(f"Failed to read from i2c address {addr:#02x} - {e}")

    def i2c_write_reg(self, addr, reg, data):
        #with SMBus(self.i2c) as bus:
        #logger.debug(f"LENGTH OF DATA {type(data)}, {len(data)}")
        logging.debug(f"i2c write reg: {reg:#02x}, value: {data.hex()}")
        buf = bytearray(1)
        buf[0] = reg
        buf.extend(bytes(data))
        try:
            return self.i2c.write_block_data(addr, reg, buf)
        except Exception as e:
            logger.error(f"Failed to write to address {addr:#02x} reg={reg:#02x} - {e}")

    def opd_en_pin_mode(self, i2c_addr: OpdAddress):
        #result = self.i2c_read_reg(i2c_addr, MAX7310_AD_MODE)
        #result &= ~(1 << OPD_EN)  # Set the EN pin to output mode
        #result = 0b11110111
        #print("result is ", result, type(result), " length is: ", len(result))
        #self.i2c_write_reg(i2c_addr, MAX7310_AD_MODE, bytes([result]))
        self.read_max7310_reg(i2c_addr, Max7310Reg.MODE)

    def opd_print_status(self, i2c_addr: OpdAddress):
        print("====================")
        result = self.i2c_read_reg(i2c_addr, Max7310Reg.INPUT)
        print("MAX7310_AD_INPUT = 0x%X" % result)

        result = self.i2c_read_reg(i2c_addr, Max7310Reg.ODR)
        print("MAX7310_AD_ODR   = 0x%X" % result)

        result = self.i2c_read_reg(i2c_addr, Max7310Reg.POL)
        print("MAX7310_AD_POL   = 0x%X" % result)

        result = self.i2c_read_reg(i2c_addr, Max7310Reg.MODE)
        print("MAX7310_AD_MODE  = 0x%X" % result)


    def max7310_initialize(self, i2c_addr: OpdAddress):
        logger.debug(f"configuring card at addr {i2c_addr:#02x}")
        #configure inversion register
        resetData = bytes([0])
        self.i2c_write_reg(i2c_addr, Max7310Reg.POL, resetData)
        #set outputs as high/low
        self.clear_max7310_pin(i2c_addr, Max7310Pin.OPD_EN)
        self.clear_max7310_pin(i2c_addr, Max7310Pin.OPD_CB_RESET)
        self.set_max7310_pin(i2c_addr, Max7310Pin.OPD_BOOT0)#active low
        self.set_max7310_pin(i2c_addr, Max7310Pin.OPD_PIN7)

        #configure output pins
        config = 255
        config &= ~(1 << Max7310Pin.OPD_EN)
        config &= ~(1 << Max7310Pin.OPD_CB_RESET)
        config &= ~(1 << Max7310Pin.OPD_BOOT0)
        config &= ~(1 << Max7310Pin.OPD_PIN7)
        logger.debug(f"config byte is {config:#02x}")
        self.i2c_write_reg(i2c_addr, Max7310Reg.MODE, bytes([config]))


    def read_max7310_reg(self, i2c_addr: OpdAddress, reg: Max7310Reg):
        result = self.i2c_read_reg(i2c_addr, reg)
        logger.debug(f"read register #{reg} got: {result:#02x}")
        return result

    def read_max7310_pin(self, i2c_addr: OpdAddress, pin_num: Max7310Pin):
        result = self.i2c_read_reg(i2c_addr, Max7310Reg.ODR)
        result &= (1 << pin_num)
        logger.debug(f"read gpio #{pin_num}, got: {result:#02x}")
        #self.opd_print_status(i2c_addr)

        return result


    def set_max7310_pin(self, i2c_addr: OpdAddress, pin_num: Max7310Pin):
        result = self.i2c_read_reg(i2c_addr, Max7310Reg.ODR)
        logger.info(f"setting pin #{pin_num}, read: {result:02x}")
        result |= (1 << pin_num)
        #result = self.read_max7310_pin(i2c_addr, pin_num)
        logger.info(f"setting pin #{pin_num}, writing back: {result:02x}")
        self.i2c_write_reg(i2c_addr, Max7310Reg.ODR, bytes([result]))
        return


    def clear_max7310_pin(self, i2c_addr: OpdAddress, pin_num: Max7310Pin):
        result = self.i2c_read_reg(i2c_addr, Max7310Reg.ODR)
        logger.info(f"clearing pin #{pin_num}, read: {result:#02x}")
        result &= ~(1 << pin_num)
        logger.info(f"clearing pin #{pin_num}, writing back: {result:#02x}")
        self.i2c_write_reg(i2c_addr, Max7310Reg.ODR, bytes([result]))


    def set_node_EN(self, i2c_addr: OpdAddress, enable_flag: bool) -> OpdCardState | None:
        logger.debug(f"calling set_node_EN with addr: {i2c_addr:02x}, flag: {enable_flag:02x}")
        #self.max7310_initialize(i2c_addr)
        if enable_flag:
            self.set_max7310_pin(i2c_addr, Max7310Pin.OPD_EN)
        else:
            self.clear_max7310_pin(i2c_addr, Max7310Pin.OPD_EN)

        #for idx in range(5):
        reg = self.i2c_read_reg(i2c_addr, Max7310Reg.ODR)
        logger.debug(f"register contains {reg:#02x}")
        #    time.sleep(1)

        logger.debug(f" the input register has: {self.read_max7310_reg(i2c_addr, Max7310Reg.INPUT):#02x}")


        #read the register back and return the state it's in
        readback = self.read_max7310_pin(i2c_addr, Max7310Pin.OPD_EN)
        logger.debug(f" readback is {readback:#02x}")
        if readback == 0:
            if enable_flag:
                logger.error("gpio pin write failed, pin didn't go high")
            return OpdCardState.unpowered
        else:
            if not enable_flag:
                logger.error("gpio pin clear failed, pin didn't go low")
            return OpdCardState.powered


    def set_node_ISP(self, i2c_addr: OpdAddress, enable_flag: bool):
        logger.debug(f"setting OPD_BOOT0 pin to: {enable_flag} (active low)")
        #active low logic
        if enable_flag:
            self.clear_max7310_pin(i2c_addr, Max7310Pin.OPD_BOOT0)
        else:
            self.set_max7310_pin(i2c_addr, Max7310Pin.OPD_BOOT0)

        readback = self.read_max7310_pin(i2c_addr, Max7310Pin.OPD_BOOT0)
        if readback == 0:
            if enable_flag:
                logger.error("failed to set isp pin, didn't go high")
            return IspModeState.enabled
        else:
            if enable_flag:
                logger.error("failed to set isp pin, didn't go low")
            return IspModeState.disabled

    def set_node_UART(self, i2c_addr: OpdAddress, enable_flag: bool):
        logger.debug(f"setting OPD UART pin to: {enable_flag}")
        if enable_flag:
            self.set_max7310_pin(i2c_addr, Max7310Pin.OPD_PIN7)
        else:
            self.clear_max7310_pin(i2c_addr, Max7310Pin.OPD_PIN7)

        readback = self.read_max7310_pin(i2c_addr, Max7310Pin.OPD_PIN7)
        if readback == 1:
            if not enable_flag:
                logger.error("failed to set uart pin, didn't go high")
            return UartState.enabled
        else:
            if enable_flag:
                logger.error("failed to set uart pin, didn't go low")
            return UartState.disabled

    def set_node_CB_RESET(self, i2c_addr: OpdAddress, enable_flag: bool):
        logger.debug(f"setting OPD_CB_RESET pin to: {enable_flag}")
        #active low logic
        if enable_flag:
            self.set_max7310_pin(i2c_addr, Max7310Pin.OPD_CB_RESET)
        else:
            self.clear_max7310_pin(i2c_addr, Max7310Pin.OPD_CB_RESET)

        readback = self.read_max7310_pin(i2c_addr, Max7310Pin.OPD_CB_RESET)
        if readback == 1:
            if not enable_flag:
                logger.error("failed to set cb-reset pin, didn't go high")
            return CBResetState.enabled
        else:
            if enable_flag:
                logger.error("failed to set cb-reset pin, didn't go low")
            return CBResetState.disabled





#mychip = Mcp2221a("a", "b", "c", "idk")

#test
#print(mychip.i2c, mychip.serial, mychip.gpio, mychip.opdState, mychip.nShutdown)


def runCommand(command):
    try:
        result = subprocess.check_output(command, shell=True, executable="/bin/bash",
                   stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as cpe:
        result = cpe.output
        #errored = True

    #TODO: add error handling here
    return result


def getMcp2221a(gpiodev):
    #run udevadm to get usb path to chip that provides said gpio
    #eg. DEVPATH=/devices/pci0000:00/0000:00:08.1/0000:c4:00.3/usb1/1-2/1-2.1/1-2.1:1.2/0003:04D8:00DD.005C/gpiochip2
    fullPath = runCommand(f"udevadm info --query=path /dev/{str(gpiodev)}")
    usbPath = fullPath.split("/".encode())[-4]
    sysPrefix = "/sys/bus/usb/devices/" + usbPath.decode()

    #tty appears in .0
    ttyPath = sysPrefix + ":1.0/tty/"
    tty = "/dev/" + runCommand(f"ls {ttyPath} | grep tty").decode().strip()

    #gpio and i2c appear in .2
    i2cGpioPrefix = sysPrefix + ":1.2"
    i2cGpioPath = (i2cGpioPrefix + "/" + runCommand(f"ls {i2cGpioPrefix} | grep 0003:04D8:00DD").decode()).strip()
    i2c = "/dev/" + runCommand(f"ls {i2cGpioPath} | grep i2c").decode().strip()
    gpio = "/dev/" + runCommand(f"ls {i2cGpioPath} | grep gpiochip").decode().strip()
    logger.info(f"{i2c}, {gpio}, {tty}")

    return Mcp2221a(i2c, tty, gpio, usbPath)



def getMcp2221as():
    rtn = []

    #TODO: add error handling
    #find a chip by looking for gpios
    gpioResult = runCommand("gpiodetect")
    gpioDevices = []
    for line in gpioResult.decode().splitlines():
        if 'mcp2221' in line:
            gpioDevices.append(line.split()[0])
    logger.info(f"gpiodevices: {gpioDevices}")

    for gpioDevice in gpioDevices:
        rtn.append(getMcp2221a(gpioDevice))

    return rtn

#getMcp2221as()

