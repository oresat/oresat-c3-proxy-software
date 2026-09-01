from lib.opd import OpdPowerState, BusShutdownState, opd_table
from smbus2 import SMBus, i2c_msg
import gpiod
from gpiod import Chip
from gpiod.line import Direction, Value
import subprocess
from pathlib import Path
import time


SHUTDOWNPIN = 2
OPDPOWPIN = 3


class Mcp2221a:
    i2c = ""
    serial = ""
    gpio = ""
    OPDState = OpdPowerState
    SDState = BusShutdownState

    def __init__(self, i2c, serial, gpio, usbPath):
        self.i2c = i2c
        self.serial = serial
        self.gpio = gpio
        self.gpioReq = Chip(gpio).request_lines(
            consumer="mcp2221a object",
            config={
                2: gpiod.LineSettings(
                    direction=Direction.OUTPUT, output_value=Value.ACTIVE
                ),
                3: gpiod.LineSettings(
                    direction=Direction.OUTPUT, output_value=Value.ACTIVE
                )
            }
        )
        self.usbPath = usbPath
        self.OPDState = OpdPowerState.idling
        self.SDState = BusShutdownState.idling

    def __del__(self):
        self.gpioReq.release()


#    #should use context manager with this
#    def getGpioRequest(self):
#        print(self.gpio)
#        request = Chip(self.gpio)
#        return request


    def toggleSD(self):

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
            print(Exception)



    def probe_bus(self):
        with SMBus(self.i2c) as bus:
            for row in opd_table:
                addr = row[1]
                found = False
                try:
                    #throws exception if no response
                    bus.write_quick(addr)
                    found = True
                except Exception:
                    pass

                print("I2C device at address 0x%X (%13s): %s" %(addr, row[0], ("FOUND" if found else "not found")))

    def i2c_read_reg(self, addr, reg):
        with SMBus(self.i2c) as bus:
            write = i2c_msg.write(addr, bytes([reg]))
            read = i2c_msg.read(addr, 1)
            try:
                bus.rdwr(write, read)
                return read
            except Exception:
                print("Failed to read from i2c address 0x%X" % addr)

    def i2c_write_reg(self, addr, reg, data):
        with SMBus(self.i2c) as bus:
            buf = bytearray(1)
            buf[0] = reg
            buf.extend(data)
            write = i2c_msg.write(addr, bytes([data]))
            try:
                bus.rdwr(write)
            except Exception:
                print("Failed to write to address 0x%X: reg=0x%X" % (addr, reg))

    def opd_en_pin_mode(self, i2c_addr):
        result = self.i2c_read_reg(i2c_addr, MAX7310_AD_MODE)
        result[0] &= ~(1 << OPD_EN)  # Set the EN pin to output mode
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
        result = i2c_read_reg(self, i2c_addr, MAX7310_AD_ODR)
        result[0] |= (1 << pin_num)
        i2c_write_reg(self, i2c_addr, MAX7310_AD_ODR, result)
        return

    def clear_max7310_pin(self, i2c_addr, pin_num):
        result = i2c_read_reg(self, i2c_addr, MAX7310_AD_ODR)
        result[0] &= ~(1 << pin_num)
        i2c_write_reg(self, i2c_addr, MAX7310_AD_ODR, result)

    def opd_enable_disable_node(self, i2c_addr, enable_flag):
        opd_en_pin_mode(self, i2c_addr)
        if enable_flag:
            set_max7310_pin(self, i2c_addr, OPD_EN)
        else:
            clear_max7310_pin(self, i2c_addr, OPD_EN)
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
    print(i2c, gpio, tty)

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
    print(gpioDevices)

    for gpioDevice in gpioDevices:
        rtn.append(getMcp2221a(gpioDevice))

    return rtn

getMcp2221as()

