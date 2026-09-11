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
        self.OPDState = OpdPowerState.asserting
        self.SDState = BusShutdownState.asserting
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


    def toggleSD(self):
            logging.debug(f"toggling power on: {self}")

        #try:
            req = self.gpioReq
            if self.SDState == BusShutdownState.idling:
                req.set_value(SHUTDOWNPIN, Value.ACTIVE)
                self.SDState = BusShutdownState.asserting
            elif self.SDState == BusShutdownState.asserting:
                req.set_value(SHUTDOWNPIN, Value.INACTIVE)
                self.SDState = BusShutdownState.idling
        #except Exception:
        #    print(Exception)

    def toggleOPDPWR(self):
        logger.debug(f"toggling OPD_PWR on {self}")

        try:
            #with self.gpioReq as req:
            req = self.gpioReq
            if self.OPDState == OpdPowerState.idling:
                req.set_value(OPDPOWPIN, Value.ACTIVE)
                self.OPDState = OpdPowerState.asserting
            elif self.OPDState == OpdPowerState.asserting:
                req.set_value(OPDPOWPIN, Value.INACTIVE)
                self.OPDState = OpdPowerState.idling

        except Exception:
            logger.debug(Exception)

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
            logging.debug(f"i2c read value: {val}")
            return val
        except Exception as e:
            logger.error(f"Failed to read from i2c address 0x{addr} - {e}")

    def i2c_write_reg(self, addr, reg, data):
        #with SMBus(self.i2c) as bus:
        buf = bytearray(1)
        buf[0] = reg
        buf.extend(bytes(data))
        try:
            return self.i2c.write_block_data(addr, reg, buf)
        except Exception as e:
            logger.error(f"Failed to write to address 0x{addr} reg=0x{reg} - {e}")

    def opd_en_pin_mode(self, i2c_addr):
        result = self.i2c_read_reg(i2c_addr, MAX7310_AD_MODE)
        result &= ~(1 << OPD_EN)  # Set the EN pin to output mode
        result = bytearray([result])
        #print("result is ", result, type(result), " length is: ", len(result))
        self.i2c_write_reg(i2c_addr, MAX7310_AD_MODE, result)

    def opt_print_status(self, i2c_addr):
        print("====================")
        result = self.i2c_read_reg(i2c_addr, MAX7310_AD_INPUT)
        print("MAX7310_AD_INPUT = 0x%X" % result[0])

        result = self.i2c_read_reg(i2c_addr, MAX7310_AD_ODR)
        print("MAX7310_AD_ODR   = 0x%X" % result[0])

        result = self.i2c_read_reg(i2c_addr, MAX7310_AD_POL)
        print("MAX7310_AD_POL   = 0x%X" % result[0])

        result = self.i2c_read_reg(i2c_addr, MAX7310_AD_MODE)
        print("MAX7310_AD_MODE  = 0x%X" % result[0])


    def set_max7310_pin(self, i2c_addr, pin_num):
        result = self.i2c_read_reg(i2c_addr, MAX7310_AD_ODR)
        result |= (1 << pin_num)
        #result = bytes(result)
        logger.info(f"setting pin, result: {result}")
        self.i2c_write_reg(i2c_addr, MAX7310_AD_ODR, bytes([result]))
        return

    def clear_max7310_pin(self, i2c_addr, pin_num):
        result = self.i2c_read_reg(i2c_addr, MAX7310_AD_ODR)
        result &= ~(1 << pin_num)
        self.i2c_write_reg(i2c_addr, MAX7310_AD_ODR, bytes(result))

    def opd_enable_disable_node(self, i2c_addr, enable_flag):
        self.opd_en_pin_mode(i2c_addr)
        if enable_flag:
            self.set_max7310_pin(i2c_addr, OPD_EN)
        else:
            self.clear_max7310_pin(i2c_addr, OPD_EN)
        return


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
    logger.info(gpioDevices)

    for gpioDevice in gpioDevices:
        rtn.append(getMcp2221a(gpioDevice))

    return rtn

getMcp2221as()

