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
with gpiod.Chip(GPIOCHIP) as chip:
    info = chip.get_info()
    print(f"{info.name}, [{info.label}] ({info.num_lines} lines)")


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
    message = [
            0x0,
            0xb1, #write flash
            0x01, #write GP settings
            0b00100000, #put gpio0 in uart led mode
            0b00100000, #put gpio1 in uart led mode
            0b00001000, #set gpio2 as output, default high
            0b00001000, #set gpio3 as output, default high
    ]




    h = hid.device()
    h.open(idVendor,idProduct)
    print("Manufacturer: %s" % h.get_manufacturer_string())
    print("Product: %s" % h.get_product_string())
    print("Serial No: %s" % h.get_serial_number_string())

    h.set_nonblocking(1)
    rtn = h.write(message)
    print(rtn) #number of bytes written I thinks



import time

from gpiod.line import Direction, Value
from gpiod import Chip

setup_mcp2221a()



LINE = 0

#breakpoint()
chip = Chip("/dev/gpiochip2")
request = chip.request_lines(
    consumer="blink-example",
    config={
        LINE: gpiod.LineSettings(
            direction=Direction.OUTPUT, output_value=Value.ACTIVE
        )
    },
)



#
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
    request.set_value(LINE, Value.ACTIVE)
    time.sleep(1)
    request.set_value(LINE, Value.INACTIVE)
    time.sleep(1)
