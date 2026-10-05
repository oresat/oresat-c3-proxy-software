

from smbus2 import SMBus, i2c_msg
import gpiod
from lib.mcp2221a import getMcp2221as, Mcp2221a
import time


#uses the knon vendor and product ID to configure the gpio modes in flash
# via USB HID packets
def setup_mcp2221a():
    import hid

    # HID constants
    idVendor=0x04d8
    idProduct=0x00dd

    #from page 35 of mcp2221a
    configureGpioMessage = [
        0xb1, #write flash
        0x01, #write GP settings
        0b00000010, #put gpio0 in uart led mode
        0b00000011, #put gpio1 in uart led mode
        0b00010000, #set gpio2 as output, default high
        0b00010000, #set gpio3 as output, default high
    ]

    #set the productID to something special so we can recognise chips later
    #table 3-14, page 36
    productIDBaseString = "MCP2221(a): " #MCP2221(a) UART/I2C Bridge
    chipSpecifcName = "_2_"
    toSet = productIDBaseString + chipSpecifcName
    stringAsBytes = bytearray(toSet, "UTF-16")
    stringLength = len(stringAsBytes)

    configureProductIDMessage = [
        0xB1, #Write Flash Data – command code.
        0x03,
        #Write USB Manufacturer Descriptor String –
        #writes the USB Manufacturer String Descriptor used during
        #the USB enumeration.
        stringLength + 2, #Note 2
        #Number of bytes + 2 in the provided USB Serial Number
        #Descriptor String.
        0x03, #The value at this index must always be 0x03.
    ]

    finalString = bytearray(configureProductIDMessage) + stringAsBytes

    print("goober")
    print("hello this is the final string", finalString)
    print("and it says: ", finalString.decode("UTF-16"))

    #chip needs to be reset after writing to flash
    #table 3-40, page 55, mcp2221a datasheet
    resetMessage = [
        0x70,
        0xAB,
        0xCD,
        0xEF,
    ]

    h = hid.device()
    h.open(idVendor,idProduct)
    print("Manufacturer: %s" % h.get_manufacturer_string())
    print("Product: %s" % h.get_product_string())
    print("Serial No: %s" % h.get_serial_number_string())

    rtn = h.write(configureGpioMessage) #print(rtn) #number of bytes written I thinks
    time.sleep(0.05)
    rtn = h.write(finalString)
    time.sleep(0.05)

    #reset the device
    print("resetting the device")
    rtn = h.write(resetMessage)
    time.sleep(0.05)
    print("Closing the device")
    h.close()

setup_mcp2221a()
