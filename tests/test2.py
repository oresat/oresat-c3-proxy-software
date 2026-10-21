from smbus2 import SMBus, i2c_msg
import gpiod

GPIOCHIP = "/dev/gpiochip2"
I2CADDR = 27

print(f"""using gpio:  {GPIOCHIP}
using i2c address: {I2CADDR}
    is this correct? y/n""")
if (input() != "y"):
    exit()



print("gpiochip: ", gpiod.is_gpiochip_device(GPIOCHIP))
with gpiod.Chip("/dev/gpiochip2") as chip:
    info = chip.get_info()
    print(f"{info.name}, [{info.label}] ({info.num_lines} lines)")
    chip.close()

with SMBus(I2CADDR) as bus:
    # Read 64 bytes from address 80
    write = i2c_msg.write(24, [0b0101])
    read = i2c_msg.read(24, 2)
    bus.i2c_rdwr(write, read)
#    print("result of write: ", write.buf)
#    print("result of read: ", read.buf)
    for k in range(read.len):
        print(read.buf[k])


#import time
#from gpiod.line import Direction, Value
#
#LINE=3
#with gpiod.request_lines(
#    GPIOCHIP,
#    consumer="blink-example",
#    config={
#        LINE: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)
#    },
#) as request:
#    while True:
#        request.set_value(LINE, Value.ACTIVE)
#        time.sleep(1)
#        request.set_value(LINE, Value.INACTIVE)
#        time.sleep(1)

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
    chipSpecifcName = "bob"
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

    #h.set_nonblocking(1)
    #rtn = h.write(configureGpioMessage)
    #print(rtn) #number of bytes written I thinks

    ## wait
    #time.sleep(0.05)

    #rtn = h.write(resetMessage)
    #time.sleep(0.05)
    rtn = h.write(finalString)
    time.sleep(0.05)

    

    # read back the answer
    print("Read the data")
    while True:
        d = h.read(64)
        if d:
            print(d)
        else:
            break
    #reset the device
    rtn = h.write(resetMessage)
    time.sleep(0.05)
    print("Closing the device")
    h.close()

import time

from gpiod.line import Direction, Value
from gpiod import Chip

setup_mcp2221a()



LINE = 2
with gpiod.Chip("/dev/gpiochip2") as chip:
    info = chip.get_info()
    print(f"{info.name}, [{info.label}] ({info.num_lines} lines)")
    chip.close()
#breakpoint()
chip = Chip("/dev/gpiochip2")
request = chip.request_lines(
    consumer="blink-example",
    config={
        2: gpiod.LineSettings(
            direction=Direction.OUTPUT, output_value=Value.ACTIVE
        ),
        3: gpiod.LineSettings(
            direction=Direction.OUTPUT, output_value=Value.ACTIVE
        )
    },
)

#with gpiod.request_lines(
#    "/dev/gpiochip2",
#    consumer="blink-example",
#    config={
#        LINE: gpiod.LineSettings(
#            direction=Direction.OUTPUT, output_value=Value.ACTIVE
#        )
#    },
#) as request:
while True:
    request.set_value(2, Value.ACTIVE)
    request.set_value(3, Value.INACTIVE)
    time.sleep(1)
    request.set_value(2, Value.INACTIVE)
    request.set_value(3, Value.ACTIVE)
    time.sleep(1)
